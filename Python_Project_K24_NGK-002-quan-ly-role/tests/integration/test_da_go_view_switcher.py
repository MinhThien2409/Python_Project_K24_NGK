# -*- coding: utf-8 -*-
"""Integration test US1 (009): giao diện không còn view-switcher.

Independent Test US1 (009 T006):
- Trang chủ KHÔNG chứa chuỗi "Chế độ xem" (khối #viewSwitcher).
- Không chứa nút "Quay lại trang Mua sắm" (topbar khu quản trị).
- Không chứa nút "Về trang mua sắm" (topbar kênh người bán).
"""

import pytest

from app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_trang_chu_khong_con_chuoi_view_switcher(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Chế độ xem" not in html
    assert "Quay lại trang Mua sắm" not in html
    assert "Về trang mua sắm" not in html


def test_trang_chu_khong_con_view_switcher_block(client):
    resp = client.get("/")
    html = resp.get_data(as_text=True)
    assert 'id="viewSwitcher"' not in html
    assert "btnViewUser" not in html
    assert "btnViewAdmin" not in html