from back_end.DAO.SanPhamDao import SanPhamDao
from back_end.Model.SanPham import SanPham
import inspect

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

    def _doc_moc_gia(self, gia, ten_truong):
        """Chuẩn hóa một mốc giá lọc; trả (giá_float, lỗi). Rỗng/None hợp lệ."""
        if gia is None:
            return None, None
        if isinstance(gia, str):
            gia = gia.strip()
            if gia == "":
                return None, None
        if isinstance(gia, bool):
            return None, {"status": False, "message": f"{ten_truong} không hợp lệ!"}
        try:
            so = float(gia)
        except (TypeError, ValueError):
            return None, {"status": False, "message": f"{ten_truong} không hợp lệ!"}
        if so != so or so in (float("inf"), float("-inf")):
            return None, {"status": False, "message": f"{ten_truong} không hợp lệ!"}
        if so < 0:
            return None, {"status": False, "message": f"{ten_truong} không được âm!"}
        return so, None

    def _dao_loc_gia_duoc(self):
        """Kiểm tra DAO tim_kiem có nhận min_price/max_price không."""
        try:
            tham_so = inspect.signature(self.dao.tim_kiem).parameters
        except (TypeError, ValueError):
            return False
        return "min_price" in tham_so or "max_price" in tham_so

    def _loc_theo_gia(self, danh_sach, gia_min, gia_max):
        """Lọc danh sách theo khoảng giá ở tầng BUS (authoritative)."""
        if gia_min is None and gia_max is None:
            return danh_sach
        ket_qua = []
        for sp in danh_sach or []:
            gia = sp.get("price")
            try:
                gia = float(gia) if gia is not None else None
            except (TypeError, ValueError):
                gia = None
            if gia is None:
                continue
            if gia_min is not None and gia < gia_min:
                continue
            if gia_max is not None and gia > gia_max:
                continue
            ket_qua.append(sp)
        return ket_qua

    def tim_kiem_san_pham(self, tu_khoa, category_id=None,
                          min_price=None, max_price=None):
        """Tìm sản phẩm theo từ khóa/danh mục/khoảng giá, chỉ hàng đang bán."""
        kw = (tu_khoa or "").strip()
        cat = category_id
        if isinstance(cat, str) and not cat.strip():
            cat = None
        if cat not in (None, ""):
            try:
                cat = int(str(cat).strip())
            except (TypeError, ValueError):
                return {"status": False,
                        "message": "Danh mục không hợp lệ!"}
        gia_min, loi = self._doc_moc_gia(min_price, "Giá tối thiểu")
        if loi:
            return loi
        gia_max, loi = self._doc_moc_gia(max_price, "Giá tối đa")
        if loi:
            return loi
        if gia_min is not None and gia_max is not None and gia_min > gia_max:
            return {"status": False,
                    "message": "Giá tối thiểu không được lớn hơn giá tối đa!"}
        if not kw and cat in (None, ""):
            tat_ca = self.dao.lay_tat_ca()
            kinh_doanh = [sp for sp in tat_ca if sp.get("is_active", True)]
            return {"status": True,
                    "data": self._loc_theo_gia(kinh_doanh, gia_min, gia_max)}
        if hasattr(self.dao, "tim_kiem"):
            if self._dao_loc_gia_duoc():
                data = self.dao.tim_kiem(kw, cat, gia_min, gia_max)
            else:
                data = self._loc_theo_gia(
                    self.dao.tim_kiem(kw, cat), gia_min, gia_max)
            return {"status": True, "data": data}
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
        return {"status": True,
                "data": self._loc_theo_gia(ket_qua, gia_min, gia_max)}

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
        try:
            category_id = int(category_id)
        except (TypeError, ValueError):
            return {"status": False, "message": "Danh mục không hợp lệ!"}
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
        ten_sach = str(ten or "").strip()
        if not ten_sach:
            return {"status": False, "message": "Tên sản phẩm không được để trống!"}
        if len(ten_sach) > 200:
            return {"status": False, "message": "Tên sản phẩm không được vượt quá 200 ký tự!"}
        try:
            gia_f = float(gia) if gia is not None else 0
        except (TypeError, ValueError):
            return {"status": False, "message": "Giá sản phẩm phải lớn hơn 0!"}
        if gia_f <= 0:
            return {"status": False, "message": "Giá sản phẩm phải lớn hơn 0!"}
        if not category_id:
            return {"status": False, "message": "Vui lòng chọn danh mục!"}
        try:
            category_id = int(category_id)
        except (TypeError, ValueError):
            return {"status": False, "message": "Danh mục không hợp lệ!"}
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
        mo_ta_sach = str(mo_ta or "").strip()
        if len(mo_ta_sach) > 1000:
            return {"status": False, "message": "Mô tả sản phẩm không được vượt quá 1000 ký tự!"}
        # Phase 4: chong duplicate khong phan biet hoa/thuong trong cung store.
        _trung = getattr(self.dao, "kiem_tra_trung_ten", None)
        if callable(_trung) and _trung(store_id, ten_sach):
            return {"status": False,
                    "message": "Sản phẩm đã tồn tại trong gian hàng, vui lòng chọn từ danh sách!"}
        sp = SanPham(
            ProductName=ten_sach, Description=mo_ta_sach,
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
        if so_luong is not None:
            try:
                if int(so_luong) < 0:
                    return {"status": False, "message": "Số lượng không được âm!"}
            except (TypeError, ValueError):
                return {"status": False, "message": "Số lượng không hợp lệ!"}
        if chu is None or int(chu) != int(store_id):
            return {"status": False, "message": "Không có quyền thao tác trên sản phẩm này!"}
        ten_sach = str(ten or "").strip()
        if not ten_sach:
            return {"status": False, "message": "Tên sản phẩm không được để trống!"}
        if len(ten_sach) > 200:
            return {"status": False, "message": "Tên sản phẩm không được vượt quá 200 ký tự!"}
        try:
            gia_f = float(gia) if gia is not None else 0
        except (TypeError, ValueError):
            return {"status": False, "message": "Giá sản phẩm phải lớn hơn 0!"}
        if gia_f <= 0:
            return {"status": False, "message": "Giá sản phẩm phải lớn hơn 0!"}
        mo_ta_sach = str(mo_ta or "").strip()
        if len(mo_ta_sach) > 1000:
            return {"status": False, "message": "Mô tả sản phẩm không được vượt quá 1000 ký tự!"}
        if not category_id:
            return {"status": False, "message": "Vui lòng chọn danh mục!"}
        try:
            category_id = int(category_id)
        except (TypeError, ValueError):
            return {"status": False, "message": "Danh mục không hợp lệ!"}
        if not self.dao.kiem_tra_category_ton_tai(category_id):
            return {"status": False, "message": "Danh mục không tồn tại, vui lòng chọn danh mục!"}
        _trung = getattr(self.dao, "kiem_tra_trung_ten", None)
        if callable(_trung) and _trung(store_id, ten_sach, product_id):
            return {"status": False, "message": "Sản phẩm đã tồn tại trong gian hàng, vui lòng chọn tên khác!"}
        sp = SanPham(
            ProductId=int(product_id), ProductName=ten_sach, Description=mo_ta_sach,
            Price=gia_f, OldPrice=float(gia_goc) if gia_goc else None,
            Quantity=int(so_luong) if so_luong is not None else 0,
            Emoji=emoji or EMOJI_MAC_DINH, ImageUrl=image_url or None,
            CategoryId=category_id,
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

    def nhap_hang(self, nguoi_id, store_id, product_id, so_luong_nhap,
                  gia_nhap=None, ghi_chu=None, supplier_id=None):
        """Seller nhập thêm tồn kho, ghi log đầy đủ vào phiếu nhập."""
        try:
            sl = int(so_luong_nhap) if so_luong_nhap not in (None, "") else 0
        except (TypeError, ValueError):
            return {"status": False, "message": "Số lượng nhập phải lớn hơn 0!"}
        if sl <= 0:
            return {"status": False, "message": "Số lượng nhập phải lớn hơn 0!"}

        gia_nhap_f = None
        if gia_nhap not in (None, ""):
            try:
                gia_nhap_f = float(gia_nhap)
                if gia_nhap_f < 0:
                    return {"status": False, "message": "Giá nhập không được âm!"}
            except (TypeError, ValueError):
                return {"status": False, "message": "Giá nhập không hợp lệ!"}

        chu = self.dao.lay_store_id(product_id)
        if chu is None or int(chu) != int(store_id):
            return {"status": False, "message": "Không có quyền thao tác trên sản phẩm này!"}

        ket_qua = self.dao.nhap_hang(
            product_id, store_id, sl, nguoi_id,
            unit_cost=gia_nhap_f, note=ghi_chu, supplier_id=supplier_id)
        if ket_qua is None:
            return {"status": False, "message": "Lỗi khi nhập hàng, vui lòng thử lại!"}

        return {"status": True,
                "message": f"Đã nhập thêm {sl} sản phẩm! Tồn kho hiện tại: {ket_qua['quantity']}.",
                "data": ket_qua}

    def lay_lich_su_nhap_hang(self, store_id, top=50):
        if not store_id:
            return {"status": False, "message": "Thiếu ID gian hàng!", "data": []}
        return {"status": True, "data": self.dao.lay_lich_su_nhap_hang(store_id, top)}

    def doi_gia_ban(self, nguoi_id, store_id, product_id, gia_moi,
                    gia_goc=None, gia_khuyen_mai=None, giam_gia=None):
        """Seller doi gia ban: legacy (gia_moi) + Phase 4 discount model.

        Phase 4: giam_gia bat → Price=discount, OldPrice=original,
        yeu cau 0 <= discount < original. Tat → Price=original, OldPrice=None.
        discount_percent do backend tu tinh, khong tin client.
        """
        chu = self.dao.lay_store_id(product_id)
        if chu is None or int(chu) != int(store_id):
            return {"status": False, "message": "Không có quyền thao tác trên sản phẩm này!"}
        if gia_goc is None and gia_khuyen_mai is None and giam_gia is None:
            try:
                g = float(gia_moi) if gia_moi is not None else 0
            except (TypeError, ValueError):
                return {"status": False, "message": "Giá bán phải lớn hơn 0!"}
            if g <= 0:
                return {"status": False, "message": "Giá bán phải lớn hơn 0!"}
            ok = self.dao.doi_gia(product_id, store_id, g)
            if ok:
                return {"status": True, "message": "Đã cập nhật giá bán!",
                        "data": {"price": g}}
            return {"status": False, "message": "Lỗi khi cập nhật giá, vui lòng thử lại!"}
        bat_giam = giam_gia in (True, 1, "1", "true", "True", "on", "ON")
        if bat_giam:
            goc, loi = self._doc_moc_gia(gia_goc, "Giá gốc")
            if loi:
                return loi
            km, loi = self._doc_moc_gia(gia_khuyen_mai, "Giá khuyến mãi")
            if loi:
                return loi
            if goc is None or goc <= 0:
                return {"status": False, "message": "Giá gốc phải lớn hơn 0!"}
            if km is None:
                return {"status": False,
                        "message": "Giá khuyến mãi phải lớn hơn hoặc bằng 0!"}
            if not km < goc:
                return {"status": False,
                        "message": "Giá khuyến mãi phải nhỏ hơn giá gốc!"}
            gia_ban, gia_cu = km, goc
        else:
            goc_nguon = gia_goc if gia_goc is not None else gia_moi
            goc, loi = self._doc_moc_gia(goc_nguon, "Giá gốc")
            if loi:
                return loi
            if goc is None or goc <= 0:
                return {"status": False, "message": "Giá gốc phải lớn hơn 0!"}
            gia_ban, gia_cu = goc, None
        _cap_nhat = getattr(self.dao, "cap_nhat_gia", None)
        if callable(_cap_nhat):
            ok = _cap_nhat(product_id, store_id, gia_ban, gia_cu)
        else:
            ok = self.dao.doi_gia(product_id, store_id, gia_ban)
        if not ok:
            return {"status": False, "message": "Lỗi khi cập nhật giá, vui lòng thử lại!"}
        du_lieu = {"price": gia_ban, "old_price": gia_cu,
                   "giam_gia": bool(bat_giam)}
        if bat_giam:
            du_lieu["discount_percent"] = round((1 - gia_ban / gia_cu) * 100, 2)
        return {"status": True, "message": "Đã cập nhật giá bán!",
                "data": du_lieu}

    # ─── PHASE 4: AUTOCOMPLETE + NHAP BULK + TAO TU PHIEU NHAP ───────────────

    def tim_kiem_cua_seller(self, store_id, tu_khoa, limit=10):
        """Phase 4: autocomplete san pham trong store cua seller."""
        if not store_id:
            return {"status": False, "message": "Thiếu ID gian hàng!", "data": []}
        kw = str(tu_khoa or "").strip()
        if not kw:
            return {"status": True, "data": []}
        _tim = getattr(self.dao, "tim_kiem_theo_store", None)
        if callable(_tim):
            return {"status": True, "data": _tim(store_id, kw, limit)}
        tat_ca = self.dao.lay_theo_store_ca_an_hien(store_id)
        kw_thuong = kw.lower()
        ket_qua = [sp for sp in (tat_ca or [])
                   if kw_thuong in str(sp.get("name") or "").lower()]
        try:
            limit = int(limit or 10)
        except (TypeError, ValueError):
            limit = 10
        return {"status": True, "data": ket_qua[:max(1, min(limit, 20))]}

    @staticmethod
    def _doc_so_luong_nhap(value):
        """Phase 4: quantity phai la integer > 0 (reject 0/-1/1.5/abc/null/bool)."""
        if isinstance(value, bool) or value in (None, ""):
            return None
        if isinstance(value, int):
            return value if value > 0 else None
        if isinstance(value, float):
            return int(value) if value.is_integer() and value > 0 else None
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return None
            try:
                f = float(s)
            except (TypeError, ValueError):
                return None
            if not f.is_integer() or f <= 0:
                return None
            return int(f)
        return None

    @staticmethod
    def _doc_gia_khong_am(value, ten_truong):
        """Phase 4: gia phai numeric >= 0 (None = khong gui)."""
        if value in (None, ""):
            return None, None
        if isinstance(value, bool):
            return None, {"status": False, "message": f"{ten_truong} không hợp lệ!"}
        try:
            so = float(str(value).strip() if isinstance(value, str) else value)
        except (TypeError, ValueError):
            return None, {"status": False, "message": f"{ten_truong} không hợp lệ!"}
        if so != so or so in (float("inf"), float("-inf")):
            return None, {"status": False, "message": f"{ten_truong} không hợp lệ!"}
        if so < 0:
            return None, {"status": False, "message": f"{ten_truong} không được âm!"}
        return so, None

    def nhap_hang_nhieu(self, nguoi_id, store_id, items, ghi_chu_chung=None):
        """Phase 4: nhap nhieu dong 1 phieu; gop duplicate; bo qua NewStock."""
        if not store_id:
            return {"status": False, "message": "Thiếu ID gian hàng!"}
        if not isinstance(items, list) or not items:
            return {"status": False,
                    "message": "Phiếu nhập phải có ít nhất một sản phẩm!"}
        gop = {}
        thu_tu = []
        for dong in items:
            if not isinstance(dong, dict):
                return {"status": False,
                        "message": "Dòng nhập hàng không hợp lệ!"}
            ma_sp = dong.get("product_id", dong.get("ProductId"))
            ten_sp = dong.get("product_name", dong.get("ProductName"))
            if ma_sp in (None, ""):
                if not ten_sp or not str(ten_sp).strip():
                    return {"status": False,
                            "message": "Mỗi dòng phải có sản phẩm (mã hoặc tên)!"}
                _tim_ten = getattr(self.dao, "tim_theo_ten_trong_store", None)
                tim_thay = _tim_ten(store_id, str(ten_sp).strip()) \
                    if callable(_tim_ten) else None
                if not tim_thay:
                    return {"status": False,
                            "message": "Không tìm thấy sản phẩm "
                                     f"'{str(ten_sp).strip()}'. "
                                     "Hãy tạo sản phẩm mới trước khi nhập!"}
                ma_sp = tim_thay.get("id")
            try:
                if isinstance(ma_sp, bool):
                    raise ValueError
                ma_sp = int(str(ma_sp).strip() if isinstance(ma_sp, str) else ma_sp)
            except (TypeError, ValueError):
                return {"status": False, "message": "Mã sản phẩm không hợp lệ!"}
            chu = self.dao.lay_store_id(ma_sp)
            if chu is None:
                return {"status": False,
                        "message": f"Sản phẩm #{ma_sp} không tồn tại!"}
            if int(chu) != int(store_id):
                return {"status": False,
                        "message": "Không có quyền thao tác trên sản phẩm này!"}
            sl = self._doc_so_luong_nhap(
                dong.get("quantity", dong.get("Quantity")))
            if sl is None:
                return {"status": False,
                        "message": "Số lượng nhập phải là số nguyên lớn hơn 0!"}
            gia_raw = dong.get("unit_cost",
                               dong.get("gia_nhap", dong.get("UnitCost")))
            gia, loi = self._doc_gia_khong_am(gia_raw, "Giá nhập")
            if loi:
                return loi
            if ma_sp not in gop:
                gop[ma_sp] = {"product_id": ma_sp, "quantity": 0, "_tien": 0.0}
                thu_tu.append(ma_sp)
            gop[ma_sp]["_tien"] += (gia or 0.0) * sl
            gop[ma_sp]["quantity"] += sl
        danh_sach = []
        for pid in thu_tu:
            g = gop[pid]
            don_gia = round(g["_tien"] / g["quantity"], 2) if g["quantity"] else 0.0
            danh_sach.append({"product_id": pid, "quantity": g["quantity"],
                              "unit_cost": don_gia})
        _bulk = getattr(self.dao, "nhap_hang_bulk", None)
        if callable(_bulk):
            ket_qua = _bulk(store_id, nguoi_id, danh_sach, ghi_chu_chung)
        else:
            ket_qua_items = []
            for it in danh_sach:
                r = self.dao.nhap_hang(it["product_id"], store_id,
                                        it["quantity"], nguoi_id,
                                        unit_cost=it["unit_cost"])
                if r is None:
                    return {"status": False,
                            "message": "Lỗi khi nhập hàng, vui lòng thử lại!"}
                ket_qua_items.append({"product_id": it["product_id"],
                                      "quantity": it["quantity"],
                                      "stock_moi": r.get("quantity")})
            ket_qua = {"receipt_id": None, "items": ket_qua_items}
        if ket_qua is None:
            return {"status": False,
                    "message": "Lỗi khi nhập hàng, vui lòng thử lại!"}
        return {"status": True,
                "message": f"Đã nhập {len(danh_sach)} sản phẩm thành công!",
                "data": ket_qua}

    def tao_va_nhap(self, nguoi_id, store_id, ten, so_luong, gia_ban=None,
                    mo_ta=None, category_id=None, emoji=None, image_url=None,
                    gia_nhap=None, ghi_chu=None):
        """Phase 4: tao SP moi tu phieu nhap (thieu field = default hop le)."""
        if not store_id:
            return {"status": False, "message": "Thiếu ID gian hàng!"}
        ten_sach = str(ten or "").strip()
        if not ten_sach:
            return {"status": False,
                    "message": "Tên sản phẩm không được để trống!"}
        _trung = getattr(self.dao, "kiem_tra_trung_ten", None)
        if callable(_trung) and _trung(store_id, ten_sach):
            return {"status": False,
                    "message": "Sản phẩm đã tồn tại trong gian hàng, "
                             "vui lòng chọn từ danh sách!"}
        sl = self._doc_so_luong_nhap(so_luong)
        if sl is None:
            return {"status": False,
                    "message": "Số lượng nhập phải là số nguyên lớn hơn 0!"}
        gia_ban_f, loi = self._doc_gia_khong_am(
            0 if gia_ban in (None, "") else gia_ban, "Giá bán")
        if loi:
            return loi
        gia_nhap_f, loi = self._doc_gia_khong_am(
            0 if gia_nhap in (None, "") else gia_nhap, "Giá nhập")
        if loi:
            return loi
        cat = category_id if category_id not in (None, "") else CATEGORY_MAC_DINH
        try:
            cat = int(cat)
        except (TypeError, ValueError):
            return {"status": False, "message": "Danh mục không hợp lệ!"}
        _kt_cat = getattr(self.dao, "kiem_tra_category_ton_tai", None)
        if callable(_kt_cat) and not _kt_cat(cat):
            return {"status": False,
                    "message": "Danh mục không tồn tại, vui lòng chọn danh mục!"}
        _tao = getattr(self.dao, "tao_va_nhap", None)
        if callable(_tao):
            ket_qua = _tao(store_id, nguoi_id, ten_sach, sl, gia_ban_f,
                           mo_ta, cat, emoji or EMOJI_MAC_DINH, image_url,
                           gia_nhap_f, ghi_chu)
        else:
            new_id = self.dao.them(SanPham(
                ProductName=ten_sach, Description=mo_ta,
                Price=float(gia_ban_f or 1), OldPrice=None, Quantity=0,
                SoldCount=0, Emoji=emoji or EMOJI_MAC_DINH,
                ImageUrl=image_url or None, CategoryId=cat,
                StoreId=int(store_id), IsActive=1))
            if not new_id:
                return {"status": False,
                        "message": "Lỗi khi tạo sản phẩm, vui lòng thử lại!"}
            r = self.dao.nhap_hang(new_id, store_id, sl, nguoi_id,
                                    unit_cost=gia_nhap_f, note=ghi_chu)
            if r is None:
                return {"status": False,
                        "message": "Lỗi khi nhập hàng, vui lòng thử lại!"}
            ket_qua = {"product_id": new_id, "quantity": sl,
                       "receipt_id": r.get("receipt_id")}
        if ket_qua is None:
            return {"status": False,
                    "message": "Lỗi khi tạo sản phẩm, vui lòng thử lại!"}
        return {"status": True,
                "message": f"Đã tạo sản phẩm '{ten_sach}' và nhập {sl} sản phẩm!",
                "data": ket_qua}
