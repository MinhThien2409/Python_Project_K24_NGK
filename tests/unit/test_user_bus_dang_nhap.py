# -*- coding: utf-8 -*-
"""Unit test đăng nhập UserBus.dang_nhap (feature 001, R1):
- đúng → thành công
- sai mật khẩu → thất bại
- banned → từ chối
- role_none → từ chối
- thiếu đầu vào → từ chối

Dùng MockUserDao, KHÔNG chạm PobbyDB thật.
"""

import pytest
from back_end.Model.User import User

from back_end.BUS.UserBus import UserBus


@pytest.fixture
def user_bus(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao()
    return bus


def _user(ma_user, ma_nhom_quyen, ten_user, dia_chi, sdt, cmnd, tendangnhap, mat_khau):
    return User(
        ma_user=ma_user,
        ma_nhom_quyen=ma_nhom_quyen,
        ten_user=ten_user,
        sdt=sdt,
        dia_chi=dia_chi,
        cmnd=cmnd,
        tendangnhap=tendangnhap,
        mat_khau=mat_khau,
    )


# ── Đăng nhập thành công ─────────────────────────────────────────────────────
def test_dang_nhap_dung_thanh_cong(mock_user_dao):
    user = _user(1, 4, "Nguyễn Văn An", "Hà Nội", "0123456789",
                  "001099012345", "user1", "123456")
    bus = UserBus()
    bus.dao = mock_user_dao(user=user)
    ket_qua = bus.dang_nhap("user1", "123456")

    assert ket_qua["status"] is True
    assert ket_qua["message"] == "Chào mừng Nguyễn Văn An trở lại!"
    assert ket_qua["data"]["ma_user"] == 1
    assert ket_qua["data"]["ten_user"] == "Nguyễn Văn An"
    assert ket_qua["data"]["ten_vai_tro"] == "Customer"
    assert ket_qua["data"]["sdt"] == "0123456789"
    assert ket_qua["data"]["dia_chi"] == "Hà Nội"
    assert ket_qua["data"]["cmnd"] == "001099012345"


def test_dang_nhap_dung_vai_tro_admin(mock_user_dao):
    user = _user(2, 1, "Admin", "TP.HCM", "0123456789",
                  "001099012345", "admin1", "123456")
    bus = UserBus()
    bus.dao = mock_user_dao(user=user)
    ket_qua = bus.dang_nhap("admin1", "123456")

    assert ket_qua["status"] is True
    assert ket_qua["data"]["ten_vai_tro"] == "Admin"
    assert ket_qua["data"]["ma_nhom_quyen"] == 1


# ── Sai mật khẩu ─────────────────────────────────────────────────────────────
def test_dang_nhap_sai_mat_khau_that_bai(mock_user_dao):
    user = _user(1, 4, "Nguyễn Văn An", "Hà Nội", "0123456789",
                  "001099012345", "user1", "123456")
    bus = UserBus()
    bus.dao = mock_user_dao(user=user)
    ket_qua = bus.dang_nhap("user1", "999999")

    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tên đăng nhập hoặc mật khẩu không chính xác!"
    assert ket_qua["data"] is None


# ── Tài khoản bị khóa ────────────────────────────────────────────────────────
def test_dang_nhap_bi_khoa_tu_choi(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(banned=True)
    ket_qua = bus.dang_nhap("user1", "123456")

    assert ket_qua["status"] is False
    assert "khóa" in ket_qua["message"].lower()
    assert ket_qua["data"] is None


# ── Vai trò không hợp lệ ─────────────────────────────────────────────────────
def test_dang_nhap_role_none_tu_choi(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(role_none=True)
    ket_qua = bus.dang_nhap("user1", "123456")

    assert ket_qua["status"] is False
    assert "vai trò" in ket_qua["message"].lower()
    assert ket_qua["data"] is None


# ── Thiếu đầu vào ────────────────────────────────────────────────────────────
def test_dang_nhap_thieu_tendangnhap(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(user=_user(1, 4, "An", "HN", "0123456789",
                                        "001", "user1", "123456"))
    ket_qua = bus.dang_nhap("", "123456")

    assert ket_qua["status"] is False
    assert "Vui lòng nhập tài khoản" in ket_qua["message"]
    assert ket_qua["data"] is None


def test_dang_nhap_thieu_mat_khau(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(user=_user(1, 4, "An", "HN", "0123456789",
                                        "001", "user1", "123456"))
    ket_qua = bus.dang_nhap("user1", "")

    assert ket_qua["status"] is False
    assert "Vui lòng nhập tài khoản" in ket_qua["message"]
    assert ket_qua["data"] is None


def test_dang_nhap_thieu_bo_dau_vao(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(user=_user(1, 4, "An", "HN", "0123456789",
                                        "001", "user1", "123456"))
    ket_qua = bus.dang_nhap(None, None)

    assert ket_qua["status"] is False
    assert "Vui lòng nhập tài khoản" in ket_qua["message"]
    assert ket_qua["data"] is None
