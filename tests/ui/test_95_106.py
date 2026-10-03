"""
TC-095 -> TC-106  |  TS-18 (xem thông tin gian hàng), TS-19 (cập nhật trang gian hàng)

Chạy (bật Flask cổng 5000):
    pytest test_seller_shop.py --base-url http://localhost:5000 -v

LƯU Ý tên file: KHÔNG đặt dạng test_tcNNN... (conftest dò TC ID trên cả nodeid).

Thiết kế:
- Các test cập nhật KHÔNG đụng seller1: mỗi test tự tạo 1 Seller mới
  (Customer mới -> gửi yêu cầu -> quanly1 duyệt -> có gian hàng). Tên shop
  luôn có hậu tố ngẫu nhiên vì tên shop phải duy nhất toàn hệ thống.
- TC-096 cần tài khoản Seller KHÔNG có gian hàng (không tạo được qua API).
  Chạy SQL ở cuối docstring này 1 lần trước khi test:

    INSERT INTO Users (FullName, Address, Phone, NationalId)
      VALUES ('Seller Không Shop', '1 Nguyễn Huệ, Q1', '0901111199', '111111199');
    INSERT INTO Accounts (UserId, Username, Password, Role_Id, trang_thai)
      VALUES (LAST_INSERT_ID(), 'seller_nostore', '123456', 3, 'active');
"""
import random
import string

import pytest
from playwright.sync_api import expect

DEFAULT_BASE = "http://localhost:5000"
MAT_KHAU = "123456"
QUAN_LY = ("quanly1", MAT_KHAU)


# ============================================================
# HẠ TẦNG
# ============================================================
class Api:
    def __init__(self, ctx):
        self.ctx = ctx
        self.me = None

    def _do(self, method, url, data=None):
        kw = {} if data is None else {"data": data}
        resp = getattr(self.ctx, method)(url, **kw)
        try:
            body = resp.json()
        except Exception:
            body = {"status": None, "message": resp.text()[:200]}
        return resp.status, body

    def get(self, url):
        return self._do("get", url)

    def post(self, url, data=None):
        return self._do("post", url, data if data is not None else {})

    def put(self, url, data=None):
        return self._do("put", url, data if data is not None else {})


@pytest.fixture
def new_api(playwright, base_url):
    ctxs = []

    def _new(login=None):
        ctx = playwright.request.new_context(base_url=base_url or DEFAULT_BASE)
        ctxs.append(ctx)
        api = Api(ctx)
        if login:
            st, body = api.post("/api/dang-nhap",
                                {"tendangnhap": login[0], "mat_khau": login[1]})
            assert body.get("status") is True, \
                f"Không đăng nhập được {login[0]}: HTTP {st} {body}"
            api.me = body["data"]
        return api

    yield _new
    for c in ctxs:
        c.dispose()


def msg(body):
    return (body.get("message") if isinstance(body, dict) else "") or ""


def _rand(n, chars=string.digits):
    return "".join(random.choice(chars) for _ in range(n))


def dang_nhap_ui(page, username, password):
    page.goto("/")
    page.locator("#hdrAuthBtn").click()
    page.locator("#loginUsername").wait_for(state="visible", timeout=10000)
    page.fill("#loginUsername", username)
    page.fill("#loginPass", password)
    page.click("#formLogin button[type='submit']")
    expect(page.locator("#hdrUserBtn")).to_be_visible(timeout=15000)


def assert_bi_tu_choi(st, body):
    assert st in (401, 403), f"Kỳ vọng HTTP 401/403, thực tế {st}"
    assert body.get("status") is not True, f"API lại cho phép: {body}"


# ---------- chuẩn bị dữ liệu ----------
def tao_seller(new_api):
    """Customer mới -> gửi yêu cầu -> quanly1 duyệt -> trả client Seller có shop."""
    ql = new_api(QUAN_LY)
    username, name, sdt = "sel_" + _rand(8), "Seller Test " + _rand(4), "0" + _rand(9)
    anon = new_api()
    st, b = anon.post("/api/dang-ky", {
        "ten_user": name, "tendangnhap": username, "sdt": sdt,
        "mat_khau": MAT_KHAU, "dia_chi": "12 Nguyễn Huệ, Quận 1, TP. HCM"})
    assert b.get("status") is True, f"Không tạo được customer: {b}"
    cust = new_api((username, MAT_KHAU))
    st, b = cust.post("/api/cap-nhat-profile", {
        "ten_user": name, "sdt": sdt,
        "dia_chi": "12 Nguyễn Huệ, Quận 1, TP. HCM", "cmnd": _rand(12)})
    assert b.get("status") is True, f"Không cập nhật hồ sơ: {b}"

    shop = "Shop TC " + _rand(6)
    st, b = cust.post("/api/dang-ky-gian-hang", {
        "StoreName": shop, "Phone": "0" + _rand(9),
        "Category": "Điện thoại", "Description": "Mô tả test"})
    assert b.get("status") is True, f"Không gửi được yêu cầu: {b}"
    st, b = ql.get("/api/seller-requests")
    rid = next(r["request_id"] for r in b["data"] if r.get("shop_name") == shop)
    st, b = ql.post(f"/api/duyet-seller/{rid}", {})
    assert b.get("status") is True, f"Không duyệt được: {b}"

    seller = new_api((username, MAT_KHAU))
    seller.username = username
    seller.uid = seller.me["ma_user"]
    seller.shop = shop
    return seller


