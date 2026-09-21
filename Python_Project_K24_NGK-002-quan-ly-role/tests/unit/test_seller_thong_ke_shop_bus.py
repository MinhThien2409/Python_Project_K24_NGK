"""Unit test BUS thong ke shop seller — US4 (T040) + US5 BUS (T048).

Chi shop minh, du 12 thang; trung/rong ten, tham nien bien, XSS.
Mock DAO — KHONG cham PobbyDB that.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.DonHangBus import DonHangBus
from back_end.BUS.GianHangBus import GianHangBus
from tests.conftest import MockDonHangSellerDao, MockShopDao


# ── US4 (T040) ──
def test_thong_ke_chi_shop_minh():
    bus = DonHangBus()
    bus.dao = MockDonHangSellerDao(
        thong_ke={"doanh_thu": 500000, "tong_don": 3, "store_id": 10})
    kq = bus.lay_thong_ke_cua_seller(10)
    assert kq["status"] is True
    assert kq["data"]["store_id"] == 10


def test_thong_ke_shop_moi_so_0():
    bus = DonHangBus()
    bus.dao = MockDonHangSellerDao(thong_ke=None)
    kq = bus.lay_thong_ke_cua_seller(99)
    assert kq["status"] is True
    assert kq["data"]["doanh_thu"] == 0


def test_doanh_thu_du_12_thang():
    bus = DonHangBus()
    bus.dao = MockDonHangSellerDao(doanh_thu_thang=None)
    kq = bus.lay_doanh_thu_seller_theo_thang(10, 2026)
    assert kq["status"] is True
    assert len(kq["data"]) == 12
    assert kq["data"][0]["thang"] == 1
    assert kq["data"][11]["thang"] == 12


# ── US5 BUS (T048) ──
def _shop_bus(trung_ten=False, ket_qua_ghi=True):
    bus = GianHangBus()
    bus.dao = MockShopDao(trung_ten=trung_ten, ket_qua_ghi=ket_qua_ghi)
    return bus


def test_cap_nhat_shop_ok():
    bus = _shop_bus()
    kq = bus.cap_nhat_trang_shop(3, 10, "Shop Moi", "Gioi thieu", 5)
    assert kq["status"] is True


def test_ten_rong():
    bus = _shop_bus()
    kq = bus.cap_nhat_trang_shop(3, 10, "   ", "GT", 5)
    assert kq["status"] is False
    assert "Tên shop" in kq["message"]


def test_ten_trung():
    bus = _shop_bus(trung_ten=True)
    kq = bus.cap_nhat_trang_shop(3, 10, "Shop B", "GT", 5)
    assert kq["status"] is False
    assert "đã có người sử dụng" in kq["message"]


def test_tham_nien_bien_0_100_ok():
    bus = _shop_bus()
    for tn in (0, 100):
        kq = bus.cap_nhat_trang_shop(3, 10, "Shop A", "GT", tn)
        assert kq["status"] is True


def test_tham_nien_ngoai_bien():
    bus = _shop_bus()
    for tn in (-1, 101, "abc"):
        kq = bus.cap_nhat_trang_shop(3, 10, "Shop A", "GT", tn)
        assert kq["status"] is False
        assert "Thâm niên" in kq["message"]


def test_xss_duoc_lam_sach():
    bus = _shop_bus()
    kq = bus.cap_nhat_trang_shop(3, 10, "Shop A", "<script>alert(1)</script>Xin chao", 5)
    assert kq["status"] is True
    assert "<script" not in kq["data"]["gioi_thieu"]
