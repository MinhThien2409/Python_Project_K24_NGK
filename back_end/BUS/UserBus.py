from back_end.Model.User import User
from back_end.DAO.UserDao import UserDao
import secrets


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

    def lay_ten_vai_tro_theo_id(self, role_id):
        return self.dao.lay_ten_vai_tro_theo_id(role_id)

    def doi_mat_khau(self, ma_user, mat_khau_cu, mat_khau_moi):
        """Đổi mật khẩu: kiểm tra mật khẩu cũ, yêu cầu mật khẩu mới khác cũ và ≥ 6 ký tự."""
        if not ma_user:
            return {"status": False, "message": "Thiếu mã user!"}
        if not mat_khau_cu:
            return {"status": False, "message": "Vui lòng nhập mật khẩu cũ!"}
        if not mat_khau_moi or len(mat_khau_moi) < 6:
            return {"status": False, "message": "Mật khẩu mới phải có ít nhất 6 ký tự!"}

        thong_tin = self.dao.lay_thong_tin_user(ma_user)
        if not thong_tin:
            return {"status": False, "message": "Tài khoản không tồn tại!", "data": None}
        if thong_tin.get("Password") != mat_khau_cu:
            return {"status": False, "message": "Mật khẩu cũ không chính xác!", "data": None}
        if mat_khau_cu == mat_khau_moi:
            return {"status": False, "message": "Mật khẩu mới phải khác mật khẩu cũ!"}

        ok = self.dao.cap_nhat_mat_khau(ma_user, mat_khau_moi)
        if not ok:
            return {"status": False, "message": "Lỗi cập nhật mật khẩu!", "data": None}
        return {"status": True, "message": "Đổi mật khẩu thành công!"}

    def kiem_tra_quyen_quan_ly(self, nguoi_thao_tac_id):
        """Kiểm tra người thao tác là Admin/Quản lý đang hoạt động (FR-012)."""
        if not nguoi_thao_tac_id:
            return {"status": False, "message": "Bạn chưa đăng nhập!", "data": None}
        thong_tin = self.dao.lay_thong_tin_user(nguoi_thao_tac_id)
        if not thong_tin:
            return {"status": False, "message": "Tài khoản không tồn tại!", "data": None}
        if thong_tin.get("trang_thai") == "banned":
            return {"status": False,
                    "message": "Tài khoản của bạn đã bị khóa! Vui lòng liên hệ quản trị viên để được hỗ trợ.",
                    "data": None}
        role_id = thong_tin.get("Role_Id") or thong_tin.get("Role_id") or thong_tin.get("role_id")
        ten_vai_tro = self.dao.lay_ten_vai_tro_theo_id(role_id)
        if ten_vai_tro is None:
            return {"status": False, "message": "Dữ liệu vai trò không hợp lệ!", "data": None}
        if ten_vai_tro not in ("Admin", "Quản lý"):
            return {"status": False, "message": "Bạn không có quyền thực hiện chức năng này!", "data": None}
        return {"status": True, "message": "", "data": {"ma_user": nguoi_thao_tac_id, "ten_vai_tro": ten_vai_tro}}

    def kiem_tra_nguoi_dung_hoat_dong(self, nguoi_thao_tac_id):
        """Kiểm tra người dùng đã đăng nhập và không bị khóa (FR-009)."""
        if not nguoi_thao_tac_id:
            return {"status": False, "message": "Bạn chưa đăng nhập!", "data": None}
        thong_tin = self.dao.lay_thong_tin_user(nguoi_thao_tac_id)
        if not thong_tin:
            return {"status": False, "message": "Tài khoản không tồn tại!", "data": None}
        if thong_tin.get("trang_thai") == "banned":
            return {"status": False,
                    "message": "Tài khoản của bạn đã bị khóa! Vui lòng liên hệ quản trị viên để được hỗ trợ.",
                    "data": None}
        return {"status": True, "message": "", "data": {"ma_user": nguoi_thao_tac_id}}

    def cap_nhat_trang_thai(self, nguoi_thao_tac_id, ma_user, trang_thai):
        """Khóa/mở khóa tài khoản: chặn Admin, Quản lý và chính người thao tác (FR-008)."""
        if not ma_user:
            return {"status": False, "message": "Thiếu mã user!"}
        if trang_thai not in ('active', 'banned'):
            return {"status": False, "message": "Trạng thái không hợp lệ!"}

        thong_tin = self.dao.lay_thong_tin_user(ma_user)
        if not thong_tin:
            return {"status": False, "message": "Tài khoản không tồn tại!"}

        # Không được thao tác lên chính tài khoản của mình
        if nguoi_thao_tac_id == ma_user:
            return {"status": False,
                    "message": "Bạn không thể khóa/mở khóa chính tài khoản của mình!"}

        # Không ai có quyền khóa tài khoản Admin (FR-008) — kiểm tra trước khi ghi
        role_id = thong_tin.get("Role_Id") or thong_tin.get("Role_id") or thong_tin.get("role_id")
        ten_vai_tro = self.dao.lay_ten_vai_tro_theo_id(role_id)
        if trang_thai == 'banned' and ten_vai_tro == "Admin":
            return {"status": False, "message": "Không ai có quyền khóa tài khoản Admin!"}
        if trang_thai == 'banned' and ten_vai_tro == "Quản lý":
            return {"status": False, "message": "Không thể khóa tài khoản Quản lý!"}

        ok = self.dao.cap_nhat_trang_thai(ma_user, trang_thai)
        if ok:
            label = "Đã khóa tài khoản!" if trang_thai == 'banned' else "Đã mở khóa tài khoản!"
            return {"status": True, "message": label}
        return {"status": False, "message": "Lỗi cập nhật trạng thái."}

    def cap_lai_mat_khau(self, nguoi_thao_tac_id, ma_user, mat_khau_moi=None):
        """Cấp lại mật khẩu cho user (FR-010/FR-011): sinh ngẫu nhiên hoặc dùng mật
        khẩu Quản lý nhập (≥ 6 ký tự); chặn mục tiêu là Admin; trả mật khẩu mới
        đúng một lần trong data."""
        thong_tin = self.dao.lay_thong_tin_user(ma_user)
        if not thong_tin:
            return {"status": False, "message": "Tài khoản không tồn tại!", "data": None}

        role_id = thong_tin.get("Role_Id") or thong_tin.get("Role_id") or thong_tin.get("role_id")
        ten_vai_tro = self.dao.lay_ten_vai_tro_theo_id(role_id)
        if ten_vai_tro == "Admin":
            return {"status": False,
                    "message": "Không thể cấp lại mật khẩu cho tài khoản Admin!",
                    "data": None}

        if not mat_khau_moi:
            mat_khau_moi = secrets.token_urlsafe(6)[:8]
        elif len(mat_khau_moi) < 6:
            return {"status": False,
                    "message": "Mật khẩu phải có ít nhất 6 ký tự!",
                    "data": None}

        ok = self.dao.cap_nhat_mat_khau(ma_user, mat_khau_moi)
        if not ok:
            return {"status": False, "message": "Lỗi cập nhật mật khẩu!", "data": None}

        return {
            "status": True,
            "message": "Đã cấp lại mật khẩu! Hãy chuyển mật khẩu dưới đây cho người dùng.",
            "data": {
                "ma_user": ma_user,
                "ten_user": thong_tin.get("FullName"),
                "mat_khau_moi": mat_khau_moi
            }
        }