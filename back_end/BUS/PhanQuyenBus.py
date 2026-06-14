from back_end.DAO.PhanQuyenDao import PhanQuyenDao  # Sửa lại đường dẫn import nếu cần


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

    def lay_quyen_cua_nhom(self, ma_nhom):
        if not ma_nhom:
            return {"status": False, "message": "Thiếu mã nhóm quyền!", "data": []}

        danh_sach = self.dao.lay_quyen_cua_nhom(ma_nhom)  # Bạn đã có trong DAO
        return {"status": True, "data": danh_sach}

    def ap_dung_quyen_nhom_cho_user(self, ma_user):
        if not ma_user:
            return {"status": False, "message": "Thiếu mã user!"}

        is_success = self.dao.ap_dung_quyen_nhom_cho_user(ma_user)
        if is_success:
            return {"status": True, "message": f"Đã áp dụng quyền nhóm cho tài khoản ID {ma_user}!"}
        else:
            return {"status": False, "message": "Lỗi khi áp dụng quyền nhóm. Kiểm tra xem nhóm có user khác không!"}

    def lay_tat_ca_roles(self):
        data = self.dao.lay_tat_ca_roles()
        return {"status": True, "data": data}

    def them_role(self, role_name):
        if not role_name or not role_name.strip():
            return {"status": False, "message": "Tên nhóm quyền không được trống!"}
        return self.dao.them_role(role_name.strip())

    def sua_role(self, role_id, role_name):
        if not role_name or not role_name.strip():
            return {"status": False, "message": "Tên nhóm quyền không được trống!"}
        return self.dao.sua_role(role_id, role_name.strip())

    def xoa_role(self, role_id):
        return self.dao.xoa_role(role_id)