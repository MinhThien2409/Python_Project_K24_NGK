from back_end.Model.User import User
from back_end.DAO.UserDao import UserDao
import re
import secrets

# ── 005 US5: hằng số validate SĐT khách (đầu file, G6) ──
SDT_REGEX_KHACH = r"^0\d{9}$"


class UserBus:
    def __init__(self):
        """Khởi tạo BUS người dùng với DAO người dùng."""
        self.dao = UserDao()

    def dang_ky_khach_hang(self, ten_user, dia_chi, sdt, tendangnhap, mat_khau):
        """Đăng ký tài khoản khách hàng mới, gán cứng nhóm quyền Customer."""
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
        """Xác thực đăng nhập, trả envelope kèm vai trò hiển thị."""
        loi = self._kiem_tra_dau_vao_dang_nhap(tendangnhap, mat_khau)
        if loi:
            return loi
        user = self.dao.dang_nhap(tendangnhap, mat_khau)
        loi = self._xu_ly_tai_khoan_dac_biet(user)
        if loi:
            return loi
        ten_vai_tro, loi = self._lay_ten_vai_tro_hop_le(user)
        if loi:
            return loi
        return self._dong_goi_ket_qua_dang_nhap(user, ten_vai_tro)

    def _kiem_tra_dau_vao_dang_nhap(self, tendangnhap, mat_khau):
        """Validate rỗng tài khoản/mật khẩu, trả lỗi hoặc None."""
        if not tendangnhap or not mat_khau:
            return {"status": False, "message": "Vui lòng nhập tài khoản và mật khẩu!", "data": None}
        return None

    def _xu_ly_tai_khoan_dac_biet(self, user):
        """Chặn tài khoản bị khóa, vai trò hỏng hoặc sai thông tin."""
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
        return None

    def _lay_ten_vai_tro_hop_le(self, user):
        """Lấy tên vai trò của user, trả (tên, lỗi)."""
        ten_vai_tro = self.dao.lay_ten_vai_tro_theo_id(user.ma_nhom_quyen)
        if not ten_vai_tro:
            return None, {
                "status": False,
                "message": "Dữ liệu vai trò không hợp lệ! Vui lòng liên hệ quản trị viên.",
                "data": None
            }
        return ten_vai_tro, None

    def _dong_goi_ket_qua_dang_nhap(self, user, ten_vai_tro):
        """Đóng gói envelope đăng nhập thành công kèm hồ sơ user."""
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
        """Lấy toàn bộ danh sách người dùng cho quản trị."""
        danh_sach = self.dao.lay_danh_sach_user()
        return {"status": True, "data": danh_sach}

    def cap_nhat_user(self, ma_user, ten_user, dia_chi, sdt,cmnd):
        """Cập nhật thông tin người dùng kèm validate tên và SĐT."""
        if not ma_user or not ten_user:
            return {"status": False, "message": "Tên người dùng không được để trống!"}
        ten = str(ten_user).strip()
        if not ten:
            return {"status": False, "message": "Tên người dùng không được để trống!"}
        sdt_sach = (sdt or "").strip() if sdt else ""
        if sdt_sach and not re.match(SDT_REGEX_KHACH, sdt_sach):
            return {"status": False, "message": "Số điện thoại không hợp lệ!"}
        dia_chi_sach = (dia_chi or "").strip() if dia_chi else dia_chi
        if len(ten) > 100 or len(sdt_sach) > 20 or (dia_chi_sach and len(dia_chi_sach) > 255):
            return {"status": False, "message": "Thông tin quá dài, vui lòng rút gọn!"}

        is_success = self.dao.cap_nhat_user(ma_user, ten, dia_chi, sdt,cmnd)
        if is_success:
            return {"status": True, "message": "Cập nhật thông tin thành công!"}
        else:
            return {"status": False, "message": "Không tìm thấy User hoặc lỗi cập nhật."}

    def cap_nhat_thong_tin_cua_toi(self, nguoi_id, ma_user, ten_user, dia_chi, sdt, cmnd):
        """Sua ho so cua chinh minh, chan thao tac tai khoan khac."""
        if int(nguoi_id or 0) != int(ma_user or 0):
            return {"status": False, "message": "Không thể thao tác trên tài khoản khác!"}
        return self.cap_nhat_user(ma_user, ten_user, dia_chi, sdt, cmnd)

    def doi_mat_khau_cua_toi(self, nguoi_id, ma_user, mat_khau_cu, mat_khau_moi):
        """Doi MK cua chinh minh, chan thao tac tai khoan khac."""
        if int(nguoi_id or 0) != int(ma_user or 0):
            return {"status": False, "message": "Không thể thao tác trên tài khoản khác!"}
        return self.doi_mat_khau(ma_user, mat_khau_cu, mat_khau_moi)

    def xoa_user(self, ma_user):
        """Xóa người dùng theo mã, báo lỗi khi mã không hợp lệ."""
        if not ma_user:
            return {"status": False, "message": "Mã User không hợp lệ!"}

        is_success = self.dao.xoa_user(ma_user)
        if is_success:
            return {"status": True, "message": "Đã xóa người dùng thành công!"}
        else:
            return {"status": False, "message": "Lỗi khi xóa người dùng."}

    def lay_thong_tin_user(self, ma_user):
        """Lấy thông tin chi tiết một người dùng theo mã."""
        return self.dao.lay_thong_tin_user(ma_user)

    def lay_ten_vai_tro_theo_id(self, role_id):
        """Lấy tên vai trò theo mã nhóm quyền."""
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
        """Kiểm tra người thao tác là Quản lý đang hoạt động (009: thu hẹp còn Quản lý)."""
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
        if ten_vai_tro != "Quản lý":
            return {"status": False, "message": "Bạn không có quyền thực hiện chức năng này!", "data": None}
        return {"status": True, "message": "", "data": {"ma_user": nguoi_thao_tac_id, "ten_vai_tro": ten_vai_tro}}

    def kiem_tra_quyen_xem_danh_sach(self, nguoi_thao_tac_id):
        """Kiểm tra người thao tác có quyền xem danh sách tài khoản người dùng —
        Admin HOẶC Quản lý (015 FR-012)."""
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

    def kiem_tra_quyen_duyet_seller(self, nguoi_thao_tac_id):
        """Kiểm tra người thao tác là Quản lý — quyền duyệt/từ chối người bán (009)."""
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
        if ten_vai_tro != "Quản lý":
            return {"status": False, "message": "Bạn không có quyền thực hiện chức năng này!", "data": None}
        return {"status": True, "message": "", "data": {"ma_user": nguoi_thao_tac_id, "ten_vai_tro": ten_vai_tro}}

    def kiem_tra_quyen_admin(self, nguoi_thao_tac_id):
        """Kiểm tra người thao tác là Admin duy nhất đang hoạt động (FR-008)."""
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
        if ten_vai_tro != "Admin":
            return {"status": False, "message": "Bạn không có quyền thực hiện chức năng này!", "data": None}
        return {"status": True, "message": "", "data": {"ma_user": nguoi_thao_tac_id, "ten_vai_tro": ten_vai_tro}}

    def tao_quan_ly(self, ten_user, tendangnhap, mat_khau, sdt=None, dia_chi=None, vai_tro=None, **kwargs):
        """Tạo tài khoản Quản lý mới, gán cứng Role_Id=2, chặn mọi yêu cầu Admin."""
        if self._yeu_cau_admin(vai_tro, kwargs):
            return {"status": False, "message": "Không thể tạo thêm tài khoản Admin!"}
        ten = (ten_user or "").strip()
        dang_nhap = (tendangnhap or "").strip()
        if not ten or not dang_nhap or not mat_khau:
            return {"status": False, "message": "Vui lòng điền đầy đủ Tên, Tên đăng nhập và Mật khẩu!"}
        if len(mat_khau) < 6:
            return {"status": False, "message": "Mật khẩu phải có ít nhất 6 ký tự!"}
        sdt_sach = (sdt or "").strip() or None
        dia_chi_sach = (dia_chi or "").strip() or None
        if len(ten) > 100 or len(dang_nhap) > 50:
            return {"status": False, "message": "Thông tin quá dài, vui lòng rút gọn!"}
        if sdt_sach and len(sdt_sach) > 20:
            return {"status": False, "message": "Thông tin quá dài, vui lòng rút gọn!"}
        if dia_chi_sach and len(dia_chi_sach) > 255:
            return {"status": False, "message": "Thông tin quá dài, vui lòng rút gọn!"}
        if self.dao.kiem_tra_tendangnhap_ton_tai(dang_nhap):
            return {"status": False, "message": f"Tên đăng nhập '{dang_nhap}' đã có người sử dụng!"}
        ma_moi = self.dao.them_quan_ly(ten, dia_chi_sach, sdt_sach, dang_nhap, mat_khau)
        if not ma_moi:
            return {"status": False, "message": "Lỗi hệ thống khi lưu dữ liệu, vui lòng thử lại."}
        return {"status": True, "message": "Đã tạo tài khoản Quản lý!",
                "data": {"ma_user": ma_moi, "ten_user": ten, "tendangnhap": dang_nhap}}

    def _yeu_cau_admin(self, vai_tro, kwargs):
        """Kiểm tra input có yêu cầu vai trò Admin hay không."""
        ung_vien = [vai_tro, kwargs.get("vai_tro"), kwargs.get("role"),
                    kwargs.get("ma_nhom_quyen"), kwargs.get("Role_Id")]
        for gia_tri in ung_vien:
            if gia_tri in (1, "1", "Admin", "admin"):
                return True
        return False

    def sua_quan_ly(self, ma_user, ten_user, dia_chi, sdt):
        """Sửa thông tin Quản lý, chỉ FullName/Address/Phone, chặn mục tiêu Admin."""
        if not ten_user or not str(ten_user).strip():
            return {"status": False, "message": "Tên người dùng không được để trống!"}
        thong_tin = self.dao.lay_thong_tin_user(ma_user)
        if not thong_tin:
            return {"status": False, "message": "Tài khoản Quản lý không tồn tại!"}
        role_id = thong_tin.get("Role_Id") or thong_tin.get("Role_id") or thong_tin.get("role_id")
        if role_id == 1 or self.dao.lay_ten_vai_tro_theo_id(role_id) == "Admin":
            return {"status": False, "message": "Không thể sửa tài khoản Admin qua chức năng này!"}
        if role_id != 2:
            return {"status": False, "message": "Tài khoản Quản lý không tồn tại!"}
        ten = str(ten_user).strip()
        dia_chi_sach = (dia_chi or "").strip() or None
        sdt_sach = (sdt or "").strip() or None
        ok = self.dao.cap_nhat_quan_ly(ma_user, ten, dia_chi_sach, sdt_sach)
        if ok:
            return {"status": True, "message": "Cập nhật thông tin thành công!"}
        return {"status": False, "message": "Tài khoản Quản lý không tồn tại!"}

    def xoa_quan_ly(self, ma_user):
        """Xóa cứng tài khoản Quản lý, chặn mục tiêu Admin."""
        if not ma_user:
            return {"status": False, "message": "Tài khoản Quản lý không tồn tại!"}
        thong_tin = self.dao.lay_thong_tin_user(ma_user)
        if not thong_tin:
            return {"status": False, "message": "Tài khoản Quản lý không tồn tại!"}
        role_id = thong_tin.get("Role_Id") or thong_tin.get("Role_id") or thong_tin.get("role_id")
        if role_id == 1 or self.dao.lay_ten_vai_tro_theo_id(role_id) == "Admin":
            return {"status": False, "message": "Không thể xóa tài khoản Admin!"}
        if role_id != 2:
            return {"status": False, "message": "Tài khoản Quản lý không tồn tại!"}
        ok = self.dao.xoa_quan_ly(ma_user)
        if ok:
            return {"status": True, "message": "Đã xóa tài khoản Quản lý!"}
        return {"status": False, "message": "Tài khoản Quản lý không tồn tại!"}

    def lay_danh_sach_quan_ly(self):
        """Lấy danh sách chỉ Quản lý, không mật khẩu."""
        danh_sach = self.dao.lay_danh_sach_quan_ly()
        return {"status": True, "message": "", "data": danh_sach}

    def kiem_tra_quyen_seller(self, nguoi_thao_tac_id):
        """Kiem tra nguoi thao tac la Seller duy nhat dang hoat dong (004 FR-010)."""
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
        if ten_vai_tro != "Seller":
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

    def cap_nhat_trang_thai(self, nguoi_thao_tac_id, ma_user, trang_thai,
                            vai_tro_nguoi_thao_tac=None):
        """Khóa/mở khóa Seller/Khách hàng bởi phiên Quản lý hợp lệ."""
        if not ma_user:
            return {"status": False, "message": "Thiếu mã user!"}
        if trang_thai not in ('active', 'banned'):
            return {"status": False, "message": "Trạng thái không hợp lệ!"}
        if vai_tro_nguoi_thao_tac != "Quản lý":
            return {"status": False, "message": "Bạn không có quyền thực hiện chức năng này!"}

        thong_tin = self.dao.lay_thong_tin_user(ma_user)
        if not thong_tin:
            return {"status": False, "message": "Tài khoản không tồn tại!"}

        if int(nguoi_thao_tac_id or 0) == int(ma_user or 0):
            return {"status": False,
                    "message": "Bạn không thể khóa/mở khóa chính tài khoản của mình!"}

        role_id = thong_tin.get("Role_Id") or thong_tin.get("Role_id") or thong_tin.get("role_id")
        ten_vai_tro = self.dao.lay_ten_vai_tro_theo_id(role_id)
        if ten_vai_tro not in ("Seller", "Customer", "Khách hàng"):
            return {"status": False,
                    "message": "Quản lý chỉ được khóa/mở khóa tài khoản Seller hoặc Khách hàng!"}

        ok = self.dao.cap_nhat_trang_thai(ma_user, trang_thai)
        if ok:
            label = "Đã khóa tài khoản!" if trang_thai == 'banned' else "Đã mở khóa tài khoản!"
            return {"status": True, "message": label}
        return {"status": False, "message": "Lỗi cập nhật trạng thái."}

    def cap_lai_mat_khau(self, nguoi_thao_tac_id, ma_user, mat_khau_moi=None):
        """Cấp lại mật khẩu cho Seller/Khách hàng bởi Quản lý."""
        gate = self.kiem_tra_quyen_quan_ly(nguoi_thao_tac_id)
        if not gate.get("status"):
            return gate
        thong_tin = self.dao.lay_thong_tin_user(ma_user)
        if not thong_tin:
            return {"status": False, "message": "Tài khoản không tồn tại!", "data": None}

        role_id = thong_tin.get("Role_Id") or thong_tin.get("Role_id") or thong_tin.get("role_id")
        ten_vai_tro = self.dao.lay_ten_vai_tro_theo_id(role_id)
        if ten_vai_tro not in ("Seller", "Customer", "Khách hàng"):
            return {"status": False,
                    "message": "Quản lý chỉ được cấp lại mật khẩu cho Seller hoặc Khách hàng!",
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