from back_end.Model.GianHang import GianHang
from back_end.Model.YeuCau import YeuCau
from back_end.DAO.GianHangDao import GianHangDao

class GianHangBus:
    def __init__(self):
        self.dao = GianHangDao()

    def dang_ky_gian_hang(self, req: YeuCau):
        """Gửi đơn đăng ký → SellerRequests (chờ Admin duyệt)"""
        if not req.ShopName or not req.UserId:
            return {"status": False,
                    "message": "Tên cửa hàng và UserId không được để trống!"}
        if not req.NationalId:
            return {"status": False,
                    "message": "Vui lòng nhập số CMND/CCCD!"}

        ok = self.dao.gui_yeu_cau_ban_hang(req)
        if ok:
            return {"status": True,
                    "message": "Đã gửi yêu cầu! Admin sẽ xét duyệt trong 24h."}
        return {"status": False,
                "message": "Lỗi hệ thống, vui lòng thử lại!"}

    def lay_danh_sach_yeu_cau(self):
        data = self.dao.lay_danh_sach_yeu_cau()
        return {"status": True, "data": data}

    def duyet_yeu_cau(self, request_id, reviewed_by):
        if not request_id:
            return {"status": False, "message": "Thiếu mã yêu cầu!"}
        ok = self.dao.duyet_yeu_cau(request_id, reviewed_by)
        if ok:
            return {"status": True,
                    "message": "Đã duyệt! Gian hàng đã được mở và tài khoản đã được cấp quyền Seller."}
        return {"status": False, "message": "Lỗi khi duyệt yêu cầu!"}

    def tu_choi_yeu_cau(self, request_id, reviewed_by, ly_do):
        if not request_id:
            return {"status": False, "message": "Thiếu mã yêu cầu!"}
        ok = self.dao.tu_choi_yeu_cau(request_id, reviewed_by, ly_do)
        if ok:
            return {"status": True, "message": "Đã từ chối yêu cầu."}
        return {"status": False, "message": "Lỗi khi từ chối!"}

    def lay_store_theo_user(self, user_id):
        store = self.dao.lay_theo_user(user_id)
        if store:
            return {"status": True, "data": store}
        return {"status": False, "message": "Bạn chưa có gian hàng!"}