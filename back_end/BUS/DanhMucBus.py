from back_end.DAO.DanhMucDao import DanhMucDao
from back_end.Model.DanhMuc import DanhMuc

# ─── Hằng số validate danh mục (T048) ───
TEN_DANH_MUC_TOI_DA = 100


class DanhMucBus:
    def __init__(self):
        """Khởi tạo BUS danh mục với DAO tương ứng."""
        self.dao = DanhMucDao()

    def lay_tat_ca(self):
        """Lấy toàn bộ danh mục."""
        data = self.dao.lay_tat_ca()
        return {"status": True, "data": data}

    def them_category(self, ten, phi_san=0):
        ten = (ten or "").strip()
        if not ten:
            return {"status": False, "message": "Tên danh mục không được để trống!"}
        if len(ten) > TEN_DANH_MUC_TOI_DA:
            return {"status": False, "message": "Tên danh mục quá dài (tối đa 100 ký tự)!"}
        if self.dao.kiem_tra_ten_ton_tai(ten):
            return {"status": False, "message": f"Danh mục '{ten}' đã tồn tại!"}

        try:
            phi_san = float(phi_san)
            if phi_san < 0 or phi_san > 50:
                return {"status": False, "message": "Phí sàn phải từ 0% đến 50%!"}
        except:
            return {"status": False, "message": "Phí sàn không hợp lệ!"}

        ok = self.dao.them(DanhMuc(CategoryName=ten, PlatformFeePercent=phi_san))
        if ok:
            return {"status": True, "message": f"Đã thêm danh mục '{ten}' thành công!"}
        return {"status": False, "message": "Lỗi khi thêm danh mục!"}

    def sua_category(self, category_id, ten_moi, phi_san=0):
        ten_moi = (ten_moi or "").strip()
        if not ten_moi:
            return {"status": False, "message": "Tên danh mục không được để trống!"}
        if len(ten_moi) > TEN_DANH_MUC_TOI_DA:
            return {"status": False, "message": "Tên danh mục quá dài (tối đa 100 ký tự)!"}
        if self.dao.kiem_tra_ten_ton_tai(ten_moi, tru_id=category_id):
            return {"status": False, "message": f"Danh mục '{ten_moi}' đã tồn tại!"}

        try:
            phi_san = float(phi_san)
            if phi_san < 0 or phi_san > 50:
                return {"status": False, "message": "Phí sàn phải từ 0% đến 50%!"}
        except:
            return {"status": False, "message": "Phí sàn không hợp lệ!"}

        ok = self.dao.sua(DanhMuc(CategoryId=category_id, CategoryName=ten_moi,
                                  PlatformFeePercent=phi_san))
        if ok:
            return {"status": True, "message": "Đã cập nhật danh mục thành công!"}
        return {"status": False, "message": "Không tìm thấy danh mục!"}

    def xoa_category(self, category_id):
        """Xóa danh mục khi không còn sản phẩm thuộc về."""
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