# -*- coding: utf-8 -*-
"""Phase 1 — kiểm thử biên API cho dữ liệu đầu vào không hợp lệ.

Nguyên tắc Phase 1:
- Backend là nguồn chân lý (authoritative), FE chỉ hỗ trợ UX.
- Dữ liệu người dùng sai (format/kiểu/giá trị) → HTTP 200 + {status:false,message}
  (KHÔNG được trả HTTP 500).
- Body không phải JSON → HTTP 400 + envelope {status:false}.

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.Model.User import User
from tests.conftest import (FakeUserDaoBus, FakeSanPhamTimKiemStore,
                            FakeGioHangStore, FakeDonHangCustomerStore)


def _dung_cu(customer_client):
    users = {
        "khachA": User(ma_user=5, ma_nhom_quyen=4, ten_user="Khách A",
                       sdt="0901234567", dia_chi="HN", cmnd="1",
                       tendangnhap="khachA", mat_khau="123456"),
    }
    thong_tin = {5: {"UserId": 5, "FullName": "Khách A", "Role_Id": 4,
                     "trang_thai": "active", "Phone": "0901234567",
                     "Address": "HN", "Password": "123456"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"khachA": "123456"})
    san_pham = {1: {"id": 1, "name": "SP A", "price": 100000, "quantity": 10,
                    "store_id": 10, "category_id": 1, "is_active": True}}
    sp_store = FakeSanPhamTimKiemStore(san_pham=dict(san_pham))
    gio_store = FakeGioHangStore(san_pham=dict(san_pham))
    don_store = FakeDonHangCustomerStore(san_pham=dict(san_pham))
    client = customer_client(user_dao=user_dao, san_pham_store=sp_store,
                             gio_hang_store=gio_store,
                             don_hang_store=don_store)
    return client


def _login(client, uid=5):
    with client.session_transaction() as s:
        s["user_id"] = uid


# ── TASK 1: Lọc giá qua API ─────────────────────────────────────────────────
def test_api_loc_gia_hop_le(customer_client):
    client = _dung_cu(customer_client)
    r = client.get("/api/products?min_price=50000&max_price=150000")
    assert r.status_code == 200
    assert r.json["status"] is True
    assert {sp["id"] for sp in r.json["data"]} == {1}


def test_api_loc_gia_ngoai_khoang_tra_rong(customer_client):
    client = _dung_cu(customer_client)
    r = client.get("/api/products?min_price=200000")
    assert r.status_code == 200
    assert r.json["status"] is True
    assert r.json["data"] == []


def test_api_min_lon_hon_max_bi_tu_choi(customer_client):
    client = _dung_cu(customer_client)
    r = client.get("/api/products?min_price=200000&max_price=100000")
    assert r.status_code == 200
    assert r.json["status"] is False
    assert "lớn hơn" in r.json["message"]


def test_api_gia_am_bi_tu_choi(customer_client):
    client = _dung_cu(customer_client)
    r = client.get("/api/products?min_price=-5")
    assert r.status_code == 200
    assert r.json["status"] is False


def test_api_gia_khong_phai_so_bi_tu_choi(customer_client):
    client = _dung_cu(customer_client)
    r = client.get("/api/products?max_price=abc")
    assert r.status_code == 200
    assert r.json["status"] is False


def test_api_gia_rong_khong_loc(customer_client):
    client = _dung_cu(customer_client)
    r = client.get("/api/products?min_price=&max_price=")
    assert r.status_code == 200
    assert r.json["status"] is True
    assert {sp["id"] for sp in r.json["data"]} == {1}


def test_api_category_id_khong_hop_le_bi_tu_choi(customer_client):
    client = _dung_cu(customer_client)
    for gia_tri in ("abc", "1.5"):
        r = client.get(f"/api/products?category_id={gia_tri}")
        assert r.status_code == 200, gia_tri
        assert r.json["status"] is False, gia_tri
        assert "Danh mục không hợp lệ" in r.json["message"], gia_tri


# ── TASK 2: Số lượng giỏ hàng qua API ───────────────────────────────────────
def test_api_them_gio_so_thap_phan_bi_tu_choi(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1.5})
    assert r.status_code == 200
    assert r.json["status"] is False
    assert "không hợp lệ" in r.json["message"]


def test_api_cap_nhat_gio_so_chu_bi_tu_choi(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1})
    r = client.post("/api/gio-hang/cap-nhat",
                    json={"ProductId": 1, "Quantity": "abc"})
    assert r.status_code == 200
    assert r.json["status"] is False
    assert "không hợp lệ" in r.json["message"]


def test_api_them_gio_cong_don_vuot_kho(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    assert client.post("/api/gio-hang/them",
                       json={"ProductId": 1, "Quantity": 6}).json["status"] is True
    r = client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 6})
    assert r.status_code == 200
    assert r.json["status"] is False
    assert "vượt tồn kho" in r.json["message"]


# ── TASK 3/4: body không phải JSON → 400 (không 500) ────────────────────────
@pytest.mark.parametrize("duong_dan", [
    "/api/dang-ky",
    "/api/dang-nhap",
    "/api/cap-nhat-profile",
    "/api/doi-mat-khau",
    "/api/gio-hang/them",
    "/api/gio-hang/cap-nhat",
    "/api/gio-hang/xoa",
    "/api/don-hang/dat-hang",
])
def test_body_khong_phai_json_tra_400(customer_client, duong_dan):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post(duong_dan, data="day-khong-phai-json",
                    content_type="text/plain")
    assert r.status_code == 400, f"{duong_dan} kỳ vọng 400, được {r.status_code}"
    assert r.json["status"] is False


# ── TASK 4: profile — trường readonly không bị ghi đè ───────────────────────
def test_profile_bo_qua_ma_user_trong_body(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/cap-nhat-profile", json={
        "ma_user": 999, "ten_user": "Khách A Mới", "sdt": "0901234567"})
    assert r.status_code == 200
    assert r.json["status"] is True
    # Phiên vẫn là user 5, không bị đổi sang 999
    phien = client.get("/api/phien")
    assert phien.json["data"]["ma_user"] == 5
    assert phien.json["data"]["ten_user"] == "Khách A Mới"


def test_profile_ten_toan_khoang_trang_bi_tu_choi(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/cap-nhat-profile",
                    json={"ten_user": "   ", "sdt": "0901234567"})
    assert r.status_code == 200
    assert r.json["status"] is False


# ── TASK 3: đặt hàng — kiểu dữ liệu sai không gây 500 ──────────────────────
def test_dat_hang_chuoi_khong_so_khong_500(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/don-hang/dat-hang", json={
        "ReceiverName": "A", "ReceiverPhone": "0901234567",
        "ShippingAddress": "HN", "PaymentMethod": "COD",
        "SubTotal": "khong-phai-so", "ShippingFee": "abc",
        "Discount": None, "TotalAmount": "xyz",
        "Items": [{"ProductId": 1, "Quantity": 1, "UnitPrice": 100000,
                   "ProductName": "SP A", "Emoji": "📦"}]})
    assert r.status_code == 200
    assert "status" in r.json


def test_dat_hang_so_luong_thap_phan_bi_tu_choi(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/don-hang/dat-hang", json={
        "ReceiverName": "A", "ReceiverPhone": "0901234567",
        "ShippingAddress": "HN", "PaymentMethod": "COD",
        "SubTotal": 100000, "ShippingFee": 25000, "Discount": 0,
        "TotalAmount": 125000,
        "Items": [{"ProductId": 1, "Quantity": 1.5, "UnitPrice": 100000,
                   "ProductName": "SP A", "Emoji": "📦"}]})
    assert r.status_code == 200
    assert r.json["status"] is False
    assert "không hợp lệ" in r.json["message"]


def test_dang_ky_mat_khau_so_khong_500(customer_client):
    client = _dung_cu(customer_client)
    r = client.post("/api/dang-ky", json={
        "ten_user": "Khách Số", "sdt": "0901234567",
        "tendangnhap": "khach_so", "mat_khau": 123})
    assert r.status_code == 200
    assert r.json["status"] is False
    assert "6 ký tự" in r.json["message"]


def test_doi_mat_khau_moi_dang_so_khong_500(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/doi-mat-khau",
                    json={"mat_khau_cu": "123456", "mat_khau_moi": 123})
    assert r.status_code == 200
    assert r.json["status"] is False


def test_dat_hang_ten_dia_chi_qua_dai_bi_tu_choi(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    for body in ({"ReceiverName": "A" * 101, "ShippingAddress": "HN"},
                 {"ReceiverName": "A", "ShippingAddress": "B" * 501}):
        r = client.post("/api/don-hang/dat-hang", json={
            "ReceiverPhone": "0901234567", "PaymentMethod": "COD",
            "SubTotal": 100000, "ShippingFee": 25000,
            "TotalAmount": 125000,
            "Items": [{"ProductId": 1, "Quantity": 1,
                       "UnitPrice": 100000,
                       "ProductName": "SP A", "Emoji": "📦"}],
            **body})
        assert r.status_code == 200, body
        assert r.json["status"] is False, body
        assert "quá dài" in r.json["message"], body


def test_dat_hang_items_khong_phai_mang_khong_500(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/don-hang/dat-hang", json={
        "ReceiverName": "A", "ReceiverPhone": "0901234567",
        "ShippingAddress": "HN", "PaymentMethod": "COD",
        "SubTotal": 0, "ShippingFee": 0, "TotalAmount": 0,
        "Items": "khong-phai-mang"})
    assert r.status_code == 200
    assert r.json["status"] is False
