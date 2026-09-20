# -*- coding: utf-8 -*-
"""Unit test UserBus.cap_nhat_trang_thai (feature 002 US3, 015 FR-008/009).

Chặn khóa Admin (mọi actor), ghi trạng thái Quản lý khi người thao tác KHÔNG phải
Admin (FR-008/009), chính mình; cho phép Admin ghi trạng thái Quản lý và khóa/
mở khóa Seller/Customer; validate status; user không tồn tại. Dùng mock DAO —
KHÔNG chạm PobbyDB. Tham số vai_tro_nguoi_thao_tac mặc định None tương đương
"không phải Admin" (giữ hành vi test gọi 3 tham số cũ).
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

# ── CHẶN THEO VAI TRÒ (015 FR-008/009) ────────────────────────────────────────
def test_khoa_admin_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=1)))
    ket_qua = bus.cap_nhat_trang_thai(2, 5, "banned")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không ai có quyền khóa tài khoản Admin!"

def test_admin_khong_khoa_duoc_admin_khac(mock_user_dao):
    """FR-009(2): kể cả Admin cũng không khóa được Admin — vai trò Admin actor."""
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=1)))
    ket_qua = bus.cap_nhat_trang_thai(1, 5, "banned", "Admin")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không ai có quyền khóa tài khoản Admin!"

def test_khoa_quan_ly_bi_tu_choi(mock_user_dao):
    """FR-011: mặc định (None = không phải Admin) không được ghi trạng thái Quản lý."""
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=2)))
    ket_qua = bus.cap_nhat_trang_thai(8, 5, "banned")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không thể khóa tài khoản Quản lý!"

def test_quan_ly_actor_khong_khoa_duoc_quan_ly(mock_user_dao):
    """FR-009(1): người thao tác là Quản lý (khác mục tiêu) → bị từ chối."""
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=2)))
    ket_qua = bus.cap_nhat_trang_thai(8, 5, "banned", "Quản lý")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không thể khóa tài khoản Quản lý!"

def test_quan_ly_actor_khong_mo_khoa_duoc_quan_ly(mock_user_dao):
    """FR-009(1) mở rộng: MỞ khóa mục tiêu Quản lý cũng bị chặn khi người khác Admin."""
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=2, trang_thai="banned")))
    ket_qua = bus.cap_nhat_trang_thai(8, 5, "active", "Quản lý")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không thể khóa tài khoản Quản lý!"

def test_admin_khoa_quan_ly_duoc_phep(mock_user_dao):
    """FR-008: chỉ Admin được khóa tài khoản Quản lý."""
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=2)))
    ket_qua = bus.cap_nhat_trang_thai(1, 5, "banned", "Admin")
    assert ket_qua["status"] is True
    assert ket_qua["message"] == "Đã khóa tài khoản!"

def test_admin_mo_khoa_quan_ly_duoc_phep(mock_user_dao):
    """FR-008: Admin mở khóa Quản lý đang bị khóa."""
    bus = _bus(mock_user_dao(thong_tin=_thong_tin(role_id=2, trang_thai="banned")))
    ket_qua = bus.cap_nhat_trang_thai(1, 5, "active", "Admin")
    assert ket_qua["status"] is True
    assert ket_qua["message"] == "Đã mở khóa tài khoản!"

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

# ── CHO PHÉP (FR-008 giữ nguyên quyền cũ) ─────────────────────────────────────
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