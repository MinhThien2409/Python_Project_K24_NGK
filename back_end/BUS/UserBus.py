from back_end.Model.User import User
from back_end.DAO.UserDao import UserDao


class UserBus:
    def __init__(self):
        self.dao = UserDao()

    def dang_ky_khach_hang(self, ten_user, dia_chi, sdt, tendangnhap, mat_khau):

        if not ten_user or not sdt or not tendangnhap or not mat_khau:
            return {"status": False, "message": "Vui lòng điền đầy đủ Tên, SĐT, Tên đăng nhập và Mật khẩu!"}

        if len(mat_khau) < 6:
            return {"status": False, "message": "Mật khẩu phải có ít nhất 6 ký tự!"}

        if self.dao.kiem_tra_tendangnhap_ton_tai(tendangnhap):
            return {"status": False, "message": f"Tên đăng nhập '{tendangnhap}' đã có người sử dụng!"}


        user_moi = User(
            ten_user=ten_user,
            dia_chi=dia_chi,
            sdt=sdt,
            cmnd=None,
            ma_nhom_quyen=14,
            tendangnhap=tendangnhap,
            mat_khau=mat_khau
        )


        is_success = self.dao.them_user(user_moi)

        if is_success:
            return {"status": True, "message": "Đăng ký tài khoản thành công!"}
        else:
            return {"status": False, "message": "Lỗi hệ thống khi lưu dữ liệu, vui lòng thử lại."}


    def dang_nhap(self, tendangnhap, mat_khau):

        if not tendangnhap or not mat_khau:
            return {"status": False, "message": "Vui lòng nhập tài khoản và mật khẩu!", "data": None}


        user = self.dao.dang_nhap(tendangnhap, mat_khau)


        if user:

            return {
                "status": True,
                "message": f"Chào mừng {user.ten_user} trở lại!",
                "data": {
                    "ma_user": user.ma_user,
                    "ten_user": user.ten_user,
                    "ma_nhom_quyen": user.ma_nhom_quyen,
                    "dia_chi":user.dia_chi,
                    "sdt":user.sdt,
                    "cmnd":user.cmnd
                }
            }
        else:
            return {"status": False, "message": "Tên đăng nhập hoặc mật khẩu không chính xác!", "data": None}


    def lay_danh_sach_user(self):
        danh_sach = self.dao.lay_danh_sach_user()
        return {"status": True, "data": danh_sach}

    def cap_nhat_user(self, ma_user, ten_user, dia_chi, sdt,cmnd):
        if not ma_user or not ten_user:
            return {"status": False, "message": "Tên người dùng không được để trống!"}

        is_success = self.dao.cap_nhat_user(ma_user, ten_user, dia_chi, sdt,cmnd)
        if is_success:
            return {"status": True, "message": "Cập nhật thông tin thành công!"}
        else:
            return {"status": False, "message": "Không tìm thấy User hoặc lỗi cập nhật."}

    def xoa_user(self, ma_user):
        if not ma_user:
            return {"status": False, "message": "Mã User không hợp lệ!"}

        is_success = self.dao.xoa_user(ma_user)
        if is_success:
            return {"status": True, "message": "Đã xóa người dùng thành công!"}
        else:
            return {"status": False, "message": "Lỗi khi xóa người dùng."}