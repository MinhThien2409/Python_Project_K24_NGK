from back_end.DAO.GianHangDao import GianHangDao
from back_end.DAO.UserDao import UserDao
from back_end.Model.YeuCau import YeuCau

class GianHangBus:
    def __init__(self):
        self.dao = GianHangDao()
        self.user_dao = UserDao()

    def dang_ky_gian_hang(self, req: YeuCau):
        """Gửi đơn đăng ký → SellerRequests (chờ Admin duyệt)"""
        if not req.ShopName or not req.UserId:
            return {"status": False, "message": "Tên cửa hàng và UserId không được để trống!"}

        # ✅ Tự động lấy NationalId từ hồ sơ user
        user_info = self.user_dao.lay_thong_tin_user(req.UserId)
        if not user_info:
            return {"status": False, "message": "Không tìm thấy thông tin tài khoản!"}

        thieu = []
        if not user_info.get('FullName'):   thieu.append('Họ tên')
        if not user_info.get('Phone'):      thieu.append('Số điện thoại')
        if not user_info.get('Address'):    thieu.append('Địa chỉ')
        if not user_info.get('NationalId'): thieu.append('CMND/CCCD')

        if thieu:
            return {"status": False,
                    "message": f"Vui lòng cập nhật đầy đủ thông tin trước khi đăng ký! Còn thiếu: {', '.join(thieu)}"}

        req.NationalId = user_info.get('NationalId')  # gán tự động, không cần user nhập lại

        ok = self.dao.gui_yeu_cau_ban_hang(req)  # gọi DAO, hàm này vẫn đúng tên
        if ok:
            return {"status": True, "message": "Đã gửi yêu cầu! Quản lý sẽ xét duyệt trong 24h."}
        return {"status": False, "message": "Lỗi hệ thống, vui lòng thử lại!"}

    def lay_danh_sach_yeu_cau(self):
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
        store = self.dao.lay_theo_user(user_id)
        if store:
            return {"status": True, "data": store}
        return {"status": False, "message": "Bạn chưa có gian hàng!"}