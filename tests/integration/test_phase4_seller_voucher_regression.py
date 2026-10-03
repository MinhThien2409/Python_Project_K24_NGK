"""Phase 4 regression/security tests for Seller Voucher integration.

Các test này bổ sung bằng chứng cho những nhánh Phase 1-3 chưa được kiểm tra
đầy đủ, không thay đổi business rule.
"""

from datetime import datetime, timedelta

from back_end.BUS.VoucherBus import VoucherBus
from back_end.DAO.DonHangDao import DonHangDao
from back_end.DAO.VoucherDao import VoucherDao
from back_end.Model.DonHang import DonHang
from back_end.Model.OrderItem import OrderItem
from tests.conftest import MockUserDao, FakeShopStore
from tests.integration.test_phase2_seller_voucher_api import (
    FakeVoucherBus,
    _manager_user,
    _seller_user,
    _session_login,
)


def test_all_foreign_seller_crud_operations_are_rejected(seller_client, monkeypatch):
    import app as app_module

    class OwnerCheckingVoucherBus(FakeVoucherBus):
        def _owned(self, voucher_id, seller_id):
            return voucher_id == 1 and seller_id == 10

        def lay_theo_id(self, voucher_id, seller_id):
            if not self._owned(voucher_id, seller_id):
                return {"status": False, "message": "Bạn không có quyền thao tác trên voucher này!"}
            return super().lay_theo_id(voucher_id, seller_id)

        def sua(self, voucher_id, seller_id, product_ids, **kw):
            if not self._owned(voucher_id, seller_id):
                return {"status": False, "message": "Bạn không có quyền thao tác trên voucher này!"}
            return super().sua(voucher_id, seller_id, product_ids, **kw)

        def toggle(self, voucher_id, seller_id):
            if not self._owned(voucher_id, seller_id):
                return {"status": False, "message": "Bạn không có quyền thao tác trên voucher này!"}
            return super().toggle(voucher_id, seller_id)

        def xoa(self, voucher_id, seller_id):
            if not self._owned(voucher_id, seller_id):
                return {"status": False, "message": "Bạn không có quyền thao tác trên voucher này!"}
            return super().xoa(voucher_id, seller_id)

    fake = OwnerCheckingVoucherBus()
    monkeypatch.setattr(app_module, "voucher_bus", fake)
    client = seller_client(
        user_dao=MockUserDao(user=_seller_user(3)),
        shop_store=FakeShopStore({10: {"StoreId": 10, "UserId": 3, "StoreName": "Shop A"}}),
    )
    _session_login(client, 3)

    payload = {
        "SellerId": 20,
        "ProductIds": [4],
        "Code": "SAVE20",
        "Name": "Save",
        "DiscountType": "PERCENT",
        "DiscountValue": 10,
        "MinOrderValue": 0,
        "MaxDiscount": 0,
        "StartDate": "2026-01-01 00:00:00",
        "EndDate": "2026-12-31 23:59:59",
        "Quantity": 10,
    }

    assert client.get("/api/voucher/2").status_code == 403
    assert client.put("/api/voucher/2", json=payload).status_code == 403
    assert client.post("/api/voucher/2/toggle").status_code == 403
    assert client.delete("/api/voucher/2").status_code == 403


def test_product_ids_are_deduplicated_before_mapping():
    assert VoucherBus._product_ids([1, 1, 2, 2]) == [1, 2]


def test_product_ids_reject_invalid_values():
    assert VoucherBus._product_ids([1, 0]) is None
    assert VoucherBus._product_ids([1, -2]) is None
    assert VoucherBus._product_ids([1, "abc"]) is None
    assert VoucherBus._product_ids("1,2") is None


class ProductOwnershipCursor:
    def __init__(self, rows):
        self.rows = rows
        self.sql = None
        self.args = None

    def execute(self, sql, args=None):
        self.sql = sql
        self.args = args

    def fetchall(self):
        return self.rows


def test_voucher_dao_product_ownership_query_is_store_scoped():
    cursor = ProductOwnershipCursor([(1,), (2,)])
    assert VoucherDao()._products_belong_to_seller(cursor, 10, [1, 2]) is True
    assert "StoreId=%s" in cursor.sql
    assert cursor.args == (10, 1, 2)


def test_voucher_dao_product_ownership_rejects_foreign_product():
    cursor = ProductOwnershipCursor([(1,)])
    assert VoucherDao()._products_belong_to_seller(cursor, 10, [1, 2]) is False


def _base_voucher_kwargs(**overrides):
    data = dict(
        code=" SAVE10 ",
        name="Save 10",
        dtype="PERCENT",
        value=10,
        min_order=0,
        max_discount=50000,
        start="2026-01-01 00:00:00",
        end="2026-12-31 23:59:59",
        quantity=10,
        seller_id=10,
    )
    data.update(overrides)
    return data


def test_voucher_percent_boundary_and_fixed_positive():
    bus = VoucherBus()

    v, err = bus.validate(**_base_voucher_kwargs(value=100))
    assert err is None and v.DiscountValue == 100

    v, err = bus.validate(**_base_voucher_kwargs(value=0))
    assert v is None and err

    v, err = bus.validate(**_base_voucher_kwargs(value=-1))
    assert v is None and err

    v, err = bus.validate(**_base_voucher_kwargs(dtype="FIXED", value=1))
    assert err is None and v.DiscountType == "FIXED"


def test_voucher_equal_start_end_is_valid():
    same = "2026-06-01 12:00:00"
    v, err = VoucherBus().validate(**_base_voucher_kwargs(start=same, end=same))
    assert err is None
    assert v.StartDate == datetime(2026, 6, 1, 12, 0, 0)


