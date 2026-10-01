# -*- coding: utf-8 -*-
"""Phase 1 — kiểm thử validate thanh toán ở tầng BUS (authoritative).

Bổ sung cho test_customer_thanh_toan_bus.py (005 US3) các quy tắc Phase 1:
- Giới hạn độ dài tên người nhận (≤100) và địa chỉ (≤500).
- Số lượng/đơn giá/mã sản phẩm của từng dòng hàng phải hợp lệ và KHÔNG gây 500.

Mock DAO — KHÔNG chạm PobbyDB thật. Viết TRƯỚC/song song implementation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.DonHangBus import DonHangBus
from back_end.Model.DonHang import DonHang
from back_end.Model.OrderItem import OrderItem
from tests.conftest import MockDonHangCustomerDao


def _bus(ket_qua_tao=1, store_ids=None):
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = MockDonHangCustomerDao(
        don_hang={}, chi_tiet={}, ket_qua_tao=ket_qua_tao,
        store_ids=store_ids or {1: 10})
    return bus


def _don(**doi):
    dh = DonHang(UserId=5, ReceiverName="Khách A", ReceiverPhone="0901234567",
                 ShippingAddress="Hà Nội", PaymentMethod="COD",
                 SubTotal=100000, ShippingFee=25000, DiscountAmount=0,
                 TotalAmount=125000)
    dh.Items = [OrderItem(ProductId=1, ProductName="SP", Emoji="📦",
                          Quantity=1, UnitPrice=100000, TotalPrice=100000)]
    for k, v in doi.items():
        setattr(dh, k, v)
    return dh


def test_ten_nguoi_nhan_qua_dai_bi_tu_choi():
    kq = _bus().tao_don_hang(_don(ReceiverName="A" * 101))
    assert kq["status"] is False
    assert "quá dài" in kq["message"]


def test_ten_nguoi_nhan_toi_da_100_van_hop_le():
    kq = _bus().tao_don_hang(_don(ReceiverName="A" * 100))
    assert kq["status"] is True


def test_dia_chi_qua_dai_bi_tu_choi():
    kq = _bus().tao_don_hang(_don(ShippingAddress="B" * 501))
    assert kq["status"] is False
    assert "quá dài" in kq["message"]


def test_dia_chi_toi_da_500_van_hop_le():
    kq = _bus().tao_don_hang(_don(ShippingAddress="B" * 500))
    assert kq["status"] is True


def test_so_luong_thap_phan_bi_tu_choi():
    dh = _don()
    dh.Items[0].Quantity = 1.5
    kq = _bus().tao_don_hang(dh)
    assert kq["status"] is False
    assert "Số lượng sản phẩm không hợp lệ" in kq["message"]


def test_so_luong_chu_bi_tu_choi_khong_500():
    dh = _don()
    dh.Items[0].Quantity = "abc"
    kq = _bus().tao_don_hang(dh)
    assert kq["status"] is False
    assert "Số lượng sản phẩm không hợp lệ" in kq["message"]


def test_so_luong_am_bi_tu_choi():
    dh = _don()
    dh.Items[0].Quantity = -2
    kq = _bus().tao_don_hang(dh)
    assert kq["status"] is False
    assert "Số lượng sản phẩm không hợp lệ" in kq["message"]


def test_don_gia_am_bi_tu_choi():
    dh = _don()
    dh.Items[0].UnitPrice = -1000
    kq = _bus().tao_don_hang(dh)
    assert kq["status"] is False
    assert "Đơn giá sản phẩm không hợp lệ" in kq["message"]


def test_ma_san_pham_chu_bi_tu_choi():
    dh = _don()
    dh.Items[0].ProductId = "abc"
    kq = _bus().tao_don_hang(dh)
    assert kq["status"] is False
    assert "Thông tin sản phẩm không hợp lệ" in kq["message"]
