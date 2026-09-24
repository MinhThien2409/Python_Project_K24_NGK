"""Integration test seller san-pham API — US1 + US3 (T012/T033).

CRUD cheo shop + 403 vai tro; nhap +10; doi gia hien thi.
Fake DAO in-memory — KHONG cham PobbyDB that.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.Model.User import User
from tests.conftest import FakeUserDaoBus, FakeSanPhamStore, FakeShopStore


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
    sp_store = FakeSanPhamStore(
        san_pham={
            1: {"id": 1, "name": "SP A", "price": 100000, "quantity": 5,
                "store_id": 10, "category_id": 1, "is_active": True},
            2: {"id": 2, "name": "SP B", "price": 200000, "quantity": 3,
                "store_id": 20, "category_id": 1, "is_active": True},
        },
        categories={1: "Hoa"})
    shop_store = FakeShopStore(stores={
        10: {"StoreId": 10, "UserId": 3, "StoreName": "Shop A"},
        20: {"StoreId": 20, "UserId": 4, "StoreName": "Shop B"},
    })
    client = seller_client(user_dao=user_dao, san_pham_store=sp_store,
                           shop_store=shop_store)
    return client, sp_store


def _login(client, uid):
    with client.session_transaction() as s:
        s["user_id"] = uid


def test_seller_sua_sp_shop_khac_bi_tu_choi(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 3)  # Seller A (store 10) sua SP cua store 20
    r = client.put("/api/seller/san-pham/2", json={"name": "Hack", "price": 1,
                                                   "quantity": 1, "category_id": 1})
    assert r.json["status"] is False
    assert "quyền" in r.json["message"]


def test_customer_goi_api_seller_403(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 5)  # Customer
    r = client.get("/api/seller/san-pham")
    assert r.status_code == 403
    assert r.json["status"] is False


def test_chua_login_403(seller_client):
    client, _ = _dung_cu(seller_client)
    r = client.get("/api/seller/san-pham")
    assert r.status_code == 403


def test_crud_seller_ok(seller_client):
    client, sp = _dung_cu(seller_client)
    _login(client, 3)
    r = client.post("/api/seller/san-pham",
                    json={"name": "SP moi", "price": 50000,
                          "quantity": 2, "category_id": 1})
    assert r.json["status"] is True
    pid = r.json["product_id"]
    r2 = client.put(f"/api/seller/san-pham/{pid}",
                    json={"name": "SP moi 2", "price": 60000,
                          "quantity": 2, "category_id": 1})
    assert r2.json["status"] is True
    r3 = client.put(f"/api/seller/san-pham/{pid}/an-hien", json={"is_active": 0})
    assert r3.json["status"] is True
    assert sp.san_pham[pid]["is_active"] is False


def test_nhap_hang_cong_don(seller_client):
    client, sp = _dung_cu(seller_client)
    _login(client, 3)
    r = client.post("/api/seller/san-pham/1/nhap-hang", json={"so_luong": 10})
    assert r.json["status"] is True
    assert sp.san_pham[1]["quantity"] == 15


def test_nhap_hang_shop_khac_bi_tu_choi(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.post("/api/seller/san-pham/2/nhap-hang", json={"so_luong": 10})
    assert r.json["status"] is False


def test_doi_gia_ok(seller_client):
    client, sp = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/san-pham/1/gia", json={"gia_moi": 80000})
    assert r.json["status"] is True
    assert sp.san_pham[1]["price"] == 80000
    assert sp.san_pham[1].get("old_price") == 100000


def test_doi_gia_0_bi_tu_choi(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/san-pham/1/gia", json={"gia_moi": 0})
    assert r.json["status"] is False
