# -*- coding: utf-8 -*-
"""Integration test đăng xuất 3 vai trò giao diện quản trị (016 US1, T005–T006).

- AP-1/T005: Admin, Quản lý, Seller → POST /api/dang-xuat → 200
  {"status":true,"message":"Đã đăng xuất."} → /api/phien hết phiên → endpoint
  quyền của vai trò đó bị 403 (Admin/Quản lý: /api/users; Seller: /api/phien).
- AP-2/T006: logout khi chưa đăng nhập → vẫn 200 không crash; logout 2 lần liên
  tiếp → idempotent an toàn.

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


NHA_MANG = {
    "admin":    (1, 1, "Admin"),
    "quanly1":  (2, 2, "Quản Lý"),
    "seller1":  (3, 3, "Seller 1"),
    "khach1":   (9, 4, "Khách Hàng"),
}


def _dao_day_du():
    """FakeUserDaoBus đủ 4 vai trò (Admin/Quản lý/Seller/Customer)."""
    return conftest.FakeUserDaoBus(
        users={u: _user(*utt) for u, utt in NHA_MANG.items()},
        thong_tin={ma: _thong_tin(ma, role, ten=ten)
                   for u, (ma, role, ten) in NHA_MANG.items()},
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


def _dang_nhap(client, username):
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": username, "mat_khau": "123456"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] is True
    return resp.get_json()


# ── T005: đăng xuất 3 vai trò giao diện quản trị ──
@pytest.mark.parametrize("username,ma_user,role_id", [
    ("admin", 1, 1),      # Admin
    ("quanly1", 2, 2),    # Quản lý
    ("seller1", 3, 3),    # Seller
])
def test_dang_xuat_3_vai_tro_ve_het_phien(client, gan_dao, username, ma_user, role_id):
    gan_dao(_dao_day_du())
    _dang_nhap(client, username)

    # Phiên đang tồn tại trước khi logout
    resp = client.get("/api/phien")
    assert resp.get_json()["status"] is True
    assert resp.get_json()["data"]["ma_user"] == ma_user

    # POST /api/dang-xuat → 200, thông điệp chuẩn
    resp = client.post("/api/dang-xuat")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": True, "message": "Đã đăng xuất."}

    # Phiên đã bị xóa
    resp = client.get("/api/phien")
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Bạn chưa đăng nhập!"
    assert body["data"] is None

    # Endpoint quyền Admin/Quản lý bị chặn sau logout
    if role_id in (1, 2):
        resp = client.get("/api/users")
        assert resp.status_code == 403


def test_dang_xuat_seller_bi_chặn_truoc_va_sau_logout_phien_ro(client, gan_dao):
    """Seller không có quyền /api/users — chứng minh qua /api/phien hết phiên."""
    gan_dao(_dao_day_du())
    _dang_nhap(client, "seller1")

    resp = client.post("/api/dang-xuat")
    assert resp.status_code == 200

    resp = client.get("/api/phien")
    body = resp.get_json()
    assert body["status"] is False
    assert body["data"] is None


# ── T006: ca biên — chưa đăng nhập / logout 2 lần ──
def test_dang_xuat_khi_chua_dang_nhap_van_200_khong_crash(client, gan_dao):
    gan_dao(_dao_day_du())
    resp = client.post("/api/dang-xuat")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": True, "message": "Đã đăng xuất."}
    # Phiên vẫn "chưa đăng nhập" sau hành động an toàn
    assert client.get("/api/phien").get_json()["status"] is False


def test_dang_xuat_hai_lan_lien_tiep_idempotent(client, gan_dao):
    gan_dao(_dao_day_du())
    _dang_nhap(client, "quanly1")

    for _ in range(2):
        resp = client.post("/api/dang-xuat")
        assert resp.status_code == 200
        assert resp.get_json() == {"status": True, "message": "Đã đăng xuất."}

    assert client.get("/api/phien").get_json()["status"] is False


def test_dang_nhap_lai_sau_logout_duoc_3_vai_tro(client, gan_dao):
    """Đăng xuất rồi đăng nhập lại (vai trò khác) vẫn thành công — phiên mới."""
    gan_dao(_dao_day_du())
    _dang_nhap(client, "admin")
    client.post("/api/dang-xuat")

    _dang_nhap(client, "seller1")
    resp = client.get("/api/phien")
    assert resp.get_json()["status"] is True
    assert resp.get_json()["data"]["ma_user"] == 3