# -*- coding: utf-8 -*-
"""Phase 4 — T111 + T96 regression.

T111: duplicate ProductId quantities are aggregated for stock validation/deduction.
T96: OldPrice must represent a real discount: OldPrice > Price > 0.
"""
from back_end.DAO.DonHangDao import DonHangDao
from back_end.Model.DonHang import DonHang
from back_end.Model.OrderItem import OrderItem
from back_end.BUS.SanPhamBus import SanPhamBus
from tests.integration.test_phase2_cart_checkout_api import (
    _dung_cu as checkout_tools, _mon, _payload
)
from tests.integration.test_phase4_price_api import _dung_cu as seller_tools, _login


def _order(items):
    order = DonHang(ShippingFee=25000, UserId=5)
    order.Items = items
    return order


def test_t111_duplicate_product_quantities_are_aggregated():
    class Cursor:
        def __init__(self, stock=5):
            self.sql = []
            self.stock = stock

        def execute(self, sql, params=()):
            self.sql.append((sql, params))

        def fetchall(self):
            return [(1, "SP thật", 100000, self.stock, 1)]

    cursor = Cursor(stock=5)
    order = _order([
        OrderItem(ProductId=1, Quantity=3, UnitPrice=1, TotalPrice=3),
        OrderItem(ProductId=1, Quantity=4, UnitPrice=1, TotalPrice=4),
    ])
    error = DonHangDao()._nap_du_lieu_san_pham_checkout(cursor, [order])
    assert error and error["error"] == "out_of_stock"
    assert error["requested"] == 7
    assert error["available"] == 5


def test_t111_duplicate_product_within_stock_passes_authoritative_reload():
    class Cursor:
        def __init__(self):
            self.sql = []

        def execute(self, sql, params=()):
            self.sql.append((sql, params))

        def fetchall(self):
            return [(1, "SP thật", 120000, 10, 1)]

    cursor = Cursor()
    order = _order([
        OrderItem(ProductId=1, Quantity=3, UnitPrice=1, TotalPrice=1),
        OrderItem(ProductId=1, Quantity=4, UnitPrice=1, TotalPrice=1),
    ])
    error = DonHangDao()._nap_du_lieu_san_pham_checkout(cursor, [order])
    assert error is None
    assert [i.TotalPrice for i in order.Items] == [360000.0, 480000.0]
    assert order.SubTotal == 840000.0
    assert order.TotalAmount == 865000.0


def test_t111_duplicate_product_deduction_uses_aggregate():
    class Cursor:
        def __init__(self):
            self.sql = []
            self.rowcount = 1

        def execute(self, sql, params=()):
            self.sql.append((sql, params))

    cursor = Cursor()
    items = [
        OrderItem(ProductId=1, Quantity=3, UnitPrice=100000, TotalPrice=300000),
        OrderItem(ProductId=1, Quantity=4, UnitPrice=100000, TotalPrice=400000),
    ]
    error = DonHangDao()._chen_items_tru_kho(cursor, object(), 10, items)
    assert error is None
    stock_updates = [
        (sql, params) for sql, params in cursor.sql
        if "UPDATE Products" in sql
    ]
    assert len(stock_updates) == 1
    assert stock_updates[0][1] == (7, 1, 7)


def test_t111_api_rejects_tampered_duplicate_quantities(customer_client):
    client, don_store, _ = checkout_tools(customer_client)
    response = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(1, 3, 1, "fake 1"),
        _mon(1, 4, 1, "fake 2"),
    ]))
    assert response.json["status"] is False, response.json
    assert "kho" in response.json["message"]
    assert don_store.don_hang == {}


def test_t111_api_allows_duplicate_quantities_when_total_is_in_stock(customer_client):
    client, don_store, _ = checkout_tools(customer_client)
    response = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(1, 2, 1, "fake 1"),
        _mon(1, 3, 1, "fake 2"),
    ]))
    assert response.json["status"] is True, response.json
    order = list(don_store.don_hang.values())[0]
    assert [it["Quantity"] for it in order["Items"]] == [2, 3]


def test_t96_valid_discount_requires_old_price_above_sale_price(seller_client):
    client, sp_store = seller_tools(seller_client)
    _login(client)
    response = client.put(
        "/api/seller/san-pham/1/gia",
        json={"gia_goc": 100000, "gia_khuyen_mai": 80000, "giam_gia": True},
    )
    assert response.json["status"] is True
    assert sp_store.san_pham[1]["old_price"] == 100000
    assert sp_store.san_pham[1]["price"] == 80000


def test_t96_abnormal_old_price_values_are_rejected(seller_client):
    client, sp_store = seller_tools(seller_client)
    _login(client)
    for old_price, sale_price in ((100000, 100000), (80000, 100000), (0, 50000), (-1, 50000)):
        response = client.put(
            "/api/seller/san-pham/1/gia",
            json={"gia_goc": old_price, "gia_khuyen_mai": sale_price, "giam_gia": True},
        )
        assert response.json["status"] is False, response.json
        assert sp_store.san_pham[1]["old_price"] is None


def test_t96_create_product_rejects_abnormal_old_price(seller_client):
    client, sp_store = seller_tools(seller_client)
    _login(client)
    response = client.post("/api/seller/san-pham", json={
        "name": "SP T96 abnormal",
        "description": "test",
        "price": 100000,
        "old_price": 90000,
        "quantity": 1,
        "category_id": 1,
    })
    assert response.json["status"] is False
    assert "Giá gốc" in response.json["message"]
    assert not any(v.get("name") == "SP T96 abnormal" for v in sp_store.san_pham.values())


def test_t96_edit_product_rejects_abnormal_old_price(seller_client):
    client, sp_store = seller_tools(seller_client)
    _login(client)
    response = client.put("/api/seller/san-pham/1", json={
        "name": "Ao",
        "description": "test",
        "price": 100000,
        "old_price": 100000,
        "quantity": 5,
        "category_id": 1,
    })
    assert response.json["status"] is False
    assert sp_store.san_pham[1]["old_price"] is None


def test_t96_no_discount_clears_old_price(seller_client):
    client, sp_store = seller_tools(seller_client)
    _login(client)
    sp_store.san_pham[1]["old_price"] = 100000
    sp_store.san_pham[1]["price"] = 80000
    response = client.put("/api/seller/san-pham/1/gia", json={
        "gia_goc": 100000,
        "gia_khuyen_mai": 1,
        "giam_gia": False,
    })
    assert response.json["status"] is True
    assert sp_store.san_pham[1]["price"] == 100000
    assert sp_store.san_pham[1]["old_price"] is None


def test_t96_bus_create_rejects_old_price_not_above_sale_price():
    bus = SanPhamBus()
    class Dao:
        def kiem_tra_category_ton_tai(self, category_id):
            return True
        def kiem_tra_trung_ten(self, store_id, ten):
            return False
        def them(self, sp):
            raise AssertionError("abnormal price must not reach DAO")
    bus.dao = Dao()
    result = bus.them_san_pham_cua_seller(
        3, 10, "SP abnormal", "test", 100000, 100000, 1, 1
    )
    assert result["status"] is False
