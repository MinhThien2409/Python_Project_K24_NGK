from back_end.DBconnection import DBconnection
from back_end.Model.GioHang import GioHang
from back_end.Model.CartItem import CartItem


class GioHangDao:
    # 1. LẤY HOẶC TẠO MỚI GIỎ HÀNG CHO USER
    def lay_hoac_tao_gio_hang(self, user_id):
        conn = DBconnection().get_connection()
        if not conn: return None
        cursor = conn.cursor()
        try:
            # Kiểm tra xem user đã có giỏ hàng chưa
            cursor.execute("SELECT * FROM Carts WHERE UserId = ?", (user_id,))
            row = cursor.fetchone()

            if row:
                cart_id = row[0]
            else:
                # Nếu chưa có, tạo giỏ hàng mới
                cursor.execute(
                    "INSERT INTO Carts (UserId, TotalAmount, CreatedAt) OUTPUT INSERTED.CartId VALUES (?, 0, GETDATE())",
                    (user_id,))
                cart_id = cursor.fetchone()[0]
                conn.commit()

            return cart_id
        except Exception as e:
            print("Lỗi lấy/tạo giỏ hàng:", e)
            return None
        finally:
            cursor.close()
            conn.close()

    # 2. THÊM HOẶC CẬP NHẬT SỐ LƯỢNG SẢN PHẨM VÀO GIỎ
    def them_vao_gio_hang(self, cart_id, product_id, quantity, unit_price):
        conn = DBconnection().get_connection()
        if not conn: return False
        cursor = conn.cursor()
        try:
            # Kiểm tra sản phẩm đã có trong giỏ chưa
            cursor.execute("SELECT Quantity FROM CartItems WHERE CartId = ? AND ProductId = ?", (cart_id, product_id))
            row = cursor.fetchone()

            if row:
                # Nếu đã có -> Cộng dồn số lượng
                new_qty = row[0] + quantity
                cursor.execute("UPDATE CartItems SET Quantity = ? WHERE CartId = ? AND ProductId = ?",
                               (new_qty, cart_id, product_id))
            else:
                # Nếu chưa có -> Thêm mới
                cursor.execute("INSERT INTO CartItems (CartId, ProductId, Quantity, UnitPrice) VALUES (?, ?, ?, ?)",
                               (cart_id, product_id, quantity, unit_price))

            conn.commit()
            return True
        except Exception as e:
            print("Lỗi thêm chi tiết giỏ hàng:", e)
            return False
        finally:
            cursor.close()
            conn.close()

    # 3. TỰ ĐỘNG TÍNH LẠI TỔNG TIỀN CỦA GIỎ HÀNG
    def cap_nhat_tong_tien(self, cart_id):
        conn = DBconnection().get_connection()
        if not conn: return False
        cursor = conn.cursor()
        try:
            # Tính tổng (Quantity * UnitPrice) từ CartItems và cập nhật ngược lại Carts
            sql = """
            UPDATE Carts 
            SET TotalAmount = ISNULL((SELECT SUM(Quantity * UnitPrice) FROM CartItems WHERE CartId = ?), 0)
            WHERE CartId = ?
            """
            cursor.execute(sql, (cart_id, cart_id))
            conn.commit()
            return True
        except Exception as e:
            print("Lỗi cập nhật tổng tiền giỏ hàng:", e)
            return False
        finally:
            cursor.close()
            conn.close()

    # 4. LẤY TOÀN BỘ DỮ LIỆU GIỎ HÀNG ĐỂ HIỂN THỊ
    def lay_chi_tiet_gio_hang(self, cart_id):
        conn = DBconnection().get_connection()
        if not conn: return []
        cursor = conn.cursor()
        try:
            # Trong thực tế, bạn sẽ JOIN với bảng Products để lấy thêm Tên và Emoji
            sql = "SELECT CartId, ProductId, Quantity, UnitPrice FROM CartItems WHERE CartId = ?"
            cursor.execute(sql, (cart_id,))
            rows = cursor.fetchall()

            items = []
            for row in rows:
                item = CartItem(CartId=row[0], ProductId=row[1], Quantity=row[2], UnitPrice=row[3])
                items.append(item.__dict__)
            return items
        except Exception as e:
            print("Lỗi lấy chi tiết giỏ hàng:", e)
            return []
        finally:
            cursor.close()
            conn.close()

    def xoa_khoi_gio(self, cart_id, product_id):
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM CartItems WHERE CartId=? AND ProductId=?",
                (cart_id, product_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Lỗi xóa khỏi giỏ:", e)
            return False
        finally:
            cursor.close();
            conn.close()

    def cap_nhat_so_luong(self, cart_id, product_id, quantity):
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE CartItems SET Quantity=? WHERE CartId=? AND ProductId=?",
                (quantity, cart_id, product_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Lỗi cập nhật số lượng:", e)
            return False
        finally:
            cursor.close();
            conn.close()