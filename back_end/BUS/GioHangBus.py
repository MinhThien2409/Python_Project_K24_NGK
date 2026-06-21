from back_end.DAO.GioHangDao import GioHangDao


class GioHangBus:
    def __init__(self):
        self.dao = GioHangDao()

    def xu_ly_them_vao_gio(self, user_id, product_id, quantity, unit_price, force=False):
        # 1. Validation cơ bản
        if not user_id or not product_id or quantity <= 0:
            return {"status": False, "message": "Thông tin sản phẩm không hợp lệ!"}

        # 2. Lấy hoặc tạo giỏ hàng cho user này
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)
        if not cart_id:
            return {"status": False, "message": "Lỗi hệ thống khởi tạo giỏ hàng!"}

        # 3. Lấy shop của sản phẩm muốn thêm
        new_store_id = self.dao.lay_store_id_san_pham(product_id)
        if not new_store_id:
            return {"status": False, "message": "Không tìm thấy thông tin gian hàng!"}

        # 4. Kiểm tra giỏ hiện tại có sản phẩm từ shop khác không
        cac_store_trong_gio = self.dao.lay_store_ids_trong_gio(cart_id)
        store_khac = next((s for s in cac_store_trong_gio if s['store_id'] != new_store_id), None)

        if store_khac and not force:
            return {
                "status": False,
                "conflict": True,
                "message": f"Giỏ hàng đang có sản phẩm từ '{store_khac['store_name']}'. "
                           f"Mỗi đơn hàng chỉ mua từ 1 shop. Xóa giỏ cũ để thêm sản phẩm này?"
            }

        # 5. Nếu đồng ý đổi shop (force=True) → xóa giỏ cũ trước
        if force and store_khac:
            self.dao.xoa_toan_bo_gio(cart_id)

        # 6. Thêm sản phẩm vào bảng CartItems — CHỈ GỌI 1 LẦN
        if not self.dao.them_vao_gio_hang(cart_id, product_id, quantity, unit_price):
            return {"status": False, "message": "Không thể thêm sản phẩm vào giỏ!"}

        # 7. Tính toán lại tổng tiền của giỏ hàng
        self.dao.cap_nhat_tong_tien(cart_id)

        return {"status": True, "message": "Đã thêm vào giỏ hàng!"}

    def lay_thong_tin_gio_hang(self, user_id):
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)
        if not cart_id:
            return {"status": False, "message": "Không tìm thấy giỏ hàng", "data": []}

        items = self.dao.lay_chi_tiet_gio_hang(cart_id)
        return {"status": True, "message": "Thành công", "data": items}

    def xoa_khoi_gio(self, user_id, product_id):
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)
        if not cart_id:
            return {"status": False, "message": "Không tìm thấy giỏ hàng!"}
        ok = self.dao.xoa_khoi_gio(cart_id, product_id)
        if ok:
            return {"status": True, "message": "Đã xóa sản phẩm khỏi giỏ hàng!"}
        return {"status": False, "message": "Lỗi khi xóa sản phẩm!"}

    def cap_nhat_so_luong(self, user_id, product_id, quantity):
        if quantity <= 0:
            return self.xoa_khoi_gio(user_id, product_id)
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)
        if not cart_id:
            return {"status": False, "message": "Không tìm thấy giỏ hàng!"}
        ok = self.dao.cap_nhat_so_luong(cart_id, product_id, quantity)
        if ok:
            return {"status": True, "message": "Đã cập nhật số lượng!"}
        return {"status": False, "message": "Lỗi cập nhật!"}

    def xoa_toan_bo_gio(self, user_id):
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)  # ✅ Sửa: thêm "_hang"
        if not cart_id:
            return {"status": False, "message": "Không tìm thấy giỏ hàng!"}
        ok = self.dao.xoa_toan_bo_gio(cart_id)
        return {"status": ok, "message": "Đã xóa giỏ hàng!" if ok else "Lỗi xóa giỏ hàng!"}