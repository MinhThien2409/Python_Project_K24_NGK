# -*- coding: utf-8 -*-
"""Unit test DanhMucBus (feature 002, US1): validate thêm/sửa/xóa danh mục.

Ca phủ: tên rỗng / toàn khoảng trắng / >100 ký tự / trùng tên; sửa loại trừ
chính mình (tru_id); xóa danh mục còn sản phẩm / không tìm thấy / rỗng OK.
Dùng mock DAO (MockDanhMucDao) — KHÔNG chạm PobbyDB thật.
"""

import pytest

from back_end.BUS.DanhMucBus import DanhMucBus


def _bus(mock_danh_muc_dao, **kw):
    bus = DanhMucBus()
    bus.dao = mock_danh_muc_dao(**kw)
    return bus


# ── THÊM DANH MỤC ────────────────────────────────────────────────────────────
def test_them_ten_rong(mock_danh_muc_dao):
    bus = _bus(mock_danh_muc_dao)
    ket_qua = bus.them_category("")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tên danh mục không được để trống!"


def test_them_ten_toan_khoang_trang(mock_danh_muc_dao):
    bus = _bus(mock_danh_muc_dao)
    ket_qua = bus.them_category("   ")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tên danh mục không được để trống!"


def test_them_ten_qua_dai(mock_danh_muc_dao):
    bus = _bus(mock_danh_muc_dao)
    ket_qua = bus.them_category("D" * 101)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tên danh mục quá dài (tối đa 100 ký tự)!"


def test_them_trung_ten(mock_danh_muc_dao):
    """Kiểm tra trùng tên theo hoa/thường/thừa khoảng trắng (mock ton_tai=True)."""
    bus = _bus(mock_danh_muc_dao, ton_tai=True)
    ket_qua = bus.them_category("  đồ gia dụng  ")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Danh mục 'đồ gia dụng' đã tồn tại!"


def test_them_hop_le(mock_danh_muc_dao):
    bus = _bus(mock_danh_muc_dao)
    ket_qua = bus.them_category("  Đồ gia dụng  ")
    assert ket_qua["status"] is True
    assert "Đã thêm danh mục" in ket_qua["message"]


# ── SỬA DANH MỤC ─────────────────────────────────────────────────────────────
def test_sua_loai_tru_chinh_minh(mock_danh_muc_dao):
    """Sửa giữ nguyên tên (chỉ thừa space) vẫn OK vì tru_id loại trừ chính mình."""
    bus = _bus(mock_danh_muc_dao, ton_tai=False)
    ket_qua = bus.sua_category(1, "Điện thoại  ")
    assert ket_qua["status"] is True


def test_sua_ten_rong(mock_danh_muc_dao):
    bus = _bus(mock_danh_muc_dao)
    ket_qua = bus.sua_category(1, "   ")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tên danh mục không được để trống!"


def test_sua_trung_ten_khac(mock_danh_muc_dao):
    bus = _bus(mock_danh_muc_dao, ton_tai=True)
    ket_qua = bus.sua_category(1, "Trùng tên khác")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Danh mục 'Trùng tên khác' đã tồn tại!"


def test_sua_khong_tim_thay(mock_danh_muc_dao):
    bus = _bus(mock_danh_muc_dao)
    bus.dao.sua = lambda category: False
    ket_qua = bus.sua_category(999, "Tên mới")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không tìm thấy danh mục!"


# ── XÓA DANH MỤC ─────────────────────────────────────────────────────────────
def test_xoa_danh_muc_co_san_pham(mock_danh_muc_dao):
    bus = _bus(mock_danh_muc_dao, so_san_pham=3)
    ket_qua = bus.xoa_category(1)
    assert ket_qua["status"] is False
    assert (ket_qua["message"] ==
            "Danh mục đang có sản phẩm, không thể xóa! Hãy chuyển sản phẩm sang danh mục khác rồi thử lại.")


def test_xoa_khong_tim_thay(mock_danh_muc_dao):
    bus = _bus(mock_danh_muc_dao, so_san_pham=None)
    ket_qua = bus.xoa_category(999)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không tìm thấy danh mục!"


def test_xoa_danh_muc_rong_ok(mock_danh_muc_dao):
    bus = _bus(mock_danh_muc_dao, so_san_pham=0)
    ket_qua = bus.xoa_category(1)
    assert ket_qua["status"] is True