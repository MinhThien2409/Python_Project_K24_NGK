# -*- coding: utf-8 -*-
"""Integration Phase 3 — customer hủy đơn + thông báo persistent + seller cấm hủy.

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.Model.User import User
from tests.conftest import (FakeUserDaoBus, FakeSanPhamTimKiemStore,
                            FakeGioHangStore, FakeDonHangCustomerStore,
                            FakeDonHangSellerStore)


class FakeDonHangStoreCoThongBao(FakeDonHangCustomerStore):
    """Fake đơn hàng + kho thông báo persistent trong memory."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.thong_bao = []
        self._tb_id = 0

    def tao_thong_bao(self, user_id, noi_dung, order_id=None):
        self._tb_id += 1
        self.thong_bao.append({"ThongBaoId": self._tb_id,
                               "UserId": int(user_id), "NoiDung": noi_dung,
                               "OrderId": order_id, "DaDoc": 0,
                               "CreatedAt": "2026-03-10 10:00:00"})
        return self._tb_id

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
                    tb["ThongBaoId"] != int(thong_bao_id):
                continue
            tb["DaDoc"] = 1
            doi = True
        return doi


def _don(order_id, user_id, status):
    return {"OrderId": order_id, "UserId": user_id, "Status": status,
            "ReceiverName": "Khách A", "ReceiverPhone": "0901234567",
            "ShippingAddress": "Hà Nội", "PaymentMethod": "COD",
            "SubTotal": 100000, "ShippingFee": 25000, "DiscountAmount": 0,
            "TotalAmount": 125000, "CreatedAt": "2026-03-10 10:00:00",
            "Items": []}


def _dung_cu(customer_client, don_hang):
    users = {"khachA": User(ma_user=5, ma_nhom_quyen=4, ten_user="Khách A",
                            sdt="0901", dia_chi="HN", cmnd="1",
                            tendangnhap="khachA", mat_khau="123456")}
    thong_tin = {5: {"UserId": 5, "FullName": "Khách A", "Role_Id": 4,
                     "trang_thai": "active"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"khachA": "123456"})
    don_store = FakeDonHangStoreCoThongBao(san_pham={}, don_hang=don_hang,
                                           next_id=99)
    client = customer_client(user_dao=user_dao,
                             san_pham_store=FakeSanPhamTimKiemStore({}),
                             gio_hang_store=FakeGioHangStore({}),
                             don_hang_store=don_store)
    with client.session_transaction() as s:
        s["user_id"] = 5
    return client, don_store


def _trang_thai(client, order_id):
    resp = client.get("/api/don-hang/cua-toi/5")
    for don in resp.get_json()["data"]:
        if don["OrderId"] == order_id:
            return don["Status"]
    return None


# ── Customer hủy qua API ─────────────────────────────────────────────────

def test_huy_pending_ok_va_thong_bao_persistent(customer_client):
    """Phase 3 §2+§5: hủy ok, thông báo lưu lại sau reload danh sách."""
    client, store = _dung_cu(customer_client, {1: _don(1, 5, "Pending")})
    resp = client.put("/api/don-hang/1/huy")
    assert resp.status_code == 200
    assert resp.get_json()["status"] is True
    assert _trang_thai(client, 1) == "Cancelled"
    tb = client.get("/api/thong-bao/cua-toi").get_json()
    assert tb["status"] is True
    assert len(tb["data"]) == 1
    assert "#1" in tb["data"][0]["NoiDung"]
    assert tb["data"][0]["DaDoc"] == 0
    assert len(store.thong_bao) == 1  # persistent trong kho


def test_huy_lai_don_da_huy_bi_tu_choi(customer_client):
    """Phase 3 §2: hủy lần 2 bị từ chối, chỉ 1 thông báo được tạo."""
    client, store = _dung_cu(customer_client, {1: _don(1, 5, "Pending")})
    assert client.put("/api/don-hang/1/huy").get_json()["status"] is True
    lan2 = client.put("/api/don-hang/1/huy").get_json()
    assert lan2["status"] is False
    assert len(store.thong_bao) == 1


@pytest.mark.parametrize("status", ["Confirmed", "Shipping", "Completed"])
def test_huy_don_da_xu_ly_bi_tu_choi(customer_client, status):
    """Phase 3 §2: Confirmed/Shipping/Completed đều không hủy được."""
    client, _ = _dung_cu(customer_client, {1: _don(1, 5, status)})
    kq = client.put("/api/don-hang/1/huy").get_json()
    assert kq["status"] is False
    assert _trang_thai(client, 1) == status


