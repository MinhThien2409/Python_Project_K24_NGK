from back_end.DBconnection import DBconnection


class PhanQuyenDao:

    def dong_bo_quyen_xuong_user(self, ma_nhom, ma_chuc_nang, xem, them, sua, xoa):
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()

        try:

            cursor.execute("SELECT UserId FROM Users WHERE Role_id=?", (ma_nhom,))
            users = cursor.fetchall()

            for u in users:
                ma_user = u.UserId

                cursor.execute("SELECT IsCustom FROM Permissions WHERE UserId=? AND ModuleId=?",
                               (ma_user, ma_chuc_nang))
                row = cursor.fetchone()

                if row:

                    if not row.IsCustom:
                        sql_update = """
                            UPDATE Permissions
                            SET CanView=?, CanAdd=?, CanEdit=?, CanDelete=?
                            WHERE UserId=? AND ModuleId=? AND IsCustom=0
                        """
                        cursor.execute(sql_update, (xem, them, sua, xoa, ma_user, ma_chuc_nang))
                else:

                    sql_insert = """
                        INSERT INTO Permissions(UserId, ModuleId, CanView, CanAdd, CanEdit, CanDelete, IsCustom)
                        VALUES (?, ?, ?, ?, ?, ?, 0)
                    """
                    cursor.execute(sql_insert, (ma_user, ma_chuc_nang, xem, them, sua, xoa))


            conn.commit()
            return True
        except Exception as e:
            print("Lỗi đồng bộ quyền: ", e)
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()


    def cap_quyen_ngoai_le_user(self, ma_user, ma_chuc_nang, xem, them, sua, xoa):
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()

        try:
            # 1. Kiểm tra xem quyền này đã tồn tại trong bảng chưa
            cursor.execute("SELECT 1 FROM Permissions WHERE UserId=? AND ModuleId=?", (ma_user, ma_chuc_nang))
            row = cursor.fetchone()

            if row:
                # 2A. Nếu ĐÃ CÓ -> Chạy lệnh UPDATE
                sql_update = """
                    UPDATE Permissions
                    SET CanView=?, CanAdd=?, CanEdit=?, CanDelete=?, IsCustom=1
                    WHERE UserId=? AND ModuleId=?
                """
                cursor.execute(sql_update, (xem, them, sua, xoa, ma_user, ma_chuc_nang))
            else:
                # 2B. Nếu CHƯA CÓ (Bảng rỗng) -> Chạy lệnh INSERT thêm mới
                sql_insert = """
                    INSERT INTO Permissions(UserId, ModuleId, CanView, CanAdd, CanEdit, CanDelete, IsCustom)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """
                cursor.execute(sql_insert, (ma_user, ma_chuc_nang, xem, them, sua, xoa))

            conn.commit()
            return True
        except Exception as e:
            print("Lỗi cấp ngoại lệ:", e)
            return False
        finally:
            cursor.close()
            conn.close()


    def khoi_phuc_ve_quyen_nhom(self, ma_user, ma_chuc_nang, xem_nhom, them_nhom, sua_nhom, xoa_nhom):
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()

        try:
            sql = """
                UPDATE Permissions
                SET CanView=?, CanAdd=?, CanEdit=?, CanDelete=?, IsCustom=0
                WHERE UserId=? AND ModuleId=?
            """
            cursor.execute(sql, (xem_nhom, them_nhom, sua_nhom, xoa_nhom, ma_user, ma_chuc_nang))
            conn.commit()
            return True
        except Exception as e:
            print("Lỗi khôi phục quyền:", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def lay_quyen_cua_user(self, ma_user):
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()

        try:
            # Lấy tất cả các module mà User này đã được cấu hình trong bảng Permissions
            sql = "SELECT ModuleId, CanView, CanAdd, CanEdit, CanDelete FROM Permissions WHERE UserId = ?"
            cursor.execute(sql, (ma_user,))
            rows = cursor.fetchall()

            danh_sach_quyen = []
            for row in rows:
                danh_sach_quyen.append({
                    "ma_chuc_nang": row.ModuleId,
                    "xem": row.CanView,
                    "them": row.CanAdd,
                    "sua": row.CanEdit,
                    "xoa": row.CanDelete
                })
            return danh_sach_quyen
        except Exception as e:
            print("Lỗi lấy quyền user:", e)
            return []
        finally:
            cursor.close()
            conn.close()

    def lay_quyen_cua_nhom(self, ma_nhom):
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()

        try:
            # Lấy quyền mặc định (IsCustom=0) từ 1 user bất kỳ trong nhóm
            # Vì dong_bo_quyen_xuong_user đã đảm bảo tất cả user cùng nhóm
            # có cùng quyền mặc định, nên lấy 1 user là đủ đại diện
            sql = """
                SELECT p.ModuleId, p.CanView, p.CanAdd, p.CanEdit, p.CanDelete
                FROM Permissions p
                WHERE p.IsCustom = 0
                  AND p.UserId = (
                      SELECT TOP 1 UserId 
                      FROM Users 
                      WHERE Role_id = ?
                  )
            """
            cursor.execute(sql, (ma_nhom,))
            rows = cursor.fetchall()

            return [
                {
                    "ma_chuc_nang": row.ModuleId,
                    "xem": bool(row.CanView),
                    "them": bool(row.CanAdd),
                    "sua": bool(row.CanEdit),
                    "xoa": bool(row.CanDelete)
                }
                for row in rows
            ]
        except Exception as e:
            print("Lỗi lấy quyền nhóm:", e)
            return []
        finally:
            cursor.close()
            conn.close()

    def ap_dung_quyen_nhom_cho_user(self, ma_user):
        """Reset toàn bộ quyền của 1 user về đúng quyền nhóm của họ (IsCustom=0)"""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            # Lấy role_id của user này
            cursor.execute("SELECT Role_id FROM Users WHERE UserId = ?", (ma_user,))
            user_row = cursor.fetchone()
            if not user_row: return False
            role_id = user_row.Role_id

            # Lấy quyền mặc định của nhóm (từ user khác cùng nhóm, IsCustom=0)
            cursor.execute("""
                SELECT ModuleId, CanView, CanAdd, CanEdit, CanDelete
                FROM Permissions
                WHERE IsCustom = 0
                  AND UserId = (
                      SELECT TOP 1 UserId FROM Users
                      WHERE Role_id = ? AND UserId != ?
                  )
            """, (role_id, ma_user))
            quyen_nhom = cursor.fetchall()

            # Áp dụng quyền nhóm xuống user, xóa IsCustom
            for q in quyen_nhom:
                cursor.execute("SELECT 1 FROM Permissions WHERE UserId=? AND ModuleId=?",
                               (ma_user, q.ModuleId))
                exists = cursor.fetchone()
                if exists:
                    cursor.execute("""
                        UPDATE Permissions
                        SET CanView=?, CanAdd=?, CanEdit=?, CanDelete=?, IsCustom=0
                        WHERE UserId=? AND ModuleId=?
                    """, (q.CanView, q.CanAdd, q.CanEdit, q.CanDelete, ma_user, q.ModuleId))
                else:
                    cursor.execute("""
                        INSERT INTO Permissions(UserId, ModuleId, CanView, CanAdd, CanEdit, CanDelete, IsCustom)
                        VALUES (?, ?, ?, ?, ?, ?, 0)
                    """, (ma_user, q.ModuleId, q.CanView, q.CanAdd, q.CanEdit, q.CanDelete))

            conn.commit()
            return True
        except Exception as e:
            print("Lỗi áp dụng quyền nhóm:", e)
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()