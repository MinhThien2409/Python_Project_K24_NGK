"""Integration test seller don-hang API — US2 (T025).

Luu don tung buoc + tu choi cheo; 403 vai tro.
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
    don_store = FakeDonHangSellerStore(
        don_hang={
            1: {"OrderId": 1, "Status": "Pending", "TotalAmount": 200000},
            2: {"OrderId": 2, "Status": "Completed", "TotalAmount": 100000},
            9: {"OrderId": 9, "Status": "Pending", "TotalAmount": 50000},
        },
        thuoc={1: {10}, 2: {10}, 9: {20}})
    shop_store = FakeShopStore(stores={
        10: {"StoreId": 10, "UserId": 3, "StoreName": "Shop A"},
    })
    client = seller_client(user_dao=user_dao, don_hang_store=don_store,
                           shop_store=shop_store)
    return client, don_store


def _login(client, uid):
    with client.session_transaction() as s:
        s["user_id"] = uid


def test_list_chi_don_shop_minh(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.get("/api/seller/don-hang")
    assert r.json["status"] is True
    ids = [d["OrderId"] for d in r.json["data"]]
    assert 1 in ids and 2 in ids
    assert 9 not in ids


def test_luong_tung_buoc_ok(seller_client):
    client, store = _dung_cu(seller_client)
    _login(client, 3)
    for moi in ["Confirmed", "Shipping", "Completed"]:
        r = client.put("/api/seller/don-hang/1/trang-thai", json={"status": moi})
        assert r.json["status"] is True, (moi, r.json)
    assert store.don_hang[1]["Status"] == "Completed"


def test_nhay_coc_bi_tu_choi(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 3)
    # don 1 dang Pending -> Completed thang la nhay coc
    r = client.put("/api/seller/don-hang/1/trang-thai", json={"status": "Completed"})
    assert r.json["status"] is False


def test_terminal_bi_tu_choi(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/don-hang/2/trang-thai", json={"status": "Cancelled"})
    assert r.json["status"] is False
    assert "cuối" in r.json["message"]


def test_don_shop_khac_bi_tu_choi(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 3)
    r = client.put("/api/seller/don-hang/9/trang-thai", json={"status": "Confirmed"})
    assert r.json["status"] is False
    assert "gian hàng" in r.json["message"]


def test_customer_403(seller_client):
    client, _ = _dung_cu(seller_client)
    _login(client, 5)
    r = client.get("/api/seller/don-hang")
    assert r.status_code == 403
