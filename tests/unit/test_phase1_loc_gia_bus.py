"""Unit test Phase 1 — Validate bộ lọc giá ở tầng BUS.

- min/max rỗng được phép.
- min ≤ max bắt buộc.
- Giá âm hoặc không phải số bị từ chối.
- Lọc giá được áp dụng ở backend (authoritative), không tin client.

Mock DAO — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.SanPhamBus import SanPhamBus

class _DaoGia:
    """DAO giả hỗ trợ lọc giá giống SanPhamDao.tim_kiem."""

    def __init__(self):
        self.danh_sach = [
            {"id": 1, "name": "A", "price": 50000, "category_id": 1,
             "is_active": True},
            {"id": 2, "name": "B", "price": 100000, "category_id": 1,
             "is_active": True},
            {"id": 3, "name": "C", "price": 200000, "category_id": 2,
             "is_active": True},
        ]
        self.goi = None

    def lay_tat_ca(self):
        return list(self.danh_sach)

    def tim_kiem(self, tu_khoa, category_id=None, min_price=None,
                 max_price=None):
        self.goi = (tu_khoa, category_id, min_price, max_price)
        ket_qua = []
        for sp in self.danh_sach:
            if not sp.get("is_active", True):
                continue
            if category_id not in (None, "") and sp["category_id"] != int(category_id):
                continue
            if tu_khoa and tu_khoa.lower() not in sp["name"].lower():
                continue
            if min_price is not None and sp["price"] < float(min_price):
                continue
            if max_price is not None and sp["price"] > float(max_price):
                continue
            ket_qua.append(sp)
        return ket_qua

def _bus():
    bus = SanPhamBus.__new__(SanPhamBus)
    bus.dao = _DaoGia()
    return bus

def test_loc_gia_min_max_hop_le():
    bus = _bus()
    kq = bus.tim_kiem_san_pham("", None, 60000, 150000)
    assert kq["status"] is True
    assert {sp["id"] for sp in kq["data"]} == {2}

def test_bo_trong_gia_van_hop_le():
    bus = _bus()
    kq = bus.tim_kiem_san_pham("", None, None, None)
    assert kq["status"] is True
    assert len(kq["data"]) == 3

def test_min_lon_hon_max_bi_tu_choi():
    bus = _bus()
    kq = bus.tim_kiem_san_pham("", None, 200000, 100000)
    assert kq["status"] is False
    assert "lớn hơn" in kq["message"]

def test_gia_am_bi_tu_choi():
    bus = _bus()
    for mn, mx in ((-1, None), (None, -5), (-10, -1)):
        kq = bus.tim_kiem_san_pham("", None, mn, mx)
        assert kq["status"] is False, f"min={mn}, max={mx} phải bị từ chối"

def test_gia_khong_phai_so_bi_tu_choi():
    bus = _bus()
    for mn, mx in (("abc", None), (None, "xyz"), ("1,5", None)):
        kq = bus.tim_kiem_san_pham("", None, mn, mx)
        assert kq["status"] is False, f"min={mn}, max={mx} phải bị từ chối"
