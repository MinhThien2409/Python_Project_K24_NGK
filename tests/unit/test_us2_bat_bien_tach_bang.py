# -*- coding: utf-8 -*-
"""Unit test ca biên tách bảng (008 US2, T023) — bất biến hai bảng.

Bất biến (data-model.md mục 7), kiểm ở tầng BUS với stub DAO:
- Hồ sơ mồ côi (Users không có Accounts — JOIN trả a.* = NULL) → không crash.
- Tài khoản mồ côi (Accounts không có Users — JOIN không ra dòng) → không crash.
- `trang_thai` NULL → coi như 'active' (không bị chặn như 'banned').

Stub DAO in-memory — KHÔNG chạm PobbyDB thật.
"""

from back_end.BUS.UserBus import UserBus


class StubDao:
    """Stub DAO trả dữ liệu theo kịch bản ca biên hai bảng."""

    def __init__(self, thong_tin=None, ket_qua_dang_nhap=None):
        self.thong_tin = thong_tin
        self.ket_qua_dang_nhap = ket_qua_dang_nhap

    def lay_thong_tin_user(self, ma_user):
        return self.thong_tin

    def lay_ten_vai_tro_theo_id(self, role_id):
        return {1: "Admin", 2: "Quản lý", 3: "Seller", 4: "Customer"}.get(role_id)

    def dang_nhap(self, username, password):
        return self.ket_qua_dang_nhap


def _thong_tin_mo_coi(mau=True):
    """Dòng JOIN `Users LEFT JOIN Accounts` khi thiếu dòng Accounts (a.* = NULL)."""
    if not mau:
        return {
            "UserId": 5, "FullName": None, "Address": None, "Phone": None,
            "NationalId": None, "Username": None, "Password": None,
            "Role_Id": None, "trang_thai": None,
        }
    return {
        "UserId": 5, "FullName": "Nguyễn Văn Mồ Côi", "Address": None,
        "Phone": "0900000000", "NationalId": None, "Username": None,
        "Password": None, "Role_Id": None, "trang_thai": None,
    }


def _bus(thong_tin=None, ket_qua_dang_nhap=None):
    bus = UserBus()
    bus.dao = StubDao(thong_tin=thong_tin, ket_qua_dang_nhap=ket_qua_dang_nhap)
    return bus


# ── Hồ sơ mồ côi (Users không có Accounts) ──────────────────────────────────
def test_ho_so_mo_coi_kiem_tra_hoat_dong_khong_crash():
    """Roles/quyền: Role_Id NULL → từ chối vai trò, KHÔNG crash."""
    bus = _bus(thong_tin=_thong_tin_mo_coi())

    kq_admin = bus.kiem_tra_quyen_admin(5)
    assert kq_admin["status"] is False
    assert "vai trò" in kq_admin["message"].lower()

    kq_quanly = bus.kiem_tra_quyen_quan_ly(5)
    assert kq_quanly["status"] is False
    assert "vai trò" in kq_quanly["message"].lower()


def test_ho_so_mo_coi_doi_mat_khau_khong_crash():
    """Password NULL → so sánh 'khác mật khẩu cũ' → từ chối, KHÔNG crash."""
    bus = _bus(thong_tin=_thong_tin_mo_coi())

    kq = bus.doi_mat_khau(5, "matkhau_cu", "matkhau_moi")

    assert kq["status"] is False
    assert "không chính xác" in kq["message"]


def test_ho_so_mo_coi_load_thong_tin_khong_crash():
    """BUS trả đúng dict JOIN (UserName/Pwd/Role/trang_thai = None) không crash."""
    bus = _bus(thong_tin=_thong_tin_mo_coi())

    thong_tin = bus.lay_thong_tin_user(5)

    assert thong_tin["UserId"] == 5
    assert thong_tin["trang_thai"] is None
    assert "Password" in thong_tin  # hợp đồng: tầng BUS cần khóa này


# ── Tài khoản mồ côi (Accounts không có Users) ──────────────────────────────
def test_tai_khoan_mo_coi_dang_nhap_khong_crash():
    """INNER JOIN Users+Accounts không ra dòng (Users thiếu) → dang_nhap None
    → BUS từ chối 'không chính xác', KHÔNG crash."""
    bus = _bus(ket_qua_dang_nhap=None)

    kq = bus.dang_nhap("username_le", "123456")

    assert kq["status"] is False
    assert "không chính xác" in kq["message"].lower()
    assert kq["data"] is None


# ── trang_thai NULL coi như active ───────────────────────────────────────────
def test_trang_thai_null_coi_nhu_active():
    """trang_thai=None → KHÔNG bị chặn như banned; vẫn được đánh giá theo vai trò."""
    thong_tin = {"UserId": 3, "Role_Id": 4, "trang_thai": None}
    bus = _bus(thong_tin=thong_tin)

    kq = bus.kiem_tra_nguoi_dung_hoat_dong(3)
    assert kq["status"] is True  # không chặn 'banned'

    # Vai trò Customer vẫn bị chặn chức năng Seller (không crash)
    kq_seller = bus.kiem_tra_quyen_seller(3)
    assert kq_seller["status"] is False
    assert "không có quyền" in kq_seller["message"]

    thong_tin = {"UserId": 3, "Role_Id": 3, "trang_thai": None}
    bus = _bus(thong_tin=thong_tin)
    kq_seller = bus.kiem_tra_quyen_seller(3)
    assert kq_seller["status"] is True  # Seller + trang_thai NULL → hoạt động


def test_trang_thai_null_khong_bi_kiem_tra_ban_nhu_banned():
    """Phân biệt: NULL ≠ banned — banned mới bị chặn."""
    thong_tin_ban = {"UserId": 4, "Role_Id": 4, "trang_thai": "banned"}
    bus = _bus(thong_tin=thong_tin_ban)

    kq = bus.kiem_tra_nguoi_dung_hoat_dong(4)
    assert kq["status"] is False
    assert "khóa" in kq["message"].lower()