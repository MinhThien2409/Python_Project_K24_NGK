"""Integration test lich su + ho so API — 005 US4 T031 (US5 mo rong o T036).

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.Model.User import User
from tests.conftest import (FakeUserDaoBus, FakeSanPhamTimKiemStore,
                            FakeGioHangStore, FakeDonHangCustomerStore)


def _dung_cu(customer_client):
    users = {
        "khachA": User(ma_user=5, ma_nhom_quyen=4, ten_user="Khách A",
                       sdt="0901", dia_chi="HN", cmnd="1",
                       tendangnhap="khachA", mat_khau="123456"),
        "khachB": User(ma_user=6, ma_nhom_quyen=4, ten_user="Khách B",
                       sdt="0902", dia_chi="HN", cmnd="2",
                       tendangnhap="khachB", mat_khau="123456"),
    }
    thong_tin = {5: {"UserId": 5, "FullName": "Khách A", "Role_Id": 4,
                     "trang_thai": "active", "Phone": "0901",
                     "Address": "HN", "Password": "123456"},
                 6: {"UserId": 6, "FullName": "Khách B", "Role_Id": 4,
                     "trang_thai": "active", "Phone": "0902",
                     "Address": "HN", "Password": "123456"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                              mat_khau={"khachA": "123456", "khachB": "123456"})
    san_pham = {1: {"store_id": 10, "price": 100000, "quantity": 50,
                    "name": "SP A", "is_active": True, "category_id": 1,
                    "id": 1}}
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


def _dat(client, sdt="0901234567"):
    return client.post("/api/don-hang/dat-hang", json={
        "ReceiverName": "A", "ReceiverPhone": sdt,
        "ShippingAddress": "HN", "PaymentMethod": "COD",
        "SubTotal": 100000, "ShippingFee": 25000, "Discount": 0,
        "TotalAmount": 125000,
        "Items": [{"ProductId": 1, "Quantity": 1, "UnitPrice": 100000,
                   "ProductName": "SP A", "Emoji": "📦"}]})


def test_lich_su_dung_chu_va_sap_xep(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    _dat(client)
    _dat(client)
    r = client.get("/api/don-hang/cua-toi/5")
    assert r.status_code == 200
    assert r.json["status"] is True
    assert len(r.json["data"]) == 2
    ngay = [d["CreatedAt"] for d in r.json["data"]]
    assert ngay == sorted(ngay, reverse=True)


def test_lich_su_khach_khac_403(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.get("/api/don-hang/cua-toi/6")
    assert r.status_code == 403


def test_hoa_don_cheo_403(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = _dat(client)
    ma_don = int(r.json["message"].split("#")[-1])
    _login(client, 6)
    r2 = client.get(f"/api/don-hang/hoa-don/{ma_don}")
    assert r2.status_code == 403


def test_chua_mua_tra_mang_rong(customer_client):
    client = _dung_cu(customer_client)
    _login(client, 6)
    r = client.get("/api/don-hang/cua-toi/6")
    assert r.status_code == 200
    assert r.json["data"] == []


# ── 005 US5 T036: profile update + đổi MK end-to-end ──
def test_cap_nhat_profile_con_hieu_luc(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/cap-nhat-profile",
                    json={"ten_user": "Khách A Mới", "dia_chi": "HCM",
                          "sdt": "0901234567", "cmnd": "001"})
    assert r.json["status"] is True
    r2 = client.get("/api/phien")
    assert r2.json["status"] is True
    assert r2.json["data"]["ten_user"] == "Khách A Mới"


def test_cap_nhat_sdt_sai_bi_tu_choi(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/cap-nhat-profile",
                    json={"ten_user": "A", "sdt": "123"})
    assert r.json["status"] is False


def test_doi_mk_moi_login_duoc_cu_fail(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/doi-mat-khau",
                    json={"mat_khau_cu": "123456", "mat_khau_moi": "moi12345"})
    assert r.json["status"] is True
    client.post("/api/dang-xuat")
    r2 = client.post("/api/dang-nhap",
                     json={"tendangnhap": "khachA", "mat_khau": "moi12345"})
    assert r2.json["status"] is True
    r3 = client.post("/api/dang-nhap",
                     json={"tendangnhap": "khachA", "mat_khau": "123456"})
    assert r3.json["status"] is False


def test_doi_mk_gui_ma_user_khac_403(customer_client):
    client = _dung_cu(customer_client)
    _login(client)
    r = client.post("/api/doi-mat-khau",
                    json={"ma_user": 6, "mat_khau_cu": "123456",
                          "mat_khau_moi": "moi12345"})
    assert r.status_code == 403
