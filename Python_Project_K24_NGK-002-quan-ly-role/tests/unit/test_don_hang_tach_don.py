"""Unit test tach don theo shop + all-or-nothing — 011 US2 T007.

Mock DAO — KHÔNG chạm PobbyDB thật. Viết TRƯỚC implementation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.DonHangBus import DonHangBus
from back_end.Model.DonHang import DonHang
from back_end.Model.OrderItem import OrderItem
from tests.conftest import MockDonHangCustomerDao


def _don(items):
    dh = DonHang(UserId=5, ReceiverName="Khách A", ReceiverPhone="0901234567",
                 ShippingAddress="Hà Nội", PaymentMethod="COD",
                 SubTotal=170000, ShippingFee=25000, DiscountAmount=0,
                 TotalAmount=195000)
    dh.Items = items
    return dh


def _mon(product_id, name, qty, price, store_id=None):
    return OrderItem(
        ProductId=product_id, ProductName=name, Emoji="📦",
        Quantity=qty, UnitPrice=price, TotalPrice=qty * price)


def _dao_tra(ket_qua, store_map=None):
    """Mock DAO trả kết quả cấu hình; store_map: {product_id: store_id}."""
    return MockDonHangCustomerDao(
        ket_qua_tao=ket_qua,
        store_ids=store_map or {1: 10, 2: 20, 3: 10})


def test_gio_2_shop_tao_2_don_dung_nhom():
    """US2: 2 shop → 2 đơn; mỗi đơn chỉ chứa sản phẩm của shop đó."""
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = _dao_tra(ket_qua=[101, 102])
    dh = _don([_mon(1, "SP A", 1, 100000), _mon(2, "SP B", 1, 70000)])
    kq = bus.tao_don_hang(dh)
    assert kq["status"] is True
    ds_don = bus.dao._ds_don  # đơn BUS đã nhóm trước khi gọi DAO
    assert len(ds_don) == 2
    id_don_1 = [sp.ProductId for sp in ds_don[0].Items]
    id_don_2 = [sp.ProductId for sp in ds_don[1].Items]
    assert set(id_don_1) == {1} and set(id_don_2) == {2}


def test_gio_1_shop_tao_1_don_nhu_cu():
    """US2: vẫn 1 shop → vẫn 1 đơn như trước."""
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = _dao_tra(ket_qua=[101], store_map={1: 10, 3: 10})
    dh = _don([_mon(1, "SP A", 2, 100000), _mon(3, "SP C", 1, 50000)])
    kq = bus.tao_don_hang(dh)
    assert kq["status"] is True
    assert kq["data"]["order_ids"] == [101]
    assert len(bus.dao._ds_don) == 1
    assert len(bus.dao._ds_don[0].Items) == 2


def test_moi_don_dung_shop_va_tong_dung():
    """US2: response orders có store_id/total đúng từng đơn."""
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = _dao_tra(ket_qua=[101, 102])
    dh = _don([_mon(1, "SP A", 2, 100000), _mon(2, "SP B", 3, 70000)])
    kq = bus.tao_don_hang(dh)
    assert kq["status"] is True
    orders = {o["order_id"]: o for o in kq["data"]["orders"]}
    assert orders[101]["store_id"] == 10
    assert orders[101]["total"] == 2 * 100000 + 25000
    assert orders[102]["store_id"] == 20
    # SHIPPING_FEE tính 1 lần cho mỗi đơn (không chia nhỏ)
    assert orders[102]["total"] == 3 * 70000 + 25000


def test_all_or_nothing_1_shop_het_hang():
    """US2: 1 shop hết hàng → KHÔNG đơn nào được tạo (DAO báo lỗi dict)."""
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = _dao_tra(ket_qua={"error": "out_of_stock",
                                "product_name": "SP B", "available": 1})
    dh = _don([_mon(1, "SP A", 1, 100000), _mon(2, "SP B", 2, 70000)])
    kq = bus.tao_don_hang(dh)
    assert kq["status"] is False
    assert "chỉ còn 1 sản phẩm" in kq["message"]


def test_het_hang_khong_tao_don_nao():
    """US2: lỗi hết hàng → data là None, không có order_ids nào."""
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = _dao_tra(ket_qua={"error": "out_of_stock",
                                "product_name": "SP B", "available": 1})
    dh = _don([_mon(1, "SP A", 1, 100000), _mon(2, "SP B", 2, 70000)])
    kq = bus.tao_don_hang(dh)
    assert kq.get("data") is None
    assert "order_ids" not in (kq.get("data") or {})