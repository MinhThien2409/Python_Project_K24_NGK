class NhomQuyen:
    def __init__(self,Ma_Nhom=None,Ten_Nhom=None):
        self.Ma_Nhom = Ma_Nhom
        self.Ten_Nhom = Ten_Nhom
class ChucNang:
    def __init__(self,Ma_Chuc_Nang=None,Ten_Chuc_Nang=None):
        self.Ma_Chuc_Nang = Ma_Chuc_Nang
        self.Ten_Chuc_Nang = Ten_Chuc_Nang
class NhomQuyenCT:
    def __init__(self, ma_nhom=None, ma_chuc_nang=None, xem=False, them=False, sua=False, xoa=False):
        self.ma_nhom = ma_nhom
        self.ma_chuc_nang = ma_chuc_nang
        self.xem = xem
        self.them = them
        self.sua = sua
        self.xoa = xoa
class PhanQuyenCaNhan:
    def __init__(self, ma_user=None, ma_chuc_nang=None, xem=False, them=False, sua=False, xoa=False, is_custom=False):
        self.ma_user = ma_user
        self.ma_chuc_nang = ma_chuc_nang
        self.xem = xem
        self.them = them
        self.sua = sua
        self.xoa = xoa

        self.is_custom = is_custom