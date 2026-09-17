from back_end.DAO.DanhMucDao import DanhMucDao
from back_end.Model.DanhMuc import DanhMuc

class DanhMucBus:
    def __init__(self):
        self.dao = DanhMucDao()

    def lay_tat_ca(self):
        data = self.dao.lay_tat_ca()
        return {"status": True, "data": data}

    def them_category(self, ten):
        ten = (ten or "").strip()
        if not ten:
            return {"status": False, "message": "Tên danh mục không được để trống!"}
        if len(ten) > 100:
            return {"status": False, "message": "Tên danh mục quá dài (tối đa 100 ký tự)!"}
        if self.dao.kiem_tra_ten_ton_tai(ten):
            return {"status": False, "message": f"Danh mục '{ten}' đã tồn tại!"}
        ok = self.dao.them(DanhMuc(CategoryName=ten))
        if ok:
            return {"status": True, "message": f"Đã thêm danh mục '{ten}' thành công!"}
        return {"status": False, "message": "Lỗi khi thêm danh mục!"}

    def sua_category(self, category_id, ten_moi):
        ten_moi = (ten_moi or "").strip()
        if not ten_moi:
            return {"status": False, "message": "Tên danh mục không được để trống!"}
        if len(ten_moi) > 100:
            return {"status": False, "message": "Tên danh mục quá dài (tối đa 100 ký tự)!"}
        if self.dao.kiem_tra_ten_ton_tai(ten_moi, tru_id=category_id):
            return {"status": False, "message": f"Danh mục '{ten_moi}' đã tồn tại!"}
        ok = self.dao.sua(DanhMuc(CategoryId=category_id, CategoryName=ten_moi))
        if ok:
            return {"status": True, "message": "Đã cập nhật danh mục thành công!"}
        return {"status": False, "message": "Không tìm thấy danh mục!"}

    def xoa_category(self, category_id):
        if not category_id:
            return {"status": False, "message": "Thiếu ID danh mục!"}
        dem = self.dao.dem_san_pham(category_id)
        if dem is None:
            return {"status": False, "message": "Không tìm thấy danh mục!"}
        if dem > 0:
            return {"status": False,
                    "message": "Danh mục đang có sản phẩm, không thể xóa! Hãy chuyển sản phẩm sang danh mục khác rồi thử lại."}
        ok = self.dao.xoa(category_id)
        if ok:
            return {"status": True, "message": "Đã xóa danh mục thành công!"}
        return {"status": False, "message": "Không tìm thấy danh mục!"}