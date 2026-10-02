from back_end.DAO.GianHangDao import GianHangDao
from back_end.DAO.UserDao import UserDao
from back_end.Model.YeuCau import YeuCau

class GianHangBus:
    def __init__(self):
        """Khởi tạo BUS gian hàng với DAO gian hàng và user."""
        self.dao = GianHangDao()
        self.user_dao = UserDao()

    def dang_ky_gian_hang(self, req: YeuCau):
        """Validate server-side và gửi đơn Seller; user/CCCD lấy từ session/profile."""
        import re
        shop = str(req.ShopName or "").strip()
        phone = str(req.BusinessPhone or "").strip()
        category = str(req.Category or "").strip()
        description = str(req.Description or "").strip()
        if not shop:
            return {"status": False, "message": "Tên cửa hàng không được để trống!"}
        if len(shop) > 150:
            return {"status": False, "message": "Tên cửa hàng không được vượt quá 150 ký tự!"}
        if not phone or not re.fullmatch(r"0\d{9}", phone):
            return {"status": False, "message": "Số điện thoại không hợp lệ!"}
        if not category:
            return {"status": False, "message": "Danh mục không được để trống!"}
        if len(category) > 50:
            return {"status": False, "message": "Danh mục không được vượt quá 50 ký tự!"}
        if len(description) > 500:
            return {"status": False, "message": "Mô tả không được vượt quá 500 ký tự!"}
        if not req.UserId:
            return {"status": False, "message": "Tài khoản đăng ký không hợp lệ!"}
        user_info = self.user_dao.lay_thong_tin_user(req.UserId)
        if not user_info:
            return {"status": False, "message": "Không tìm thấy thông tin tài khoản!"}
        thieu = []
        if not str(user_info.get('FullName') or '').strip(): thieu.append('Họ tên')
        if not str(user_info.get('Phone') or '').strip(): thieu.append('Số điện thoại')
        if not str(user_info.get('Address') or '').strip(): thieu.append('Địa chỉ')
        if not str(user_info.get('NationalId') or '').strip(): thieu.append('CMND/CCCD')
        if thieu:
            return {"status": False,
                    "message": f"Vui lòng cập nhật đầy đủ thông tin trước khi đăng ký! Còn thiếu: {', '.join(thieu)}"}
        req.ShopName = shop
        req.BusinessPhone = phone
        req.Category = category
        req.Description = description or None
        req.NationalId = str(user_info.get('NationalId')).strip()
        ok = self.dao.gui_yeu_cau_ban_hang(req)
        if ok is True or ok == "ok":
            return {"status": True, "message": "Đã gửi yêu cầu! Quản lý sẽ xét duyệt trong 24h."}
        if ok == "da_co_pending":
            return {"status": False, "message": "Tài khoản đã có yêu cầu đăng ký đang chờ duyệt!"}
        if ok == "da_la_seller":
            return {"status": False, "message": "Tài khoản này đã là Seller và có gian hàng!"}
        return {"status": False, "message": "Lỗi hệ thống, vui lòng thử lại!"}

    def lay_danh_sach_yeu_cau(self):
        """Lấy danh sách đơn đăng ký bán hàng cho Quản lý/Admin xét duyệt."""
        data = self.dao.lay_danh_sach_yeu_cau()
        return {"status": True, "data": data}

    def duyet_yeu_cau(self, nguoi_thao_tac_id, request_id):
        """Duyệt đơn bán hàng: ánh xạ mã trạng thái từ DAO sang message tiếng Việt."""
        if not request_id:
            return {"status": False, "message": "Thiếu mã yêu cầu!"}
        ket_qua = self.dao.duyet_yeu_cau(request_id, nguoi_thao_tac_id)
        if ket_qua == 'ok':
            return {"status": True,
                    "message": "Đã duyệt! Gian hàng đã được mở và tài khoản đã trở thành Seller."}
        if ket_qua == 'da_xu_ly':
            return {"status": False, "message": "Yêu cầu đã được xử lý trước đó!"}
        if ket_qua == 'da_la_seller':
            return {"status": False,
                    "message": "Tài khoản này đã có gian hàng, không thể duyệt lại!"}
        return {"status": False, "message": "Không tìm thấy yêu cầu!"}

    def tu_choi_yeu_cau(self, nguoi_thao_tac_id, request_id, ly_do):
        """Từ chối đơn bán hàng: bắt buộc lý do; ánh xạ mã trạng thái từ DAO sang message."""
        if not request_id:
            return {"status": False, "message": "Thiếu mã yêu cầu!"}
        if not ly_do or not ly_do.strip():
            return {"status": False, "message": "Vui lòng nhập lý do từ chối!"}
        ket_qua = self.dao.tu_choi_yeu_cau(request_id, nguoi_thao_tac_id, ly_do.strip())
        if ket_qua == 'ok':
            return {"status": True, "message": "Đã từ chối yêu cầu của người bán."}
        if ket_qua == 'da_xu_ly':
            return {"status": False, "message": "Yêu cầu đã được xử lý trước đó!"}
        return {"status": False, "message": "Không tìm thấy yêu cầu!"}

    def lay_store_theo_user(self, user_id):
        """Lấy gian hàng của user, báo lỗi khi chưa có gian hàng."""
        store = self.dao.lay_theo_user(user_id)
        if store:
            return {"status": True, "data": store}
        return {"status": False, "message": "Bạn chưa có gian hàng!"}

    def cap_nhat_trang_shop(self, nguoi_id, store_id, ten_shop, gioi_thieu, tham_nien):
        """Seller sua ten/gioi thieu/tham nien shop minh, lam sach XSS."""
        ten = (ten_shop or "").strip()
        if not ten:
            return {"status": False, "message": "Tên shop không được để trống!"}
        if len(ten) > 150:
            return {"status": False, "message": "Thông tin quá dài, vui lòng rút gọn!"}
        gt = (gioi_thieu or "").strip()
        if len(gt) > 500:
            return {"status": False, "message": "Thông tin quá dài, vui lòng rút gọn!"}
        tn = None
        if tham_nien not in (None, ""):
            try:
                tn = int(tham_nien)
            except (TypeError, ValueError):
                return {"status": False, "message": "Thâm niên phải từ 0 đến 100 năm!"}
            if tn < 0 or tn > 100:
                return {"status": False, "message": "Thâm niên phải từ 0 đến 100 năm!"}
        if self.dao.kiem_tra_ten_shop_trung(ten, store_id):
            return {"status": False, "message": "Tên shop đã có người sử dụng!"}
        gt_sach = self._lam_sach_xss(gt)
        ten_sach = self._lam_sach_xss(ten)
        ok = self.dao.cap_nhat_trang_shop(store_id, ten_sach, gt_sach, tn)
        if ok:
            return {"status": True, "message": "Đã cập nhật trang shop thành công!",
                    "data": {"ten_shop": ten_sach, "gioi_thieu": gt_sach, "tham_nien": tn}}
        return {"status": False, "message": "Lỗi khi cập nhật trang shop!"}

    def _lam_sach_xss(self, text):
        """Loai bo script/on-event/javascript: (lop 1, lop 2 la textContent)."""
        if not text:
            return text
        sach = text.replace("<script", "&lt;script").replace("</script", "&lt;/script")
        sach = sach.replace("javascript:", "").replace("onerror=", "").replace("onclick=", "")
        return sach.strip()
