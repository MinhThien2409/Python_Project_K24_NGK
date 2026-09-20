# -*- coding: utf-8 -*-
"""Test tab `Tổng quan gian hàng` theo design system — 015 FR-029/030/031/032.

- FR-029: renderSellerOverview dùng .admin-card + .stats-grid/.stat-box + pill
          (user-status-active), không dùng .filter-card, không màu mới.
- FR-030: số liệu (tổng sản phẩm, sắp hết hàng, tổng đã bán, doanh thu ước tính)
          tính từ /api/seller/san-pham + /api/seller/thong-ke/tong-quan.
- FR-031: có nhánh empty-state khi thiếu shop/sản phẩm.
- FR-032: kiểm thử tự động xác nhận nguồn số liệu (không hardcode) + dùng biến CSS sẵn có.

KHÔNG cần DB — đọc tĩnh static/js/main.js + static/css/style.css.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

JS = (REPO / "static" / "js" / "main.js").read_text(encoding="utf-8")
CSS = (REPO / "static" / "css" / "style.css").read_text(encoding="utf-8")


def _doan_ham(ten_ham):
    """Cắt thân hàm render (dùng định nghĩa CUỐI CÙNG trong main.js)."""
    vi_tri = []
    for mau in [f"async function {ten_ham}", f"{ten_ham} = async function",
                f"function {ten_ham}"]:
        start = JS.rfind(mau)
        if start >= 0:
            vi_tri.append(start)
    assert vi_tri, f"Không tìm thấy hàm {ten_ham}"
    cut = JS[max(vi_tri):]
    end_init = cut.index("{")
    brace, i = 1, end_init + 1
    while brace > 0 and i < len(cut):
        if cut[i] == "{":
            brace += 1
        elif cut[i] == "}":
            brace -= 1
        i += 1
    return cut[:i]


# ── FR-029: dùng đúng component của design system ──
def test_overview_dung_admin_card():
    seg = _doan_ham("renderSellerOverview")
    assert "admin-card" in seg

def test_overview_dung_stats_grid_stat_box():
    seg = _doan_ham("renderSellerOverview")
    assert "stats-grid" in seg
    assert "stat-box" in seg
    assert "stat-val" in seg

def test_overview_khong_dung_filter_card():
    seg = _doan_ham("renderSellerOverview")
    assert "filter-card" not in seg, "Tổng quan phải dùng admin-card/stats-grid (FR-029)"

def test_overview_co_pill_trang_thai_shop():
    seg = _doan_ham("renderSellerOverview")
    assert "user-status-active" in seg
    assert "Đang hoạt động" in seg

def test_overview_co_empty_state():
    seg = _doan_ham("renderSellerOverview")
    assert "empty-state" in seg
    assert "Chưa có sản phẩm" in seg or "Không tìm thấy" in seg

# ── FR-030/FR-032: số liệu khớp dữ liệu sản phẩm thật của shop ──
def test_overview_nguon_du_lieu_la_seller_san_pham_va_thong_ke():
    seg = _doan_ham("renderSellerOverview")
    assert "/api/seller/san-pham" in seg, "Phải đọc sản phẩm từ /api/seller/san-pham"
    assert "/api/seller/thong-ke/tong-quan" in seg, "Phải đọc thống kê shop"

def test_overview_tong_san_pham_tinh_tu_data_length():
    seg = _doan_ham("renderSellerOverview")
    assert "data.length" in seg, "Tổng sản phẩm phải tính theo .length của danh sách"

def test_overview_sap_het_hang_tinh_1_den_5():
    seg = _doan_ham("renderSellerOverview")
    assert "quantity >= 1" in seg and "quantity <= 5" in seg

def test_overview_tong_da_ban_tinh_theo_sold():
    seg = _doan_ham("renderSellerOverview")
    assert "sold" in seg

def test_overview_doanh_thu_tu_thong_ke():
    seg = _doan_ham("renderSellerOverview")
    assert "doanh_thu" in seg

def test_overview_dung_bien_css_san_co():
    seg = _doan_ham("renderSellerOverview")
    # Không hardcode màu hex mới — chỉ dùng var(--...) (FR-029/FR-032)
    import re
    hex_vals = re.findall(r"#[0-9a-fA-F]{3,6}\b", seg)
    assert not hex_vals, f"renderSellerOverview hardcode màu hex: {hex_vals}"