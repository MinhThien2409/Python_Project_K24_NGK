# -*- coding: utf-8 -*-
"""Integration test Quản lý khóa/mở khóa Seller + cấp lại mật khẩu (016 US3).

- Quản lý → PUT /api/users/<id_seller>/status banned → 200 status:true;
  Seller đăng nhập thất bại; mở khóa → đăng nhập lại được.
- Quản lý → POST /api/cap-lai-mat-khau cho Seller → 200 trả mat_khau_moi;
  đăng nhập bằng mật khẩu mới thành công.
- Seller trực tiếp gọi PUT /api/users/<id>/status hoặc POST /api/cap-lai-mat-khau → 403.

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""

import pytest

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


CAU_TRUC = {
    "admin":  (1, 1, "Admin"),
    "quanly1": (2, 2, "Quản Lý"),
    "quanly2": (5, 2, "Quản Lý 2"),
    "seller1": (3, 3, "Seller 1"),
    "seller2": (4, 3, "Seller 2"),
    "khach1":  (9, 4, "Khách Hàng"),
}


def _dao_day_du():
    return conftest.FakeUserDaoBus(
        users={u: _user(*utt) for u, utt in CAU_TRUC.items()},
        thong_tin={ma: _thong_tin(ma, role, ten=ten)
                   for u, (ma, role, ten) in CAU_TRUC.items()},
    )


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture
def gan_dao(app_voi_dao):
    def _gan(user_dao):
        app_voi_dao(user_dao=user_dao)
    return _gan


def _dang_nhap(client, username, mat_khau="123456"):
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": username, "mat_khau": mat_khau})
    assert resp.status_code == 200
    return resp.get_json()


# ── Quản lý khóa/mở khóa Seller ──────────────────────────────────────────────
def test_quan_ly_khoa_seller_200_va_seller_dang_nhap_that_bai(client, gan_dao):
    gan_dao(_dao_day_du())
    _dang_nhap(client, "quanly1")

    resp = client.put("/api/users/3/status", json={"status": "banned"})
    assert resp.status_code == 200
    assert resp.get_json() == {"status": True, "message": "Đã khóa tài khoản!"}

    # Seller bị khóa → đăng nhập thất bại
    ket_qua = _dang_nhap(client, "seller1")
    assert ket_qua["status"] is False
    assert "bị khóa" in ket_qua["message"]


def test_quan_ly_mo_khoa_seller_dang_nhap_lai_duoc(client, gan_dao):
    gan_dao(_dao_day_du())
    _dang_nhap(client, "quanly1")
    client.put("/api/users/3/status", json={"status": "banned"})
    assert _dang_nhap(client, "seller1")["status"] is False

    # Mở khóa → đăng nhập Seller lại OK
    resp = client.put("/api/users/3/status", json={"status": "active"})
    assert resp.status_code == 200
    assert resp.get_json() == {"status": True, "message": "Đã mở khóa tài khoản!"}
    ket_qua = _dang_nhap(client, "seller1")
    assert ket_qua["status"] is True


# ── Quản lý cấp lại mật khẩu Seller ──────────────────────────────────────────
def test_quan_ly_cap_lai_mat_khau_seller_dang_nhap_mat_khau_moi(client, gan_dao):
    gan_dao(_dao_day_du())
    _dang_nhap(client, "quanly1")

    resp = client.post("/api/cap-lai-mat-khau",
                       json={"ma_user": 3, "mat_khau_moi": "s3cretX9"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is True
    assert body["data"]["mat_khau_moi"] == "s3cretX9"

    # Mật khẩu cũ không còn dùng được, mật khẩu mới OK
    assert _dang_nhap(client, "seller1")["status"] is False
    ket_qua = _dang_nhap(client, "seller1", "s3cretX9")
    assert ket_qua["status"] is True


# ── Seller trực tiếp gọi API quyền Quản lý → 403 ─────────────────────────────
def test_seller_goi_status_403(client, gan_dao):
    gan_dao(_dao_day_du())
    _dang_nhap(client, "seller1")

    resp = client.put("/api/users/9/status", json={"status": "banned"})
    assert resp.status_code == 403


def test_seller_goi_cap_lai_mat_khau_403(client, gan_dao):
    gan_dao(_dao_day_du())
    _dang_nhap(client, "seller1")

    resp = client.post("/api/cap-lai-mat-khau",
                       json={"ma_user": 9, "mat_khau_moi": "abc123"})
    assert resp.status_code == 403


# ── Quản lý KHÔNG thao tác được Quản lý / Admin (đảm bảo không lệch sang khác) ─
def test_quan_ly_khong_khoa_duoc_quan_ly_khac(client, gan_dao):
    gan_dao(_dao_day_du())
    _dang_nhap(client, "quanly1")

    resp = client.put("/api/users/1/status", json={"status": "banned"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] is False
    assert resp.get_json()["message"] == "Không ai có quyền khóa tài khoản Admin!"

    resp = client.put("/api/users/5/status", json={"status": "banned"})
    assert resp.get_json()["status"] is False
    assert resp.get_json()["message"] == "Không thể khóa tài khoản Quản lý!"