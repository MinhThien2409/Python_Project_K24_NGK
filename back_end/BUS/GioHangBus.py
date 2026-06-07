from back_end.DAO.GioHangDao import GioHangDao


class GioHangBus:
    def __init__(self):
        self.dao = GioHangDao()

    def xu_ly_them_vao_gio(self, user_id, product_id, quantity, unit_price):
        # 1. Validation cơ bản
        if not user_id or not product_id or quantity <= 0:
            return {"status": False, "message": "Thông tin sản phẩm không hợp lệ!"}

        # 2. Lấy hoặc tạo giỏ hàng cho user này
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)
        if not cart_id:
            return {"status": False, "message": "Lỗi hệ thống khởi tạo giỏ hàng!"}

        # 3. Thêm sản phẩm vào bảng CartItems
        if not self.dao.them_vao_gio_hang(cart_id, product_id, quantity, unit_price):
            return {"status": False, "message": "Không thể thêm sản phẩm vào giỏ!"}

        # 4. Tính toán lại tổng tiền của giỏ hàng
        self.dao.cap_nhat_tong_tien(cart_id)

        return {"status": True, "message": "Đã thêm vào giỏ hàng thành công!"}

    def lay_thong_tin_gio_hang(self, user_id):
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)
        if not cart_id:
            return {"status": False, "message": "Không tìm thấy giỏ hàng", "data": []}

        items = self.dao.lay_chi_tiet_gio_hang(cart_id)
        return {"status": True, "message": "Thành công", "data": items}