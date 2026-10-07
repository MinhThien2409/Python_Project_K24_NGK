from pathlib import Path
import re
JS = Path('static/js/main.js').read_text(encoding='utf-8')
APP = Path('app.py').read_text(encoding='utf-8')

def test_phase8_no_duplicate_render_seller_products():
    assert len(re.findall(r'\bfunction\s+renderSellerProducts\s*\(', JS)) == 1
    assert JS.count('async function renderSellerProducts()') == 1

def test_phase8_dynamic_server_text_uses_html_escape():
    for marker in ('escHtml(p.name)', 'escHtml(p.description', 'escHtml(u.ten_user)', 'escHtml(u.tendangnhap)', 'escHtml(n.NoiDung', 'escHtml(i.ProductName', 'escHtml(item.ProductName'):
        assert marker in JS, marker

def test_phase8_user_callback_argument_is_json_encoded():
    assert 'JSON.stringify(String(u.ten_user ||' in JS
    assert "u.ten_user.replace(/'/g" not in JS
    assert 'moModalCapLaiMatKhau(' in JS
    assert 'xacNhanKhoaAdminTaiKhoan' in JS

def test_phase8_seller_voucher_ownership_stays_backend_derived():
    assert '_seller_store_hien_tai()' in APP
    assert "seller_id=store.get('store_id')" in APP
    assert "d.get('SellerId')" not in APP

def test_phase8_checkout_ignores_client_totals():
    assert '# Client subtotal/discount/total are intentionally ignored.' in APP
    assert "data.get('DiscountAmount')" not in APP
    assert "data.get('TotalAmount')" not in APP
    assert "data.get('SubTotal')" not in APP
