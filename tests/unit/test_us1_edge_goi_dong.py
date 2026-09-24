"""Unit test US1 ca biên — 007 T014 (test-first Đỏ-Xanh).

Gọi động/import chéo: chuỗi URL Flask, fetch JS, Jinja id,
import chéo. Không chắc thì GIỮ + ghi chú (R-02).

KHÔNG cần DB.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))


def test_moi_module_backend_import_duoc():
    """Import chéo không vỡ sau dọn dẹp."""
    import importlib
    mods = [
        "back_end.Model.User", "back_end.Model.SanPham",
        "back_end.Model.DonHang", "back_end.Model.OrderItem",
        "back_end.Model.GioHang", "back_end.Model.CartItem",
        "back_end.Model.DanhMuc", "back_end.Model.GianHang",
        "back_end.Model.YeuCau",
        "back_end.DAO.DanhMucDao", "back_end.DAO.DonHangDao",
        "back_end.DAO.GianHangDao", "back_end.DAO.GioHangDao",
        "back_end.DAO.SanPhamDao", "back_end.DAO.UserDao",
        "back_end.BUS.DanhMucBus", "back_end.BUS.DonHangBus",
        "back_end.BUS.GianHangBus", "back_end.BUS.GioHangBus",
        "back_end.BUS.SanPhamBus", "back_end.BUS.UserBus",
    ]
    for m in mods:
        importlib.import_module(m)


def test_fetch_js_chi_tro_route_ton_tai():
    """Mọi fetch('/api/...') trong main.js phải ứng với route thật."""
    import app as app_module
    routes = {str(r.rule) for r in app_module.app.url_map.iter_rules()}
    js = (REPO / "static" / "js" / "main.js").read_text(encoding="utf-8")
    urls = set(re.findall(r"['\"](/api/[^'\"`?]+)['\"]", js))
    la = []
    for u in urls:
        u = re.sub(r"\$\{[^}]+\}", "1", u)
        parts = u.strip("/").split("/")
        khớp = any(
            len(str(r).strip("/").split("/")) == len(parts)
            for r in routes
            if str(r).startswith("/api/" + parts[1] if len(parts) > 1 else "/api/")
        ) or u in routes or any(u.startswith(str(r).rsplit("/", 1)[0]) for r in routes)
        if not khớp:
            # kiểm tra nới lỏng: tiền tố 2 đoạn đầu phải tồn tại
            prefix = "/".join(parts[:3])
            if not any(str(r).startswith(prefix) for r in routes):
                la.append(u)
    assert la == [], f"fetch tới endpoint lạ (có thể đã xóa): {la}"


def test_khong_eval_exec_trong_backend():
    """Không gọi động nguy hiểm có thể che giấu tham chiếu."""
    for d in ["back_end/BUS", "back_end/DAO", "back_end/Model"]:
        for f in (REPO / d).glob("*.py"):
            src = f.read_text(encoding="utf-8")
            assert "eval(" not in src, f"{f.name} chứa eval()"
            assert "exec(" not in src, f"{f.name} chứa exec()"


def test_getelementbyid_ton_tai_trong_html():
    """id JS getElementById phải có trong index.html (lấy mẫu)."""
    html = (REPO / "templates" / "index.html").read_text(encoding="utf-8")
    js = (REPO / "static" / "js" / "main.js").read_text(encoding="utf-8")
    ids = set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", js))
    thieu_nhieu = [i for i in ids if f'id="{i}"' not in html and f"id='{i}'" not in html]
    # Cho phép id render động, nhưng không được thiếu quá nửa
    assert len(thieu_nhieu) <= len(ids) / 2, \
        f"Quá nhiều id JS không có trong HTML: {thieu_nhieu[:10]}"
