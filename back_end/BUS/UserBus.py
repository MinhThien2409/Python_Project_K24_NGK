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
            ma_nhom_quyen=4,
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

        # ✅ Tài khoản bị khóa
        if isinstance(user, dict) and user.get('banned'):
            return {
                "status": False,
                "message": "Tài khoản của bạn đã bị khóa! Vui lòng liên hệ quản trị viên để được hỗ trợ.",
                "data": None
            }

        # Role_Id NULL hoặc trỏ tới vai trò không tồn tại → từ chối rõ ràng, không crash (FR-009)
        if isinstance(user, dict) and user.get('role_none'):
            return {
                "status": False,
                "message": "Dữ liệu vai trò không hợp lệ! Vui lòng liên hệ quản trị viên.",
                "data": None
            }

        if not user:
            return {"status": False, "message": "Tên đăng nhập hoặc mật khẩu không chính xác!", "data": None}

        ten_vai_tro = self.dao.lay_ten_vai_tro_theo_id(user.ma_nhom_quyen)
        if not ten_vai_tro:
            return {
                "status": False,
                "message": "Dữ liệu vai trò không hợp lệ! Vui lòng liên hệ quản trị viên.",
                "data": None
            }

        return {
            "status": True,
            "message": f"Chào mừng {user.ten_user} trở lại!",
            "data": {
                "ma_user": user.ma_user,
                "ten_user": user.ten_user,
                "ma_nhom_quyen": user.ma_nhom_quyen,
                "ten_vai_tro": ten_vai_tro,
                "ten_vai_tro_hien_thi": ten_vai_tro,
                "dia_chi": user.dia_chi,
                "sdt": user.sdt,
                "cmnd": user.cmnd
            }
        }

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

    def lay_thong_tin_user(self, ma_user):
        return self.dao.lay_thong_tin_user(ma_user)

    def cap_nhat_trang_thai(self, ma_user, trang_thai):
        if not ma_user:
            return {"status": False, "message": "Thiếu mã user!"}
        if trang_thai not in ('active', 'banned'):
            return {"status": False, "message": "Trạng thái không hợp lệ!"}

        # Không ai có quyền khóa tài khoản Admin (FR-009) — kiểm tra trước khi ghi
        thong_tin = self.dao.lay_thong_tin_user(ma_user)
        if not thong_tin:
            return {"status": False, "message": "Không tìm thấy người dùng!"}
        role_id = thong_tin.get("Role_Id") or thong_tin.get("Role_id") or thong_tin.get("role_id")
        ten_vai_tro = self.dao.lay_ten_vai_tro_theo_id(role_id)
        if trang_thai == 'banned' and ten_vai_tro == "Admin":
            return {"status": False, "message": "Không ai có quyền khóa tài khoản Admin!"}

        ok = self.dao.cap_nhat_trang_thai(ma_user, trang_thai)
        if ok:
            label = "Đã khóa tài khoản!" if trang_thai == 'banned' else "Đã mở khóa tài khoản!"
            return {"status": True, "message": label}
        return {"status": False, "message": "Lỗi cập nhật trạng thái."}