from back_end.DBconnection import DBconnection
from back_end.Model.User import User  # Chỉ import duy nhất 1 class User


class UserDao:
    def them_user(self, user: User):
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
            print("Lỗi khi thêm người dùng:", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def dang_nhap(self, username, password):
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()

        try:
            sql = """
                SELECT UserId, FullName, Role_id, Address, Phone, NationalId,
                       COALESCE(trang_thai, 'active') AS trang_thai
                FROM Users 
                WHERE Username = ? AND Password = ?
            """
            cursor.execute(sql, (username, password))
            row = cursor.fetchone()

            if not row:
                return None

            # ✅ Tài khoản đã bị khóa → không cho đăng nhập
            if row.trang_thai == 'banned':
                return {"banned": True}

            return User(
                ma_user=row.UserId,
                ten_user=row.FullName,
                ma_nhom_quyen=row.Role_id,
                dia_chi=row.Address,
                sdt=row.Phone,
                cmnd=row.NationalId
            )
        except Exception as e:
            print("Lỗi đăng nhập:", e)
            return None
        finally:
            cursor.close()
            conn.close()


    def kiem_tra_tendangnhap_ton_tai(self, tendangnhap):
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT UserId FROM Users WHERE Username = ?", (tendangnhap,))
            row = cursor.fetchone()
            return row is not None
        except Exception as e:
            print("Lỗi kiểm tra tên đăng nhập:", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def lay_danh_sach_user(self):
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
            print(f"Lỗi lay_danh_sach_user: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    def cap_nhat_user(self, ma_user, ten_user, dia_chi, sdt,cmnd):
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = "UPDATE Users SET FullName=?, Address=?, Phone=?,NationalId=? WHERE UserId=?"
            cursor.execute(sql, (ten_user, dia_chi, sdt,cmnd, ma_user))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Lỗi khi cập nhật User:", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def xoa_user(self, ma_user):
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            sql = "DELETE FROM Users WHERE UserId=?"
            cursor.execute(sql, (ma_user,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Lỗi khi xoá User:", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def cap_nhat_vai_tro(self, ma_user, role_id):
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Users SET Role_id=? WHERE UserId=?",
                (role_id, ma_user)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Lỗi cập nhật vai trò:", e)
            return False
        finally:
            cursor.close();
            conn.close()

    def lay_thong_tin_user(self, ma_user):
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
            print("Lỗi lay_thong_tin_user:", e)
            return None
        finally:
            cursor.close();
            conn.close()

    def cap_nhat_trang_thai(self, ma_user, trang_thai):
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
            print(f"Lỗi cap_nhat_trang_thai: {e}")
            return False
        finally:
            cursor.close()
            conn.close()