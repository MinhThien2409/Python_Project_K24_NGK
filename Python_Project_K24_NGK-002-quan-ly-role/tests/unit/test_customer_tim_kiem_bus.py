"""Unit test tim kiem san pham BUS — 005 US1 T008.

Mock DAO — KHÔNG chạm PobbyDB thật. Viết TRƯỚC implementation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.SanPhamBus import SanPhamBus
from tests.conftest import MockSanPhamTimKiemDao


def _bus():
    bus = SanPhamBus.__new__(SanPhamBus)
    bus.dao = MockSanPhamTimKiemDao(
        danh_sach=[
            {"id": 1, "name": "Hoa Hồng Đỏ", "category_id": 1, "is_active": True},
            {"id": 2, "name": "HOA CÚC VÀNG", "category_id": 1, "is_active": True},
            {"id": 3, "name": "Chậu Lan Tím", "category_id": 2, "is_active": True},
            {"id": 4, "name": "Hoa Hồng Ẩn", "category_id": 1, "is_active": False},
        ])
    return bus


def test_tim_kiem_khong_phan_biet_hoa_thuong():
    bus = _bus()
    kq = bus.tim_kiem_san_pham("hoa hồng", None)
    assert kq["status"] is True
    ids = {sp["id"] for sp in kq["data"]}
    assert 1 in ids and 4 not in ids


def test_tim_kiem_hoa_van_khop_thuong():
    bus = _bus()
    kq = bus.tim_kiem_san_pham("HOA CÚC", None)
    assert kq["status"] is True
    assert any(sp["id"] == 2 for sp in kq["data"])


def test_loc_theo_category():
    bus = _bus()
    kq = bus.tim_kiem_san_pham("", 2)
    assert kq["status"] is True
    assert {sp["id"] for sp in kq["data"]} == {3}


def test_loai_sp_an_khi_tim():
    bus = _bus()
    kq = bus.tim_kiem_san_pham("hồng", None)
    assert all(sp.get("is_active", True) for sp in kq["data"])
    assert all(sp["id"] != 4 for sp in kq["data"])


def test_tu_khoa_rong_tra_danh_sach_kinh_doanh():
    bus = _bus()
    kq = bus.tim_kiem_san_pham("   ", None)
    assert kq["status"] is True
    assert {sp["id"] for sp in kq["data"]} == {1, 2, 3}
