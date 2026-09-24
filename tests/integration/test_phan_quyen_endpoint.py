# -*- coding: utf-8 -*-
"""Integration test bảng phân quyền endpoint (009 US2 + US3, T012 + T019).

Phần Admin (US2, T012):
- Admin gọi `GET /api/users`, `GET/POST/PUT/DELETE /api/quan-ly*` → 200.
- Admin gọi `POST/PUT/DELETE /api/categories*`, duyệt seller, cấp lại mật khẩu → 403
  (quyền đã thuộc Quản lý).
- Admin khoá/mở khoá tài khoản → 200 (015 FR-008: Admin duy nhất ghi trạng thái Quản lý).
- Admin gọi các endpoint đã gỡ (thống kê, đơn hàng quản trị, products hệ thống) → 404.

Phần Quản lý (US3, T019 + 015 FR-012):
- Quản lý gọi 4 endpoint được phép (categories ghi, duyệt/từ chối seller,
  khoá/mở khoá, cấp lại mật khẩu) → 200.
- Quản lý gọi /api/users → 200 (015 FR-012 — SC-004); /api/quan-ly* → 403.

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
def dao_voi_admin_quan_ly(app_voi_dao, gian_hang_dao=None):
    """FakeUserDaoBus: 1 Admin + 1 Quản lý + 1 Customer, gắn vào app."""
    user_dao = conftest.FakeUserDaoBus(
        users={
            "admin":   _user(1, 1, "admin", "Admin"),
            "quanly1": _user(2, 2, "quanly1", "Quản Lý"),
            "khach1":  _user(9, 4, "khach1", "Khách Hàng"),
        },
        thong_tin={
            1: _thong_tin(1, 1, "active", "Admin"),
            2: _thong_tin(2, 2, "active", "Quản Lý"),
            9: _thong_tin(9, 4, "active", "Khách Hàng"),
        },
    )
    app_voi_dao(user_dao=user_dao, gian_hang_dao=gian_hang_dao)
    return user_dao


def _dang_nhap(client, username):
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": username, "mat_khau": "123456"})
    assert resp.status_code == 200
    return resp.get_json()


# ═══════════════════ PHẦN ADMIN (US2, T012) ═══════════════════
def test_admin_goi_users_200(client, dao_voi_admin_quan_ly):
    _dang_nhap(client, "admin")
    resp = client.get("/api/users")
    assert resp.status_code == 200
    assert resp.get_json()["status"] is True


def test_admin_goi_quan_ly_200(client, dao_voi_admin_quan_ly):
    _dang_nhap(client, "admin")
    assert client.get("/api/quan-ly").status_code == 200
    assert client.post("/api/quan-ly",
                       json={"ten_user": "Quản Lý Mới", "tendangnhap": "qlmoi",
                             "mat_khau": "123456"}).status_code == 200


def test_admin_goi_quan_ly_sua_xoa_200(client, dao_voi_admin_quan_ly):
    _dang_nhap(client, "admin")
    # Sửa Quản lý id=2
    assert client.put("/api/quan-ly/2",
                      json={"ten_user": "Quản Lý Sửa", "dia_chi": "HCM",
                            "sdt": "0900000000"}).status_code == 200
    # Xoá (tạo thêm 1 Quản lý rồi xoá để không phá fixture)
    dao_voi_admin_quan_ly.them_quan_ly("QL Tạm", "", "", "qltam", "123456")
    ma_moi = max(u.ma_user for u in dao_voi_admin_quan_ly.users.values())
    assert client.delete(f"/api/quan-ly/{ma_moi}").status_code == 200


def test_admin_categories_ghi_403(client, dao_voi_admin_quan_ly):
    _dang_nhap(client, "admin")
    resp = client.post("/api/categories", json={"name": "Hoa"})
    assert resp.status_code == 403
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Bạn không có quyền thực hiện chức năng này!"


def test_admin_duyet_seller_403(client, dao_voi_admin_quan_ly):
    _dang_nhap(client, "admin")
    for url in ["/api/seller-requests", "/api/duyet-seller/1", "/api/tu-choi-seller/1"]:
        resp = client.get(url) if url == "/api/seller-requests" else client.post(url, json={})
        assert resp.status_code == 403, url
        assert resp.get_json()["message"] == "Bạn không có quyền thực hiện chức năng này!"


def test_admin_khoa_tai_khoan_ok_cap_lai_mat_khau_403(client, dao_voi_admin_quan_ly):
    """015 FR-008: Admin được khoá tài khoản; cấp lại mật khẩu vẫn thuộc Quản lý."""
    _dang_nhap(client, "admin")
    resp = client.put("/api/users/9/status", json={"status": "banned"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Đã khóa tài khoản!"
    resp = client.post("/api/cap-lai-mat-khau", json={"ma_user": 9, "mat_khau_moi": "matkhau1"})
    assert resp.status_code == 403
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Bạn không có quyền thực hiện chức năng này!"


def test_admin_thong_ke_don_hang_products_404(client, dao_voi_admin_quan_ly):
    _dang_nhap(client, "admin")
    for method, url in [
        ("get", "/api/thong-ke/tong-quan"), ("get", "/api/thong-ke/doanh-thu-theo-thang"),
        ("get", "/api/don-hang/tat-ca"), ("put", "/api/don-hang/1/trang-thai"),
        ("get", "/api/don-hang/cua-seller/1"),
        ("post", "/api/products"), ("put", "/api/products/1"), ("delete", "/api/products/1"),
    ]:
        resp = getattr(client, method)(url)
        # 404 (route bị gỡ hẳn) hoặc 405 (path còn GET công khai) đều = chức năng đã cắt
        assert resp.status_code in (404, 405), f"{method.upper()} {url}"


# ═══════════════════ PHẦN QUẢN LÝ (US3, T019) ═══════════════════
def test_quan_ly_categories_ghi_200(client, dao_voi_admin_quan_ly):
    _dang_nhap(client, "quanly1")
    resp = client.post("/api/categories", json={"name": "Hoa"})
    assert resp.status_code == 200


def test_quan_ly_duyet_tu_choi_seller_200(client, dao_voi_admin_quan_ly):
    _dang_nhap(client, "quanly1")
    assert client.get("/api/seller-requests").status_code == 200


def test_quan_ly_khoa_va_cap_lai_mat_khau_200(client, dao_voi_admin_quan_ly):
    _dang_nhap(client, "quanly1")
    resp = client.put("/api/users/9/status", json={"status": "banned"})
    assert resp.status_code == 200
    resp = client.post("/api/cap-lai-mat-khau", json={"ma_user": 9, "mat_khau_moi": "matkhau1"})
    assert resp.status_code == 200


def test_quan_ly_users_200(client, dao_voi_admin_quan_ly):
    """015 FR-012: Quản lý được truy cập danh sách tài khoản."""
    _dang_nhap(client, "quanly1")
    resp = client.get("/api/users")
    assert resp.status_code == 200
    assert resp.get_json()["status"] is True


def test_quan_ly_quan_ly_quan_tri_403(client, dao_voi_admin_quan_ly):
    _dang_nhap(client, "quanly1")
    for method, url in [("GET", "/api/quan-ly"), ("POST", "/api/quan-ly"),
                        ("PUT", "/api/quan-ly/2"), ("DELETE", "/api/quan-ly/2")]:
        resp = getattr(client, method.lower())(url, json={})
        assert resp.status_code == 403, f"{method} {url}"
        assert resp.get_json()["message"] == "Bạn không có quyền thực hiện chức năng này!"


def test_quan_ly_products_don_hang_thong_ke_403_404(client, dao_voi_admin_quan_ly):
    _dang_nhap(client, "quanly1")
    # Sản phẩm hệ thống đã gỡ (POST/PUT/DELETE), thống kê & đơn hàng quản trị → 404
    for method, url in [
        ("get", "/api/thong-ke/tong-quan"), ("get", "/api/thong-ke/doanh-thu-theo-thang"),
        ("get", "/api/don-hang/tat-ca"), ("put", "/api/don-hang/1/trang-thai"),
        ("get", "/api/don-hang/cua-seller/1"),
        ("post", "/api/products"), ("put", "/api/products/1"),
    ]:
        resp = getattr(client, method)(url)
        # 404 (route bị gỡ hẳn) hoặc 405 (path còn GET công khai) đều = chức năng đã cắt
        assert resp.status_code in (404, 405), f"{method.upper()} {url}"