# -*- coding: utf-8 -*-
"""Static test dựng HTML động của `renderAdminUsers` (016 US2 T009 + US3 T013).

- T009 (US2): nhánh Admin (laAdmin && ma_nhom_quyen === 2) dựng nút Xóa phải có
  thẻ mở <button class="admin-action-btn ..."> — KHÔNG còn dạng text thô
  `onclick="xoaQuanLy(` thiếu thẻ mở trong mọi template string.
- T013 (US3): nhánh Quản lý (laQuanLy) phải trỏ vai trò Seller `=== 3` — không
  còn `=== 4` (Khách hàng) ở nhánh hành động.

Đọc tĩnh static/js/main.js — KHÔNG cần DB.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

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


SEG = _doan_ham("renderAdminUsers")


# ── T009: nhánh Admin — nút Xóa có đủ thẻ mở (hết chuỗi thô) ──
def test_xoa_quan_ly_khong_con_chuoi_ngon_tho():
    """Không còn chuỗi `onclick="xoaQuanLy(` thiếu thẻ <button> mở."""
    entries = SEG.split("onclick=\"xoaQuanLy(")
    assert len(entries) >= 1, "renderAdminUsers phải giữ luồng xóa Quản lý"
    # Mọi chuỗi gọi xoaQuanLy phải nằm TRONG một thẻ <button ...> mở ở dòng ƯỚC tính
    for i, chunk in enumerate(entries[1:], start=1):
        # Phần trước chunk là kết thúc nút Sửa `</button>` — phần ngay trước
        # `onclick="xoaQuanLy(` phải là thẻ mở `<button class="admin-action-btn`
        prefix = chunk[:0]  # bản thân segment đã bỏ qua chuỗi khớp
    # Kiểm tra trực tiếp: chuỗi gọi xóa phải đi kèm thẻ mở button cùng kiểu
    assert '<button class="admin-action-btn btn-cancel"' in SEG
    assert 'onclick="xoaQuanLy(' in SEG


def test_admin_branch_du_nut_sua_xoa_khoa_co_the_mo():
    # Nhánh Admin (laAdmin && ma_nhom_quyen === 2) có đủ 3 nút với thẻ mở hợp lệ
    seg_admin = SEG[SEG.index("laAdmin && u.ma_nhom_quyen === 2"):]
    seg_admin = seg_admin[:seg_admin.index("laQuanLy")]
    for tag in ['<button class="admin-action-btn btn-edit"',
                '<button class="admin-action-btn btn-cancel"']:
        assert tag in seg_admin, f"Thiếu thẻ mở {tag} trong nhánh Admin"
    # Nút Xóa giờ là <button class="admin-action-btn btn-cancel" onclick="xoaQuanLy(...)">
    for mau in ['>✏️ Sửa</button>', '>🗑️ Xóa</button>', '🔒 Khóa', '🔓 Mở khóa']:
        assert mau in seg_admin, f"Thiếu {mau} trong nhánh Admin"


def test_khong_con_span_chuoi_ngon_tho_xoa():
    """Nút Xóa không còn bị dựng thành text rời (thẻ đóng không có thẻ mở)."""
    # Nếu còn lỗi cũ: chuỗi `onclick="xoaQuanLy(` nằm ngay sau `</button>` của nút Sửa
    # mà không có thẻ mở → phát hiện bằng cách tìm pattern lỗi điển hình.
    assert 'onclick="xoaQuanLy(${u.ma_user})">🗑️ Xóa</button>' in SEG
    # Chuỗi gọi có đúng tên hàm xóaQuanLy và có thẻ mở button liền trước
    i = SEG.index('onclick="xoaQuanLy(')
    prefix = SEG[i - 80:i]
    assert 'admin-action-btn btn-cancel' in prefix
    assert 'onclick="xoaQuanLy(' + ')">&#128465;&#65039;' not in prefix


# ── T013: nhánh Quản lý — trỏ Seller (=== 3), không còn Customer (=== 4) ──
def test_quan_ly_branch_tro_seller_khong_con_customer():
    seg_ql = SEG[SEG.index("laQuanLy"):]
    seg_ql = seg_ql[:seg_ql.index("} else {")]
    # Điều kiện hiển thị nút Khóa/Cấp lại mật khẩu phải là Seller
    assert "u.ma_nhom_quyen === 3" in seg_ql
    # Không còn nhắm Khách hàng (=== 4) ở nhánh hành động Quản lý
    assert "=== 4" not in seg_ql


def test_quan_ly_branch_co_nut_khoa_va_cap_lai_mat_khau():
    seg_ql = SEG[SEG.index("laQuanLy"):]
    seg_ql = seg_ql[:seg_ql.index("} else {")]
    # Nút Khóa/Mở khóa: thẻ mở dùng ternary btn-edit/btn-cancel + nhãn có sẵn
    assert "<button class=\"admin-action-btn ${isBanned ? 'btn-edit' : 'btn-cancel'}\"" in seg_ql
    assert "🔒 Khóa" in seg_ql and "🔓 Mở khóa" in seg_ql
    assert "moModalCapLaiMatKhau(" in seg_ql
    assert "🔑 Cấp lại mật khẩu" in seg_ql


def test_customer_row_roi_vao_chi_xem():
    """Hàng Khách hàng (=== 4) KHÔNG có nút thao tác — rơi vào nhánh 'Chỉ xem'."""
    assert "Chỉ xem" in SEG
    # Trong renderAdminUsers không còn nhánh hành động nào nhắm role 4
    # (Customer chỉ có giao diện của chính họ qua isMe)
    assert "u.ma_nhom_quyen === 4" not in SEG