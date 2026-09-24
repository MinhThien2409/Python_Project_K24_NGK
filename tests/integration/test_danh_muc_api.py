# -*- coding: utf-8 -*-
"""Integration test CRUD danh mục (feature 002, US1) qua Flask test_client.

Login Quản lý tạo session → POST/PUT/DELETE /api/categories[/<id>].
Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""

import pytest

import app as app_module
from app import app

import conftest
from back_end.Model.User import User


def _user(ma_user=8, role_id=2, username="manager1"):
    return User(
        ma_user=ma_user, ma_nhom_quyen=role_id, ten_user="Nguyễn Thị Quản Lý",
        sdt="0900000000", dia_chi="Hà Nội", cmnd="001099000000",
        tendangnhap=username, mat_khau="123456",
    )


def _thong_tin(ma_user=8, role_id=2, trang_thai="active"):
    return {
        "UserId": ma_user, "Role_Id": role_id, "trang_thai": trang_thai,
        "FullName": "Nguyễn Thị Quản Lý", "Phone": "0900000000", "Address": "Hà Nội",
    }


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture
def gan_dao(app_voi_dao):
    """Gắn FakeUserDaoBus (login Quản lý) + FakeDanhMucDao vào app module."""

    def _gan(danh_muc_dao):
        user_dao = conftest.FakeUserDaoBus(
            users={"manager1": _user()},
            thong_tin={8: _thong_tin()},
        )
        app_voi_dao(user_dao=user_dao, danh_muc_dao=danh_muc_dao)

    return _gan


def _dang_nhap(client):
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": "manager1", "mat_khau": "123456"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] is True


# ── POST /api/categories ──────────────────────────────────────────────────────
def test_them_danh_muc_hop_le(client, gan_dao):
    dao = conftest.FakeDanhMucDao()
    gan_dao(dao)
    _dang_nhap(client)

    resp = client.post("/api/categories", json={"name": "Đồ gia dụng"})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] is True
    assert body["message"] == "Đã thêm danh mục 'Đồ gia dụng' thành công!"
    assert dao.categories == {1: "Đồ gia dụng"}


def test_them_danh_muc_trung_ten(client, gan_dao):
    dao = conftest.FakeDanhMucDao()
    dao.categories = {1: "Đồ gia dụng"}
    dao.next_id = 2
    gan_dao(dao)
    _dang_nhap(client)

    resp = client.post("/api/categories", json={"name": "đồ GIA DỤNG  "})
    body = resp.get_json()
    assert body["status"] is False
    assert "đã tồn tại" in body["message"]
    assert len(dao.categories) == 1  # không thêm trùng


def test_them_ten_101_ky_tu(client, gan_dao):
    dao = conftest.FakeDanhMucDao()
    gan_dao(dao)
    _dang_nhap(client)

    resp = client.post("/api/categories", json={"name": "D" * 101})
    body = resp.get_json()
    assert body["status"] is False
    assert "100 ký tự" in body["message"]


# ── PUT /api/categories/<id> ──────────────────────────────────────────────────
def test_sua_danh_muc(client, gan_dao):
    dao = conftest.FakeDanhMucDao()
    dao.categories = {1: "Điện thoại"}
    dao.next_id = 2
    gan_dao(dao)
    _dang_nhap(client)

    resp = client.put("/api/categories/1", json={"name": "Điện thoại & Phụ kiện"})
    body = resp.get_json()
    assert body["status"] is True
    assert dao.categories[1] == "Điện thoại & Phụ kiện"


def test_sua_id_khong_ton_tai(client, gan_dao):
    dao = conftest.FakeDanhMucDao()
    dao.categories = {1: "Điện thoại"}
    dao.next_id = 2
    gan_dao(dao)
    _dang_nhap(client)

    resp = client.put("/api/categories/99", json={"name": "Tên mới"})
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Không tìm thấy danh mục!"


# ── DELETE /api/categories/<id> ───────────────────────────────────────────────
def test_xoa_danh_muc_rong(client, gan_dao):
    dao = conftest.FakeDanhMucDao()
    dao.categories = {1: "Điện thoại"}
    dao.next_id = 2
    gan_dao(dao)
    _dang_nhap(client)

    resp = client.delete("/api/categories/1")
    body = resp.get_json()
    assert body["status"] is True
    assert 1 not in dao.categories


def test_xoa_danh_muc_con_san_pham(client, gan_dao):
    dao = conftest.FakeDanhMucDao()
    dao.categories = {1: "Điện thoại"}
    dao.next_id = 2
    dao.products = {1: 5}
    gan_dao(dao)
    _dang_nhap(client)

    resp = client.delete("/api/categories/1")
    body = resp.get_json()
    assert body["status"] is False
    assert (body["message"] ==
            "Danh mục đang có sản phẩm, không thể xóa! Hãy chuyển sản phẩm sang danh mục khác rồi thử lại.")
    assert 1 in dao.categories  # giữ nguyên


def test_xoa_id_khong_ton_tai(client, gan_dao):
    dao = conftest.FakeDanhMucDao()
    gan_dao(dao)
    _dang_nhap(client)

    resp = client.delete("/api/categories/99")
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Không tìm thấy danh mục!"