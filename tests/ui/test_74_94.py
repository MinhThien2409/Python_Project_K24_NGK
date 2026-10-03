"""
TC-074 -> TC-094  |  TS-14..TS-17: Yêu cầu đăng ký gian hàng (Seller)
  TS-14 Đăng ký gian hàng      TS-15 Xem danh sách yêu cầu
  TS-16 Duyệt yêu cầu          TS-17 Từ chối yêu cầu

Chạy (bật Flask cổng 5000):
    pytest test_seller_request.py --base-url http://localhost:5000 -v

LƯU Ý tên file: KHÔNG đặt dạng test_tcNNN... (conftest dò TC ID trên cả nodeid).

Thiết kế:
- Seed đã có sẵn request pending của khach3/khach4 nên KHÔNG dùng lại các user
  này (dễ vướng "đã có yêu cầu chờ duyệt"). Mỗi test tự tạo Customer MỚI
  (đăng ký -> cập nhật hồ sơ đủ SĐT/địa chỉ/CMND) rồi gửi yêu cầu với tên shop
  duy nhất => chạy lại bao nhiêu lần cũng không đụng nhau.
- Quản lý dùng quanly1/123456 (seed).
- Không so khớp nguyên văn message; chỉ status/HTTP/dữ liệu. Message ghi vào Actual.
- Dữ liệu test (customer, request) không bị xóa vì hệ thống không có API xóa.
"""
import random
import string

import pytest
from playwright.sync_api import expect

DEFAULT_BASE = "http://localhost:5000"
MAT_KHAU = "123456"
QUAN_LY = ("quanly1", MAT_KHAU)
ROLE_SELLER, ROLE_CUSTOMER = 3, 4


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
    """Đăng nhập bằng giao diện (không dùng fixture login của conftest)."""
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


# ---------- dữ liệu ----------
def tao_customer(new_api, co_ho_so=True):
    """Tạo Customer mới (đăng ký + đăng nhập). co_ho_so=True -> bổ sung
    SĐT/địa chỉ/CMND để đủ điều kiện đăng ký gian hàng."""
    username = "cust_" + _rand(8)
    name = "Khách Test " + _rand(4)
    sdt = "0" + _rand(9)
    anon = new_api()
    st, body = anon.post("/api/dang-ky", {
        "ten_user": name, "tendangnhap": username, "sdt": sdt,
        "mat_khau": MAT_KHAU, "dia_chi": "12 Nguyễn Huệ, Quận 1, TP. HCM"})
    assert body.get("status") is True, f"Không tạo được customer: {body}"
    cust = new_api((username, MAT_KHAU))
    cust.username, cust.name, cust.sdt = username, name, sdt
    cust.uid = cust.me["ma_user"]
    if co_ho_so:
        st, body = cust.post("/api/cap-nhat-profile", {
            "ten_user": name, "sdt": sdt,
            "dia_chi": "12 Nguyễn Huệ, Quận 1, TP. HCM", "cmnd": _rand(12)})
        assert body.get("status") is True, f"Không cập nhật hồ sơ: {body}"
    return cust


def lay_danh_muc(api):
    st, body = api.get("/api/categories")
    ds = body.get("data") or []
    return (ds[0].get("category_name") or ds[0].get("name")) if ds else "Điện thoại"


def body_yeu_cau(api, shop, **override):
    d = {"StoreName": shop, "Phone": "0" + _rand(9),
         "Category": lay_danh_muc(api),
         "Description": "Mô tả gian hàng đầy đủ cho test"}
    d.update(override)
    return d


def gui_yeu_cau(api, shop, **override):
    return api.post("/api/dang-ky-gian-hang", body_yeu_cau(api, shop, **override))


def ds_yeu_cau(ql):
    st, body = ql.get("/api/seller-requests")
    return (body.get("data") or []) if isinstance(body, dict) else []


def tim_yeu_cau(ql, shop):
    return next((r for r in ds_yeu_cau(ql) if r.get("shop_name") == shop), None)


