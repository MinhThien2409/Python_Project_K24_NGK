# -*- coding: utf-8 -*-
"""Phase 3 — BUS: customer tự hủy đơn (Pending→Cancelled) + seller cấm hủy sau Confirmed.

Fake/mock in-memory — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.DonHangBus import DonHangBus
from tests.conftest import MockDonHangCustomerDao, MockDonHangSellerDao


class FakeHuyDonDao(MockDonHangCustomerDao):
    """Mock đơn hàng + kho thông báo, mô phỏng DAO đổi Pending→Cancelled."""

    def __init__(self, don_hang=None, chi_tiet=None, tao_ok=True):
        super().__init__(don_hang=don_hang, chi_tiet=chi_tiet, ket_qua_tao=1)
        self.cap_nhat_ok = True
        self.so_lan_cap_nhat = 0
        self.lan_cap_nhat_cuoi = None
        self.thong_bao = []
        self.tao_ok = tao_ok

    def cap_nhat_trang_thai(self, order_id, trang_thai_moi):
        self.so_lan_cap_nhat += 1
        self.lan_cap_nhat_cuoi = (int(order_id), trang_thai_moi)
        don = (self.don_hang or {}).get(int(order_id))
        if don:
            don["Status"] = trang_thai_moi
        return self.cap_nhat_ok

    def tao_thong_bao(self, user_id, noi_dung, order_id=None):
        if not self.tao_ok:
            raise RuntimeError("kho thông báo lỗi")
        self.thong_bao.append({"UserId": int(user_id), "NoiDung": noi_dung,
                               "OrderId": order_id, "DaDoc": 0})
        return len(self.thong_bao)

    def lay_thong_bao_cua_user(self, user_id, gioi_han=20):
        ds = [dict(tb) for tb in self.thong_bao
              if tb["UserId"] == int(user_id)]
        return ds[:int(gioi_han)]

    def danh_dau_thong_bao_da_doc(self, user_id, thong_bao_id=None):
        doi = False
        for tb in self.thong_bao:
            if tb["UserId"] != int(user_id):
                continue
            if thong_bao_id is not None and \
                    tb.get("ThongBaoId", len(self.thong_bao)) != int(thong_bao_id):
                continue
            tb["DaDoc"] = 1
            doi = True
        return doi


def _don(order_id, user_id, status):
    return {"OrderId": order_id, "UserId": user_id, "Status": status,
            "ReceiverName": "Khách A", "ReceiverPhone": "0901234567",
            "ShippingAddress": "Hà Nội", "PaymentMethod": "COD",
            "SubTotal": 100000, "ShippingFee": 25000, "DiscountAmount": 0,
            "TotalAmount": 125000}


def _bus_customer(don_hang, tao_ok=True):
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = FakeHuyDonDao(don_hang=don_hang, tao_ok=tao_ok)
    return bus


def _bus_seller(trang_thai, thuoc_store=True):
    bus = DonHangBus()
    bus.dao = MockDonHangSellerDao(trang_thai=trang_thai,
                                   thuoc_store=thuoc_store)
    return bus


# ── Customer tự hủy ──────────────────────────────────────────────────────

def test_customer_huy_pending_ok_va_co_thong_bao():
    """Phase 3 §2: Pending→Cancelled ok, ghi 1 lần, có thông báo."""
    bus = _bus_customer({1: _don(1, 5, "Pending")})
    kq = bus.huy_don_hang_cua_customer(5, 1)
    assert kq["status"] is True
    assert "hủy" in kq["message"]
    assert bus.dao.so_lan_cap_nhat == 1
    assert bus.dao.lan_cap_nhat_cuoi == (1, "Cancelled")
    assert len(bus.dao.thong_bao) == 1
    assert bus.dao.thong_bao[0]["UserId"] == 5
    assert "#1" in bus.dao.thong_bao[0]["NoiDung"]


def test_customer_huy_hai_lan_chi_cap_nhat_mot_lan():
    """Phase 3 §2: hủy lại đơn đã Cancelled bị từ chối, không ghi DB lần 2."""
    bus = _bus_customer({1: _don(1, 5, "Pending")})
    assert bus.huy_don_hang_cua_customer(5, 1)["status"] is True
    lan2 = bus.huy_don_hang_cua_customer(5, 1)
    assert lan2["status"] is False
    assert "đã được hủy" in lan2["message"]
    assert bus.dao.so_lan_cap_nhat == 1


def test_customer_huy_confirmed_bi_tu_choi():
    """Phase 3 §2: đã Confirmed thì customer không được hủy."""
    bus = _bus_customer({1: _don(1, 5, "Confirmed")})
    kq = bus.huy_don_hang_cua_customer(5, 1)
    assert kq["status"] is False
    assert "xác nhận" in kq["message"]
    assert bus.dao.so_lan_cap_nhat == 0


def test_customer_huy_shipping_bi_tu_choi():
    """Phase 3 §2: đang Shipping thì customer không được hủy."""
    bus = _bus_customer({1: _don(1, 5, "Shipping")})
    kq = bus.huy_don_hang_cua_customer(5, 1)
    assert kq["status"] is False
    assert bus.dao.so_lan_cap_nhat == 0


def test_customer_huy_completed_bi_tu_choi():
    """Phase 3 §2: đã Completed thì customer không được hủy."""
    bus = _bus_customer({1: _don(1, 5, "Completed")})
    kq = bus.huy_don_hang_cua_customer(5, 1)
    assert kq["status"] is False
    assert "hoàn thành" in kq["message"]
    assert bus.dao.so_lan_cap_nhat == 0


def test_customer_huy_don_nguoi_khac_bi_tu_choi():
    """Phase 3 §2: không được hủy đơn của khách khác."""
    bus = _bus_customer({1: _don(1, 9, "Pending")})
    kq = bus.huy_don_hang_cua_customer(5, 1)
    assert kq["status"] is False
    assert "không có quyền" in kq["message"]
    assert bus.dao.so_lan_cap_nhat == 0


def test_customer_huy_don_khong_ton_tai():
    """Phase 3 §2: đơn không tồn tại / mã sai báo không tìm thấy."""
    bus = _bus_customer({})
    assert bus.huy_don_hang_cua_customer(5, 999)["status"] is False
    assert bus.huy_don_hang_cua_customer(5, "abc")["status"] is False
    assert bus.dao.so_lan_cap_nhat == 0


def test_customer_chua_dang_nhap_khong_huy_duoc():
    """Phase 3 §2: thiếu user_id thì từ chối xác thực."""
    bus = _bus_customer({1: _don(1, 5, "Pending")})
    kq = bus.huy_don_hang_cua_customer(None, 1)
    assert kq["status"] is False
    assert bus.dao.so_lan_cap_nhat == 0


def test_thong_bao_loi_khong_hong_huy_don():
    """Phase 3 §5: kho thông báo lỗi vẫn hủy đơn thành công."""
    bus = _bus_customer({1: _don(1, 5, "Pending")}, tao_ok=False)
    kq = bus.huy_don_hang_cua_customer(5, 1)
    assert kq["status"] is True


def test_dao_chua_co_thong_bao_van_huy_ok():
    """Phase 3 §5: DAO thiếu API thông báo vẫn hủy đơn bình thường."""
    class DaoKhongThongBao(MockDonHangCustomerDao):
        def cap_nhat_trang_thai(self, order_id, trang_thai_moi):
            self.don_hang[int(order_id)]["Status"] = trang_thai_moi
            return True
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = DaoKhongThongBao(
        don_hang={1: _don(1, 5, "Pending")}, chi_tiet={}, ket_qua_tao=1)
    assert bus.huy_don_hang_cua_customer(5, 1)["status"] is True
    assert bus.lay_thong_bao_cua_user(5) == {"status": True, "data": []}


def test_lay_va_danh_dau_thong_bao():
    """Phase 3 §5: đọc + đánh dấu đã đọc thông báo đã lưu."""
    bus = _bus_customer({1: _don(1, 5, "Pending")})
    bus.huy_don_hang_cua_customer(5, 1)
    ds = bus.lay_thong_bao_cua_user(5)
    assert ds["status"] is True and len(ds["data"]) == 1
    assert bus.danh_dau_thong_bao_da_doc(None)["status"] is False
    assert bus.danh_dau_thong_bao_da_doc(5, "xyz")["status"] is False


# ── Seller cấm hủy sau Confirmed ─────────────────────────────────────────

def test_seller_huy_pending_ok():
    """Phase 3 §3: seller được hủy đơn đang Chờ duyệt."""
    bus = _bus_seller(trang_thai={1: "Pending"})
    kq = bus.cap_nhat_trang_thai_cua_seller(3, 10, 1, "Cancelled")
    assert kq["status"] is True


def test_seller_huy_confirmed_bi_tu_choi():
    """Phase 3 §3: seller KHÔNG được hủy đơn đã Confirmed."""
    bus = _bus_seller(trang_thai={1: "Confirmed"})
    kq = bus.cap_nhat_trang_thai_cua_seller(3, 10, 1, "Cancelled")
    assert kq["status"] is False
    assert "Chờ duyệt" in kq["message"]


def test_seller_huy_shipping_bi_tu_choi():
    """Phase 3 §3: seller KHÔNG được hủy đơn đang Shipping."""
    bus = _bus_seller(trang_thai={1: "Shipping"})
    kq = bus.cap_nhat_trang_thai_cua_seller(3, 10, 1, "Cancelled")
    assert kq["status"] is False


def test_seller_huy_completed_giu_thong_bao_terminal():
    """Phase 3 §3: Completed→Cancelled vẫn bị chặn như cũ."""
    bus = _bus_seller(trang_thai={1: "Completed"})
    kq = bus.cap_nhat_trang_thai_cua_seller(3, 10, 1, "Cancelled")
    assert kq["status"] is False
    assert "cuối" in kq["message"]


def test_seller_luong_thuong_khong_doi():
    """Phase 3 §3: các bước xuôi Pending→Confirmed→Shipping→Completed còn chạy."""
    assert _bus_seller({1: "Pending"}).cap_nhat_trang_thai_cua_seller(
        3, 10, 1, "Confirmed")["status"] is True
    assert _bus_seller({1: "Confirmed"}).cap_nhat_trang_thai_cua_seller(
        3, 10, 1, "Shipping")["status"] is True
    assert _bus_seller({1: "Shipping"}).cap_nhat_trang_thai_cua_seller(
        3, 10, 1, "Completed")["status"] is True
