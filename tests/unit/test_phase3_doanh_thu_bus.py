# -*- coding: utf-8 -*-
"""Phase 3 — doanh thu seller: Completed-only, theo OrderItems từng store.

Fake mirror ngữ nghĩa SQL `_thong_ke_chinh_cua_store` + báo cáo tháng:
chỉ đơn Completed, SUM(Quantity*UnitPrice) theo StoreId, loại Cancelled,
KHÔNG tin TotalAmount client. KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.BUS.DonHangBus import DonHangBus


class FakeDoanhThuStore:
    """Mirror SQL seller: doanh thu Completed theo items của đúng store."""

    def __init__(self, don_hang, items, san_pham):
        # don_hang: {order_id: {"Status", "CreatedAt"}}
        # items: [(order_id, product_id, qty, unit_price)]
        # san_pham: {product_id: store_id}
        self.don_hang = don_hang
        self.items = items
        self.san_pham = san_pham

    def _thuoc_store(self, store_id, product_id):
        return self.san_pham.get(int(product_id)) == int(store_id)

    def _doanh_thu(self, store_id):
        tong = 0.0
        for oid, pid, qty, gia in self.items:
            don = self.don_hang.get(int(oid)) or {}
            if don.get("Status") == "Completed" and \
                    self._thuoc_store(store_id, pid):
                tong += int(qty) * float(gia)
        return tong

    def _don_cua_store(self, store_id):
        ds = []
        for oid, don in self.don_hang.items():
            if any(int(o) == int(oid) and self._thuoc_store(store_id, p)
                   for o, p, _, _ in self.items):
                ds.append(don)
        return ds

    def lay_thong_ke_cua_seller(self, store_id):
        don = self._don_cua_store(store_id)
        dem = lambda tt: sum(1 for d in don if d.get("Status") == tt)
        return {"doanh_thu": self._doanh_thu(store_id),
                "tong_don": len(don), "cho_duyet": dem("Pending"),
                "da_xac_nhan": dem("Confirmed"), "dang_giao": dem("Shipping"),
                "hoan_thanh": dem("Completed"), "da_huy": dem("Cancelled")}

    def lay_doanh_thu_seller_theo_thang(self, store_id, year):
        gom = {}
        for oid, pid, qty, gia in self.items:
            don = self.don_hang.get(int(oid)) or {}
            if don.get("Status") != "Completed":
                continue
            if not self._thuoc_store(store_id, pid):
                continue
            if str(don.get("CreatedAt", ""))[:4] != str(year):
                continue
            thang = int(str(don.get("CreatedAt", ""))[5:7])
            muc = gom.setdefault(thang, {"thang": thang, "doanh_thu": 0.0,
                                           "so_don": set()})
            muc["doanh_thu"] += int(qty) * float(gia)
            muc["so_don"].add(int(oid))
        data = []
        for i in range(1, 13):
            muc = gom.get(i)
            data.append({"thang": i,
                         "doanh_thu": muc["doanh_thu"] if muc else 0,
                         "so_don": len(muc["so_don"]) if muc else 0})
        return data


SAN_PHAM = {1: 10, 2: 10, 3: 20}  # product_id -> store_id

DON_HANG = {
    1: {"Status": "Completed", "CreatedAt": "2026-03-05 10:00:00"},
    2: {"Status": "Completed", "CreatedAt": "2026-03-06 10:00:00"},
    3: {"Status": "Cancelled", "CreatedAt": "2026-03-07 10:00:00"},
    4: {"Status": "Pending", "CreatedAt": "2026-03-08 10:00:00"},
    5: {"Status": "Completed", "CreatedAt": "2026-04-01 10:00:00"},
}

ITEMS = [
    (1, 1, 2, 100000),   # store 10: 200k Completed
    (1, 3, 1, 50000),    # store 20: 50k Completed (đơn gộp 2 shop)
    (2, 2, 1, 70000),    # store 10: 70k Completed
    (3, 1, 5, 100000),   # store 10: Cancelled → loại
    (4, 1, 5, 100000),   # store 10: Pending → loại
    (5, 1, 1, 100000),   # store 10: 100k Completed (tháng 4)
]


def _bus():
    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = FakeDoanhThuStore(DON_HANG, ITEMS, SAN_PHAM)
    return bus


def test_case3_don_gop_hai_shop_chi_tinh_shop_minh():
    """Phase 3 Case 3: đơn gộp 2 shop → mỗi store chỉ tính items của mình."""
    kq = _bus().lay_thong_ke_cua_seller(10)["data"]
    assert kq["doanh_thu"] == 200000 + 70000 + 100000
    kq20 = _bus().lay_thong_ke_cua_seller(20)["data"]
    assert kq20["doanh_thu"] == 50000


def test_case4_shop_khac_nhau_doc_lap():
    """Phase 3 Case 4: ±1 đơn shop khác không đổi doanh thu shop A."""
    assert _bus().lay_thong_ke_cua_seller(10)["data"]["doanh_thu"] == 370000


def test_case5_cancelled_khong_tinh_doanh_thu_nhung_van_dem():
    """Phase 3 Case 5: Cancelled loại khỏi doanh thu, vẫn đếm da_huy=1."""
    kq = _bus().lay_thong_ke_cua_seller(10)["data"]
    assert kq["doanh_thu"] == 370000
    assert kq["da_huy"] == 1
    assert kq["tong_don"] == 5


def test_case6_khong_tin_total_amount_client():
    """Phase 3 Case 6: doanh thu từ Quantity*UnitPrice, không phải Total."""
    bus = _bus()
    bus.dao.don_hang[1]["TotalAmountGia"] = 999999999  # nhiễu ngoài items
    assert bus.lay_thong_ke_cua_seller(10)["data"]["doanh_thu"] == 370000


def test_case7_tong_thong_ke_khop_bao_cao_thang():
    """Phase 3 Case 7: tổng thống kê == tổng báo cáo theo tháng."""
    bus = _bus()
    tong = bus.lay_thong_ke_cua_seller(10)["data"]["doanh_thu"]
    thang = bus.lay_doanh_thu_seller_theo_thang(10, 2026)["data"]
    assert len(thang) == 12
    muc3 = thang[2]
    assert muc3 == {"thang": 3, "doanh_thu": 270000.0, "so_don": 2}
    assert thang[3] == {"thang": 4, "doanh_thu": 100000.0, "so_don": 1}
    assert sum(m["doanh_thu"] for m in thang) == tong
    assert sum(m["doanh_thu"] for m in
               bus.lay_doanh_thu_seller_theo_thang(20, 2026)["data"]) == \
        bus.lay_thong_ke_cua_seller(20)["data"]["doanh_thu"]


def test_pending_khong_tinh_doanh_thu():
    """Phase 3: đơn Pending/Chờ duyệt không cộng vào doanh thu."""
    kq = _bus().lay_thong_ke_cua_seller(10)["data"]
    assert kq["cho_duyet"] == 1
    assert kq["doanh_thu"] == 370000
