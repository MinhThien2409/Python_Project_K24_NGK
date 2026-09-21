# -*- coding: utf-8 -*-
"""Unit test phân quyền Admin/Quản lý (009 US2 + US3, T011 + T018).

US2 (T011):
- Gate `kiem_tra_quyen_xem_danh_sach` Admin|Quản lý (015 FR-012): Admin qua,
  Quản lý qua, Customer/Seller chặn, banned chặn, chưa đăng nhập chặn.
- `kiem_tra_quyen_quan_ly` đã thu hẹp: Quản lý qua, Admin chặn.
- Gate mới `kiem_tra_quyen_duyet_seller` Quản lý-only: Quản lý qua, Admin chặn.
- Các chức năng đã cắt không còn tồn tại trong app (route bị gỡ → 404).

Dùng mock DAO + kiểm tra bảng route, KHÔNG chạm PobbyDB thật.
"""

import pytest

import app as app_module
from app import app
from back_end.BUS.UserBus import UserBus

# ── Gate kiem_tra_quyen_xem_danh_sach (Admin | Quản lý — 015 FR-012) ──────
@pytest.fixture
def user_bus(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao()
    return bus


def test_xem_danh_sach_admin_duoc_phep(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(thong_tin={"UserId": 1, "Role_Id": 1, "trang_thai": "active"})
    ket_qua = bus.kiem_tra_quyen_xem_danh_sach(1)
    assert ket_qua["status"] is True
    assert ket_qua["data"]["ten_vai_tro"] == "Admin"


def test_xem_danh_sach_quan_ly_duoc_phep(mock_user_dao):
    """015 FR-012: Quản lý được truy cập danh sách tài khoản."""
    bus = UserBus()
    bus.dao = mock_user_dao(thong_tin={"UserId": 2, "Role_Id": 2, "trang_thai": "active"})
    ket_qua = bus.kiem_tra_quyen_xem_danh_sach(2)
    assert ket_qua["status"] is True
    assert ket_qua["data"]["ten_vai_tro"] == "Quản lý"


@pytest.mark.parametrize("role_id", [3, 4], ids=["seller", "customer"])
def test_xem_danh_sach_vai_tro_thuong_bi_chan(mock_user_dao, role_id):
    bus = UserBus()
    bus.dao = mock_user_dao(thong_tin={"UserId": 8, "Role_Id": role_id, "trang_thai": "active"})
    ket_qua = bus.kiem_tra_quyen_xem_danh_sach(8)
    assert ket_qua["status"] is False


def test_xem_danh_sach_chua_dang_nhap(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao()
    ket_qua = bus.kiem_tra_quyen_xem_danh_sach(None)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Bạn chưa đăng nhập!"


def test_xem_danh_sach_bi_khoa_chan(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(thong_tin={"UserId": 1, "Role_Id": 1, "trang_thai": "banned"})
    ket_qua = bus.kiem_tra_quyen_xem_danh_sach(1)
    assert ket_qua["status"] is False
    assert "khóa" in ket_qua["message"].lower()


# ── kiem_tra_quyen_quan_ly đã thu hẹp còn Quản lý ───────────────────────────
def test_quyen_quan_ly_admin_bi_chan(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(thong_tin={"UserId": 1, "Role_Id": 1, "trang_thai": "active"})
    ket_qua = bus.kiem_tra_quyen_quan_ly(1)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Bạn không có quyền thực hiện chức năng này!"


def test_quyen_quan_ly_quan_ly_duoc_phep(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(thong_tin={"UserId": 2, "Role_Id": 2, "trang_thai": "active"})
    ket_qua = bus.kiem_tra_quyen_quan_ly(2)
    assert ket_qua["status"] is True
    assert ket_qua["data"]["ten_vai_tro"] == "Quản lý"


# ── Gate mới kiem_tra_quyen_duyet_seller (Quản lý-only) ─────────────────────
def test_duyet_seller_quan_ly_duoc_phep(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(thong_tin={"UserId": 2, "Role_Id": 2, "trang_thai": "active"})
    ket_qua = bus.kiem_tra_quyen_duyet_seller(2)
    assert ket_qua["status"] is True
    assert ket_qua["data"]["ten_vai_tro"] == "Quản lý"


def test_duyet_seller_admin_bi_chan(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao(thong_tin={"UserId": 1, "Role_Id": 1, "trang_thai": "active"})
    ket_qua = bus.kiem_tra_quyen_duyet_seller(1)
    assert ket_qua["status"] is False


def test_duyet_seller_chua_dang_nhap(mock_user_dao):
    bus = UserBus()
    bus.dao = mock_user_dao()
    ket_qua = bus.kiem_tra_quyen_duyet_seller(None)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Bạn chưa đăng nhập!"


# ── Các chức năng đã cắt không còn route (→ 404) ─────────────────────────────
CAC_ROUTE_DA_CAT = [
    "add_product",                       # POST /api/products
    "update_product",                    # PUT /api/products/<id>
    "delete_product",                    # DELETE /api/products/<id>
    "api_thong_ke_tong_quan",            # GET /api/thong-ke/tong-quan
    "api_doanh_thu_theo_thang",          # GET /api/thong-ke/doanh-thu-theo-thang
    "api_lay_tat_ca_don_hang",           # GET /api/don-hang/tat-ca
    "api_cap_nhat_trang_thai",           # PUT /api/don-hang/<id>/trang-thai
    "api_lay_don_hang_cua_seller",       # GET /api/don-hang/cua-seller/<id>
]


@pytest.mark.parametrize("endpoint_name", CAC_ROUTE_DA_CAT)
def test_chuc_nang_cat_khong_con_route(endpoint_name):
    assert endpoint_name not in app.view_functions


def test_chuc_nang_cat_tra_404(client_phan_quyen_app):
    for method, url in [
        ("post", "/api/products"),            # POST đã gỡ, GET giữ nguyên (xem sản phẩm)
        ("put", "/api/products/1"),
        ("delete", "/api/products/1"),
        ("get", "/api/thong-ke/tong-quan"),
        ("get", "/api/thong-ke/doanh-thu-theo-thang"),
        ("get", "/api/don-hang/tat-ca"),
        ("put", "/api/don-hang/1/trang-thai"),
        ("get", "/api/don-hang/cua-seller/1"),
    ]:
        resp = getattr(client_phan_quyen_app, method)(url)
        # 404 (route bị gỡ hẳn) hoặc 405 (path còn GET công khai) đều = chức năng đã cắt
        assert resp.status_code in (404, 405), f"{method.upper()} {url}"


@pytest.fixture
def client_phan_quyen_app():
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()