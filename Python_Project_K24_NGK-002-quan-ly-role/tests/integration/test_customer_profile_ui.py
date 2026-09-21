from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_header_khong_con_profile_nhung_con_history():
    html = (ROOT / "templates/index.html").read_text(encoding="utf-8")
    assert "id=\"hdrProfileBtn\"" not in html
    assert "id=\"hdrHistoryBtn\"" in html


def test_profile_modal_khong_con_tab_edit_va_nut_lich_su():
    html = (ROOT / "templates/index.html").read_text(encoding="utf-8")
    profile = html.split('id="profileModal"', 1)[1].split('id="checkoutModal"', 1)[0]
    assert "id=\"ptab-edit\"" not in profile
    assert "📋 Xem lịch sử đơn hàng" not in profile


def test_js_khong_con_handler_ui_profile_du_thua():
    js = (ROOT / "static/js/main.js").read_text(encoding="utf-8")
    assert "hdrProfileBtn" not in js
    assert "ptab-edit" not in js
    assert "openOrderHistoryModal(); closeModal('profileModal')" not in js
