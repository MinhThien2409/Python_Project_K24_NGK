"""Integration Phase 4 — stock bulk API (gop, arithmetic, ownership).

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
            2: {"id": 2, "name": "Quan", "price": 50000, "old_price": None,
                "quantity": 1, "store_id": 10, "category_id": 1,
                "is_active": True},
            9: {"id": 9, "name": "Shop Khac", "price": 1, "old_price": None,
                "quantity": 9, "store_id": 20, "category_id": 1,
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


def test_bulk_ok_va_gop_trung(seller_client):
    client, sp_store = _dung_cu(seller_client)
    _login(client)
    r = client.post("/api/seller/nhap-hang",
                    json={"items": [{"product_id": 1, "quantity": 3},
                                    {"product_name": "quan", "quantity": 2},
                                    {"product_id": 1, "quantity": 2,
                                     "new_stock": 9999}],
                          "ghi_chu": "dot 1"})
    assert r.json["status"] is True
    assert len(r.json["data"]["items"]) == 2
    assert sp_store.san_pham[1]["quantity"] == 5 + 5
    assert sp_store.san_pham[2]["quantity"] == 1 + 2


def test_bulk_so_luong_sai_bi_tu_choi(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client)
    for xau in (0, -1, "abc", "1.5", None, True):
        r = client.post("/api/seller/nhap-hang",
                        json={"items": [{"product_id": 1, "quantity": xau}]})
        assert r.json["status"] is False, xau


def test_bulk_rong_bi_tu_choi(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client)
    assert client.post("/api/seller/nhap-hang",
                       json={"items": []}).json["status"] is False


def test_bulk_chen_sp_shop_khac_bi_tu_choi(seller_client):
    client, sp_store = _dung_cu(seller_client)
    _login(client)
    r = client.post("/api/seller/nhap-hang",
                    json={"items": [{"product_id": 1, "quantity": 1},
                                    {"product_id": 9, "quantity": 1}]})
    assert r.json["status"] is False
    assert sp_store.san_pham[1]["quantity"] == 5  # all-or-nothing giu nguyen