def doc_shop(api):
    st, body = api.get("/api/seller/trang-shop")
    assert st == 200 and body.get("status") is True, f"HTTP {st} {body}"
    return body["data"]


def luu_shop(api, ten, gioi_thieu="", tham_nien=None):
    return api.put("/api/seller/trang-shop",
                   {"ten_shop": ten, "gioi_thieu": gioi_thieu,
                    "tham_nien": tham_nien})


# ============================================================
# TS-18 — XEM THÔNG TIN GIAN HÀNG
# ============================================================
def test_tc095_seller_co_gian_hang_xem_thong_tin(new_api, page, actual):
    seller = new_api(("seller1", MAT_KHAU))
    shop = doc_shop(seller)
    actual(f"API trang-shop: {shop}")
    assert shop.get("store_name"), "Thiếu tên shop"

    # Khớp với dữ liệu gian hàng theo user
    st, b = seller.get(f"/api/stores/by-user/{seller.me['ma_user']}")
    assert b.get("status") is True
    assert b["data"].get("store_id") == shop.get("store_id")
    assert b["data"].get("store_name") == shop.get("store_name")

    # Giao diện: trang shop hiển thị đúng thông tin
    dang_nhap_ui(page, "seller1", MAT_KHAU)
    expect(page.locator("#sellerDashboard")).to_be_visible(timeout=10000)
    page.locator("#smenu-shop").click()
    expect(page.locator("#sellerShopName")).to_have_value(
        shop["store_name"], timeout=10000)
    expect(page.locator("#sellerShopDesc")).to_have_value(shop.get("description") or "")
    tn = shop.get("tham_nien")
    expect(page.locator("#sellerShopThamNien")).to_have_value(
        "" if tn is None else str(tn))


def test_tc096_seller_chua_co_gian_hang(new_api, actual):
    anon = new_api()
    st, b = anon.post("/api/dang-nhap",
                      {"tendangnhap": "seller_nostore", "mat_khau": MAT_KHAU})
    assert b.get("status") is True, \
        "Chưa có tài khoản seller_nostore — chạy SQL trong docstring đầu file test"
    api = new_api(("seller_nostore", MAT_KHAU))

    st, body = api.get("/api/seller/trang-shop")
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert st < 500, f"Lỗi server HTTP {st}"
    assert body.get("status") is False
    assert msg(body).strip(), "Không có thông báo chưa có gian hàng"
    assert not body.get("data"), "Trả dữ liệu shop dù chưa có gian hàng"


def test_tc097_customer_truy_cap_trang_shop(page, actual):
    dang_nhap_ui(page, "khach1", MAT_KHAU)
    page.wait_for_load_state("networkidle")
    expect(page.locator("#hdrGoSellerBtn")).to_be_hidden()
    expect(page.locator("#sellerDashboard")).to_be_hidden()

    resp = page.request.get("/api/seller/trang-shop")
    body = resp.json() if resp.status < 500 else {}
    actual(f"HTTP {resp.status}, status={body.get('status')}, message='{msg(body)}'")
    assert resp.status in (401, 403)
    assert not body.get("data")


def test_tc098_chua_dang_nhap_xem_shop(new_api, actual):
    st, body = new_api().get("/api/seller/trang-shop")
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert_bi_tu_choi(st, body)
    assert not body.get("data")


