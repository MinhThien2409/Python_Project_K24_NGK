"""Integration Phase 4 — product API (duplicate, autocomplete, tao-va-nhap).

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
    }
    thong_tin = {
        3: {"UserId": 3, "FullName": "Seller A", "Role_Id": 3,
            "trang_thai": "active"},
        4: {"UserId": 4, "FullName": "Seller B", "Role_Id": 3,
            "trang_thai": "active"},
    }
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"sellerA": "123456",
                                        "sellerB": "123456"})
    sp_store = FakeSanPhamStore(
        san_pham={
            1: {"id": 1, "name": "Ao Thun", "price": 100000,
                "old_price": None, "quantity": 5, "store_id": 10,
                "category_id": 1, "is_active": True},
            2: {"id": 2, "name": "Ao Thun", "price": 90000,
                "old_price": None, "quantity": 2, "store_id": 20,
                "category_id": 1, "is_active": True},
        },
        categories={1: "Thoi trang"})
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


def test_them_trung_ten_khac_hoa_thuong_bi_tu_choi(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.post("/api/seller/san-pham",
                    json={"name": "  AO THUN  ", "price": 100000,
                          "quantity": 5, "category_id": 1})
    assert r.json["status"] is False
    assert "tồn tại" in r.json["message"]


def test_them_trung_ten_khac_store_van_ok(seller_client):
    client, sp_store = _dung_cu(seller_client)
    _login(client, 3)
    del sp_store.san_pham[1]  # store 10 chua co "Ao Thun" → duoc them
    r = client.post("/api/seller/san-pham",
                    json={"name": "Ao Thun", "price": 100000,
                          "quantity": 5, "category_id": 1})
    assert r.json["status"] is True


def test_tim_kiem_chi_thay_store_minh(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.get("/api/seller/san-pham/tim-kiem?q=ao")
    assert r.json["status"] is True
    assert {sp["id"] for sp in r.json["data"]} == {1}


def test_tim_kiem_rong_tra_mang_rong(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.get("/api/seller/san-pham/tim-kiem?q=   ")
    assert r.json == {"status": True, "data": []}


def test_tao_va_nhap_tao_moi_va_cong_kho(seller_client):
    client, sp_store = _dung_cu(seller_client)
    _login(client, 3)
    r = client.post("/api/seller/san-pham/tao-va-nhap",
                    json={"name": "Mu Noi Dia", "quantity": 7,
                          "gia_nhap": 20000})
    assert r.json["status"] is True
    nid = r.json["data"]["product_id"]
    assert sp_store.san_pham[nid]["quantity"] == 7
    assert sp_store.san_pham[nid]["store_id"] == 10


def test_tao_va_nhap_trung_ten_bi_tu_choi(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.post("/api/seller/san-pham/tao-va-nhap",
                    json={"name": "ao thun", "quantity": 7})
    assert r.json["status"] is False
