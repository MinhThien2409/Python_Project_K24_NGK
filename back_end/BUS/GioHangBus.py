from back_end.DAO.GioHangDao import GioHangDao
from back_end.DAO.SanPhamDao import SanPhamDao


class GioHangBus:
    def __init__(self):
        """Khởi tạo BUS giỏ hàng với DAO giỏ hàng và sản phẩm."""
        self.dao = GioHangDao()
        self.san_pham_dao = SanPhamDao()

    def _lay_kho(self, product_id):
        """Doc ton kho/giá/ẩn qua SanPhamDao, KHÔNG tin client."""
        try:
            return self.san_pham_dao.lay_thong_tin_kho(product_id)
        except AttributeError:
            return None

    def _ep_so_luong(self, quantity):
        """Ép số lượng về int, None/rỗng/chữ → 0 (không hợp lệ)."""
        try:
            return int(quantity) if quantity not in (None, "") else 0
        except (TypeError, ValueError):
            return 0

    def _kiem_kho(self, product_id, so_luong):
        """Check SP ẩn + vượt kho, trả (kho, lỗi)."""
        kho = self._lay_kho(product_id)
        if not kho or not kho.get("is_active", True):
            return None, {"status": False, "message": "Sản phẩm không còn kinh doanh!"}
        if so_luong > int(kho.get("quantity", 0)):
            return None, {"status": False, "message": (
                f"Số lượng vượt tồn kho, chỉ còn {kho.get('quantity', 0)} sản phẩm!")}
        return kho, None

    def xu_ly_them_vao_gio(self, user_id, product_id, quantity, unit_price, force=False):
        """Thêm vào giỏ: check kho + giá DB + luật 1-shop."""
        so_luong = self._ep_so_luong(quantity)
        if not user_id or not product_id or so_luong <= 0:
            return {"status": False, "message": "Thông tin sản phẩm không hợp lệ!"}
        kho, loi = self._kiem_kho(product_id, so_luong)
        if loi:
            return loi
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)
        if not cart_id:
            return {"status": False, "message": "Lỗi hệ thống khởi tạo giỏ hàng!"}
        new_store_id = self.dao.lay_store_id_san_pham(product_id)
        if not new_store_id:
            return {"status": False, "message": "Không tìm thấy thông tin gian hàng!"}
        cac_store = self.dao.lay_store_ids_trong_gio(cart_id)
        store_khac = next((s for s in cac_store if s['store_id'] != new_store_id), None)
        if store_khac and not force:
            return {"status": False, "conflict": True, "message": (
                f"Giỏ hàng đang có sản phẩm từ '{store_khac['store_name']}'. "
                "Mỗi đơn hàng chỉ mua từ 1 shop. Xóa giỏ cũ để thêm sản phẩm này?")}
        if force and store_khac:
            self.dao.xoa_toan_bo_gio(cart_id)
        gia_chuan = float(kho.get("price", 0))
        if not self.dao.them_vao_gio_hang(cart_id, product_id, so_luong, gia_chuan):
            return {"status": False, "message": "Không thể thêm sản phẩm vào giỏ!"}
        self.dao.cap_nhat_tong_tien(cart_id)
        return {"status": True, "message": "Đã thêm vào giỏ hàng!"}

    def lay_thong_tin_gio_hang(self, user_id):
        """Lấy chi tiết giỏ hàng của user (tự tạo giỏ nếu chưa có)."""
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)
        if not cart_id:
            return {"status": False, "message": "Không tìm thấy giỏ hàng", "data": []}

        items = self.dao.lay_chi_tiet_gio_hang(cart_id)
        return {"status": True, "message": "Thành công", "data": items}

    def xoa_khoi_gio(self, user_id, product_id):
        """Xóa một sản phẩm khỏi giỏ hàng của user."""
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)
        if not cart_id:
            return {"status": False, "message": "Không tìm thấy giỏ hàng!"}
        ok = self.dao.xoa_khoi_gio(cart_id, product_id)
        if ok:
            return {"status": True, "message": "Đã xóa sản phẩm khỏi giỏ hàng!"}
        return {"status": False, "message": "Lỗi khi xóa sản phẩm!"}

    def cap_nhat_so_luong(self, user_id, product_id, quantity):
        """Đổi số lượng: check kho, SL<=0 thì xóa món."""
        so_luong = self._ep_so_luong(quantity)
        if so_luong <= 0:
            return self.xoa_khoi_gio(user_id, product_id)
        _, loi = self._kiem_kho(product_id, so_luong)
        if loi:
            return loi
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)
        if not cart_id:
            return {"status": False, "message": "Không tìm thấy giỏ hàng!"}
        ok = self.dao.cap_nhat_so_luong(cart_id, product_id, so_luong)
        if ok:
            return {"status": True, "message": "Đã cập nhật số lượng!"}
        return {"status": False, "message": "Lỗi cập nhật!"}

    def xoa_toan_bo_gio(self, user_id):
        """Xóa toàn bộ sản phẩm trong giỏ hàng của user."""
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)  # ✅ Sửa: thêm "_hang"
        if not cart_id:
            return {"status": False, "message": "Không tìm thấy giỏ hàng!"}
        ok = self.dao.xoa_toan_bo_gio(cart_id)
        return {"status": ok, "message": "Đã xóa giỏ hàng!" if ok else "Lỗi xóa giỏ hàng!"}