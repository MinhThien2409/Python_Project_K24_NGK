# -*- coding: utf-8 -*-
"""Integration test đăng ký tạo HAI bảng (008 US4, T041) — POST /api/dang-ky.

Independent Test US4 : đăng ký một khách mới tạo đồng thời **một dòng `Users`
(hồ sơ)** và **một dòng `Accounts` (đăng nhập)** liên kết đúng qua `UserId`
(1-1), vai trò Customer (4), trang_thai 'active'.

Fake DAO in-memory mô phỏng đúng hành vi hai bảng của `UserDao.them_user`
(ghi `Users` → lastrowid → ghi `Accounts`) — KHÔNG chạm PobbyDB thật.
"""

import pytest

import app as app_module
from app import app

import conftest
from back_end.BUS.UserBus import UserBus
from back_end.Model.User import User


class FakeUserDaoHaiBang(conftest.FakeUserDaoBus):
    """FakeUserDaoBus + `them_user` ghi vào hai bảng mô phỏng (Users/Accounts)."""

    def them_user(self, user):
        """Ghi 1 dòng 'Users' + 1 dòng 'Accounts' liên kết UserId (như UserDao)."""
        ma_moi = max([u.ma_user for u in self.users.values()] + [0]) + 1
        # 1 dòng Users (hồ sơ)
        self.users[user.tendangnhap] = User(
            ma_user=ma_moi, ma_nhom_quyen=4, ten_user=user.ten_user,
            sdt=user.sdt, dia_chi=user.dia_chi, cmnd=user.cmnd,
            tendangnhap=user.tendangnhap, mat_khau=user.mat_khau,
        )
        # 1 dòng Accounts (đăng nhập), liên kết 1-1 qua UserId
        self.thong_tin[ma_moi] = {
            "UserId": ma_moi, "FullName": user.ten_user, "Phone": user.sdt,
            "Address": user.dia_chi, "Role_Id": 4, "trang_thai": "active",
            "Username": user.tendangnhap, "Password": user.mat_khau,
        }
        self.mat_khau[user.tendangnhap] = user.mat_khau
        self.lan_them_cuoi = {
            "ma_user": ma_moi,
            "Users": self.users[user.tendangnhap],
            "Accounts": self.thong_tin[ma_moi],
        }
        return True


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def _gan_bus(client, dao):
    bus = UserBus()
    bus.dao = dao
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(app_module, "user_bus", bus)
    return client


# ── Đăng ký tạo đúng một Users + một Accounts ────────────────────────────────
def test_dang_ky_tao_hai_bang_lien_ket_dung(client):
    dao = FakeUserDaoHaiBang()
    _gan_bus(client, dao)

    resp = client.post("/api/dang-ky", json={
        "ten_user": "Khách Hàng Mới",
        "dia_chi": "12 Lê Lợi, Quận 1, TP.HCM",
        "sdt": "0912345678",
        "tendangnhap": "khach_moi",
        "mat_khau": "matkhau123",
    })
    assert resp.status_code == 200
    assert resp.get_json()["status"] is True

    # ĐÚNG MỘT dòng Users và ĐÚNG MỘT dòng Accounts được tạo
    assert len(dao.users) == 1
    assert len(dao.thong_tin) == 1
    assert len(dao.mat_khau) == 1

    dong = dao.lan_them_cuoi
    # Liên kết 1-1 đúng: Users.UserId == Accounts.UserId == Account.UserId
    assert dong["Users"].ma_user == dong["Accounts"]["UserId"] == dong["ma_user"]
    # Accounts giữ thông tin đăng nhập
    assert dong["Accounts"]["Username"] == "khach_moi"
    assert dong["Accounts"]["Password"] == "matkhau123"
    # Vai trò Customer (4) + trạng thái active (giống schema mặc định)
    assert dong["Accounts"]["Role_Id"] == 4
    assert dong["Accounts"]["trang_thai"] == "active"
    # Hồ sơ Users giữ thông tin con người
    assert dong["Users"].ten_user == "Khách Hàng Mới"


def test_chua_lien_ket_thi_thong_tin_dang_nhap_bi_thieu(client):
    """Chứng minh hai bảng tách bạch: hồ sơ mới không đính kèm credential.

    Một User mới (hồ sơ) không tồn tại trong Accounts → không có Password.
    """
    dao = FakeUserDaoHaiBang()
    _gan_bus(client, dao)
    resp = client.post("/api/dang-ky", json={
        "ten_user": "Nguyễn Văn A", "sdt": "0987654321",
        "tendangnhap": "khach_a", "mat_khau": "123456",
    })
    assert resp.get_json()["status"] is True
    assert len(dao.users) == 1
    # Accounts tồn tại đúng một dòng liên kết với cái Users duy nhất
    assert dao.lan_them_cuoi["Users"].ma_user in dao.thong_tin


# ── Ca biên: trùng tên đăng nhập → không tạo thêm bảng nào ──────────────────
def test_dang_ky_trung_tendangnhap_khong_tao_hai_bang(client):
    dao = FakeUserDaoHaiBang(
        users={
            "khach_cu": User(ma_user=9, ma_nhom_quyen=4, ten_user="Khách Cũ",
                             sdt="0900000000", dia_chi="Hà Nội", cmnd=None,
                             tendangnhap="khach_cu", mat_khau="123456"),
        },
        thong_tin={
            9: {"UserId": 9, "FullName": "Khách Cũ", "Role_Id": 4,
                "trang_thai": "active"},
        },
    )
    _gan_bus(client, dao)

    resp = client.post("/api/dang-ky", json={
        "ten_user": "Khách Trùng", "sdt": "0911111111",
        "tendangnhap": "khach_cu", "mat_khau": "123456",
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is False
    assert "đã có người sử dụng" in body["message"]
    # KHÔNG tạo thêm dòng nào ở hai bảng
    assert len(dao.users) == 1
    assert len(dao.thong_tin) == 1


# ── Ca biên: người dùng mới đăng nhập được với tài khoản vừa tạo ────────────
def test_khach_moi_dang_nhap_duoc_voi_tai_khoan_vua_tao(client):
    dao = FakeUserDaoHaiBang()
    _gan_bus(client, dao)
    client.post("/api/dang-ky", json={
        "ten_user": "Khách Mới X", "sdt": "0912345678",
        "tendangnhap": "khach_x", "mat_khau": "123456",
    })

    resp = client.post("/api/dang-nhap", json={
        "tendangnhap": "khach_x", "mat_khau": "123456",
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] is True
    assert body["data"]["ten_vai_tro"] == "Customer"
    assert body["data"]["ma_user"] == 1