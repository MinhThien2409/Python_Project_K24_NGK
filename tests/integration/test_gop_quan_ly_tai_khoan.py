# -*- coding: utf-8 -*-
"""Test DOM gộp `Quản lý tài khoản Quản lý` vào bảng người dùng — 015 FR-005/006/007.

- FR-005: không còn tab/menu `🛡️ Quản lý` (menu-quanly/pane-quanly/renderDanhSachQuanLy);
          danh sách tài khoản Quản lý hiển thị trong pane-users (bộ lọc vai trò có Quản lý).
- FR-006: người xem Admin → hàng Quản lý có Sửa/Xóa/Thay đổi trạng thái (Khóa/Mở khóa);
          các hàng khác "Chỉ xem".
- FR-007: nút `+ Thêm tài khoản quản lý` ở đầu bảng pane-users (chỉ Admin);
          form tạo/sửa Quản lý (quanLyModal) giữ nguyên, refresh về renderAdminUsers().

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
    """Cắt nội dung một pane trong khối <main> của khu quản trị."""
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


# ── FR-005: gỡ tab/pane Quản lý, gộp vào bảng người dùng ──
def test_khong_con_menu_quan_ly_trong_html():
    assert 'id="menu-quanly"' not in HTML
    assert "🛡️ Quản lý" not in HTML

def test_khong_con_pane_quan_ly_trong_html():
    assert 'id="pane-quanly"' not in HTML
    assert 'id="tblQuanLyBody"' not in HTML
    assert 'id="qlSearchFilter"' not in HTML and 'id="qlStatusFilter"' not in HTML

def test_khong_con_ham_render_danh_sach_quan_ly():
    assert "renderDanhSachQuanLy" not in JS
    seg = _doan_ham("switchAdminTab")
    assert "'quanly'" not in seg, "switchAdminTab còn nhánh tab quanly"

def test_pane_users_gop_danh_sach_quan_ly():
    block = _doan_pane("pane-users")
    assert "userRoleFilter" in block
    # Bộ lọc vai trò có đủ 4 vai trò (lọc được tài khoản Quản lý — FR-005)
    assert '<option value="Quản lý">Quản lý</option>' in block
    assert '<option value="Admin">Quản trị viên</option>' in block
    assert "<th>Trạng thái</th>" in block

# ── FR-007: nút + Thêm tài khoản quản lý ở đầu bảng pane-users ──
def test_pane_users_co_nut_them_tai_khoan_quan_ly():
    block = _doan_pane("pane-users")
    assert "Thêm tài khoản quản lý" in block
    assert 'onclick="openModalTaoQuanLy()"' in block

def test_form_tao_sua_quan_ly_giu_nguyen():
    # form tạo/sửa Quản lý (quanLyModal) vẫn tồn tại — dùng lại từ pane-users
    for id_ in ["quanLyModal", "quanLyEditId", "quanLyTen", "quanLyTaiKhoan",
                "quanLyMatKhau", "quanLyDiaChi"]:
        assert f'id="{id_}"' in HTML, f"Thiếu {id_} trong HTML"
    assert "function openModalTaoQuanLy" in JS
    assert "function openModalSuaQuanLy" in JS

# ── FR-006: Admin → hàng Quản lý có Sửa/Xóa/Khóa-Mở khóa ──
def test_render_quan_ly_admin_co_sua_xoa_khoa_mo():
    seg = _doan_ham("renderAdminUsers")
    # Người xem Admin: hàng vai trò Quản lý (ma_nhom_quyen === 2)
    assert "=== 2" in seg or "=== 2," in seg or "=== 2)" in seg
    assert "✏️ Sửa" in seg and "🗑️ Xóa" in seg
    assert "🔒 Khóa" in seg and "🔓 Mở khóa" in seg
    # Nút Sửa/Xóa gắn đúng hàm quan-ly (tái sử dụng luồng cũ)
    assert "openModalSuaQuanLy(" in seg
    assert "xoaQuanLy(" in seg
    assert "capNhatTrangThaiNhanh(" in seg

def test_render_quan_ly_giu_nhan_chi_xem_va_tai_khoan_cua_ban():
    seg = _doan_ham("renderAdminUsers")
    assert "Chỉ xem" in seg
    assert "Tài khoản của bạn" in seg

# ── FR-013/FR-014: Quản lý → chỉ thao tác hàng Seller ──
def test_render_quan_ly_chi_thao_tac_seller():
    """016 US3: Quản lý thao tác Seller (=== 3), Khách hàng chỉ xem."""
    seg = _doan_ham("renderAdminUsers")
    assert "=== 3" in seg or "=== 3," in seg or "=== 3)" in seg
    assert "🔑 Cấp lại mật khẩu" in seg
    assert "openModalSuaQuanLy(" in seg  # vẫn tồn tại nhưng chỉ admin gọi

    # Không còn nhắm Khách hàng ở nhánh hành động Quản lý (016 US3)
    seg_ql = seg[seg.index("laQuanLy"):seg.index("} else {")]
    assert "=== 4" not in seg_ql

# ── refresh về bảng users sau khi tạo/sửa/xóa Quản lý ──
def test_luu_quan_ly_refresh_bang_users():
    seg = _doan_ham("handleLuuQuanLy")
    assert "renderAdminUsers" in seg
    assert "closeModal('quanLyModal')" in seg

def test_xoa_quan_ly_refresh_bang_users():
    seg = _doan_ham("xoaQuanLy")
    assert "renderAdminUsers" in seg