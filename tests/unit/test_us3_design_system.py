"""Static test design-system — 007 T050 (test-first Đỏ-Xanh).

Biến :root (--primary #9116d4, --accent #F5A623, --radius 12px),
font Nunito/Be Vietnam Pro, tái dùng class chung, không framework mới.
KHÔNG cần DB.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))


def _css():
    return (REPO / "static" / "css" / "style.css").read_text(encoding="utf-8")


def test_root_giu_bien_chuan():
    css = _css()
    assert "--primary" in css and "#9116d4" in css
    assert "--accent" in css and "#F5A623" in css
    assert "--radius" in css and "12px" in css


def test_font_chuan_khong_font_la():
    css = _css().lower()
    assert "nunito" in css
    assert "be vietnam pro" in css


def test_tai_dung_class_dung_chung():
    css = _css()
    for cls in [".product-card", ".btn-submit", ".hdr-btn",
                ".modal-box", ".filter-card", ".admin-layout", ".stat-val"]:
        assert cls in css, f"Thiếu class dùng chung {cls}"


def test_khong_framework_moi():
    css = _css().lower()
    html = (REPO / "templates" / "index.html").read_text(encoding="utf-8").lower()
    for kw in ["bootstrap", "tailwind", "@tailwind", "bulma", "foundation"]:
        assert kw not in css, f"CSS lẫn framework lạ: {kw}"
        assert kw not in html, f"HTML lẫn framework lạ: {kw}"
    # không hardcode màu lạ ngoài :root (mẫu kiểm: không quá nhiều mã hex rời)
    hexes = set(re.findall(r"#[0-9a-fA-F]{6}", _css()))
    assert len(hexes) <= 25, f"Quá nhiều mã màu hardcode: {sorted(hexes)}"


def test_khong_mau_font_la_trong_html_inline():
    html = (REPO / "templates" / "index.html").read_text(encoding="utf-8")
    assert "font-family:" not in html.replace(" ", "").lower() or \
        "BeVietnamPro" in html or "Nunito" in html or "var(" in html
