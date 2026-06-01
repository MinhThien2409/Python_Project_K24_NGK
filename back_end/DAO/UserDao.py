from DBconnection import DBconnection
from Model.User import User  # Chỉ import duy nhất 1 class User


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
                SELECT UserId, FullName, Role_id ,Address,Phone,NationalId
                FROM Users 
                WHERE Username = ? AND Password = ?
            """
            cursor.execute(sql, (username, password))
            row = cursor.fetchone()

            if row:

                return User(
                    ma_user=row.UserId,
                    ten_user=row.FullName,
                    ma_nhom_quyen=row.Role_id,
                    dia_chi=row.Address,
                    sdt=row.Phone,
                    cmnd=row.NationalId
                )
            return None
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

            sql = """
                SELECT u.UserId, u.FullName, u.Address, u.Phone, u.Role_id, r.RoleName, u.Username 
                FROM Users u
                JOIN Roles r ON u.Role_id = r.RoleId
            """
            cursor.execute(sql)
            rows = cursor.fetchall()

            danh_sach_user = []
            for row in rows:
                user_dict = {
                    "ma_user": row.UserId,
                    "ten_user": row.FullName,
                    "dia_chi": row.Address,
                    "sdt": row.Phone,
                    "ma_nhom_quyen": row.Role_id,
                    "ten_nhom_quyen": row.RoleName,
                    "tendangnhap": row.Username
                }
                danh_sach_user.append(user_dict)
            return danh_sach_user
        except Exception as e:
            print("Lỗi khi lấy danh sách User:", e)
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