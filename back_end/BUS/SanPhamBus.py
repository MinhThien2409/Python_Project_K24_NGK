from back_end.DAO.SanPhamDao import SanPhamDao
from back_end.Model.SanPham import SanPham


class SanPhamBus:
    def __init__(self):
        self.dao = SanPhamDao()

    # ─── LẤY DỮ LIỆU ────────────────────────────────────────────────────────

    def lay_tat_ca(self):
        data = self.dao.lay_tat_ca()
        return {"status": True, "data": data}

    def lay_theo_id(self, product_id):
        if not product_id:
            return {"status": False, "message": "Thiếu ID sản phẩm!"}
        sp = self.dao.lay_theo_id(product_id)
        if sp:
            return {"status": True, "data": sp}
        return {"status": False, "message": "Không tìm thấy sản phẩm!"}

    def lay_theo_store(self, store_id):
        if not store_id:
            return {"status": False, "message": "Thiếu ID gian hàng!"}
        data = self.dao.lay_theo_store(store_id)
        return {"status": True, "data": data}

    def lay_ban_chay(self, top=10):
        data = self.dao.lay_ban_chay(top)
        return {"status": True, "data": data}

    # ─── THÊM SẢN PHẨM ──────────────────────────────────────────────────────

    def them_san_pham(self, ten, mo_ta, gia, gia_goc,
                     so_luong, rating, emoji,image_url,
                     category_id, store_id):
        # Validate
        if not ten or not ten.strip():
            return {"status": False, "message": "Tên sản phẩm không được để trống!"}
        if not gia or float(gia) <= 0:
            return {"status": False, "message": "Giá sản phẩm phải lớn hơn 0!"}
        if not category_id:
            return {"status": False, "message": "Vui lòng chọn danh mục!"}
        if not store_id:
            return {"status": False, "message": "Thiếu thông tin gian hàng!"}
        if so_luong is not None and int(so_luong) < 0:
            return {"status": False, "message": "Số lượng không được âm!"}

        sp = SanPham(
            ProductName = ten.strip(),
            Description = mo_ta,
            Price       = float(gia),
            OldPrice    = float(gia_goc) if gia_goc else None,
            Quantity    = int(so_luong) if so_luong is not None else 0,
            Rating      = float(rating) if rating else 4.5,
            SoldCount   = 0,
            Emoji       = emoji or "📦",
            ImageUrl    = image_url or None,
            CategoryId  = int(category_id),
            StoreId     = int(store_id),
            IsActive    = 1
        )

        new_id = self.dao.them(sp)
        if new_id:
            return {"status": True,
                    "message": f"Đã thêm sản phẩm '{ten}' thành công!",
                    "product_id": new_id}
        return {"status": False, "message": "Lỗi khi thêm sản phẩm, vui lòng thử lại!"}

    # ─── SỬA SẢN PHẨM ───────────────────────────────────────────────────────

    def sua_san_pham(self, product_id, ten, mo_ta, gia, gia_goc,
                     so_luong, rating, emoji,image_url, category_id, store_id):
        if not product_id:
            return {"status": False, "message": "Thiếu ID sản phẩm!"}
        if not ten or not ten.strip():
            return {"status": False, "message": "Tên sản phẩm không được để trống!"}
        if not gia or float(gia) <= 0:
            return {"status": False, "message": "Giá sản phẩm phải lớn hơn 0!"}

        sp = SanPham(
            ProductId   = int(product_id),
            ProductName = ten.strip(),
            Description = mo_ta,
            Price       = float(gia),
            OldPrice    = float(gia_goc) if gia_goc else None,
            Quantity    = int(so_luong) if so_luong is not None else 0,
            Rating      = float(rating) if rating else 4.5,
            Emoji       = emoji or "📦",
            ImageUrl    = image_url or None,
            CategoryId  = int(category_id),
            StoreId     = int(store_id),
            IsActive    = 1
        )

        ok = self.dao.sua(sp)
        if ok:
            return {"status": True, "message": "Cập nhật sản phẩm thành công!"}
        return {"status": False, "message": "Lỗi khi cập nhật sản phẩm!"}

    # ─── XÓA SẢN PHẨM (xóa mềm) ────────────────────────────────────────────

    def xoa_san_pham(self, product_id):
        if not product_id:
            return {"status": False, "message": "Thiếu ID sản phẩm!"}
        ok = self.dao.xoa(product_id)
        if ok:
            return {"status": True, "message": "Đã xóa sản phẩm thành công!"}
        return {"status": False, "message": "Lỗi khi xóa sản phẩm!"}

    # ─── CẬP NHẬT SỐ LƯỢNG BÁN ─────────────────────────────────────────────

    def cap_nhat_so_luong_ban(self, product_id, so_luong):
        if not product_id or not so_luong:
            return {"status": False, "message": "Thiếu thông tin!"}
        ok = self.dao.cap_nhat_so_luong_ban(product_id, int(so_luong))
        if ok:
            return {"status": True, "message": "Cập nhật số lượng thành công!"}
        return {"status": False,
                "message": "Lỗi cập nhật — có thể sản phẩm không đủ hàng!"}