def tao_pending(new_api, ql, ho_so=True):
    """Tạo customer + yêu cầu pending. Trả (customer, shop_name, request_id)."""
    cust = tao_customer(new_api, co_ho_so=ho_so)
    shop = "Shop TC " + _rand(6)
    st, body = gui_yeu_cau(cust, shop)
    assert body.get("status") is True, f"Không gửi được yêu cầu: {body}"
    r = tim_yeu_cau(ql, shop)
    assert r, "Yêu cầu vừa gửi không có trong danh sách của Quản lý"
    assert r["status"] == "pending"
    return cust, shop, r["request_id"]


def duyet(ql, rid):
    return ql.post(f"/api/duyet-seller/{rid}", {})


def tu_choi(ql, rid, ly_do="Hồ sơ chưa đạt"):
    return ql.post(f"/api/tu-choi-seller/{rid}", {"ly_do": ly_do})


def store_cua(api, uid):
    st, body = api.get(f"/api/stores/by-user/{uid}")
    return body.get("data") if body.get("status") else None


ACTORS = [
    pytest.param("khach1", id="khach1"),
    pytest.param("seller1", id="seller1"),
    pytest.param(None, id="khong_session"),
]


def lam_actor(new_api, ten):
    return new_api((ten, MAT_KHAU)) if ten else new_api()


# ============================================================
# TS-14 — ĐĂNG KÝ GIAN HÀNG
# ============================================================
def test_tc074_dang_ky_gian_hang_day_du(new_api, page, actual):
    ql = new_api(QUAN_LY)
    cust = tao_customer(new_api)  # hồ sơ đủ, chưa có gian hàng
    shop = "Shop Thiên An " + _rand(5)

    dang_nhap_ui(page, cust.username, MAT_KHAU)
    page.locator("#hdrRegisterSellerBtn").click()
    expect(page.locator("#sellerModal")).to_be_visible(timeout=10000)
    page.fill("#selShopName", shop)
    page.fill("#selPhone", "0" + _rand(9))
    page.locator("#selCat").select_option(index=0)
    page.fill("#sellerDesc", "Chuyên đồ điện tử chính hãng")
    page.get_by_role("button", name="Gửi yêu cầu xét duyệt").click()

    expect(page.locator("#toast")).to_contain_text("🎉", timeout=10000)
    actual(f"Toast: '{page.locator('#toast').inner_text()}'")

    r = tim_yeu_cau(ql, shop)
    assert r, "Yêu cầu không xuất hiện trong danh sách của Quản lý"
    actual(f"Request #{r['request_id']} status={r['status']}")
    assert r["status"] == "pending"


def test_tc075_dang_ky_khi_chua_dang_nhap(new_api, actual):
    ql = new_api(QUAN_LY)
    truoc = len(ds_yeu_cau(ql))
    anon = new_api()
    st, body = anon.post("/api/dang-ky-gian-hang",
                         {"StoreName": "Shop Test", "Phone": "0912345678",
                          "Category": "Điện thoại", "Description": "x"})
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert_bi_tu_choi(st, body)
    assert len(ds_yeu_cau(ql)) == truoc, "Có yêu cầu mới bị tạo"


@pytest.mark.parametrize("truong_hop", [
    pytest.param("a_ten_shop_rong", id="a_ten_shop_rong"),
    pytest.param("b_khong_xac_dinh_user", id="b_khong_xac_dinh_user"),
])
def test_tc076_thieu_ten_shop_hoac_userid(new_api, actual, truong_hop):
    """(b) UserId do server lấy từ session (không tin client) nên 'UserId rỗng'
    được mô phỏng bằng việc không có session => không xác định được user."""
    ql = new_api(QUAN_LY)
    truoc = len(ds_yeu_cau(ql))
    if truong_hop == "a_ten_shop_rong":
        cust = tao_customer(new_api)
        st, body = gui_yeu_cau(cust, "")
        assert st < 500
        assert body.get("status") is False
    else:
        anon = new_api()
        st, body = anon.post("/api/dang-ky-gian-hang",
                             body_yeu_cau(anon, "Shop Thiếu UserId " + _rand(4),
                                          UserId=""))
        assert_bi_tu_choi(st, body)
    actual(f"{truong_hop}: HTTP {st}, status={body.get('status')}, "
           f"message='{msg(body)}'")
    assert len(ds_yeu_cau(ql)) == truoc, "Có yêu cầu mới bị tạo"


