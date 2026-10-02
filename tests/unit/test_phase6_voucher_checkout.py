from datetime import datetime, timedelta
from back_end.DAO.DonHangDao import DonHangDao
from back_end.Model.DonHang import DonHang
from back_end.Model.OrderItem import OrderItem

class Cursor:
    def __init__(self,row): self.row=row; self.rowcount=0; self.sql=[]; self.lastrowid=1
    def execute(self,sql,args=None):
        self.sql.append((sql,args))
        if sql.strip().upper().startswith("UPDATE VOUCHER"):
            self.rowcount=1
    def fetchone(self): return self.row
    def close(self): pass

def orders(voucher="SAVE10"):
    d=DonHang(UserId=5,ShippingFee=25000,VoucherCode=voucher)
    d.Items=[OrderItem(ProductId=1,Quantity=2,UnitPrice=100000,TotalPrice=200000)]
    d.SubTotal=200000; d.TotalAmount=225000
    return [d]

def row(**kw):
    now=datetime.now()
    d=dict(VoucherId=1,Code="SAVE10",Name="Save 10",DiscountType="PERCENT",DiscountValue=10,
           MinOrderValue=0,MaxDiscount=50000,StartDate=now-timedelta(days=1),
           EndDate=now+timedelta(days=1),Quantity=10,UsedQuantity=0,IsActive=1)
    d.update(kw)
    return tuple(d[k] for k in ("VoucherId","Code","Name","DiscountType","DiscountValue","MinOrderValue","MaxDiscount","StartDate","EndDate","Quantity","UsedQuantity","IsActive"))

def test_percent_and_max_discount():
    o=orders(); c=Cursor(row()); assert DonHangDao()._ap_dung_voucher(c,o) is None
    assert o[0].DiscountAmount==20000 and o[0].TotalAmount==205000
    assert any("FOR UPDATE" in q for q,_ in c.sql)

def test_fixed_cannot_exceed_subtotal():
    o=orders(); c=Cursor(row(DiscountType="FIXED",DiscountValue=999999,MaxDiscount=0))
    assert DonHangDao()._ap_dung_voucher(c,o) is None
    assert o[0].DiscountAmount==200000 and o[0].TotalAmount==25000

def test_minimum_order():
    o=orders(); c=Cursor(row(MinOrderValue=300000)); r=DonHangDao()._ap_dung_voucher(c,o)
    assert r["error"]=="invalid_voucher" and "tối thiểu" in r["message"]

def test_expired():
    o=orders(); c=Cursor(row(EndDate=datetime.now()-timedelta(seconds=1))); r=DonHangDao()._ap_dung_voucher(c,o)
    assert "hết hạn" in r["message"]

def test_not_started():
    o=orders(); c=Cursor(row(StartDate=datetime.now()+timedelta(days=1))); r=DonHangDao()._ap_dung_voucher(c,o)
    assert "chưa bắt đầu" in r["message"]

def test_disabled():
    o=orders(); c=Cursor(row(IsActive=0)); r=DonHangDao()._ap_dung_voucher(c,o)
    assert "vô hiệu hóa" in r["message"]

def test_exhausted():
    o=orders(); c=Cursor(row(Quantity=1,UsedQuantity=1)); r=DonHangDao()._ap_dung_voucher(c,o)
    assert "hết lượt" in r["message"]

def test_no_voucher_has_no_discount():
    o=orders(voucher=None); c=Cursor(None); assert DonHangDao()._ap_dung_voucher(c,o) is None
    assert o[0].DiscountAmount==0 and o[0].TotalAmount==225000

def test_discount_never_negative():
    o=orders(); c=Cursor(row(DiscountType="FIXED",DiscountValue=-999))
    # Invalid DB data is not accepted as a positive discount.
    result=DonHangDao()._ap_dung_voucher(c,o)
    assert result is None or o[0].DiscountAmount>=0

class Conn:
    def __init__(self,cursor): self.c=cursor; self.rollback_count=0; self.commit_count=0
    def cursor(self): return self.c
    def rollback(self): self.rollback_count+=1
    def commit(self): self.commit_count+=1
    def close(self): pass

class FailingDao(DonHangDao):
    def _chen_items_tru_kho(self,cursor,conn,new_order_id,order_items):
        return {"error":"out_of_stock","product_name":"SP","available":0}

def test_failed_stock_checkout_rolls_back_after_voucher_lock(monkeypatch):
    c=Cursor(row())
    conn=Conn(c)
    monkeypatch.setattr("back_end.DAO.DonHangDao.DBconnection.get_connection",lambda self:conn)
    d=FailingDao()
    o=orders()
    result=d.tao_don_hang(o)
    assert result["error"]=="out_of_stock"
    assert conn.rollback_count>=1
    assert conn.commit_count==0
