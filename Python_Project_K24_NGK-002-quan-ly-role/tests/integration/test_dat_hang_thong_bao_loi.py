"""Integration test thong bao loi nghiep vu — 011 US3 T013.

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.Model.User import User
from tests.conftest import (FakeUserDaoBus, FakeSanPhamTimKiemStore,
                            FakeGioHangStore, FakeDonHangCustomerStore)


def _dung_cu(customer_client, san_pham_extra=None):
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
        1: {"id": 1, "name": "SP Còn hàng", "price": 100000, "quantity": 5,
            "store_id": 10, "category_id": 1, "is_active": True},
        2: {"id": 2, "name": "SP Hết kho", "price": 50000, "quantity": 1,
            "store_id": 10, "category_id": 1, "is_active": True},
    }
    if san_pham_extra:
        san_pham.update(san_pham_extra)
    sp_tim = FakeSanPhamTimKiemStore(san_pham=dict(san_pham))
    gio_store = FakeGioHangStore(
        san_pham={pid: {"store_id": sp["store_id"], "price": sp["price"],
                        "name": sp["name"]} for pid, sp in san_pham.items()})
    don_store = FakeDonHangCustomerStore(san_pham=dict(san_pham))
    client = customer_client(user_dao=user_dao, san_pham_store=sp_tim,
                             gio_hang_store=gio_store,
                             don_hang_store=don_store)
    return client, don_store


def _login(client, uid=5):
    with client.session_transaction() as s:
        s["user_id"] = uid


def _payload(items):
    sub = sum(it["Quantity"] * it["UnitPrice"] for it in items)
    return {"ReceiverName": "Khách A", "ReceiverPhone": "0901234567",
            "ShippingAddress": "Hà Nội", "PaymentMethod": "COD",
            "SubTotal": sub, "ShippingFee": 25000, "Discount": 0,
            "TotalAmount": sub + 25000, "Items": items}


def _mon(pid, qty, price, ten):
    return {"ProductId": pid, "ProductName": ten, "Emoji": "📦",
            "Quantity": qty, "UnitPrice": price, "TotalPrice": qty * price}


def test_het_hang_bao_cu_the_ten_va_so_luong(customer_client):
    """US3: hết hàng → message cụ thể có tên SP + số còn lại, KHÔNG 'Hệ thống bận'."""
    client, _ = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(2, 5, 50000, "SP Hết kho")]))  # kho còn 1
    assert r.json["status"] is False
    assert "SP Hết kho" in r.json["message"]
    assert "chỉ còn 1 sản phẩm" in r.json["message"]
    assert "Hệ thống bận" not in r.json["message"]


def test_sp_khong_ton_tai_bao_cu_the(customer_client):
    """US3: sản phẩm không tồn tại → message 'không tìm thấy' cụ thể."""
    client, _ = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(999, 1, 10000, "SP Mất tích")]))
    assert r.json["status"] is False
    assert "không tìm thấy" in r.json["message"].lower()
    assert "Hệ thống bận" not in r.json["message"]


def test_thieu_thong_tin_nguoi_nhan(customer_client):
    """US3: thiếu địa chỉ → message đầy đủ thông tin, không chung chung."""
    client, _ = _dung_cu(customer_client)
    _login(client)
    payload = _payload([_mon(1, 1, 100000, "SP Còn hàng")])
    payload["ShippingAddress"] = ""
    r = client.post("/api/don-hang/dat-hang", json=payload)
    assert r.json["status"] is False
    assert "đầy đủ thông tin" in r.json["message"]


def test_dau_vao_hop_le_khong_bao_he_thong_ban(customer_client):
    """US3: đầu vào hợp lệ → đặt thành công, KHÔNG bao giờ thấy 'Hệ thống bận'."""
    client, _ = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/don-hang/dat-hang", json=_payload([
        _mon(1, 1, 100000, "SP Còn hàng")]))
    assert r.json["status"] is True
    assert "Hệ thống bận" not in r.json["message"]
    assert "1 đơn hàng đã được tạo" in r.json["message"]