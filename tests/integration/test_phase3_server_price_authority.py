# -*- coding: utf-8 -*-
"""Phase 3 — T154/T127/T128: server-authoritative checkout."""

from tests.integration.test_phase2_cart_checkout_api import (
    _dung_cu, _mon, _payload, SAN_PHAM, FakeDonHangStoreCoGia
)


def test_client_money_fields_are_ignored(customer_client):
    client, don_store, _ = _dung_cu(customer_client)
    payload = _payload([_mon(1, 2, 1, "<script>fake</script>")])
    payload.update({
        "SubTotal": 1,
        "DiscountAmount": 999999999,
        "Discount": 999999999,
        "TotalAmount": 2,
    })
    payload["Items"][0].update({
        "UnitPrice": 1,
        "TotalPrice": 2,
        "ProductName": "Giá giả"
    })

    response = client.post("/api/don-hang/dat-hang", json=payload)

    assert response.json["status"] is True, response.json
    order = list(don_store.don_hang.values())[0]
    assert order["Items"][0]["UnitPrice"] == 100000.0
    assert order["Items"][0]["TotalPrice"] == 200000.0
    assert order["SubTotal"] == 200000.0
    assert order["DiscountAmount"] == 0.0
    assert order["TotalAmount"] == 225000.0


def test_server_recalculates_multi_item_total(customer_client):
    client, don_store, _ = _dung_cu(customer_client)
    response = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(1, 2, 1, "fake"),
        _mon(2, 1, 1, "fake"),
    ]))

    assert response.json["status"] is True, response.json
    orders = sorted(don_store.don_hang.values(), key=lambda x: x["OrderId"])
    assert len(orders) == 2
    assert [o["SubTotal"] for o in orders] == [200000.0, 70000.0]
    assert [o["TotalAmount"] for o in orders] == [212500.0, 82500.0]
    assert orders[0]["Items"][0]["UnitPrice"] == 100000.0
    assert orders[1]["Items"][0]["UnitPrice"] == 70000.0


def test_checkout_uses_current_db_price(customer_client):
    products = {k: dict(v) for k, v in SAN_PHAM.items()}
    products[1]["price"] = 135000
    don_store = FakeDonHangStoreCoGia(products, {}, 1)
    client, don_store, _ = _dung_cu(customer_client, don_store=don_store)

    response = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(1, 1, 1, "old client price")
    ]))

    assert response.json["status"] is True, response.json
    order = list(don_store.don_hang.values())[0]
    assert order["Items"][0]["UnitPrice"] == 135000.0
    assert order["SubTotal"] == 135000.0
    assert order["TotalAmount"] == 160000.0


def test_hidden_product_cannot_checkout(customer_client):
    products = {k: dict(v) for k, v in SAN_PHAM.items()}
    products[1]["is_active"] = False
    don_store = FakeDonHangStoreCoGia(products, {}, 1)
    client, don_store, _ = _dung_cu(customer_client, don_store=don_store)

    response = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(1, 1, 100000, "hidden")
    ]))

    assert response.json["status"] is False
    assert "kinh doanh" in response.json["message"]
    assert don_store.don_hang == {}


def test_hidden_after_cart_add_is_rejected(customer_client):
    products = {k: dict(v) for k, v in SAN_PHAM.items()}
    don_store = FakeDonHangStoreCoGia(products, {}, 1)
    client, don_store, cart = _dung_cu(customer_client, don_store=don_store)
    client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1})

    don_store.san_pham[1]["is_active"] = False
    response = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(1, 1, 100000, "hidden after cart")
    ]))

    assert response.json["status"] is False
    assert don_store.don_hang == {}
    assert cart.gio[5] == {1: 1}


def test_client_cannot_override_stock(customer_client):
    products = {k: dict(v) for k, v in SAN_PHAM.items()}
    products[1]["quantity"] = 1
    don_store = FakeDonHangStoreCoGia(products, {}, 1)
    client, don_store, _ = _dung_cu(customer_client, don_store=don_store)

    response = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(1, 2, 1, "fake")
    ]))

    assert response.json["status"] is False
    assert "1" in response.json["message"] and "kho" in response.json["message"]
    assert don_store.don_hang == {}


def test_authoritative_dao_query_locks_product_state():
    from back_end.DAO.DonHangDao import DonHangDao
    from back_end.Model.DonHang import DonHang
    from back_end.Model.OrderItem import OrderItem

    class Cursor:
        def __init__(self):
            self.sql = []
        def execute(self, sql, params=()):
            self.sql.append((sql, params))
        def fetchall(self):
            return [(1, "SP thật", 123000, 4, 1)]

    cursor = Cursor()
    order = DonHang(ShippingFee=25000)
    order.Items = [OrderItem(ProductId=1, Quantity=2, UnitPrice=1, TotalPrice=2)]
    error = DonHangDao()._nap_du_lieu_san_pham_checkout(cursor, [order])

    assert error is None
    assert "FOR UPDATE" in cursor.sql[0][0].upper()
    assert order.Items[0].UnitPrice == 123000.0
    assert order.Items[0].TotalPrice == 246000.0
    assert order.SubTotal == 246000.0
    assert order.TotalAmount == 271000.0
