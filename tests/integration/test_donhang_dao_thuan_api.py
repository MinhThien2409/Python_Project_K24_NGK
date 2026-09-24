"""Integration test endpoint DonHang sau refactor DAO-thuần — 007 T027.

Envelope {status, message, data} đi qua BUS bọc DAO thuần
(dict/list, lỗi trả {}/[]). KHÔNG chạm PobbyDB thật: stub DAO.

Trước T038: FAIL (DAO trả {"status":...}, BUS thấu qua).
Sau T038: PASS.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from back_end.BUS.DonHangBus import DonHangBus


class StubDaoThuan:
    """DAO thuần mẫu: thống kê trả dict, doanh thu trả list."""

    def lay_thong_ke_tong_quan(self):
        return {"doanh_thu": 1000.0, "tong_don": 2}

    def lay_doanh_thu_theo_thang(self, year):
        return [{"thang": 1, "doanh_thu": 500.0, "so_don": 1}]

    def lay_don_hang_cua_user(self, ma_user):
        return [{"OrderId": 1}]

    def lay_trang_thai(self, order_id):
        return "Pending"

    def don_thuoc_store(self, order_id, store_id):
        return True

    def cap_nhat_trang_thai(self, order_id, new_status):
        return True


class StubDaoLoi:
    """DAO thuần khi lỗi: trả {}/[] (KHÔNG trả status-dict)."""

    def lay_thong_ke_tong_quan(self):
        return {}

    def lay_doanh_thu_theo_thang(self, year):
        return []

    def lay_don_hang_cua_user(self, ma_user):
        return []


def _bus(dao):
    bus = DonHangBus()
    bus.dao = dao
    return bus


def test_thong_ke_tong_quan_envelope_chuan():
    r = _bus(StubDaoThuan()).lay_thong_ke_tong_quan()
    assert r["status"] is True
    assert r["data"]["tong_don"] == 2


def test_doanh_thu_theo_thang_envelope_chuan():
    r = _bus(StubDaoThuan()).lay_doanh_thu_theo_thang(2026)
    assert r["status"] is True
    assert isinstance(r["data"], list) and r["data"][0]["thang"] == 1


def test_dao_loi_bus_van_envelope_viet():
    r = _bus(StubDaoLoi()).lay_thong_ke_tong_quan()
    assert "status" in r and "data" in r
    assert r["data"] == {}
    r2 = _bus(StubDaoLoi()).lay_doanh_thu_theo_thang(2026)
    assert r2["data"] == []


def test_don_cua_toi_envelope_data_list():
    r = _bus(StubDaoThuan()).lay_don_hang_cua_toi(1)
    assert r["status"] is True and isinstance(r["data"], list)


def test_thay_doi_trang_thai_envelope_viet():
    r = _bus(StubDaoThuan()).thay_doi_trang_thai(1, "Confirmed")
    assert r["status"] is True
    assert "message" in r and "Traceback" not in r["message"]
