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
                  AND COALESCE(s.IsActive, 0) = 1
                  AND EXISTS (SELECT 1 FROM Accounts a WHERE a.UserId = s.UserId AND COALESCE(a.trang_thai, 'banned') = 'active')
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
                  AND p.IsActive = 1
                  AND COALESCE(s.IsActive, 0) = 1
                  AND EXISTS (SELECT 1 FROM Accounts a WHERE a.UserId = s.UserId AND COALESCE(a.trang_thai, 'banned') = 'active')
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
                  AND COALESCE(s.IsActive, 0) = 1
                  AND EXISTS (SELECT 1 FROM Accounts a WHERE a.UserId = s.UserId AND COALESCE(a.trang_thai, 'banned') = 'active')
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
                  AND COALESCE(s.IsActive, 0) = 1
                  AND EXISTS (SELECT 1 FROM Accounts a WHERE a.UserId = s.UserId AND COALESCE(a.trang_thai, 'banned') = 'active')
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

    def tim_kiem(self, tu_khoa, category_id=None, min_price=None, max_price=None):
        """Tim san pham theo tu khoa khong phan biet hoa/thuong, chi IsActive=1.

        Ho tro them loc theo khoang gia (min_price/max_price) do BUS truyen
        xuong — min/max da duoc validate, None = khong loc.
        """
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
                WHERE p.IsActive = 1
                  AND COALESCE(s.IsActive, 0) = 1
                  AND EXISTS (SELECT 1 FROM Accounts a WHERE a.UserId = s.UserId AND COALESCE(a.trang_thai, 'banned') = 'active')
                  AND LOWER(p.ProductName) LIKE ?
            """
            params = [kw]
            if category_id not in (None, ""):
                sql += " AND p.CategoryId = ?"
                params.append(int(category_id))
            if min_price is not None:
                sql += " AND p.Price >= ?"
                params.append(float(min_price))
            if max_price is not None:
                sql += " AND p.Price <= ?"
                params.append(float(max_price))
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
                "SELECT Quantity, IsActive, Price, ProductName, Emoji FROM Products WHERE ProductId = %s",
                (int(product_id),))
            row = cursor.fetchone()
            if not row:
                return None
            return {"quantity": row[0] or 0, "is_active": bool(row[1]),
                    "price": float(row[2] or 0), "name": row[3], "emoji": row[4]}
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
                    Emoji       = ?,
                    ImageUrl    = COALESCE(?, ImageUrl),   -- không gửi ảnh thì giữ ảnh cũ
                    CategoryId  = ?
                WHERE ProductId = ? AND StoreId = ?
            """
            cursor.execute(sql, (
                sp.ProductName, sp.Description,
                sp.Price, sp.OldPrice,
                sp.Emoji, sp.ImageUrl,
                sp.CategoryId,
                sp.ProductId, int(store_id)
            ))
            conn.commit()
            # BUS đã kiểm tra quyền sở hữu bằng lay_store_id() → không dựa vào rowcount
            return True
        except Exception as e:
            logger.exception("Lỗi sua_theo_store SanPham: %s", e)
            conn.rollback()
            return False
        finally:
            cursor.close();
            conn.close()

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

    def nhap_hang(self, product_id, store_id, so_luong, nguoi_id,
                  unit_cost=None, note=None, supplier_id=None):
        """Nhập kho + ghi log đầy đủ vào StockReceipts/StockReceiptItems."""
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            # 1. Cộng dồn tồn kho
            cursor.execute(
                "UPDATE Products SET Quantity = Quantity + ? WHERE ProductId = ? AND StoreId = ?",
                (so_luong, product_id, store_id))
            if cursor.rowcount == 0:
                conn.rollback()
                return None

            gia_nhap = float(unit_cost) if unit_cost not in (None, "") else 0
            tong_tien = gia_nhap * so_luong

            # 2. Ghi phiếu nhập (log giao dịch)
            cursor.execute(
                """INSERT INTO StockReceipts
                       (StoreId, SupplierId, SupplierNote, CreatedBy, TotalCost, Note)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (store_id, supplier_id, None, nguoi_id, tong_tien, note))
            receipt_id = cursor.lastrowid

            # 3. Ghi chi tiết dòng hàng nhập
            cursor.execute(
                "INSERT INTO StockReceiptItems (ReceiptId, ProductId, Quantity, UnitCost) VALUES (?, ?, ?, ?)",
                (receipt_id, product_id, so_luong, gia_nhap))

            conn.commit()
            cursor.execute("SELECT Quantity FROM Products WHERE ProductId = ?", (product_id,))
            row = cursor.fetchone()
            return {"quantity": row[0] if row else None, "receipt_id": receipt_id}
        except Exception as e:
            logger.exception("Lỗi nhap_hang SanPham: %s", e)
            conn.rollback()
            return None
        finally:
            cursor.close();
            conn.close()

    def lay_lich_su_nhap_hang(self, store_id, top=50):
        """Lấy log các lần nhập hàng của 1 gian hàng, kèm tên sản phẩm."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            sql = """
                SELECT
                    r.ReceiptId, r.CreatedAt, r.CreatedBy, r.TotalCost, r.Note,
                    i.ProductId, p.ProductName, p.Emoji,
                    i.Quantity, i.UnitCost
                FROM StockReceipts r
                JOIN StockReceiptItems i ON i.ReceiptId = r.ReceiptId
                JOIN Products p           ON p.ProductId = i.ProductId
                WHERE r.StoreId = ?
                ORDER BY r.CreatedAt DESC, r.ReceiptId DESC
                LIMIT ?
            """
            cursor.execute(sql, (int(store_id), int(top)))
            rows = cursor.fetchall()
            ket_qua = []
            for row in rows:
                ket_qua.append({
                    "receipt_id": row.ReceiptId,
                    "created_at": row.CreatedAt.strftime('%d/%m/%Y %H:%M') if row.CreatedAt else None,
                    "created_by": row.CreatedBy,
                    "total_cost": float(row.TotalCost or 0),
                    "note": row.Note or "",
                    "product_id": row.ProductId,
                    "product_name": row.ProductName,
                    "emoji": row.Emoji or "📦",
                    "quantity": row.Quantity,
                    "unit_cost": float(row.UnitCost) if row.UnitCost is not None else None,
                })
            return ket_qua
        except Exception as e:
            logger.exception("Lỗi lay_lich_su_nhap_hang: %s", e)
            return []
        finally:
            cursor.close();
            conn.close()

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

    # ─── PHASE 4: TIM KIEM THEO STORE / TRUNG TEN / NHAP BULK / GIA ────────

    def tim_kiem_theo_store(self, store_id, tu_khoa, limit=10):
        """Phase 4: autocomplete san pham trong store (khong phan biet hoa/thuong)."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            try:
                limit = int(limit or 10)
            except (TypeError, ValueError):
                limit = 10
            limit = max(1, min(limit, 20))
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
                WHERE p.StoreId = ? AND LOWER(p.ProductName) LIKE ?
                ORDER BY p.ProductId DESC
                LIMIT ?
            """
            cursor.execute(sql, (int(store_id), kw, limit))
            rows = cursor.fetchall()
            return [self._to_dict(r) for r in rows]
        except Exception as e:
            logger.exception("Lỗi tim_kiem_theo_store SanPham: %s", e)
            return []
        finally:
            cursor.close(); conn.close()

    def kiem_tra_trung_ten(self, store_id, ten, tru_product_id=None):
        """Phase 4: kiem tra trung ten (case-insensitive) trong cung store."""
        if not ten or not str(ten).strip():
            return False
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = ("SELECT ProductId FROM Products "
                   "WHERE StoreId = ? AND LOWER(ProductName) = LOWER(?)")
            params = [int(store_id), str(ten).strip()]
            if tru_product_id not in (None, ""):
                sql += " AND ProductId <> ?"
                params.append(int(tru_product_id))
            cursor.execute(sql, tuple(params))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.exception("Lỗi kiem_tra_trung_ten SanPham: %s", e)
            return False
        finally:
            cursor.close(); conn.close()

    def tim_theo_ten_trong_store(self, store_id, ten):
        """Phase 4: tim 1 SP theo ten chinh xac (case-insensitive) trong store."""
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
                WHERE p.StoreId = ? AND LOWER(p.ProductName) = LOWER(?)
            """
            cursor.execute(sql, (int(store_id), str(ten).strip()))
            row = cursor.fetchone()
            return self._to_dict(row) if row else None
        except Exception as e:
            logger.exception("Lỗi tim_theo_ten_trong_store SanPham: %s", e)
            return None
        finally:
            cursor.close(); conn.close()

    def nhap_hang_bulk(self, store_id, nguoi_id, items, ghi_chu_chung=None):
        """Phase 4: nhap nhieu dong trong 1 phieu (all-or-nothing).

        items: list dict {product_id, quantity, unit_cost} — da validate o BUS.
        Tra {'receipt_id', 'items': [{product_id, quantity, stock_moi}]}.
        """
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            tong_tien = 0.0
            for it in items:
                gia = float(it.get("unit_cost") or 0)
                tong_tien += gia * int(it["quantity"])
            cursor.execute(
                """INSERT INTO StockReceipts
                       (StoreId, SupplierId, SupplierNote, CreatedBy, TotalCost, Note)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (int(store_id), None, None, nguoi_id, tong_tien, ghi_chu_chung))
            receipt_id = cursor.lastrowid
            ket_qua_items = []
            for it in items:
                pid = int(it["product_id"])
                sl = int(it["quantity"])
                gia = float(it.get("unit_cost") or 0)
                cursor.execute(
                    "UPDATE Products SET Quantity = Quantity + ? "
                    "WHERE ProductId = ? AND StoreId = ?",
                    (sl, pid, int(store_id)))
                if cursor.rowcount == 0:
                    conn.rollback()
                    return None
                cursor.execute(
                    "INSERT INTO StockReceiptItems "
                    "(ReceiptId, ProductId, Quantity, UnitCost) VALUES (?, ?, ?, ?)",
                    (receipt_id, pid, sl, gia))
                cursor.execute(
                    "SELECT Quantity FROM Products WHERE ProductId = ?", (pid,))
                row = cursor.fetchone()
                ket_qua_items.append({
                    "product_id": pid, "quantity": sl,
                    "stock_moi": row[0] if row else None})
            conn.commit()
            return {"receipt_id": receipt_id, "items": ket_qua_items}
        except Exception as e:
            logger.exception("Lỗi nhap_hang_bulk SanPham: %s", e)
            conn.rollback()
            return None
        finally:
            cursor.close();
            conn.close()

    def tao_va_nhap(self, store_id, nguoi_id, ten, so_luong,
                    gia_ban=0, mo_ta=None, category_id=1,
                    emoji=None, image_url=None, gia_nhap=None, ghi_chu=None):
        """Phase 4: tao SP moi tu phieu nhap + nhap kho, 1 giao dich."""
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO Products
                    (ProductName, Description, Price, OldPrice,
                     Quantity, SoldCount, Emoji, ImageUrl,
                     CategoryId, StoreId, IsActive)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(ten).strip(), mo_ta,
                 float(gia_ban or 0), None,
                 0, 0, emoji or EMOJI_MAC_DINH, image_url or None,
                 int(category_id or 1), int(store_id), 1))
            new_id = cursor.lastrowid
            gia_nhap_f = float(gia_nhap) if gia_nhap not in (None, "") else 0
            tong_tien = gia_nhap_f * int(so_luong)
            cursor.execute(
                """INSERT INTO StockReceipts
                       (StoreId, SupplierId, SupplierNote, CreatedBy, TotalCost, Note)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (int(store_id), None, None, nguoi_id, tong_tien, ghi_chu))
            receipt_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO StockReceiptItems "
                "(ReceiptId, ProductId, Quantity, UnitCost) VALUES (?, ?, ?, ?)",
                (receipt_id, new_id, int(so_luong), gia_nhap_f))
            cursor.execute(
                "UPDATE Products SET Quantity = Quantity + ? "
                "WHERE ProductId = ? AND StoreId = ?",
                (int(so_luong), new_id, int(store_id)))
            conn.commit()
            return {"product_id": new_id, "quantity": int(so_luong),
                    "receipt_id": receipt_id}
        except Exception as e:
            logger.exception("Lỗi tao_va_nhap SanPham: %s", e)
            conn.rollback()
            return None
        finally:
            cursor.close();
            conn.close()

    def cap_nhat_gia(self, product_id, store_id, gia_ban, gia_goc=None):
        """Phase 4: dat truc tiep (Price, OldPrice) voi ownership.

        gia_goc=None → tat giam gia (xoa OldPrice).
        T96: nếu có giá gốc thì OldPrice phải lớn hơn Price > 0.
        """
        try:
            gia_ban = float(gia_ban)
            if gia_ban <= 0:
                return False
            if gia_goc is not None:
                gia_goc = float(gia_goc)
                if gia_goc <= 0 or gia_goc <= gia_ban:
                    return False
        except (TypeError, ValueError):
            return False
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Products SET Price = ?, OldPrice = ? "
                "WHERE ProductId = ? AND StoreId = ?",
                (float(gia_ban),
                 float(gia_goc) if gia_goc is not None else None,
                 int(product_id), int(store_id)))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi cap_nhat_gia SanPham: %s", e)
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
