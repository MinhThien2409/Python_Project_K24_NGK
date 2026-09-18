"""Unit test BUS san pham seller — US1 + US3 (T011/T013/T032).

Test-first: viet truoc, FAIL truoc khi co implementation.
Mock DAO — KHONG cham PobbyDB that.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.SanPhamBus import SanPhamBus
from tests.conftest import MockSanPhamDao


def _bus(store_cua_sp=None, ton_tai_category=True, ket_qua_ghi=True, ton_kho_moi=0):
    bus = SanPhamBus()
    bus.dao = MockSanPhamDao(
        store_cua_sp=store_cua_sp, ton_tai_category=ton_tai_category,
        ket_qua_ghi=ket_qua_ghi, ton_kho_moi=ton_kho_moi)
    return bus


# ── US1: them/sua/an_hien sai chu (T011) ──
def test_them_san_pham_cua_seller_ok():
    bus = _bus(ton_tai_category=True)
    kq = bus.them_san_pham_cua_seller(3, 10, "Hoa hong", "Dep", 100000, None, 5, 1)
    assert kq["status"] is True
    assert "product_id" in kq


def test_them_san_pham_sai_chu_shop_khac():
    # Them luon gan store tu session nen khong co sai chu;
    # sai chu xay ra o sua/an_hien — them van ok voi store that
    bus = _bus()
    kq = bus.them_san_pham_cua_seller(3, 10, "Hoa", None, 50000, None, 1, 1)
    assert kq["status"] is True


def test_sua_san_pham_cua_seller_sai_chu():
    bus = _bus(store_cua_sp={7: 99})
    kq = bus.sua_san_pham_cua_seller(3, 10, 7, "Ten", None, 50000, None, 1, 1)
    assert kq["status"] is False
    assert "quyền" in kq["message"]


def test_sua_san_pham_cua_seller_ok():
    bus = _bus(store_cua_sp={7: 10})
    kq = bus.sua_san_pham_cua_seller(3, 10, 7, "Ten moi", None, 50000, None, 1, 1)
    assert kq["status"] is True


def test_an_hien_sai_chu():
    bus = _bus(store_cua_sp={7: 99})
    kq = bus.an_hien_san_pham_cua_seller(3, 10, 7, 0)
    assert kq["status"] is False
    assert "quyền" in kq["message"]


def test_an_hien_ok():
    bus = _bus(store_cua_sp={7: 10})
    kq = bus.an_hien_san_pham_cua_seller(3, 10, 7, 0)
    assert kq["status"] is True


# ── US1 edge: ten rong, gia am, SL am, category khong ton tai (T013) ──
def test_them_ten_rong():
    bus = _bus()
    kq = bus.them_san_pham_cua_seller(3, 10, "   ", None, 50000, None, 1, 1)
    assert kq["status"] is False
    assert "Tên sản phẩm" in kq["message"]


def test_them_gia_am():
    bus = _bus()
    kq = bus.them_san_pham_cua_seller(3, 10, "Hoa", None, -100, None, 1, 1)
    assert kq["status"] is False
    assert "Giá sản phẩm" in kq["message"]


def test_them_sl_am():
    bus = _bus()
    kq = bus.them_san_pham_cua_seller(3, 10, "Hoa", None, 50000, None, -5, 1)
    assert kq["status"] is False
    assert "Số lượng" in kq["message"]


def test_them_category_khong_ton_tai():
    bus = _bus(ton_tai_category=False)
    kq = bus.them_san_pham_cua_seller(3, 10, "Hoa", None, 50000, None, 1, 999)
    assert kq["status"] is False
    assert "danh mục" in kq["message"]


# ── US3: nhap_hang + doi_gia_ban (T032) ──
def test_nhap_hang_ok():
    bus = _bus(store_cua_sp={5: 10}, ton_kho_moi=15)
    kq = bus.nhap_hang(3, 10, 5, 10)
    assert kq["status"] is True
    assert "10" in kq["message"]


def test_nhap_hang_am_0_rong():
    bus = _bus(store_cua_sp={5: 10})
    for sl in (-5, 0, None, ""):
        kq = bus.nhap_hang(3, 10, 5, sl)
        assert kq["status"] is False
        assert "Số lượng nhập" in kq["message"]


def test_nhap_hang_sai_chu():
    bus = _bus(store_cua_sp={5: 99})
    kq = bus.nhap_hang(3, 10, 5, 10)
    assert kq["status"] is False
    assert "quyền" in kq["message"]


def test_doi_gia_ok():
    bus = _bus(store_cua_sp={5: 10})
    kq = bus.doi_gia_ban(3, 10, 5, 199000)
    assert kq["status"] is True


def test_doi_gia_0_am():
    bus = _bus(store_cua_sp={5: 10})
    for g in (0, -100):
        kq = bus.doi_gia_ban(3, 10, 5, g)
        assert kq["status"] is False
        assert "Giá bán" in kq["message"]


def test_doi_gia_sai_chu():
    bus = _bus(store_cua_sp={5: 99})
    kq = bus.doi_gia_ban(3, 10, 5, 199000)
    assert kq["status"] is False
    assert "quyền" in kq["message"]
