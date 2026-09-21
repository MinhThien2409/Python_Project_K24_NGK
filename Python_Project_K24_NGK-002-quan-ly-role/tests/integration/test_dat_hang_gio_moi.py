# -*- coding: utf-8 -*-
"""Integration test đặt hàng khách CHƯA có giỏ (016 US4, T022).

- Login Customer chưa từng có giỏ → thêm hàng (giỏ mới tự tạo) → POST
  /api/don-hang/dat-hang → 200 status:true; giỏ mới bị xóa sau đặt.
- Validate: số điện thoại người nhận không hợp lệ → status:false
  "Số điện thoại người nhận không hợp lệ!"; thiếu thông tin → status:false.

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.Model.User import User
from tests.conftest import (FakeUserDaoBus, FakeSanPhamTimKiemStore,
                            FakeGioHangStore, FakeDonHangCustomerStore)


def _dung_cu(customer_client):
    """Khách A (id 5) chưa có giỏ: FakeGioHangStore khởi tạo rỗng."""
    users = {
        "khachA": User(ma_user=5, ma_nhom_quyen=4, ten_user="Khách A",
                       sdt="0901", dia_chi="HN", cmnd="1",
                       tendangnhap="khachA", mat_khau="123456"),
    }
    thong_tin = {5: {"UserId": 5, "FullName": "Khách A", "Role_Id": 4,
                     "trang_thai": "active"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"khachA": "123456"})
    san_pham = {
        1: {"id": 1, "name": "Hoa Hồng", "price": 100000, "quantity": 5,
            "store_id": 10, "category_id": 1, "is_active": True},
    }
    sp_tim = FakeSanPhamTimKiemStore(san_pham=dict(san_pham))
    gio_store = FakeGioHangStore(
        san_pham={pid: {"store_id": sp["store_id"], "price": sp["price"],
                        "name": sp["name"]} for pid, sp in san_pham.items()})
    don_store = FakeDonHangCustomerStore(san_pham=dict(san_pham),
                                         don_hang={}, next_id=1)
    client = customer_client(user_dao=user_dao, san_pham_store=sp_tim,
                             gio_hang_store=gio_store,
                             don_hang_store=don_store)
    assert gio_store.gio == {}, "Fixture phải bắt đầu KHÔNG có giỏ (khách mới)"
    return client, don_store, gio_store


def _login(client, uid=5):
    with client.session_transaction() as s:
        s["user_id"] = uid


def _payload(**kw):
    data = {"ReceiverName": "Khách A", "ReceiverPhone": "0901234567",
            "ShippingAddress": "Hà Nội", "PaymentMethod": "COD",
            "SubTotal": 100000, "ShippingFee": 25000, "Discount": 0,
            "TotalAmount": 125000,
            "Items": [{"ProductId": 1, "ProductName": "Hoa Hồng", "Emoji": "🌹",
                       "Quantity": 1, "UnitPrice": 100000, "TotalPrice": 100000}]}
    data.update(kw)
    return data


# ── Khách chưa có giỏ: thêm hàng → đặt → giỏ mới tự tạo rồi xóa ──
def test_khach_chua_co_gio_dat_hang_thanh_cong(customer_client):
    client, don_store, gio_store = _dung_cu(customer_client)
    _login(client)

    # Thêm hàng vào giỏ (chưa tồn tại giỏ trước đó)
    r = client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1})
    assert r.json["status"] is True

    # Giỏ hiện có 1 món
    gio = client.get("/api/gio-hang/5").json["data"]
    assert len(gio) == 1

    # Đặt hàng thành công
    r = client.post("/api/don-hang/dat-hang", json=_payload())
    assert r.json["status"] is True, r.json
    assert len(r.json["data"]["order_ids"]) == 1

    # Đơn thật trong "DB" và giỏ đã rỗng sau đặt
    assert len(don_store.don_hang) == 1
    gio = client.get("/api/gio-hang/5").json["data"]
    assert gio == []


def test_khach_chua_co_gio_dang_ky_roi_moi_dat(customer_client):
    """Đặt 2 lần liên tiếp (giỏ mới sinh ra giữa 2 lần) — không crash."""
    client, don_store, _ = _dung_cu(customer_client)
    _login(client)

    client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1})
    r1 = client.post("/api/don-hang/dat-hang", json=_payload())
    assert r1.json["status"] is True

    client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 2})
    r2 = client.post("/api/don-hang/dat-hang", json=_payload(
        SubTotal=200000, TotalAmount=225000,
        Items=[{"ProductId": 1, "ProductName": "Hoa Hồng", "Emoji": "🌹",
                "Quantity": 2, "UnitPrice": 100000, "TotalPrice": 200000}]))
    assert r2.json["status"] is True, r2.json
    assert len(don_store.don_hang) == 2


# ── Validate payload ──
def test_sdt_khong_hop_le_bi_tu_choi(customer_client):
    client, don_store, _ = _dung_cu(customer_client)
    _login(client)
    client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1})

    r = client.post("/api/don-hang/dat-hang", json=_payload(ReceiverPhone="abc"))
    assert r.status_code == 200
    assert r.json["status"] is False
    assert r.json["message"] == "Số điện thoại người nhận không hợp lệ!"
    assert len(don_store.don_hang) == 0  # không đơn nào bị tạo


def test_thieu_ten_nguoi_nhan_bi_tu_choi(customer_client):
    client, don_store, _ = _dung_cu(customer_client)
    _login(client)
    client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1})

    r = client.post("/api/don-hang/dat-hang", json=_payload(ReceiverName=""))
    assert r.json["status"] is False
    assert len(don_store.don_hang) == 0


def test_khach_chua_dang_nhap_dat_hang_403(customer_client):
    client, _, _ = _dung_cu(customer_client)
    # Không login
    r = client.post("/api/don-hang/dat-hang", json=_payload())
    assert r.status_code == 403