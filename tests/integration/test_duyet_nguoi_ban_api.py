# -*- coding: utf-8 -*-
"""Integration test duyệt/từ chối người bán (feature 002, US2) qua Flask test_client.

Login Quản lý → POST /api/duyet-seller/<id> / POST /api/tu-choi-seller/<id>.
Fake DAO có trạng thái in-memory — KHÔNG chạm PobbyDB thật.
"""

import pytest

from app import app

import conftest
from back_end.Model.User import User


def _user(ma_user=8, role_id=2, username="manager1"):
    return User(
        ma_user=ma_user, ma_nhom_quyen=role_id, ten_user="Nguyễn Thị Quản Lý",
        sdt="0900000000", dia_chi="Hà Nội", cmnd="001099000000",
        tendangnhap=username, mat_khau="123456",
    )


def _thong_tin(ma_user=8, role_id=2, trang_thai="active"):
    return {
        "UserId": ma_user, "Role_Id": role_id, "trang_thai": trang_thai,
        "FullName": "Nguyễn Thị Quản Lý", "Phone": "0900000000", "Address": "Hà Nội",
    }


def _yeu_cau_mau(request_id, user_id, status="pending"):
    return {
        "request_id": request_id,
        "user_id": user_id,
        "ten_user": f"Người gửi {user_id}",
        "shop_name": "Shop Hoa Tươi",
        "phone": "0901234567",
        "category": "Hoa",
        "description": "Bán hoa tươi",
        "national_id": None,
        "status": status,
        "created_at": "2026-09-15 14:30:00",
        "reviewed_by": None,
        "reviewed_at": None,
        "reject_reason": None,
    }


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture
def gan_dao(app_voi_dao):
    """Gắn FakeUserDaoBus (login Quản lý) + FakeGianHangDao vào app module."""

    def _gan(gian_hang_dao):
        user_dao = conftest.FakeUserDaoBus(
            users={"manager1": _user()},
            thong_tin={8: _thong_tin()},
        )
        app_voi_dao(user_dao=user_dao, gian_hang_dao=gian_hang_dao)

    return _gan


def _dang_nhap(client):
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": "manager1", "mat_khau": "123456"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] is True


# ── DUYỆT ────────────────────────────────────────────────────────────────────
def test_duyet_thanh_cong(client, gan_dao):
    gian_hang_dao = conftest.FakeGianHangDao(
        requests={5: _yeu_cau_mau(5, user_id=12)},
        roles={12: 4},
    )
    gan_dao(gian_hang_dao)
    _dang_nhap(client)

    resp = client.post("/api/duyet-seller/5", json={})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] is True
    assert "Seller" in body["message"]

    # Effect: user 12 thành Seller (Role_id=3) + có Store mới
    assert gian_hang_dao.roles[12] == 3
    assert 12 in gian_hang_dao.stores
    assert gian_hang_dao.requests[5]["status"] == "approved"
    assert gian_hang_dao.requests[5]["reviewed_by"] == 8  # từ session, không phải client


def test_duyet_lai_bi_chan(client, gan_dao):
    gian_hang_dao = conftest.FakeGianHangDao(
        requests={5: _yeu_cau_mau(5, user_id=12, status="approved")},
        roles={12: 4},
    )
    gian_hang_dao.stores.add(12)
    gian_hang_dao.roles[12] = 3
    gan_dao(gian_hang_dao)
    _dang_nhap(client)

    resp = client.post("/api/duyet-seller/5", json={})
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Yêu cầu đã được xử lý trước đó!"


def test_duyet_request_khong_ton_tai(client, gan_dao):
    gian_hang_dao = conftest.FakeGianHangDao()
    gan_dao(gian_hang_dao)
    _dang_nhap(client)

    resp = client.post("/api/duyet-seller/999", json={})
    body = resp.get_json()
    assert body["status"] is False
    assert body["message"] == "Không tìm thấy yêu cầu!"


def test_duyet_user_da_la_seller(client, gan_dao):
    gian_hang_dao = conftest.FakeGianHangDao(
        requests={5: _yeu_cau_mau(5, user_id=12)},
        roles={12: 3},
    )
    gian_hang_dao.stores.add(12)
    gan_dao(gian_hang_dao)
    _dang_nhap(client)

    resp = client.post("/api/duyet-seller/5", json={})
    body = resp.get_json()
    assert body["status"] is False
    assert "đã có gian hàng" in body["message"]


# ── TỪ CHỐI ──────────────────────────────────────────────────────────────────
def test_tu_choi_thieu_ly_do(client, gan_dao):
    gian_hang_dao = conftest.FakeGianHangDao(
        requests={5: _yeu_cau_mau(5, user_id=12)},
        roles={12: 4},
    )
    gan_dao(gian_hang_dao)
    _dang_nhap(client)

    resp = client.post("/api/tu-choi-seller/5", json={})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] is False
    assert body["message"] == "Vui lòng nhập lý do từ chối!"
    assert gian_hang_dao.requests[5]["status"] == "pending"  # giữ nguyên


def test_tu_choi_thanh_cong(client, gan_dao):
    gian_hang_dao = conftest.FakeGianHangDao(
        requests={5: _yeu_cau_mau(5, user_id=12)},
        roles={12: 4},
    )
    gan_dao(gian_hang_dao)
    _dang_nhap(client)

    resp = client.post("/api/tu-choi-seller/5", json={"ly_do": "Hồ sơ thiếu giấy tờ"})
    body = resp.get_json()
    assert body["status"] is True
    assert gian_hang_dao.requests[5]["status"] == "rejected"
    assert gian_hang_dao.requests[5]["reject_reason"] == "Hồ sơ thiếu giấy tờ"
    assert gian_hang_dao.roles[12] == 4  # giữ nguyên vai trò


# ── CẠNH TRANH 2 PHIÊN ───────────────────────────────────────────────────────
def test_can_tranh_hai_phien_duyet(client, gan_dao):
    """Phiên thứ hai duyệt cùng 1 request → DAO trả 'da_xu_ly'."""
    gian_hang_dao = conftest.FakeGianHangDao(
        requests={5: _yeu_cau_mau(5, user_id=12, status="approved")},
        roles={12: 3},
    )
    gian_hang_dao.stores.add(12)

    duyet_goc = gian_hang_dao.duyet_yeu_cau
    dem = {"lan": 0}

    def duyet(request_id, reviewed_by):
        dem["lan"] += 1
        if dem["lan"] > 1:
            return "da_xu_ly"
        return duyet_goc(request_id, reviewed_by)

    gian_hang_dao.duyet_yeu_cau = duyet

    gan_dao(gian_hang_dao)
    _dang_nhap(client)

    resp1 = client.post("/api/duyet-seller/5", json={})
    resp2 = client.post("/api/duyet-seller/5", json={})
    assert resp2.get_json()["message"] == "Yêu cầu đã được xử lý trước đó!"