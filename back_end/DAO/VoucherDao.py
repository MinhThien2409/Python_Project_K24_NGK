import logging
from back_end.DBconnection import DBconnection

logger = logging.getLogger(__name__)


class VoucherDao:
    def _conn(self):
        return DBconnection.get_connection()

    @staticmethod
    def _select():
        return """SELECT VoucherId,SellerId,Code,Name,DiscountType,DiscountValue,
                         MinOrderValue,MaxDiscount,StartDate,EndDate,Quantity,
                         UsedQuantity,IsActive FROM Voucher"""

    @staticmethod
    def _row(r):
        return {
            "VoucherId": r[0], "SellerId": r[1], "Code": r[2], "Name": r[3],
            "DiscountType": r[4], "DiscountValue": float(r[5]),
            "MinOrderValue": float(r[6] or 0), "MaxDiscount": float(r[7] or 0),
            "StartDate": str(r[8]) if r[8] else None, "EndDate": str(r[9]) if r[9] else None,
            "Quantity": int(r[10] or 0), "UsedQuantity": int(r[11] or 0),
            "IsActive": bool(r[12])
        }

    def _attach_products(self, cursor, row):
        if not row:
            return None
        cursor.execute("SELECT ProductId FROM VoucherProduct WHERE VoucherId=%s ORDER BY ProductId", (row["VoucherId"],))
        row["ProductIds"] = [int(r[0]) for r in cursor.fetchall()]
        return row

    def lay_tat_ca(self, seller_id):
        conn = self._conn()
        if conn is None:
            return []
        cur = conn.cursor()
        try:
            cur.execute(self._select() + " WHERE SellerId=%s ORDER BY VoucherId DESC", (seller_id,))
            rows = [self._row(r) for r in cur.fetchall()]
            for row in rows:
                self._attach_products(cur, row)
            return rows
        finally:
            cur.close()
            conn.close()

    def lay_theo_id(self, i):
        conn = self._conn()
        if conn is None:
            return None
        cur = conn.cursor()
        try:
            cur.execute(self._select() + " WHERE VoucherId=%s", (i,))
            r = cur.fetchone()
            return self._attach_products(cur, self._row(r) if r else None)
        finally:
            cur.close()
            conn.close()

    def lay_theo_code(self, code):
        conn = self._conn()
        if conn is None:
            return None
        cur = conn.cursor()
        try:
            cur.execute(self._select() + " WHERE Code=%s", (code,))
            r = cur.fetchone()
            return self._attach_products(cur, self._row(r) if r else None)
        finally:
            cur.close()
            conn.close()

    def seller_dang_hoat_dong(self, seller_id):
        conn = self._conn()
        if conn is None:
            return False
        cur = conn.cursor()
        try:
            cur.execute("""SELECT EXISTS(
                SELECT 1 FROM Stores s JOIN Accounts a ON a.UserId=s.UserId
                WHERE s.StoreId=%s AND s.IsActive=1 AND a.trang_thai='active'
            )""", (seller_id,))
            row = cur.fetchone()
            return bool(row[0]) if row else False
        finally:
            cur.close(); conn.close()

    def lay_gia_san_pham_theo_voucher(self, voucher_id, product_ids):
        ids = [int(x) for x in (product_ids or [])]
        if not ids:
            return {"eligible_ids": [], "products": {}}
        conn = self._conn()
        if conn is None:
            return {"eligible_ids": [], "products": {}}
        cur = conn.cursor()
        try:
            ph = ",".join(["%s"] * len(ids))
            cur.execute(
                f"""SELECT vp.ProductId,p.Price,p.Quantity,p.IsActive
                    FROM VoucherProduct vp
                    JOIN Products p ON p.ProductId=vp.ProductId
                    WHERE vp.VoucherId=%s AND vp.ProductId IN ({ph})""",
                tuple([voucher_id] + ids)
            )
            rows = cur.fetchall()
            products = {
                int(r[0]): {
                    "price": float(r[1] or 0),
                    "quantity": int(r[2] or 0),
                    "is_active": bool(r[3])
                } for r in rows
            }
            return {"eligible_ids": list(products.keys()), "products": products}
        finally:
            cur.close()
            conn.close()

    def lay_gia_san_pham(self, product_ids):
        ids = [int(x) for x in (product_ids or [])]
        if not ids:
            return {}
        conn = self._conn()
        if conn is None:
            return {}
        cur = conn.cursor()
        try:
            ph = ",".join(["%s"] * len(ids))
            cur.execute(f"SELECT ProductId,Price,Quantity,IsActive FROM Products WHERE ProductId IN ({ph})", tuple(ids))
            return {int(r[0]): {"price": float(r[1] or 0), "quantity": int(r[2] or 0), "is_active": bool(r[3])} for r in cur.fetchall()}
        finally:
            cur.close()
            conn.close()

    def code_ton_tai(self, code, tru_id=None):
        conn = self._conn()
        if conn is None:
            return False
        cur = conn.cursor()
        try:
            q = "SELECT VoucherId FROM Voucher WHERE Code=%s"
            args = (code,)
            if tru_id is not None:
                q += " AND VoucherId<>%s"
                args = (code, tru_id)
            cur.execute(q, args)
            return cur.fetchone() is not None
        finally:
            cur.close()
            conn.close()

    def _products_belong_to_seller(self, cursor, seller_id, product_ids):
        ids = sorted(set(int(x) for x in product_ids))
        if not ids:
            return False
        ph = ",".join(["%s"] * len(ids))
        cursor.execute(
            f"SELECT ProductId FROM Products WHERE StoreId=%s AND ProductId IN ({ph})",
            tuple([seller_id] + ids)
        )
        found = {int(r[0]) for r in cursor.fetchall()}
        return len(found) == len(ids)

    def them(self, v, product_ids):
        conn = self._conn()
        if conn is None:
            return "error"
        cur = conn.cursor()
        try:
            if not self._products_belong_to_seller(cur, v.SellerId, product_ids):
                conn.rollback()
                return "invalid_product"
            cur.execute(
                """INSERT INTO Voucher
                   (SellerId,Code,Name,DiscountType,DiscountValue,MinOrderValue,
                    MaxDiscount,StartDate,EndDate,Quantity,UsedQuantity,IsActive)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s)""",
                (v.SellerId,v.Code,v.Name,v.DiscountType,v.DiscountValue,v.MinOrderValue,
                 v.MaxDiscount,v.StartDate,v.EndDate,v.Quantity,int(bool(v.IsActive)))
            )
            voucher_id = cur.lastrowid
            cur.executemany(
                "INSERT INTO VoucherProduct(VoucherId,ProductId) VALUES(%s,%s)",
                [(voucher_id, pid) for pid in product_ids]
            )
            conn.commit()
            return "ok"
        except Exception as e:
            conn.rollback()
            logger.exception("Loi them voucher: %s", e)
            return "error"
        finally:
            cur.close()
            conn.close()

    def sua(self, v, product_ids):
        conn = self._conn()
        if conn is None:
            return "error"
        cur = conn.cursor()
        try:
            if not self._products_belong_to_seller(cur, v.SellerId, product_ids):
                conn.rollback()
                return "invalid_product"
            cur.execute(
                """UPDATE Voucher SET Code=%s,Name=%s,DiscountType=%s,DiscountValue=%s,
                   MinOrderValue=%s,MaxDiscount=%s,StartDate=%s,EndDate=%s,
                   Quantity=%s,IsActive=%s
                   WHERE VoucherId=%s AND SellerId=%s""",
                (v.Code,v.Name,v.DiscountType,v.DiscountValue,v.MinOrderValue,v.MaxDiscount,
                 v.StartDate,v.EndDate,v.Quantity,int(bool(v.IsActive)),v.VoucherId,v.SellerId)
            )
            if cur.rowcount != 1:
                conn.rollback()
                return "error"
            cur.execute("DELETE FROM VoucherProduct WHERE VoucherId=%s", (v.VoucherId,))
            cur.executemany(
                "INSERT INTO VoucherProduct(VoucherId,ProductId) VALUES(%s,%s)",
                [(v.VoucherId, pid) for pid in product_ids]
            )
            conn.commit()
            return "ok"
        except Exception as e:
            conn.rollback()
            logger.exception("Loi sua voucher: %s", e)
            return "error"
        finally:
            cur.close()
            conn.close()

    def toggle(self, i, seller_id):
        conn = self._conn()
        if conn is None:
            return False
        cur = conn.cursor()
        try:
            cur.execute("UPDATE Voucher SET IsActive=NOT IsActive WHERE VoucherId=%s AND SellerId=%s", (i, seller_id))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.exception("Loi toggle voucher: %s", e)
            return False
        finally:
            cur.close()
            conn.close()

    def xoa(self, i, seller_id):
        conn = self._conn()
        if conn is None:
            return "error"
        cur = conn.cursor()
        try:
            cur.execute("SELECT UsedQuantity FROM Voucher WHERE VoucherId=%s AND SellerId=%s FOR UPDATE", (i, seller_id))
            r = cur.fetchone()
            if not r:
                conn.rollback()
                return "error"
            if int(r[0] or 0) > 0:
                conn.rollback()
                return "used"
            cur.execute("DELETE FROM VoucherProduct WHERE VoucherId=%s", (i,))
            cur.execute("DELETE FROM Voucher WHERE VoucherId=%s AND SellerId=%s", (i, seller_id))
            if cur.rowcount != 1:
                conn.rollback()
                return "error"
            conn.commit()
            return "ok"
        except Exception as e:
            conn.rollback()
            logger.exception("Loi xoa voucher: %s", e)
            return "error"
        finally:
            cur.close()
            conn.close()
