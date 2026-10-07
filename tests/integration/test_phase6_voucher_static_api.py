from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def test_voucher_management_routes_are_seller_owned():
    app=(ROOT/"app.py").read_text(encoding="utf-8")
    assert "/api/voucher" in app
    assert "/api/voucher/<int:voucher_id>" in app
    assert "/api/voucher/kiem-tra" in app
    assert "_seller_store_hien_tai()" in app
    assert "kiem_tra_quyen_quan_ly(session.get('user_id'))" not in app.split("# API VOUCHER — SELLER",1)[1].split("# API GIỎ HÀNG",1)[0]

def test_checkout_does_not_accept_client_authoritative_values():
    app=(ROOT/"app.py").read_text(encoding="utf-8")
    checkout=app.split("def api_dat_hang():",1)[1].split("@app.route('/api/don-hang/hoa-don",1)[0]
    assert "data.get('Discount')" not in checkout
    assert "data.get('TotalAmount')" not in checkout
    assert "data.get('SubTotal')" not in checkout
    assert "data.get('SellerId')" not in checkout
    assert "data.get('UsedQuantity')" not in checkout
    assert "VoucherCode=voucher_code or None" in checkout

def test_order_dao_locks_voucher_and_uses_voucher_product_scope():
    dao=(ROOT/"back_end/DAO/DonHangDao.py").read_text(encoding="utf-8")
    assert "FROM Voucher v" in dao
    assert "FOR UPDATE" in dao
    assert "VoucherProduct" in dao
    assert "p.StoreId=%s" in dao
    assert "VoucherCode" in dao
    assert "UsedQuantity=UsedQuantity+1" in dao

def test_voucher_delete_locks_row_before_used_quantity_check():
    dao=(ROOT/"back_end/DAO/VoucherDao.py").read_text(encoding="utf-8")
    assert "SELECT UsedQuantity FROM Voucher WHERE VoucherId=%s AND SellerId=%s FOR UPDATE" in dao
    assert "DELETE FROM VoucherProduct WHERE VoucherId=%s" in dao
    assert "DELETE FROM Voucher WHERE VoucherId=%s AND SellerId=%s" in dao
