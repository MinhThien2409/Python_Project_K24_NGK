# -*- coding: utf-8 -*-
"""Integration test endpoint Admin/Quản lý (feature 003, Nguyên tắc IV — test-first).

Bao phủ:
- T009 [US1]: đếm Admin luôn bằng 1 qua test_client.
- T016 [US2]: POST /api/quan-ly (tạo → login mới OK, sai vai trò → 403, phiên hết hạn → 403).
- T023 [US3]: GET/PUT/DELETE /api/quan-ly (danh sách chỉ Quản lý không mật khẩu,
  sửa hiển thị đúng, xóa → login fail, sai vai trò → 403).

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""

import pytest

import app as app_module
from app import app

import conftest
from back_end.Model.User import User


def _user(ma_user, role_id, username, ten_user="Người dùng"):
    return User(
        ma_user=ma_user, ma_nhom_quyen=role_id, ten_user=ten_user,
        sdt="0900000000", dia_chi="Hà Nội", cmnd=None,
        tendangnhap=username, mat_khau="123456",
    )


def _thong_tin(ma_user, role_id, trang_thai="active"):
    return {
        "UserId": ma_user, "FullName": "Người dùng", "Phone": "0900000000",
        "Address": "Hà Nội", "Role_Id": role_id, "trang_thai": trang_thai,
        "Username": f"user{ma_user}", "Password": "123456",
    }


def _dung_he_thong_co_ban(app_voi_dao):
    """Dựng hệ thống: 1 Admin + 1 Quản lý + 1 Seller + 1 Customer."""
    users = {
        "user1": _user(1, 1, "user1", "Admin"),
        "quanly1": _user(2, 2, "quanly1", "Quản lý Một"),
        "seller1": _user(3, 3, "seller1", "Seller"),
        "customer1": _user(4, 4, "customer1", "Customer"),
    }
    thong_tin = {
        1: _thong_tin(1, 1),
        2: _thong_tin(2, 2),
        3: _thong_tin(3, 3),
        4: _thong_tin(4, 4),
    }
    mat_khau = {k: "123456" for k in users}
    user_dao = conftest.FakeUserDaoBus(
        users=users, thong_tin=thong_tin, mat_khau=mat_khau,
    )
    app_voi_dao(user_dao=user_dao)
    return user_dao


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def _dang_nhap(client, username, password="123456"):
    return client.post("/api/dang-nhap",
                       json={"tendangnhap": username, "mat_khau": password})


# ── T009 [US1]: Admin luôn bằng 1 ─────────────────────────────────────────────
def test_dem_admin_luon_bang_mot(client, app_voi_dao):
    user_dao = _dung_he_thong_co_ban(app_voi_dao)
    assert user_dao.dem_admin() == 1


def test_tao_admin_thu_hai_bi_tu_choi(client, app_voi_dao):
    _dung_he_thong_co_ban(app_voi_dao)
    _dang_nhap(client, "user1")
    resp = client.post("/api/quan-ly", json={
        "ten_user": "Admin Mới", "tendangnhap": "admin2",
        "mat_khau": "123456", "vai_tro": "Admin",
    })
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Không thể tạo thêm tài khoản Admin!"


# ── T016 [US2]: POST /api/quan-ly ─────────────────────────────────────────────
def test_tao_quan_ly_roi_dang_nhap_moi_ok(client, app_voi_dao):
    _dung_he_thong_co_ban(app_voi_dao)
    _dang_nhap(client, "user1")
    resp = client.post("/api/quan-ly", json={
        "ten_user": "Quản lý Mới", "tendangnhap": "quanly_moi",
        "mat_khau": "123456", "sdt": "0901111111", "dia_chi": "Hà Nội",
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is True
    assert body["message"] == "Đã tạo tài khoản Quản lý!"

    client.post("/api/dang-xuat")
    resp = _dang_nhap(client, "quanly_moi")
    body = resp.get_json()
    assert body["status"] is True
    assert body["data"]["ma_nhom_quyen"] == 2


def test_tao_quan_ly_trung_ten_bi_tu_choi(client, app_voi_dao):
    _dung_he_thong_co_ban(app_voi_dao)
    _dang_nhap(client, "user1")
    resp = client.post("/api/quan-ly", json={
        "ten_user": "Trùng", "tendangnhap": "quanly1", "mat_khau": "123456",
    })
    assert resp.get_json()["status"] is False
    assert "đã có người sử dụng" in resp.get_json()["message"]


def test_tao_quan_ly_mat_khau_ngan_bi_tu_choi(client, app_voi_dao):
    _dung_he_thong_co_ban(app_voi_dao)
    _dang_nhap(client, "user1")
    resp = client.post("/api/quan-ly", json={
        "ten_user": "Mới", "tendangnhap": "quanly_new", "mat_khau": "123",
    })
    assert resp.get_json()["status"] is False
    assert resp.get_json()["message"] == "Mật khẩu phải có ít nhất 6 ký tự!"


@pytest.mark.parametrize("username", ["quanly1", "seller1", "customer1"])
def test_tao_quan_ly_sai_vai_tro_403(client, app_voi_dao, username):
    _dung_he_thong_co_ban(app_voi_dao)
    _dang_nhap(client, username)
    resp = client.post("/api/quan-ly", json={
        "ten_user": "Mới", "tendangnhap": "quanly_x", "mat_khau": "123456",
    })
    assert resp.status_code == 403
    assert resp.get_json()["status"] is False


def test_tao_quan_ly_phien_het_han_403(client, app_voi_dao):
    _dung_he_thong_co_ban(app_voi_dao)
    resp = client.post("/api/quan-ly", json={
        "ten_user": "Mới", "tendangnhap": "quanly_x", "mat_khau": "123456",
    })
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Bạn chưa đăng nhập!"


# ── T023 [US3]: GET/PUT/DELETE /api/quan-ly ───────────────────────────────────
def test_danh_sach_chi_quan_ly_khong_mat_khau(client, app_voi_dao):
    _dung_he_thong_co_ban(app_voi_dao)
    _dang_nhap(client, "user1")
    resp = client.get("/api/quan-ly")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is True
    for item in body["data"]:
        assert item["ma_nhom_quyen"] == 2
        assert "mat_khau" not in item
        assert "Password" not in item


def test_sua_quan_ly_hien_thi_dung(client, app_voi_dao):
    _dung_he_thong_co_ban(app_voi_dao)
    _dang_nhap(client, "user1")
    resp = client.put("/api/quan-ly/2", json={
        "ten_user": "Tên Đã Sửa", "dia_chi": "Địa chỉ Mới", "sdt": "0909999999",
    })
    assert resp.get_json()["status"] is True

    resp = client.get("/api/quan-ly")
    ds = resp.get_json()["data"]
    muc = next(m for m in ds if m["ma_user"] == 2)
    assert muc["ten_user"] == "Tên Đã Sửa"
    assert muc["ma_nhom_quyen"] == 2


def test_xoa_quan_ly_roi_dang_nhap_that_bai(client, app_voi_dao):
    _dung_he_thong_co_ban(app_voi_dao)
    _dang_nhap(client, "user1")
    resp = client.delete("/api/quan-ly/2")
    assert resp.get_json()["status"] is True

    client.post("/api/dang-xuat")
    resp = _dang_nhap(client, "quanly1")
    assert resp.get_json()["status"] is False


@pytest.mark.parametrize("username", ["quanly1", "seller1", "customer1"])
def test_sua_xoa_sai_vai_tro_403(client, app_voi_dao, username):
    _dung_he_thong_co_ban(app_voi_dao)
    _dang_nhap(client, username)
    resp = client.put("/api/quan-ly/2", json={"ten_user": "X"})
    assert resp.status_code == 403
    resp = client.delete("/api/quan-ly/2")
    assert resp.status_code == 403
    resp = client.get("/api/quan-ly")
    assert resp.status_code == 403
