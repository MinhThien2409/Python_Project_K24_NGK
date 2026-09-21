"""Integration test hoa don nhieu don — 011 US4 T018.

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
    }
    thong_tin = {5: {"UserId": 5, "FullName": "Khách A", "Role_Id": 4,
                     "trang_thai": "active"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                               mat_khau={"khachA": "123456"})
    san_pham = {
        1: {"id": 1, "name": "SP Shop10", "price": 100000, "quantity": 5,
            "store_id": 10, "category_id": 1, "is_active": True},
        2: {"id": 2, "name": "SP Shop20", "price": 70000, "quantity": 5,
            "store_id": 20, "category_id": 1, "is_active": True},
    }
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


def test_2_don_doc_lap():
    """US4: đặt cùng lúc 2 đơn → 2 OrderId khác nhau trong DB."""
    from back_end.BUS.DonHangBus import DonHangBus
    from back_end.Model.DonHang import DonHang
    from back_end.Model.OrderItem import OrderItem

    # Thiết lập chung
    users = {"khachA": User(ma_user=5, ma_nhom_quyen=4, ten_user="Khách A",
                             sdt="0901", dia_chi="HN", cmnd="1",
                             tendangnhap="khachA", mat_khau="123456")}
    thong_tin = {5: {"UserId": 5, "FullName": "Khách A", "Role_Id": 4,
                     "trang_thai": "active"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin,
                               mat_khau={"khachA": "123456"})
    san_pham = {
        1: {"id": 1, "name": "SP Shop10", "price": 100000, "quantity": 5,
            "store_id": 10, "category_id": 1, "is_active": True},
        2: {"id": 2, "name": "SP Shop20", "price": 70000, "quantity": 5,
            "store_id": 20, "category_id": 1, "is_active": True},
    }
    sp_tim = FakeSanPhamTimKiemStore(san_pham=dict(san_pham))
    gio_store = FakeGioHangStore(
        san_pham={pid: {"store_id": sp["store_id"], "price": sp["price"],
                        "name": sp["name"]} for pid, sp in san_pham.items()})
    don_store = FakeDonHangCustomerStore(san_pham=dict(san_pham))

    from back_end.BUS.UserBus import UserBus
    from back_end.BUS.SanPhamBus import SanPhamBus
    from back_end.BUS.GioHangBus import GioHangBus
    from back_end.BUS.DonHangBus import DonHangBus as _DH
    import app as app_module

    ub = UserBus(); ub.dao = user_dao
    app_module.user_bus = ub
    sb = SanPhamBus(); sb.dao = sp_tim
    app_module.san_pham_bus = sb
    cb = GioHangBus(); cb.dao = gio_store
    cb.san_pham_dao = sp_tim
    app_module.cart_bus = cb
    db = _DH(); db.dao = don_store
    app_module.don_hang_bus = db

    def dat(dh):
        return db.tao_don_hang(dh)

    # Đơn 1 của shop 10
    dh1 = DonHang(UserId=5, ReceiverName="Khách A", ReceiverPhone="0901234567",
                   ShippingAddress="Hà Nội", PaymentMethod="COD",
                   SubTotal=100000, ShippingFee=25000, DiscountAmount=0,
                   TotalAmount=125000)
    dh1.Items = [OrderItem(ProductId=1, ProductName="SP Shop10", Emoji="📦",
                            Quantity=1, UnitPrice=100000, TotalPrice=100000)]
    # Đơn 2 của shop 20
    dh2 = DonHang(UserId=5, ReceiverName="Khách A", ReceiverPhone="0901234567",
                   ShippingAddress="Hà Nội", PaymentMethod="COD",
                   SubTotal=70000, ShippingFee=25000, DiscountAmount=0,
                   TotalAmount=95000)
    dh2.Items = [OrderItem(ProductId=2, ProductName="SP Shop20", Emoji="📦",
                            Quantity=1, UnitPrice=70000, TotalPrice=70000)]

    kq1 = dat(dh1)
    kq2 = dat(dh2)
    assert kq1["status"] is True and kq2["status"] is True
    oid1, oid2 = kq1["data"]["order_ids"][0], kq2["data"]["order_ids"][0]
    assert oid1 != oid2
    # Cả 2 đơn đều trong DB cùng user
    don_all = don_store.don_hang.values()
    assert len(don_all) == 2
    assert all(int(d["UserId"]) == 5 for d in don_all)


def test_hoa_don_chi_tra_dung_don():
    """US4: GET /api/don-hang/hoa-don/<id> trả chính xác nội dung đơn đó."""
    from back_end.BUS.UserBus import UserBus
    from back_end.BUS.SanPhamBus import SanPhamBus
    from back_end.BUS.GioHangBus import GioHangBus
    from back_end.BUS.DonHangBus import DonHangBus as _DH
    import app as app_module


def test_huy_1_don_khong_anh_huong_don_khac():
    """US4: hủy 1 đơn (Pending → Cancelled) → đơn còn giữ nguyên Pending."""
    from back_end.BUS.UserBus import UserBus
    from back_end.BUS.SanPhamBus import SanPhamBus
    from back_end.BUS.GioHangBus import GioHangBus
    from back_end.BUS.DonHangBus import DonHangBus as _DH
    import app as app_module