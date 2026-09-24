"""Integration test seller thong-ke + trang-shop API — US4+US5 (T041/T049).

TK khop seed + co lap 2 shop; sua shop customer thay + 403.
Fake DAO in-memory — KHONG cham PobbyDB that.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.Model.User import User
from tests.conftest import FakeUserDaoBus, FakeDonHangSellerStore, FakeShopStore


def _dung_cu(seller_client):
    users = {
        "sellerA": User(ma_user=3, ma_nhom_quyen=3, ten_user="Seller A",
                        sdt="0901", dia_chi="HN", cmnd="1",
                        tendangnhap="sellerA", mat_khau="123456"),
        "sellerB": User(ma_user=4, ma_nhom_quyen=3, ten_user="Seller B",
                        sdt="0902", dia_chi="HN", cmnd="2",
                        tendangnhap="sellerB", mat_khau="123456"),
        "customer": User(ma_user=5, ma_nhom_quyen=4, ten_user="Khach",
                         sdt="0903", dia_chi="HN", cmnd="3",
                         tendangnhap="customer", mat_khau="123456"),
    }
    thong_tin = {
        3: {"UserId": 3, "FullName": "Seller A", "Role_Id": 3, "trang_thai": "active"},
        4: {"UserId": 4, "FullName": "Seller B", "Role_Id": 3, "trang_thai": "active"},
        5: {"UserId": 5, "FullName": "Khach", "Role_Id": 4, "trang_thai": "active"},
    }
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"sellerA": "123456", "sellerB": "123456",
                                        "customer": "123456"})
    don_store = FakeDonHangSellerStore(
        don_hang={
            1: {"OrderId": 1, "Status": "Completed", "TotalAmount": 200000},
            2: {"OrderId": 2, "Status": "Pending", "TotalAmount": 100000},
        },
        thuoc={1: {10}, 2: {20}})
    shop_store = FakeShopStore(stores={
        10: {"StoreId": 10, "UserId": 3, "StoreName": "Shop A",
             "Description": "Mo ta A", "ThamNien": 3},
        20: {"StoreId": 20, "UserId": 4, "StoreName": "Shop B",
             "Description": "Mo ta B", "ThamNien": 1},
    })
    client = seller_client(user_dao=user_dao, don_hang_store=don_store,
                           shop_store=shop_store)
    return client, don_store, shop_store


def _login(client, uid):
    with client.session_transaction() as s:
        s["user_id"] = uid


def test_tong_quan_chi_shop_minh(seller_client):
    client, _, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.get("/api/seller/thong-ke/tong-quan")
    assert r.json["status"] is True
    assert r.json["data"]["tong_don"] == 1
    assert r.json["data"]["doanh_thu"] == 200000


def test_doanh_thu_theo_thang_du_12(seller_client):
    client, _, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.get("/api/seller/thong-ke/doanh-thu-theo-thang?year=2026")
    assert r.json["status"] is True
    assert len(r.json["data"]) == 12


def test_seller_b_khong_thay_shop_a(seller_client):
    client, _, _ = _dung_cu(seller_client)
    _login(client, 4)
    r = client.get("/api/seller/thong-ke/tong-quan")
    assert r.json["data"]["tong_don"] == 1
    assert r.json["data"]["doanh_thu"] == 100000


def test_sua_shop_ok(seller_client):
    client, _, shop = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/trang-shop",
                   json={"ten_shop": "Shop A Moi", "gioi_thieu": "Moi", "tham_nien": 5})
    assert r.json["status"] is True
    assert shop.stores[10]["StoreName"] == "Shop A Moi"


def test_sua_shop_trung_ten_bi_tu_choi(seller_client):
    client, _, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/trang-shop", json={"ten_shop": "Shop B"})
    assert r.json["status"] is False


def test_customer_sua_shop_403(seller_client):
    client, _, _ = _dung_cu(seller_client)
    _login(client, 5)
    r = client.put("/api/seller/trang-shop", json={"ten_shop": "Hack"})
    assert r.status_code == 403


def test_xem_trang_shop(seller_client):
    client, _, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.get("/api/seller/trang-shop")
    assert r.json["status"] is True
    assert r.json["data"]["store_name"] == "Shop A"
