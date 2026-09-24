"""Unit test bo rang buoc 1 shop — 011 US1 T003.

Mock DAO — KHÔNG chạm PobbyDB thật. Viết TRƯỚC implementation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.GioHangBus import GioHangBus
from tests.conftest import MockGioHangDao, MockSanPhamTimKiemDao


def _bus(kho=None, stores=None, gio_hang=None):
    """BUS giỏ với mock DAO; hai món thuộc hai shop khác nhau."""
    bus = GioHangBus.__new__(GioHangBus)
    bus.dao = MockGioHangDao(
        kho=kho or {},
        stores=stores or {1: 10, 2: 20},
        gio_hang=gio_hang or {})
    bus.san_pham_dao = MockSanPhamTimKiemDao(kho=kho or {
        1: {"quantity": 5, "is_active": True, "price": 100000},
        2: {"quantity": 4, "is_active": True, "price": 70000},
    })
    return bus


def test_them_mon_shop_khac_thanh_cong():
    """US1: giỏ đang có shop 10, thêm món shop 20 vẫn thành công."""
    bus = _bus()
    kq1 = bus.xu_ly_them_vao_gio(5, 1, 1, 100000)
    assert kq1["status"] is True
    kq2 = bus.xu_ly_them_vao_gio(5, 2, 1, 70000)
    assert kq2["status"] is True, kq2
    assert bus.dao.gio_hang.get(1) == 1
    assert bus.dao.gio_hang.get(2) == 1


def test_khong_con_truong_conflict():
    """US1: response thêm món shop khác KHÔNG còn trường conflict."""
    bus = _bus()
    bus.xu_ly_them_vao_gio(5, 1, 1, 100000)
    kq2 = bus.xu_ly_them_vao_gio(5, 2, 1, 70000)
    assert kq2["status"] is True
    assert "conflict" not in kq2
    assert bus.dao.da_xoa_toan_bo is False  # không bị xóa giỏ khi thêm shop khác


def test_kiem_kho_van_giu_nguyen():
    """US1: quy tắc kho cũ vẫn còn — vượt kho / sp ẩn bị từ chối."""
    bus = _bus()
    kq = bus.xu_ly_them_vao_gio(5, 1, 99, 100000)  # kho còn 5
    assert kq["status"] is False
    assert "vượt tồn kho" in kq["message"]
    bus2 = _bus(kho={2: {"quantity": 4, "is_active": False, "price": 70000}})
    kq2 = bus2.xu_ly_them_vao_gio(5, 2, 1, 70000)
    assert kq2["status"] is False
    assert "không còn kinh doanh" in kq2["message"]


def test_xoa_cap_nhat_khong_anh_huong_mon_khac():
    """US1: xóa/cập nhật một món không đụng tới món thuộc shop khác."""
    bus = _bus()
    bus.xu_ly_them_vao_gio(5, 1, 1, 100000)
    bus.xu_ly_them_vao_gio(5, 2, 2, 70000)
    # Cập nhật món 1
    kq = bus.cap_nhat_so_luong(5, 1, 3)
    assert kq["status"] is True
    assert bus.dao.gio_hang.get(1) == 3, "món 1 phải đổi sang 3"
    assert bus.dao.gio_hang.get(2) == 2, "món 2 không được đổi"
    # Xóa món 1
    kq = bus.xoa_khoi_gio(5, 1)
    assert kq["status"] is True
    assert 1 not in bus.dao.gio_hang
    assert bus.dao.gio_hang.get(2) == 2, "món 2 không được xóa theo"