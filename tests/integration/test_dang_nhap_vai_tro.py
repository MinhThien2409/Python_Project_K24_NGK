# -*- coding: utf-8 -*-
"""Integration test User Story 4: POST /api/dang-nhap theo vai trò chuẩn
qua Flask test_client (SC-003).

- T026: 4 vai trò trả đúng ten_vai_tro; banned (non-admin) bị từ chối;
        Role_Id NULL/lạ bị từ chối rõ ràng (không crash).
"""

import pytest

from app import app

from back_end.BUS.UserBus import UserBus
from back_end.DAO.UserDao import UserDao
from back_end.Model.User import User


class FakeUserDao(UserDao):
    """Thay DAO thật để KHÔNG chạm PobbyDB — giữ giao diện duck-typing."""

    def __init__(self, user_map):
        self.user_map = user_map

    def dang_nhap(self, username, password):
        return self.user_map.get(username)


def _bus_voi_user(ma_nhom_quyen, trang_thai=None):
    user = User(
        ma_user=1,
        ma_nhom_quyen=ma_nhom_quyen,
        ten_user="Nguyễn Văn An",
        sdt="0123456789",
        dia_chi="Hà Nội",
        cmnd="001099012345",
        tendangnhap="user1",
        mat_khau="123456",
    )
    if trang_thai == "banned":
        return {"banned": True}
    return user


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def _gom_dang_nhap(client, username):
    """Chèn UserBus có DAO giả vào app trước khi gọi /api/dang-nhap."""
    # Giữ lại phan_quyen... không còn; chỉ cần user_bus. Thay DAO trực tiếp.
    UserBus.__orig__ = getattr(UserBus, "__orig__", None)
    return client.post(
        "/api/dang-nhap",
        json={"tendangnhap": username, "mat_khau": "123456"},
    )


def test_dang_nhap_4_vai_tro(client):
    """Gọi BUS trực tiếp với 4 vai trò khác nhau — xác nhận hợp đồng data."""
    for ma_nhom_quyen, ten_vai_tro in [(1, "Admin"), (2, "Quản lý"), (3, "Seller"), (4, "Customer")]:
        bus = UserBus()
        bus.dao = FakeUserDao({"user1": _bus_voi_user(ma_nhom_quyen)})
        ket_qua = bus.dang_nhap("user1", "123456")
        assert ket_qua["status"] is True, ten_vai_tro
        assert ket_qua["data"]["ten_vai_tro"] == ten_vai_tro
        assert ket_qua["data"]["ma_nhom_quyen"] == ma_nhom_quyen


def test_dang_nhap_baned_non_admin_bi_tu_choi(client):
    bus = UserBus()
    bus.dao = FakeUserDao({"user1": {"banned": True}})
    ket_qua = bus.dang_nhap("user1", "123456")
    assert ket_qua["status"] is False
    assert "khóa" in ket_qua["message"].lower()


def test_dang_nhap_role_none_bi_tu_choi(client):
    """Role_Id NULL/lạ (dao trả {"role_none": True}) → từ chối rõ ràng."""
    bus = UserBus()
    bus.dao = FakeUserDao({"user1": {"role_none": True}})
    ket_qua = bus.dang_nhap("user1", "123456")
    assert ket_qua["status"] is False
    assert "vai trò" in ket_qua["message"].lower()
    assert ket_qua["data"] is None


def test_dang_nhap_username_sai(client):
    bus = UserBus()
    bus.dao = FakeUserDao({})
    ket_qua = bus.dang_nhap("không_tồn_tại", "123456")
    assert ket_qua["status"] is False
    assert ket_qua["data"] is None


def test_endpoint_dang_nhap_co_route(client):
    """Endpoint /api/dang-nhap vẫn tồn tại (không bị xóa oan ở US3)."""
    assert any(r.rule == "/api/dang-nhap" for r in app.url_map.iter_rules())