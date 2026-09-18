import logging

from back_end.DBconnection import DBconnection
from back_end.Model.User import User  # Chỉ import duy nhất 1 class User

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
        """Đọc 1 dòng user kèm tên vai trò theo username/password."""
        # JOIN Roles lấy tên vai trò trong cùng 1 query (FR-008) — dùng placeholder `?`
        sql = """
            SELECT u.UserId, u.FullName, u.Role_id, u.Address, u.Phone, u.NationalId,
                   COALESCE(u.trang_thai, 'active') AS trang_thai,
                   r.RoleName
            FROM Users u
            LEFT JOIN Roles r ON u.Role_id = r.RoleId
            WHERE u.Username = ? AND u.Password = ?
        """
        cursor.execute(sql, (username, password))
        return cursor.fetchone()

    def _nap_thong_tin_dang_nhap(self, row):
        """Nạp dòng DB thành User, hoặc cờ banned/role_none khi đặc biệt."""
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
        """Xác thực đăng nhập theo username/password."""
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
        """Kiểm tra tên đăng nhập đã tồn tại trong bảng Users chưa."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT UserId FROM Users WHERE Username = ?", (tendangnhap,))
            row = cursor.fetchone()
            return row is not None
        except Exception as e:
            logger.exception("Lỗi kiểm tra tên đăng nhập: %s", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def lay_danh_sach_user(self):
        """Lấy toàn bộ user kèm tên vai trò và trạng thái."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT u.UserId, u.FullName, u.Username, u.Phone,
                       u.Role_id, r.RoleName,
                       COALESCE(u.trang_thai, 'active') AS trang_thai
                FROM Users u
                LEFT JOIN Roles r ON u.Role_id = r.RoleId
                ORDER BY u.UserId
            """)
            rows = cursor.fetchall()
            return [
                {
                    "ma_user": r[0],
                    "ten_user": r[1],
                    "tendangnhap": r[2],
                    "sdt": r[3],
                    "ma_nhom_quyen": r[4],
                    "ten_nhom_quyen": r[5],
                    "trang_thai": r[6]
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
        """Lấy chi tiết một user theo UserId dạng dict."""
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM Users WHERE UserId = ?", (ma_user,)
            )
            row = cursor.fetchone()
            if not row: return None
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))
        except Exception as e:
            logger.exception("Lỗi lay_thong_tin_user: %s", e)
            return None
        finally:
            cursor.close();
            conn.close()

    def dem_admin(self):
        """Đếm số tài khoản Admin (Role_Id=1) cho SC-001."""
        conn = DBconnection.get_connection()
        if conn is None: return 0
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM Users WHERE Role_Id = 1")
            row = cursor.fetchone()
            return int(row[0]) if row else 0
        except Exception as e:
            logger.exception("Lỗi dem_admin: %s", e)
            return 0
        finally:
            cursor.close()
            conn.close()

    def lay_danh_sach_quan_ly(self):
        """Lấy danh sách chỉ Quản lý (Role_Id=2), không trả Password."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT u.UserId, u.FullName, u.Username, u.Phone, u.Address,
                       u.Role_id, r.RoleName,
                       COALESCE(u.trang_thai, 'active') AS trang_thai
                FROM Users u
                LEFT JOIN Roles r ON u.Role_id = r.RoleId
                WHERE u.Role_id = 2 ORDER BY u.UserId
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
        """Thêm người dùng mới vào bảng Users."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()

        try:
            sql = """
                INSERT INTO Users (FullName, Address, Phone, NationalId, Role_id, Username, Password)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (
                user.ten_user,
                user.dia_chi,
                user.sdt,
                user.cmnd,
                user.ma_nhom_quyen,
                user.tendangnhap,
                user.mat_khau
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.exception("Lỗi khi thêm người dùng: %s", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def cap_nhat_user(self, ma_user, ten_user, dia_chi, sdt,cmnd):
        """Cập nhật thông tin cơ bản của user theo UserId."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = "UPDATE Users SET FullName=?, Address=?, Phone=?,NationalId=? WHERE UserId=?"
            cursor.execute(sql, (ten_user, dia_chi, sdt,cmnd, ma_user))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi khi cập nhật User: %s", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def xoa_user(self, ma_user):
        """Xóa cứng user theo UserId."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = "DELETE FROM Users WHERE UserId=?"
            cursor.execute(sql, (ma_user,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi khi xoá User: %s", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def cap_nhat_mat_khau(self, ma_user, mat_khau_moi):
        """Cấp lại mật khẩu cho user (ghi cột Password theo UserId — FR-010)."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Users SET Password=? WHERE UserId=?",
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
        """Cập nhật trạng thái khóa/mở khóa tài khoản theo UserId."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Users SET trang_thai = ? WHERE UserId = ?",
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
        """Thêm tài khoản Quản lý (gán cứng Role_Id=2, trang_thai active)."""
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            sql = """
                INSERT INTO Users (FullName, Address, Phone, Role_id, Username, Password, trang_thai)
                VALUES (?, ?, ?, 2, ?, ?, 'active')
            """
            cursor.execute(sql, (ten_user, dia_chi, sdt, tendangnhap, mat_khau))
            conn.commit()
            cursor.execute("SELECT @@IDENTITY")
            row = cursor.fetchone()
            return int(row[0]) if row and row[0] is not None else True
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
        """Cập nhật Quản lý, chỉ FullName/Address/Phone, điều kiện Role_Id=2."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = "UPDATE Users SET FullName=?, Address=?, Phone=? WHERE UserId=? AND Role_Id=2"
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
        """Xóa cứng Quản lý, điều kiện Role_Id=2."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = "DELETE FROM Users WHERE UserId=? AND Role_Id=2"
            cursor.execute(sql, (ma_user,))
            conn.commit()
            return cursor.rowcount > 0
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
