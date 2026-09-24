"""Integration test dat hang nhieu shop — 011 US2 T008.

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
    }
    thong_tin = {5: {"UserId": 5, "FullName": "Khách A", "Role_Id": 4,
                     "trang_thai": "active"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"khachA": "123456"})
    san_pham = {
        1: {"id": 1, "name": "SP Shop10", "price": 100000, "quantity": 5,
            "store_id": 10, "category_id": 1, "is_active": True},
        2: {"id": 2, "name": "SP Shop20", "price": 70000, "quantity": 4,
            "store_id": 20, "category_id": 1, "is_active": True},
        3: {"id": 3, "name": "SP Hết kho", "price": 50000, "quantity": 1,
            "store_id": 30, "category_id": 1, "is_active": True},
    }
    sp_tim = FakeSanPhamTimKiemStore(san_pham=dict(san_pham))
    gio_store = FakeGioHangStore(
        san_pham={pid: {"store_id": sp["store_id"], "price": sp["price"],
                        "name": sp["name"]} for pid, sp in san_pham.items()})
    don_store = FakeDonHangCustomerStore(san_pham=dict(san_pham),
                                         don_hang={}, next_id=1)
    client = customer_client(user_dao=user_dao, san_pham_store=sp_tim,
                             gio_hang_store=gio_store,
                             don_hang_store=don_store)
    return client, don_store, gio_store


def _login(client, uid=5):
    with client.session_transaction() as s:
        s["user_id"] = uid


def _payload(items):
    """Payload đặt hàng chuẩn — tiền tính theo từng món + phí ship 25k."""
    sub = sum(it["Quantity"] * it["UnitPrice"] for it in items)
    return {"ReceiverName": "Khách A", "ReceiverPhone": "0901234567",
            "ShippingAddress": "Hà Nội", "PaymentMethod": "COD",
            "SubTotal": sub, "ShippingFee": 25000, "Discount": 0,
            "TotalAmount": sub + 25000, "Items": items}


def _mon(pid, qty, price, ten):
    return {"ProductId": pid, "ProductName": ten, "Emoji": "📦",
            "Quantity": qty, "UnitPrice": price, "TotalPrice": qty * price}


def test_gio_2_shop_tao_2_don(customer_client):
    """US2: gio 2 shop → data.order_ids dài 2, Orders trong DB đúng nhóm, giỏ rỗng."""
    client, don_store, gio_store = _dung_cu(customer_client)
    _login(client)
    client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1})
    client.post("/api/gio-hang/them", json={"ProductId": 2, "Quantity": 2})
    r = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(1, 1, 100000, "SP Shop10"), _mon(2, 2, 70000, "SP Shop20")]))
    assert r.json["status"] is True, r.json
    data = r.json["data"]
    assert len(data["order_ids"]) == 2
    assert "2 đơn hàng đã được tạo" in r.json["message"]
    # Hai đơn trong DB, mỗi đơn chỉ chứa sản phẩm đúng shop
    don_ids = [don["OrderId"] for don in don_store.don_hang.values()]
    assert sorted(don_ids) == sorted(data["order_ids"])
    for don in don_store.don_hang.values():
        sp_ids = [it["ProductId"] for it in don["Items"]]
        # món 1 thuộc shop 10, món 2 thuộc shop 20 — không trộn
        assert not (1 in sp_ids and 2 in sp_ids)
    # Giỏ đã bị xóa sau khi thành công toàn bộ
    gio = client.get("/api/gio-hang/5").json["data"]
    assert gio == []


def test_gio_1_shop_tao_1_don(customer_client):
    """US2: gio 1 shop → vẫn tạo 1 đơn như cũ (data.order_ids dài 1)."""
    client, _, _ = _dung_cu(customer_client)
    _login(client)
    client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 2})
    r = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(1, 2, 100000, "SP Shop10")]))
    assert r.json["status"] is True
    assert len(r.json["data"]["order_ids"]) == 1
    assert "1 đơn hàng đã được tạo" in r.json["message"]


def test_het_hang_khong_tao_don_nao(customer_client):
    """US2: 1 shop hết hàng → KHÔNG đơn nào được tạo, giỏ vẫn còn."""
    client, don_store, gio_store = _dung_cu(customer_client)
    _login(client)
    client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1})
    # SP3 chỉ còn 1, đặt 5 → hết hàng
    r = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(1, 1, 100000, "SP Shop10"), _mon(3, 5, 50000, "SP Hết kho")]))
    assert r.json["status"] is False
    assert "chỉ còn 1 sản phẩm" in r.json["message"]
    assert don_store.don_hang == {}, "không đơn nào được tạo (all-or-nothing)"
    assert gio_store.gio[5] == {1: 1}, "giỏ KHÔNG bị xóa khi thất bại"


def test_orders_response_chua_store_id_va_total(customer_client):
    """US2: data.orders đủ order_id/store_id/store_name/total theo contract."""
    client, _, _ = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(1, 1, 100000, "SP Shop10"), _mon(2, 1, 70000, "SP Shop20")]))
    orders = {o["order_id"]: o for o in r.json["data"]["orders"]}
    assert len(orders) == 2
    for o in orders.values():
        assert {"order_id", "store_id", "store_name", "total"} <= set(o.keys())
    assert orders[r.json["data"]["order_ids"][0]]["store_name"]
    # tổng mỗi đơn = tiền món + phí ship 25k
    tong = sum(o["total"] for o in orders.values())
    assert tong == 100000 + 70000 + 25000 * 2