# -*- coding: utf-8 -*-
"""Regression test US4 (009, T025): Seller/Customer giữ nguyên chức năng.

- Seller dùng đủ /api/seller/* (sản phẩm, đơn hàng, nhập hàng, thống kê,
  trang shop, giá bán) → 200.
- Customer dùng giỏ hàng, đặt đơn, cập nhật hồ sơ → 200.
- Customer gọi API seller / quản lý → 403.

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""

from back_end.Model.User import User
from tests.conftest import FakeUserDaoBus, FakeSanPhamStore, FakeSanPhamTimKiemStore, \
    FakeShopStore, FakeDonHangSellerStore, FakeGioHangStore, FakeDonHangCustomerStore


def _users_va_stores():
    users = {
        "sellerA": User(ma_user=3, ma_nhom_quyen=3, ten_user="Seller A",
                        sdt="0901", dia_chi="HN", cmnd="1",
                        tendangnhap="sellerA", mat_khau="123456"),
        "customer": User(ma_user=5, ma_nhom_quyen=4, ten_user="Khach",
                         sdt="0903", dia_chi="HN", cmnd="3",
                         tendangnhap="customer", mat_khau="123456"),
    }
    thong_tin = {
        3: {"UserId": 3, "FullName": "Seller A", "Role_Id": 3, "trang_thai": "active"},
        5: {"UserId": 5, "FullName": "Khach", "Role_Id": 4, "trang_thai": "active"},
    }
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"sellerA": "123456", "customer": "123456"})
    sp_store = FakeSanPhamStore(
        san_pham={1: {"id": 1, "name": "SP A", "price": 100000, "quantity": 10,
                      "store_id": 10, "category_id": 1, "is_active": True}},
        categories={1: "Hoa"})
    shop_store = FakeShopStore(stores={
        10: {"StoreId": 10, "UserId": 3, "StoreName": "Shop A"}})
    return user_dao, sp_store, shop_store


def _login(client, uid):
    with client.session_transaction() as s:
        s["user_id"] = uid


# ═══════════════ SELLER: đủ 6 nhóm chức năng /api/seller/* (FR-008) ═══════════════
def test_seller_san_pham_day_du(seller_client):
    user_dao, sp_store, shop_store = _users_va_stores()
    client = seller_client(user_dao=user_dao, san_pham_store=sp_store, shop_store=shop_store)
    _login(client, 3)

    assert client.get("/api/seller/san-pham").status_code == 200

    r = client.post("/api/seller/san-pham", json={
        "name": "SP Moi", "description": "", "price": 50000, "quantity": 5,
        "category_id": 1})
    assert r.status_code == 200
    assert r.get_json()["status"] is True
    ma_moi = r.get_json()["product_id"]

    assert client.put(f"/api/seller/san-pham/{ma_moi}",
                      json={"name": "SP Moi 2", "price": 60000, "quantity": 6}).status_code == 200
    assert client.put(f"/api/seller/san-pham/{ma_moi}/an-hien",
                      json={"is_active": 0}).status_code == 200
    assert client.post(f"/api/seller/san-pham/{ma_moi}/nhap-hang",
                       json={"so_luong": 10}).status_code == 200
    assert client.put(f"/api/seller/san-pham/{ma_moi}/gia",
                      json={"gia_moi": 55000}).status_code == 200


def test_seller_don_hang_va_trang_thai(seller_client):
    user_dao, sp_store, shop_store = _users_va_stores()
    don_store = FakeDonHangSellerStore(
        don_hang={1: {"OrderId": 1, "Status": "Pending", "TotalAmount": 100000}},
        thuoc={1: {10}})
    client = seller_client(user_dao=user_dao, san_pham_store=sp_store,
                           shop_store=shop_store, don_hang_store=don_store)
    _login(client, 3)

    assert client.get("/api/seller/don-hang").status_code == 200
    r = client.put("/api/seller/don-hang/1/trang-thai", json={"status": "Confirmed"})
    assert r.status_code == 200
    assert don_store.don_hang[1]["Status"] == "Confirmed"


def test_seller_thong_ke_va_trang_shop(seller_client):
    user_dao, sp_store, shop_store = _users_va_stores()
    don_store = FakeDonHangSellerStore(
        don_hang={1: {"OrderId": 1, "Status": "Completed", "TotalAmount": 100000}},
        thuoc={1: {10}})
    client = seller_client(user_dao=user_dao, san_pham_store=sp_store,
                           shop_store=shop_store, don_hang_store=don_store)
    _login(client, 3)

    assert client.get("/api/seller/thong-ke/tong-quan").status_code == 200
    assert client.get("/api/seller/thong-ke/doanh-thu-theo-thang").status_code == 200
    assert client.get("/api/seller/trang-shop").status_code == 200
    r = client.put("/api/seller/trang-shop",
                   json={"ten_shop": "Shop A Moi", "gioi_thieu": "Hay", "tham_nien": 2})
    assert r.status_code == 200


# ═══════════════ CUSTOMER: giỏ hàng + đặt đơn + hồ sơ (FR-009) ═══════════════
def test_customer_gio_hang_dat_don_ho_so(customer_client):
    user_dao, sp_store, shop_store = _users_va_stores()
    # FakeSanPhamTimKiemStore (integration) cung cap lay_thong_tin_kho cho GioHangBus
    sp_tim = FakeSanPhamTimKiemStore(
        san_pham={1: {**dict(sp_store.san_pham[1]), "emoji": "🌸"}})
    gio_store = FakeGioHangStore(san_pham=sp_store.san_pham)
    don_store = FakeDonHangCustomerStore(san_pham=sp_store.san_pham)
    client = customer_client(user_dao=user_dao, san_pham_store=sp_tim,
                             gio_hang_store=gio_store, don_hang_store=don_store)
    _login(client, 5)

    # Giỏ hàng: thêm + xem
    r = client.post("/api/gio-hang/them",
                    json={"ProductId": 1, "Quantity": 2, "UnitPrice": 100000})
    assert r.status_code == 200
    assert r.get_json()["status"] is True
    assert client.get("/api/gio-hang/5").status_code == 200

    # Đặt đơn
    r = client.post("/api/don-hang/dat-hang", json={
        "ReceiverName": "Khach", "ReceiverPhone": "0903123456",
        "ShippingAddress": "HN", "PaymentMethod": "COD",
        "SubTotal": 200000, "ShippingFee": 25000, "TotalAmount": 225000,
        "Items": [{"ProductId": 1, "ProductName": "SP A", "Quantity": 2,
                   "UnitPrice": 100000}]})
    assert r.status_code == 200
    assert r.get_json()["status"] is True, r.get_json()

    # Cập nhật hồ sơ
    r = client.post("/api/cap-nhat-profile",
                    json={"ten_user": "Khach Moi", "sdt": "0904123456",
                          "dia_chi": "HCM", "cmnd": "3"})
    assert r.status_code == 200

    # Xem đơn của mình
    assert client.get("/api/don-hang/cua-toi/5").status_code == 200


# ═══════════════ CUSTOMER gọi API vai trò khác → 403 (FR-010) ═══════════════
def test_customer_goi_api_seller_quan_ly_403(seller_client):
    user_dao, sp_store, shop_store = _users_va_stores()
    client = seller_client(user_dao=user_dao, san_pham_store=sp_store, shop_store=shop_store)
    _login(client, 5)  # Customer

    for url in ["/api/seller/san-pham", "/api/seller/don-hang",
                "/api/seller/thong-ke/tong-quan", "/api/seller/trang-shop"]:
        assert client.get(url).status_code == 403, url

    assert client.post("/api/duyet-seller/1", json={}).status_code == 403
    assert client.put("/api/users/9/status", json={"status": "banned"}).status_code == 403
    assert client.post("/api/cap-lai-mat-khau",
                       json={"ma_user": 3, "mat_khau_moi": "123"}).status_code == 403
    assert client.get("/api/quan-ly").status_code == 403
    assert client.get("/api/users").status_code == 403