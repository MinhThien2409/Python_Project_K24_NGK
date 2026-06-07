from back_end.DBconnection import DBconnection
from back_end.Model.DonHang import DonHang
from back_end.Model.OrderItem import OrderItem


class DonHangDao:
    # ==========================================
    # 1. TẠO ĐƠN HÀNG (DÙNG TRANSACTION)
    # ==========================================
    def tao_don_hang(self, order: DonHang, order_items: list):
        conn = DBconnection().get_connection()
        if not conn: return False
        cursor = conn.cursor()
        try:
            sql_order = """
            INSERT INTO Orders (Status, ShippingFee, UserId, ReceiverName, 
                                ReceiverPhone, ShippingAddress, PaymentMethod, 
                                VoucherCode, SubTotal, DiscountAmount, TotalAmount, Note)
            OUTPUT INSERTED.OrderId
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql_order, (
                str(order.Status),
                float(order.ShippingFee or 0),
                int(order.UserId),
                str(order.ReceiverName),
                str(order.ReceiverPhone),
                str(order.ShippingAddress),
                str(order.PaymentMethod),
                str(order.VoucherCode) if order.VoucherCode else None,
                float(order.SubTotal or 0),
                float(order.DiscountAmount or 0),
                float(order.TotalAmount or 0),
                str(order.Note) if order.Note else None
            ))

            new_order_id = cursor.fetchone()[0]

            sql_item = """
            INSERT INTO OrderItems (OrderId, ProductId, ProductName, Emoji, Quantity, UnitPrice, TotalPrice)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            for item in order_items:
                cursor.execute(sql_item, (
                    int(new_order_id),
                    int(item.ProductId),
                    str(item.ProductName or f'Sản phẩm #{item.ProductId}'),
                    str(item.Emoji or '📦'),
                    int(item.Quantity or 0),
                    float(item.UnitPrice or 0),
                    float(item.TotalPrice or 0)
                ))

            conn.commit()
            return new_order_id

        except Exception as e:
            conn.rollback()
            print("Lỗi tạo đơn hàng + chi tiết:", e)
            return False
        finally:
            cursor.close()
            conn.close()
    # ==========================================
    # 2. LẤY ĐƠN THEO USER (KÈM CHI TIẾT SẢN PHẨM)
    # ==========================================
    def lay_don_hang_cua_user(self, ma_user):
        conn = DBconnection().get_connection()
        if not conn: return []
        cursor = conn.cursor()
        try:
            # Lấy toàn bộ đơn hàng của user
            sql_orders = "SELECT * FROM Orders WHERE UserId = ? ORDER BY CreatedAt DESC"
            cursor.execute(sql_orders, (ma_user,))
            rows = cursor.fetchall()

            danh_sach_don = []

            for row in rows:
                dh = DonHang(
                    OrderId=row[0], Status=row[1], ShippingFee=row[2], CartId=row[3],
                    UserId=row[4], ReceiverName=row[5], ReceiverPhone=row[6],
                    ShippingAddress=row[7], PaymentMethod=row[8], VoucherCode=row[9],
                    SubTotal=row[10], DiscountAmount=row[11], TotalAmount=row[12],
                    Note=row[13], CreatedAt=row[14], UpdatedAt=row[15]
                )

                # Truy vấn lấy danh sách OrderItems của đơn hàng này
                sql_items = "SELECT * FROM OrderItems WHERE OrderId = ?"
                cursor.execute(sql_items, (dh.OrderId,))
                items_rows = cursor.fetchall()

                # Ép dữ liệu vào class OrderItem và đưa vào list dh.Items
                for i_row in items_rows:
                    item = OrderItem(
                        OrderItemId=i_row[0], OrderId=i_row[1], ProductId=i_row[2],
                        ProductName=i_row[3], Emoji=i_row[4], Quantity=i_row[5],
                        UnitPrice=i_row[6], TotalPrice=i_row[7]
                    )
                    dh.Items.append(item.__dict__)  # Đổi thành dict để dễ xuất JSON

                danh_sach_don.append(dh.__dict__)

            return danh_sach_don
        except Exception as e:
            print("Lỗi lấy lịch sử đơn hàng:", e)
            return []
        finally:
            cursor.close()
            conn.close()

    # ==========================================
    # 3. ĐỔI STATUS (TRẠNG THÁI ĐƠN HÀNG)
    # ==========================================
    def cap_nhat_trang_thai(self, order_id, new_status):
        conn = DBconnection().get_connection()
        if not conn: return False
        cursor = conn.cursor()
        try:
            sql = "UPDATE Orders SET Status = ?, UpdatedAt = GETDATE() WHERE OrderId = ?"
            cursor.execute(sql, (new_status, order_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Lỗi cập nhật trạng thái đơn {order_id}:", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def lay_tat_ca_don_hang(self):
        conn = DBconnection().get_connection()
        if not conn: return []
        cursor = conn.cursor()
        try:
            sql = """
            SELECT o.OrderId, o.Status, o.ShippingFee, o.UserId,
                   u.ten_user AS CustomerName,
                   o.ReceiverName, o.ReceiverPhone, o.ShippingAddress,
                   o.PaymentMethod, o.SubTotal, o.DiscountAmount,
                   o.TotalAmount, o.CreatedAt
            FROM Orders o
            LEFT JOIN Users u ON o.UserId = u.ma_user
            ORDER BY o.CreatedAt DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            result = []

            for row in rows:
                don = dict(zip(columns, row))

                # Lấy items của từng đơn
                cursor2 = conn.cursor()
                cursor2.execute("SELECT * FROM OrderItems WHERE OrderId = ?", (don['OrderId'],))
                item_rows = cursor2.fetchall()
                item_columns = [col[0] for col in cursor2.description]
                don['Items'] = [dict(zip(item_columns, ir)) for ir in item_rows]
                cursor2.close()

                # Chuyển datetime thành string
                if don.get('CreatedAt'):
                    don['CreatedAt'] = str(don['CreatedAt'])

                result.append(don)

            return result
        except Exception as e:
            print("Lỗi lay_tat_ca_don_hang:", e)
            return []
        finally:
            cursor.close()
            conn.close()