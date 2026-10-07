"""Phase 1 - server-side authorization regression tests (T150)."""

import pytest


class GateUserBus:
    def __init__(self, user=None, role=None, active=True):
        self.user = user
        self.role = role
        self.active = active
        self.calls = []

    def kiem_tra_nguoi_dung_hoat_dong(self, user_id):
        self.calls.append(("active", user_id))
        if not user_id:
            return {"status": False, "message": "Bạn chưa đăng nhập!", "data": None}
        if not self.active:
            return {"status": False, "message": "Tài khoản của bạn đã bị khóa!", "data": None}
        return {"status": True, "message": "", "data": None}

    def lay_thong_tin_user(self, user_id):
        self.calls.append(("user", user_id))
        return self.user

    def lay_ten_vai_tro_theo_id(self, role_id):
        self.calls.append(("role", role_id))
        return self.role

    def cap_nhat_trang_thai_quan_ly(self, *args):
        self.calls.append(("status_admin", args))
        return {"status": True}

    def cap_nhat_trang_thai(self, *args):
        self.calls.append(("status_manager", args))
        return {"status": True}

    def cap_lai_mat_khau_quan_ly(self, *args):
        self.calls.append(("reset_admin", args))
        return {"status": True}

    def cap_lai_mat_khau(self, *args):
        self.calls.append(("reset_manager", args))
        return {"status": True}


def _user(role_id):
    return {"UserId": 1, "Role_Id": role_id, "trang_thai": "active"}


def _login(client, user_id=1):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


@pytest.fixture
def auth_client(monkeypatch):
    import app as app_module

    app_module.app.config["TESTING"] = True
    bus = GateUserBus(user=_user(4), role="Customer")
    monkeypatch.setattr(app_module, "user_bus", bus)
    return app_module.app.test_client(), bus


def test_anonymous_cannot_read_store_by_user(auth_client):
    client, bus = auth_client

    response = client.get("/api/stores/by-user/1")

    assert response.status_code == 403
    assert response.get_json()["status"] is False
    assert ("active", None) in bus.calls


def test_customer_cannot_read_another_users_store(auth_client):
    client, bus = auth_client
    _login(client, 1)

    response = client.get("/api/stores/by-user/2")

    assert response.status_code == 403
    assert "khác" in response.get_json()["message"]
    assert all(call[0] != "store_lookup" for call in bus.calls)


def test_customer_can_read_own_store_after_authentication(auth_client, monkeypatch):
    import app as app_module

    client, bus = auth_client
    _login(client, 1)

    class StoreBus:
        def lay_store_theo_user(self, user_id):
            bus.calls.append(("store_lookup", user_id))
            return {"status": True, "data": {"store_id": 10, "user_id": user_id}}

    monkeypatch.setattr(app_module, "gian_hang_bus", StoreBus())

    response = client.get("/api/stores/by-user/1")

    assert response.status_code == 200
    assert response.get_json()["data"]["user_id"] == 1


@pytest.mark.parametrize(
    ("role", "role_id", "expected_status"),
    [
        ("Customer", 4, 403),
        ("Seller", 3, 403),
        ("Quản lý", 2, 200),
        ("Admin", 1, 200),
    ],
)
def test_user_status_endpoint_is_server_side_role_gated(auth_client, role, role_id, expected_status):
    client, bus = auth_client
    bus.user = _user(role_id)
    bus.role = role
    _login(client, 1)

    response = client.put("/api/users/2/status", json={"status": "banned"})

    assert response.status_code == expected_status
    if expected_status == 403:
        assert not any(call[0] in ("status_admin", "status_manager") for call in bus.calls)


@pytest.mark.parametrize(
    ("role", "role_id", "expected_status"),
    [
        ("Customer", 4, 403),
        ("Seller", 3, 403),
        ("Quản lý", 2, 200),
        ("Admin", 1, 200),
    ],
)
def test_password_reset_endpoint_is_server_side_role_gated(auth_client, role, role_id, expected_status):
    client, bus = auth_client
    bus.user = _user(role_id)
    bus.role = role
    _login(client, 1)

    response = client.post("/api/cap-lai-mat-khau", json={"ma_user": 2, "mat_khau_moi": "123456"})

    assert response.status_code == expected_status
    if expected_status == 403:
        assert not any(call[0] in ("reset_admin", "reset_manager") for call in bus.calls)


def test_banned_session_cannot_use_admin_status_endpoint(auth_client):
    client, bus = auth_client
    bus.user = _user(1)
    bus.role = "Admin"
    bus.active = False
    _login(client, 1)

    response = client.put("/api/users/2/status", json={"status": "banned"})

    assert response.status_code == 403
    assert not any(call[0] == "status_admin" for call in bus.calls)


def test_forged_role_in_request_does_not_upgrade_customer(auth_client):
    client, bus = auth_client
    _login(client, 1)

    response = client.put(
        "/api/users/2/status",
        json={"status": "banned", "Role": "Admin", "Role_Id": 1, "UserId": 999},
    )

    assert response.status_code == 403
    assert not any(call[0] == "status_admin" for call in bus.calls)
