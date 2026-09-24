# -*- coding: utf-8 -*-
"""Integration test endpoint POST /api/dang-nhap (feature 01, US1) qua Flask
test_client. Không chạm PobbyDB thật — dùng FakeUserDaoBus (mock DAO).

- đúng → status True, message chào mừng, data có đủ 8 khóa.
- sai mật khẩu → status False, message "không chính xác", data None.
- thiếu đầu vào → status False, message "Vui lòng nhập", data None.
- banned → status False, message "khóa", data None.
- role_none → status False, message "vai trò", data None.
"""

import pytest

import conftest

import app as app_module
from app import app

from back_end.BUS.UserBus import UserBus
from back_end.Model.User import User

TAM_VIET = 8  # số khóa bắt buộc trong data đăng nhập thành công


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def _user(ma_user, role_id, username, ten="Nguyễn Văn An"):
    return User(
        ma_user=ma_user,
        ma_nhom_quyen=role_id,
        ten_user=ten,
        sdt="0123456789",
        dia_chi="Hà Nội",
        cmnd="001099012345",
        tendangnhap=username,
        mat_khau="123456",
    )


def _tao_dao():
    return conftest.FakeUserDaoBus(
        users={
            "user1": _user(1, 4, "user1", "Nguyễn Văn An"),
            "admin1": _user(2, 1, "admin1", "Admin"),
        },
        thong_tin={
            1: {"UserId": 1, "Role_Id": 4, "trang_thai": "active",
                "FullName": "Nguyễn Văn An", "Phone": "0123456789",
                "Address": "Hà Nội", "NationalId": "001099012345"},
            2: {"UserId": 2, "Role_Id": 1, "trang_thai": "active",
                "FullName": "Admin", "Phone": "0123456789",
                "Address": "TP.HCM", "NationalId": "001099012345"},
        },
    )


def _tap_bus(client, bus):
    """Gắn UserBus (có DAO giả) vào app thay cho user_bus thật."""
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(app_module, "user_bus", bus)
    return client, monkeypatch


def _dang_nhap(client, tendangnhap, mat_khau="123456"):
    resp = client.post(
        "/api/dang-nhap",
        json={"tendangnhap": tendangnhap, "mat_khau": mat_khau},
    )
    assert resp.status_code == 200
    return resp.get_json()


# ── Đăng nhập thành công ─────────────────────────────────────────────────────
def test_endpoint_dang_nhap_dung_thanh_cong(client):
    bus = UserBus()
    bus.dao = _tao_dao()
    _tap_bus(client, bus)

    ket_qua = _dang_nhap(client, "user1")

    assert ket_qua["status"] is True
    assert ket_qua["message"] == "Chào mừng Nguyễn Văn An trở lại!"
    assert ket_qua["data"]["ma_user"] == 1
    assert ket_qua["data"]["ten_user"] == "Nguyễn Văn An"
    assert ket_qua["data"]["ten_vai_tro"] == "Customer"
    assert ket_qua["data"]["ma_nhom_quyen"] == 4
    assert ket_qua["data"]["sdt"] == "0123456789"
    assert ket_qua["data"]["dia_chi"] == "Hà Nội"
    assert ket_qua["data"]["cmnd"] == "001099012345"


def test_endpoint_dang_nhap_vai_tro_admin(client):
    bus = UserBus()
    bus.dao = _tao_dao()
    _tap_bus(client, bus)

    ket_qua = _dang_nhap(client, "admin1")

    assert ket_qua["status"] is True
    assert ket_qua["data"]["ten_vai_tro"] == "Admin"
    assert ket_qua["data"]["ma_nhom_quyen"] == 1
    assert ket_qua["data"]["ten_vai_tro_hien_thi"] == "Admin"


def test_endpoint_dang_nhap_co_du_8_khoa_data(client):
    bus = UserBus()
    bus.dao = _tao_dao()
    _tap_bus(client, bus)

    ket_qua = _dang_nhap(client, "user1")

    assert isinstance(ket_qua["data"], dict)
    assert len(ket_qua["data"]) == TAM_VIET
    assert set(ket_qua["data"].keys()) == {
        "ma_user", "ten_user", "ma_nhom_quyen", "ten_vai_tro",
        "ten_vai_tro_hien_thi", "dia_chi", "sdt", "cmnd",
    }


# ── Sai mật khẩu ─────────────────────────────────────────────────────────────
def test_endpoint_dang_nhap_sai_mat_khau_that_bai(client):
    bus = UserBus()
    bus.dao = _tao_dao()
    _tap_bus(client, bus)

    ket_qua = _dang_nhap(client, "user1", mat_khau="999999")

    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tên đăng nhập hoặc mật khẩu không chính xác!"
    assert ket_qua["data"] is None


# ── Thiếu đầu vào ────────────────────────────────────────────────────────────
def test_endpoint_dang_nhap_thieu_tendangnhap(client):
    bus = UserBus()
    bus.dao = _tao_dao()
    _tap_bus(client, bus)

    ket_qua = _dang_nhap(client, "")

    assert ket_qua["status"] is False
    assert "Vui lòng nhập" in ket_qua["message"]
    assert ket_qua["data"] is None


def test_endpoint_dang_nhap_thieu_mat_khau(client):
    bus = UserBus()
    bus.dao = _tao_dao()
    _tap_bus(client, bus)

    ket_qua = _dang_nhap(client, "user1", mat_khau="")

    assert ket_qua["status"] is False
    assert "Vui lòng nhập" in ket_qua["message"]
    assert ket_qua["data"] is None


def test_endpoint_dang_nhap_thieu_bo_dau_vao(client):
    bus = UserBus()
    bus.dao = _tao_dao()
    _tap_bus(client, bus)

    ket_qua = _dang_nhap(client, None, mat_khau=None)

    assert ket_qua["status"] is False
    assert "Vui lòng nhập" in ket_qua["message"]
    assert ket_qua["data"] is None


# ── Tài khoản bị khóa ────────────────────────────────────────────────────────
def test_endpoint_dang_nhap_bi_khoa_tu_choi(client):
    dao = _tao_dao()
    # DAO trả cờ banned khi user đăng nhập → BUS từ chối "khóa".
    dao._bang_ban = {"user1"}
    dao._bang_role_none = set()
    bus = UserBus()
    bus.dao = dao
    _tap_bus(client, bus)

    ket_qua = _dang_nhap(client, "user1")

    assert ket_qua["status"] is False
    assert "khóa" in ket_qua["message"].lower()
    assert ket_qua["data"] is None


# ── Vai trò không hợp lệ ─────────────────────────────────────────────────────
def test_endpoint_dang_nhap_role_none_tu_choi(client):
    dao = _tao_dao()
    dao._bang_ban = set()
    dao._bang_role_none = {"user1"}
    bus = UserBus()
    bus.dao = dao
    _tap_bus(client, bus)

    ket_qua = _dang_nhap(client, "user1")

    assert ket_qua["status"] is False
    assert "vai trò" in ket_qua["message"].lower()
    assert ket_qua["data"] is None


# ── User không tồn tại ───────────────────────────────────────────────────────
def test_endpoint_dang_nhap_user_khong_ton_tai(client):
    bus = UserBus()
    bus.dao = _tao_dao()
    _tap_bus(client, bus)

    ket_qua = _dang_nhap(client, "khong_ton_tai", mat_khau="123456")

    assert ket_qua["status"] is False
    assert "không chính xác" in ket_qua["message"].lower()
    assert ket_qua["data"] is None
