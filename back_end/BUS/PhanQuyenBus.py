from DAO.PhanQuyenDao import PhanQuyenDao  # Sửa lại đường dẫn import nếu cần


class PhanQuyenBus:
    def __init__(self):

        self.dao = PhanQuyenDao()


    def cap_nhat_quyen(self, ma_nhom, ma_chuc_nang, xem, them, sua, xoa):
        if not ma_nhom or not ma_chuc_nang:
            # Đã xóa khoảng trắng thừa ở chữ 'status'
            return {"status": False, "message": "Thiếu thông tin Mã nhóm hoặc Mã chức năng!"}

        # Đã bổ sung biến 'xoa' vào cuối
        is_success = self.dao.dong_bo_quyen_xuong_user(ma_nhom, ma_chuc_nang, xem, them, sua, xoa)

        if is_success:
            return {"status": True, "message": "Đã lưu cấu hình Nhóm và đồng bộ thành công các thành viên!"}
        else:
            return {"status": False, "message": "Lỗi hệ thống đồng bộ quyền."}


    def cap_quyen_ngoai_le(self, ma_user, ma_chuc_nang, xem, them, sua, xoa):
        if not ma_user or not ma_chuc_nang:
            return {"status": False, "message": "Vui lòng chọn tài khoản và chức năng cần cấp quyền!"}


        is_success = self.dao.cap_quyen_ngoai_le_user(ma_user, ma_chuc_nang, xem, them, sua, xoa)

        if is_success:
            return {"status": True, "message": f"Đã áp dụng quyền ngoại lệ thành công cho tài khoản ID: {ma_user}!"}
        else:
            return {"status": False, "message": "Lỗi khi cấp quyền ngoại lệ."}


    def reset_ve_quyen_nhom(self, ma_user, ma_chuc_nang, xem_nhom, them_nhom, sua_nhom, xoa_nhom):

        is_success = self.dao.khoi_phuc_ve_quyen_nhom(ma_user, ma_chuc_nang, xem_nhom, them_nhom, sua_nhom, xoa_nhom)

        if is_success:
            return {"status": True, "message": "Tài khoản này đã được khôi phục về luật chung của Nhóm."}
        else:
            return {"status": False, "message": "Lỗi khi khôi phục quyền mặc định."}

    def lay_quyen_cua_user(self, ma_user):
        if not ma_user:
            return {"status": False, "message": "Thiếu mã user", "data": []}

        danh_sach = self.dao.lay_quyen_cua_user(ma_user)
        return {"status": True, "data": danh_sach}