from Model.User import Khach
from DAO.UserDao import UserDao
class UserBus:
    def __init__(self):
        self.userdao = UserDao()
    def dangkykhachhang(self,ten_user,dia_chi,sdt,tendangnhap,mat_khau):

        if not ten_user or not sdt or not tendangnhap or not mat_khau:
            return {"status": False, "message": "Vui lòng điền đầy đủ Tên, SĐT, Tên đăng nhập và Mật khẩu!"}
        if len(mat_khau<6):
                return {"status": False, "message": "Mật khẩu phải có ít nhất 6 ký tự!"}
        if self.dao.kiem_tra_tendangnhap_ton_tai(tendangnhap):
            return {"status": False, "message": f"Tên đăng nhập '{tendangnhap}' đã có người sử dụng!"}

        khach_moi = Khach(
            ten_user=ten_user,
            dia_chi=dia_chi,
            sdt=sdt,
            tendangnhap=tendangnhap,
            mat_khau=mat_khau
        )

        is_success = self.dao.them_khach_hang(khach_moi)

        if is_success:
            return {"status": True, "message": "Đăng ký tài khoản thành công!"}
        else:
            return {"status": False, "message": "Lỗi hệ thống khi lưu dữ liệu, vui lòng thử lại."}
