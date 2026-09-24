"""Test DOM kênh Người bán sau tái cấu trúc — 010 + 015 (test-first Đỏ→Xanh).

US1 (T004): #sellerDashboard dùng đúng bộ component quản trị: .admin-layout,
            .admin-menu-item, .admin-pane, id convention smenu-/spane-.
US2 (T008): #spane-overview không còn form sửa shop; #spane-shop chứa form.
US3 (T014): #spane-products không còn thao tác đổi giá; #spane-gia chứa bảng giá.
015 (T015): menu + pane `Quản lý nhập hàng` (spane-nhaphang) (FR-016/017);
            #spane-products không còn nút 📦 Nhập và 🗑️ Ẩn, cột Trạng thái là
            pill 4 mức (FR-020/023/024/025); luồng 🙈 Ẩn/👁️ Hiện giữ nguyên.

KHÔNG cần DB — đọc tĩnh templates/index.html + static/js/main.js theo contract
contracts/seller-ui-map.md.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

HTML = (REPO / "templates" / "index.html").read_text(encoding="utf-8")
JS = (REPO / "static" / "js" / "main.js").read_text(encoding="utf-8")


def _seller_block():
    """Cắt khối DOM #sellerDashboard từ HTML (kết thúc trước khối POPUP MODALS)."""
    start = HTML.index('id="sellerDashboard"')
    end = HTML.index("POPUP MODALS")
    return HTML[start:end]


def _block_of(tag_id):
    """Cắt nội dung một pane/mục theo id từ khối seller."""
    block = _seller_block()
    start = block.index(f'id="{tag_id}"')
    # Kết thúc tại thẻ đóng </div> của phần tử có id (tìm vị trí id kế tiếp để giới hạn)
    cut = block[start:]
    return cut


# ── US1 (T004): bố cục giống trang quản trị ──
def test_seller_dashboard_dung_admin_layout():
    block = _seller_block()
    assert '<div class="admin-layout">' in block  # 2 cột, không style riêng
    assert '<aside class="admin-menu">' in block
    assert '<main class="admin-main">' in block


def test_menu_seller_dung_admin_menu_item():
    block = _seller_block()
    for mid in ["smenu-overview", "smenu-products", "smenu-orders",
                "smenu-nhaphang", "smenu-shop", "smenu-gia"]:
        assert f'id="{mid}"' in block, f"Thiếu mục menu {mid}"
    assert block.count('id="smenu-') == 6


def test_pane_seller_dung_admin_pane():
    block = _seller_block()
    for pid in ["spane-overview", "spane-products", "spane-orders",
                "spane-nhaphang", "spane-shop", "spane-gia"]:
        assert f'id="{pid}"' in block, f"Thiếu pane {pid}"
    assert block.count('class="admin-pane"') == 6


def test_switch_seller_tab_dung_convention_va_co_nhanh_moi():
    seg = JS[JS.index("async function switchSellerTab"):]
    seg = seg[:seg.index("\n}\n") + 3]
    for nhanh in ["'overview'", "'products'", "'orders'", "'nhaphang'",
                  "'shop'", "'gia'"]:
        assert nhanh in seg, f"switchSellerTab thiếu nhánh {nhanh}"
    assert "renderSellerNhapHang" in seg
    assert "renderTrangShop" in seg
    assert "renderGiaBan" in seg
    assert "smenu-" in seg and "spane-" in seg


# ── US2 (T008): tách "Trang shop" ──
def test_overview_khong_con_form_sua_shop():
    block = _block_of("spane-overview").split('id="spane-products"')[0]
    for field in ["sellerShopName", "sellerShopDesc", "sellerShopThamNien"]:
        assert field not in block, f"spane-overview còn trường {field}"


def test_spane_shop_chua_form_sua_shop():
    block = _block_of("spane-shop").split('id="spane-gia"')[0]
    for field in ["sellerShopName", "sellerShopDesc", "sellerShopThamNien"]:
        assert f'id="{field}"' in block, f"spane-shop thiếu trường {field}"
    assert "sellerLuuTrangShop" in block


def test_render_overview_khong_tao_form_shop_trong_js():
    seg = JS[JS.index("renderSellerOverview = async function"):]
    seg = seg[:seg.index("async function renderTrangShop")]
    assert "sellerShopName" not in seg, "renderSellerOverview vẫn tạo form shop (JS)"
    assert "/api/seller/trang-shop" not in seg, "renderSellerOverview vẫn đọc trang-shop (JS)"


