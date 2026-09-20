"""Integration test checkout API — 005 US3 T024.

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.Model.User import User
from tests.conftest import (FakeUserDaoBus, FakeSanPhamTimKiemStore,
                            FakeGioHangStore, FakeDonHangCustomerStore)


def _dung_cu(customer_client):
    users = {
        "khachA": User(ma_user=5, ma_nhom_quyen=4, ten_user="Khách A",
                       sdt="0901", dia_chi="HN", cmnd="1",
                       tendangnhap="khachA", mat_khau="123456"),
        "khachB": User(ma_user=6, ma_nhom_quyen=4, ten_user="Khách B",
                       sdt="0902", dia_chi="HN", cmnd="2",
                       tendangnhap="khachB", mat_khau="123456"),
    }
    thong_tin = {5: {"UserId": 5, "FullName": "Khách A", "Role_Id": 4,
                     "trang_thai": "active"},
                 6: {"UserId": 6, "FullName": "Khách B", "Role_Id": 4,
                     "trang_thai": "active"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"khachA": "123456", "khachB": "123456"})
    san_pham = {1: {"store_id": 10, "price": 100000, "quantity": 5,
                    "name": "SP A", "is_active": True, "category_id": 1,
                    "id": 1}}
    sp_store = FakeSanPhamTimKiemStore(san_pham=dict(san_pham))
    gio_store = FakeGioHangStore(san_pham=dict(san_pham))
    don_store = FakeDonHangCustomerStore(san_pham=dict(san_pham))
    client = customer_client(user_dao=user_dao, san_pham_store=sp_store,
                             gio_hang_store=gio_store,
                             don_hang_store=don_store)
    return client, don_store


def _login(client, uid=5):
    with client.session_transaction() as s:
        s["user_id"] = uid


def _payload(items=None):
    return {"ReceiverName": "Khách A", "ReceiverPhone": "0901234567",
            "ShippingAddress": "Hà Nội", "PaymentMethod": "COD",
            "SubTotal": 200000, "ShippingFee": 25000, "Discount": 0,
            "TotalAmount": 225000,
            "Items": items if items is not None else [
                {"ProductId": 1, "Quantity": 2, "UnitPrice": 100000,
                 "ProductName": "SP A", "Emoji": "📦"}]}


def test_checkout_tao_don_tru_kho_trong_gio(customer_client):
    client, don_store = _dung_cu(customer_client)
    _login(client)
    client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 2})
    r = client.post("/api/don-hang/dat-hang", json=_payload())
    assert r.json["status"] is True
    assert r.json["data"]["order_ids"][0] > 0
    assert don_store.san_pham[1]["quantity"] == 3
    r2 = client.get("/api/gio-hang/5")
    assert r2.json["status"] is True
    assert r2.json["data"] == []


def test_hoa_don_khop_tung_dong_tien(customer_client):
    client, _ = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/don-hang/dat-hang", json=_payload())
    assert r.json["status"] is True
    ma_don = r.json["data"]["order_ids"][0]
    r2 = client.get(f"/api/don-hang/hoa-don/{ma_don}")
    assert r2.status_code == 200
    assert r2.json["status"] is True
    data = r2.json["data"]
    assert data["SubTotal"] == 200000
    assert data["ShippingFee"] == 25000
    assert data["TotalAmount"] == 225000
    assert len(data["Items"]) == 1


def test_gio_rong_bi_tu_choi(customer_client):
    client, _ = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/don-hang/dat-hang", json=_payload(items=[]))
    assert r.json["status"] is False
    assert "Giỏ hàng trống" in r.json["message"]


def test_hoa_don_khach_khac_403(customer_client):
    client, _ = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/don-hang/dat-hang", json=_payload())
    ma_don = r.json["data"]["order_ids"][0]
    _login(client, 6)
    r2 = client.get(f"/api/don-hang/hoa-don/{ma_don}")
    assert r2.status_code == 403
    assert "không có quyền" in r2.json["message"]
