# -*- coding: utf-8 -*-
"""Unit test 2 gate phân quyền server-side (feature 002, R1):
UserBus.kiem_tra_quyen_quan_ly (chỉ Admin/Quản lý) và
UserBus.kiem_tra_nguoi_dung_hoat_dong (đã đăng nhập + active — FR-009).

Dùng mock DAO, KHÔNG chạm PobbyDB thật.
"""

import pytest

from back_end.BUS.UserBus import UserBus


@pytest.fixture
def user_bus(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao()
    return bus


# ── kiem_tra_quyen_quan_ly ────────────────────────────────────────────────────
def test_khoa_quyen_quan_ly_chua_dang_nhap(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao()
    ket_qua = bus.kiem_tra_quyen_quan_ly(None)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Bạn chưa đăng nhập!"


def test_khoa_quyen_quan_ly_khong_ton_tai(mock_user_dao):
    bus = UserBus()
    dao = mock_user_dao()
    dao.lay_thong_tin_user = lambda ma_user: None
    bus.dao = dao
    ket_qua = bus.kiem_tra_quyen_quan_ly(999)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tài khoản không tồn tại!"


def test_khoa_quyen_quan_ly_bi_khoa(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(
        thong_tin={"UserId": 8, "Role_Id": 4, "trang_thai": "banned"}
    )
    ket_qua = bus.kiem_tra_quyen_quan_ly(8)
    assert ket_qua["status"] is False
    assert "khóa" in ket_qua["message"].lower()


@pytest.mark.parametrize("role_id", [3, 4], ids=["seller", "customer"])
def test_khoa_quyen_quan_ly_tu_choi_vai_tro_thuong(mock_user_dao, role_id):
    bus = UserBus()
    bus.dao = mock_user_dao(
        thong_tin={"UserId": 8, "Role_Id": role_id, "trang_thai": "active"}
    )
    ket_qua = bus.kiem_tra_quyen_quan_ly(8)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Bạn không có quyền thực hiện chức năng này!"


def test_khoa_quyen_quan_ly_role_lạ(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(
        thong_tin={"UserId": 8, "Role_Id": 99, "trang_thai": "active"}
    )
    ket_qua = bus.kiem_tra_quyen_quan_ly(8)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Dữ liệu vai trò không hợp lệ!"


@pytest.mark.parametrize("role_id", [1, 2], ids=["admin", "quan-ly"])
def test_khoa_quyen_quan_ly_cho_phep(mock_user_dao, role_id):
    bus = UserBus()
    bus.dao = mock_user_dao(
        thong_tin={"UserId": 8, "Role_Id": role_id, "trang_thai": "active"}
    )
    ket_qua = bus.kiem_tra_quyen_quan_ly(8)
    assert ket_qua["status"] is True
    assert ket_qua["data"]["ma_user"] == 8


# ── kiem_tra_nguoi_dung_hoat_dong ────────────────────────────────────────────
def test_nguoi_dung_hoat_dong_chua_dang_nhap(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao()
    ket_qua = bus.kiem_tra_nguoi_dung_hoat_dong(None)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Bạn chưa đăng nhập!"


def test_nguoi_dung_hoat_dong_bi_khoa_chan(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(
        thong_tin={"UserId": 8, "Role_Id": 4, "trang_thai": "banned"}
    )
    ket_qua = bus.kiem_tra_nguoi_dung_hoat_dong(8)
    assert ket_qua["status"] is False
    assert "khóa" in ket_qua["message"].lower()


@pytest.mark.parametrize("role_id", [1, 2, 3, 4], ids=["admin", "quan-ly", "seller", "customer"])
def test_nguoi_dung_hoat_dong_cho_phep_moi_vai_tro(mock_user_dao, role_id):
    bus = UserBus()
    bus.dao = mock_user_dao(
        thong_tin={"UserId": 8, "Role_Id": role_id, "trang_thai": "active"}
    )
    ket_qua = bus.kiem_tra_nguoi_dung_hoat_dong(8)
    assert ket_qua["status"] is True