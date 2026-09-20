# -*- coding: utf-8 -*-
"""Integration test khóa/mở khóa tài khoản (feature 002, US3) qua Flask test_client.

Login Quản lý → PUT /api/users/<ma_user>/status; kiểm tra đăng nhập của user
khóa thất bại; phiên cũ của user khóa gọi /api/don-hang/dat-hang → 403 (FR-009);
mở khóa → đăng nhập lại được. Admin khóa/mở khóa Quản lý (015 FR-008): thành
công, Quản lý bị khóa không đăng nhập được; Quản lý khóa Quản lý khác → từ chối.
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


def _login(client, username):
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": username, "mat_khau": "123456"})
    assert resp.status_code == 200
    return resp.get_json()


def _tao_user_dao(manager_ma=8):
    return conftest.FakeUserDaoBus(
        users={
            "manager1": _user(manager_ma, 2, "manager1", "Quản Lý"),
            "customer_bi_khoa": _user(9, 4, "customer_bi_khoa", "Customer"),
        },
        thong_tin={
            manager_ma: _thong_tin(manager_ma, 2, ten="Quản Lý"),
            9: _thong_tin(9, 4, ten="Customer"),
        },
    )


def test_khoa_thi_dang_nhap_that_bai(client, app_voi_dao):
    user_dao = _tao_user_dao()
    _gan_dao(app_voi_dao, user_dao)

    # Quản lý đăng nhập và khóa customer
    resp = _login(client, "manager1")
    assert resp["status"] is True
    resp = client.put("/api/users/9/status", json={"status": "banned"})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] is True
    assert body["message"] == "Đã khóa tài khoản!"

    # Customer bị khóa → đăng nhập bằng mật khẩu đúng vẫn thất bại
    resp = _login(client, "customer_bi_khoa")
    assert resp["status"] is False
    assert "bị khóa" in resp["message"]


def test_phien_cu_bi_khoa_khong_dung_duoc_api_nghiep_vu(client, app_voi_dao):
    user_dao = _tao_user_dao()
    _gan_dao(app_voi_dao, user_dao)

    # Phiên 1: customer đăng nhập (session còn)
    client_customer = app.test_client()
    app.config.update(TESTING=True)
    resp = _login(client_customer, "customer_bi_khoa")
    assert resp["status"] is True

    # Quản lý khóa customer ở client khác
    _login(client, "manager1")
    resp = client.put("/api/users/9/status", json={"status": "banned"})
    assert resp.get_json()["status"] is True

    # Phiên cũ của customer gọi đặt hàng → 403 (FR-009)
    resp = client_customer.post("/api/don-hang/dat-hang",
                                json={"UserId": 9, "Items": []})
    assert resp.status_code == 403
    body = resp.get_json()
    assert body["status"] is False
    assert "bị khóa" in body["message"]


def test_mo_khoa_dang_nhap_lai_ok(client, app_voi_dao):
    user_dao = _tao_user_dao()
    _gan_dao(app_voi_dao, user_dao)

    _login(client, "manager1")
    resp = client.put("/api/users/9/status", json={"status": "banned"})
    assert resp.get_json()["status"] is True
    assert _login(client, "customer_bi_khoa")["status"] is False

    # Mở khóa → đăng nhập lại thành công
    resp = client.put("/api/users/9/status", json={"status": "active"})
    assert resp.get_json()["status"] is True
    assert _login(client, "customer_bi_khoa")["status"] is True


def test_khoa_khong_ton_tai_tra_loi(client, app_voi_dao):
    user_dao = _tao_user_dao()
    _gan_dao(app_voi_dao, user_dao)
    _login(client, "manager1")

    resp = client.put("/api/users/999/status", json={"status": "banned"})
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Tài khoản không tồn tại!"


def test_status_rong_bi_tu_choi(client, app_voi_dao):
    user_dao = _tao_user_dao()
    _gan_dao(app_voi_dao, user_dao)
    _login(client, "manager1")

    resp = client.put("/api/users/9/status", json={"status": ""})
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Trạng thái không hợp lệ!"


def test_khoa_quan_ly_khac_bi_tu_choi(client, app_voi_dao):
    user_dao = conftest.FakeUserDaoBus(
        users={"manager1": _user(8, 2, "manager1", "Quản Lý")},
        thong_tin={8: _thong_tin(8, 2, ten="Quản Lý")},
    )
    user_dao.thong_tin[7] = _thong_tin(7, 2, ten="Quản Lý Khác")
    _gan_dao(app_voi_dao, user_dao)
    _login(client, "manager1")

    resp = client.put("/api/users/7/status", json={"status": "banned"})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] is False
    assert body["message"] == "Không thể khóa tài khoản Quản lý!"

def _tao_dao_admin_quan_ly():
    """Admin (user1) + Quản lý (user8) — kịch bản FR-008."""
    return conftest.FakeUserDaoBus(
        users={
            "admin1": _user(1, 1, "admin1", "ADMIN"),
            "manager1": _user(8, 2, "manager1", "Quản Lý"),
        },
        thong_tin={
            1: _thong_tin(1, 1, ten="ADMIN"),
            8: _thong_tin(8, 2, ten="Quản Lý"),
        },
    )

def test_admin_khoa_quan_ly_dang_nhap_khong_duoc(client, app_voi_dao):
    """015 FR-008: chỉ Admin ghi trạng thái Quản lý — khóa khiến Quản lý không
    đăng nhập được; sau đó mở khóa thì đăng nhập lại được."""
    user_dao = _tao_dao_admin_quan_ly()
    _gan_dao(app_voi_dao, user_dao)

    _login(client, "admin1")
    resp = client.put("/api/users/8/status", json={"status": "banned"})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] is True
    assert body["message"] == "Đã khóa tài khoản!"

    # Quản lý bị khóa → đăng nhập đúng mật khẩu vẫn thất bại
    assert _login(client, "manager1")["status"] is False

    # Admin mở khóa → đăng nhập lại được
    resp = client.put("/api/users/8/status", json={"status": "active"})
    assert resp.get_json()["status"] is True
    assert _login(client, "manager1")["status"] is True

def test_quan_ly_actor_khong_khoa_duoc_quan_ly(client, app_voi_dao):
    """015 FR-009(1): Quản lý tác động lên Quản lý khác bị chặn — không khóa luôn."""
    user_dao = _tao_dao_admin_quan_ly()
    user_dao.thong_tin[7] = _thong_tin(7, 2, ten="Quản Lý Khác")
    _gan_dao(app_voi_dao, user_dao)
    _login(client, "manager1")

    resp = client.put("/api/users/1/status", json={"status": "banned"})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] is False
    assert body["message"] == "Không ai có quyền khóa tài khoản Admin!"

    # Quản lý muốn khóa Quản lý khác (user7): không được, kể cả khi muốn khoá
    resp = client.put("/api/users/7/status", json={"status": "banned"})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] is False
    assert body["message"] == "Không thể khóa tài khoản Quản lý!"


def test_tu_khoa_ban_than_bi_tu_choi(client, app_voi_dao):
    user_dao = _tao_user_dao()
    _gan_dao(app_voi_dao, user_dao)
    _login(client, "manager1")

    resp = client.put("/api/users/8/status", json={"status": "banned"})
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Bạn không thể khóa/mở khóa chính tài khoản của mình!"