"""Unit test Phase 4 — My Products BUS (duplicate, autocomplete, tao-va-nhap).

Mock DAO — KHONG cham PobbyDB that.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.SanPhamBus import SanPhamBus
from tests.conftest import MockSanPhamDao


def _bus(**kwargs):
    bus = SanPhamBus()
    bus.dao = MockSanPhamDao(store_cua_sp={1: 10, 2: 20}, **kwargs)
    return bus


# ── Chong duplicate khi THEM (khong phan biet hoa/thuong, trong store) ──
def test_them_trung_ten_chinh_xac_bi_tu_choi():
    bus = _bus(trung_ten={"ao thun"})
    kq = bus.them_san_pham_cua_seller(3, 10, "Ao Thun", "mo ta", 100000,
                                      None, 5, 1)
    assert kq["status"] is False
    assert "tồn tại" in kq["message"]


def test_them_trung_ten_khac_hoa_thuong_bi_tu_choi():
    bus = _bus(trung_ten={"ao thun"})
    kq = bus.them_san_pham_cua_seller(3, 10, "  AO THUN  ", "mo ta",
                                      100000, None, 5, 1)
    assert kq["status"] is False


def test_them_ten_moi_ok():
    bus = _bus(trung_ten={"ao thun"})
    kq = bus.them_san_pham_cua_seller(3, 10, "Quan Jean", "mo ta",
                                      100000, None, 5, 1)
    assert kq["status"] is True


# ── Autocomplete tim kiem cua seller ──
def test_tim_kiem_thieu_store():
    bus = _bus()
    kq = bus.tim_kiem_cua_seller(None, "ao")
    assert kq["status"] is False


def test_tim_kiem_tu_khoa_trong_tra_rong():
    bus = _bus(tim_kiem_kq=[{"id": 1}])
    kq = bus.tim_kiem_cua_seller(10, "   ")
    assert kq["status"] is True
    assert kq["data"] == []


def test_tim_kiem_tra_ket_qua_dao():
    goi_y = [{"id": 1, "name": "Ao Thun"}]
    bus = _bus(tim_kiem_kq=goi_y)
    kq = bus.tim_kiem_cua_seller(10, "ao")
    assert kq["status"] is True
    assert kq["data"] == goi_y


# ── Tao SP moi tu phieu nhap ──
def test_tao_va_nhap_trung_ten_bi_tu_choi():
    bus = _bus(trung_ten={"ao moi"})
    kq = bus.tao_va_nhap(3, 10, "AO MOI", 5, gia_ban=50000)
    assert kq["status"] is False
    assert bus.dao.goi_tao_va_nhap == []


def test_tao_va_nhap_ten_trong_bi_tu_choi():
    bus = _bus()
    assert bus.tao_va_nhap(3, 10, "   ", 5)["status"] is False


def test_tao_va_nhap_thieu_field_dung_default():
    bus = _bus()
    kq = bus.tao_va_nhap(3, 10, "SP Moi Toanh", 5)
    assert kq["status"] is True
    assert kq["data"]["quantity"] == 5


def test_tao_va_nhap_so_luong_sai_bi_tu_choi():
    bus = _bus()
    for xau in (0, -1, "abc", None, "1.5", True):
        assert bus.tao_va_nhap(3, 10, "SP X", xau)["status"] is False, xau
    assert bus.dao.goi_tao_va_nhap == []
