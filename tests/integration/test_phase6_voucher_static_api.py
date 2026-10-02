from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def test_voucher_management_routes_and_checkout_preview_exist():
    app= (ROOT/"app.py").read_text(encoding="utf-8")
    assert "/api/voucher" in app
    assert "/api/voucher/<int:voucher_id>" in app
    assert "/api/voucher/kiem-tra" in app
    assert "kiem_tra_quyen_quan_ly" in app

def test_checkout_does_not_accept_client_discount_or_total_as_authoritative():
    app=(ROOT/"app.py").read_text(encoding="utf-8")
    checkout=app.split("def api_dat_hang():",1)[1].split("@app.route('/api/don-hang/hoa-don",1)[0]
    assert "data.get('Discount')" not in checkout
    assert "data.get('TotalAmount')" not in checkout
    assert "data.get('SubTotal')" not in checkout
    assert "VoucherCode=voucher_code or None" in checkout

def test_order_dao_locks_voucher_and_snapshots_code():
    dao=(ROOT/"back_end/DAO/DonHangDao.py").read_text(encoding="utf-8")
    assert "FROM Voucher WHERE Code=%s FOR UPDATE" in dao
    assert "VoucherCode" in dao
    assert "UsedQuantity=UsedQuantity+1" in dao
