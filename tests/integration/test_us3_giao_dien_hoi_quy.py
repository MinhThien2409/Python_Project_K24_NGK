"""Test hồi quy giao diện + console — 007 T052 (test-first Đỏ-Xanh).

3 vai trò render đúng, không fetch tới endpoint đã xóa.
KHÔNG cần DB (static + test_client GET /).
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import app as app_module


def test_trang_chu_render_3_vai_tro():
    client = app_module.app.test_client()
    html = client.get("/").get_data(as_text=True)
    assert "Customer" in html or "customer" in html.lower()
    assert "Seller" in html or "seller" in html.lower()
    assert "Admin" in html or "admin" in html.lower()


def test_khong_fetch_toi_endpoint_danh_gia():
    js = (REPO / "static" / "js" / "main.js").read_text(encoding="utf-8")
    for kw in ["/api/danh-gia", "/api/reviews", "/api/review", "prodRating",
               "setRatingFilter", "reviewModal"]:
        assert kw not in js, f"JS còn gọi UI đánh giá đã xóa: {kw}"


def test_html_khong_con_ui_danh_gia():
    html = (REPO / "templates" / "index.html").read_text(encoding="utf-8")
    for kw in ["prodRating", "setRatingFilter", "reviewModal", "rating-row"]:
        assert kw not in html, f"HTML còn UI đánh giá đã xóa: {kw}"


def test_console_khong_loi_route_xoa():
    """Mọi fetch trong JS đều ứng với route còn hiệu lực."""
    routes = {str(r.rule) for r in app_module.app.url_map.iter_rules()}
    js = (REPO / "static" / "js" / "main.js").read_text(encoding="utf-8")
    urls = set(re.findall(r"['\"](/api/[a-z0-9\-/]+)['\"]", js))
    la = []
    for u in urls:
        if not any(str(r) == u or str(r).startswith(u + "/") or
                   u.startswith(str(r).split("<")[0].rstrip("/"))
                   for r in routes):
            la.append(u)
    assert la == [], f"fetch tới endpoint không tồn tại: {la}"
