# -*- coding: utf-8 -*-
"""Unit test GianHangBus duyet/tu_choi người bán (feature 002, US2).

Mock GianHangDao trả mã trạng thái ('ok'/'da_xu_ly'/'khong_tim_thay'/'da_la_seller')
→ BUS ánh xạ sang message tiếng Việt; tu_choi thiếu lý do bị từ chối.
Dùng mock DAO — KHÔNG chạm PobbyDB thật.
"""

import pytest

from back_end.BUS.GianHangBus import GianHangBus


def _bus(mock_gian_hang_dao, **kw):
    bus = GianHangBus()
    bus.dao = mock_gian_hang_dao(**kw)
    return bus


# ── DUYỆT ────────────────────────────────────────────────────────────────────
def test_duyet_chua_co_request_id(mock_gian_hang_dao):
    bus = _bus(mock_gian_hang_dao)
    ket_qua = bus.duyet_yeu_cau(8, None)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Thiếu mã yêu cầu!"


def test_duyet_da_xu_ly(mock_gian_hang_dao):
    bus = _bus(mock_gian_hang_dao, ket_qua_duyet="da_xu_ly")
    ket_qua = bus.duyet_yeu_cau(8, 5)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Yêu cầu đã được xử lý trước đó!"


def test_duyet_user_da_la_seller(mock_gian_hang_dao):
    bus = _bus(mock_gian_hang_dao, ket_qua_duyet="da_la_seller")
    ket_qua = bus.duyet_yeu_cau(8, 5)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Tài khoản này đã có gian hàng, không thể duyệt lại!"


def test_duyet_khong_tim_thay(mock_gian_hang_dao):
    bus = _bus(mock_gian_hang_dao, ket_qua_duyet="khong_tim_thay")
    ket_qua = bus.duyet_yeu_cau(8, 999)
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không tìm thấy yêu cầu!"


def test_duyet_thanh_cong(mock_gian_hang_dao):
    bus = _bus(mock_gian_hang_dao, ket_qua_duyet="ok")
    ket_qua = bus.duyet_yeu_cau(8, 5)
    assert ket_qua["status"] is True
    assert "trở thành Seller" in ket_qua["message"]


def test_bus_truyen_reviewed_by_la_nguoi_thao_tac(mock_gian_hang_dao):
    """BUS phải truyền author_user_id làm reviewed_by cho DAO (không lấy từ client)."""
    bus = _bus(mock_gian_hang_dao)
    da_goi = {}

    def duyet(request_id, reviewed_by):
        da_goi["reviewed_by"] = reviewed_by
        return "ok"

    bus.dao.duyet_yeu_cau = duyet
    bus.duyet_yeu_cau(8, 5)
    assert da_goi["reviewed_by"] == 8


# ── TỪ CHỐI ──────────────────────────────────────────────────────────────────
def test_tu_choi_thieu_ly_do(mock_gian_hang_dao):
    bus = _bus(mock_gian_hang_dao)
    ket_qua = bus.tu_choi_yeu_cau(8, 5, "   ")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Vui lòng nhập lý do từ chối!"


def test_tu_choi_chua_co_request_id(mock_gian_hang_dao):
    bus = _bus(mock_gian_hang_dao)
    ket_qua = bus.tu_choi_yeu_cau(8, None, "Lý do")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Thiếu mã yêu cầu!"


def test_tu_choi_da_xu_ly(mock_gian_hang_dao):
    bus = _bus(mock_gian_hang_dao, ket_qua_tu_choi="da_xu_ly")
    ket_qua = bus.tu_choi_yeu_cau(8, 5, "Hồ sơ thiếu giấy tờ")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Yêu cầu đã được xử lý trước đó!"


def test_tu_choi_khong_tim_thay(mock_gian_hang_dao):
    bus = _bus(mock_gian_hang_dao, ket_qua_tu_choi="khong_tim_thay")
    ket_qua = bus.tu_choi_yeu_cau(8, 999, "Hồ sơ thiếu giấy tờ")
    assert ket_qua["status"] is False
    assert ket_qua["message"] == "Không tìm thấy yêu cầu!"


def test_tu_choi_thanh_cong(mock_gian_hang_dao):
    bus = _bus(mock_gian_hang_dao, ket_qua_tu_choi="ok")
    ket_qua = bus.tu_choi_yeu_cau(8, 5, "Hồ sơ thiếu giấy tờ")
    assert ket_qua["status"] is True
    assert "từ chối" in ket_qua["message"].lower()