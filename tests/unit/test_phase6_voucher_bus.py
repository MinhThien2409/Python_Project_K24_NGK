from datetime import datetime, timedelta
from back_end.BUS.VoucherBus import VoucherBus

class FakeVoucherDao:
    def __init__(self):
        self.codes=set()
    def code_ton_tai(self, code, tru_id=None): return code in self.codes
    def them(self, v): self.codes.add(v.Code); return True

def bus():
    b=VoucherBus(); b.dao=FakeVoucherDao(); return b

def base(**kw):
    d=dict(code=" SAVE10 ",name="Save 10",dtype="PERCENT",value=10,min_order=100000,
           max_discount=50000,start="2026-01-01 00:00:00",end="2026-12-31 23:59:59",quantity=10)
    d.update(kw); return d

def test_valid_normalizes_code():
    v,e=bus().validate(**base()); assert e is None; assert v.Code=="SAVE10"

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

def test_create_duplicate():
    b=bus(); assert b.tao(**base())["status"] is True; assert b.tao(**base())["status"] is False

def test_fixed_validation():
    v,e=bus().validate(**base(dtype="FIXED",value=25000)); assert e is None and v.DiscountType=="FIXED"

def test_code_normalization_is_case_insensitive():
    assert VoucherBus.normalize_code("  save10 ")=="SAVE10"
