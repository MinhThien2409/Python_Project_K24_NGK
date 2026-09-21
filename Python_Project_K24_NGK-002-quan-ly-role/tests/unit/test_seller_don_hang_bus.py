"""Unit test BUS don hang seller — US2 (T024).

Terminal, nhay coc, don shop khac, trang thai la.
Mock DAO — KHONG cham PobbyDB that.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.DonHangBus import DonHangBus
from tests.conftest import MockDonHangSellerDao


def _bus(trang_thai=None, thuoc_store=True):
    bus = DonHangBus()
    bus.dao = MockDonHangSellerDao(trang_thai=trang_thai, thuoc_store=thuoc_store)
    return bus


def test_chuyen_tung_buoc_ok():
    bus = _bus(trang_thai={1: "Pending"}, thuoc_store=True)
    kq = bus.cap_nhat_trang_thai_cua_seller(3, 10, 1, "Confirmed")
    assert kq["status"] is True


def test_nhay_coc_pending_completed():
    bus = _bus(trang_thai={1: "Pending"}, thuoc_store=True)
    kq = bus.cap_nhat_trang_thai_cua_seller(3, 10, 1, "Completed")
    assert kq["status"] is False
    assert "luồng" in kq["message"]


def test_nhay_coc_pending_shipping():
    bus = _bus(trang_thai={1: "Pending"}, thuoc_store=True)
    kq = bus.cap_nhat_trang_thai_cua_seller(3, 10, 1, "Shipping")
    assert kq["status"] is False


def test_terminal_completed():
    bus = _bus(trang_thai={1: "Completed"}, thuoc_store=True)
    kq = bus.cap_nhat_trang_thai_cua_seller(3, 10, 1, "Cancelled")
    assert kq["status"] is False
    assert "cuối" in kq["message"]


def test_terminal_cancelled():
    bus = _bus(trang_thai={1: "Cancelled"}, thuoc_store=True)
    kq = bus.cap_nhat_trang_thai_cua_seller(3, 10, 1, "Confirmed")
    assert kq["status"] is False


def test_don_shop_khac():
    bus = _bus(trang_thai={1: "Pending"}, thuoc_store=False)
    kq = bus.cap_nhat_trang_thai_cua_seller(3, 10, 1, "Confirmed")
    assert kq["status"] is False
    assert "gian hàng" in kq["message"]


def test_trang_thai_la():
    bus = _bus(trang_thai={1: "Pending"}, thuoc_store=True)
    kq = bus.cap_nhat_trang_thai_cua_seller(3, 10, 1, "DangGiao")
    assert kq["status"] is False
    assert "không hợp lệ" in kq["message"]


def test_don_khong_ton_tai():
    bus = _bus(trang_thai={}, thuoc_store=True)
    kq = bus.cap_nhat_trang_thai_cua_seller(3, 10, 999, "Confirmed")
    assert kq["status"] is False
