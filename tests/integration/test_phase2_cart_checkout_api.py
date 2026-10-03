# -*- coding: utf-8 -*-
"""Integration Phase 2 — checkout theo món đã chọn + chặn giá mạo (API).

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.Model.User import User
from tests.conftest import (FakeUserDaoBus, FakeSanPhamTimKiemStore,
                            FakeGioHangStore, FakeDonHangCustomerStore)


class FakeDonHangStoreCoGia(FakeDonHangCustomerStore):
    """Fake đơn hàng + nguồn đối chiếu giá/tồn/trạng thái từ DB giả lập."""

    def lay_thong_tin_san_pham(self, product_ids):
        ket_qua = {}
        for pid in (product_ids or []):
            sp = self.san_pham.get(int(pid))
            if sp:
                ket_qua[int(pid)] = {
                    "name": sp.get("name"), "price": float(sp.get("price", 0)),
                    "quantity": int(sp.get("quantity", 0)),
                    "is_active": bool(sp.get("is_active", True)),
                }
        return ket_qua


SAN_PHAM = {
    1: {"id": 1, "name": "SP Shop10", "price": 100000, "quantity": 5,
        "store_id": 10, "category_id": 1, "is_active": True},
    2: {"id": 2, "name": "SP Shop20", "price": 70000, "quantity": 4,
        "store_id": 20, "category_id": 1, "is_active": True},
}


def _dung_cu(customer_client, don_store=None):
    users = {"khachA": User(ma_user=5, ma_nhom_quyen=4, ten_user="Khách A",
                            sdt="0901", dia_chi="HN", cmnd="1",
                            tendangnhap="khachA", mat_khau="123456")}
    thong_tin = {5: {"UserId": 5, "FullName": "Khách A", "Role_Id": 4,
                     "trang_thai": "active"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"khachA": "123456"})
    sp_tim = FakeSanPhamTimKiemStore(san_pham={k: dict(v)
                                              for k, v in SAN_PHAM.items()})
    gio_store = FakeGioHangStore(
        san_pham={pid: {"store_id": sp["store_id"], "price": sp["price"],
                        "name": sp["name"]} for pid, sp in SAN_PHAM.items()})
    don_store = don_store or FakeDonHangStoreCoGia(
        san_pham={k: dict(v) for k, v in SAN_PHAM.items()},
        don_hang={}, next_id=1)
    client = customer_client(user_dao=user_dao, san_pham_store=sp_tim,
                             gio_hang_store=gio_store,
                             don_hang_store=don_store)
    with client.session_transaction() as s:
        s["user_id"] = 5
    return client, don_store, gio_store


def _mon(pid, qty, price, ten):
    return {"ProductId": pid, "ProductName": ten, "Emoji": "📦",
            "Quantity": qty, "UnitPrice": price, "TotalPrice": qty * price}


def _payload(items, payment="COD"):
    sub = sum(it["Quantity"] * it["UnitPrice"] for it in items)
    return {"ReceiverName": "Khách A", "ReceiverPhone": "0901234567",
            "ShippingAddress": "Hà Nội", "PaymentMethod": payment,
            "SubTotal": sub, "ShippingFee": 25000, "Discount": 0,
            "TotalAmount": sub + 25000, "Items": items}


def test_chi_mua_mon_da_chon_giu_mon_chua_chon(customer_client):
    """Phase 2 §4: mua món 1 → món 2 chưa chọn vẫn còn trong giỏ."""
    client, don_store, _ = _dung_cu(customer_client)
    client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1})
    client.post("/api/gio-hang/them", json={"ProductId": 2, "Quantity": 2})
    r = client.post("/api/don-hang/dat-hang", json=_payload(
        [_mon(1, 1, 100000, "SP Shop10")]))
    assert r.json["status"] is True, r.json
    don = list(don_store.don_hang.values())[0]
    assert [it["ProductId"] for it in don["Items"]] == [1]
    gio = client.get("/api/gio-hang/5").json["data"]
    con_lai = {g["ProductId"] for g in gio}
    assert con_lai == {2}, f"món chưa chọn phải còn lại, còn: {gio}"


def test_gia_mao_bi_ghi_de_theo_db(customer_client):
    """Phase 2 §7/§9: UnitPrice=1 → đơn lưu giá DB 100000, tổng 125000."""
    client, don_store, _ = _dung_cu(customer_client)
    r = client.post("/api/don-hang/dat-hang", json=_payload(
        [_mon(1, 1, 1, "SP Shop10")]))
    assert r.json["status"] is True, r.json
    don = list(don_store.don_hang.values())[0]
    assert don["Items"][0]["UnitPrice"] == 100000.0
    assert don["Items"][0]["TotalPrice"] == 100000.0
    assert don["SubTotal"] == 100000.0
    assert don["TotalAmount"] == 125000.0


def test_phuong_thuc_la_bi_tu_choi_va_gio_nguyen(customer_client):
    """Phase 2 §8: ZaloPay → 200 False 'chưa được hỗ trợ', giỏ còn nguyên."""
    client, don_store, gio_store = _dung_cu(customer_client)
    client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1})
    r = client.post("/api/don-hang/dat-hang", json=_payload(
        [_mon(1, 1, 100000, "SP Shop10")], payment="ZaloPay"))
    assert r.status_code == 200
    assert r.json["status"] is False
    assert "không hợp lệ" in r.json["message"]
    assert don_store.don_hang == {}
    assert gio_store.gio[5] == {1: 1}


def test_items_rong_bi_chan(customer_client):
    """Phase 2 §3: Items rỗng (bỏ chọn hết) → chặn, không tạo đơn."""
    client, don_store, _ = _dung_cu(customer_client)
    r = client.post("/api/don-hang/dat-hang", json=_payload([]))
    assert r.json["status"] is False
    assert don_store.don_hang == {}


def test_sp_ngung_ban_bi_tu_choi(customer_client):
    """Phase 2 §7: sản phẩm is_active=False → từ chối 'không còn kinh doanh'."""
    san_pham_an = {k: dict(v) for k, v in SAN_PHAM.items()}
    san_pham_an[1]["is_active"] = False
    don_store = FakeDonHangStoreCoGia(san_pham=san_pham_an, don_hang={},
                                      next_id=1)
    client, don_store, _ = _dung_cu(customer_client, don_store=don_store)
    r = client.post("/api/don-hang/dat-hang", json=_payload(
        [_mon(1, 1, 100000, "SP Shop10")]))
    assert r.json["status"] is False
    assert "không còn kinh doanh" in r.json["message"]
    assert don_store.don_hang == {}
