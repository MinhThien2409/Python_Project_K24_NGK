# -*- coding: utf-8 -*-
"""Integration test phân quyền (feature 002) — các endpoint quản trị phải chặn.

US1 (T014): POST/PUT/DELETE /api/categories[/<id>] — chưa đăng nhập / Seller /
Customer → HTTP 403 + body hợp đồng; GET /api/categories vẫn công khai 200.

US2 (T023): GET /api/seller-requests, POST /api/duyet-seller/<id>,
POST /api/tu-choi-seller/<id> → HTTP 403 khi không đủ quyền.

US3 (T034): GET /api/users, PUT /api/users/<ma_user>/status → HTTP 403.

US4 (T043): POST /api/cap-lai-mat-khau → HTTP 403.

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""

import pytest

import app as app_module
from app import app

import conftest
from back_end.Model.User import User


def _user(ma_user, role_id, username):
    return User(
        ma_user=ma_user, ma_nhom_quyen=role_id, ten_user="Người dùng",
        sdt="0900000000", dia_chi="Hà Nội", cmnd="001099000000",
        tendangnhap=username, mat_khau="123456",
    )


def _thong_tin(ma_user, role_id, trang_thai="active"):
    return {
        "UserId": ma_user, "Role_Id": role_id, "trang_thai": trang_thai,
        "FullName": "Người dùng", "Phone": "0900000000", "Address": "Hà Nội",
    }


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture
def gan_nguoi_dung(app_voi_dao):
    """Gắn FakeUserDaoBus với vai trò/trạng thái cho trước vào app module."""

    def _gan(role_id=4, username="customer1", trang_thai="active", ma_user=9):
        user_dao = conftest.FakeUserDaoBus(
            users={username: _user(ma_user, role_id, username)},
            thong_tin={ma_user: _thong_tin(ma_user, role_id, trang_thai)},
        )
        app_voi_dao(user_dao=user_dao,
                    danh_muc_dao=conftest.FakeDanhMucDao(),
                    gian_hang_dao=conftest.FakeGianHangDao())
        return user_dao

    return _gan


# ── US1: danh mục ────────────────────────────────────────────────────────────
def test_categories_chu_a_dang_nhap_edge_403(client, app_voi_dao):
    app_voi_dao(danh_muc_dao=conftest.FakeDanhMucDao())

    for method, url in [("post", "/api/categories"),
                        ("put", "/api/categories/1"),
                        ("delete", "/api/categories/1")]:
        resp = getattr(client, method)(url, json={"name": "X"})
        assert resp.status_code == 403, f"{method.upper()} {url}"
        body = resp.get_json()
        assert body["status"] is False
        assert body["message"] == "Bạn chưa đăng nhập!"
        assert body["data"] is None


@pytest.mark.parametrize("role_id,username,ma_user",
                         [(3, "seller1", 9), (4, "customer1", 10)],
                         ids=["seller", "customer"])
def test_categories_thuong_user_403(client, gan_nguoi_dung, role_id, username, ma_user):
    gan_nguoi_dung(role_id=role_id, username=username, ma_user=ma_user)
    client.post("/api/dang-nhap",
                json={"tendangnhap": username, "mat_khau": "123456"})

    for method, url in [("post", "/api/categories"),
                        ("put", "/api/categories/1"),
                        ("delete", "/api/categories/1")]:
        resp = getattr(client, method)(url, json={"name": "X"})
        assert resp.status_code == 403, f"{method.upper()} {url}"
        body = resp.get_json()
        assert body["status"] is False
        assert body["message"] == "Bạn không có quyền thực hiện chức năng này!"


def test_categories_get_van_cong_khai(client, gan_nguoi_dung):
    gan_nguoi_dung(role_id=4, username="customer1", ma_user=10)
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    assert resp.get_json()["status"] is True


# ── US2: duyệt người bán ─────────────────────────────────────────────────────
@pytest.mark.parametrize("method,url", [
    ("get", "/api/seller-requests"),
    ("post", "/api/duyet-seller/1"),
    ("post", "/api/tu-choi-seller/1"),
], ids=["seller-requests", "duyet-seller", "tu-choi-seller"])
def test_duyet_nguoi_ban_chua_dang_nhap_403(client, app_voi_dao, method, url):
    app_voi_dao(danh_muc_dao=conftest.FakeDanhMucDao(),
                gian_hang_dao=conftest.FakeGianHangDao())
    resp = getattr(client, method)(url, json={})
    assert resp.status_code == 403, f"{method.upper()} {url}"
    assert resp.get_json()["message"] == "Bạn chưa đăng nhập!"


@pytest.mark.parametrize("role_id,username,ma_user",
                         [(3, "seller1", 9), (4, "customer1", 10)],
                         ids=["seller", "customer"])
def test_duyet_nguoi_ban_thuong_user_403(client, gan_nguoi_dung, role_id, username, ma_user):
    gan_nguoi_dung(role_id=role_id, username=username, ma_user=ma_user)
    client.post("/api/dang-nhap",
                json={"tendangnhap": username, "mat_khau": "123456"})

    endpoints = [
        ("get", "/api/seller-requests", {}),
        ("post", "/api/duyet-seller/1", {}),
        ("post", "/api/tu-choi-seller/1", {"ly_do": "Hồ sơ thiếu"}),
    ]
    for method, url, body in endpoints:
        resp = getattr(client, method)(url, json=body)
        assert resp.status_code == 403, f"{method.upper()} {url}"
        assert resp.get_json()["message"] == "Bạn không có quyền thực hiện chức năng này!"


# ── US3: khóa tài khoản user ─────────────────────────────────────────────────
def test_users_chua_dang_nhap_403(client, app_voi_dao):
    app_voi_dao(danh_muc_dao=conftest.FakeDanhMucDao())
    resp = client.get("/api/users")
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Bạn chưa đăng nhập!"

    resp = client.put("/api/users/5/status", json={"status": "banned"})
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Bạn chưa đăng nhập!"


@pytest.mark.parametrize("role_id,username,ma_user",
                         [(3, "seller1", 9), (4, "customer1", 10)],
                         ids=["seller", "customer"])
def test_users_thuong_user_403(client, gan_nguoi_dung, role_id, username, ma_user):
    gan_nguoi_dung(role_id=role_id, username=username, ma_user=ma_user)
    client.post("/api/dang-nhap",
                json={"tendangnhap": username, "mat_khau": "123456"})

    resp = client.get("/api/users")
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Bạn không có quyền thực hiện chức năng này!"

    resp = client.put(f"/api/users/{ma_user}/status", json={"status": "banned"})
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Bạn không có quyền thực hiện chức năng này!"


# ── US4: cấp lại mật khẩu ────────────────────────────────────────────────────
def test_cap_lai_mat_khau_chua_dang_nhap_403(client, app_voi_dao):
    app_voi_dao(danh_muc_dao=conftest.FakeDanhMucDao())
    resp = client.post("/api/cap-lai-mat-khau", json={"ma_user": 5})
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Bạn chưa đăng nhập!"


@pytest.mark.parametrize("role_id,username,ma_user",
                         [(3, "seller1", 9), (4, "customer1", 10)],
                         ids=["seller", "customer"])
def test_cap_lai_mat_khau_thuong_user_403(client, gan_nguoi_dung, role_id, username, ma_user):
    gan_nguoi_dung(role_id=role_id, username=username, ma_user=ma_user)
    client.post("/api/dang-nhap",
                json={"tendangnhap": username, "mat_khau": "123456"})

    resp = client.post("/api/cap-lai-mat-khau", json={"ma_user": ma_user})
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Bạn không có quyền thực hiện chức năng này!"