# ============================================================
# TS-19 — CẬP NHẬT TRANG GIAN HÀNG
# ============================================================
def test_tc099_cap_nhat_shop_hop_le(new_api, page, actual):
    seller = tao_seller(new_api)
    ten_moi = "Shop Thiên An 2 " + _rand(5)

    dang_nhap_ui(page, seller.username, MAT_KHAU)
    expect(page.locator("#sellerDashboard")).to_be_visible(timeout=10000)
    page.locator("#smenu-shop").click()
    expect(page.locator("#sellerShopName")).to_have_value(seller.shop, timeout=10000)

    page.fill("#sellerShopName", ten_moi)
    page.fill("#sellerShopDesc", "Chuyên đồ gia dụng")
    page.fill("#sellerShopThamNien", "5")
    page.get_by_role("button", name="Lưu trang shop").click()
    expect(page.locator("#toast")).to_contain_text("✅", timeout=10000)
    actual(f"Toast: '{page.locator('#toast').inner_text()}'")

    # Tải lại trang -> dữ liệu mới
    page.reload()
    expect(page.locator("#sellerDashboard")).to_be_visible(timeout=15000)
    page.locator("#smenu-shop").click()
    expect(page.locator("#sellerShopName")).to_have_value(ten_moi, timeout=10000)
    expect(page.locator("#sellerShopDesc")).to_have_value("Chuyên đồ gia dụng")
    expect(page.locator("#sellerShopThamNien")).to_have_value("5")

    shop = doc_shop(seller)
    assert shop["store_name"] == ten_moi and shop.get("tham_nien") == 5


@pytest.mark.parametrize("ten", [
    pytest.param("", id="rong"),
    pytest.param("   ", id="toan_khoang_trang"),
])
def test_tc100_ten_shop_rong(new_api, actual, ten):
    seller = tao_seller(new_api)
    truoc = doc_shop(seller)
    st, body = luu_shop(seller, ten, "Giới thiệu", 3)
    actual(f"Tên='{ten}': HTTP {st}, status={body.get('status')}, "
           f"message='{msg(body)}'")
    assert st < 500
    assert body.get("status") is False
    assert doc_shop(seller) == truoc, "Dữ liệu cũ bị thay đổi"


def test_tc101_ten_shop_150_ky_tu(new_api, actual):
    seller = tao_seller(new_api)
    ten = "S" + _rand(149, string.ascii_letters)  # đúng 150 ký tự, duy nhất
    assert len(ten) == 150
    st, body = luu_shop(seller, ten, "", None)
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert body.get("status") is True
    assert doc_shop(seller)["store_name"] == ten


def test_tc102_ten_shop_151_ky_tu(new_api, actual):
    seller = tao_seller(new_api)
    truoc = doc_shop(seller)
    ten = "S" + _rand(150, string.ascii_letters)
    assert len(ten) == 151
    st, body = luu_shop(seller, ten, "", None)
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert st < 500
    assert body.get("status") is False
    assert doc_shop(seller) == truoc, "Dữ liệu bị thay đổi"


def test_tc103_gioi_thieu_500_ky_tu(new_api, actual):
    seller = tao_seller(new_api)
    gt = "B" * 500
    st, body = luu_shop(seller, seller.shop, gt, 2)
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert body.get("status") is True
    assert doc_shop(seller).get("description") == gt


def test_tc104_gioi_thieu_501_ky_tu(new_api, actual):
    seller = tao_seller(new_api)
    truoc = doc_shop(seller)
    st, body = luu_shop(seller, seller.shop, "B" * 501, 2)
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert st < 500
    assert body.get("status") is False
    assert doc_shop(seller) == truoc, "Dữ liệu bị thay đổi"


@pytest.mark.parametrize("gia_tri,hop_le", [
    pytest.param(-1, False, id="am_1"),
    pytest.param(101, False, id="101"),
    pytest.param("abc", False, id="abc"),
    pytest.param(0, True, id="bien_0_hop_le"),
    pytest.param(100, True, id="bien_100_hop_le"),
])
def test_tc105_tham_nien_ngoai_0_100(new_api, actual, gia_tri, hop_le):
    seller = tao_seller(new_api)
    truoc = doc_shop(seller)
    st, body = luu_shop(seller, seller.shop, "Giới thiệu", gia_tri)
    actual(f"Thâm niên={gia_tri!r}: HTTP {st}, status={body.get('status')}, "
           f"message='{msg(body)}'")
    assert st < 500
    if hop_le:
        assert body.get("status") is True
        assert doc_shop(seller).get("tham_nien") == gia_tri
    else:
        assert body.get("status") is False
        assert doc_shop(seller) == truoc, "Dữ liệu cũ bị thay đổi"


def test_tc106_ten_shop_trung(new_api, actual):
    a = tao_seller(new_api)
    b = tao_seller(new_api)
    truoc = doc_shop(a)

    st, body = luu_shop(a, b.shop, "Giới thiệu", 1)
    actual(f"A đổi sang tên của B ('{b.shop}'): HTTP {st}, "
           f"status={body.get('status')}, message='{msg(body)}'")
    assert st < 500
    assert body.get("status") is False
    m = msg(body).lower()
    assert any(k in m for k in ("tồn tại", "đã có", "sử dụng")), \
        f"Message không báo trùng tên: '{msg(body)}'"
    assert doc_shop(a) == truoc, "Dữ liệu shop A bị thay đổi"