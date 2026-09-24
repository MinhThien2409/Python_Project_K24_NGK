"""Integration test tim kiem API — 005 US1 T009.

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.Model.User import User
from tests.conftest import FakeUserDaoBus, FakeSanPhamTimKiemStore


def _dung_cu(customer_client):
    users = {
        "khach": User(ma_user=5, ma_nhom_quyen=4, ten_user="Khách",
                      sdt="0903", dia_chi="HN", cmnd="3",
                      tendangnhap="khach", mat_khau="123456"),
    }
    thong_tin = {5: {"UserId": 5, "FullName": "Khách", "Role_Id": 4,
                     "trang_thai": "active"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"khach": "123456"})
    sp_store = FakeSanPhamTimKiemStore(san_pham={
        1: {"id": 1, "name": "Hoa Hồng Đỏ", "price": 100000, "quantity": 5,
            "store_id": 10, "category_id": 1, "is_active": True},
        2: {"id": 2, "name": "HOA CÚC VÀNG", "price": 50000, "quantity": 3,
            "store_id": 10, "category_id": 1, "is_active": True},
        3: {"id": 3, "name": "Chậu Lan Tím", "price": 200000, "quantity": 2,
            "store_id": 10, "category_id": 2, "is_active": True},
        4: {"id": 4, "name": "Hoa Hồng Ẩn", "price": 90000, "quantity": 9,
            "store_id": 10, "category_id": 1, "is_active": False},
    })
    client = customer_client(user_dao=user_dao, san_pham_store=sp_store)
    return client


def test_guest_tim_kiem_hoa_thuong(customer_client):
    client = _dung_cu(customer_client)
    r = client.get("/api/products?q=hoa HỒNG")
    assert r.status_code == 200
    assert r.json["status"] is True
    ids = {sp["id"] for sp in r.json["data"]}
    assert 1 in ids and 4 not in ids


def test_loc_category_id(customer_client):
    client = _dung_cu(customer_client)
    r = client.get("/api/products?category_id=2")
    assert r.status_code == 200
    assert {sp["id"] for sp in r.json["data"]} == {3}


def test_chi_tiet_sp(customer_client):
    client = _dung_cu(customer_client)
    r = client.get("/api/products/1")
    assert r.status_code == 200
    assert r.json["status"] is True
    assert r.json["data"]["id"] == 1


def test_ket_qua_rong_tra_mang_rong(customer_client):
    client = _dung_cu(customer_client)
    r = client.get("/api/products?q=khong-ton-tai-xyz")
    assert r.status_code == 200
    assert r.json["status"] is True
    assert r.json["data"] == []
