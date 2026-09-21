# -*- coding: utf-8 -*-
"""Test nút `Xem chi tiết đơn hàng` của Seller — 015 FR-026/027/028.

- FR-026: mỗi đơn trong spane-orders có nút riêng, độc lập với nút cập nhật trạng thái.
- FR-027: modal chi tiết đủ trường: mã đơn, ngày đặt, trạng thái, người nhận + SĐT,
          địa chỉ giao, phương thức thanh toán, mặt hàng (tên, số lượng, đơn giá,
          thành tiền), tạm tính, chiết khấu, phí ship, tổng cộng, ghi chú ("—" khi trống).
- FR-028: dữ liệu chỉ lấy từ đơn thuộc shop của Seller qua `/api/seller/don-hang`
          (không hiển thị đơn shop khác — dữ liệu đã lọc ở DAO).

KHÔNG cần DB — đọc tĩnh templates/index.html + static/js/main.js.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

HTML = (REPO / "templates" / "index.html").read_text(encoding="utf-8")
JS = (REPO / "static" / "js" / "main.js").read_text(encoding="utf-8")


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


def _doan_pane(pane_id):
    """Cắt một pane trong khối seller dashboard."""
    start = HTML.index(f'id="{pane_id}"')
    cut = HTML[start:]
    for boundary in ['id="pane-', 'id="spane-', 'POPUP MODALS']:
        try:
            idx = cut.index(boundary, 1)
            cut = cut[:idx]
            break
        except ValueError:
            continue
    return cut


# ── FR-026: nút Xem chi tiết trên từng đơn, độc lập với cập nhật ──
def test_spane_orders_co_cot_chi_tiet():
    block = _doan_pane("spane-orders")
    assert "<th>Chi tiết</th>" in block

def test_moi_don_co_nut_xem_chi_tiet_va_nut_trang_thai():
    seg = _doan_ham("renderSellerOrders")
    assert "Xem chi tiết đơn hàng" in seg
    assert "showChiTietDonHang(" in seg or "openChiTietDonHang(" in seg
    # Các nút cập nhật trạng thái vẫn còn (độc lập — FR-026)
    assert "sellerCapNhatDon(" in seg

def test_render_seller_orders_dung_endpoint_cua_shop():
    seg = _doan_ham("renderSellerOrders")
    assert "/api/seller/don-hang" in seg, "Phải lấy đơn từ /api/seller/don-hang (FR-028)"
    assert "/api/don-hang/cua-seller" not in seg, "Endpoint cũ/cày hỏng không được dùng"

def test_cap_nhat_trang_thai_dung_endpoint_seller():
    seg = _doan_ham("sellerCapNhatDon")
    assert "/api/seller/don-hang/" in seg
    assert "/trang-thai" in seg

# ── FR-027: modal chi tiết đầy đủ 13 trường ──
def test_co_modal_chi_tiet_don_hang_trong_html():
    assert 'id="sellerOrderDetailModal"' in HTML

def test_show_chi_tiet_du_truong_giao_nhan_thanh_toan():
    seg = _doan_ham("showChiTietDonHang")
    for token in ["OrderId", "CreatedAt", "Status", "ReceiverName",
                  "ReceiverPhone", "ShippingAddress", "PaymentMethod"]:
        assert token in seg, f"Thiếu trường {token} trong chi tiết đơn"

def test_show_chi_tiet_du_truong_tien_va_mat_hang():
    seg = _doan_ham("showChiTietDonHang")
    for token in ["SubTotal", "DiscountAmount", "ShippingFee", "TotalAmount", "Note"]:
        assert token in seg, f"Thiếu trường tiền {token}"
    # Danh sách mặt hàng: đơn giá, số lượng, thành tiền từng dòng
    for token in ["UnitPrice", "Quantity", "TotalPrice", "ProductName"]:
        assert token in seg, f"Thiếu trường mặt hàng {token}"

def test_show_chi_tiet_chong_xss_bang_textcontent():
    seg = _doan_ham("showChiTietDonHang")
    assert "textContent" in seg

# ── FR-028: chi tiết chỉ hiển thị dữ liệu thuộc shop ──
def test_danh_sach_don_chi_lay_tu_nguon_cua_shop():
    # Nguồn dữ liệu duy nhất là /api/seller/don-hang (đã lọc theo store ở DAO);
    # không có fetch chi tiết theo order_id nào khác (không lộ đơn shop khác).
    seg = _doan_ham("renderSellerOrders")
    assert seg.count("fetch(") == 1, "Không gọi thêm endpoint nào khác khi tải đơn"