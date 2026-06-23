from back_end.DAO.DonHangDao import DonHangDao
from back_end.Model.DonHang import DonHang


class DonHangBus:
    def __init__(self):
        self.dao = DonHangDao()

    def tao_don_hang(self, dh: DonHang):
        if not dh.ReceiverName or not dh.ReceiverPhone or not dh.ShippingAddress:
            return {"status": False, "message": "Vui lòng điền đầy đủ thông tin người nhận hàng!"}

        if not dh.Items or len(dh.Items) == 0:
            return {"status": False, "message": "Đơn hàng không có sản phẩm nào!"}

        if dh.TotalAmount <= 0:
            return {"status": False, "message": "Tổng tiền đơn hàng không hợp lệ!"}

        product_ids = [item.ProductId for item in dh.Items]
        store_ids = self.dao.lay_store_ids_cua_san_pham(product_ids)
        if len(set(store_ids)) > 1:
            return {"status": False,
                    "message": "Đơn hàng chỉ được chứa sản phẩm từ 1 shop duy nhất!"}

        dh.Status = 'Pending'
        result = self.dao.tao_don_hang(dh, dh.Items)

        # ✅ Xử lý lỗi hết hàng trả về từ DAO
        if isinstance(result, dict):
            if result.get('error') == 'out_of_stock':
                return {"status": False,
                        "message": f"Sản phẩm '{result['product_name']}' chỉ còn {result['available']} sản phẩm trong kho!"}
            if result.get('error') == 'not_found':
                return {"status": False,
                        "message": f"Không tìm thấy sản phẩm {result['product_name']}!"}

        if result:
            return {"status": True, "message": f"Đặt hàng thành công! Mã đơn: #{result}"}
        return {"status": False, "message": "Hệ thống bận, vui lòng thử lại sau!"}
    def lay_don_hang_cua_toi(self, user_id):
        if not user_id:
            return {"status": False, "message": "Lỗi xác thực người dùng", "data": []}
        danh_sach = self.dao.lay_don_hang_cua_user(user_id)
        return {"status": True, "data": danh_sach}

    def thay_doi_trang_thai(self, order_id, new_status):
        trang_thai_hop_le = ['Pending', 'Confirmed', 'Shipping', 'Completed', 'Cancelled']
        if new_status not in trang_thai_hop_le:
            return {"status": False, "message": "Trạng thái đơn hàng không hợp lệ!"}

        is_success = self.dao.cap_nhat_trang_thai(order_id, new_status)
        if is_success:
            return {"status": True, "message": f"Đã chuyển đơn hàng sang: {new_status}"}
        else:
            return {"status": False, "message": "Không tìm thấy đơn hàng hoặc có lỗi xảy ra!"}

    def lay_tat_ca_don_hang(self):
        danh_sach = self.dao.lay_tat_ca_don_hang()
        return {"status": True, "data": danh_sach}

    def lay_thong_ke_tong_quan(self):
        return self.dao.lay_thong_ke_tong_quan()

    def lay_doanh_thu_theo_thang(self, year):
        return self.dao.lay_doanh_thu_theo_thang(year)

    def lay_don_hang_cua_seller(self, store_id):
        if not store_id:
            return {"status": False, "message": "Thiếu store_id!", "data": []}
        danh_sach = self.dao.lay_don_hang_cua_seller(store_id)
        return {"status": True, "data": danh_sach}