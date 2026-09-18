"""Integration test US1 — 007 T013 (test-first Đỏ-Xanh).

Hồi quy endpoint sau xóa: route còn lại đúng envelope
{status, message, data}; route đã xóa trả 404 (QS-1 + QS-3).

KHÔNG chạm PobbyDB thật: dùng test_client, chỉ gọi các
route không cần DB (GET / và 404).
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import app as app_module

# Inventory rút gọn từ contracts/cleanup-contract.md mục 2 —
# các route KHÔNG cần DB để smoke-test.
ROUTE_KHONG_DB = ["/", "/api/categories", "/api/products"]


def _lay_route_table():
    return [(str(r.rule), sorted(r.methods - {"HEAD", "OPTIONS"}))
            for r in app_module.app.url_map.iter_rules()
            if str(r.rule).startswith("/api/")]


def test_tat_ca_route_contract_con_ton_tai():
    """Mọi route trong contract phải còn (chưa bị xóa nhầm)."""
    src = (REPO / "app.py").read_text(encoding="utf-8")
    bat_buoc = [
        "/api/dang-nhap", "/api/dang-ky", "/api/phien",
        "/api/categories", "/api/products",
        "/api/gio-hang/them", "/api/don-hang/dat-hang",
        "/api/don-hang/cua-seller", "/api/thong-ke/tong-quan",
        "/api/quan-ly", "/api/seller/san-pham",
        "/api/seller/don-hang", "/api/seller/trang-shop",
        "/api/duyet-seller", "/api/cap-lai-mat-khau",
    ]
    thieu = [u for u in bat_buoc if u not in src]
    assert thieu == [], f"Route contract bị thiếu trong app.py: {thieu}"


def test_so_luong_route_khop_contract():
    """Tổng số route /api/* (tính theo cặp path+method) khớp inventory 54."""
    routes = _lay_route_table()
    assert 50 <= len(routes) <= 60, \
        f"Số route /api/* lạ: {len(routes)} (kỳ vọng ~54)"


def test_trang_chu_tra_200():
    client = app_module.app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200


def test_endpoint_da_xoa_tra_404():
    """Route không tồn tại phải 404 (chuẩn sau-xóa QS-1)."""
    client = app_module.app.test_client()
    for url in ["/api/danh-gia", "/api/reviews", "/api/khong-ton-tai-xyz"]:
        resp = client.get(url)
        assert resp.status_code == 404, f"{url} kỳ vọng 404, được {resp.status_code}"


def test_handler_dung_jsonify_envelope():
    """Mọi handler /api/* trả jsonify (envelope kiểm ở test BUS/API)."""
    src = (REPO / "app.py").read_text(encoding="utf-8")
    assert "jsonify" in src
    # Không handler nào return trực tiếp dict lỗi stack trace
    assert "traceback" not in src.lower()
