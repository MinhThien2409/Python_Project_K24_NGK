# -*- coding: utf-8 -*-
"""Test DOM + logic thanh bo loc dropdown (013) — viet TRUOC implementation.

Kiem tra tinh (khong can DB/trinh duyet): doc templates/index.html,
static/css/style.css, static/js/main.js roig assert:
- Moi danh sach (pane) hien co deu co .filter-bar nam trong admin-card tieu de,
  gom it nhat 1 select/input voi id duy nhat va onchange/oninput goi dung han
  render cua pane do (FR-001, FR-006).
- .filter-bar co display:flex + flex-wrap:wrap (SC-003, hop dong muc 3).
- Ham render tuong ung doc gia tri bo loc va Array.filter tren mang da fetch,
  co nhanh "Khong tim thay ket qua" (FR-003, SC-004).

Ghi chu pham vi: pane-products/pane-orders/pane-vouchers/pane-dashboard da bi
spec 009 cat khoi giao dien nen khong xuat hien o day. Spec 015 (FR-005) gop
`pane-quanly` vao `pane-users` (chi con mot bang) nen khong con bo loc ql* va
ham renderDanhSachQuanLy.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

HTML = (REPO / "templates" / "index.html").read_text(encoding="utf-8")
CSS = (REPO / "static" / "css" / "style.css").read_text(encoding="utf-8")
JS = (REPO / "static" / "js" / "main.js").read_text(encoding="utf-8")

# Tap bo loc cua tung pane theo contracts/filter-bar.md (ap dung cho pane con ton tai)
CAU_HINH_BO_LOC = {
    "pane-categories": [
        {"id": "catSearchFilter",       "loai": "input",  "han_dong": "renderAdminCategories()"},
    ],
    "pane-sellers": [
        {"id": "sellerReqFilterStatus", "loai": "select", "han_dong": "renderAdminSellers()"},
    ],
    "pane-users": [
        {"id": "userRoleFilter",        "loai": "select", "han_dong": "renderAdminUsers()"},
        {"id": "userSearchFilter",      "loai": "input",  "han_dong": "renderAdminUsers()"},
    ],
    "spane-products": [
        {"id": "spFilterStock",         "loai": "select", "han_dong": "renderSellerProducts()"},
        {"id": "spSearchFilter",        "loai": "input",  "han_dong": "renderSellerProducts()"},
    ],
    "spane-orders": [
        {"id": "soFilterStatus",        "loai": "select", "han_dong": "renderSellerOrders()"},
    ],
}

TON_THEO_CAU_HINH = ["catSearchFilter", "sellerReqFilterStatus",
                     "userRoleFilter", "userSearchFilter",
                     "spFilterStock", "spSearchFilter", "soFilterStatus"]


def _doan_cua_pane(pane_id):
    """Cat doan HTML cua mot pane (tu id="pane-x" den pane ke tiep)."""
    start = HTML.index(f'id="{pane_id}"')
    cut = HTML[start:]
    # Gioi han den vung SELLER DASHBOARD / POPUP MODALS (DBD khong thuoc pane)
    for boundary in ['id="pane-', 'id="spane-', 'POPUP MODALS']:
        try:
            idx = cut.index(boundary, 1)
            cut = cut[:idx]
            break
        except ValueError:
            continue
    return cut


def _doan_ham(ten_ham):
    """Cat than ham render tu JS (dang `async function ten()` hoac gan bien).
    Dung dinh nghia CUOI CUNG (rfind) vi main.js co the re-assign ham
    (vi du: `async function renderSellerProducts` cu o dau file,
    ban BAN 004 gan lai o cuoi file)."""
    vi_tri = []
    for mau in [f"async function {ten_ham}", f"{ten_ham} = async function",
                f"function {ten_ham}"]:
        start = JS.rfind(mau)
        if start >= 0:
            vi_tri.append(start)
    if not vi_tri:
        raise AssertionError(f"Khong tim thay ham {ten_ham} trong main.js")
    cut = JS[max(vi_tri):]
    # Ket thuc tai khoi `{...}` can bang dau tien
    end_init = cut.index("{")
    brace = 1
    i = end_init + 1
    while brace > 0 and i < len(cut):
        if cut[i] == "{":
            brace += 1
        elif cut[i] == "}":
            brace -= 1
        i += 1
    return cut[:i]


# ── FR-001 + FR-006: moi pane co bo loc tren list, duy nhat, dung handler ──
def test_moi_pane_deu_co_thanh_bo_loc():
    for pane_id, bo_loc in CAU_HINH_BO_LOC.items():
        block = _doan_cua_pane(pane_id)
        assert 'class="filter-bar"' in block, f"{pane_id} thieu .filter-bar"
        for item in bo_loc:
            assert f'id="{item["id"]}"' in block, f"{pane_id} thieu bo loc {item['id']}"


def test_bo_loc_goi_dung_ham_render():
    for pane_id, bo_loc in CAU_HINH_BO_LOC.items():
        block = _doan_cua_pane(pane_id)
        for item in bo_loc:
            loai = item["loai"]
            attr = "onchange" if loai == "select" else "oninput"
            assert f'{attr}="{item["han_dong"]}"' in block, \
                f"{pane_id}:{item['id']} can {attr}=\"{item['han_dong']}\""


def test_id_bo_loc_duy_nhat_toan_trang():
    for bo_loc_id in TON_THEO_CAU_HINH:
        assert HTML.count(f'id="{bo_loc_id}"') == 1, \
            f"id {bo_loc_id} phai xuat hien dung 1 lan (duy nhat toan trang)"


def test_moi_item_trong_thanh_bo_loc_co_nhan_label():
    for pane_id, bo_loc in CAU_HINH_BO_LOC.items():
        block = _doan_cua_pane(pane_id)
        for item in bo_loc:
            assert f'<label for="{item["id"]}">' in block, \
                f"{pane_id}:{item['id']} thieu <label for=...>"


def test_thanh_bo_loc_nam_trong_cung_admin_card_tieu_de():
    for pane_id, bo_loc in CAU_HINH_BO_LOC.items():
        block = _doan_cua_pane(pane_id)
        # Tim admin-card co tieu de h3 trước .filter-bar
        card = block[: block.index('class="filter-bar"')]
        assert "<h3>" in card, f"{pane_id}: bo loc phai nam trong card co tieu de"


# ── CSS (hop dong muc 3): 1 class duy nhat .filter-bar, bien san co ──
def test_css_filter_bar_display_flex_va_wrap():
    seg = CSS[CSS.index(".filter-bar") :]
    seg = seg[: seg.index("}")].lower()
    assert "display:flex" in seg
    assert "flex-wrap:wrap" in seg
    assert "gap:10px" in seg
    assert "align-items:flex-end" in seg


def test_css_filter_bar_chi_dung_bien_san_co():
    seg = CSS[CSS.index(".filter-bar"):]
    seg = seg[: seg.index("/* 11.")] if "/* 11." in seg else seg[:2000]
    assert "var(--border)" in seg or "var(--text-muted)" in seg \
        or "var(--primary)" in seg or "var(--radius)" in seg


def test_css_filter_item_co_loai_doc_label():
    seg = CSS[CSS.index(".filter-bar"):]
    seg = seg[: seg.index("/* 11.")] if "/* 11." in seg else seg[:2000]
    assert ".filter-bar .filter-item" in seg
    assert ".filter-bar label" in seg
    assert ".filter-bar select" in seg and ".filter-bar input" in seg


# ── FR-003: logic loc client trong ham render, khong goi API them ──
def test_render_admin_categories_loc_client():
    seg = _doan_ham("renderAdminCategories")
    assert "getElementById('catSearchFilter')" in seg
    assert ".filter(" in seg
    assert "Không tìm thấy kết quả" in seg
    assert seg.count("fetch(") == 1  # chi 1 lan tai ban dau


def test_render_admin_sellers_loc_client():
    seg = _doan_ham("renderAdminSellers")
    assert "getElementById('sellerReqFilterStatus')" in seg
    assert ".filter(" in seg
    assert "Không tìm thấy kết quả" in seg
    assert seg.count("fetch(") == 1


def test_render_seller_products_loc_client():
    seg = _doan_ham("renderSellerProducts")
    assert "getElementById('spFilterStock')" in seg
    assert "getElementById('spSearchFilter')" in seg
    assert ".filter(" in seg
    assert "Không tìm thấy kết quả" in seg
    assert seg.count("fetch(") == 1


def test_render_seller_orders_loc_client():
    seg = _doan_ham("renderSellerOrders")
    assert "getElementById('soFilterStatus')" in seg
    assert ".filter(" in seg
    assert "Không tìm thấy kết quả" in seg
    assert seg.count("fetch(") == 1


def test_render_admin_users_gian_nguyen_phi_loc_cu():
    seg = _doan_ham("renderAdminUsers")
    assert "getElementById('userRoleFilter')" in seg
    assert "getElementById('userSearchFilter')" in seg
    assert ".filter(" in seg


def test_tinh_toan_ton_kho_seller():
    """Sap het = 1-5, con hang = >5, het hang = 0 (data-model muc 1)."""
    seg = _doan_ham("renderSellerProducts")
    assert "low-stock" in seg and "in-stock" in seg and "out-of-stock" in seg
    assert "soLuong > 5" in seg
    assert "soLuong >= 1 && soLuong <= 5" in seg
    assert "soLuong === 0" in seg