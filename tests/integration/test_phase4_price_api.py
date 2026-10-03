"""Integration Phase 4 — price API (discount on/off, tampering, ownership).

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
    }
    thong_tin = {3: {"UserId": 3, "FullName": "Seller A", "Role_Id": 3,
                     "trang_thai": "active"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"sellerA": "123456"})
    sp_store = FakeSanPhamStore(
        san_pham={
            1: {"id": 1, "name": "Ao", "price": 100000, "old_price": None,
                "quantity": 5, "store_id": 10, "category_id": 1,
                "is_active": True},
            9: {"id": 9, "name": "Shop Khac", "price": 1, "old_price": None,
                "quantity": 1, "store_id": 20, "category_id": 1,
                "is_active": True},
        },
        categories={1: "Thoi trang"})
    shop_store = FakeShopStore(stores={
        10: {"StoreId": 10, "UserId": 3, "StoreName": "Shop A"},
    })
    client = seller_client(user_dao=user_dao, san_pham_store=sp_store,
                           shop_store=shop_store)
    return client, sp_store


def _login(client):
    with client.session_transaction() as s:
        s["user_id"] = 3


def test_bat_giam_gia_ok(seller_client):
    client, sp_store = _dung_cu(seller_client)
    _login(client)
    r = client.put("/api/seller/san-pham/1/gia",
                   json={"gia_goc": 100000, "gia_khuyen_mai": 80000,
                         "giam_gia": True})
    assert r.json["status"] is True
    assert r.json["data"]["discount_percent"] == 20.0
    assert sp_store.san_pham[1]["price"] == 80000
    assert sp_store.san_pham[1]["old_price"] == 100000


def test_gia_km_bang_goc_bi_tu_choi(seller_client):
    client, sp_store = _dung_cu(seller_client)
    _login(client)
    r = client.put("/api/seller/san-pham/1/gia",
                   json={"gia_goc": 100000, "gia_khuyen_mai": 100000,
                         "giam_gia": True})
    assert r.json["status"] is False
    assert sp_store.san_pham[1]["old_price"] is None


def test_tat_giam_gia_khong_active_km(seller_client):
    client, sp_store = _dung_cu(seller_client)
    _login(client)
    sp_store.san_pham[1]["old_price"] = 100000
    sp_store.san_pham[1]["price"] = 80000
    r = client.put("/api/seller/san-pham/1/gia",
                   json={"gia_goc": 100000, "gia_khuyen_mai": 1,
                         "giam_gia": False, "discount_percent": 99})
    assert r.json["status"] is True
    assert sp_store.san_pham[1]["price"] == 100000
    assert sp_store.san_pham[1]["old_price"] is None
    assert "discount_percent" not in r.json["data"]


def test_legacy_gia_moi_van_chay(seller_client):
    client, sp_store = _dung_cu(seller_client)
    _login(client)
    r = client.put("/api/seller/san-pham/1/gia", json={"gia_moi": 80000})
    assert r.json["status"] is True
    assert sp_store.san_pham[1]["price"] == 80000


def test_doi_gia_shop_khac_bi_tu_choi(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client)
    r = client.put("/api/seller/san-pham/9/gia",
                   json={"gia_goc": 100000, "gia_khuyen_mai": 80000,
                         "giam_gia": True})
    assert r.json["status"] is False