def test_voucher_quantity_zero_is_valid_but_unusable_at_checkout():
    bus = VoucherBus()
    v, err = bus.validate(**_base_voucher_kwargs(quantity=0))
    assert err is None
    assert v.Quantity == 0


class CheckoutCursor:
    def __init__(self, row, eligible=True):
        self.row = row
        self.eligible = eligible
        self.rowcount = 0
        self.lastrowid = 99
        self.sql = []

    def execute(self, sql, args=None):
        self.sql.append((sql, args))
        upper = sql.strip().upper()
        if upper.startswith("UPDATE VOUCHER"):
            self.rowcount = 1

    def fetchone(self):
        return self.row

    def fetchall(self):
        if self.eligible and self.row:
            return [(1, 100000, 10, 10, 1)]
        return []

    def close(self):
        pass


def checkout_row(**overrides):
    now = datetime.now()
    data = dict(
        VoucherId=1,
        SellerId=10,
        Code="SAVE10",
        Name="Save",
        DiscountType="PERCENT",
        DiscountValue=10,
        MinOrderValue=0,
        MaxDiscount=50000,
        StartDate=now - timedelta(days=1),
        EndDate=now + timedelta(days=1),
        Quantity=10,
        UsedQuantity=0,
        IsActive=1,
    )
    data.update(overrides)
    return tuple(
        data[k]
        for k in (
            "VoucherId", "SellerId", "Code", "Name", "DiscountType",
            "DiscountValue", "MinOrderValue", "MaxDiscount", "StartDate",
            "EndDate", "Quantity", "UsedQuantity", "IsActive",
        )
    )


def checkout_order(product_id=1, quantity=2, price=100000, voucher="SAVE10"):
    order = DonHang(UserId=5, ShippingFee=25000, VoucherCode=voucher)
    order.Items = [
        OrderItem(
            ProductId=product_id,
            Quantity=quantity,
            UnitPrice=price,
            TotalPrice=quantity * price,
        )
    ]
    order.SubTotal = quantity * price
    order.TotalAmount = order.SubTotal + order.ShippingFee
    return order


def test_checkout_scopes_eligible_product_to_voucher_seller():
    cursor = CheckoutCursor(checkout_row())
    order = checkout_order()

    assert DonHangDao()._ap_dung_voucher(cursor, [order]) is None
    sql = next(q for q, _ in cursor.sql if "FROM VoucherProduct" in q)
    assert "p.StoreId=%s" in sql


def test_checkout_increments_used_quantity_once_and_snapshots_calculated_values():
    cursor = CheckoutCursor(checkout_row())
    order = checkout_order()

    assert DonHangDao()._ap_dung_voucher(cursor, [order]) is None
    assert order.VoucherCode == "SAVE10"
    assert order.DiscountAmount == 20000
    assert order.TotalAmount == 205000

    update_sql = next(q for q, _ in cursor.sql if "UPDATE Voucher" in q)
    assert "UsedQuantity=UsedQuantity+1" in update_sql

    insert_cursor = CheckoutCursor(checkout_row())
    DonHangDao()._chen_order_lay_id(insert_cursor, order)
    insert_sql, params = insert_cursor.sql[0]
    assert "VoucherCode" in insert_sql
    assert params[7:11] == ("SAVE10", 200000.0, 20000.0, 205000.0)


def test_checkout_rejects_equal_quantity_as_exhausted():
    cursor = CheckoutCursor(checkout_row(Quantity=1, UsedQuantity=1))
    result = DonHangDao()._ap_dung_voucher(cursor, [checkout_order()])
    assert result["error"] == "invalid_voucher"


class FailingOrderCursor(CheckoutCursor):
    def execute(self, sql, args=None):
        if sql.strip().upper().startswith("INSERT INTO ORDERS"):
            raise RuntimeError("order insert failed")
        super().execute(sql, args)


class CheckoutConn:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.rollback_count = 0
        self.commit_count = 0

    def cursor(self):
        return self.cursor_obj

    def rollback(self):
        self.rollback_count += 1

    def commit(self):
        self.commit_count += 1

    def close(self):
        pass


def test_order_creation_error_rolls_back_after_voucher_processing(monkeypatch):
    cursor = FailingOrderCursor(checkout_row())
    conn = CheckoutConn(cursor)
    monkeypatch.setattr(
        "back_end.DAO.DonHangDao.DBconnection.get_connection",
        lambda self: conn,
    )

    result = DonHangDao().tao_don_hang([checkout_order()])
    assert result is False
    assert conn.rollback_count >= 1
    assert conn.commit_count == 0


def test_checkout_backend_ignores_client_product_price(customer_client):
    from tests.integration.test_customer_thanh_toan_api import _dung_cu, _login, _payload

    client, _ = _dung_cu(customer_client)
    _login(client)
    payload = _payload()
    payload["Items"][0]["UnitPrice"] = 1
    payload["Items"][0]["TotalPrice"] = 1

    response = client.post("/api/don-hang/dat-hang", json=payload)
    assert response.json["status"] is True

    order_id = response.json["data"]["order_ids"][0]
    invoice = client.get(f"/api/don-hang/hoa-don/{order_id}").json["data"]
    assert invoice["SubTotal"] == 200000
    assert invoice["TotalAmount"] == 225000


def test_checkout_ui_does_not_send_authoritative_amounts_or_seller_fields():
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    js = (repo / "static" / "js" / "main.js").read_text(encoding="utf-8")
    start = js.index("async function handlePlaceOrder")
    payload_start = js.index("const orderPayload =", start)
    end = js.index("};", payload_start) + 2
    payload = js[payload_start:end]

    assert "voucherCode" in payload
    assert "SellerId" not in payload
    assert "UsedQuantity" not in payload
    assert "DiscountAmount" not in payload
    assert "TotalAmount" not in payload
    assert "SubTotal" not in payload
