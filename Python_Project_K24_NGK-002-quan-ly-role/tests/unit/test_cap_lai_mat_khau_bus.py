# -*- coding: utf-8 -*-
"""Unit test UserBus.cap_lai_mat_khau (feature 002, US4) — cấp lại mật khẩu.

Sinh ngẫu nhiên (secrets, ≥ 6 ký tự) hoặc nhận mật khẩu Quản lý nhập (≥ 6 ký tự);
chặn mục tiêu là Admin; user không tồn tại từ chối; user đang banned vẫn giữ
banned sau khi reset (mật khẩu mới không tự mở khóa). Mock DAO — KHÔNG chạm PobbyDB.
"""

import pytest

from back_end.BUS.UserBus import UserBus


def _bus(mock):
    bus = UserBus()
    bus.dao = mock
    return bus


def _thong_tin(role_id, trang_thai="active", fullname="Người dùng"):
    return {
        "UserId": 5, "FullName": fullname, "Role_Id": role_id,
        "trang_thai": trang_thai,
    }


# ── SINH NGẪU NHIÊN ──────────────────────────────────────────────────────────
def test_sinh_ngau_nhien_hop_le(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=4)))
    ghi_nhan = {}

    def cap_nhat_mat_khau(ma_user, mat_khau_moi):
        ghi_nhan["ma_user"] = ma_user
        ghi_nhan["mat_khau_moi"] = mat_khau_moi
        return True

    bus.dao.cap_nhat_mat_khau = cap_nhat_mat_khau

    ket_qua = bus.cap_lai_mat_khau(2, 5, None)
    assert ket_qua["status"] is True
    mat_khau_moi = ket_qua["data"]["mat_khau_moi"]
    assert len(mat_khau_moi) >= 6
    assert ket_qua["data"]["ma_user"] == 5
    assert ket_qua["data"]["ten_user"] == "Người dùng"
    assert ghi_nhan["ma_user"] == 5
    assert ghi_nhan["mat_khau_moi"] == mat_khau_moi  # trả đúng mật khẩu đã ghi


def test_sinh_ngau_nhien_chuoi_khong_thay_doi_ket_qua_khi_mat_khau_moi_rong(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=4)))
    ket_qua = bus.cap_lai_mat_khau(2, 5, "")
    assert ket_qua["status"] is True
    assert len(ket_qua["data"]["mat_khau_moi"]) >= 6


# ── QUẢN LÝ NHẬP MẬT KHẨU ────────────────────────────────────────────────────
def test_mat_khau_nhap_du_6_ky_tu_ok(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=4)))
    ket_qua = bus.cap_lai_mat_khau(2, 5, "matkhau67890")
    assert ket_qua["status"] is True
    assert ket_qua["data"]["mat_khau_moi"] == "matkhau67890"


def test_mat_khau_nhap_ngan_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=4)))
    ket_qua = bus.cap_lai_mat_khau(2, 5, "12345")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Mật khẩu phải có ít nhất 6 ký tự!"


# ── CHẶN MỤC TIÊU LÀ ADMIN ───────────────────────────────────────────────────
def test_cap_lai_mat_khau_admin_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=1)))
    ket_qua = bus.cap_lai_mat_khau(2, 1, "matkhau67890")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không thể cấp lại mật khẩu cho tài khoản Admin!"


# ── USER KHÔNG TỒN TẠI ───────────────────────────────────────────────────────
def test_user_khong_ton_tai_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao())

    def lay_thong_tin_user(ma_user):
        return None

    bus.dao.lay_thong_tin_user = lay_thong_tin_user
    ket_qua = bus.cap_lai_mat_khau(2, 999, None)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tài khoản không tồn tại!"


# ── CA BIÊN: USER BANNED VẪN GIỮ BANNED ──────────────────────────────────────
def test_reset_user_banned_van_giu_banned(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=4, trang_thai="banned")))
    ket_qua = bus.cap_lai_mat_khau(2, 5, "matkhau67890")
    assert ket_qua["status"] is True
    thong_tin = bus.dao.lay_thong_tin_user(5)
    assert thong_tin["trang_thai"] == "banned"


def test_dao_that_bai_tra_loi_ro_rang(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=4), mat_khau_moi_ok=False))
    ket_qua = bus.cap_lai_mat_khau(2, 5, "matkhau67890")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Lỗi cập nhật mật khẩu!"