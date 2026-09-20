# -*- coding: utf-8 -*-
"""UserDao — truy cập Users (hồ sơ) + Accounts (đăng nhập), 008-split-user-table.

Sau khi tách bảng:
  * Users   : UserId, FullName, Address, Phone, NationalId  (hồ sơ)
  * Accounts: AccountId, UserId(UNIQUE 1-1), Username(UNIQUE),
              Password, Role_Id, trang_thai                  (đăng nhập)
Mọi truy vấn đọc lấy thông tin đăng nhập đều JOIN `Accounts`; mọi truy vấn ghi
vào 1 hồ sơ mới đều chèn CẢ HAI bảng trong một giao dịch (cursor.lastrowid để
liên kết 1-1, thay `SELECT @@IDENTITY` cũ — xem data-model.md mục 9).
"""

import logging

from back_end.DBconnection import DBconnection
from back_end.Model.User import User  # Hồ sơ
from back_end.Model.TaiKhoan import TaiKhoan  # Tài khoản đăng nhập

logger = logging.getLogger(__name__)

# ─── Hằng số dùng chung (T048) ───────────────────────────────────────────────
ROLE_ADMIN = 1
ROLE_QUAN_LY = 2
ROLE_SELLER = 3
ROLE_CUSTOMER = 4
TRANG_THAI_BI_KHOA = "banned"

TEN_VAI_TRO_THEO_ID = {
    ROLE_ADMIN: "Admin",
    ROLE_QUAN_LY: "Quản lý",
    ROLE_SELLER: "Seller",
    ROLE_CUSTOMER: "Customer",
}


