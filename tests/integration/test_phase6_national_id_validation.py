# -*- coding: utf-8 -*-
"""Phase 6 — T26 CMND/CCCD server-side validation."""
import pytest

from back_end.BUS.validation import validate_national_id
from back_end.BUS.GianHangBus import GianHangBus
from back_end.Model.YeuCau import YeuCau


@pytest.mark.parametrize("value", ["123456789", "123456789012"])
def test_t26_valid_cmnd_cccd(value):
    assert validate_national_id(value, required=True) == (True, None)


@pytest.mark.parametrize(
    "value",
    [
        "12345678",
        "1234567890",
        "12345678901",
        "1234567890123",
        "12345678A",
        "123456789 0",
        "12 345678901",
        "123-456-789",
        "",
        None,
    ],
)
def test_t26_invalid_cmnd_cccd(value):
    ok, message = validate_national_id(value, required=True)
    assert ok is False
    assert message




def test_t26_direct_api_rejects_invalid_national_id(monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module.user_bus, "kiem_tra_nguoi_dung_hoat_dong", lambda uid: {"status": True})
    monkeypatch.setattr(app_module.gian_hang_bus.user_dao, "lay_thong_tin_user", lambda uid: {
        "UserId": uid, "FullName": "API User", "Phone": "0901234567",
        "Address": "HN", "NationalId": "123456789A",
    })
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1
    response = client.post("/api/dang-ky-gian-hang", json={
        "StoreName": "Phase6 API Shop", "Phone": "0901234567",
        "Category": "Test", "Description": "invalid NID",
        "NationalId": "999999999999999",
    })
    body = response.get_json()
    assert response.status_code == 200
    assert body["status"] is False
    assert "CMND/CCCD" in body["message"]


def _seller_bus_with_profile(national_id):
    bus = GianHangBus()
    bus.user_dao.lay_thong_tin_user = lambda uid: {
        "UserId": uid,
        "FullName": "Phase6 User",
        "Phone": "0901234567",
        "Address": "HN",
        "NationalId": national_id,
    }
    return bus


@pytest.mark.parametrize("value", ["123456789", "123456789012"])
def test_t26_seller_registration_accepts_valid_national_id(monkeypatch, value):
    bus = _seller_bus_with_profile(value)
    monkeypatch.setattr(bus.dao, "gui_yeu_cau_ban_hang", lambda req: "ok")
    result = bus.dang_ky_gian_hang(
        YeuCau(UserId=1, ShopName="Phase6 Shop", BusinessPhone="0901234567",
               Category="Test", Description="x")
    )
    assert result["status"] is True


@pytest.mark.parametrize("value", ["12345678", "123456789A", "1234567890"])
def test_t26_seller_registration_rejects_invalid_national_id(monkeypatch, value):
    bus = _seller_bus_with_profile(value)
    called = {"value": False}

    def fake_insert(req):
        called["value"] = True
        return "ok"

    monkeypatch.setattr(bus.dao, "gui_yeu_cau_ban_hang", fake_insert)
    result = bus.dang_ky_gian_hang(
        YeuCau(UserId=1, ShopName="Phase6 Shop", BusinessPhone="0901234567",
               Category="Test", Description="x")
    )
    assert result["status"] is False
    assert "CMND/CCCD" in result["message"]
    assert called["value"] is False
