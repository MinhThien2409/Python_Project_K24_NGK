# -*- coding: utf-8 -*-
"""Integration test phân quyền sau tách bảng (008 US3, T031) — /api/users.

Cập nhật theo 015 FR-012: GET /api/users giờ dành cho Admin & Quản lý.
- Tài khoản Customer gọi endpoint quản trị (`GET /api/users`) → 403.
- Tài khoản Quản lý gọi cùng endpoint → thành công (200) — SC-004.
- Tài khoản Admin gọi cùng endpoint → thành công (200).
- Tài khoản `banned` gọi → 403 (bị khóa, kể cả khi phiên còn tồn tại).

Danh sách trả về KHÔNG được chứa mật khẩu (bất biến US2, FR-011).

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
def dao_voi_quan_ly(app_voi_dao):
    """FakeUserDaoBus: 1 Admin + 1 Quản lý hoạt động, gắn vào app."""
    user_dao = conftest.FakeUserDaoBus(
        users={
            "admin": _user(1, 1, "admin", "Admin"),
            "quanly1": _user(2, 2, "quanly1", "Quản Lý"),
            "khach1": _user(9, 4, "khach1", "Khách Hàng"),
        },
        thong_tin={
            1: _thong_tin(1, 1, "active", "Admin"),
            2: _thong_tin(2, 2, "active", "Quản Lý"),
            9: _thong_tin(9, 4, "active", "Khách Hàng"),
        },
    )
    app_voi_dao(user_dao=user_dao)
    return user_dao

def _dang_nhap(client, username):
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": username, "mat_khau": "123456"})
    assert resp.status_code == 200
    return resp.get_json()

# ── Customer gọi → 403 ───────────────────────────────────────────────────────
def test_customer_goi_users_403(client, dao_voi_quan_ly):
    _dang_nhap(client, "khach1")

    resp = client.get("/api/users")
    assert resp.status_code == 403
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Bạn không có quyền thực hiện chức năng này!"
    assert body["data"] is None

# ── Quản lý gọi → 200 (015 FR-012: Quản lý được truy cập) ──────────────────
def test_quan_ly_goi_users_200(client, dao_voi_quan_ly):
    """015 FR-012: Quản lý truy cập danh sách tài khoản (SC-004 — hết lỗi 403)."""
    _dang_nhap(client, "quanly1")

    resp = client.get("/api/users")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is True
    danh_sach = body["data"]
    assert len(danh_sach) == 3
    for d in danh_sach:
        assert "Password" not in d and "mat_khau" not in d

# ── Admin gọi → 200 + danh sách (không mật khẩu) ─────────────────────────────
def test_admin_goi_users_200(client, dao_voi_quan_ly):
    _dang_nhap(client, "admin")

    resp = client.get("/api/users")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is True
    danh_sach = body["data"]
    assert len(danh_sach) == 3
    ten_users = [d["ten_user"] for d in danh_sach]
    assert "Admin" in ten_users and "Quản Lý" in ten_users and "Khách Hàng" in ten_users
    # Bất biến US2 (FR-011): không trả mật khẩu
    for d in danh_sach:
        assert "Password" not in d and "mat_khau" not in d
        assert set(d.keys()) == {"ma_user", "ten_user", "tendangnhap", "sdt",
                                 "dia_chi", "ma_nhom_quyen", "ten_nhom_quyen",
                                 "trang_thai"}

def test_admin_goi_users_thay_du_vai_tro(client, dao_voi_quan_ly):
    _dang_nhap(client, "admin")

    resp = client.get("/api/users")
    danh_sach = resp.get_json()["data"]
    bang_vai_tro = {d["ma_nhom_quyen"] for d in danh_sach}
    assert bang_vai_tro == {1, 2, 4}
    assert {d["ten_nhom_quyen"] for d in danh_sach} == {"Admin", "Quản lý", "Customer"}

# ── Tài khoản banned gọi → 403 ───────────────────────────────────────────────
def test_tai_khoan_ban_goi_users_403(client, dao_voi_quan_ly):
    # Giả lập Admin đã bị khóa (phiên vẫn còn tồn tại từ trước khi khóa)
    dao_voi_quan_ly.thong_tin[1]["trang_thai"] = "banned"
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    resp = client.get("/api/users")
    assert resp.status_code == 403
    body = resp.get_json()
    assert body["status"] is False
    assert "khóa" in body["message"].lower()

# ── Chưa đăng nhập → 403 ─────────────────────────────────────────────────────
def test_chua_dang_nhap_403(client, dao_voi_quan_ly):
    resp = client.get("/api/users")
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Bạn chưa đăng nhập!"