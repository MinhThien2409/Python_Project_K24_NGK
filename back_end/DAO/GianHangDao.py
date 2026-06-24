from back_end.DBconnection import DBconnection
from back_end.Model.GianHang import GianHang
from back_end.Model.YeuCau import YeuCau

class GianHangDao:

    # ── STORES ──────────────────────────────────────────────────────────────

    def them_gianhang(self, gianhang: GianHang):
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
            print("Lỗi thêm gian hàng:", e)
            return False
        finally:
            cursor.close(); conn.close()

    def cap_nhat_gianhang(self, gianhang: GianHang):
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
            print("Lỗi cập nhật gian hàng:", e)
            return False
        finally:
            cursor.close(); conn.close()

    def xoa_gianhang(self, StoreId):
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Stores WHERE StoreId=?", (StoreId,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Lỗi xoá gian hàng:", e)
            return False
        finally:
            cursor.close(); conn.close()

    # ── SELLER REQUESTS ─────────────────────────────────────────────────────

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
            print("Lỗi gửi yêu cầu:", e)
            return False
        finally:
            cursor.close(); conn.close()

    def lay_danh_sach_yeu_cau(self):
        """Admin xem danh sách đơn chờ duyệt"""
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
                    "created_at":    str(row.CreatedAt) if row.CreatedAt else ""
                }
                for row in rows
            ]
        except Exception as e:
            print("Lỗi lấy danh sách yêu cầu:", e)
            return []
        finally:
            cursor.close(); conn.close()

    def duyet_yeu_cau(self, request_id, reviewed_by):
        """Admin duyệt → cập nhật Status + tạo Store + đổi Role user"""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            # 1. Lấy thông tin đơn
            cursor.execute(
                "SELECT * FROM SellerRequests WHERE RequestId=?", (request_id,))
            req = cursor.fetchone()
            if not req: return False

            # 2. Cập nhật trạng thái đơn
            cursor.execute("""
                UPDATE SellerRequests
                SET Status='approved', ReviewedBy=?, ReviewedAt=GETDATE()
                WHERE RequestId=?
            """, (reviewed_by, request_id))

            # 3. Tạo Stores mới từ dữ liệu đơn
            cursor.execute("""
                INSERT INTO Stores
                    (StoreName, UserId, Phone, Category, Description, IsActive)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (req.ShopName, req.UserId, req.BusinessPhone,
                  req.Category, req.Description))

            # 4. Đổi Role user thành Seller (13)
            cursor.execute(
                "UPDATE Users SET Role_id=13 WHERE UserId=?", (req.UserId,))

            conn.commit()
            return True
        except Exception as e:
            print("Lỗi duyệt yêu cầu:", e)
            conn.rollback()
            return False
        finally:
            cursor.close(); conn.close()

    def tu_choi_yeu_cau(self, request_id, reviewed_by, ly_do):
        """Admin từ chối đơn"""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE SellerRequests
                SET Status='rejected', ReviewedBy=?,
                    ReviewedAt=GETDATE(), RejectReason=?
                WHERE RequestId=?
            """, (reviewed_by, ly_do, request_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Lỗi từ chối yêu cầu:", e)
            return False
        finally:
            cursor.close(); conn.close()

    # GianHangDao
    def lay_theo_user(self, user_id):
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
            return {
                "store_id": row.StoreId,
                "store_name": row.StoreName,
                "phone": row.Phone,
                "category": row.Category,
                "description": row.Description
            }
        except Exception as e:
            print("Lỗi lay_theo_user:", e)
            return None
        finally:
            cursor.close();
            conn.close()