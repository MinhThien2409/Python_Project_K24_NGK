from back_end.Model.GianHang import GianHang
from back_end.DAO.GianHangDao import GianHangDao

class GianHangBus:
    def __init__(self):
        self.dao = GianHangDao()
    def dang_ky_gian_hang(self,gianhang:GianHang):
        if not gianhang.StoreName or not gianhang.UserId:
            return {
                'status':False,"message":"Tên cửa hàng và UserId không được để trống"
            }

        is_success=self.dao.them_gianhang(gianhang)
        if is_success:
            return{
                'status':True,"message":" Mở gian hàng thành công! "
            }
        else:
            return{
                'status':False,"message" :"Không thể mở gian hàng, Vui lòng thử lại sau!"
            }