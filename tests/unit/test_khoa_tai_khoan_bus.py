# -*- coding: utf-8 -*-
"""Unit tests cho UserBus.cap_nhat_trang_thai theo policy hiện tại.

Quản lý là actor duy nhất được dùng chức năng khóa/mở khóa; mục tiêu chỉ có
Seller hoặc Customer/Khách hàng và không được thao tác chính tài khoản mình.
"""
from back_end.BUS.UserBus import UserBus


def _bus(mock):
    bus = UserBus()
    bus.dao = mock
    return bus


def _thong_tin(role_id, trang_thai="active", fullname="Người dùng"):
    return {
        "UserId": 5,
        "FullName": fullname,
        "Role_Id": role_id,
        "trang_thai": trang_thai,
    }


def test_khoa_admin_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(1)))
    kq = bus.cap_nhat_trang_thai(2, 5, "banned", "Quản lý")
    assert kq["status"] is False
    assert "Seller hoặc Khách hàng" in kq["message"]


def test_khoa_quan_ly_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(2)))
    kq = bus.cap_nhat_trang_thai(8, 5, "banned", "Quản lý")
    assert kq["status"] is False
    assert "Seller hoặc Khách hàng" in kq["message"]


def test_quan_ly_actor_khong_khoa_duoc_quan_ly(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(2)))
    kq = bus.cap_nhat_trang_thai(8, 5, "banned", "Quản lý")
    assert kq["status"] is False
    assert "Seller hoặc Khách hàng" in kq["message"]


def test_quan_ly_actor_khong_mo_khoa_duoc_quan_ly(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(2, "banned")))
    kq = bus.cap_nhat_trang_thai(8, 5, "active", "Quản lý")
    assert kq["status"] is False
    assert "Seller hoặc Khách hàng" in kq["message"]


def test_tu_khoa_ban_than_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(2)))
    kq = bus.cap_nhat_trang_thai(5, 5, "banned", "Quản lý")
    assert kq["status"] is False
    assert "chính tài khoản" in kq["message"]


def test_tu_mo_khoa_ban_than_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(2)))
    kq = bus.cap_nhat_trang_thai(5, 5, "active", "Quản lý")
    assert kq["status"] is False
    assert "chính tài khoản" in kq["message"]


def test_khoa_customer_ok(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(4)))
    kq = bus.cap_nhat_trang_thai(2, 5, "banned", "Quản lý")
    assert kq["status"] is True
    assert kq["message"] == "Đã khóa tài khoản!"


def test_khoa_seller_ok(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(3)))
    kq = bus.cap_nhat_trang_thai(2, 5, "banned", "Quản lý")
    assert kq["status"] is True
    assert kq["message"] == "Đã khóa tài khoản!"


def test_mo_khoa_ok(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(4, "banned")))
    kq = bus.cap_nhat_trang_thai(2, 5, "active", "Quản lý")
    assert kq["status"] is True
    assert kq["message"] == "Đã mở khóa tài khoản!"


def test_trang_thai_khong_hop_le(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(4)))
    kq = bus.cap_nhat_trang_thai(2, 5, "xoa", "Quản lý")
    assert kq["status"] is False
    assert kq["message"] == "Trạng thái không hợp lệ!"


def test_thieu_ma_user(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(2)))
    kq = bus.cap_nhat_trang_thai(2, None, "banned", "Quản lý")
    assert kq["status"] is False
    assert kq["message"] == "Thiếu mã user!"


def test_user_khong_ton_tai(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(2)))
    bus.dao.lay_thong_tin_user = lambda ma_user: None
    kq = bus.cap_nhat_trang_thai(2, 999, "banned", "Quản lý")
    assert kq["status"] is False
    assert kq["message"] == "Tài khoản không tồn tại!"
