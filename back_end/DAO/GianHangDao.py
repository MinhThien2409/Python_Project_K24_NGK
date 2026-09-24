import logging

from back_end.DBconnection import DBconnection
from back_end.Model.GianHang import GianHang
from back_end.Model.YeuCau import YeuCau

logger = logging.getLogger(__name__)

# ─── Hằng số dùng chung (T048) ───────────────────────────────────────────────
ROLE_SELLER = 3
TRU_STORE_ID_MAC_DINH = -1

KET_QUA_OK = "ok"
KET_QUA_DA_XU_LY = "da_xu_ly"
KET_QUA_KHONG_TIM_THAY = "khong_tim_thay"
KET_QUA_DA_LA_SELLER = "da_la_seller"


class GianHangDao:

    # ─── ĐỌC ───

    def lay_danh_sach_yeu_cau(self):
        """Quản lý/Admin xem danh sách đơn đăng ký bán hàng (kèm thông tin xét duyệt)"""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            sql = """
                SELECT sr.*, u.FullName
                FROM SellerRequests sr
                JOIN Users u ON sr.UserId = u.UserId
                ORDER BY sr.CreatedAt DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [
                {
                    "request_id":    row.RequestId,
                    "user_id":       row.UserId,
                    "ten_user":      row.FullName,
                    "shop_name":     row.ShopName,
                    "phone":         row.BusinessPhone,
                    "category":      row.Category,
                    "description":   row.Description,
                    "national_id":   row.NationalId,
                    "status":        row.Status,
                    "created_at":    str(row.CreatedAt) if row.CreatedAt else "",
                    "reviewed_by":   row.ReviewedBy,
                    "reviewed_at":   str(row.ReviewedAt) if row.ReviewedAt else None,
                    "reject_reason": row.RejectReason
                }
                for row in rows
            ]
        except Exception as e:
            logger.exception("Lỗi lấy danh sách yêu cầu: %s", e)
            return []
        finally:
            cursor.close(); conn.close()

    # GianHangDao
    def lay_theo_user(self, user_id):
        """Lấy gian hàng đang hoạt động của một user."""
        conn = DBconnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM Stores WHERE UserId = ? AND IsActive = 1",
                (user_id,)
            )
            row = cursor.fetchone()
            if not row: return None
            cursor= conn.cursor()
            lay = lambda *ten: next(
                (getattr(row, t, None) for t in ten if hasattr(row, t)), None)
            return {
                "store_id": lay("StoreId"),
                "store_name": lay("StoreName"),
                "phone": lay("Phone"),
                "category": lay("Category"),
                "description": lay("Description"),
                "tham_nien": lay("ThamNien"),
            }
        except Exception as e:
            logger.exception("Lỗi lay_theo_user: %s", e)
            return None
        finally:
            cursor.close();
            conn.close()

    def kiem_tra_ten_shop_trung(self, ten_shop, tru_store_id=None):
        """Kiem tra ten shop da co nguoi dung (tru shop hien tai)."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT StoreId FROM Stores WHERE StoreName = ? AND StoreId <> ?",
                (ten_shop, tru_store_id or TRU_STORE_ID_MAC_DINH))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.exception("Lỗi kiem_tra_ten_shop_trung: %s", e)
            return False
        finally:
            cursor.close(); conn.close()

    # ─── GHI ───

    def them_gianhang(self, gianhang: GianHang):
        """Thêm gian hàng mới vào bảng Stores."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = """
                INSERT INTO Stores
                    (StoreName, Address, UserId, Phone, Category, Description, IsActive)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """
            cursor.execute(sql, (
                gianhang.StoreName, gianhang.Address, gianhang.UserId,
                gianhang.Phone, gianhang.Category, gianhang.Description
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.exception("Lỗi thêm gian hàng: %s", e)
            return False
        finally:
            cursor.close(); conn.close()

    def cap_nhat_gianhang(self, gianhang: GianHang):
        """Cập nhật thông tin gian hàng theo StoreId."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = """
                UPDATE Stores
                SET StoreName=?, Address=?, Phone=?,
                    Category=?, Description=?, IsActive=?
                WHERE StoreId=?
            """
            cursor.execute(sql, (
                gianhang.StoreName, gianhang.Address, gianhang.Phone,
                gianhang.Category, gianhang.Description, gianhang.IsActive,
                gianhang.StoreId
            ))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi cập nhật gian hàng: %s", e)
            return False
        finally:
            cursor.close(); conn.close()

    def xoa_gianhang(self, StoreId):
        """Xóa gian hàng theo StoreId."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Stores WHERE StoreId=?", (StoreId,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi xoá gian hàng: %s", e)
            return False
        finally:
            cursor.close(); conn.close()

    def gui_yeu_cau_ban_hang(self, req: YeuCau):
        """User gửi đơn đăng ký → insert vào SellerRequests"""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = """
                INSERT INTO SellerRequests
                    (UserId, ShopName, BusinessPhone, Category,
                     Description, NationalId, Status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """
            cursor.execute(sql, (
                req.UserId, req.ShopName, req.BusinessPhone,
                req.Category, req.Description, req.NationalId
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.exception("Lỗi gửi yêu cầu: %s", e)
            return False
        finally:
            cursor.close(); conn.close()

    def duyet_yeu_cau(self, request_id, reviewed_by):
        """Duyệt đơn bán hàng: cập nhật Status + tạo Store + nâng quyền Seller trong 1 transaction.

        Chỉ duyệt đơn còn Status='pending' (chống xử lý lặp — FR-007); user đã là Seller
        (Role_Id=3) thì không duyệt lại. Trả mã 'ok'|'da_xu_ly'|'khong_tim_thay'|'da_la_seller'.
        """
        conn = DBconnection.get_connection()
        if conn is None: return KET_QUA_KHONG_TIM_THAY
        cursor = conn.cursor()
        try:
            req, loi = self._khoa_don_cho_duyet(cursor, request_id, reviewed_by)
            if loi:
                return loi
            loi = self._tao_store_va_nang_quyen(cursor, req)
            if loi:
                return loi
            conn.commit()
            return KET_QUA_OK
        except Exception as e:
            logger.exception("Lỗi duyệt yêu cầu: %s", e)
            conn.rollback()
            return KET_QUA_KHONG_TIM_THAY
        finally:
            cursor.close(); conn.close()

    def _khoa_don_cho_duyet(self, cursor, request_id, reviewed_by):
        """Khóa đơn pending (guard Status), trả (đơn, mã lỗi)."""
        # 0. Xác nhận đơn tồn tại trước (phân biệt 'khong_tim_thay' với 'da_xu_ly')
        cursor.execute(
            "SELECT * FROM SellerRequests WHERE RequestId=?", (request_id,))
        req = cursor.fetchone()
        if not req: return None, KET_QUA_KHONG_TIM_THAY
        # 1. Cập nhật trạng thái — guard WHERE Status='pending' (atomic, chống cạnh tranh)
        cursor.execute("""
            UPDATE SellerRequests
            SET Status='approved', ReviewedBy=?, ReviewedAt=NOW()
            WHERE RequestId=? AND Status='pending'
        """, (reviewed_by, request_id))
        if cursor.rowcount == 0:
            return None, KET_QUA_DA_XU_LY
        return req, None

    def _tao_store_va_nang_quyen(self, cursor, req):
        """Tạo Stores từ đơn và nâng user thành Seller, trả mã lỗi."""
        # 2. User đã là Seller → không duyệt lại.
        #    T039: Role_Id đã chuyển sang bảng Accounts (008-split-user-table).
        cursor.execute(
            "SELECT Role_Id FROM Accounts WHERE UserId=?", (req.UserId,))
        user = cursor.fetchone()
        if not user: return KET_QUA_KHONG_TIM_THAY
        if user.Role_Id == ROLE_SELLER:
            return KET_QUA_DA_LA_SELLER
        # 3. Tạo Stores mới từ dữ liệu đơn
        cursor.execute("""
            INSERT INTO Stores
                (StoreName, UserId, Phone, Category, Description, IsActive)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (req.ShopName, req.UserId, req.BusinessPhone,
              req.Category, req.Description))
        # 4. Đổi Role user thành Seller (3) — sửa lỗi cũ gán 13 (không tồn tại).
        #    T039: Role_Id đã chuyển sang bảng Accounts (008-split-user-table).
        cursor.execute(
            "UPDATE Accounts SET Role_Id=3 WHERE UserId=?", (req.UserId,))
        return None

    def tu_choi_yeu_cau(self, request_id, reviewed_by, ly_do):
        """Từ chối đơn bán hàng: chỉ áp dụng cho đơn còn Status='pending' (FR-007).

        User giữ nguyên vai trò, không tạo Store. Trả 'ok'|'da_xu_ly'|'khong_tim_thay'.
        """
        conn = DBconnection.get_connection()
        if conn is None: return KET_QUA_KHONG_TIM_THAY
        cursor = conn.cursor()
        try:
            # 0. Xác nhận đơn tồn tại trước (phân biệt 'khong_tim_thay' với 'da_xu_ly')
            cursor.execute(
                "SELECT RequestId FROM SellerRequests WHERE RequestId=?", (request_id,))
            if not cursor.fetchone(): return KET_QUA_KHONG_TIM_THAY

            # 1. Cập nhật trạng thái — guard WHERE Status='pending' (atomic, chống cạnh tranh)
            cursor.execute("""
                UPDATE SellerRequests
                SET Status='rejected', ReviewedBy=?,
                    ReviewedAt=NOW(), RejectReason=?
                WHERE RequestId=? AND Status='pending'
            """, (reviewed_by, ly_do, request_id))
            if cursor.rowcount == 0:
                return KET_QUA_DA_XU_LY

            conn.commit()
            return KET_QUA_OK
        except Exception as e:
            logger.exception("Lỗi từ chối yêu cầu: %s", e)
            conn.rollback()
            return KET_QUA_KHONG_TIM_THAY
        finally:
            cursor.close(); conn.close()

    def cap_nhat_trang_shop(self, store_id, ten, gioi_thieu, tham_nien):
        """Cap nhat ten/gioi thieu/tham nien cua shop."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Stores SET StoreName = ?, Description = ?, ThamNien = ? WHERE StoreId = ?",
                (ten, gioi_thieu, tham_nien, store_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi cap_nhat_trang_shop: %s", e)
            conn.rollback()
            return False
        finally:
            cursor.close(); conn.close()
