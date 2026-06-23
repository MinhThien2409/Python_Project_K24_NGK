from back_end.DBconnection import DBconnection
from back_end.Model.DonHang import DonHang
from back_end.Model.OrderItem import OrderItem


class DonHangDao:
    # ==========================================
    # 1. TẠO ĐƠN HÀNG (DÙNG TRANSACTION)
    # ==========================================
    import uuid  # thêm dòng này lên đầu file

    def tao_don_hang(self, order: DonHang, order_items: list):
        conn = DBconnection().get_connection()
        if not conn: return False
        cursor = conn.cursor()
        try:
            sql_order = """
            INSERT INTO Orders (Status, ShippingFee, UserId, ReceiverName,
                                ReceiverPhone, ShippingAddress, PaymentMethod,
                                SubTotal, DiscountAmount, TotalAmount, Note)
            OUTPUT INSERTED.OrderId
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql_order, (
                str(order.Status),
                float(order.ShippingFee or 0),
                int(order.UserId),
                str(order.ReceiverName),
                str(order.ReceiverPhone),
                str(order.ShippingAddress),
                str(order.PaymentMethod),
                float(order.SubTotal or 0),
                float(order.DiscountAmount or 0),
                float(order.TotalAmount or 0),
                str(order.Note) if order.Note else None
            ))

            new_order_id = cursor.fetchone()[0]

            sql_item = """
            INSERT INTO OrderItems (OrderId, ProductId, ProductName, Emoji,
                                    Quantity, UnitPrice, TotalPrice)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            # ✅ Lệnh trừ kho — atomic, có điều kiện Quantity >= ? để không bị âm
            sql_tru_kho = """
            UPDATE Products 
            SET Quantity = Quantity - ? 
            WHERE ProductId = ? AND Quantity >= ?
            """

            for item in order_items:
                qty = int(item.Quantity or 0)

                cursor.execute(sql_item, (
                    int(new_order_id),
                    int(item.ProductId),
                    str(item.ProductName or f'Sản phẩm #{item.ProductId}'),
                    str(item.Emoji or '📦'),
                    qty,
                    float(item.UnitPrice or 0),
                    float(item.TotalPrice or 0)
                ))

                # ✅ Trừ tồn kho ngay khi đặt hàng thành công
                cursor.execute(sql_tru_kho, (qty, int(item.ProductId), qty))

                if cursor.rowcount == 0:
                    # Không đủ hàng → lấy thông tin báo lỗi rồi hủy toàn bộ đơn
                    cursor.execute(
                        "SELECT ProductName, Quantity FROM Products WHERE ProductId = ?",
                        (item.ProductId,)
                    )
                    info = cursor.fetchone()
                    conn.rollback()
                    if info:
                        return {"error": "out_of_stock",
                                "product_name": info.ProductName,
                                "available": info.Quantity}
                    return {"error": "not_found", "product_name": f"#{item.ProductId}"}

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
            sql_orders = """
            SELECT * FROM Orders 
            WHERE UserId = ? 
            ORDER BY CreatedAt DESC
            """
            cursor.execute(sql_orders, (ma_user,))
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            danh_sach_don = []

            for row in rows:
                don = dict(zip(columns, row))

                # Lấy items
                cursor2 = conn.cursor()
                cursor2.execute(
                    "SELECT * FROM OrderItems WHERE OrderId = ?",
                    (don['OrderId'],)
                )
                item_rows = cursor2.fetchall()
                item_columns = [col[0] for col in cursor2.description]
                don['Items'] = [dict(zip(item_columns, ir)) for ir in item_rows]
                cursor2.close()

                # Chuyển datetime thành string
                if don.get('CreatedAt'):
                    don['CreatedAt'] = str(don['CreatedAt'])
                if don.get('UpdatedAt'):
                    don['UpdatedAt'] = str(don['UpdatedAt'])

                danh_sach_don.append(don)

            return danh_sach_don
        except Exception as e:
            print("Lỗi lay_don_hang_cua_user:", e)
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
            cursor.execute("SELECT Status FROM Orders WHERE OrderId = ?", (order_id,))
            row = cursor.fetchone()
            if not row:
                return False

            current_status = row[0]
            print(f"Đơn #{order_id}: {current_status} → {new_status}")

            cursor.execute(
                "UPDATE Orders SET Status = ? WHERE OrderId = ?",
                (new_status, order_id)
            )
            rows_affected = cursor.rowcount

            # Cộng SoldCount khi hoàn thành
            if new_status == 'Completed' and current_status != 'Completed':
                cursor.execute(
                    "SELECT ProductId, Quantity FROM OrderItems WHERE OrderId = ?",
                    (order_id,)
                )
                for item in cursor.fetchall():
                    cursor.execute(
                        "UPDATE Products SET SoldCount = ISNULL(SoldCount, 0) + ? WHERE ProductId = ?",
                        (item[1], item[0])
                    )

            # ✅ Hoàn lại tồn kho khi đơn bị hủy
            if new_status == 'Cancelled' and current_status != 'Cancelled':
                cursor.execute(
                    "SELECT ProductId, Quantity FROM OrderItems WHERE OrderId = ?",
                    (order_id,)
                )
                for item in cursor.fetchall():
                    cursor.execute(
                        "UPDATE Products SET Quantity = Quantity + ? WHERE ProductId = ?",
                        (item[1], item[0])
                    )

            conn.commit()
            return rows_affected > 0

        except Exception as e:
            conn.rollback()
            print(f"LỖI cap_nhat_trang_thai: {e}")
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
            SELECT 
                o.OrderId,
                o.Status,
                o.ShippingFee,
                o.UserId,
                u.FullName      AS CustomerName,
                o.ReceiverName,
                o.ReceiverPhone,
                o.ShippingAddress,
                o.PaymentMethod,
                o.SubTotal,
                o.DiscountAmount,
                o.TotalAmount,
                o.CreatedAt
            FROM Orders o
            LEFT JOIN Users u ON o.UserId = u.UserId
            ORDER BY o.CreatedAt DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            result = []

            for row in rows:
                don = dict(zip(columns, row))

                cursor2 = conn.cursor()
                cursor2.execute(
                    "SELECT * FROM OrderItems WHERE OrderId = ?",
                    (don['OrderId'],)
                )
                item_rows = cursor2.fetchall()
                item_columns = [col[0] for col in cursor2.description]
                don['Items'] = [dict(zip(item_columns, ir)) for ir in item_rows]
                cursor2.close()

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

    def lay_thong_ke_tong_quan(self):
        conn = DBconnection.get_connection()
        if conn is None: return {}
        cursor = conn.cursor()
        try:

            cursor.execute("""
                SELECT 
                    ISNULL(SUM(CASE WHEN Status <> 'Cancelled' THEN TotalAmount ELSE 0 END), 0) AS doanh_thu,
                    COUNT(*) AS tong_don,
                    SUM(CASE WHEN Status='Pending'   THEN 1 ELSE 0 END) AS cho_duyet,
                    SUM(CASE WHEN Status='Shipping'  THEN 1 ELSE 0 END) AS dang_giao,
                    SUM(CASE WHEN Status='Completed' THEN 1 ELSE 0 END) AS hoan_thanh,
                    SUM(CASE WHEN Status='Cancelled' THEN 1 ELSE 0 END) AS da_huy
                FROM Orders
            """)
            row = cursor.fetchone()

            # Tổng sản phẩm
            cursor.execute("SELECT COUNT(*) AS tong FROM Products")
            p = cursor.fetchone()

            # Tổng user
            cursor.execute("SELECT COUNT(*) AS tong FROM Users")
            u = cursor.fetchone()

            cursor.execute("""
                SELECT TOP 5
                    p.ProductId,
                    p.ProductName,
                    p.Emoji,
                    p.SoldCount,
                    p.Price,
                    c.CategoryName  
                FROM Products p
                LEFT JOIN Categories c ON p.CategoryId = c.CategoryId
                ORDER BY p.SoldCount DESC
            """)
            top_sp = cursor.fetchall()

            cursor.execute("""
                SELECT TOP 5
                    o.OrderId,
                    o.ReceiverName,
                    o.TotalAmount,
                    o.Status,
                    o.CreatedAt,
                    u.FullName
                FROM Orders o
                LEFT JOIN Users u ON o.UserId = u.UserId
                ORDER BY o.CreatedAt DESC
            """)
            recent = cursor.fetchall()

            return {
                "status": True,
                "data": {
                    "doanh_thu": float(row.doanh_thu),
                    "tong_don": row.tong_don,
                    "cho_duyet": row.cho_duyet,
                    "dang_giao": row.dang_giao,
                    "hoan_thanh": row.hoan_thanh,
                    "da_huy": row.da_huy,
                    "tong_san_pham": p.tong,
                    "tong_user": u.tong,

                    "top_san_pham": [
                        {
                            "id": r.ProductId,
                            "name": r.ProductName,
                            "emoji": r.Emoji or '📦',
                            "sold": r.SoldCount or 0,
                            "price": float(r.Price),
                            "category": r.CategoryName or '—'
                        } for r in top_sp
                    ],

                    "don_gan_day": [
                        {
                            "order_id": r.OrderId,
                            "receiver_name": r.ReceiverName,
                            "customer_name": r.FullName or '—',
                            "total_amount": float(r.TotalAmount),
                            "status": r.Status,
                            "created_at": str(r.CreatedAt)
                        } for r in recent
                    ]
                }
            }
        except Exception as e:
            print("Lỗi thống kê:", e)
            return {"status": False, "data": {}}
        finally:
            cursor.close()
            conn.close()

    def lay_doanh_thu_theo_thang(self, year):
        conn = DBconnection.get_connection()
        if conn is None: return {}
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    MONTH(CreatedAt) AS thang,
                    ISNULL(SUM(TotalAmount), 0) AS doanh_thu,
                    COUNT(*) AS so_don
                FROM Orders
                WHERE YEAR(CreatedAt) = ?
                  AND Status = 'Completed'
                GROUP BY MONTH(CreatedAt)
                ORDER BY thang
            """, (year,))
            rows = cursor.fetchall()

            # Đảm bảo đủ 12 tháng
            data = {i: {"thang": i, "doanh_thu": 0, "so_don": 0} for i in range(1, 13)}
            for r in rows:
                data[r.thang] = {
                    "thang": r.thang,
                    "doanh_thu": float(r.doanh_thu),
                    "so_don": r.so_don
                }
            return {"status": True, "data": list(data.values())}
        except Exception as e:
            print("Lỗi doanh thu theo tháng:", e)
            return {"status": False, "data": []}
        finally:
            cursor.close();
            conn.close()

    def lay_don_hang_cua_seller(self, store_id):
        conn = DBconnection().get_connection()
        if not conn: return []
        cursor = conn.cursor()
        try:
            # Lấy các đơn hàng có ít nhất 1 sản phẩm thuộc store này
            sql = """
            SELECT DISTINCT
                o.OrderId, o.Status, o.ShippingFee, o.UserId,
                u.FullName   AS CustomerName,
                o.ReceiverName, o.ReceiverPhone, o.ShippingAddress,
                o.PaymentMethod, o.SubTotal, o.DiscountAmount,
                o.TotalAmount, o.CreatedAt
            FROM Orders o
            LEFT JOIN Users u ON o.UserId = u.UserId
            INNER JOIN OrderItems oi ON o.OrderId = oi.OrderId
            INNER JOIN Products p   ON oi.ProductId = p.ProductId
            WHERE p.StoreId = ?
            ORDER BY o.CreatedAt DESC
            """
            cursor.execute(sql, (store_id,))
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            result = []

            for row in rows:
                don = dict(zip(columns, row))

                # Chỉ lấy những OrderItems thuộc store này
                cursor2 = conn.cursor()
                cursor2.execute("""
                    SELECT oi.OrderItemId, oi.OrderId, oi.ProductId,
                           oi.ProductName, oi.Emoji, oi.Quantity,
                           oi.UnitPrice, oi.TotalPrice
                    FROM OrderItems oi
                    INNER JOIN Products p ON oi.ProductId = p.ProductId
                    WHERE oi.OrderId = ? AND p.StoreId = ?
                """, (don['OrderId'], store_id))
                item_rows = cursor2.fetchall()
                item_columns = [col[0] for col in cursor2.description]
                don['Items'] = [dict(zip(item_columns, ir)) for ir in item_rows]
                cursor2.close()

                if don.get('CreatedAt'):
                    don['CreatedAt'] = str(don['CreatedAt'])

                result.append(don)

            return result
        except Exception as e:
            print("Lỗi lay_don_hang_cua_seller:", e)
            return []
        finally:
            cursor.close()
            conn.close()

    def lay_store_ids_cua_san_pham(self, product_ids):
        """Trả về danh sách StoreId duy nhất của các sản phẩm trong đơn"""
        if not product_ids: return []
        conn = DBconnection().get_connection()
        if not conn: return []
        cursor = conn.cursor()
        try:
            placeholders = ','.join(['?'] * len(product_ids))
            cursor.execute(
                f"SELECT DISTINCT StoreId FROM Products WHERE ProductId IN ({placeholders})",
                tuple(product_ids)
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print("Lỗi lay_store_ids_cua_san_pham:", e)
            return []
        finally:
            cursor.close();
            conn.close()