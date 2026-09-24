import logging
import uuid

from back_end.DBconnection import DBconnection
from back_end.Model.DonHang import DonHang
from back_end.Model.OrderItem import OrderItem

logger = logging.getLogger(__name__)

# LƯU Ý (MySQL):
# - Placeholder dùng %s (mysql-connector-python / PyMySQL) thay cho ? của pyodbc.
# - Kết quả trả về là tuple → truy cập theo chỉ số (row[0]) thay vì row.TenCot.
# - SUM(...) trong MySQL trả Decimal → ép int()/float() để JSON hóa được.
# - "SELECT TOP (n)" (SQL Server) → "LIMIT n" ở cuối câu lệnh.


class DonHangDao:
    # ─── GHI ───
    def tao_don_hang(self, orders: list):
        """Tạo N đơn + chi tiết trong 1 giao dịch; trả list OrderId mới.

        All-or-nothing (plan.md D3): 1 đơn thất bại (hết hàng) → rollback toàn
        bộ, không đơn nào được tạo. Mỗi phần tử là 1 DonHang đã nhóm theo shop
        (BUS đảm nhiệm), Items của nó chỉ chứa sản phẩm cùng StoreId.
        """
        conn = DBconnection().get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        try:
            cac_order_id = []
            for order in orders:
                new_order_id = self._chen_order_lay_id(cursor, order)
                loi_kho = self._chen_items_tru_kho(cursor, conn, new_order_id,
                                                   order.Items)
                if loi_kho:
                    return loi_kho
                cac_order_id.append(new_order_id)
            conn.commit()
            return cac_order_id
        except Exception as e:
            conn.rollback()
            logger.exception("Lỗi tạo N đơn hàng + chi tiết: %s", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def _chen_order_lay_id(self, cursor, order):
        """Chèn Orders và trả về OrderId mới sinh (MySQL: cursor.lastrowid)."""
        sql_order = """
        INSERT INTO Orders (Status, ShippingFee, UserId, ReceiverName,
                            ReceiverPhone, ShippingAddress, PaymentMethod,
                            SubTotal, DiscountAmount, TotalAmount, Note)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_order, (
            str(order.Status),
            float(order.ShippingFee or 0),
            int(order.UserId),
            str(order.ReceiverName),
            str(order.ReceiverPhone),
            str(order.ShippingAddress),
            str(order.PaymentMethod),
            float(order.SubTotal or 0),
            float(order.DiscountAmount or 0),
            float(order.TotalAmount or 0),
            str(order.Note) if order.Note else None
        ))
        return cursor.lastrowid

    def _chen_items_tru_kho(self, cursor, conn, new_order_id, order_items):
        """Chèn OrderItems kèm trừ kho, thiếu hàng thì rollback và báo lỗi."""
        sql_item = """
        INSERT INTO OrderItems (OrderId, ProductId, ProductName, Emoji,
                                Quantity, UnitPrice, TotalPrice)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        # Lệnh trừ kho — atomic, có điều kiện Quantity >= %s để không bị âm
        sql_tru_kho = """
        UPDATE Products
        SET Quantity = Quantity - %s
        WHERE ProductId = %s AND Quantity >= %s
        """
        for item in order_items:
            qty = int(item.Quantity or 0)
            cursor.execute(sql_item, (
                int(new_order_id),
                int(item.ProductId),
                str(item.ProductName or f'Sản phẩm #{item.ProductId}'),
                str(item.Emoji or '📦'),
                qty,
                float(item.UnitPrice or 0),
                float(item.TotalPrice or 0)
            ))
            # Trừ tồn kho ngay khi đặt hàng thành công
            cursor.execute(sql_tru_kho, (qty, int(item.ProductId), qty))
            if cursor.rowcount == 0:
                return self._xu_ly_thieu_hang(cursor, conn, item)
        return None

    def _xu_ly_thieu_hang(self, cursor, conn, item):
        """Rollback khi thiếu hàng và trả dict lỗi tồn kho."""
        cursor.execute(
            "SELECT ProductName, Quantity FROM Products WHERE ProductId = %s",
            (item.ProductId,)
        )
        info = cursor.fetchone()
        conn.rollback()
        if info:
            return {"error": "out_of_stock",
                    "product_name": info[0],
                    "available": info[1]}
        return {"error": "not_found", "product_name": f"#{item.ProductId}"}

    # ─── ĐỌC ───
    def lay_don_hang_cua_user(self, ma_user):
        """Lấy danh sách đơn kèm items của một khách hàng."""
        conn = DBconnection().get_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM Orders WHERE UserId = %s ORDER BY CreatedAt DESC",
                (ma_user,)
            )
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [self._nap_items_va_chuan_hoa(conn, columns, row) for row in rows]
        except Exception as e:
            logger.exception("Lỗi lay_don_hang_cua_user: %s", e)
            return []
        finally:
            cursor.close()
            conn.close()

    def _nap_items_va_chuan_hoa(self, conn, columns, row):
        """Gắn Items vào dict đơn và chuẩn hóa ngày giờ."""
        don = dict(zip(columns, row))
        don["Items"] = self._lay_items_cua_don(conn, don["OrderId"])
        if don.get("CreatedAt"):
            don["CreatedAt"] = str(don["CreatedAt"])
        if don.get("UpdatedAt"):
            don["UpdatedAt"] = str(don["UpdatedAt"])
        return don

    def _lay_items_cua_don(self, conn, order_id):
        """Đọc toàn bộ OrderItems của một đơn hàng."""
        cursor2 = conn.cursor()
        try:
            cursor2.execute("SELECT * FROM OrderItems WHERE OrderId = %s", (order_id,))
            item_rows = cursor2.fetchall()
            item_columns = [col[0] for col in cursor2.description]
            return [dict(zip(item_columns, ir)) for ir in item_rows]
        finally:
            cursor2.close()

    # ─── GHI ───
    def cap_nhat_trang_thai(self, order_id, new_status):
        """Cập nhật trạng thái đơn (luồng đã được BUS validate)."""
        conn = DBconnection().get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        try:
            current_status = self._doc_trang_thai_hien_tai(cursor, order_id)
            if current_status is None:
                return False
            logger.warning("Đơn #%s: %s → %s", order_id, current_status, new_status)
            rows_affected = self._ghi_trang_thai_moi(cursor, order_id, new_status)
            self._dong_bo_kho_theo_trang_thai(cursor, order_id, current_status, new_status)
            conn.commit()
            return rows_affected > 0
        except Exception as e:
            conn.rollback()
            logger.exception("Lỗi cap_nhat_trang_thai: %s", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def _doc_trang_thai_hien_tai(self, cursor, order_id):
        """Đọc Status hiện tại của đơn, thiếu thì trả None."""
        cursor.execute("SELECT Status FROM Orders WHERE OrderId = %s", (order_id,))
        row = cursor.fetchone()
        return row[0] if row else None

    def _ghi_trang_thai_moi(self, cursor, order_id, new_status):
        """Ghi Status mới và trả số dòng ảnh hưởng."""
        cursor.execute(
            "UPDATE Orders SET Status = %s WHERE OrderId = %s",
            (new_status, order_id)
        )
        return cursor.rowcount

    def _dong_bo_kho_theo_trang_thai(self, cursor, order_id, current_status, new_status):
        """Cộng SoldCount khi Completed, hoàn Quantity khi Cancelled."""
        if new_status == "Completed" and current_status != "Completed":
            self._cong_sold_count(cursor, order_id)
        if new_status == "Cancelled" and current_status != "Cancelled":
            self._hoan_ton_kho(cursor, order_id)

    def _cong_sold_count(self, cursor, order_id):
        """Cộng SoldCount theo Quantity từng item khi đơn hoàn thành."""
        cursor.execute(
            "SELECT ProductId, Quantity FROM OrderItems WHERE OrderId = %s",
            (order_id,)
        )
        for item in cursor.fetchall():
            cursor.execute(
                "UPDATE Products SET SoldCount = COALESCE(SoldCount, 0) + %s WHERE ProductId = %s",
                (item[1], item[0])
            )

    def _hoan_ton_kho(self, cursor, order_id):
        """Hoàn lại tồn kho theo Quantity từng item khi đơn bị hủy."""
        cursor.execute(
            "SELECT ProductId, Quantity FROM OrderItems WHERE OrderId = %s",
            (order_id,)
        )
        for item in cursor.fetchall():
            cursor.execute(
                "UPDATE Products SET Quantity = Quantity + %s WHERE ProductId = %s",
                (item[1], item[0])
            )

    # ─── ĐỌC ───
    def lay_tat_ca_don_hang(self):
        """Lấy toàn bộ đơn kèm tên khách và items."""
        conn = DBconnection().get_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        try:
            cursor.execute(self._sql_tat_ca_don_hang())
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [self._nap_items_va_chuan_hoa(conn, columns, row) for row in rows]
        except Exception as e:
            logger.exception("Lỗi lay_tat_ca_don_hang: %s", e)
            return []
        finally:
            cursor.close()
            conn.close()

    def _sql_tat_ca_don_hang(self):
        """Câu lệnh lấy toàn bộ đơn kèm tên khách hàng.

        T040 (008-split-user-table): KHÔNG cần sửa — truy vấn chỉ dùng
        `u.FullName` và `o.UserId` đều thuộc bảng `Users` (hồ sơ), không tham
        chiếu cột nào đã chuyển sang `Accounts` (Username/Password/Role_Id/
        trang_thai).
        """
        return """
        SELECT
            o.OrderId,
            o.Status,
            o.ShippingFee,
            o.UserId,
            u.FullName      AS CustomerName,
            o.ReceiverName,
            o.ReceiverPhone,
            o.ShippingAddress,
            o.PaymentMethod,
            o.SubTotal,
            o.DiscountAmount,
            o.TotalAmount,
            o.CreatedAt
        FROM Orders o
        LEFT JOIN Users u ON o.UserId = u.UserId
        ORDER BY o.CreatedAt DESC
        """

    def lay_thong_ke_tong_quan(self):
        """Thống kê tổng quan shop (dict thuần, lỗi trả {})."""
        conn = DBconnection().get_connection()
        if conn is None:
            return {}
        cursor = conn.cursor()
        try:
            tong = self._thong_ke_don_chinh(cursor)
            san_pham, nguoi_dung = self._dem_san_pham_va_user(cursor)
            tong["tong_san_pham"] = san_pham
            tong["tong_user"] = nguoi_dung
            tong["top_san_pham"] = self._top_san_pham_chung(cursor)
            tong["don_gan_day"] = self._don_gan_day_chung(cursor)
            return tong
        except Exception as e:
            logger.exception("Lỗi thống kê: %s", e)
            return {}
        finally:
            cursor.close()
            conn.close()

    def _thong_ke_don_chinh(self, cursor):
        """Tổng doanh thu và đếm đơn theo từng trạng thái."""
        cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN Status <> 'Cancelled' THEN TotalAmount ELSE 0 END), 0) AS doanh_thu,
                COUNT(*) AS tong_don,
                SUM(CASE WHEN Status='Pending'   THEN 1 ELSE 0 END) AS cho_duyet,
                SUM(CASE WHEN Status='Shipping'  THEN 1 ELSE 0 END) AS dang_giao,
                SUM(CASE WHEN Status='Completed' THEN 1 ELSE 0 END) AS hoan_thanh,
                SUM(CASE WHEN Status='Cancelled' THEN 1 ELSE 0 END) AS da_huy
            FROM Orders
        """)
        row = cursor.fetchone()
        # MySQL: SUM() trả Decimal (hoặc NULL nếu bảng rỗng) → ép kiểu tường minh
        return {"doanh_thu": float(row[0] or 0), "tong_don": int(row[1] or 0),
                "cho_duyet": int(row[2] or 0), "dang_giao": int(row[3] or 0),
                "hoan_thanh": int(row[4] or 0), "da_huy": int(row[5] or 0)}

    def _dem_san_pham_va_user(self, cursor):
        """Đếm tổng sản phẩm và người dùng.

        T040 (008-split-user-table): `COUNT(*) FROM Users` đếm hồ sơ — bảng
        `Users` còn nguyên sau khi tách; không cần sửa.
        """
        cursor.execute("SELECT COUNT(*) AS tong FROM Products")
        p = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) AS tong FROM Users")
        u = cursor.fetchone()
        return p[0], u[0]

    def _top_san_pham_chung(self, cursor):
        """Top 5 sản phẩm bán chạy toàn shop."""
        cursor.execute("""
            SELECT
                p.ProductId,
                p.ProductName,
                p.Emoji,
                p.ImageUrl,
                p.SoldCount,
                p.Price,
                c.CategoryName
            FROM Products p
            LEFT JOIN Categories c ON p.CategoryId = c.CategoryId
            ORDER BY p.SoldCount DESC
            LIMIT 5
        """)
        return [{"id": r[0], "name": r[1], "emoji": r[2] or "📦",
                 "image_url": r[3], "sold": r[4] or 0,
                 "price": float(r[5] or 0), "category": r[6] or "—"}
                for r in cursor.fetchall()]

    def _don_gan_day_chung(self, cursor):
        """5 đơn hàng gần nhất toàn shop."""
        cursor.execute("""
            SELECT
                o.OrderId,
                o.ReceiverName,
                o.TotalAmount,
                o.Status,
                o.CreatedAt,
                u.FullName
            FROM Orders o
            LEFT JOIN Users u ON o.UserId = u.UserId
            ORDER BY o.CreatedAt DESC
            LIMIT 5
        """)
        return [{"order_id": r[0], "receiver_name": r[1],
                 "customer_name": r[5] or "—",
                 "total_amount": float(r[2] or 0), "status": r[3],
                 "created_at": str(r[4]) if r[4] else ""}
                for r in cursor.fetchall()]

    def lay_doanh_thu_theo_thang(self, year):
        """Doanh thu 12 tháng của đơn Completed (list thuần, lỗi trả [])."""
        conn = DBconnection().get_connection()
        if conn is None:
            return []
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT
                    MONTH(CreatedAt) AS thang,
                    COALESCE(SUM(TotalAmount), 0) AS doanh_thu,
                    COUNT(*) AS so_don
                FROM Orders
                WHERE YEAR(CreatedAt) = %s
                  AND Status = 'Completed'
                GROUP BY MONTH(CreatedAt)
                ORDER BY thang
            """, (year,))
            return self._du_12_thang_chung(cursor.fetchall())
        except Exception as e:
            logger.exception("Lỗi doanh thu theo tháng: %s", e)
            return []
        finally:
            cursor.close()
            conn.close()

    def _du_12_thang_chung(self, rows):
        """Dựng đủ 12 tháng từ rows doanh thu chung."""
        data = {i: {"thang": i, "doanh_thu": 0, "so_don": 0} for i in range(1, 13)}
        for r in rows:
            data[int(r[0])] = {"thang": int(r[0]), "doanh_thu": float(r[1] or 0),
                               "so_don": int(r[2] or 0)}
        return list(data.values())

    def lay_don_hang_cua_seller(self, store_id):
        """Lấy đơn có sản phẩm thuộc shop kèm items của shop."""
        conn = DBconnection().get_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        try:
            cursor.execute(self._sql_don_cua_seller(), (store_id,))
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [self._nap_items_cua_store(conn, columns, row, store_id)
                    for row in rows]
        except Exception as e:
            logger.exception("Lỗi lay_don_hang_cua_seller: %s", e)
            return []
        finally:
            cursor.close()
            conn.close()

    def _sql_don_cua_seller(self):
        """Câu lệnh lấy đơn có ít nhất 1 sản phẩm thuộc shop."""
        return """
        SELECT DISTINCT
            o.OrderId, o.Status, o.ShippingFee, o.UserId,
            u.FullName   AS CustomerName,
            o.ReceiverName, o.ReceiverPhone, o.ShippingAddress,
            o.PaymentMethod, o.SubTotal, o.DiscountAmount,
            o.TotalAmount, o.CreatedAt, o.Note AS Note
        FROM Orders o
        LEFT JOIN Users u ON o.UserId = u.UserId
        INNER JOIN OrderItems oi ON o.OrderId = oi.OrderId
        INNER JOIN Products p   ON oi.ProductId = p.ProductId
        WHERE p.StoreId = %s
        ORDER BY o.CreatedAt DESC
        """

    def _nap_items_cua_store(self, conn, columns, row, store_id):
        """Gắn items thuộc shop vào dict đơn và chuẩn hóa ngày."""
        don = dict(zip(columns, row))
        cursor2 = conn.cursor()
        try:
            cursor2.execute("""
                SELECT oi.OrderItemId, oi.OrderId, oi.ProductId,
                       oi.ProductName, oi.Emoji, oi.Quantity,
                       oi.UnitPrice, oi.TotalPrice
                FROM OrderItems oi
                INNER JOIN Products p ON oi.ProductId = p.ProductId
                WHERE oi.OrderId = %s AND p.StoreId = %s
            """, (don["OrderId"], store_id))
            item_rows = cursor2.fetchall()
            item_columns = [col[0] for col in cursor2.description]
            don["Items"] = [dict(zip(item_columns, ir)) for ir in item_rows]
        finally:
            cursor2.close()
        if don.get("CreatedAt"):
            don["CreatedAt"] = str(don["CreatedAt"])
        return don

    def lay_trang_thai(self, order_id):
        """Lấy Status hiện tại của đơn để kiểm tra luồng seller."""
        conn = DBconnection().get_connection()
        if not conn:
            return None
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT Status FROM Orders WHERE OrderId = %s", (order_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.exception("Lỗi lay_trang_thai: %s", e)
            return None
        finally:
            cursor.close()
            conn.close()

    def don_thuoc_store(self, order_id, store_id):
        """Kiểm tra đơn có chứa sản phẩm của store hay không."""
        conn = DBconnection().get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM OrderItems oi
                    JOIN Products p ON oi.ProductId = p.ProductId
                    WHERE oi.OrderId = %s AND p.StoreId = %s
                )
            """, (order_id, store_id))
            row = cursor.fetchone()
            return bool(row[0]) if row else False
        except Exception as e:
            logger.exception("Lỗi don_thuoc_store: %s", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def lay_thong_ke_cua_seller(self, store_id):
        """Thống kê shop theo items thuộc store, loại Cancelled."""
        conn = DBconnection().get_connection()
        if not conn:
            return {}
        cursor = conn.cursor()
        try:
            tong = self._thong_ke_chinh_cua_store(cursor, store_id)
            tong["top_san_pham"] = self._top_sp_cua_store(cursor, store_id)
            tong["don_gan_day"] = self._don_gan_day_cua_store(cursor, store_id)
            return tong
        except Exception as e:
            logger.exception("Lỗi lay_thong_ke_cua_seller: %s", e)
            return {}
        finally:
            cursor.close()
            conn.close()

    def _thong_ke_chinh_cua_store(self, cursor, store_id):
        """Tổng doanh thu và đếm đơn theo trạng thái của 1 store."""
        cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN o.Status <> 'Cancelled'
                    THEN oi.Quantity * oi.UnitPrice ELSE 0 END), 0) AS doanh_thu,
                COUNT(DISTINCT o.OrderId) AS tong_don,
                SUM(CASE WHEN o.Status = 'Pending' THEN 1 ELSE 0 END) AS cho_duyet,
                SUM(CASE WHEN o.Status = 'Shipping' THEN 1 ELSE 0 END) AS dang_giao,
                SUM(CASE WHEN o.Status = 'Completed' THEN 1 ELSE 0 END) AS hoan_thanh,
                SUM(CASE WHEN o.Status = 'Cancelled' THEN 1 ELSE 0 END) AS da_huy
            FROM Orders o
            JOIN OrderItems oi ON o.OrderId = oi.OrderId
            JOIN Products p ON oi.ProductId = p.ProductId
            WHERE p.StoreId = %s
        """, (store_id,))
        row = cursor.fetchone()
        return {"doanh_thu": float(row[0] or 0), "tong_don": int(row[1] or 0),
                "cho_duyet": int(row[2] or 0), "dang_giao": int(row[3] or 0),
                "hoan_thanh": int(row[4] or 0), "da_huy": int(row[5] or 0)}

    def _top_sp_cua_store(self, cursor, store_id):
        """Top 5 sản phẩm bán chạy của 1 store."""
        cursor.execute("""
            SELECT
                p.ProductId, p.ProductName, p.SoldCount, p.Price
            FROM Products p
            WHERE p.StoreId = %s
            ORDER BY p.SoldCount DESC
            LIMIT %s
        """, (store_id, 5))
        return [{"id": r[0], "name": r[1], "sold": r[2] or 0,
                 "price": float(r[3] or 0)} for r in cursor.fetchall()]

    def _don_gan_day_cua_store(self, cursor, store_id):
        """5 đơn gần nhất có sản phẩm của 1 store."""
        # SQL Server: SELECT TOP (?) ...  →  MySQL: LIMIT ở cuối câu lệnh.
        # DISTINCT để 1 đơn có nhiều item của shop không bị lặp lại.
        cursor.execute("""
            SELECT DISTINCT
                o.OrderId, o.TotalAmount, o.Status, o.CreatedAt
            FROM Orders o
            JOIN OrderItems oi ON o.OrderId = oi.OrderId
            JOIN Products p ON oi.ProductId = p.ProductId
            WHERE p.StoreId = %s
            ORDER BY o.CreatedAt DESC
            LIMIT %s
        """, (store_id, 5))
        return [{"order_id": r[0], "total_amount": float(r[1] or 0),
                 "status": r[2], "created_at": str(r[3]) if r[3] else ""}
                for r in cursor.fetchall()]

    def lay_doanh_thu_seller_theo_thang(self, store_id, year):
        """Doanh thu 12 tháng của shop, chỉ đơn Completed có sản phẩm store."""
        conn = DBconnection().get_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT MONTH(o.CreatedAt) AS thang,
                    COALESCE(SUM(oi.Quantity * oi.UnitPrice), 0) AS doanh_thu,
                    COUNT(DISTINCT o.OrderId) AS so_don
                FROM Orders o
                JOIN OrderItems oi ON o.OrderId = oi.OrderId
                JOIN Products p ON oi.ProductId = p.ProductId
                WHERE p.StoreId = %s AND YEAR(o.CreatedAt) = %s
                    AND o.Status = 'Completed'
                GROUP BY MONTH(o.CreatedAt)
            """, (store_id, year))
            return self._du_12_thang_seller(cursor.fetchall())
        except Exception as e:
            logger.exception("Lỗi lay_doanh_thu_seller_theo_thang: %s", e)
            return []
        finally:
            cursor.close()
            conn.close()

    def _du_12_thang_seller(self, rows):
        """Dựng đủ 12 tháng từ rows doanh thu của seller."""
        data = {i: {"thang": i, "doanh_thu": 0, "so_don": 0} for i in range(1, 13)}
        for r in rows:
            data[int(r[0])] = {"thang": int(r[0]), "doanh_thu": float(r[1] or 0),
                               "so_don": int(r[2] or 0)}
        return list(data.values())

    def lay_chi_tiet_don_hang(self, order_id):
        """Đọc 1 đơn kèm items để dùng hóa đơn (ownership check ở BUS)."""
        conn = DBconnection().get_connection()
        if not conn:
            return None
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM Orders WHERE OrderId = %s", (int(order_id),))
            row = cursor.fetchone()
            if not row:
                return None
            columns = [col[0] for col in cursor.description]
            don = dict(zip(columns, row))
            items = self._lay_items_theo_id(cursor, int(order_id))
            if don.get("CreatedAt"):
                don["CreatedAt"] = str(don["CreatedAt"])
            if don.get("UpdatedAt"):
                don["UpdatedAt"] = str(don["UpdatedAt"])
            return {"don": don, "items": items}
        except Exception as e:
            logger.exception("Lỗi lay_chi_tiet_don_hang: %s", e)
            return None
        finally:
            cursor.close()
            conn.close()

    def _lay_items_theo_id(self, cursor, order_id):
        """Đọc items của đơn bằng cursor đang mở sẵn."""
        cursor.execute("SELECT * FROM OrderItems WHERE OrderId = %s", (order_id,))
        item_rows = cursor.fetchall()
        item_columns = [col[0] for col in cursor.description]
        return [dict(zip(item_columns, ir)) for ir in item_rows]

    def lay_store_ids_cua_san_pham(self, product_ids):
        """Trả dict {ProductId: StoreId} của các sản phẩm trong đơn (nhóm theo shop)."""
        if not product_ids:
            return {}
        conn = DBconnection().get_connection()
        if not conn:
            return {}
        cursor = conn.cursor()
        try:
            placeholders = ",".join(["%s"] * len(product_ids))
            # Tham số hóa được kiểm soát: placeholders chỉ sinh từ số lượng id
            cursor.execute(
                f"SELECT ProductId, StoreId FROM Products WHERE ProductId IN ({placeholders})",
                tuple(product_ids)
            )
            return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            logger.exception("Lỗi lay_store_ids_cua_san_pham: %s", e)
            return {}
        finally:
            cursor.close()
            conn.close()

    def lay_ten_cua_cac_store(self, store_ids):
        """Trả dict {StoreId: StoreName} của các shop trong đơn (011 US2)."""
        if not store_ids:
            return {}
        conn = DBconnection().get_connection()
        if not conn:
            return {}
        cursor = conn.cursor()
        try:
            placeholders = ",".join(["%s"] * len(store_ids))
            cursor.execute(
                f"SELECT StoreId, StoreName FROM Stores WHERE StoreId IN ({placeholders})",
                tuple(store_ids)
            )
            return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            logger.exception("Lỗi lay_ten_cua_cac_store: %s", e)
            return {}
        finally:
            cursor.close()
            conn.close()