class UserDao:

    # ─── ĐỌC ───

    def _doc_user_theo_username(self, cursor, username, password):
        """Đọc 1 dòng user kèm tên vai trò theo username/password.

        T016: JOIN Accounts (Username/Password/Role_Id/trang_thai) + Users
        (hồ sơ) + Roles (tên vai trò) trong cùng 1 query (FR-008); giữ nguyên
        alias cột (UserId, FullName, Role_id, trang_thai, RoleName) để không
        đổi khóa JSON ở tầng BUS (accounts-contract.md mục 3).
        """
        sql = """
            SELECT u.UserId, u.FullName, a.Role_Id, u.Address, u.Phone, u.NationalId,
                   COALESCE(a.trang_thai, 'active') AS trang_thai,
                   r.RoleName
            FROM Users u
            JOIN Accounts a ON a.UserId = u.UserId
            LEFT JOIN Roles r ON a.Role_Id = r.RoleId
            WHERE a.Username = ? AND a.Password = ?
        """
        cursor.execute(sql, (username, password))
        return cursor.fetchone()

    def _nap_thong_tin_dang_nhap(self, row):
        """Nạp dòng DB thành User, hoặc cờ banned/role_none khi đặc biệt.

        T017: đọc `Role_Id`/`trang_thai` từ kết quả JOIN (bảng Accounts);
        giữ nguyên thứ tự kiểm tra cờ `banned` → `role_none` → `None`.
        """
        if not row:
            return None
        # ✅ Tài khoản đã bị khóa → không cho đăng nhập
        if row.trang_thai == TRANG_THAI_BI_KHOA:
            return {"banned": True}
        # Role_Id NULL hoặc trỏ tới vai trò không tồn tại → trả cờ role_none để BUS từ chối rõ ràng
        if row.Role_id is None or row.RoleName is None:
            return {"role_none": True}
        return User(
            ma_user=row.UserId,
            ten_user=row.FullName,
            ma_nhom_quyen=row.Role_id,
            dia_chi=row.Address,
            sdt=row.Phone,
            cmnd=row.NationalId
        )

    def dang_nhap(self, username, password):
        """Xác thực đăng nhập theo username/password (JOIN Users+Accounts+Roles)."""
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            row = self._doc_user_theo_username(cursor, username, password)
            return self._nap_thong_tin_dang_nhap(row)
        except Exception as e:
            logger.exception("Lỗi đăng nhập: %s", e)
            return None
        finally:
            cursor.close()
            conn.close()

    def lay_ten_vai_tro_theo_id(self, role_id):
        """Trả tên vai trò chuẩn theo Role_Id (1=Admin, 2=Quản lý, 3=Seller,
        4=Customer); không phải vai trò chuẩn thì trả None."""
        return TEN_VAI_TRO_THEO_ID.get(role_id)

    def kiem_tra_tendangnhap_ton_tai(self, tendangnhap):
        """T025: kiểm tra tên đăng nhập đã tồn tại trong bảng `Accounts` chưa
        (Username duy nhất toàn hệ thống theo Accounts.Username UNIQUE)."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT AccountId FROM Accounts WHERE Username = ?", (tendangnhap,))
            row = cursor.fetchone()
            return row is not None
        except Exception as e:
            logger.exception("Lỗi kiểm tra tên đăng nhập: %s", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def lay_danh_sach_user(self):
        """T033: lấy toàn bộ user kèm tên vai trò và trạng thái — JOIN Accounts
        để lấy Username, Role_Id, trang_thai (không trả Password)."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT u.UserId, u.FullName, a.Username, u.Phone, u.Address,
                       a.Role_Id, r.RoleName,
                       COALESCE(a.trang_thai, 'active') AS trang_thai
                FROM Users u
                JOIN Accounts a ON a.UserId = u.UserId
                LEFT JOIN Roles r ON a.Role_Id = r.RoleId
                ORDER BY u.UserId
            """)
            rows = cursor.fetchall()
            return [
                {
                    "ma_user": r[0],
                    "ten_user": r[1],
                    "tendangnhap": r[2],
                    "sdt": r[3],
                    "dia_chi": r[4],
                    "ma_nhom_quyen": r[5],
                    "ten_nhom_quyen": r[6],
                    "trang_thai": r[7]
                }
                for r in rows
            ]
        except Exception as e:
            logger.exception("Lỗi lay_danh_sach_user: %s", e)
            return []
        finally:
            cursor.close()
            conn.close()

    def lay_thong_tin_user(self, ma_user):
        """T018: lấy chi tiết user theo UserId dạng dict.

        Đổi `SELECT * FROM Users` thành JOIN tường minh `Users` + `Accounts`
        (accounts-contract.md mục 3): trả đủ hồ sơ (`u.*`) lẫn thông tin đăng
        nhập (`Username`, `Password`, `Role_Id`, `trang_thai`) để tầng BUS
        (đổi mật khẩu, kiểm tra quyền...) không cần sửa.
        """
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT u.*, a.Username, a.Password, a.Role_Id, a.trang_thai "
                "FROM Users u "
                "LEFT JOIN Accounts a ON a.UserId = u.UserId "
                "WHERE u.UserId = ?", (ma_user,)
            )
            row = cursor.fetchone()
            if not row: return None
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))
        except Exception as e:
            logger.exception("Lỗi lay_thong_tin_user: %s", e)
            return None
        finally:
            cursor.close()
            conn.close()

    def dem_admin(self):
        """T032: đếm số tài khoản Admin (Role_Id=1) — đếm trên bảng `Accounts`."""
        conn = DBconnection.get_connection()
        if conn is None: return 0
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM Accounts WHERE Role_Id = 1")
            row = cursor.fetchone()
            return int(row[0]) if row else 0
        except Exception as e:
            logger.exception("Lỗi dem_admin: %s", e)
            return 0
        finally:
            cursor.close()
            conn.close()

    def lay_danh_sach_quan_ly(self):
        """T034: danh sách chỉ Quản lý (Role_Id=2) — JOIN Accounts, lọc trên
        bảng `Accounts`, không trả Password."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT u.UserId, u.FullName, a.Username, u.Phone, u.Address,
                       a.Role_Id, r.RoleName,
                       COALESCE(a.trang_thai, 'active') AS trang_thai
                FROM Users u
                JOIN Accounts a ON a.UserId = u.UserId
                LEFT JOIN Roles r ON a.Role_Id = r.RoleId
                WHERE a.Role_Id = 2 ORDER BY u.UserId
            """)
            rows = cursor.fetchall()
            return [
                {
                    "ma_user": r[0],
                    "ten_user": r[1],
                    "tendangnhap": r[2],
                    "sdt": r[3],
                    "dia_chi": r[4],
                    "ma_nhom_quyen": r[5],
                    "ten_nhom_quyen": r[6],
                    "trang_thai": r[7]
                }
                for r in rows
            ]
        except Exception as e:
            logger.exception("Lỗi lay_danh_sach_quan_ly: %s", e)
            return []
        finally:
            cursor.close()
            conn.close()

    # ─── GHI ───

    def them_user(self, user: User):
        """T024: thêm người dùng — chèn Users (hồ sơ) → `cursor.lastrowid` → chèn
        Accounts (đăng nhập) trong MỘT giao dịch; không để lại hồ sơ mồ côi."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            # 1. Hồ sơ (Users) — bảng KHÔNG còn cột đăng nhập.
            cursor.execute(
                "INSERT INTO Users (FullName, Address, Phone, NationalId) "
                "VALUES (?, ?, ?, ?)",
                (user.ten_user, user.dia_chi, user.sdt, user.cmnd)
            )
            ma_user = cursor.lastrowid
            # 2. Tài khoản (Accounts) — liên kết 1-1 qua UserId.
            role_id = user.ma_nhom_quyen if user.ma_nhom_quyen else ROLE_CUSTOMER
            tai_khoan = TaiKhoan(
                ma_user=ma_user, tendangnhap=user.tendangnhap,
                mat_khau=user.mat_khau, ma_nhom_quyen=role_id, trang_thai="active",
            )
            cursor.execute(
                "INSERT INTO Accounts (UserId, Username, Password, Role_Id, trang_thai) "
                "VALUES (?, ?, ?, ?, ?)",
                (tai_khoan.ma_user, tai_khoan.tendangnhap, tai_khoan.mat_khau,
                 tai_khoan.ma_nhom_quyen, tai_khoan.trang_thai)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.exception("Lỗi khi thêm người dùng: %s", e)
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def cap_nhat_user(self, ma_user, ten_user, dia_chi, sdt, cmnd):
        """T028: cập nhật thông tin cơ bản (hồ sơ) của user theo UserId.

        KHÔNG cần sửa cho spec 008: truy vấn chỉ chạm bảng `Users`
        (FullName/Address/Phone/NationalId) — các cột ấy vẫn ở `Users` sau khi
        tách (data-model.md mục 2). Thông tin đăng nhập không bị đụng tới.
        """
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = "UPDATE Users SET FullName=?, Address=?, Phone=?, NationalId=? WHERE UserId=?"
            cursor.execute(sql, (ten_user, dia_chi, sdt, cmnd, ma_user))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi khi cập nhật User: %s", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def xoa_user(self, ma_user):
        """T027: xóa cứng user theo UserId — xoá `Accounts` TRƯỚC rồi `Users`,
        trong một giao dịch (FK_Accounts_Users không ON DELETE CASCADE), không
        để lại dòng mồ côi ở hai bảng."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Accounts WHERE UserId=?", (ma_user,))
            cursor.execute("DELETE FROM Users WHERE UserId=?", (ma_user,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi khi xoá User: %s", e)
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def cap_nhat_mat_khau(self, ma_user, mat_khau_moi):
        """T026: cấp lại mật khẩu — `UPDATE` trên bảng `Accounts` theo `UserId`
        (cột Password đã chuyển sang Accounts; FR-010)."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Accounts SET Password=? WHERE UserId=?",
                (mat_khau_moi, ma_user)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi cap_nhat_mat_khau: %s", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def cap_nhat_trang_thai(self, ma_user, trang_thai):
        """T035: cập nhật khóa/mở khóa — `UPDATE` trên bảng `Accounts`
        (cột trang_thai đã chuyển sang Accounts)."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Accounts SET trang_thai = ? WHERE UserId = ?",
                (trang_thai, ma_user)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi cap_nhat_trang_thai: %s", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def them_quan_ly(self, ten_user, dia_chi, sdt, tendangnhap, mat_khau):
        """T036: thêm tài khoản Quản lý — chèn `Users` (hồ sơ) → `cursor.lastrowid`
        → chèn `Accounts` (Role_Id=2, trang_thai='active'), trong một giao dịch;
        trả `UserId` mới (thay `SELECT @@IDENTITY` — cú pháp SQL Server cũ)."""
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Users (FullName, Address, Phone) VALUES (?, ?, ?)",
                (ten_user, dia_chi, sdt)
            )
            ma_user = cursor.lastrowid
            cursor.execute(
                "INSERT INTO Accounts (UserId, Username, Password, Role_Id, trang_thai) "
                "VALUES (?, ?, ?, 2, 'active')",
                (ma_user, tendangnhap, mat_khau)
            )
            conn.commit()
            return int(ma_user)
        except Exception as e:
            logger.exception("Lỗi khi thêm quản lý: %s", e)
            try:
                conn.rollback()
            except Exception:
                pass
            return None
        finally:
            cursor.close()
            conn.close()

    def cap_nhat_quan_ly(self, ma_user, ten_user, dia_chi, sdt):
        """T037: cập nhật Quản lý — chỉ FullName/Address/Phone; điều kiện
        `Role_Id=2` kiểm tra qua bảng `Accounts` (JOIN trong WHERE)."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = """
                UPDATE Users SET FullName=?, Address=?, Phone=?
                WHERE UserId = ?
                  AND EXISTS (SELECT 1 FROM Accounts a
                              WHERE a.UserId = Users.UserId AND a.Role_Id = 2)
            """
            cursor.execute(sql, (ten_user, dia_chi, sdt, ma_user))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi khi cập nhật quản lý: %s", e)
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            cursor.close()
            conn.close()

    def xoa_quan_ly(self, ma_user):
        """T038: xóa cứng Quản lý — kiểm tra vai trò qua bảng `Accounts`
        (Role_Id=2), xoá `Accounts` + `Users` trong một giao dịch."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT AccountId FROM Accounts WHERE UserId=? AND Role_Id=2",
                (ma_user,)
            )
            if not cursor.fetchone():
                return False
            cursor.execute("DELETE FROM Accounts WHERE UserId=?", (ma_user,))
            cursor.execute("DELETE FROM Users WHERE UserId=?", (ma_user,))
            conn.commit()
            return True
        except Exception as e:
            logger.exception("Lỗi khi xoá quản lý: %s", e)
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            cursor.close()
            conn.close()