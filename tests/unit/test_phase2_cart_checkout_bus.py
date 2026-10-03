# -*- coding: utf-8 -*-
"""Phase 2 — BUS: checkout theo món đã chọn + đối chiếu giá/tồn DB (authoritative).

Fake/mock in-memory — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.DonHangBus import DonHangBus
from back_end.BUS.GioHangBus import GioHangBus
from back_end.Model.DonHang import DonHang
from back_end.Model.OrderItem import OrderItem
from tests.conftest import MockDonHangCustomerDao


class FakeDonHangDaoCoGia(MockDonHangCustomerDao):
    """Mock đơn hàng + nguồn đối chiếu giá/tồn/trạng thái từ DB giả lập."""

    def __init__(self, bang_gia=None, **kwargs):
        super().__init__(**kwargs)
        self.bang_gia = bang_gia or {}

    def lay_thong_tin_san_pham(self, product_ids):
        return {int(pid): dict(self.bang_gia[int(pid)])
                for pid in (product_ids or []) if int(pid) in self.bang_gia}


def _bus_gia(bang_gia):
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = FakeDonHangDaoCoGia(don_hang={}, chi_tiet={}, ket_qua_tao=1,
                                  store_ids={1: 10, 2: 20}, bang_gia=bang_gia)
    return bus


def _don(items, **doi):
    dh = DonHang(UserId=5, ReceiverName="Khách A", ReceiverPhone="0901234567",
                 ShippingAddress="Hà Nội", PaymentMethod="COD",
                 SubTotal=0, ShippingFee=25000, DiscountAmount=0,
                 TotalAmount=0)
    dh.Items = items
    for k, v in doi.items():
        setattr(dh, k, v)
    return dh


def _mon(pid, qty, price, ten="SP"):
    return OrderItem(ProductId=pid, ProductName=ten, Emoji="📦",
                     Quantity=qty, UnitPrice=price, TotalPrice=qty * price)


BANG_GIA = {
    1: {"name": "SP Shop10", "price": 100000.0, "quantity": 5, "is_active": True},
    2: {"name": "SP Shop20", "price": 70000.0, "quantity": 4, "is_active": True},
}

# ── Đối chiếu authoritative ──────────────────────────────────────────────

def test_gia_mao_bi_ghi_de_theo_db():
    """Phase 2 §9: client gửi UnitPrice=1 → BUS ghi đè 100000, đơn vẫn tạo."""
    bus = _bus_gia(BANG_GIA)
    dh = _don([_mon(1, 2, 1)], SubTotal=2, TotalAmount=25002)
    kq = bus.tao_don_hang(dh)
    assert kq["status"] is True, kq
    assert dh.Items[0].UnitPrice == 100000.0
    assert dh.Items[0].TotalPrice == 200000.0
    assert dh.SubTotal == 200000.0
    assert dh.TotalAmount == 225000.0


def test_sp_khong_ton_tai_bi_tu_choi():
    bus = _bus_gia(BANG_GIA)
    kq = bus.tao_don_hang(_don([_mon(99, 1, 50000, "SP Ma")]))
    assert kq["status"] is False
    assert "Không tìm thấy sản phẩm" in kq["message"]


def test_sp_ngung_kinh_doanh_bi_tu_choi():
    bang = {1: {"name": "SP Ẩn", "price": 100000.0, "quantity": 5,
                "is_active": False}}
    kq = _bus_gia(bang).tao_don_hang(_don([_mon(1, 1, 100000, "SP Ẩn")]))
    assert kq["status"] is False
    assert "không còn kinh doanh" in kq["message"]


def test_vuot_kho_bi_tu_choi():
    bang = {1: {"name": "SP Ít", "price": 100000.0, "quantity": 1,
                "is_active": True}}
    kq = _bus_gia(bang).tao_don_hang(_don([_mon(1, 5, 100000, "SP Ít")]))
    assert kq["status"] is False
    assert "chỉ còn 1 sản phẩm" in kq["message"]


def test_dao_cu_thieu_nguon_gia_van_tuong_thich():
    """Phase 2: DAO không có lay_thong_tin_san_pham (mock cũ) → giữ hành vi cũ."""
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = MockDonHangCustomerDao(don_hang={}, chi_tiet={}, ket_qua_tao=7,
                                     store_ids={1: 10})
    dh = _don([_mon(1, 1, 100000)], SubTotal=100000, TotalAmount=125000)
    kq = bus.tao_don_hang(dh)
    assert kq["status"] is True, kq
    assert kq["data"]["order_ids"] == [7]


def test_phuong_thuc_la_bi_tu_choi():
    bus = _bus_gia(BANG_GIA)
    dh = _don([_mon(1, 1, 100000)], PaymentMethod="ZaloPay",
              SubTotal=100000, TotalAmount=125000)
    kq = bus.tao_don_hang(dh)
    assert kq["status"] is False
    assert "không hợp lệ" in kq["message"]


def test_items_khong_phai_list_bi_tu_choi_khong_500():
    bus = _bus_gia(BANG_GIA)
    kq = bus.tao_don_hang(_don("khong-phai-list"))
    assert kq["status"] is False
    assert "Giỏ hàng trống" in kq["message"]


# ── Xóa chọn lọc sau checkout ────────────────────────────────────────────

class FakeGioDaoChonLoc:
    def __init__(self, items):
        self.items = dict(items)
        self.da_cap_nhat_tong = 0

    def lay_hoac_tao_gio_hang(self, user_id):
        return 1

    def xoa_cac_san_pham(self, cart_id, product_ids):
        for pid in product_ids:
            self.items.pop(int(pid), None)
        return True

    def xoa_khoi_gio(self, cart_id, product_id):
        self.items.pop(int(product_id), None)
        return True

    def cap_nhat_tong_tien(self, cart_id):
        self.da_cap_nhat_tong += 1
        return True


class FakeGioDaoCu(FakeGioDaoChonLoc):
    """Fake cũ không có xoa_cac_san_pham → BUS phải fallback từng món."""

    def __init__(self, items):
        self.items = dict(items)
        self.da_cap_nhat_tong = 0

    def __getattribute__(self, ten):
        if ten == "xoa_cac_san_pham":
            raise AttributeError(ten)
        return object.__getattribute__(self, ten)


def _bus_gio(dao):
    bus = GioHangBus.__new__(GioHangBus)
    bus.dao = dao
    return bus


def test_chi_xoa_mon_da_mua_giu_mon_chua_chon():
    dao = FakeGioDaoChonLoc({1: 1, 2: 2})
    kq = _bus_gio(dao).xoa_cac_san_pham(5, [1])
    assert kq["status"] is True
    assert dao.items == {2: 2}, "món chưa chọn phải còn trong giỏ"
    assert dao.da_cap_nhat_tong == 1


def test_fallback_dao_cu_khong_co_xoa_theo_ds():
    dao = FakeGioDaoCu({1: 1, 2: 2})
    kq = _bus_gio(dao).xoa_cac_san_pham(5, [1, 2])
    assert kq["status"] is True
    assert dao.items == {}


def test_xoa_theo_ds_id_rac_bi_tu_choi():
    kq = _bus_gio(FakeGioDaoChonLoc({1: 1})).xoa_cac_san_pham(5, ["abc", None])
    assert kq["status"] is False
