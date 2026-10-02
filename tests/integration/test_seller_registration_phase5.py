import pytest

from app import app
import conftest
from back_end.Model.User import User


def _user():
    return User(
        ma_user=5, ma_nhom_quyen=4, ten_user="Khách A",
        sdt="0901234567", dia_chi="Hà Nội", cmnd="001099000000",
        tendangnhap="customer1", mat_khau="123456"
    )


class FakeSellerRegistrationDao:
    def __init__(self, requests=None, roles=None):
        self.requests = requests or {}
        self.roles = roles or {}
        self.next_id = max(self.requests.keys(), default=0) + 1

    def gui_yeu_cau_ban_hang(self, req):
        if self.roles.get(req.UserId) == 3:
            return "da_la_seller"
        if any(r["user_id"] == req.UserId and r["status"] == "pending"
               for r in self.requests.values()):
            return "da_co_pending"
        rid = self.next_id
        self.next_id += 1
        self.requests[rid] = {
            "user_id": req.UserId, "status": "pending",
            "shop_name": req.ShopName, "category": req.Category
        }
        return "ok"


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture
def seller_reg_setup(app_voi_dao):
    user_dao = conftest.FakeUserDaoBus(
        users={"customer1": _user()},
        thong_tin={
            5: {
                "UserId": 5, "FullName": "Khách A", "Phone": "0901234567",
                "Address": "Hà Nội", "NationalId": "001099000000",
                "Role_Id": 4, "trang_thai": "active"
            }
        }
    )
    seller_dao = FakeSellerRegistrationDao()
    app_voi_dao(user_dao=user_dao, gian_hang_dao=seller_dao)
    return user_dao, seller_dao


def _login(client):
    resp = client.post("/api/dang-nhap",
                       json={"tendangnhap": "customer1", "mat_khau": "123456"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] is True


def _body():
    return {
        "UserId": 9999,
        "StoreName": "Shop A",
        "Phone": "0901234567",
        "Category": "Hoa",
        "Description": "Bán hoa"
    }


def test_duplicate_pending_bi_chan(client, seller_reg_setup):
    _, dao = seller_reg_setup
    _login(client)
    assert client.post("/api/dang-ky-gian-hang", json=_body()).get_json()["status"] is True
    resp = client.post("/api/dang-ky-gian-hang", json={**_body(), "StoreName": "Shop B"})
    body = resp.get_json()
    assert body["status"] is False
    assert "đang chờ duyệt" in body["message"]
    assert len(dao.requests) == 1


def test_rejected_duoc_dang_ky_lai(client, seller_reg_setup):
    _, dao = seller_reg_setup
    _login(client)
    assert client.post("/api/dang-ky-gian-hang", json=_body()).get_json()["status"] is True
    dao.requests[1]["status"] = "rejected"
    resp = client.post("/api/dang-ky-gian-hang", json={**_body(), "StoreName": "Shop C"})
    assert resp.get_json()["status"] is True
    assert len(dao.requests) == 2
    assert dao.requests[2]["status"] == "pending"


def test_seller_da_approved_bi_chan(client, seller_reg_setup):
    _, dao = seller_reg_setup
    dao.roles[5] = 3
    _login(client)
    resp = client.post("/api/dang-ky-gian-hang", json=_body())
    assert resp.get_json()["status"] is False
    assert "đã là Seller" in resp.get_json()["message"]


@pytest.mark.parametrize("patch", [
    {"StoreName": "   "},
    {"Phone": "123"},
    {"Category": ""},
    {"Description": "x" * 501},
])
def test_registration_validation(patch, client, seller_reg_setup):
    seller_reg_setup
    _login(client)
    body = _body()
    body.update(patch)
    resp = client.post("/api/dang-ky-gian-hang", json=body)
    assert resp.status_code == 200
    assert resp.get_json()["status"] is False


def test_userid_client_khong_duoc_tin(client, seller_reg_setup):
    _, dao = seller_reg_setup
    _login(client)
    resp = client.post("/api/dang-ky-gian-hang", json={**_body(), "UserId": 999999})
    assert resp.get_json()["status"] is True
    assert dao.requests[1]["user_id"] == 5


def test_invalid_json_bi_tu_choi(client, seller_reg_setup):
    _login(client)
    resp = client.post("/api/dang-ky-gian-hang",
                       data="not-json", content_type="application/json")
    assert resp.status_code == 400
    assert resp.get_json()["status"] is False