"""Unit test Phase 4 — Stock/Import BUS (strict quantity, gop, ownership).

Fake DAO in-memory — KHONG cham PobbyDB that.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.SanPhamBus import SanPhamBus
from tests.conftest import FakeSanPhamStore


def _bus():
    store = FakeSanPhamStore(
        san_pham={
            1: {"id": 1, "name": "Ao Thun", "price": 100000,
                "quantity": 5, "store_id": 10, "category_id": 1,
                "is_active": True},
            2: {"id": 2, "name": "Shop Khac", "price": 50000,
                "quantity": 7, "store_id": 20, "category_id": 1,
                "is_active": True},
        },
        categories={1: "Thoi trang"})
    bus = SanPhamBus()
    bus.dao = store
    return bus, store


# ── Quantity integer > 0: 0/-1/1.5/abc/null/bool deu reject ──
def test_so_luong_khong_hop_le_bi_tu_choi():
    bus, _ = _bus()
    for xau in (0, -1, "0", "-3", "abc", "", None, True, False,
                1.5, "1.5", "10x", float("nan")):
        kq = bus.nhap_hang_nhieu(3, 10, [{"product_id": 1, "quantity": xau}])
        assert kq["status"] is False, xau
        assert "Số lượng" in kq["message"]


def test_so_luong_dang_chuoi_so_hop_le():
    bus, store = _bus()
    kq = bus.nhap_hang_nhieu(3, 10, [{"product_id": 1, "quantity": "10"}])
    assert kq["status"] is True
    assert store.san_pham[1]["quantity"] == 5 + 10


# ── Stock moi = cu + nhap (bo qua NewStock client) ──
def test_ton_moi_bang_cu_cong_nhap_bo_qua_new_stock():
    bus, store = _bus()
    kq = bus.nhap_hang_nhieu(3, 10, [{"product_id": 1, "quantity": 3,
                                      "new_stock": 9999, "NewStock": 9999}])
    assert kq["status"] is True
    assert store.san_pham[1]["quantity"] == 5 + 3
    assert kq["data"]["items"][0]["stock_moi"] == 8


# ── Gop dong trung: 1 phieu, tong so luong ──
def test_gop_dong_trung_thanh_mot():
    bus, store = _bus()
    kq = bus.nhap_hang_nhieu(3, 10, [{"product_id": 1, "quantity": 3},
                                      {"product_id": 1, "quantity": 2}])
    assert kq["status"] is True
    assert len(kq["data"]["items"]) == 1
    assert kq["data"]["items"][0]["quantity"] == 5
    assert store.san_pham[1]["quantity"] == 5 + 5


def test_nhieu_dong_nhieu_sp_ok():
    bus, store = _bus()
    store.san_pham[3] = {"id": 3, "name": "Quan", "price": 1,
                         "quantity": 0, "store_id": 10, "category_id": 1,
                         "is_active": True}
    kq = bus.nhap_hang_nhieu(3, 10, [{"product_id": 1, "quantity": 2},
                                      {"product_id": 3, "quantity": 4}],
                                      ghi_chu_chung="dot 1")
    assert kq["status"] is True
    assert len(kq["data"]["items"]) == 2
    assert store.san_pham[1]["quantity"] == 7
    assert store.san_pham[3]["quantity"] == 4


# ── Ownership + resolve bang ten ──
def test_nhap_sp_shop_khac_bi_tu_choi():
    bus, _ = _bus()
    kq = bus.nhap_hang_nhieu(3, 10, [{"product_id": 2, "quantity": 1}])
    assert kq["status"] is False
    assert "quyền" in kq["message"]


def test_nhap_sp_khong_ton_tai_bi_tu_choi():
    bus, _ = _bus()
    kq = bus.nhap_hang_nhieu(3, 10, [{"product_id": 999, "quantity": 1}])
    assert kq["status"] is False


def test_resolve_bang_ten_khac_hoa_thuong():
    bus, store = _bus()
    kq = bus.nhap_hang_nhieu(3, 10, [{"product_name": "  AO THUN ",
                                      "quantity": 2}])
    assert kq["status"] is True
    assert store.san_pham[1]["quantity"] == 7


def test_ten_khong_ton_tai_goi_y_tao_moi():
    bus, _ = _bus()
    kq = bus.nhap_hang_nhieu(3, 10, [{"product_name": "SP Chua Co",
                                      "quantity": 2}])
    assert kq["status"] is False
    assert "tạo sản phẩm mới" in kq["message"]


def test_phieu_rong_va_dong_sai_bi_tu_choi():
    bus, _ = _bus()
    assert bus.nhap_hang_nhieu(3, 10, [])["status"] is False
    assert bus.nhap_hang_nhieu(3, 10, None)["status"] is False
    assert bus.nhap_hang_nhieu(3, 10, ["x"])["status"] is False
    assert bus.nhap_hang_nhieu(3, 10, [{"quantity": 2}])["status"] is False
    assert bus.nhap_hang_nhieu(3, None, [{"product_id": 1,
                                          "quantity": 2}])["status"] is False
