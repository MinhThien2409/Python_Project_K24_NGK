# -*- coding: utf-8 -*-
"""Unit test BUS Admin/Quản lý (feature 003, Nguyên tắc IV — test-first).

Bao phủ:
- T007 [US1]: chặn tạo Admin thứ hai + gate Admin-only + dem_admin.
- T015 [US2]: validate tao_quan_ly (trùng tên, mật khẩu ngắn, toàn trắng, quá dài).
- T022 [US3]: sua_quan_ly và xoa_quan_ly (chặn mục tiêu Admin, mục tiêu không tồn tại).

Dùng mock DAO, KHÔNG chạm PobbyDB thật.
"""

import pytest

from back_end.BUS.UserBus import UserBus


def _bus(dao):
    bus = UserBus()
    bus.dao = dao
    return bus


# ── T007 [US1]: gate kiem_tra_quyen_admin ─────────────────────────────────────
def test_gate_admin_chua_dang_nhap(mock_user_dao):
    bus = _bus(mock_user_dao())
    ket_qua = bus.kiem_tra_quyen_admin(None)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Bạn chưa đăng nhập!"


def test_gate_admin_khong_ton_tai(mock_user_dao):
    dao = mock_user_dao()
    dao.lay_thong_tin_user = lambda ma_user: None
    bus = _bus(dao)
    ket_qua = bus.kiem_tra_quyen_admin(999)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tài khoản không tồn tại!"


def test_gate_admin_bi_khoa(mock_user_dao):
    bus = _bus(mock_user_dao(
        thong_tin={"UserId": 1, "Role_Id": 1, "trang_thai": "banned"}
    ))
    ket_qua = bus.kiem_tra_quyen_admin(1)
    assert ket_qua["status"] is False
    assert "khóa" in ket_qua["message"].lower()


@pytest.mark.parametrize("role_id", [2, 3, 4], ids=["quan-ly", "seller", "customer"])
def test_gate_admin_tu_choi_khong_phai_admin(mock_user_dao, role_id):
    bus = _bus(mock_user_dao(
        thong_tin={"UserId": 8, "Role_Id": role_id, "trang_thai": "active"}
    ))
    ket_qua = bus.kiem_tra_quyen_admin(8)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Bạn không có quyền thực hiện chức năng này!"


def test_gate_admin_cho_phep_admin(mock_user_dao):
    bus = _bus(mock_user_dao(
        thong_tin={"UserId": 1, "Role_Id": 1, "trang_thai": "active"}
    ))
    ket_qua = bus.kiem_tra_quyen_admin(1)
    assert ket_qua["status"] is True
    assert ket_qua["data"]["ma_user"] == 1


def test_gate_admin_role_la(mock_user_dao):
    bus = _bus(mock_user_dao(
        thong_tin={"UserId": 8, "Role_Id": 99, "trang_thai": "active"}
    ))
    ket_qua = bus.kiem_tra_quyen_admin(8)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Dữ liệu vai trò không hợp lệ!"


def test_chan_tao_admin_thu_hai(mock_user_dao):
    bus = _bus(mock_user_dao())
    ket_qua = bus.tao_quan_ly(
        ten_user="Người Mới", tendangnhap="admin_moi",
        mat_khau="123456", sdt="0900000000", dia_chi="Hà Nội",
        vai_tro="Admin",
    )
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không thể tạo thêm tài khoản Admin!"


def test_dem_admin_bang_mot(mock_user_dao):
    bus = _bus(mock_user_dao(so_admin=1))
    assert bus.dao.dem_admin() == 1


# ── T015 [US2]: validate tao_quan_ly ──────────────────────────────────────────
def test_tao_quan_ly_thanh_cong(mock_user_dao):
    bus = _bus(mock_user_dao(ton_tai_tendangnhap=False, them_quan_ly_ok=True))
    ket_qua = bus.tao_quan_ly(
        ten_user="Nguyễn Văn B", tendangnhap="quanly_b",
        mat_khau="123456", sdt="0901111111", dia_chi="Hà Nội",
    )
    assert ket_qua["status"] is True
    assert ket_qua["message"] == "Đã tạo tài khoản Quản lý!"


def test_tao_quan_ly_thieu_truong(mock_user_dao):
    bus = _bus(mock_user_dao())
    ket_qua = bus.tao_quan_ly(ten_user="", tendangnhap="", mat_khau="")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Vui lòng điền đầy đủ Tên, Tên đăng nhập và Mật khẩu!"


