"""Unit test luật chuyển trạng thái DonHang về BUS — 007 T026.

Pending→Shipping→Completed + Cancelled hoàn kho, giữ nguyên hành vi.
KHÔNG chạm DB thật: dùng FakeDonHangDao (giống conftest).

Trước T039: FAIL (BUS không validate luồng, Completed/Cancelled
không bị chặn, luật nằm ở DAO).
Sau T039: PASS (BUS validate qua lay_trang_thai + LUONG).
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from back_end.BUS.DonHangBus import DonHangBus


class FakeDonHangDao:
    """Fake DAO tối thiểu cho luồng trạng thái (giống MockDonHangSellerDao)."""

    def __init__(self, trang_thai=None):
        self.trang_thai = dict(trang_thai or {})
        self.goi_cap_nhat = []

    def lay_trang_thai(self, order_id):
        return self.trang_thai.get(int(order_id))

    def don_thuoc_store(self, order_id, store_id):
        return True

    def cap_nhat_trang_thai(self, order_id, new_status):
        self.goi_cap_nhat.append((int(order_id), new_status))
        self.trang_thai[int(order_id)] = new_status
        return True


def _bus(trang_thai):
    bus = DonHangBus()
    bus.dao = FakeDonHangDao(trang_thai)
    return bus


def test_luong_pending_shipping_completed_ok():
    bus = _bus({1: "Pending"})
    assert _bus({1: "Pending"}).thay_doi_trang_thai(1, "Cancelled")["status"] is True
    b2 = _bus({2: "Pending"})
    assert b2.thay_doi_trang_thai(2, "Confirmed")["status"] is True
    b3 = _bus({3: "Confirmed"})
    assert b3.thay_doi_trang_thai(3, "Shipping")["status"] is True
    b4 = _bus({4: "Shipping"})
    r = b4.thay_doi_trang_thai(4, "Completed")
    assert r["status"] is True
    assert (4, "Completed") in b4.dao.goi_cap_nhat


def test_nhay_coc_pending_sang_completed_bi_chan():
    bus = _bus({1: "Pending"})
    r = bus.thay_doi_trang_thai(1, "Completed")
    assert r["status"] is False
    assert bus.dao.goi_cap_nhat == [], "Luồng sai không được chạm DAO"


def test_trang_thai_cuoi_khong_doi_duoc():
    for cuoi in ("Completed", "Cancelled"):
        bus = _bus({9: cuoi})
        r = bus.thay_doi_trang_thai(9, "Shipping")
        assert r["status"] is False, f"{cuoi} phải là trạng thái cuối"
        assert bus.dao.goi_cap_nhat == []


def test_trang_thai_la_bi_chan_khong_cham_dao():
    bus = _bus({1: "Pending"})
    r = bus.thay_doi_trang_thai(1, "DangGiao")
    assert r["status"] is False
    assert bus.dao.goi_cap_nhat == []


def test_don_khong_ton_tai_bao_loi_viet():
    bus = _bus({})
    r = bus.thay_doi_trang_thai(999, "Shipping")
    assert r["status"] is False
    assert "message" in r and isinstance(r["message"], str) and len(r["message"]) > 0
    assert "Traceback" not in r["message"]


def test_cancelled_hoan_kho_giu_hanh_vi():
    """Cancelled từ Pending/Shipping được phép (hoàn kho ở DAO executor)."""
    for hien in ("Pending", "Confirmed", "Shipping"):
        bus = _bus({5: hien})
        r = bus.thay_doi_trang_thai(5, "Cancelled")
        assert r["status"] is True, f"{hien}→Cancelled phải OK"
