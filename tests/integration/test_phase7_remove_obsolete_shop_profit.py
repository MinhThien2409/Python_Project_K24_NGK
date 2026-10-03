from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAIN_JS = PROJECT_ROOT / "static" / "js" / "main.js"
INDEX_HTML = PROJECT_ROOT / "templates" / "index.html"
APP_PY = PROJECT_ROOT / "app.py"


def test_seller_profit_obsolete_logic_removed():
    js = MAIN_JS.read_text(encoding="utf-8")
    obsolete_markers = [
        "tinhThuNhapRongSeller",
        "tinhGiaVonTrungBinhMap",
        "Lợi nhuận",
        "loiNhuan",
        "thuNhapRong",
    ]
    for marker in obsolete_markers:
        assert marker not in js, f"Seller Profit obsolete marker vẫn còn: {marker}"


def test_seller_revenue_and_shop_features_remain():
    js = MAIN_JS.read_text(encoding="utf-8")
    html = INDEX_HTML.read_text(encoding="utf-8")
    app = APP_PY.read_text(encoding="utf-8")

    assert "Doanh thu" in js
    assert "/api/seller/trang-shop" in js
    assert 'id="smenu-shop"' in html
    assert 'id="spane-shop"' in html
    assert "@app.route('/api/seller/trang-shop'" in app
