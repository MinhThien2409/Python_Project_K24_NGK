# -*- coding: utf-8 -*-
"""Integration test cấp lại mật khẩu (feature 002, US4) qua Flask test_client.

Login Quản lý → POST /api/cap-lai-mat-khau; đăng nhập bằng mật khẩu mới OK và
mật khẩu cũ fail; sau reset mật khẩu mới không xuất hiện trong GET /api/users;
reset user đang banned vẫn giữ banned; mật khẩu ngắn / target Admin bị từ chối.
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
    }


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def _gan_dao(app_voi_dao, user_dao):
    app_voi_dao(user_dao=user_dao, danh_muc_dao=conftest.FakeDanhMucDao())


def _login(client, username, password="123456"):
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": username, "mat_khau": password})
    assert resp.status_code == 200
    return resp.get_json()


def _tao_user_dao():
    return conftest.FakeUserDaoBus(
        users={
            "manager1": _user(8, 2, "manager1", "Quản Lý"),
            "customer1": _user(9, 4, "customer1", "Khách Hàng"),
        },
        thong_tin={
            8: _thong_tin(8, 2, ten="Quản Lý"),
            9: _thong_tin(9, 4, ten="Khách Hàng"),
        },
    )


def test_cap_lai_mat_khau_ngau_nhien_dang_nhap_moi_ok(client, app_voi_dao):
    user_dao = _tao_user_dao()
    _gan_dao(app_voi_dao, user_dao)

    _login(client, "manager1")
    resp = client.post("/api/cap-lai-mat-khau", json={"ma_user": 9})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] is True
    assert "cấp lại mật khẩu" in body["message"].lower()
    mat_khau_moi = body["data"]["mat_khau_moi"]
    assert len(mat_khau_moi) >= 6
    assert body["data"]["ma_user"] == 9
    assert body["data"]["ten_user"] == "Khách Hàng"

    # Đăng nhập bằng mật khẩu mới thành công
    assert _login(client, "customer1", mat_khau_moi)["status"] is True
    # Mật khẩu cũ thất bại
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": "customer1", "mat_khau": "123456"})
    assert resp.get_json()["status"] is False


def test_mat_khau_moi_khong_xuat_hien_trong_danh_sach(client, app_voi_dao):
    user_dao = _tao_user_dao()
    _gan_dao(app_voi_dao, user_dao)

    _login(client, "manager1")
    resp = client.post("/api/cap-lai-mat-khau", json={"ma_user": 9})
    mat_khau_moi = resp.get_json()["data"]["mat_khau_moi"]

    # 015 FR-012: Quản lý được phép GET /api/users (SC-004) — danh sách vẫn
    # không chứa mật khẩu mới (bất biến FR-011) khi truy vấn qua API.
    resp = client.get("/api/users")
    assert resp.status_code == 200
    assert resp.get_json()["status"] is True
    noi_dung_api = str(resp.get_json()["data"])
    assert mat_khau_moi not in noi_dung_api

    # lay_danh_sach_user KHÔNG chứa mật khẩu mới (FR-011)
    danh_sach = user_dao.lay_danh_sach_user()
    assert mat_khau_moi not in str(danh_sach)


def test_mat_khau_nhap_ngan_bi_tu_choi(client, app_voi_dao):
    user_dao = _tao_user_dao()
    _gan_dao(app_voi_dao, user_dao)

    _login(client, "manager1")
    resp = client.post("/api/cap-lai-mat-khau",
                       json={"ma_user": 9, "mat_khau_moi": "123"})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] is False
    assert body["message"] == "Mật khẩu phải có ít nhất 6 ký tự!"


def test_cap_lai_mat_khau_admin_bi_tu_choi(client, app_voi_dao):
    user_dao = conftest.FakeUserDaoBus(
        users={
            "manager1": _user(8, 2, "manager1", "Quản Lý"),
            "user1": _user(1, 1, "user1", "Admin"),
        },
        thong_tin={
            8: _thong_tin(8, 2, ten="Quản Lý"),
            1: _thong_tin(1, 1, ten="Admin"),
        },
    )
    _gan_dao(app_voi_dao, user_dao)

    _login(client, "manager1")
    resp = client.post("/api/cap-lai-mat-khau", json={"ma_user": 1})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] is False
    assert body["message"] == "Không thể cấp lại mật khẩu cho tài khoản Admin!"


def test_reset_user_banned_van_giu_banned(client, app_voi_dao):
    user_dao = conftest.FakeUserDaoBus(
        users={
            "manager1": _user(8, 2, "manager1", "Quản Lý"),
            "customer_bi_khoa": _user(9, 4, "customer_bi_khoa", "Bị Khóa"),
        },
        thong_tin={
            8: _thong_tin(8, 2, ten="Quản Lý"),
            9: _thong_tin(9, 4, trang_thai="banned", ten="Bị Khóa"),
        },
    )
    _gan_dao(app_voi_dao, user_dao)

    _login(client, "manager1")
    resp = client.post("/api/cap-lai-mat-khau",
                       json={"ma_user": 9, "mat_khau_moi": "matkhau67890"})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] is True

    # Mật khẩu mới không tự mở khóa — user vẫn banned, đăng nhập vẫn bị từ chối
    assert user_dao.thong_tin[9]["trang_thai"] == "banned"
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": "customer_bi_khoa", "mat_khau": "matkhau67890"})
    assert resp.get_json()["status"] is False
    assert "bị khóa" in resp.get_json()["message"]


def test_user_khong_ton_tai_bi_tu_choi(client, app_voi_dao):
    user_dao = _tao_user_dao()
    _gan_dao(app_voi_dao, user_dao)

    _login(client, "manager1")
    resp = client.post("/api/cap-lai-mat-khau", json={"ma_user": 999})
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Tài khoản không tồn tại!"