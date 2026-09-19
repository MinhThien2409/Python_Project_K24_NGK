# -*- coding: utf-8 -*-
"""Integration test T015 [P] [US1] — GET /api/phien.

- Chưa đăng nhập → từ chối (status False, message "Bạn chưa đăng nhập!", data None).
- Đã đăng nhập → trả đúng `trang_thai` và `ten_vai_tro` theo DB (active/banned).

Dùng Flask test_client + fake DAO — KHÔNG chạm PobbyDB thật.
"""

import pytest

import app as app_module
from app import app

from back_end.BUS.UserBus import UserBus
from back_end.DAO.UserDao import UserDao
from back_end.Model.User import User

VAI_TRO = {1: "Admin", 2: "Quản lý", 3: "Seller", 4: "Customer"}


class FakeUserDaoSession(UserDao):
    """Thay DAO thật cho endpoint phiên — KHÔNG chạm DB."""

    def __init__(self, user_map, thong_tin_map=None):
        self.user_map = user_map
        self.thong_tin_map = thong_tin_map or {}

    def dang_nhap(self, username, password):
        return self.user_map.get(username)

    def lay_thong_tin_user(self, ma_user):
        return self.thong_tin_map.get(ma_user)

    def lay_ten_vai_tro_theo_id(self, role_id):
        return VAI_TRO.get(role_id)


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture
def gan_dao(monkeypatch):
    """Gắn UserBus với DAO giả vào module app cho các lần gọi endpoint."""

    def _gan(user_map, thong_tin_map=None):
        fake = FakeUserDaoSession(user_map=user_map, thong_tin_map=thong_tin_map)
        bus = UserBus()
        bus.dao = fake
        monkeypatch.setattr(app_module, "user_bus", bus)
        return fake

    return _gan


def _user_quan_ly():
    return User(
        ma_user=8,
        ma_nhom_quyen=2,
        ten_user="Nguyễn Thị Quản Lý",
        sdt="0900000000",
        dia_chi="Hà Nội",
        cmnd="001099000001",
        tendangnhap="manager1",
        mat_khau="123456",
    )


def _dang_nhap(client, gan_dao, username="manager1"):
    """Đăng nhập và trả về response."""
    return client.post(
        "/api/dang-nhap",
        json={"tendangnhap": username, "mat_khau": "123456"},
    )


def test_phien_chua_dang_nhap_bui_troi(client):
    """Chưa đăng nhập → từ chối, không đọc DB."""
    resp = client.get("/api/phien")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Bạn chưa đăng nhập!"
    assert body["data"] is None


def test_phien_dang_dang_nhap_tra_dung_trang_thai_va_ten_vai_tro(client, gan_dao):
    """Đã đăng nhập, active → status True, trang_thai/ten_vai_tro đúng."""
    gan_dao(
        {"manager1": _user_quan_ly()},
        {8: {"UserId": 8, "FullName": "Nguyễn Thị Quản Lý", "Role_Id": 2,
             "trang_thai": "active", "Phone": "0900000000", "Address": "Hà Nội"}},
    )
    _dang_nhap(client, gan_dao)

    resp = client.get("/api/phien")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is True
    assert body["message"] == ""
    assert body["data"]["ma_user"] == 8
    assert body["data"]["ten_user"] == "Nguyễn Thị Quản Lý"
    assert body["data"]["ten_vai_tro"] == "Quản lý"
    assert body["data"]["ten_vai_tro_hien_thi"] == "Quản lý"
    assert body["data"]["trang_thai"] == "active"
    assert body["data"]["sdt"] == "0900000000"
    assert body["data"]["dia_chi"] == "Hà Nội"


def test_phien_dang_dang_nhap_tra_dung_ten_vai_tro_admin(client, gan_dao):
    """Đã đăng nhập, vai trò Admin (Role_Id=1) → ten_vai_tro "Admin"."""
    user = User(
        ma_user=1,
        ma_nhom_quyen=1,
        ten_user="Admin Hệ Thống",
        sdt="0911111111",
        dia_chi="TP.HCM",
        cmnd="001099000009",
        tendangnhap="admin1",
        mat_khau="123456",
    )
    gan_dao(
        {"admin1": user},
        {1: {"UserId": 1, "FullName": "Admin Hệ Thống", "Role_Id": 1,
             "trang_thai": "active", "Phone": "0911111111", "Address": "TP.HCM"}},
    )
    _dang_nhap(client, gan_dao, username="admin1")

    resp = client.get("/api/phien")
    body = resp.get_json()
    assert body["status"] is True
    assert body["data"]["ma_user"] == 1
    assert body["data"]["ten_vai_tro"] == "Admin"
    assert body["data"]["trang_thai"] == "active"


def test_phien_dang_dang_nhap_nhung_bi_khoa(client, gan_dao):
    """Đã đăng nhập nhưng bị banned → status False, message tiếng Việt, data None."""
    gan_dao(
        {"manager1": _user_quan_ly()},
        {8: {"UserId": 8, "FullName": "Nguyễn Thị Quản Lý", "Role_Id": 2,
             "trang_thai": "banned", "Phone": "0900000000", "Address": "Hà Nội"}},
    )
    _dang_nhap(client, gan_dao)

    resp = client.get("/api/phien")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is False
    assert "khóa" in body["message"].lower()
    assert body["data"] is None


def test_phien_dang_xuat_xoa_phien(client, gan_dao):
    """Đăng xuất → session xóa → /api/phien coi như chưa đăng nhập."""
    gan_dao(
        {"manager1": _user_quan_ly()},
        {8: {"UserId": 8, "FullName": "Nguyễn Thị Quản Lý", "Role_Id": 2,
             "trang_thai": "active", "Phone": "0900000000", "Address": "Hà Nội"}},
    )
    _dang_nhap(client, gan_dao)

    assert client.post("/api/dang-xuat").get_json() == {
        "status": True, "message": "Đã đăng xuất."
    }

    resp = client.get("/api/phien")
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Bạn chưa đăng nhập!"
    assert body["data"] is None
