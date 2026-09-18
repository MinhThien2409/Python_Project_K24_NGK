"""Static test customer SQL + ownership — 005 T006/T041.

Không cần DB: đọc file nguồn dạng text, assert placeholder ? và gate session.
Viết TRƯỚC implementation (test-first Đỏ→Xanh).
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))


def _doc(duong_dan):
    return (REPO / duong_dan).read_text(encoding="utf-8")


def _bo_dong_log(src):
    """Loai dong logging/import logging truoc khi soi `%s` SQL (007: DAO dung logging)."""
    return "\n".join(
        d for d in src.splitlines()
        if "log" not in d.lower()
    )


# ── SQL toàn placeholder ? (không %s / NOW() / lastrowid) ──
def test_gio_hang_dao_khong_con_mysql_dialect():
    src = _bo_dong_log(_doc("back_end/DAO/GioHangDao.py"))
    assert "%s" not in src
    assert "NOW()" not in _doc("back_end/DAO/GioHangDao.py")
    assert "lastrowid" not in _doc("back_end/DAO/GioHangDao.py")


def test_don_hang_dao_khong_con_mysql_dialect():
    src = _bo_dong_log(_doc("back_end/DAO/DonHangDao.py"))
    assert "%s" not in src
    assert "lastrowid" not in src
    assert "OUTPUT INSERTED" in src


def test_san_pham_dao_tim_kiem_dung_placeholder():
    src = _doc("back_end/DAO/SanPhamDao.py")
    assert "def tim_kiem" in src
    assert "LIKE ?" in src
    assert "IsActive = 1" in src
    assert "%s" not in _bo_dong_log(src)


def test_san_pham_dao_co_lay_thong_tin_kho():
    src = _doc("back_end/DAO/SanPhamDao.py")
    assert "def lay_thong_tin_kho" in src
    assert "Quantity" in src and "IsActive" in src and "Price" in src


# ── BUS không SQL, giá từ DB, ownership ở BUS ──
def test_bus_khong_chua_sql():
    for f in ["back_end/BUS/SanPhamBus.py", "back_end/BUS/GioHangBus.py",
              "back_end/BUS/DonHangBus.py", "back_end/BUS/UserBus.py"]:
        src = _doc(f)
        assert "SELECT" not in src, f"{f} chứa SQL trong BUS"
        assert "INSERT" not in src, f"{f} chứa SQL trong BUS"


def test_gio_hang_bus_lay_gia_tu_db():
    src = _doc("back_end/BUS/GioHangBus.py")
    assert "lay_thong_tin_kho" in src


def test_don_hang_bus_co_hoa_don_ownership():
    src = _doc("back_end/BUS/DonHangBus.py")
    assert "lay_hoa_don_cua_toi" in src
    assert "không có quyền xem hóa đơn" in src


def test_user_bus_co_ownership_wrapper():
    src = _doc("back_end/BUS/UserBus.py")
    assert "cap_nhat_thong_tin_cua_toi" in src
    assert "doi_mat_khau_cua_toi" in src
    assert "Không thể thao tác trên tài khoản khác!" in src


# ── Route dùng session, không tin user_id / giá client ──
def test_cart_checkout_history_gate_session():
    app = _doc("app.py")
    for route in ["/api/gio-hang/them", "/api/gio-hang/cap-nhat",
                  "/api/gio-hang/xoa", "/api/don-hang/dat-hang",
                  "/api/don-hang/cua-toi", "/api/don-hang/hoa-don"]:
        assert route in app, f"thiếu route {route}"
    assert "kiem_tra_nguoi_dung_hoat_dong" in app


def test_doi_mat_khau_dung_session():
    app = _doc("app.py")
    doan = app[app.find("/api/doi-mat-khau"):]
    assert "session" in doan
