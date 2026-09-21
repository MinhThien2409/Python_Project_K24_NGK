"""Unit test US2 BUS bỏ qua rating — 006 T012/T014 (test-first Đỏ-Xanh).

Mock DAO — KHÔNG chạm PobbyDB thật.
Kỳ vọng SAU implement: them/sua kèm rating vẫn PASS, không lưu rating.
Trước implement: FAIL vì BUS còn tham số rating / validate rating.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.SanPhamBus import SanPhamBus


class DaoGia:
    """Mock DAO tối thiểu cho BUS loại bỏ đánh giá."""

    def __init__(self):
        self.da_them = None
        self.da_sua = None
        self.da_sua_store = None

    def kiem_tra_category_ton_tai(self, category_id):
        return True

    def them(self, sp):
        self.da_them = sp
        # BUS mới KHÔNG còn gán Rating → Model không còn attr Rating
        assert not hasattr(sp, "Rating"), "Model SanPham vẫn còn field Rating"
        return 1

    def sua(self, sp):
        self.da_sua = sp
        assert not hasattr(sp, "Rating"), "Model SanPham vẫn còn field Rating"
        return True

    def sua_theo_store(self, sp, store_id):
        self.da_sua_store = (sp, store_id)
        assert not hasattr(sp, "Rating"), "Model SanPham vẫn còn field Rating"
        return True

    def lay_store_id(self, product_id):
        return 6


def _bus_voi_dao_gia():
    bus = SanPhamBus()
    dao = DaoGia()
    bus.dao = dao
    return bus, dao


def _goi_them(bus, **ghi_de):
    tham_so = dict(
        ten="Tai nghe Bluetooth", mo_ta="Chống ồn ANC",
        gia=890000, gia_goc=1200000, so_luong=40,
        emoji="📦", image_url=None, category_id=14, store_id=6,
    )
    tham_so.update(ghi_de)
    # SAU implement BUS không còn tham số rating → gọi kèm rating phải TypeError
    # nếu vẫn nhận rating nghĩa là chưa dọn → ép FAIL rõ ràng
    import inspect
    sig = inspect.signature(bus.them_san_pham)
    assert "rating" not in sig.parameters, "BUS.them_san_pham vẫn còn tham số rating"
    return bus.them_san_pham(**tham_so)


def _goi_sua(bus, **ghi_de):
    tham_so = dict(
        product_id=1, ten="Tai nghe Bluetooth", mo_ta="Chống ồn ANC",
        gia=890000, gia_goc=1200000, so_luong=40,
        emoji="📦", image_url=None, category_id=14, store_id=6,
    )
    tham_so.update(ghi_de)
    import inspect
    sig = inspect.signature(bus.sua_san_pham)
    assert "rating" not in sig.parameters, "BUS.sua_san_pham vẫn còn tham số rating"
    return bus.sua_san_pham(**tham_so)


# ── T012: them/sua kèm rating vẫn PASS, validate giữ nguyên ──
def test_them_khong_con_tham_so_rating_va_pass():
    bus, dao = _bus_voi_dao_gia()
    kq = _goi_them(bus)
    assert kq["status"] is True
    assert dao.da_them is not None
    assert not hasattr(dao.da_them, "Rating")


def test_sua_khong_con_tham_so_rating_va_pass():
    bus, dao = _bus_voi_dao_gia()
    kq = _goi_sua(bus)
    assert kq["status"] is True
    assert not hasattr(dao.da_sua, "Rating")


def test_validate_ten_gia_danh_muc_store_giu_nguyen():
    bus, _ = _bus_voi_dao_gia()
    kq = _goi_them(bus, ten="   ")
    assert kq["status"] is False
    assert "Tên sản phẩm" in kq["message"]
    kq = _goi_them(bus, gia=0)
    assert kq["status"] is False
    assert "Giá sản phẩm" in kq["message"]


def test_seller_them_sua_khong_con_tham_so_rating():
    import inspect
    bus, dao = _bus_voi_dao_gia()
    assert "rating" not in inspect.signature(bus.them_san_pham_cua_seller).parameters
    assert "rating" not in inspect.signature(bus.sua_san_pham_cua_seller).parameters
    kq = bus.them_san_pham_cua_seller(
        1, 6, "Tai nghe", "Mô tả", 890000, 1200000, 40, 14)
    assert kq["status"] is True
    kq = bus.sua_san_pham_cua_seller(
        1, 6, 1, "Tai nghe", "Mô tả", 890000, 1200000, 40, 14)
    assert kq["status"] is True


# ── T014: ca biên rating None/5/"xxx" đều không lưu, không crash ──
def test_model_khong_con_field_rating():
    from back_end.Model.SanPham import SanPham
    import inspect
    assert "Rating" not in inspect.signature(SanPham.__init__).parameters
    sp = SanPham(ProductName="X", Price=1000, Quantity=1, CategoryId=1, StoreId=6)
    assert not hasattr(sp, "Rating")


def test_dao_to_dict_khong_con_khoa_rating():
    from back_end.DAO.SanPhamDao import SanPhamDao
    import inspect
    src = inspect.getsource(SanPhamDao._to_dict)
    assert '"rating"' not in src and "'rating'" not in src
    assert "Rating" not in src