def test_co_ham_render_trang_shop():
    assert "async function renderTrangShop" in JS
    assert "/api/seller/trang-shop" in JS


# ── US3 (T014): tách "Quản lý giá bán" ──
def test_spane_products_khong_con_doi_gia():
    block = _block_of("spane-products").split('id="spane-orders"')[0]
    assert "tblSellerGiaBody" not in block
    assert "sellerDoiGia" not in block


def test_spane_gia_chua_bang_gia():
    block = _block_of("spane-gia")
    assert "<table>" in block
    assert 'id="tblSellerGiaBody"' in block


def test_render_products_khong_tao_nut_doi_gia_trong_js():
    start = JS.rindex("async function renderSellerProducts()")
    seg = JS[start:]
    seg = seg[:seg.index("async function openEditSellerProduct")]
    assert "sellerDoiGia" not in seg, "renderSellerProducts vẫn tạo nút đổi giá (JS)"


def test_co_ham_render_gia_ban():
    assert "async function renderGiaBan" in JS
    assert "/api/seller/san-pham" in JS
    assert "/gia" in JS


# ── 015 US: tab Quản lý nhập hàng (FR-016/017) ──
def test_spane_nhaphang_chua_giao_dien_nhap_hang():
    block = _block_of("spane-nhaphang")
    assert '<div class="admin-card">' in block
    assert "spNhapHangBody" in block, "Thiếu bảng danh sách sản phẩm nhập hàng"
    # Nút Nhập được tạo động trong JS (hàm nhapHangSeller) — HTML chỉ gắn ô tìm kiếm
    assert 'oninput="renderSellerNhapHang()"' in block
    assert "nhập hàng" in block.lower()

def test_co_ham_render_nhap_hang():
    assert "async function renderSellerNhapHang" in JS
    assert "spNhapHangBody" in JS
    assert "nhapHangSeller" in JS
    assert "/nhap-hang" in JS, "Thiếu endpoint nhập hàng trong JS"

# ── 015 FR-020: bỏ nút Nhập + 🗑️ Ẩn khỏi bảng sản phẩm ──
def test_spane_products_khong_con_nut_nhap_va_xoa():
    block = _block_of("spane-products")
    assert "📦 Nhập" not in block
    assert "🗑️ Ẩn" not in block
    assert "deleteSellerProduct" not in block
    assert "sellerNhapHang" not in block, "Nút nhập phải chuyển sang tab nhập hàng"

def test_render_products_khong_tao_nut_nhap_va_xoa_trong_js():
    start = JS.rindex("async function renderSellerProducts()")
    seg = JS[start:]
    seg = seg[:seg.index("async function openEditSellerProduct")]
    assert "🗑️ Ẩn" not in seg, "renderSellerProducts vẫn tạo nút xóa (JS)"
    assert "📦 Nhập" not in seg, "renderSellerProducts vẫn tạo nút nhập (JS)"
    assert "deleteSellerProduct" not in seg
    assert "sellerAnHien" in seg, "Luồng ẩn/hiện phải giữ nguyên (FR-020)"

def test_js_khong_con_delete_san_pham():
    assert "deleteSellerProduct" not in JS, "deleteSellerProduct phải bị gỡ (FR-021)"
    assert "🗑️ Ẩn" not in JS

# ── 015 FR-023/024/025: cột Trạng thái = pill 4 mức ──
def test_cot_trang_thai_thay_cho_da_ban():
    block = _block_of("spane-products")
    assert "<th>Trạng thái</th>" in block
    assert "<th>Đã bán</th>" not in block

def test_pill_trang_thai_sp_co_4_muc_va_so_da_ban():
    start = JS.rindex("async function renderSellerProducts()")
    seg = JS[start:]
    seg = seg[:seg.index("async function openEditSellerProduct")]
    # 4 mức pill (FR-024) — id class/quy ước đủ phân biệt
    assert "status-hidden" in seg        # Đang ẩn
    assert "status-cancelled" in seg     # Hết hàng
    assert "status-pending" in seg       # Sắp hết (1–5)
    assert "user-status-active" in seg   # Đang bán
    # SoldCount vẫn hiển thị dưới pill (FR-025)
    assert "Đã bán" in seg
    assert "sold" in seg or "SoldCount" in seg