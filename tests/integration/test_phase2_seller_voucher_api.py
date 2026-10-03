from back_end.Model.User import User
from tests.conftest import MockUserDao, FakeShopStore


class FakeVoucherBus:
    def __init__(self):
        self.calls=[]
        self.data={
            1:{"VoucherId":1,"SellerId":10,"Code":"SAVE10","ProductIds":[1,3]},
            2:{"VoucherId":2,"SellerId":20,"Code":"SAVE20","ProductIds":[4]},
        }

    def lay_tat_ca(self, seller_id):
        self.calls.append(("list", seller_id))
        return {"status":True,"data":[v for v in self.data.values() if v["SellerId"]==seller_id]}

    def lay_theo_id(self, voucher_id, seller_id):
        self.calls.append(("detail", voucher_id, seller_id))
        v=self.data.get(voucher_id)
        if not v or v["SellerId"]!=seller_id:
            return {"status":False,"message":"Bạn không có quyền thao tác trên voucher này!"}
        return {"status":True,"data":v}

    def tao(self, seller_id, product_ids, **kw):
        self.calls.append(("create", seller_id, product_ids, kw))
        return {"status":True,"message":"Tạo voucher thành công!"}

    def sua(self, voucher_id, seller_id, product_ids, **kw):
        self.calls.append(("update", voucher_id, seller_id, product_ids, kw))
        return {"status":True,"message":"Cập nhật voucher thành công!"}

    def toggle(self, voucher_id, seller_id):
        self.calls.append(("toggle", voucher_id, seller_id))
        return {"status":True,"message":"Đã cập nhật trạng thái voucher!"}

    def xoa(self, voucher_id, seller_id):
        self.calls.append(("delete", voucher_id, seller_id))
        return {"status":True,"message":"Đã xóa voucher!"}


def _seller_user(uid):
    return User(ma_user=uid, ma_nhom_quyen=3, ten_user=f"Seller {uid}",
                sdt="0123456789", dia_chi="HN", cmnd="1",
                tendangnhap=f"seller{uid}", mat_khau="123456")


def _manager_user():
    return User(ma_user=2, ma_nhom_quyen=2, ten_user="Manager",
                sdt="0123456789", dia_chi="HN", cmnd="2",
                tendangnhap="manager1", mat_khau="123456")


def _session_login(client, uid):
    with client.session_transaction() as sess:
        sess["user_id"]=uid


def test_seller_voucher_crud_uses_authenticated_store_not_body(seller_client, monkeypatch):
    import app as app_module
    fake=FakeVoucherBus()
    monkeypatch.setattr(app_module, "voucher_bus", fake)
    client=seller_client(
        user_dao=MockUserDao(user=_seller_user(3)),
        shop_store=FakeShopStore({10:{"StoreId":10,"UserId":3,"StoreName":"Shop A"}})
    )
    _session_login(client,3)

    payload={"SellerId":999,"ProductIds":[1,3],"Code":"SAVE10","Name":"Save",
             "DiscountType":"PERCENT","DiscountValue":10,"MinOrderValue":0,
             "MaxDiscount":0,"StartDate":"2026-01-01 00:00:00",
             "EndDate":"2026-12-31 23:59:59","Quantity":10}
    assert client.post("/api/voucher",json=payload).status_code==200
    assert fake.calls[-1][0]=="create" and fake.calls[-1][1]==10

    assert client.get("/api/voucher").status_code==200
    assert fake.calls[-1]==("list",10)

    assert client.get("/api/voucher/1").status_code==200
    assert fake.calls[-1]==("detail",1,10)

    assert client.put("/api/voucher/1",json=payload).status_code==200
    assert fake.calls[-1][2]==10

    assert client.post("/api/voucher/1/toggle").status_code==200
    assert fake.calls[-1]==("toggle",1,10)

    assert client.delete("/api/voucher/1").status_code==200
    assert fake.calls[-1]==("delete",1,10)


def test_seller_cannot_access_other_seller_voucher(seller_client, monkeypatch):
    import app as app_module
    fake=FakeVoucherBus()
    monkeypatch.setattr(app_module, "voucher_bus", fake)
    client=seller_client(
        user_dao=MockUserDao(user=_seller_user(3)),
        shop_store=FakeShopStore({10:{"StoreId":10,"UserId":3,"StoreName":"Shop A"}})
    )
    _session_login(client,3)
    r=client.get("/api/voucher/2")
    assert r.status_code==403


def test_manager_cannot_use_seller_voucher_api(seller_client, monkeypatch):
    import app as app_module
    fake=FakeVoucherBus()
    monkeypatch.setattr(app_module, "voucher_bus", fake)
    client=seller_client(
        user_dao=MockUserDao(user=_manager_user()),
        shop_store=FakeShopStore({10:{"StoreId":10,"UserId":2,"StoreName":"Manager Shop"}})
    )
    _session_login(client,2)

    payload={"SellerId":10,"ProductIds":[1],"Code":"MGR10","Name":"Save",
             "DiscountType":"PERCENT","DiscountValue":10,"MinOrderValue":0,
             "MaxDiscount":0,"StartDate":"2026-01-01 00:00:00",
             "EndDate":"2026-12-31 23:59:59","Quantity":10}
    assert client.get("/api/voucher").status_code==403
    assert client.get("/api/voucher/1").status_code==403
    assert client.post("/api/voucher",json=payload).status_code==403
    assert client.put("/api/voucher/1",json=payload).status_code==403
    assert client.post("/api/voucher/1/toggle").status_code==403
    assert client.delete("/api/voucher/1").status_code==403
    assert fake.calls==[]

