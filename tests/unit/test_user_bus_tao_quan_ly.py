# -*- coding: utf-8 -*-
"""Unit test tạo tài khoản Quản lý (008 US3, T029) — `UserBus.tao_quan_ly`.

- Tạo thành công → status True, data có ma_user/ten_user/tendangnhap.
- Trùng tên đăng nhập → từ chối, KHÔNG gọi them_quan_ly.
- Mật khẩu dưới 6 ký tự → từ chối.
- Yêu cầu vai trò Admin (qua `vai_tro` hoặc `ma_nhom_quyen`) → từ chối.

Mock UserDao — KHÔNG chạm PobbyDB thật.
"""

import pytest

from back_end.BUS.UserBus import UserBus


def _bus(dao):
    bus = UserBus()
    bus.dao = dao
    return bus


# ── Tạo thành công ───────────────────────────────────────────────────────────
def test_tao_quan_ly_thanh_cong(mock_user_dao):
    dao = mock_user_dao(ton_tai_tendangnhap=False, them_quan_ly_ok=True)

    kq = _bus(dao).tao_quan_ly("Nguyễn Văn B", "quanly_moi", "matkhau123",
                                sdt="0912345678", dia_chi="Hà Nội")

    assert kq["status"] is True
    assert kq["message"] == "Đã tạo tài khoản Quản lý!"
    assert kq["data"]["ma_user"] == 100  # id giả từ MockUserDao
    assert kq["data"]["tendangnhap"] == "quanly_moi"


def test_tao_quan_ly_khong_ten_khong_tendangnhap_tu_choi(mock_user_dao):
    dao = mock_user_dao()
    dao.them_quan_ly = lambda *a, **k: pytest.fail("KHÔNG được gọi DAO")

    kq = _bus(dao).tao_quan_ly("", "", "123456")

    assert kq["status"] is False
    assert "điền đầy đủ" in kq["message"]


# ── Trùng tên đăng nhập ──────────────────────────────────────────────────────
def test_trung_tendangnhap_tu_choi(mock_user_dao):
    dao = mock_user_dao(ton_tai_tendangnhap=True)
    dao.them_quan_ly = lambda *a, **k: pytest.fail("KHÔNG được gọi DAO khi trùng")

    kq = _bus(dao).tao_quan_ly("Nguyễn Văn B", "quanly_trung", "matkhau123")

    assert kq["status"] is False
    assert "đã có người sử dụng" in kq["message"]


# ── Mật khẩu ngắn ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("mat_khau", ["123", "12345"])
def test_mat_khau_duoi_6_ky_tu_tu_choi(mock_user_dao, mat_khau):
    dao = mock_user_dao()
    dao.them_quan_ly = lambda *a, **k: pytest.fail("KHÔNG được gọi DAO")

    kq = _bus(dao).tao_quan_ly("Nguyễn Văn B", "quanly_ngan", mat_khau)

    assert kq["status"] is False
    assert "ít nhất 6 ký tự" in kq["message"]


# ── Yêu cầu vai trò Admin → từ chối ─────────────────────────────────────────
@pytest.mark.parametrize("vai_tro_admin", ["Admin", "admin", 1, "1"])
def test_yeu_cau_vai_tro_admin_tu_choi(mock_user_dao, vai_tro_admin):
    dao = mock_user_dao()
    dao.them_quan_ly = lambda *a, **k: pytest.fail("KHÔNG được gọi DAO")

    kq = _bus(dao).tao_quan_ly("Nguyễn Văn B", "quanly_moi", "matkhau123",
                                vai_tro=vai_tro_admin)

    assert kq["status"] is False
    assert "Không thể tạo thêm tài khoản Admin!" in kq["message"]


def test_yeu_cau_admin_qua_ma_nhom_quyen_tu_choi(mock_user_dao):
    dao = mock_user_dao()
    dao.them_quan_ly = lambda *a, **k: pytest.fail("KHÔNG được gọi DAO")

    kq = _bus(dao).tao_quan_ly("Nguyễn Văn B", "quanly_moi", "matkhau123",
                                ma_nhom_quyen=1)

    assert kq["status"] is False
    assert "Không thể tạo thêm tài khoản Admin!" in kq["message"]


# ── DAO lỗi → trả về message hệ thống ───────────────────────────────────────
def test_dao_loi_tra_ve_message_loi_he_thong(mock_user_dao):
    dao = mock_user_dao(ton_tai_tendangnhap=False, them_quan_ly_ok=False)

    kq = _bus(dao).tao_quan_ly("Nguyễn Văn B", "quanly_loi", "matkhau123")

    assert kq["status"] is False
    assert "Lỗi hệ thống" in kq["message"]