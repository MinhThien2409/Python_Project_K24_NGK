"""Unit test gio hang BUS — 005 US2 T015.

Mock DAO — KHÔNG chạm PobbyDB thật. Viết TRƯỚC implementation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.GioHangBus import GioHangBus
from tests.conftest import MockGioHangDao, MockSanPhamTimKiemDao


def _bus(kho=None, stores=None, gio_hang=None):
    bus = GioHangBus.__new__(GioHangBus)
    bus.dao = MockGioHangDao(
        kho=kho or {}, stores=stores or {1: 10}, gio_hang=gio_hang or {})
    bus.san_pham_dao = MockSanPhamTimKiemDao(
        kho=kho or {1: {"quantity": 5, "is_active": True, "price": 100000}})
    return bus


def test_vuot_ton_kho_bi_tu_choi():
    bus = _bus(kho={1: {"quantity": 2, "is_active": True, "price": 100000}},
               stores={1: 10})
    kq = bus.xu_ly_them_vao_gio(5, 1, 5, 100000)
    assert kq["status"] is False
    assert "vượt tồn kho" in kq["message"]


def test_sp_an_bi_tu_choi():
    bus = _bus(kho={1: {"quantity": 5, "is_active": False, "price": 100000}},
               stores={1: 10})
    kq = bus.xu_ly_them_vao_gio(5, 1, 1, 100000)
    assert kq["status"] is False
    assert "không còn kinh doanh" in kq["message"]


def test_gia_client_bi_bo_qua():
    bus = _bus(kho={1: {"quantity": 5, "is_active": True, "price": 100000}},
               stores={1: 10})
    kq = bus.xu_ly_them_vao_gio(5, 1, 1, 1)
    assert kq["status"] is True
    # Đơn giá DB phải được dùng, không phải giá client 1đ
    assert bus.dao.gio_hang.get(1, 0) == 1


def test_sl_am_rong_bi_tu_choi():
    bus = _bus()
    for sl in (None, "", 0, -3):
        kq = bus.xu_ly_them_vao_gio(5, 1, sl, 100000)
        assert kq["status"] is False, f"SL={sl!r} phải bị từ chối"
        assert "không hợp lệ" in kq["message"]


def test_cap_nhat_vuot_kho_bi_tu_choi():
    bus = _bus(kho={1: {"quantity": 2, "is_active": True, "price": 100000}},
               stores={1: 10}, gio_hang={1: 1})
    kq = bus.cap_nhat_so_luong(5, 1, 9)
    assert kq["status"] is False
    assert "vượt tồn kho" in kq["message"]


def test_cap_nhat_sl_0_thi_xoa():
    bus = _bus(kho={1: {"quantity": 5, "is_active": True, "price": 100000}},
               stores={1: 10}, gio_hang={1: 2})
    kq = bus.cap_nhat_so_luong(5, 1, 0)
    assert kq["status"] is True
    assert 1 not in bus.dao.gio_hang
