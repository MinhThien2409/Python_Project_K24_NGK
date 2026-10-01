"""Unit test Phase 1 — Validate số lượng giỏ hàng (cộng dồn + kiểu dữ liệu).

- Số thập phân / chữ / None / rỗng → từ chối.
- Số nguyên > 0 mới hợp lệ.
- Tồn kho kiểm tra theo TỔNG (đang có trong giỏ + thêm mới ≤ tồn).
- Số lượng = 0 khi cập nhật → xóa món (giữ nguyên hành vi cũ).

Mock DAO — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.GioHangBus import GioHangBus
from tests.conftest import MockGioHangDao, MockSanPhamTimKiemDao

def _bus(kho=None, gio_hang=None):
    bus = GioHangBus.__new__(GioHangBus)
    bus.dao = MockGioHangDao(kho=kho or {}, stores={1: 10},
                             gio_hang=gio_hang or {})
    bus.san_pham_dao = MockSanPhamTimKiemDao(kho=kho or {})
    return bus

def test_so_thap_phan_bi_tu_choi():
    bus = _bus(kho={1: {"quantity": 10, "is_active": True, "price": 1000}},
               gio_hang={})
    for sl in (1.5, 2.7, "3.5"):
        kq = bus.xu_ly_them_vao_gio(5, 1, sl, 1000)
        assert kq["status"] is False, f"SL={sl!r} phải bị từ chối"
        assert "không hợp lệ" in kq["message"]

def test_so_nguyen_hop_le_duoc_them():
    bus = _bus(kho={1: {"quantity": 10, "is_active": True, "price": 1000}},
               gio_hang={})
    kq = bus.xu_ly_them_vao_gio(5, 1, "2", 1000)
    assert kq["status"] is True
    assert bus.dao.gio_hang.get(1) == 2

def test_tong_gio_cong_don_vuot_kho_bi_tu_choi():
    """Đang có 2 trong giỏ, thêm 2 nữa khi tồn 3 → từ chối."""
    bus = _bus(kho={1: {"quantity": 3, "is_active": True, "price": 1000}},
               gio_hang={1: 2})
    kq = bus.xu_ly_them_vao_gio(5, 1, 2, 1000)
    assert kq["status"] is False
    assert "vượt tồn kho" in kq["message"]

def test_tong_gio_cong_don_con_duoc():
    """Đang có 1 trong giỏ, thêm 2 nữa khi tồn 3 → cho qua."""
    bus = _bus(kho={1: {"quantity": 3, "is_active": True, "price": 1000}},
               gio_hang={1: 1})
    kq = bus.xu_ly_them_vao_gio(5, 1, 2, 1000)
    assert kq["status"] is True
    assert bus.dao.gio_hang.get(1) == 3

def test_cap_nhat_so_thap_phan_bi_tu_choi():
    bus = _bus(kho={1: {"quantity": 5, "is_active": True, "price": 1000}},
               gio_hang={1: 2})
    kq = bus.cap_nhat_so_luong(5, 1, 1.5)
    assert kq["status"] is False
    assert "không hợp lệ" in kq["message"]

def test_cap_nhat_0_van_xoa_mon():
    bus = _bus(kho={1: {"quantity": 5, "is_active": True, "price": 1000}},
               gio_hang={1: 2})
    kq = bus.cap_nhat_so_luong(5, 1, 0)
    assert kq["status"] is True
    assert 1 not in bus.dao.gio_hang
