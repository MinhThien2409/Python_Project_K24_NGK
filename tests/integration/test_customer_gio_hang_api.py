"""Integration test gio hang API — 005 US2 T016.

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.Model.User import User
from tests.conftest import (FakeUserDaoBus, FakeSanPhamTimKiemStore,
                            FakeGioHangStore)


def _dung_cu(customer_client):
    users = {
        "khachA": User(ma_user=5, ma_nhom_quyen=4, ten_user="Khách A",
                       sdt="0901", dia_chi="HN", cmnd="1",
                       tendangnhap="khachA", mat_khau="123456"),
    }
    thong_tin = {5: {"UserId": 5, "FullName": "Khách A", "Role_Id": 4,
                     "trang_thai": "active"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"khachA": "123456"})
    sp_store = FakeSanPhamTimKiemStore(san_pham={
        1: {"id": 1, "name": "SP Còn hàng", "price": 100000, "quantity": 5,
            "store_id": 10, "category_id": 1, "is_active": True},
        2: {"id": 2, "name": "SP Ẩn", "price": 50000, "quantity": 9,
            "store_id": 10, "category_id": 1, "is_active": False},
        3: {"id": 3, "name": "SP Shop khác", "price": 70000, "quantity": 4,
            "store_id": 20, "category_id": 1, "is_active": True},
    })
    gio_store = FakeGioHangStore(
        san_pham={1: {"store_id": 10, "price": 100000, "name": "SP Còn hàng"},
                  2: {"store_id": 10, "price": 50000, "name": "SP Ẩn"},
                  3: {"store_id": 20, "price": 70000, "name": "SP Shop khác"}})
    client = customer_client(user_dao=user_dao, san_pham_store=sp_store,
                             gio_hang_store=gio_store)
    return client


def _login(client, uid=5):
    with client.session_transaction() as s:
        s["user_id"] = uid


def test_chua_login_403(customer_client):
    client = _dung_cu(customer_client)
    r = client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1})
    assert r.status_code == 403


def test_them_sua_xoa_gio(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 2})
    assert r.json["status"] is True
    r = client.post("/api/gio-hang/cap-nhat",
                    json={"ProductId": 1, "Quantity": 3})
    assert r.json["status"] is True
    assert "cập nhật số lượng" in r.json["message"].lower()
    r = client.post("/api/gio-hang/xoa", json={"ProductId": 1})
    assert r.json["status"] is True


def test_vuot_kho_bi_tu_choi(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 99})
    assert r.json["status"] is False
    assert "vượt tồn kho" in r.json["message"]


def test_sp_an_bi_tu_choi(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/gio-hang/them", json={"ProductId": 2, "Quantity": 1})
    assert r.json["status"] is False
    assert "không còn kinh doanh" in r.json["message"]


def test_conflict_shop_khac(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/gio-hang/them", json={"ProductId": 1, "Quantity": 1})
    assert r.json["status"] is True
    r = client.post("/api/gio-hang/them", json={"ProductId": 3, "Quantity": 1})
    assert r.json["status"] is False
    assert r.json.get("conflict") is True
