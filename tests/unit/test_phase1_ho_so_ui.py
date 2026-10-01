# -*- coding: utf-8 -*-
"""Phase 1 — kiểm tra chuẩn hóa (trim) + biên UI tĩnh.

- BUS profile phải LƯU giá trị đã trim (không lưu khoảng trắng thừa).
- Template phải có ô "Xác nhận mật khẩu mới" (Task 6, Q2: chỉ ở FE).
- Modal hồ sơ phải có nút Lưu ở trạng thái `disabled` ban đầu và handler
  kiểm tra thay đổi (Task 5).

Tĩnh — KHÔNG cần DB/trình duyệt.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from back_end.BUS.UserBus import UserBus


class _DaoGhiNhan:
    """Ghi lại đúng tham số nhận được để kiểm chứng trim."""

    def __init__(self):
        self.tham_so = None

    def cap_nhat_user(self, ma_user, ten_user, dia_chi, sdt, cmnd):
        self.tham_so = {
            "ma_user": ma_user, "ten_user": ten_user, "dia_chi": dia_chi,
            "sdt": sdt, "cmnd": cmnd,
        }
        return True


# ── Task 4: trim phải được LƯU xuống DAO ────────────────────────────────────
def test_cap_nhat_profile_luu_gia_tri_da_trim():
    bus = UserBus()
    dao = _DaoGhiNhan()
    bus.dao = dao
    ket_qua = bus.cap_nhat_user(5, "  Nguyễn Văn A  ", "  Hà Nội  ",
                                "0901234567", " 001  ")
    assert ket_qua["status"] is True
    assert dao.tham_so["ten_user"] == "Nguyễn Văn A"
    assert dao.tham_so["dia_chi"] == "Hà Nội"
    assert dao.tham_so["sdt"] == "0901234567"
    assert dao.tham_so["cmnd"] == "001"


def test_cap_nhat_profile_khong_goi_dao_khi_ten_rong():
    bus = UserBus()
    dao = _DaoGhiNhan()
    bus.dao = dao
    ket_qua = bus.cap_nhat_user(5, "   ", "HN", "0901234567", "001")
    assert ket_qua["status"] is False
    assert dao.tham_so is None


# ── Task 6: ô xác nhận mật khẩu ở FE ────────────────────────────────────────
def test_template_co_o_xac_nhan_mat_khau_moi():
    html = (REPO / "templates" / "index.html").read_text(encoding="utf-8")
    assert 'id="pwXacNhan"' in html
    assert 'id="pwMoi"' in html
    assert 'id="pwCu"' in html


def test_js_doi_mat_khau_kiem_tra_xac_nhan():
    js = (REPO / "static" / "js" / "main.js").read_text(encoding="utf-8")
    assert "pwXacNhan" in js
    assert "không khớp" in js
    # Backend giữ nguyên chữ ký 2 tham số (Q2: confirm chỉ ở FE)
    assert "mat_khau_cu: cu, mat_khau_moi: moi" in js


# ── Task 5: nút Lưu disabled cho tới khi có thay đổi ───────────────────────
def test_js_co_ham_kiem_tra_thay_doi_profile():
    js = (REPO / "static" / "js" / "main.js").read_text(encoding="utf-8")
    assert "kiemTraThayDoiProfile" in js
    assert "btnSaveProfile" in js
    assert "disabled" in js
    # Ghi nhớ mốc gốc để phát hiện hoàn tác
    assert "profileGoc" in js


# ── Task 6: backend vẫn chỉ nhận (mat_khau_cu, mat_khau_moi) ───────────────
def test_backend_doi_mat_khau_khong_doi_chu_ky():
    app_src = (REPO / "app.py").read_text(encoding="utf-8")
    assert "mat_khau_moi = data.get('mat_khau_moi')" in app_src
    assert "xac_nhan" not in app_src
