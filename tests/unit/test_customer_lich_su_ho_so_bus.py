"""Unit test lich su + ho so BUS — 005 US4 T030 (US5 mo rong o T035).

Mock DAO — KHÔNG chạm PobbyDB thật. Viết TRƯỚC implementation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.DonHangBus import DonHangBus
from tests.conftest import MockDonHangCustomerDao


def _bus(don_hang=None):
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = MockDonHangCustomerDao(don_hang=don_hang or {})
    return bus


def test_lich_su_chi_dung_chu():
    bus = _bus(don_hang={
        1: {"OrderId": 1, "UserId": 5, "Status": "Pending", "CreatedAt": "2026-09-18 09:00:01"},
        2: {"OrderId": 2, "UserId": 6, "Status": "Pending", "CreatedAt": "2026-09-18 09:00:02"},
    })
    kq = bus.lay_don_hang_cua_toi(5)
    assert kq["status"] is True
    assert {d["OrderId"] for d in kq["data"]} == {1}


def test_lich_su_sap_xep_moi_nhat_truoc():
    bus = _bus(don_hang={
        1: {"OrderId": 1, "UserId": 5, "Status": "Pending", "CreatedAt": "2026-09-18 09:00:01"},
        2: {"OrderId": 2, "UserId": 5, "Status": "Shipping", "CreatedAt": "2026-09-18 10:00:01"},
    })
    kq = bus.lay_don_hang_cua_toi(5)
    assert [d["OrderId"] for d in kq["data"]] == [2, 1]


def test_hoa_don_dung_chu_ownership():
    bus = _bus(don_hang={9: {"OrderId": 9, "UserId": 5, "Status": "Completed"}})
    bus.dao.chi_tiet = {9: [{"ProductId": 1}]}
    kq = bus.lay_hoa_don_cua_toi(5, 9)
    assert kq["status"] is True


def test_hoa_don_cheo_403():
    bus = _bus(don_hang={9: {"OrderId": 9, "UserId": 6, "Status": "Completed"}})
    bus.dao.chi_tiet = {9: []}
    kq = bus.lay_hoa_don_cua_toi(5, 9)
    assert kq["status"] is False
    assert "không có quyền" in kq["message"]


def test_chua_mua_tra_mang_rong():
    bus = _bus(don_hang={})
    kq = bus.lay_don_hang_cua_toi(99)
    assert kq["status"] is True
    assert kq["data"] == []


# ── 005 US5 T035: SĐT sai + sai MK cũ + trùng MK + IDOR ──
class _DaoUserGia:
    def __init__(self):
        self.thong_tin = {5: {"UserId": 5, "FullName": "A", "Password": "cu1234",
                              "Role_Id": 4, "trang_thai": "active"}}
        self.da_cap_nhat = []

    def lay_thong_tin_user(self, ma_user):
        return self.thong_tin.get(ma_user)

    def cap_nhat_user(self, *a):
        self.da_cap_nhat.append(a)
        return True

    def cap_nhat_mat_khau(self, ma_user, moi):
        self.thong_tin[ma_user]["Password"] = moi
        return True


def _bus_user():
    from back_end.BUS.UserBus import UserBus
    bus = UserBus.__new__(UserBus)
    bus.dao = _DaoUserGia()
    return bus


def test_cap_nhat_sdt_sai_bi_tu_choi():
    bus = _bus_user()
    kq = bus.cap_nhat_user(5, "A", "HN", "123", "001")
    assert kq["status"] is False
    assert "Số điện thoại không hợp lệ" in kq["message"]


def test_doi_mk_sai_cu_bi_tu_choi():
    bus = _bus_user()
    kq = bus.doi_mat_khau_cua_toi(5, 5, "sai", "moi1234")
    assert kq["status"] is False
    assert "không chính xác" in kq["message"]


def test_doi_mk_trung_cu_bi_tu_choi():
    bus = _bus_user()
    kq = bus.doi_mat_khau_cua_toi(5, 5, "cu1234", "cu1234")
    assert kq["status"] is False
    assert "phải khác mật khẩu cũ" in kq["message"]


def test_idor_chong_tai_khoan():
    bus = _bus_user()
    kq = bus.cap_nhat_thong_tin_cua_toi(5, 6, "B", "HN", "0901234567", "001")
    assert kq["status"] is False
    assert "tài khoản khác" in kq["message"]
    kq2 = bus.doi_mat_khau_cua_toi(5, 6, "cu1234", "moi1234")
    assert kq2["status"] is False
    assert "tài khoản khác" in kq2["message"]