@pytest.mark.parametrize("truong", [
    pytest.param({"Phone": ""}, id="sdt_kinh_doanh_trong"),
    pytest.param({"Category": ""}, id="danh_muc_trong"),
    pytest.param("ho_so_thieu", id="ho_so_thieu_cmnd_dia_chi"),
])
def test_tc077_thieu_thong_tin_ho_so(new_api, actual, truong):
    """Mô tả (#sellerDesc) KHÔNG bắt buộc theo form -> không đưa vào đây."""
    ql = new_api(QUAN_LY)
    truoc = len(ds_yeu_cau(ql))
    shop = "Shop Thiên An " + _rand(5)
    if truong == "ho_so_thieu":
        cust = tao_customer(new_api, co_ho_so=False)  # chưa có CMND
        st, body = gui_yeu_cau(cust, shop)
    else:
        cust = tao_customer(new_api)
        st, body = gui_yeu_cau(cust, shop, **truong)
    actual(f"{truong}: HTTP {st}, status={body.get('status')}, "
           f"message='{msg(body)}'")
    assert st < 500
    assert body.get("status") is False, "Hệ thống vẫn nhận yêu cầu thiếu thông tin"
    assert msg(body).strip(), "Không có thông báo chỉ rõ trường còn thiếu"
    assert tim_yeu_cau(ql, shop) is None
    assert len(ds_yeu_cau(ql)) == truoc


@pytest.mark.parametrize("loi", [
    pytest.param({"StoreName": "A" * 5000}, id="ten_shop_qua_dai"),
    pytest.param({"Phone": "9" * 500, "Category": "X" * 500}, id="sdt_danh_muc_qua_dai"),
])
def test_tc078_dang_ky_gay_loi_luu_du_lieu(new_api, actual, loi):
    """Ép lỗi ràng buộc DB bằng dữ liệu vượt độ dài cột. (Ngắt hẳn DB cần làm
    thủ công, không tự động hóa được ở đây.)"""
    ql = new_api(QUAN_LY)
    truoc = len(ds_yeu_cau(ql))
    cust = tao_customer(new_api)
    st, body = gui_yeu_cau(cust, "Shop Lỗi " + _rand(4), **loi)
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert st < 500, f"Lỗi 500 không kiểm soát (HTTP {st})"
    assert isinstance(body.get("status"), bool), "Phản hồi không đúng envelope JSON"
    assert msg(body).strip(), "Không có thông báo lỗi dễ hiểu"
    if body["status"] is False:
        assert len(ds_yeu_cau(ql)) == truoc, "Có bản ghi nửa chừng sau khi lỗi"


# ============================================================
# TS-15 — XEM DANH SÁCH YÊU CẦU SELLER
# ============================================================
def test_tc079_quan_ly_xem_danh_sach(new_api, actual):
    ql = new_api(QUAN_LY)
    # Bảo đảm đủ 3 trạng thái: pending / approved / rejected
    _, _, rid_ap = tao_pending(new_api, ql)
    _, _, rid_rj = tao_pending(new_api, ql)
    tao_pending(new_api, ql)
    assert duyet(ql, rid_ap)[1].get("status") is True
    assert tu_choi(ql, rid_rj)[1].get("status") is True

    st, body = ql.get("/api/seller-requests")
    assert st == 200 and body.get("status") is True
    ds = body["data"]
    trang_thai = {r.get("status") for r in ds}
    actual(f"{len(ds)} yêu cầu; trạng thái có: {sorted(trang_thai)}; "
           f"khóa: {sorted(ds[0].keys())}")
    assert {"pending", "approved", "rejected"} <= trang_thai
    for r in ds:
        assert r.get("shop_name"), "Thiếu tên shop"
        assert r.get("ten_user"), "Thiếu người gửi"
        assert r.get("status"), "Thiếu trạng thái"
    assert any(("created" in k.lower() or "time" in k.lower() or "ngay" in k.lower())
               for k in ds[0].keys()), "Danh sách không có trường thời gian gửi"


