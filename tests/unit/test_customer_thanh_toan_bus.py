"""Unit test thanh toan BUS — 005 US3 T023.

Mock DAO — KHÔNG chạm PobbyDB thật. Viết TRƯỚC implementation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.DonHangBus import DonHangBus
from back_end.Model.DonHang import DonHang
from back_end.Model.OrderItem import OrderItem
from tests.conftest import MockDonHangCustomerDao


def _don(sdt="0901234567", payment="COD", items="co"):
    dh = DonHang(UserId=5, ReceiverName="Khách A", ReceiverPhone=sdt,
                 ShippingAddress="Hà Nội", PaymentMethod=payment,
                 SubTotal=100000, ShippingFee=25000, DiscountAmount=0,
                 TotalAmount=125000)
    if items == "co":
        dh.Items = [OrderItem(ProductId=1, ProductName="SP", Emoji="📦",
                              Quantity=1, UnitPrice=100000, TotalPrice=100000)]
    elif items == "rong":
        dh.Items = []
    return dh


def _bus(ket_qua_tao=1, don_hang=None, chi_tiet=None, store_ids=None):
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = MockDonHangCustomerDao(
        don_hang=don_hang or {}, chi_tiet=chi_tiet or {},
        ket_qua_tao=ket_qua_tao, store_ids=store_ids or {1: 10})
    return bus


def test_thieu_dia_chi_bi_tu_choi():
    bus = _bus()
    dh = _don()
    dh.ShippingAddress = ""
    kq = bus.tao_don_hang(dh)
    assert kq["status"] is False
    assert "đầy đủ thông tin" in kq["message"]


def test_sdt_sai_bi_tu_choi():
    bus = _bus()
    for sdt in ("123", "abc", "090123456", "09012345678", "1901234567"):
        kq = bus.tao_don_hang(_don(sdt=sdt))
        assert kq["status"] is False, f"SĐT={sdt!r} phải bị từ chối"
        assert "Số điện thoại người nhận không hợp lệ" in kq["message"]


def test_payment_la_bi_tu_choi():
    bus = _bus()
    kq = bus.tao_don_hang(_don(payment="Free"))
    assert kq["status"] is False
    assert "Phương thức thanh toán không hợp lệ" in kq["message"]


def test_gio_rong_bi_tu_choi():
    bus = _bus()
    kq = bus.tao_don_hang(_don(items="rong"))
    assert kq["status"] is False
    assert "Giỏ hàng trống" in kq["message"]


def test_het_hang_bao_out_of_stock():
    bus = _bus(ket_qua_tao={"error": "out_of_stock", "product_name": "SP X",
                            "available": 1})
    kq = bus.tao_don_hang(_don())
    assert kq["status"] is False
    assert "chỉ còn 1 sản phẩm" in kq["message"]


def test_hoa_don_cheo_bi_tu_choi():
    bus = _bus(don_hang={7: {"OrderId": 7, "UserId": 6, "Status": "Pending"}},
               chi_tiet={7: []})
    kq = bus.lay_hoa_don_cua_toi(5, 7)
    assert kq["status"] is False
    assert "không có quyền xem hóa đơn" in kq["message"]


def test_hoa_don_dung_chu():
    items = [{"ProductId": 1, "Quantity": 1, "UnitPrice": 100000}]
    bus = _bus(don_hang={7: {"OrderId": 7, "UserId": 5, "Status": "Pending"}},
               chi_tiet={7: items})
    kq = bus.lay_hoa_don_cua_toi(5, 7)
    assert kq["status"] is True
    assert kq["data"]["Items"] == items
