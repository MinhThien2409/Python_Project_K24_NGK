# -*- coding: utf-8 -*-
"""Integration test phiên đăng nhập (feature 002, R1):
- Đăng nhập thành công lưu session['user_id'] (cookie ký).
- GET /api/phien trả đúng 3 nhánh: đang đăng nhập / banned / chưa đăng nhập.
- POST /api/dang-xuat xóa session.

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
    """Thay DAO thật cho endpoint đăng nhập/phiên — KHÔNG chạm DB."""

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
    """Gắn UserBus với DAO giả vào module app cho trước các lần gọi endpoint."""

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


def test_dang_nhap_luu_session(client, gan_dao):
    gan_dao(
        {"manager1": _user_quan_ly()},
        {8: {"UserId": 8, "FullName": "Nguyễn Thị Quản Lý", "Role_Id": 2,
             "trang_thai": "active", "Phone": "0900000000", "Address": "Hà Nội"}},
    )
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": "manager1", "mat_khau": "123456"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] is True

    with client.session_transaction() as sess:
        assert sess.get("user_id") == 8


def test_api_phien_dang_dang_nhap(client, gan_dao):
    gan_dao(
        {"manager1": _user_quan_ly()},
        {8: {"UserId": 8, "FullName": "Nguyễn Thị Quản Lý", "Role_Id": 2,
             "trang_thai": "active", "Phone": "0900000000", "Address": "Hà Nội"}},
    )
    client.post("/api/dang-nhap",
                json={"tendangnhap": "manager1", "mat_khau": "123456"})
    resp = client.get("/api/phien")
    body = resp.get_json()
    assert body["status"] is True
    assert body["data"]["ma_user"] == 8
    assert body["data"]["trang_thai"] == "active"
    assert body["data"]["ten_vai_tro"] == "Quản lý"
    assert body["data"]["ten_user"] == "Nguyễn Thị Quản Lý"


def test_api_phien_bi_khoa(client, gan_dao):
    gan_dao(
        {"manager1": _user_quan_ly()},
        {8: {"UserId": 8, "FullName": "Nguyễn Thị Quản Lý", "Role_Id": 2,
             "trang_thai": "banned", "Phone": "0900000000", "Address": "Hà Nội"}},
    )
    client.post("/api/dang-nhap",
                json={"tendangnhap": "manager1", "mat_khau": "123456"})
    resp = client.get("/api/phien")
    body = resp.get_json()
    assert body["status"] is False
    assert "khóa" in body["message"].lower()
    assert body["data"] is None


def test_api_phien_chua_dang_nhap(client):
    resp = client.get("/api/phien")
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Bạn chưa đăng nhập!"
    assert body["data"] is None


def test_dang_xuat_xoa_session(client, gan_dao):
    gan_dao(
        {"manager1": _user_quan_ly()},
        {8: {"UserId": 8, "FullName": "Nguyễn Thị Quản Lý", "Role_Id": 2,
             "trang_thai": "active", "Phone": "0900000000", "Address": "Hà Nội"}},
    )
    client.post("/api/dang-nhap",
                json={"tendangnhap": "manager1", "mat_khau": "123456"})

    resp = client.post("/api/dang-xuat")
    assert resp.get_json() == {"status": True, "message": "Đã đăng xuất."}

    # Session đã xóa → /api/phien coi như chưa đăng nhập
    resp_phien = client.get("/api/phien")
    assert resp_phien.get_json()["status"] is False
    assert resp_phien.get_json()["message"] == "Bạn chưa đăng nhập!"