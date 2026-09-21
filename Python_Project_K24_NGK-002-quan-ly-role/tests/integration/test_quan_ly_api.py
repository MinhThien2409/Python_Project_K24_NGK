# -*- coding: utf-8 -*-
"""Integration test quản lý Quản lý (008 US3, T030) — /api/quan-ly.

- Gate Admin-only: chưa đăng nhập / Customer / Quản lý → 403.
- GET  /api/quan-ly            → danh sách chỉ Quản lý, không mật khẩu.
- POST /api/quan-ly            → tạo Quản lý mới.
- PUT  /api/quan-ly/<id>       → sửa thông tin Quản lý.
- DELETE /api/quan-ly/<id>     → xóa Quản lý.

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""

import pytest

import app as app_module
from app import app

import conftest
from back_end.Model.User import User


def _user(ma_user, role_id, username, ten="Người dùng"):
    return User(
        ma_user=ma_user, ma_nhom_quyen=role_id, ten_user=ten,
        sdt="0900000000", dia_chi="Hà Nội", cmnd="001099000000",
        tendangnhap=username, mat_khau="123456",
    )


def _thong_tin(ma_user, role_id, trang_thai="active", ten="Người dùng"):
    return {
        "UserId": ma_user, "Role_Id": role_id, "trang_thai": trang_thai,
        "FullName": ten, "Phone": "0900000000", "Address": "Hà Nội",
        "Username": "username", "Password": "123456",
    }


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture
def dao_admin(app_voi_dao):
    """FakeUserDaoBus có 1 Admin (ma_user=1) + 1 Quản lý (ma_user=2), gắn vào app."""
    user_dao = conftest.FakeUserDaoBus(
        users={
            "admin": _user(1, 1, "admin", "Admin"),
            "quanly1": _user(2, 2, "quanly1", "Quản Lý"),
        },
        thong_tin={
            1: _thong_tin(1, 1, "active", "Admin"),
            2: _thong_tin(2, 2, "active", "Quản Lý"),
        },
    )
    app_voi_dao(user_dao=user_dao)
    return user_dao


def _dang_nhap(client, username):
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": username, "mat_khau": "123456"})
    assert resp.status_code == 200
    return resp.get_json()


# ── Gate Admin-only ──────────────────────────────────────────────────────────
def test_chua_dang_nhap_403(client, dao_admin):
    resp = client.get("/api/quan-ly")
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Bạn chưa đăng nhập!"


@pytest.mark.parametrize("role_id,username,ma_user", [(3, "seller", 9),
                                                      (4, "khach", 10)])
def test_thuong_user_403(client, dao_admin, role_id, username, ma_user):
    dao_admin.users[username] = _user(ma_user, role_id, username)
    dao_admin.thong_tin[ma_user] = _thong_tin(ma_user, role_id)
    _dang_nhap(client, username)

    resp = client.get("/api/quan-ly")
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Bạn không có quyền thực hiện chức năng này!"


def test_quan_ly_khong_du_quyen_403(client, dao_admin):
    _dang_nhap(client, "quanly1")

    resp = client.post("/api/quan-ly",
                       json={"ten_user": "X", "tendangnhap": "x", "mat_khau": "123456"})
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Bạn không có quyền thực hiện chức năng này!"


# ── GET: danh sách chỉ Quản lý ───────────────────────────────────────────────
def test_admin_get_danh_sach_quan_ly(client, dao_admin):
    _dang_nhap(client, "admin")

    resp = client.get("/api/quan-ly")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is True
    danh_sach = body["data"]
    assert [d["ten_user"] for d in danh_sach] == ["Quản Lý"]
    assert [d["ma_nhom_quyen"] for d in danh_sach] == [2]
    # Bất biến US2: không trả mật khẩu trong danh sách
    assert all("Password" not in d and "mat_khau" not in d for d in danh_sach)


# ── POST: tạo Quản lý ────────────────────────────────────────────────────────
def test_admin_post_tao_quan_ly(client, dao_admin):
    _dang_nhap(client, "admin")

    resp = client.post("/api/quan-ly", json={
        "ten_user": "Quản Lý Mới", "tendangnhap": "quanly2",
        "mat_khau": "123456", "sdt": "0912345678", "dia_chi": "Hà Nội",
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is True
    assert body["data"]["ma_user"] == 3
    assert body["data"]["tendangnhap"] == "quanly2"
    # Trạng thái mới thực sự được ghi vào fake DAO (Users + Accounts liên kết)
    assert "quanly2" in dao_admin.users
    assert dao_admin.thong_tin[3]["Role_Id"] == 2
    assert dao_admin.thong_tin[3]["trang_thai"] == "active"


def test_admin_post_trung_tendangnhap_tu_choi(client, dao_admin):
    _dang_nhap(client, "admin")

    resp = client.post("/api/quan-ly", json={
        "ten_user": "Trùng", "tendangnhap": "quanly1", "mat_khau": "123456",
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is False
    assert "đã có người sử dụng" in body["message"]


# ── PUT: sửa Quản lý ─────────────────────────────────────────────────────────
def test_admin_put_sua_quan_ly(client, dao_admin):
    _dang_nhap(client, "admin")

    resp = client.put("/api/quan-ly/2", json={
        "ten_user": "Quản Lý Sửa", "dia_chi": "TP.HCM", "sdt": "0911111111",
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is True
    assert dao_admin.users["quanly1"].ten_user == "Quản Lý Sửa"
    assert dao_admin.users["quanly1"].dia_chi == "TP.HCM"
    assert dao_admin.thong_tin[2]["FullName"] == "Quản Lý Sửa"


def test_admin_put_sua_admin_bi_chan(client, dao_admin):
    _dang_nhap(client, "admin")

    resp = client.put("/api/quan-ly/1", json={
        "ten_user": "Admin Giả", "dia_chi": "X", "sdt": "0900000000",
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is False
    assert "Admin" in body["message"]
    assert dao_admin.users["admin"].ten_user == "Admin"  # không bị sửa


# ── DELETE: xóa Quản lý ──────────────────────────────────────────────────────
def test_admin_delete_xoa_quan_ly(client, dao_admin):
    _dang_nhap(client, "admin")

    resp = client.delete("/api/quan-ly/2")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is True
    assert "quanly1" not in dao_admin.users
    assert 2 not in dao_admin.thong_tin
    assert "quanly1" not in dao_admin.mat_khau


def test_admin_delete_admin_bi_chan(client, dao_admin):
    _dang_nhap(client, "admin")

    resp = client.delete("/api/quan-ly/1")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is False
    assert "Admin" in body["message"]
    assert "admin" in dao_admin.users