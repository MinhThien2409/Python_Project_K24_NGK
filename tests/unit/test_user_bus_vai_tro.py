# -*- coding: utf-8 -*-
"""Unit test User Story 4: đăng nhập theo vai trò chuẩn (1=Admin, 2=Quản lý,
3=Seller, 4=Customer) dựa trên mock DAO — KHÔNG chạm PobbyDB thật.

- T024: UserBus.dang_nhap trả ten_vai_tro + ten_vai_tro_hien_thi cho 4 vai trò.
- T025: cap_nhat_trang_thai từ chối khóa Admin; dang_ky_khach_hang gán
        Customer (Role_Id=4); Role_Id NULL/lạ bị từ chối rõ ràng (không crash).
"""

import pytest

from back_end.BUS.UserBus import UserBus


@pytest.fixture
def user_bus(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao()
    return bus


# ── T024: ten_vai_tro đầy đủ + hiển thị 4 vai trò chuẩn ──────────────────────
@pytest.mark.parametrize("ma_nhom_quyen,ten_vai_tro,ten_vai_tro_hien_thi", [
    (1, "Admin", "Admin"),
    (2, "Quản lý", "Quản lý"),
    (3, "Seller", "Seller"),
    (4, "Customer", "Customer"),
], ids=["admin", "quan-ly", "seller", "customer"])
def test_dang_nhap_tra_ten_vai_tro(user_bus, user_mau, ma_nhom_quyen, ten_vai_tro, ten_vai_tro_hien_thi, mock_user_dao):
    user_mau.ma_nhom_quyen = ma_nhom_quyen
    bus = UserBus()
    bus.dao = mock_user_dao(user=user_mau)

    ket_qua = bus.dang_nhap("user1", "123456")

    assert ket_qua["status"] is True
    assert ket_qua["data"]["ten_vai_tro"] == ten_vai_tro
    assert ket_qua["data"]["ten_vai_tro_hien_thi"] == ten_vai_tro_hien_thi
    assert ket_qua["data"]["ma_nhom_quyen"] == ma_nhom_quyen


def test_dang_nhap_van_tra_du_ten_user(user_bus, user_mau, mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(user=user_mau)

    ket_qua = bus.dang_nhap("user1", "123456")

    assert ket_qua["data"]["ten_user"] == "Nguyễn Văn An"
    assert ket_qua["data"]["ma_user"] == 1


# ── T025: chặn khóa Admin / đăng ký Customer / Role NULL-lạ từ chối ─────────
def test_cap_nhat_trang_thai_tu_choi_khoa_admin(mock_user_dao):
    """Khóa Admin bị từ chối rõ ràng, không crash (FR-008)."""
    bus = UserBus()
    dao = mock_user_dao()

    # DAO giả lập: user #1 có Role_Id = 1 (Admin) và đang active
    dao.lay_thong_tin_user = lambda ma_user: {"UserId": 1, "Role_Id": 1, "trang_thai": "active"}
    bus.dao = dao

    ket_qua = bus.cap_nhat_trang_thai(2, 1, "banned")

    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không ai có quyền khóa tài khoản Admin!"


def test_cap_nhat_trang_thai_cho_phep_khoa_non_admin(mock_user_dao):
    bus = UserBus()
    dao = mock_user_dao()
    dao.lay_thong_tin_user = lambda ma_user: {"UserId": 5, "Role_Id": 4, "trang_thai": "active"}
    dao.cap_nhat_trang_thai = lambda ma_user, trang_thai: True
    bus.dao = dao

    ket_qua = bus.cap_nhat_trang_thai(2, 5, "banned")

    assert ket_qua["status"] is True


def test_dang_ky_khach_hang_gán_customer(mock_user_dao):
    """Đăng ký mới phải gán Customer (Role_Id=4), không còn hardcode 14."""

    def them_user(user):
        assert user.ma_nhom_quyen == 4, f"Khách hàng phải có Role_Id=4, thực tế {user.ma_nhom_quyen}"
        return True

    bus = UserBus()
    dao = mock_user_dao()
    dao.them_user = them_user
    bus.dao = dao

    ket_qua = bus.dang_ky_khach_hang("Nguyễn Văn A", "Hà Nội", "0987654321", "user_a", "matkhau123")

    assert ket_qua["status"] is True


def test_dang_nhap_role_none_bi_tu_choi_ro_rang(mock_user_dao):
    """Role_Id NULL/lạ (DAO trả {"role_none": True}) → từ chối, không crash."""
    bus = UserBus()
    bus.dao = mock_user_dao(role_none=True)

    ket_qua = bus.dang_nhap("user1", "123456")

    assert ket_qua["status"] is False
    assert "vai trò" in ket_qua["message"].lower()
    assert ket_qua["data"] is None


def test_dang_nhap_banned_van_bi_tu_choi(mock_user_dao):
    """Hành vi banned giữ nguyên (không phải US4 phá vỡ thuộc tính cũ)."""
    bus = UserBus()
    bus.dao = mock_user_dao(banned=True)

    ket_qua = bus.dang_nhap("user1", "123456")

    assert ket_qua["status"] is False
    assert "khóa" in ket_qua["message"].lower()
    assert ket_qua["data"] is None