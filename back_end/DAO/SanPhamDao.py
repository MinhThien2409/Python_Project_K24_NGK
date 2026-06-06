from back_end.DBconnection import DBconnection
from back_end.Model.SanPham import SanPham


class SanPhamDao:

    # ─── ĐỌC ────────────────────────────────────────────────────────────────

    def lay_tat_ca(self):
        """Lấy toàn bộ sản phẩm đang active, kèm tên danh mục và tên cửa hàng."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            sql = """
                SELECT
                    p.ProductId, p.ProductName, p.Description,
                    p.Price, p.OldPrice, p.Quantity,
                    p.Rating, p.SoldCount, p.Emoji,
                    p.CategoryId, p.StoreId, p.IsActive,
                    c.CategoryName,
                    s.StoreName
                FROM Products p
                LEFT JOIN Categories c ON p.CategoryId = c.CategoryId
                LEFT JOIN Stores     s ON p.StoreId    = s.StoreId
                WHERE p.IsActive = 1
                ORDER BY p.ProductId DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [self._to_dict(r) for r in rows]
        except Exception as e:
            print("Lỗi lay_tat_ca SanPham:", e)
            return []
        finally:
            cursor.close(); conn.close()

    def lay_theo_id(self, product_id):
        """Lấy 1 sản phẩm theo ID."""
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            sql = """
                SELECT
                    p.ProductId, p.ProductName, p.Description,
                    p.Price, p.OldPrice, p.Quantity,
                    p.Rating, p.SoldCount, p.Emoji,
                    p.CategoryId, p.StoreId, p.IsActive,
                    c.CategoryName,
                    s.StoreName
                FROM Products p
                LEFT JOIN Categories c ON p.CategoryId = c.CategoryId
                LEFT JOIN Stores     s ON p.StoreId    = s.StoreId
                WHERE p.ProductId = ?
            """
            cursor.execute(sql, (product_id,))
            row = cursor.fetchone()
            return self._to_dict(row) if row else None
        except Exception as e:
            print("Lỗi lay_theo_id SanPham:", e)
            return None
        finally:
            cursor.close(); conn.close()

    def lay_theo_store(self, store_id):
        """Lấy tất cả sản phẩm của 1 gian hàng (dùng cho Seller Dashboard)."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            sql = """
                SELECT
                    p.ProductId, p.ProductName, p.Description,
                    p.Price, p.OldPrice, p.Quantity,
                    p.Rating, p.SoldCount, p.Emoji,
                    p.CategoryId, p.StoreId, p.IsActive,
                    c.CategoryName,
                    s.StoreName
                FROM Products p
                LEFT JOIN Categories c ON p.CategoryId = c.CategoryId
                LEFT JOIN Stores     s ON p.StoreId    = s.StoreId
                WHERE p.StoreId = ?
                ORDER BY p.ProductId DESC
            """
            cursor.execute(sql, (store_id,))
            rows = cursor.fetchall()
            return [self._to_dict(r) for r in rows]
        except Exception as e:
            print("Lỗi lay_theo_store SanPham:", e)
            return []
        finally:
            cursor.close(); conn.close()

    def lay_ban_chay(self, top=10):
        """Lấy top sản phẩm bán chạy nhất (dùng cho Admin Dashboard)."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            sql = f"""
                SELECT TOP {top}
                    p.ProductId, p.ProductName, p.Description,
                    p.Price, p.OldPrice, p.Quantity,
                    p.Rating, p.SoldCount, p.Emoji,
                    p.CategoryId, p.StoreId, p.IsActive,
                    c.CategoryName,
                    s.StoreName
                FROM Products p
                LEFT JOIN Categories c ON p.CategoryId = c.CategoryId
                LEFT JOIN Stores     s ON p.StoreId    = s.StoreId
                WHERE p.IsActive = 1
                ORDER BY p.SoldCount DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [self._to_dict(r) for r in rows]
        except Exception as e:
            print("Lỗi lay_ban_chay SanPham:", e)
            return []
        finally:
            cursor.close(); conn.close()

    # ─── GHI ────────────────────────────────────────────────────────────────

    def them(self, sp: SanPham):
        """Thêm sản phẩm mới, trả về ProductId vừa tạo."""
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            sql = """
                INSERT INTO Products
                    (ProductName, Description, Price, OldPrice,
                     Quantity, Rating, SoldCount, Emoji,
                     CategoryId, StoreId, IsActive)
                OUTPUT INSERTED.ProductId
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (
                sp.ProductName, sp.Description, sp.Price, sp.OldPrice,
                sp.Quantity,    sp.Rating,      sp.SoldCount, sp.Emoji,
                sp.CategoryId,  sp.StoreId,     sp.IsActive
            ))
            row = cursor.fetchone()
            conn.commit()
            return row[0] if row else None
        except Exception as e:
            print("Lỗi them SanPham:", e)
            conn.rollback()
            return None
        finally:
            cursor.close(); conn.close()

    def sua(self, sp: SanPham):
        """Cập nhật thông tin sản phẩm."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = """
                UPDATE Products
                SET ProductName = ?, Description = ?,
                    Price       = ?, OldPrice    = ?,
                    Quantity    = ?, Rating      = ?,
                    Emoji       = ?, CategoryId  = ?,
                    StoreId     = ?, IsActive    = ?
                WHERE ProductId = ?
            """
            cursor.execute(sql, (
                sp.ProductName, sp.Description,
                sp.Price,       sp.OldPrice,
                sp.Quantity,    sp.Rating,
                sp.Emoji,       sp.CategoryId,
                sp.StoreId,     sp.IsActive,
                sp.ProductId
            ))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Lỗi sua SanPham:", e)
            conn.rollback()
            return False
        finally:
            cursor.close(); conn.close()

    def xoa(self, product_id):
        """Xóa mềm — chỉ đặt IsActive = 0, không xóa khỏi DB."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Products SET IsActive = 0 WHERE ProductId = ?",
                (product_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Lỗi xoa SanPham:", e)
            conn.rollback()
            return False
        finally:
            cursor.close(); conn.close()

    def cap_nhat_so_luong_ban(self, product_id, so_luong_ban_them):
        """Tăng SoldCount và giảm Quantity sau khi đặt hàng thành công."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE Products
                SET SoldCount = SoldCount + ?,
                    Quantity  = Quantity  - ?
                WHERE ProductId = ? AND Quantity >= ?
            """, (so_luong_ban_them, so_luong_ban_them,
                  product_id,        so_luong_ban_them))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Lỗi cap_nhat_so_luong_ban:", e)
            conn.rollback()
            return False
        finally:
            cursor.close(); conn.close()

    # ─── HELPER ─────────────────────────────────────────────────────────────

    def _to_dict(self, row) -> dict:
        """Chuyển row DB thành dict để trả về JSON."""
        return {
            "id"           : row.ProductId,
            "name"         : row.ProductName,
            "description"  : row.Description   or "",
            "price"        : float(row.Price),
            "old_price"    : float(row.OldPrice) if row.OldPrice else None,
            "quantity"     : row.Quantity       or 0,
            "rating"       : float(row.Rating)  if row.Rating   else 4.5,
            "sold"         : row.SoldCount      or 0,
            "emoji"        : row.Emoji          or "📦",
            "category_id"  : row.CategoryId,
            "category_name": row.CategoryName   or "",
            "store_id"     : row.StoreId,
            "shop"         : row.StoreName      or "Pobby Official",
            "is_active"    : bool(row.IsActive)
        }