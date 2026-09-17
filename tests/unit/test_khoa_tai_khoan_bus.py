# -*- coding: utf-8 -*-
"""Unit test UserBus.cap_nhat_trang_thai (feature 002, US3) — khóa/mở khóa tài khoản.

Chặn khóa Admin (giữ nguyên), Quản lý (FR-008), chính mình; cho phép khóa
Seller/Customer; validate status; user không tồn tại. Dùng mock DAO — KHÔNG chạm PobbyDB.
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


# ── CHẶN THEO VAI TRÒ ─────────────────────────────────────────────────────────
def test_khoa_admin_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=1)))
    ket_qua = bus.cap_nhat_trang_thai(2, 5, "banned")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không ai có quyền khóa tài khoản Admin!"


def test_khoa_quan_ly_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=2)))
    ket_qua = bus.cap_nhat_trang_thai(8, 5, "banned")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không thể khóa tài khoản Quản lý!"


def test_tu_khoa_ban_than_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=2)))
    ket_qua = bus.cap_nhat_trang_thai(5, 5, "banned")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Bạn không thể khóa/mở khóa chính tài khoản của mình!"


def test_tu_mo_khoa_ban_than_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=2)))
    ket_qua = bus.cap_nhat_trang_thai(5, 5, "active")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Bạn không thể khóa/mở khóa chính tài khoản của mình!"


# ── CHO PHÉP ──────────────────────────────────────────────────────────────────
def test_khoa_customer_ok(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=4)))
    ket_qua = bus.cap_nhat_trang_thai(2, 5, "banned")
    assert ket_qua["status"] is True
    assert ket_qua["message"] == "Đã khóa tài khoản!"


def test_khoa_seller_ok(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=3)))
    ket_qua = bus.cap_nhat_trang_thai(2, 5, "banned")
    assert ket_qua["status"] is True
    assert ket_qua["message"] == "Đã khóa tài khoản!"


def test_mo_khoa_ok(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=4, trang_thai="banned")))
    ket_qua = bus.cap_nhat_trang_thai(2, 5, "active")
    assert ket_qua["status"] is True
    assert ket_qua["message"] == "Đã mở khóa tài khoản!"


# ── CA BIÊN ───────────────────────────────────────────────────────────────────
def test_trang_thai_khong_hop_le(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=4)))
    ket_qua = bus.cap_nhat_trang_thai(2, 5, "xoa")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Trạng thái không hợp lệ!"


def test_thieu_ma_user(mock_user_dao):
    bus = _bus(mock_user_dao())
    ket_qua = bus.cap_nhat_trang_thai(2, None, "banned")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Thiếu mã user!"


def test_user_khong_ton_tai(mock_user_dao):
    bus = _bus(mock_user_dao())

    def lay_thong_tin_user(ma_user):
        return None

    bus.dao.lay_thong_tin_user = lay_thong_tin_user
    ket_qua = bus.cap_nhat_trang_thai(2, 999, "banned")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tài khoản không tồn tại!"