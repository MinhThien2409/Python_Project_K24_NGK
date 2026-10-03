"""Unit test Phase 4 — Price BUS (discount model + tampering).

Fake DAO in-memory — KHONG cham PobbyDB that.
Quy uoc: giam_gia bat → Price=KM, OldPrice=goc (KM < goc).
Tat → Price=goc, OldPrice=None (khong active KM).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.SanPhamBus import SanPhamBus
from tests.conftest import FakeSanPhamStore


def _bus():
    store = FakeSanPhamStore(
        san_pham={
            1: {"id": 1, "name": "Ao", "price": 100000, "old_price": None,
                "quantity": 5, "store_id": 10, "category_id": 1,
                "is_active": True},
            2: {"id": 2, "name": "Shop Khac", "price": 50000,
                "old_price": None, "quantity": 7, "store_id": 20,
                "category_id": 1, "is_active": True},
        },
        categories={1: "Thoi trang"})
    bus = SanPhamBus()
    bus.dao = store
    return bus, store


# ── Legacy path (chi gia_moi) giu nguyen behavior cu ──
def test_legacy_gia_moi_ok():
    bus, store = _bus()
    kq = bus.doi_gia_ban(3, 10, 1, 80000)
    assert kq["status"] is True
    assert store.san_pham[1]["price"] == 80000


def test_legacy_gia_sai_bi_tu_choi():
    bus, _ = _bus()
    for xau in (0, -5, "abc", None):
        assert bus.doi_gia_ban(3, 10, 1, xau)["status"] is False, xau


# ── Giam gia BAT: KM < goc ──
def test_bat_giam_gia_hop_le():
    bus, store = _bus()
    kq = bus.doi_gia_ban(3, 10, 1, None, gia_goc=100000,
                         gia_khuyen_mai=80000, giam_gia=True)
    assert kq["status"] is True
    assert store.san_pham[1]["price"] == 80000
    assert store.san_pham[1]["old_price"] == 100000
    assert kq["data"]["discount_percent"] == 20.0


def test_bat_giam_gia_km_bang_hoac_lon_hon_goc_bi_tu_choi():
    bus, _ = _bus()
    for km in (100000, 120000):
        kq = bus.doi_gia_ban(3, 10, 1, None, gia_goc=100000,
                             gia_khuyen_mai=km, giam_gia=True)
        assert kq["status"] is False, km
        assert "nhỏ hơn giá gốc" in kq["message"]


def test_bat_giam_gia_thieu_km_hoac_goc_bi_tu_choi():
    bus, _ = _bus()
    assert bus.doi_gia_ban(3, 10, 1, None, gia_goc=100000,
                           giam_gia=True)["status"] is False
    assert bus.doi_gia_ban(3, 10, 1, None, gia_khuyen_mai=80000,
                           giam_gia=True)["status"] is False
    assert bus.doi_gia_ban(3, 10, 1, None, gia_goc=0,
                           gia_khuyen_mai=0, giam_gia=True)["status"] is False
    assert bus.doi_gia_ban(3, 10, 1, None, gia_goc="abc",
                           gia_khuyen_mai=1, giam_gia=True)["status"] is False


# ── Giam gia TAT: ban dung gia goc, khong active KM ──
def test_tat_giam_gia_xoa_old_price():
    bus, store = _bus()
    store.san_pham[1]["old_price"] = 100000
    store.san_pham[1]["price"] = 80000
    kq = bus.doi_gia_ban(3, 10, 1, None, gia_goc=100000, giam_gia=False)
    assert kq["status"] is True
    assert store.san_pham[1]["price"] == 100000
    assert store.san_pham[1]["old_price"] is None
    assert "discount_percent" not in kq["data"]


def test_tat_giam_gia_km_gui_kem_bi_bo_qua():
    bus, store = _bus()
    kq = bus.doi_gia_ban(3, 10, 1, None, gia_goc=90000,
                         gia_khuyen_mai=1, giam_gia=False)
    assert kq["status"] is True
    assert store.san_pham[1]["price"] == 90000
    assert store.san_pham[1]["old_price"] is None


# ── Ownership + tampering: discount_percent backend tu tinh ──
def test_doi_gia_shop_khac_bi_tu_choi():
    bus, _ = _bus()
    kq = bus.doi_gia_ban(3, 10, 2, None, gia_goc=100000,
                         gia_khuyen_mai=80000, giam_gia=True)
    assert kq["status"] is False
    assert "quyền" in kq["message"]


def test_discount_percent_backend_tu_tinh():
    bus, _ = _bus()
    kq = bus.doi_gia_ban(3, 10, 1, None, gia_goc=100000,
                         gia_khuyen_mai=75000, giam_gia=True)
    assert kq["status"] is True
    assert kq["data"]["discount_percent"] == 25.0
    # BUS khong co tham so nao de client ap dat san percent — verify signature.
    import inspect
    assert "discount_percent" not in inspect.signature(
        bus.doi_gia_ban).parameters
