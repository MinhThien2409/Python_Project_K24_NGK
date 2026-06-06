from back_end.DAO.DanhMucDao import DanhMucDao
from back_end.Model.DanhMuc import DanhMuc

class DanhMucBus:
    def __init__(self):
        self.dao = DanhMucDao()

    def lay_tat_ca(self):
        data = self.dao.lay_tat_ca()
        return {"status": True, "data": data}

    def them_category(self, ten):
        if not ten or not ten.strip():
            return {"status": False, "message": "Tên danh mục không được để trống!"}
        ok = self.dao.them(DanhMuc(CategoryName=ten.strip()))
        if ok:
            return {"status": True, "message": f"Đã thêm danh mục '{ten}' thành công!"}
        return {"status": False, "message": "Lỗi khi thêm danh mục!"}

    def sua_category(self, category_id, ten_moi):
        if not ten_moi or not ten_moi.strip():
            return {"status": False, "message": "Tên danh mục không được để trống!"}
        ok = self.dao.sua(DanhMuc(CategoryId=category_id, CategoryName=ten_moi.strip()))
        if ok:
            return {"status": True, "message": "Đã cập nhật danh mục thành công!"}
        return {"status": False, "message": "Lỗi khi cập nhật danh mục!"}

    def xoa_category(self, category_id):
        if not category_id:
            return {"status": False, "message": "Thiếu ID danh mục!"}
        ok = self.dao.xoa(category_id)
        if ok:
            return {"status": True, "message": "Đã xóa danh mục thành công!"}
        return {"status": False, "message": "Lỗi khi xóa danh mục (có thể đang có sản phẩm thuộc danh mục này)!"}