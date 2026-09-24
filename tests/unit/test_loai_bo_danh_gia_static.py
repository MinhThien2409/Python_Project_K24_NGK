"""Unit test US1+US3 static — 006 T006/T007/T020 (test-first Đỏ-Xanh).

Không cần DB: đọc file nguồn dạng text.
Kỳ vọng SAU implement: 0 tồn dư rating trong HTML/JS/CSS.
Trước implement: các test này FAIL (còn rating).
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))


def _doc(duong_dan):
    return (REPO / duong_dan).read_text(encoding="utf-8")


# ── T006: Customer UI không còn rating-row/setRatingFilter/reviewModal/sort rating ──
def test_customer_html_khong_con_rating_row():
    html = _doc("templates/index.html")
    assert "rating-row" not in html
    assert "setRatingFilter" not in html
    assert "reviewModal" not in html
    assert "reviewModalContent" not in html


def test_customer_html_khong_con_sort_rating():
    html = _doc("templates/index.html")
    assert 'value="rating"' not in html


def test_customer_js_khong_con_sort_rating_va_hien_thi_sao():
    js = _doc("static/js/main.js")
    assert "sort === 'rating'" not in js
    assert 'sort === "rating"' not in js
    assert "p.rating" not in js
    assert "prodRating" not in js
    assert "setRatingFilter" not in js
    assert "reviewModal" not in js


# ── T007: Seller form không còn input #prodRating ──
def test_seller_form_khong_con_prod_rating():
    html = _doc("templates/index.html")
    assert "prodRating" not in html
    assert "Đánh giá (0-5)" not in html


# ── T020: CSS không còn block rating ──
def test_css_khong_con_rating_star_review():
    css = _doc("static/css/style.css")
    assert ".rating-row" not in css
    assert ".star-input" not in css
    assert ".review-item" not in css
    # .star dùng riêng cho rating cũng phải xóa (giữ style dùng chung khác)
    assert ".star" not in css
