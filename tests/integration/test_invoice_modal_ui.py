from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_invoice_modal_z_index_cao_hon_order_history():
    css = (ROOT / "static/css/style.css").read_text(encoding="utf-8")
    assert "#invoiceModal" in css
    assert "z-index: 260" in css or "z-index:260" in css


def test_dong_invoice_khong_dong_lich_su():
    html = (ROOT / "templates/index.html").read_text(encoding="utf-8")
    assert "closeModal('invoiceModal')" in html
    assert "closeModal('orderHistoryModal')" not in html.split('id="invoiceModal"', 1)[1].split('id="orderHistoryModal"', 1)[0]
