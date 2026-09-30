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
def test_quan_ly_branch_co_nut_khoa_va_cap_lai_mat_khau():
    seg_ql = SEG[SEG.index("laQuanLy"):]
    seg_ql = seg_ql[:seg_ql.index("} else {")]
    # Nút Khóa/Mở khóa: thẻ mở dùng ternary btn-edit/btn-cancel + nhãn có sẵn
    assert "<button class=\"admin-action-btn ${isBanned ? 'btn-edit' : 'btn-cancel'}\"" in seg_ql
    assert "🔒 Khóa" in seg_ql and "🔓 Mở khóa" in seg_ql
    assert "moModalCapLaiMatKhau(" in seg_ql
    assert "🔑 Cấp lại mật khẩu" in seg_ql
