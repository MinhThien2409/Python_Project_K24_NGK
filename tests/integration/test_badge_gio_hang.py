"""Test badge gio hang (frontend template/JS) — 011 US3 T014.

Doc truc tiep static/js/main.js — khong chay JS.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

MAIN_JS = Path(__file__).resolve().parent.parent.parent / "static" / "js" / "main.js"


def _ham(source, ten):
    """Trích phần thân hàm `ten` từ source (thô, đủ cho kiểm tra chuỗi)."""
    match = re.search(r"function\s+" + re.escape(ten) + r"\s*\([^)]*\)\s*\{", source)
    assert match, f"Không tìm thấy function {ten}"
    dau = match.end()
    # Cân bằng ngoặc nhọn để lấy trọn thân hàm
    mo = 1
    for i in range(dau, len(source)):
        if source[i] == "{":
            mo += 1
        elif source[i] == "}":
            mo -= 1
            if mo == 0:
                return source[match.start():i + 1]
    return source[match.start():]


def test_update_cart_badge_doc_truong_quantity():
    """US3: updateCartBadge đọc trường Quantity (không chỉ .qty) và ép sang số."""
    src = MAIN_JS.read_text(encoding="utf-8")
    ham = _ham(src, "updateCartBadge")
    assert "Quantity" in ham, "phải đọc trường Quantity từ giỏ server"
    assert "Number(" in ham, "phải ép kiểu Number để tránh NaN"
    assert "Math.max(0" in ham, "phải chặn số âm"
    # Ưu tiên c.Quantity (fallback c.qty được phép giữ) — không đọc qty trước Quantity
    assert ham.index("c.Quantity") < (ham.index("c.qty") if "c.qty" in ham else 10 ** 9)


def test_handle_place_order_doc_data_orders():
    """US3: handlePlaceOrder đọc data.orders từ response để hiện hoá đơn nhiều đơn."""
    src = MAIN_JS.read_text(encoding="utf-8")
    ham = _ham(src, "handlePlaceOrder")
    assert "data.orders" in ham or "result.data" in ham
    assert "order_ids" in ham or "orders" in ham


def test_khong_con_confirm_xoa_gio_khi_conflict():
    """US1/US3 regression: không còn nhánh confirm() đổi shop trong xuLyThemVaoGio."""
    src = MAIN_JS.read_text(encoding="utf-8")
    assert "result.conflict" not in src, "server không còn trả conflict nữa"
    ham = _ham(src, "xuLyThemVaoGio")
    assert "confirm(" not in ham