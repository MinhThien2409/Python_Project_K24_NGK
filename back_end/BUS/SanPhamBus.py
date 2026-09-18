from back_end.DAO.SanPhamDao import SanPhamDao
from back_end.Model.SanPham import SanPham

# ─── Hằng số sản phẩm (T048: gom magic value đầu file) ───
SO_LUONG_BAN_CHAY_MAC_DINH = 10
EMOJI_MAC_DINH = "📦"
CATEGORY_MAC_DINH = 1


class SanPhamBus:
    def __init__(self):
        """Khởi tạo BUS sản phẩm với DAO tương ứng."""
        self.dao = SanPhamDao()

    # ─── LẤY DỮ LIỆU ────────────────────────────────────────────────────────

    def lay_tat_ca(self):
        """Lấy toàn bộ sản phẩm."""
        data = self.dao.lay_tat_ca()
        return {"status": True, "data": data}

    def lay_theo_id(self, product_id):
        """Lấy sản phẩm theo mã."""
        if not product_id:
            return {"status": False, "message": "Thiếu ID sản phẩm!"}
        sp = self.dao.lay_theo_id(product_id)
        if sp:
            return {"status": True, "data": sp}
        return {"status": False, "message": "Không tìm thấy sản phẩm!"}

    def lay_theo_store(self, store_id):
        """Lấy sản phẩm đang kinh doanh của gian hàng."""
        if not store_id:
            return {"status": False, "message": "Thiếu ID gian hàng!"}
        data = self.dao.lay_theo_store(store_id)
        return {"status": True, "data": data}

    def lay_ban_chay(self, top=SO_LUONG_BAN_CHAY_MAC_DINH):
        """Lấy danh sách sản phẩm bán chạy nhất."""
        data = self.dao.lay_ban_chay(top)
        return {"status": True, "data": data}

    def tim_kiem_san_pham(self, tu_khoa, category_id=None):
        """Tìm sản phẩm theo từ khóa, chỉ lấy hàng đang kinh doanh."""
        kw = (tu_khoa or "").strip()
        cat = category_id
        if isinstance(cat, str) and not cat.strip():
            cat = None
        if not kw and cat in (None, ""):
            tat_ca = self.dao.lay_tat_ca()
            return {"status": True, "data": [sp for sp in tat_ca
                                             if sp.get("is_active", True)]}
        if hasattr(self.dao, "tim_kiem"):
            return {"status": True, "data": self.dao.tim_kiem(kw, cat)}
        tat_ca = self.dao.lay_tat_ca()
        kw_thuong = kw.lower()
        ket_qua = []
        for sp in tat_ca:
            if not sp.get("is_active", True):
                continue
            if cat not in (None, "") and sp.get("category_id") != int(cat):
                continue
            if kw_thuong and kw_thuong not in (sp.get("name") or "").lower():
                continue
            ket_qua.append(sp)
        return {"status": True, "data": ket_qua}

    # ─── THÊM SẢN PHẨM ──────────────────────────────────────────────────────

    def them_san_pham(self, ten, mo_ta, gia, gia_goc,
                     so_luong, emoji, image_url,
                     category_id, store_id, **_bo_qua):
        """Thêm sản phẩm mới sau khi kiểm tra giá và tồn kho."""
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
            SoldCount   = 0,
            Emoji       = emoji or EMOJI_MAC_DINH,
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
                     so_luong, emoji, image_url, category_id, store_id, **_bo_qua):
        """Cập nhật sản phẩm sau khi kiểm tra tên và giá."""
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
            Emoji       = emoji or EMOJI_MAC_DINH,
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
        """Xóa mềm sản phẩm theo mã."""
        if not product_id:
            return {"status": False, "message": "Thiếu ID sản phẩm!"}
        ok = self.dao.xoa(product_id)
        if ok:
            return {"status": True, "message": "Đã xóa sản phẩm thành công!"}
        return {"status": False, "message": "Lỗi khi xóa sản phẩm!"}

    # ─── CẬP NHẬT SỐ LƯỢNG BÁN ─────────────────────────────────────────────

    def cap_nhat_so_luong_ban(self, product_id, so_luong):
        """Cập nhật số lượng đã bán sau khi kiểm tra tồn kho."""
        if not product_id or not so_luong:
            return {"status": False, "message": "Thiếu thông tin!"}
        ok = self.dao.cap_nhat_so_luong_ban(product_id, int(so_luong))
        if ok:
            return {"status": True, "message": "Cập nhật số lượng thành công!"}
        return {"status": False,
                "message": "Lỗi cập nhật — có thể sản phẩm không đủ hàng!"}

    def lay_theo_store_cua_seller(self, store_id):
        """Lấy toàn bộ sản phẩm của shop cho Seller kể cả hàng ẩn."""
        if not store_id:
            return {"status": False, "message": "Thiếu ID gian hàng!", "data": []}
        data = self.dao.lay_theo_store_ca_an_hien(store_id)
        return {"status": True, "data": data}

    # ─── SELLER: QUAN LY SAN PHAM CUA SHOP (004 US1) ─────────────────────────

    def them_san_pham_cua_seller(self, nguoi_id, store_id, ten, mo_ta, gia,
                                 gia_goc, so_luong, category_id,
                                 emoji=None, image_url=None, **_bo_qua):
        """Seller thêm sản phẩm mới vào gian hàng của mình."""
        if not ten or not str(ten).strip():
            return {"status": False, "message": "Tên sản phẩm không được để trống!"}
        try:
            gia_f = float(gia) if gia is not None else 0
        except (TypeError, ValueError):
            return {"status": False, "message": "Giá sản phẩm phải lớn hơn 0!"}
        if gia_f <= 0:
            return {"status": False, "message": "Giá sản phẩm phải lớn hơn 0!"}
        if not category_id:
            return {"status": False, "message": "Vui lòng chọn danh mục!"}
        if not store_id:
            return {"status": False, "message": "Thiếu thông tin gian hàng!"}
        if so_luong is not None:
            try:
                if int(so_luong) < 0:
                    return {"status": False, "message": "Số lượng không được âm!"}
            except (TypeError, ValueError):
                return {"status": False, "message": "Số lượng không được âm!"}
        if not self.dao.kiem_tra_category_ton_tai(category_id):
            return {"status": False, "message": "Danh mục không tồn tại, vui lòng chọn danh mục!"}
        sp = SanPham(
            ProductName=str(ten).strip(), Description=mo_ta,
            Price=gia_f, OldPrice=float(gia_goc) if gia_goc else None,
            Quantity=int(so_luong) if so_luong is not None else 0,
            SoldCount=0,
            Emoji=emoji or EMOJI_MAC_DINH, ImageUrl=image_url or None,
            CategoryId=int(category_id), StoreId=int(store_id), IsActive=1)
        new_id = self.dao.them(sp)
        if new_id:
            return {"status": True,
                    "message": f"Đã thêm sản phẩm '{str(ten).strip()}' thành công!",
                    "product_id": new_id}
        return {"status": False, "message": "Lỗi khi thêm sản phẩm, vui lòng thử lại!"}

    def sua_san_pham_cua_seller(self, nguoi_id, store_id, product_id, ten, mo_ta,
                                gia, gia_goc, so_luong, category_id,
                                emoji=None, image_url=None, **_bo_qua):
        """Seller sửa sản phẩm của shop mình, chặn shop khác."""
        if not product_id:
            return {"status": False, "message": "Thiếu ID sản phẩm!"}
        chu = self.dao.lay_store_id(product_id)
        if chu is None or int(chu) != int(store_id):
            return {"status": False, "message": "Không có quyền thao tác trên sản phẩm này!"}
        if not ten or not str(ten).strip():
            return {"status": False, "message": "Tên sản phẩm không được để trống!"}
        try:
            gia_f = float(gia) if gia is not None else 0
        except (TypeError, ValueError):
            return {"status": False, "message": "Giá sản phẩm phải lớn hơn 0!"}
        if gia_f <= 0:
            return {"status": False, "message": "Giá sản phẩm phải lớn hơn 0!"}
        sp = SanPham(
            ProductId=int(product_id), ProductName=str(ten).strip(), Description=mo_ta,
            Price=gia_f, OldPrice=float(gia_goc) if gia_goc else None,
            Quantity=int(so_luong) if so_luong is not None else 0,
            Emoji=emoji or EMOJI_MAC_DINH, ImageUrl=image_url or None,
            CategoryId=int(category_id) if category_id else CATEGORY_MAC_DINH,
            StoreId=int(store_id), IsActive=1)
        ok = self.dao.sua_theo_store(sp, store_id)
        if ok:
            return {"status": True, "message": "Cập nhật sản phẩm thành công!"}
        return {"status": False, "message": "Lỗi khi cập nhật sản phẩm!"}

    def an_hien_san_pham_cua_seller(self, nguoi_id, store_id, product_id, is_active):
        """Seller ẩn hoặc hiện sản phẩm của shop mình."""
        if not product_id:
            return {"status": False, "message": "Thiếu ID sản phẩm!"}
        chu = self.dao.lay_store_id(product_id)
        if chu is None or int(chu) != int(store_id):
            return {"status": False, "message": "Không có quyền thao tác trên sản phẩm này!"}
        ok = self.dao.an_hien_theo_store(product_id, store_id, is_active)
        if ok:
            ten = "hiện" if int(is_active) else "ẩn"
            return {"status": True, "message": f"Đã {ten} sản phẩm thành công!"}
        return {"status": False, "message": "Lỗi khi cập nhật sản phẩm!"}

    # ─── SELLER: NHAP HANG + GIA BAN (004 US3) ───────────────────────────────

    def nhap_hang(self, nguoi_id, store_id, product_id, so_luong_nhap):
        """Seller nhập thêm tồn kho, cộng dồn số lượng."""
        try:
            sl = int(so_luong_nhap) if so_luong_nhap not in (None, "") else 0
        except (TypeError, ValueError):
            return {"status": False, "message": "Số lượng nhập phải lớn hơn 0!"}
        if sl <= 0:
            return {"status": False, "message": "Số lượng nhập phải lớn hơn 0!"}
        chu = self.dao.lay_store_id(product_id)
        if chu is None or int(chu) != int(store_id):
            return {"status": False, "message": "Không có quyền thao tác trên sản phẩm này!"}
        ton_moi = self.dao.nhap_hang(product_id, store_id, sl)
        if ton_moi is None:
            return {"status": False, "message": "Lỗi khi nhập hàng, vui lòng thử lại!"}
        return {"status": True,
                "message": f"Đã nhập thêm {sl} sản phẩm! Tồn kho hiện tại: {ton_moi}."}

    def doi_gia_ban(self, nguoi_id, store_id, product_id, gia_moi):
        """Seller doi gia ban, giu OldPrice khi giam gia."""
        try:
            g = float(gia_moi) if gia_moi is not None else 0
        except (TypeError, ValueError):
            return {"status": False, "message": "Giá bán phải lớn hơn 0!"}
        if g <= 0:
            return {"status": False, "message": "Giá bán phải lớn hơn 0!"}
        chu = self.dao.lay_store_id(product_id)
        if chu is None or int(chu) != int(store_id):
            return {"status": False, "message": "Không có quyền thao tác trên sản phẩm này!"}
        ok = self.dao.doi_gia(product_id, store_id, g)
        if ok:
            return {"status": True, "message": "Đã cập nhật giá bán!",
                    "data": {"price": g}}
        return {"status": False, "message": "Lỗi khi cập nhật giá, vui lòng thử lại!"}