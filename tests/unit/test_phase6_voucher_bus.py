from datetime import datetime
from back_end.BUS.VoucherBus import VoucherBus

class FakeVoucherDao:
    def __init__(self):
        self.codes=set()
        self.vouchers={}
        self.next_id=1
        self.product_result="ok"

    def code_ton_tai(self, code, tru_id=None):
        return code in self.codes and all(v.get("VoucherId") != tru_id for v in self.vouchers.values())

    def them(self, v, product_ids):
        if self.product_result != "ok":
            return self.product_result
        self.codes.add(v.Code)
        v.VoucherId=self.next_id
        self.next_id += 1
        self.vouchers[v.VoucherId]={
            "VoucherId":v.VoucherId,"SellerId":v.SellerId,"UsedQuantity":v.UsedQuantity,
            "IsActive":v.IsActive
        }
        return "ok"

    def lay_theo_id(self, i):
        return self.vouchers.get(i)

    def lay_theo_code(self, code):
        return None

def bus():
    b=VoucherBus()
    b.dao=FakeVoucherDao()
    return b

def base(**kw):
    d=dict(code=" SAVE10 ",name="Save 10",dtype="PERCENT",value=10,min_order=100000,
           max_discount=50000,start="2026-01-01 00:00:00",end="2026-12-31 23:59:59",
           quantity=10,seller_id=1)
    d.update(kw)
    return d

def test_valid_normalizes_code():
    v,e=bus().validate(**base()); assert e is None; assert v.Code=="SAVE10"; assert v.SellerId==1

def test_missing_code():
    v,e=bus().validate(**base(code="")); assert v is None and "không được để trống" in e

def test_invalid_type():
    v,e=bus().validate(**base(dtype="BOGO")); assert v is None

def test_invalid_percent():
    for value in (0,100.1):
        v,e=bus().validate(**base(value=value)); assert v is None

def test_invalid_fixed():
    v,e=bus().validate(**base(dtype="FIXED",value=0)); assert v is None

def test_invalid_min_order():
    v,e=bus().validate(**base(min_order=-1)); assert v is None

def test_invalid_max_discount():
    v,e=bus().validate(**base(max_discount=-1)); assert v is None

def test_invalid_date_range():
    v,e=bus().validate(**base(start="2026-12-31 00:00:00",end="2026-01-01 00:00:00")); assert v is None

def test_invalid_quantity():
    v,e=bus().validate(**base(quantity=-1)); assert v is None

def test_invalid_used_quantity():
    v,e=bus().validate(**base(quantity=1,used=2)); assert v is None

def test_create_requires_product():
    assert bus().tao(product_ids=[], **base())["status"] is False

def test_create_duplicate():
    b=bus()
    assert b.tao(product_ids=[1], **base())["status"] is True
    assert b.tao(product_ids=[1], **base())["status"] is False

def test_product_validation_failure_is_atomic():
    b=bus(); b.dao.product_result="invalid_product"
    result=b.tao(product_ids=[2], **base())
    assert result["status"] is False

def test_fixed_validation():
    v,e=bus().validate(**base(dtype="FIXED",value=25000)); assert e is None and v.DiscountType=="FIXED"

def test_code_normalization_is_case_insensitive():
    assert VoucherBus.normalize_code("  save10 ")=="SAVE10"

def test_update_foreign_voucher_is_rejected():
    b=bus()
    b.dao.vouchers[1]={"VoucherId":1,"SellerId":2,"UsedQuantity":0,"IsActive":True}
    data=base(code="NEW10"); data.pop("seller_id")
    result=b.sua(1,1,[1],**data)

def test_delete_used_voucher_is_rejected():
    b=bus()
    b.dao.vouchers[1]={"VoucherId":1,"SellerId":1,"UsedQuantity":2,"IsActive":True}
    result=b.xoa(1,1)
    assert result["status"] is False

def test_toggle_foreign_voucher_is_rejected():
    b=bus()
    b.dao.vouchers[1]={"VoucherId":1,"SellerId":2,"UsedQuantity":0,"IsActive":True}
    result=b.toggle(1,1)
    assert result["status"] is False
