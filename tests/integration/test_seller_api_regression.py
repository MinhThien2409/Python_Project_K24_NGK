"""Regression test seller API sau tái cấu trúc giao diện — 010 (test-first).

T007 (US2): GET/PUT /api/seller/trang-shop giữ nguyên hành vi — hợp lệ thành
            công; tên trống/trùng/thâm niên sai → từ chối tiếng Việt.
T013 (US3): PUT /api/seller/san-pham/<id>/gia giữ nguyên hành vi — hợp lệ
            thành công; giá không hợp lệ → từ chối.

Fake DAO in-memory — KHÔNG chạm PobbyDB thật (giữ nguyên luồng BUS).
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
        3: {"UserId": 3, "FullName": "Seller A", "Role_Id": 3, "trang_thai": "active"},
        4: {"UserId": 4, "FullName": "Seller B", "Role_Id": 3, "trang_thai": "active"},
    }
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"sellerA": "123456", "sellerB": "123456"})
    sp_store = FakeSanPhamStore(
        san_pham={
            1: {"id": 1, "name": "SP A", "price": 100000, "quantity": 5,
                "store_id": 10, "category_id": 1, "is_active": True},
            2: {"id": 2, "name": "SP B", "price": 200000, "quantity": 3,
                "store_id": 20, "category_id": 1, "is_active": True},
        },
        categories={1: "Hoa"})
    shop_store = FakeShopStore(stores={
        10: {"StoreId": 10, "UserId": 3, "StoreName": "Shop A",
             "Description": "Gioi thieu A", "ThamNien": 3},
        20: {"StoreId": 20, "UserId": 4, "StoreName": "Shop B"},
    })
    client = seller_client(user_dao=user_dao, san_pham_store=sp_store,
                           shop_store=shop_store)
    return client, sp_store, shop_store


def _login(client, uid):
    with client.session_transaction() as s:
        s["user_id"] = uid


# ── T007: /api/seller/trang-shop giữ nguyên hành vi ──
def test_trang_shop_get_hop_le(seller_client):
    client, _, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.get("/api/seller/trang-shop")
    assert r.json["status"] is True
    assert r.json["data"]["store_name"] == "Shop A"
    assert r.json["data"]["store_id"] == 10


def test_trang_shop_put_hop_le(seller_client):
    client, _, shop = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/trang-shop", json={
        "ten_shop": "Shop A Moi", "gioi_thieu": "Hay nhat", "tham_nien": 5})
    assert r.json["status"] is True
    assert "thành công" in r.json["message"]
    assert shop.stores[10]["StoreName"] == "Shop A Moi"
    assert shop.stores[10]["ThamNien"] == 5


def test_trang_shop_ten_trong_bi_tu_choi(seller_client):
    client, _, shop = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/trang-shop", json={
        "ten_shop": "   ", "gioi_thieu": "x", "tham_nien": 1})
    assert r.json["status"] is False
    assert r.json["message"] == "Tên shop không được để trống!"
    assert shop.stores[10]["StoreName"] == "Shop A"


def test_trang_shop_ten_trung_bi_tu_choi(seller_client):
    client, _, shop = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/trang-shop", json={
        "ten_shop": "Shop B", "gioi_thieu": "x", "tham_nien": 1})
    assert r.json["status"] is False
    assert "đã có người sử dụng" in r.json["message"]
    assert shop.stores[10]["StoreName"] == "Shop A"


def test_trang_shop_tham_nien_sai_bi_tu_choi(seller_client):
    client, _, shop = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/trang-shop", json={
        "ten_shop": "Shop A", "gioi_thieu": "x", "tham_nien": 150})
    assert r.json["status"] is False
    assert "0 đến 100" in r.json["message"]
    assert shop.stores[10]["ThamNien"] == 3


# ── T013: PUT /api/seller/san-pham/<id>/gia giữ nguyên hành vi ──
def test_doi_gia_hop_le(seller_client):
    client, sp, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/san-pham/1/gia", json={"gia_moi": 80000})
    assert r.json["status"] is True
    assert sp.san_pham[1]["price"] == 80000
    assert sp.san_pham[1]["old_price"] == 100000


def test_doi_gia_khong_hop_le_bi_tu_choi(seller_client):
    client, sp, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/san-pham/1/gia", json={"gia_moi": 0})
    assert r.json["status"] is False
    assert "lớn hơn 0" in r.json["message"]
    assert sp.san_pham[1]["price"] == 100000


def test_doi_gia_shop_khac_bi_tu_choi(seller_client):
    client, sp, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/san-pham/2/gia", json={"gia_moi": 50000})
    assert r.json["status"] is False
    assert "quyền" in r.json["message"]
    assert sp.san_pham[2]["price"] == 200000


def test_chua_login_403(seller_client):
    client, _, _ = _dung_cu(seller_client)
    r = client.get("/api/seller/trang-shop")
    assert r.status_code == 403
    assert r.json["status"] is False