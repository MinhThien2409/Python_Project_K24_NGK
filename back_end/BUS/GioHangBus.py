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
        """Ép về int; None/rỗng/chữ/float lẻ → None (không hợp lệ)."""
        if quantity is None or isinstance(quantity, bool):
            return None
        try:
            if isinstance(quantity, float) and not quantity.is_integer():
                return None
            if isinstance(quantity, str):
                quantity = quantity.strip()
                if quantity == "":
                    return None
            return int(quantity)
        except (TypeError, ValueError):
            return None

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
        so_luong = self._ep_so_luong(quantity)
        if not user_id or not product_id or so_luong is None or so_luong <= 0:
            return {"status": False, "message": "Thông tin sản phẩm không hợp lệ!"}
        kho, loi = self._kiem_kho(product_id, so_luong)
        if loi:
            return loi
        cart_id = self.dao.lay_hoac_tao_gio_hang(user_id)
        if not cart_id:
            return {"status": False, "message": "Lỗi hệ thống khởi tạo giỏ hàng!"}
        gia_chuan = float(kho.get("price", 0))
        if not self.dao.them_vao_gio_hang(cart_id, product_id, so_luong, gia_chuan):
            return {"status": False, "message": "Không thể thêm sản phẩm vào giỏ!"}
        self.dao.cap_nhat_tong_tien(cart_id)
        return {"status": True, "message": "Đã thêm vào giỏ hàng!"}

    def lay_thong_tin_gio_hang(self, user_id):
        cart_id = self.dao.lay_gio_hang_id(user_id)  # chỉ tra cứu, giả định trả None nếu chưa có
        if not cart_id:
            return {"status": True, "message": "Giỏ hàng trống", "data": []}
        items = self.dao.lay_chi_tiet_gio_hang(cart_id)
        return {"status": True, "message": "Thành công", "data": items}

    def xoa_khoi_gio(self, user_id, product_id):
        cart_id = self.dao.lay_gio_hang_id(user_id)
        if not cart_id:
            return {"status": False, "message": "Không tìm thấy giỏ hàng!"}
        items = self.dao.lay_chi_tiet_gio_hang(cart_id) or []
        if not self._co_trong_gio(items, product_id):
            return {"status": False, "message": "Không tìm thấy sản phẩm trong giỏ!"}
        if self.dao.xoa_khoi_gio(cart_id, product_id):
            return {"status": True, "message": "Đã xóa sản phẩm khỏi giỏ hàng!"}
        return {"status": False, "message": "Lỗi khi xóa sản phẩm!"}

    def cap_nhat_so_luong(self, user_id, product_id, quantity):
        so_luong = self._ep_so_luong(quantity)
        if so_luong is None or so_luong < 0:
            return {"status": False, "message": "Số lượng không hợp lệ!"}
        if so_luong == 0:
            return self.xoa_khoi_gio(user_id, product_id)  # giữ hành vi "0 = xóa"
        _, loi = self._kiem_kho(product_id, so_luong)
        if loi:
            return loi
        cart_id = self.dao.lay_gio_hang_id(user_id)
        if not cart_id:
            return {"status": False, "message": "Không tìm thấy giỏ hàng!"}
        if self.dao.cap_nhat_so_luong(cart_id, product_id, so_luong):
            return {"status": True, "message": "Đã cập nhật số lượng!"}
        return {"status": False, "message": "Lỗi cập nhật!"}

    def _co_trong_gio(self, items, product_id):
        """Tên khóa 'ProductId' là giả định, chỉnh theo dict DAO thật trả về."""
        try:
            pid = int(product_id)
        except (TypeError, ValueError):
            return False
        return any(int(i.get("ProductId", i.get("product_id", -1))) == pid for i in items)

    def xoa_toan_bo_gio(self, user_id):
        cart_id = self.dao.lay_gio_hang_id(user_id)
        if not cart_id:
            return {"status": False, "message": "Không tìm thấy giỏ hàng!"}
        ok = self.dao.xoa_toan_bo_gio(cart_id)
        return {"status": ok, "message": "Đã xóa giỏ hàng!" if ok else "Lỗi xóa giỏ hàng!"}