def test_tc080_chua_dang_nhap_xem_yeu_cau(new_api, actual):
    st, body = new_api().get("/api/seller-requests")
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert_bi_tu_choi(st, body)
    assert not body.get("data")


def test_tc081_customer_xem_yeu_cau(page, actual):
    dang_nhap_ui(page, "khach1", MAT_KHAU)
    page.wait_for_load_state("networkidle")
    expect(page.locator("#adminInterface")).to_be_hidden()
    expect(page.locator("#menu-sellers")).to_be_hidden()
    resp = page.request.get("/api/seller-requests")
    body = resp.json() if resp.ok or resp.status < 500 else {}
    actual(f"HTTP {resp.status}, status={body.get('status')}, message='{msg(body)}'")
    assert resp.status in (401, 403)
    assert not body.get("data")


def test_tc082_seller_xem_yeu_cau(page, actual):
    dang_nhap_ui(page, "seller1", MAT_KHAU)
    page.wait_for_load_state("networkidle")
    expect(page.locator("#adminInterface")).to_be_hidden()
    expect(page.locator("#menu-sellers")).to_be_hidden()
    resp = page.request.get("/api/seller-requests")
    body = resp.json() if resp.status < 500 else {}
    actual(f"HTTP {resp.status}, status={body.get('status')}, message='{msg(body)}'")
    assert resp.status in (401, 403)
    assert not body.get("data")


def test_tc083_danh_sach_phan_anh_du_lieu_request(new_api, actual):
    ql = new_api(QUAN_LY)
    cust = tao_customer(new_api)
    shop = "Shop Đối Chiếu " + _rand(5)
    sdt_kd, mo_ta = "0" + _rand(9), "Mô tả đối chiếu " + _rand(4)
    st, body = gui_yeu_cau(cust, shop, Phone=sdt_kd, Description=mo_ta)
    assert body.get("status") is True, body

    r = tim_yeu_cau(ql, shop)
    assert r, "Không thấy request vừa tạo"
    actual(f"Request: {r}")
    assert r["status"] == "pending"
    assert r.get("ten_user") == cust.name, "Người gửi không khớp"
    assert str(r.get("phone")) == sdt_kd
    assert (r.get("description") or "") == mo_ta
    assert sum(1 for x in ds_yeu_cau(ql) if x.get("shop_name") == shop) == 1