def test_trang_thai_client_gui_len_bi_bo_qua(customer_client):
    """Phase 3 §6: body {status} mạo không ảnh hưởng — luôn Cancelled."""
    client, _ = _dung_cu(customer_client, {1: _don(1, 5, "Pending")})
    resp = client.put("/api/don-hang/1/huy", json={"status": "Confirmed"})
    assert resp.get_json()["status"] is True
    assert _trang_thai(client, 1) == "Cancelled"


def test_huy_don_nguoi_khac_403(customer_client):
    """Phase 3 §2+§6: hủy đơn của khách khác → 403."""
    client, _ = _dung_cu(customer_client, {1: _don(1, 9, "Pending")})
    resp = client.put("/api/don-hang/1/huy")
    assert resp.status_code == 403
    assert resp.get_json()["status"] is False


def test_huy_don_khong_ton_tai(customer_client):
    """Phase 3 §2: đơn không tồn tại báo lỗi, không crash."""
    client, _ = _dung_cu(customer_client, {})
    kq = client.put("/api/don-hang/999/huy").get_json()
    assert kq["status"] is False


def test_chua_dang_nhap_huy_403_va_thong_bao_403(customer_client):
    """Phase 3 §6: chưa đăng nhập không hủy / không đọc thông báo."""
    client, _ = _dung_cu(customer_client, {1: _don(1, 5, "Pending")})
    with client.session_transaction() as s:
        s.clear()
    assert client.put("/api/don-hang/1/huy").status_code == 403
    assert client.get("/api/thong-bao/cua-toi").status_code == 403
    assert client.post("/api/thong-bao/danh-dau-da-doc",
                       json={}).status_code == 403


def test_danh_dau_da_doc_xoa_badge(customer_client):
    """Phase 3 §5: đánh dấu đã đọc hết → lần đọc sau DaDoc=1."""
    client, _ = _dung_cu(customer_client, {1: _don(1, 5, "Pending")})
    client.put("/api/don-hang/1/huy")
    kq = client.post("/api/thong-bao/danh-dau-da-doc", json={}).get_json()
    assert kq["status"] is True
    tb = client.get("/api/thong-bao/cua-toi").get_json()["data"]
    assert all(m["DaDoc"] == 1 for m in tb)


def test_danh_dau_mot_thong_bao(customer_client):
    """Phase 3 §5: đánh dấu 1 thông báo theo id, body rỗng = tất cả."""
    client, _ = _dung_cu(customer_client, {1: _don(1, 5, "Pending")})
    client.put("/api/don-hang/1/huy")
    tb_id = client.get("/api/thong-bao/cua-toi").get_json()["data"][0]["ThongBaoId"]
    kq = client.post("/api/thong-bao/danh-dau-da-doc",
                     json={"thong_bao_id": tb_id}).get_json()
    assert kq["status"] is True


# ── Seller cấm hủy sau Confirmed qua API ─────────────────────────────────

def _dung_cu_seller(seller_client, status):
    from tests.conftest import FakeShopStore
    users = {"sellerA": User(ma_user=3, ma_nhom_quyen=3, ten_user="Seller A",
                              sdt="0901", dia_chi="HN", cmnd="1",
                              tendangnhap="sellerA", mat_khau="123456")}
    thong_tin = {3: {"UserId": 3, "FullName": "Seller A", "Role_Id": 3,
                      "trang_thai": "active"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"sellerA": "123456"})
    don_store = FakeDonHangSellerStore(
        don_hang={1: {"OrderId": 1, "Status": status, "TotalAmount": 200000}},
        thuoc={1: {10}})
    shop_store = FakeShopStore(stores={
        10: {"StoreId": 10, "UserId": 3, "StoreName": "Shop A"}})
    client = seller_client(user_dao=user_dao, don_hang_store=don_store,
                           shop_store=shop_store)
    with client.session_transaction() as s:
        s["user_id"] = 3
    return client, don_store


def test_seller_huy_confirmed_bi_tu_choi(seller_client):
    """Phase 3 §3: seller hủy đơn Confirmed qua API bị từ chối."""
    client, _ = _dung_cu_seller(seller_client, "Confirmed")
    kq = client.put("/api/seller/don-hang/1/trang-thai",
                    json={"status": "Cancelled"}).get_json()
    assert kq["status"] is False


def test_seller_huy_pending_ok(seller_client):
    """Phase 3 §3: seller hủy đơn Pending qua API thành công."""
    client, store = _dung_cu_seller(seller_client, "Pending")
    kq = client.put("/api/seller/don-hang/1/trang-thai",
                    json={"status": "Cancelled"}).get_json()
    assert kq["status"] is True
    assert store.don_hang[1]["Status"] == "Cancelled"
