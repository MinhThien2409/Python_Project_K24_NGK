# -*- coding: utf-8 -*-
"""Unit test cập nhật hồ sơ (008 US2, T022) — `UserBus.cap_nhat_user`.

- Cập nhật thành công → status True, DAO nhận đúng tham số đã chuẩn hóa.
- Tên rỗng / toàn khoảng trắng → từ chối, KHÔNG gọi DAO.
- SĐT sai định dạng → từ chối, KHÔNG gọi DAO.
- Dữ liệu quá dài → từ chối, KHÔNG gọi DAO.

Mock UserDao — KHÔNG chạm PobbyDB thật (Nguyên tắc IV: test trước implementation).
"""

import pytest

from back_end.BUS.UserBus import UserBus


def _bus_voi_dao(dao):
    """Gắn DAO đã cấu hình vào UserBus."""
    bus = UserBus()
    bus.dao = dao
    return bus


# ── Cập nhật thành công ──────────────────────────────────────────────────────
def test_cap_nhat_ho_so_thanh_cong(mock_user_dao):
    dao = mock_user_dao()
    goi = []
    def cap_nhat_user(ma_user, ten, dia_chi, sdt, cmnd):
        goi.append((ma_user, ten, dia_chi, sdt, cmnd))
        return True
    dao.cap_nhat_user = cap_nhat_user

    kq = _bus_voi_dao(dao).cap_nhat_user(1, "Nguyễn Văn B", "Hà Nội",
                                          "0987654321", "001099000001")

    assert kq["status"] is True
    assert kq["message"] == "Cập nhật thông tin thành công!"
    assert goi == [(1, "Nguyễn Văn B", "Hà Nội", "0987654321", "001099000001")]


# ── Ca biên: tên rỗng / khoảng trắng ────────────────────────────────────────
@pytest.mark.parametrize("ten_bi_loi", ["", "   ", None])
def test_ten_rong_tu_choi(mock_user_dao, ten_bi_loi):
    dao = mock_user_dao()
    def cap_nhat_user(*a, **k):
        pytest.fail("KHÔNG được gọi DAO khi tên rỗng")
    dao.cap_nhat_user = cap_nhat_user

    kq = _bus_voi_dao(dao).cap_nhat_user(1, ten_bi_loi, "Hà Nội",
                                          "0987654321", "cmnd")

    assert kq["status"] is False
    assert "Tên người dùng không được để trống!" in kq["message"]


# ── Ca biên: SĐT sai định dạng ───────────────────────────────────────────────
@pytest.mark.parametrize("sdt_sai", ["abc", "12345", "098765432", "09876543210",
                                     "8 98765432", "0a98765432"])
def test_sdt_sai_dinh_dang_tu_choi(mock_user_dao, sdt_sai):
    dao = mock_user_dao()
    def cap_nhat_user(*a, **k):
        pytest.fail("KHÔNG được gọi DAO khi SĐT sai định dạng")
    dao.cap_nhat_user = cap_nhat_user

    kq = _bus_voi_dao(dao).cap_nhat_user(1, "Nguyễn Văn B", "Hà Nội", sdt_sai, "cmnd")

    assert kq["status"] is False
    assert "Số điện thoại không hợp lệ!" in kq["message"]


def test_sdt_bo_trong_van_duoc_phep(mock_user_dao):
    """SĐT trống (không bắt buộc) vẫn cho qua, DAO nhận chuỗi rỗng."""
    dao = mock_user_dao()
    goi = []
    def cap_nhat_user(ma_user, ten, dia_chi, sdt, cmnd):
        goi.append((ma_user, ten, dia_chi, sdt, cmnd))
        return True
    dao.cap_nhat_user = cap_nhat_user

    kq = _bus_voi_dao(dao).cap_nhat_user(1, "Nguyễn Văn B", "Hà Nội", "", "cmnd")

    assert kq["status"] is True
    assert goi == [(1, "Nguyễn Văn B", "Hà Nội", "", "cmnd")]


# ── Ca biên: dữ liệu quá dài ─────────────────────────────────────────────────
def test_ten_qua_dai_tu_choi(mock_user_dao):
    dao = mock_user_dao()
    def cap_nhat_user(*a, **k):
        pytest.fail("KHÔNG được gọi DAO khi dữ liệu quá dài")
    dao.cap_nhat_user = cap_nhat_user

    kq = _bus_voi_dao(dao).cap_nhat_user(1, "X" * 101, "Hà Nội",
                                          "0987654321", "cmnd")

    assert kq["status"] is False
    assert "quá dài" in kq["message"].lower()


def test_sdt_qua_dai_tu_choi(mock_user_dao):
    """SĐT dài > 10 số không khớp định dạng regex → từ chối trước khi gọi DAO."""
    dao = mock_user_dao()
    def cap_nhat_user(*a, **k):
        pytest.fail("KHÔNG được gọi DAO khi SĐT không hợp lệ")
    dao.cap_nhat_user = cap_nhat_user

    kq = _bus_voi_dao(dao).cap_nhat_user(1, "Nguyễn Văn B", "Hà Nội",
                                          "0" + "9" * 20, "cmnd")

    assert kq["status"] is False
    assert "Số điện thoại không hợp lệ!" in kq["message"]


def test_dia_chi_qua_dai_tu_choi(mock_user_dao):
    """Địa chỉ > 255 ký tự → từ chối 'quá dài' trước khi gọi DAO."""
    dao = mock_user_dao()
    def cap_nhat_user(*a, **k):
        pytest.fail("KHÔNG được gọi DAO khi dữ liệu quá dài")
    dao.cap_nhat_user = cap_nhat_user

    kq = _bus_voi_dao(dao).cap_nhat_user(1, "Nguyễn Văn B", "Địa chỉ " * 32 + "X",
                                          "0987654321", "cmnd")

    assert kq["status"] is False
    assert "quá dài" in kq["message"].lower()


# ── DAO báo lỗi ──────────────────────────────────────────────────────────────
def test_dao_tra_ve_false_bao_loi(mock_user_dao):
    dao = mock_user_dao()
    def cap_nhat_user(*a, **k):
        return False
    dao.cap_nhat_user = cap_nhat_user

    kq = _bus_voi_dao(dao).cap_nhat_user(1, "Nguyễn Văn B", "Hà Nội",
                                          "0987654321", "cmnd")

    assert kq["status"] is False
    assert "Không tìm thấy User hoặc lỗi cập nhật." in kq["message"]