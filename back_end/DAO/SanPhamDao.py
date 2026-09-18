import logging

from back_end.DBconnection import DBconnection
from back_end.Model.SanPham import SanPham

logger = logging.getLogger(__name__)

# ─── Hằng số dùng chung (T048) ───────────────────────────────────────────────
TOP_MAC_DINH = 10
EMOJI_MAC_DINH = "📦"
SHOP_MAC_DINH = "Pobby Official"


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
                    p.SoldCount, p.Emoji, p.ImageUrl,
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
            logger.exception("Lỗi lay_tat_ca SanPham: %s", e)
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
                    p.SoldCount, p.Emoji, p.ImageUrl,
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
            logger.exception("Lỗi lay_theo_id SanPham: %s", e)
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
                    p.SoldCount, p.Emoji, p.ImageUrl,
                    p.CategoryId, p.StoreId, p.IsActive,
                    c.CategoryName,
                    s.StoreName
                FROM Products p
                LEFT JOIN Categories c ON p.CategoryId = c.CategoryId
                LEFT JOIN Stores     s ON p.StoreId    = s.StoreId
                WHERE p.StoreId = ? AND p.IsActive = 1
                ORDER BY p.ProductId DESC
            """
            cursor.execute(sql, (store_id,))
            rows = cursor.fetchall()
            return [self._to_dict(r) for r in rows]
        except Exception as e:
            logger.exception("Lỗi lay_theo_store SanPham: %s", e)
            return []
        finally:
            cursor.close(); conn.close()

    def lay_ban_chay(self, top=10):
        """Lấy top sản phẩm bán chạy nhất (dùng cho Admin Dashboard)."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            # LIMIT voi top da ep int o BUS/controller — tranh injection (MySQL dialect)
            top = int(top or TOP_MAC_DINH)
            sql = """
                SELECT
                    p.ProductId, p.ProductName, p.Description,
                    p.Price, p.OldPrice, p.Quantity,
                    p.SoldCount, p.Emoji, p.ImageUrl,
                    p.CategoryId, p.StoreId, p.IsActive,
                    c.CategoryName,
                    s.StoreName
                FROM Products p
                LEFT JOIN Categories c ON p.CategoryId = c.CategoryId
                LEFT JOIN Stores     s ON p.StoreId    = s.StoreId
                WHERE p.IsActive = 1
                ORDER BY p.SoldCount DESC
                LIMIT ?
            """
            cursor.execute(sql, (top,))
            rows = cursor.fetchall()
            return [self._to_dict(r) for r in rows]
        except Exception as e:
            logger.exception("Lỗi lay_ban_chay SanPham: %s", e)
            return []
        finally:
            cursor.close(); conn.close()

    def lay_theo_store_ca_an_hien(self, store_id):
        """Lay tat ca SP cua shop ke ca an (Seller Dashboard)."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            sql = """
                SELECT
                    p.ProductId, p.ProductName, p.Description,
                    p.Price, p.OldPrice, p.Quantity,
                    p.SoldCount, p.Emoji, p.ImageUrl,
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
            logger.exception("Lỗi lay_theo_store_ca_an_hien: %s", e)
            return []
        finally:
            cursor.close(); conn.close()

    def lay_store_id(self, product_id):
        """Tra StoreId cua san pham de kiem tra so huu seller."""
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT StoreId FROM Products WHERE ProductId = ?", (product_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.exception("Lỗi lay_store_id SanPham: %s", e)
            return None
        finally:
            cursor.close(); conn.close()

    def tim_kiem(self, tu_khoa, category_id=None):
        """Tim san pham theo tu khoa khong phan biet hoa/thuong, chi IsActive=1."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            kw = f"%{(tu_khoa or '').strip().lower()}%"
            sql = """
                SELECT
                    p.ProductId, p.ProductName, p.Description,
                    p.Price, p.OldPrice, p.Quantity,
                    p.SoldCount, p.Emoji, p.ImageUrl,
                    p.CategoryId, p.StoreId, p.IsActive,
                    c.CategoryName,
                    s.StoreName
                FROM Products p
                LEFT JOIN Categories c ON p.CategoryId = c.CategoryId
                LEFT JOIN Stores     s ON p.StoreId    = s.StoreId
                WHERE p.IsActive = 1 AND LOWER(p.ProductName) LIKE ?
            """
            params = [kw]
            if category_id not in (None, ""):
                sql += " AND p.CategoryId = ?"
                params.append(int(category_id))
            sql += " ORDER BY p.ProductId DESC"
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return [self._to_dict(r) for r in rows]
        except Exception as e:
            logger.exception("Lỗi tim_kiem SanPham: %s", e)
            return []
        finally:
            cursor.close(); conn.close()

    def lay_thong_tin_kho(self, product_id):
        """Doc ton kho + trang thai + gia chuan de gio hang check (1 query)."""
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT Quantity, IsActive, Price FROM Products WHERE ProductId = ?",
                (int(product_id),))
            row = cursor.fetchone()
            if not row:
                return None
            return {"quantity": row[0] or 0, "is_active": bool(row[1]),
                    "price": float(row[2] or 0)}
        except Exception as e:
            logger.exception("Lỗi lay_thong_tin_kho SanPham: %s", e)
            return None
        finally:
            cursor.close(); conn.close()

    def kiem_tra_category_ton_tai(self, category_id):
        """Kiem tra CategoryId co ton tai khong."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT CategoryId FROM Categories WHERE CategoryId = ?", (category_id,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.exception("Lỗi kiem_tra_category: %s", e)
            return False
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
                     Quantity, SoldCount, Emoji, ImageUrl,
                     CategoryId, StoreId, IsActive)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (
                sp.ProductName, sp.Description, sp.Price, sp.OldPrice,
                sp.Quantity,    sp.SoldCount, sp.Emoji, sp.ImageUrl,
                sp.CategoryId,  sp.StoreId,     sp.IsActive
            ))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.exception("Lỗi them SanPham: %s", e)
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
                    Quantity    = ?,
                    Emoji       = ?, ImageUrl = ?, CategoryId  = ?,
                    StoreId     = ?, IsActive    = ?
                WHERE ProductId = ?
            """
            cursor.execute(sql, (
                sp.ProductName, sp.Description,
                sp.Price,       sp.OldPrice,
                sp.Quantity,
                sp.Emoji,  sp.ImageUrl,     sp.CategoryId,
                sp.StoreId,     sp.IsActive,
                sp.ProductId
            ))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi sua SanPham: %s", e)
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
            logger.exception("Lỗi xoa SanPham: %s", e)
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
            logger.exception("Lỗi cap_nhat_so_luong_ban: %s", e)
            conn.rollback()
            return False
        finally:
            cursor.close(); conn.close()

    def sua_theo_store(self, sp: SanPham, store_id):
        """Sua san pham voi ownership WHERE ProductId AND StoreId."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = """
                UPDATE Products
                SET ProductName = ?, Description = ?,
                    Price       = ?, OldPrice    = ?,
                    Quantity    = ?,
                    Emoji       = ?, ImageUrl = ?, CategoryId  = ?,
                    IsActive    = ?
                WHERE ProductId = ? AND StoreId = ?
            """
            cursor.execute(sql, (
                sp.ProductName, sp.Description,
                sp.Price,       sp.OldPrice,
                sp.Quantity,
                sp.Emoji,  sp.ImageUrl,     sp.CategoryId,
                sp.IsActive,
                sp.ProductId, int(store_id)
            ))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi sua_theo_store SanPham: %s", e)
            conn.rollback()
            return False
        finally:
            cursor.close(); conn.close()

    def an_hien_theo_store(self, product_id, store_id, is_active):
        """An/hien san pham voi ownership WHERE ProductId AND StoreId."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Products SET IsActive = ? WHERE ProductId = ? AND StoreId = ?",
                (int(is_active), int(product_id), int(store_id))
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi an_hien_theo_store SanPham: %s", e)
            conn.rollback()
            return False
        finally:
            cursor.close(); conn.close()

    def nhap_hang(self, product_id, store_id, so_luong):
        """Nhap them ton kho cong don atomic Quantity+?."""
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Products SET Quantity = Quantity + ? WHERE ProductId = ? AND StoreId = ?",
                (int(so_luong), int(product_id), int(store_id))
            )
            if cursor.rowcount == 0:
                conn.rollback()
                return None
            cursor.execute(
                "SELECT Quantity FROM Products WHERE ProductId = ?", (int(product_id),))
            row = cursor.fetchone()
            conn.commit()
            return row[0] if row else None
        except Exception as e:
            logger.exception("Lỗi nhap_hang SanPham: %s", e)
            conn.rollback()
            return None
        finally:
            cursor.close(); conn.close()

    def doi_gia(self, product_id, store_id, gia_moi):
        """Doi gia ban, giu OldPrice khi giam gia."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """UPDATE Products
                   SET OldPrice = CASE WHEN Price < ? THEN Price ELSE OldPrice END,
                       Price = ?
                   WHERE ProductId = ? AND StoreId = ?""",
                (float(gia_moi), float(gia_moi), int(product_id), int(store_id))
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi doi_gia SanPham: %s", e)
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
            "sold"         : row.SoldCount      or 0,
            "emoji"        : row.Emoji          or EMOJI_MAC_DINH,
            "image_url"    : row.ImageUrl,
            "category_id"  : row.CategoryId,
            "category_name": row.CategoryName   or "",
            "store_id"     : row.StoreId,
            "shop"         : row.StoreName      or SHOP_MAC_DINH,
            "is_active"    : bool(row.IsActive)
        }