def test_tao_quan_ly_toan_trang(mock_user_dao):
    bus = _bus(mock_user_dao())
    ket_qua = bus.tao_quan_ly(ten_user="   ", tendangnhap="   ", mat_khau="123456")
    assert ket_qua["status"] is False


def test_tao_quan_ly_trung_ten(mock_user_dao):
    bus = _bus(mock_user_dao(ton_tai_tendangnhap=True))
    ket_qua = bus.tao_quan_ly(
        ten_user="Nguyễn Văn B", tendangnhap="quanly_b", mat_khau="123456",
    )
    assert ket_qua["status"] is False
    assert "đã có người sử dụng" in ket_qua["message"]


def test_tao_quan_ly_mat_khau_ngan(mock_user_dao):
    bus = _bus(mock_user_dao())
    ket_qua = bus.tao_quan_ly(
        ten_user="Nguyễn Văn B", tendangnhap="quanly_moi", mat_khau="123",
    )
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Mật khẩu phải có ít nhất 6 ký tự!"


def test_tao_quan_ly_qua_dai(mock_user_dao):
    bus = _bus(mock_user_dao())
    ket_qua = bus.tao_quan_ly(
        ten_user="A" * 101, tendangnhap="quanly_moi", mat_khau="123456",
    )
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Thông tin quá dài, vui lòng rút gọn!"
    ket_qua = bus.tao_quan_ly(
        ten_user="Nguyễn Văn B", tendangnhap="u" * 51, mat_khau="123456",
    )
    assert ket_qua["status"] is False


# ── T022 [US3]: sua_quan_ly và xoa_quan_ly ────────────────────────────────────
def test_sua_quan_ly_chan_muc_tieu_admin(mock_user_dao):
    dao = mock_user_dao(cap_nhat_quan_ly_ok=True)
    dao.lay_thong_tin_user = lambda ma_user: {
        "UserId": ma_user, "Role_Id": 1, "trang_thai": "active",
    }
    bus = _bus(dao)
    ket_qua = bus.sua_quan_ly(1, "Tên Mới", "Địa chỉ", "0900000000")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không thể sửa tài khoản Admin qua chức năng này!"


def test_sua_quan_ly_khong_ton_tai(mock_user_dao):
    dao = mock_user_dao()
    dao.lay_thong_tin_user = lambda ma_user: None
    bus = _bus(dao)
    ket_qua = bus.sua_quan_ly(999, "Tên Mới", "Địa chỉ", "0900000000")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tài khoản Quản lý không tồn tại!"


def test_sua_quan_ly_ten_rong(mock_user_dao):
    dao = mock_user_dao()
    dao.lay_thong_tin_user = lambda ma_user: {
        "UserId": ma_user, "Role_Id": 2, "trang_thai": "active",
    }
    bus = _bus(dao)
    ket_qua = bus.sua_quan_ly(2, "   ", "Địa chỉ", "0900000000")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tên người dùng không được để trống!"


def test_sua_quan_ly_thanh_cong(mock_user_dao):
    dao = mock_user_dao(cap_nhat_quan_ly_ok=True)
    dao.lay_thong_tin_user = lambda ma_user: {
        "UserId": ma_user, "Role_Id": 2, "trang_thai": "active",
    }
    bus = _bus(dao)
    ket_qua = bus.sua_quan_ly(2, "Tên Mới", "Địa chỉ", "0900000000")
    assert ket_qua["status"] is True
    assert ket_qua["message"] == "Cập nhật thông tin thành công!"


def test_xoa_quan_ly_chan_muc_tieu_admin(mock_user_dao):
    dao = mock_user_dao()
    dao.lay_thong_tin_user = lambda ma_user: {
        "UserId": ma_user, "Role_Id": 1, "trang_thai": "active",
    }
    bus = _bus(dao)
    ket_qua = bus.xoa_quan_ly(1)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không thể xóa tài khoản Admin!"


def test_xoa_quan_ly_khong_ton_tai(mock_user_dao):
    dao = mock_user_dao()
    dao.lay_thong_tin_user = lambda ma_user: None
    bus = _bus(dao)
    ket_qua = bus.xoa_quan_ly(999)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tài khoản Quản lý không tồn tại!"


def test_xoa_quan_ly_thanh_cong(mock_user_dao):
    dao = mock_user_dao(xoa_quan_ly_ok=True)
    dao.lay_thong_tin_user = lambda ma_user: {
        "UserId": ma_user, "Role_Id": 2, "trang_thai": "active",
    }
    bus = _bus(dao)
    ket_qua = bus.xoa_quan_ly(2)
    assert ket_qua["status"] is True
    assert ket_qua["message"] == "Đã xóa tài khoản Quản lý!"
