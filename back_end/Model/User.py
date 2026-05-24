class User:
    def __init__(self,ma_user=None,ten_user=None,dia_chi=None,sdt=None,vai_tro=None,tendangnhap=None,mat_khau=None):
        self.ma_user=ma_user
        self.ten_user=ten_user
        self.dia_chi=dia_chi
        self.sdt=sdt
        self.vai_tro=vai_tro
        self.tendangnhap=tendangnhap
        self.mat_khau=mat_khau

class Khach(User):
    def __init__(self, ma_user=None, ten_user=None, dia_chi=None, sdt=None, tendangnhap=None, mat_khau=None):
        super().__init__(ma_user, ten_user, dia_chi, sdt, 'Khach', tendangnhap, mat_khau)

class NguoiBan(User):
    def __init__(self, ma_user=None, ten_user=None, dia_chi=None, sdt=None, cmnd=None, ma_gian_hang=None, tendangnhap=None, mat_khau=None):
        super().__init__(ma_user, ten_user, dia_chi, sdt, 'NguoiBan', tendangnhap, mat_khau)
        self.cmnd = cmnd
        self.ma_gian_hang = ma_gian_hang
