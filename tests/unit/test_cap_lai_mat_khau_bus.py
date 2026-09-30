# -*- coding: utf-8 -*-
"""Unit tests cấp lại mật khẩu theo policy hiện tại.

Actor phải là Quản lý; mục tiêu chỉ Seller/Customer. Test dùng MockUserDao
với thông tin riêng cho actor và target, không chạm PobbyDB.
"""
from back_end.BUS.UserBus import UserBus


def _bus(mock):
    bus = UserBus()
    bus.dao = mock
    return bus


def _info(user_id, role_id, trang_thai="active", fullname="Người dùng"):
    return {
        "UserId": user_id,
        "FullName": fullname,
        "Role_Id": role_id,
        "trang_thai": trang_thai,
    }


def _dao(mock_user_dao, target_role=4, target_status="active",
         mat_khau_moi_ok=True):
    return mock_user_dao(
        thong_tin={
            2: _info(2, 2, fullname="Quản lý"),
            5: _info(5, target_role, target_status),
        },
        mat_khau_moi_ok=mat_khau_moi_ok,
    )


def test_sinh_ngau_nhien_hop_le(mock_user_dao):
    bus = _bus(_dao(mock_user_dao))
    ghi_nhan = {}

    def cap_nhat_mat_khau(ma_user, mat_khau_moi):
        ghi_nhan["ma_user"] = ma_user
        ghi_nhan["mat_khau_moi"] = mat_khau_moi
        return True

    bus.dao.cap_nhat_mat_khau = cap_nhat_mat_khau
    kq = bus.cap_lai_mat_khau(2, 5, None)
    assert kq["status"] is True
    assert len(kq["data"]["mat_khau_moi"]) >= 6
    assert ghi_nhan["ma_user"] == 5


def test_sinh_ngau_nhien_chuoi_khong_thay_doi_ket_qua_khi_mat_khau_moi_rong(mock_user_dao):
    bus = _bus(_dao(mock_user_dao))
    kq = bus.cap_lai_mat_khau(2, 5, "")
    assert kq["status"] is True
    assert len(kq["data"]["mat_khau_moi"]) >= 6


def test_mat_khau_nhap_du_6_ky_tu_ok(mock_user_dao):
    bus = _bus(_dao(mock_user_dao))
    kq = bus.cap_lai_mat_khau(2, 5, "matkhau67890")
    assert kq["status"] is True
    assert kq["data"]["mat_khau_moi"] == "matkhau67890"


def test_mat_khau_nhap_ngan_bi_tu_choi(mock_user_dao):
    bus = _bus(_dao(mock_user_dao))
    kq = bus.cap_lai_mat_khau(2, 5, "12345")
    assert kq["status"] is False
    assert kq["message"] == "Mật khẩu phải có ít nhất 6 ký tự!"


def test_cap_lai_mat_khau_admin_bi_tu_choi(mock_user_dao):
    bus = _bus(_dao(mock_user_dao, target_role=1))
    kq = bus.cap_lai_mat_khau(2, 5, "matkhau67890")
    assert kq["status"] is False
    assert "Seller hoặc Khách hàng" in kq["message"]


def test_user_khong_ton_tai_bi_tu_choi(mock_user_dao):
    bus = _bus(mock_user_dao(thong_tin={2: _info(2, 2, fullname="Quản lý")}))
    kq = bus.cap_lai_mat_khau(2, 999, None)
    assert kq["status"] is False
    assert kq["message"] == "Tài khoản không tồn tại!"


def test_reset_user_banned_van_giu_banned(mock_user_dao):
    bus = _bus(_dao(mock_user_dao, target_status="banned"))
    kq = bus.cap_lai_mat_khau(2, 5, "matkhau67890")
    assert kq["status"] is True
    assert bus.dao.lay_thong_tin_user(5)["trang_thai"] == "banned"


def test_dao_that_bai_tra_loi_ro_rang(mock_user_dao):
    bus = _bus(_dao(mock_user_dao, mat_khau_moi_ok=False))
    kq = bus.cap_lai_mat_khau(2, 5, "matkhau67890")
    assert kq["status"] is False
    assert kq["message"] == "Lỗi cập nhật mật khẩu!"