# ============================================================
# TS-16 — DUYỆT YÊU CẦU SELLER
# ============================================================
def test_tc084_duyet_yeu_cau_hop_le(new_api, page, actual):
    ql = new_api(QUAN_LY)
    cust, shop, rid = tao_pending(new_api, ql)
    assert store_cua(ql, cust.uid) is None, "User đã có gian hàng trước khi duyệt"

    st, body = duyet(ql, rid)
    actual(f"Duyệt: HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert body.get("status") is True

    assert tim_yeu_cau(ql, shop)["status"] == "approved"
    store = store_cua(ql, cust.uid)
    assert store, "Không tạo gian hàng liên kết user"
    actual(f"Gian hàng: {store}")

    me2 = new_api((cust.username, MAT_KHAU)).me
    assert me2["ma_nhom_quyen"] == ROLE_SELLER, "User chưa thành Seller"

    dang_nhap_ui(page, cust.username, MAT_KHAU)
    expect(page.locator("#hdrGoSellerBtn")).to_be_visible(timeout=10000)
    expect(page.locator("#sellerDashboard")).to_be_visible(timeout=10000)


def test_tc085_duyet_request_khong_ton_tai(new_api, actual):
    ql = new_api(QUAN_LY)
    truoc = len(ds_yeu_cau(ql))
    st, body = duyet(ql, 99999)
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert st < 500, f"Lỗi server HTTP {st}"
    assert body.get("status") is False
    assert len(ds_yeu_cau(ql)) == truoc


@pytest.mark.parametrize("da_xu_ly", [
    pytest.param("approved", id="da_approved"),
    pytest.param("rejected", id="da_rejected"),
])
def test_tc086_duyet_request_da_xu_ly(new_api, actual, da_xu_ly):
    ql = new_api(QUAN_LY)
    cust, shop, rid = tao_pending(new_api, ql)
    if da_xu_ly == "approved":
        assert duyet(ql, rid)[1].get("status") is True
    else:
        assert tu_choi(ql, rid, "Không đạt")[1].get("status") is True
    store_truoc = store_cua(ql, cust.uid)

    st, body = duyet(ql, rid)
    actual(f"Duyệt lại request {da_xu_ly}: HTTP {st}, status={body.get('status')}, "
           f"message='{msg(body)}'")
    assert st < 500
    assert body.get("status") is False
    assert tim_yeu_cau(ql, shop)["status"] == da_xu_ly, "Trạng thái bị đổi"
    assert store_cua(ql, cust.uid) == store_truoc, "Dữ liệu gian hàng bị đổi"


@pytest.mark.parametrize("nguon", [
    pytest.param("user_vua_duoc_duyet", id="user_vua_duoc_duyet"),
    pytest.param("seller1", id="seller1_co_san"),
])
def test_tc087_duyet_user_da_co_gian_hang(new_api, actual, nguon):
    ql = new_api(QUAN_LY)
    if nguon == "seller1":
        user = new_api(("seller1", MAT_KHAU))
        uid = user.me["ma_user"]
    else:
        cust, _, rid = tao_pending(new_api, ql)
        assert duyet(ql, rid)[1].get("status") is True
        user = new_api((cust.username, MAT_KHAU))  # phiên mới: đã là Seller
        uid = cust.uid
    store_truoc = store_cua(ql, uid)
    assert store_truoc, "Chuẩn bị sai: user chưa có gian hàng"

    shop2 = "Shop Trùng " + _rand(5)
    st, body = gui_yeu_cau(user, shop2)
    actual(f"Gửi request thứ 2: HTTP {st}, status={body.get('status')}, "
           f"message='{msg(body)}'")
    assert st < 500
    if body.get("status") is True:  # nếu hệ thống nhận request -> duyệt phải bị chặn
        r2 = tim_yeu_cau(ql, shop2)
        assert r2, "Không thấy request thứ 2"
        st2, b2 = duyet(ql, r2["request_id"])
        actual(f"Duyệt request thứ 2: HTTP {st2}, status={b2.get('status')}, "
               f"message='{msg(b2)}'")
        assert st2 < 500
        assert b2.get("status") is False, "Duyệt được -> có thể tạo gian hàng trùng"
    assert store_cua(ql, uid) == store_truoc, "Gian hàng của user bị thay đổi/trùng"


@pytest.mark.parametrize("actor", ACTORS)
def test_tc088_duyet_actor_khong_phai_quan_ly(new_api, actual, actor):
    ql = new_api(QUAN_LY)
    cust, shop, rid = tao_pending(new_api, ql)

    api = lam_actor(new_api, actor)
    st, body = duyet(api, rid)
    actual(f"Actor={actor or 'không session'}: HTTP {st}, "
           f"status={body.get('status')}, message='{msg(body)}'")
    assert_bi_tu_choi(st, body)
    assert tim_yeu_cau(ql, shop)["status"] == "pending", "Request không còn pending"
    assert store_cua(ql, cust.uid) is None, "Đã tạo gian hàng"


def test_tc089_hai_phien_cung_duyet(new_api, actual):
    """Mô phỏng tuần tự: phiên A duyệt, ngay sau đó phiên B duyệt cùng request."""
    ql = new_api(QUAN_LY)
    cust, shop, rid = tao_pending(new_api, ql)
    phien_a = new_api(QUAN_LY)
    phien_b = new_api(QUAN_LY)

    st_a, b_a = duyet(phien_a, rid)
    st_b, b_b = duyet(phien_b, rid)
    actual(f"A: HTTP {st_a}, status={b_a.get('status')}; "
           f"B: HTTP {st_b}, status={b_b.get('status')}, message='{msg(b_b)}'")
    assert b_a.get("status") is True
    assert st_b < 500
    assert b_b.get("status") is False, "Lần duyệt thứ hai vẫn có hiệu lực"
    assert tim_yeu_cau(ql, shop)["status"] == "approved"
    assert store_cua(ql, cust.uid), "Không có gian hàng"
    assert sum(1 for r in ds_yeu_cau(ql) if r.get("shop_name") == shop) == 1


# ============================================================
# TS-17 — TỪ CHỐI YÊU CẦU SELLER
# ============================================================
def test_tc090_tu_choi_voi_ly_do_hop_le(new_api, actual):
    ql = new_api(QUAN_LY)
    cust, shop, rid = tao_pending(new_api, ql)
    ly_do = "Hồ sơ chưa đầy đủ thông tin"

    st, body = tu_choi(ql, rid, ly_do)
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert body.get("status") is True

    r = tim_yeu_cau(ql, shop)
    assert r["status"] == "rejected"
    assert r.get("reject_reason") == ly_do, f"Lý do lưu: '{r.get('reject_reason')}'"
    assert new_api((cust.username, MAT_KHAU)).me["ma_nhom_quyen"] == ROLE_CUSTOMER
    assert store_cua(ql, cust.uid) is None, "Đã tạo gian hàng"


@pytest.mark.parametrize("ly_do", [
    pytest.param("", id="rong"),
    pytest.param("   ", id="toan_khoang_trang"),
])
def test_tc091_thieu_ly_do_tu_choi(new_api, actual, ly_do):
    ql = new_api(QUAN_LY)
    cust, shop, rid = tao_pending(new_api, ql)
    st, body = tu_choi(ql, rid, ly_do)
    actual(f"Lý do='{ly_do}': HTTP {st}, status={body.get('status')}, "
           f"message='{msg(body)}'")
    assert st < 500
    assert body.get("status") is False
    assert tim_yeu_cau(ql, shop)["status"] == "pending", "Request không còn pending"


@pytest.mark.parametrize("rid", [
    pytest.param("", id="request_id_trong"),
    pytest.param("99999", id="request_id_99999"),
])
def test_tc092_thieu_hoac_khong_ton_tai_request_id(new_api, actual, rid):
    ql = new_api(QUAN_LY)
    st, body = ql.post(f"/api/tu-choi-seller/{rid}", {"ly_do": "Hồ sơ chưa đạt"})
    actual(f"request_id='{rid}': HTTP {st}, status={body.get('status')}, "
           f"message='{msg(body)}'")
    assert st < 500, f"Lỗi server HTTP {st}"
    assert body.get("status") is not True


@pytest.mark.parametrize("da_xu_ly", [
    pytest.param("approved", id="da_approved"),
    pytest.param("rejected", id="da_rejected"),
])
def test_tc093_tu_choi_request_da_xu_ly(new_api, actual, da_xu_ly):
    ql = new_api(QUAN_LY)
    cust, shop, rid = tao_pending(new_api, ql)
    if da_xu_ly == "approved":
        assert duyet(ql, rid)[1].get("status") is True
    else:
        assert tu_choi(ql, rid, "Lý do ban đầu")[1].get("status") is True
    truoc = tim_yeu_cau(ql, shop)

    st, body = tu_choi(ql, rid, "Test")
    actual(f"Từ chối lại request {da_xu_ly}: HTTP {st}, "
           f"status={body.get('status')}, message='{msg(body)}'")
    assert st < 500
    assert body.get("status") is False
    sau = tim_yeu_cau(ql, shop)
    assert sau["status"] == truoc["status"] == da_xu_ly
    assert sau.get("reject_reason") == truoc.get("reject_reason"), "Lý do bị ghi đè"


@pytest.mark.parametrize("actor", ACTORS)
def test_tc094_tu_choi_actor_khong_phai_quan_ly(new_api, actual, actor):
    ql = new_api(QUAN_LY)
    cust, shop, rid = tao_pending(new_api, ql)

    api = lam_actor(new_api, actor)
    st, body = tu_choi(api, rid, "Hồ sơ chưa đạt")
    actual(f"Actor={actor or 'không session'}: HTTP {st}, "
           f"status={body.get('status')}, message='{msg(body)}'")
    assert_bi_tu_choi(st, body)
    assert tim_yeu_cau(ql, shop)["status"] == "pending", "Request không còn pending"