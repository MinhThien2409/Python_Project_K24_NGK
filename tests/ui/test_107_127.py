"""
TC-107 -> TC-127  |  TS-20 (xem danh mục), TS-21 (tạo), TS-22 (cập nhật), TS-23 (xóa)

Chạy (bật Flask cổng 5000):
    pytest tests/ui/test_107_127.py --base-url http://localhost:5000 -v

LƯU Ý tên file: KHÔNG đặt dạng test_tcNNN... (conftest dò TC ID trên cả nodeid).

Thiết kế:
- Mỗi test tự tạo danh mục riêng (tên có hậu tố ngẫu nhiên vì tên danh mục phải
  duy nhất) và fixture `rac` tự xóa các danh mục đó khi test kết thúc.
  Không đụng tới 6 danh mục seed.
- TC-125 cần danh mục "còn sản phẩm": test tự tạo Seller mới + 1 sản phẩm trong
  danh mục riêng (không có API xóa sản phẩm nên danh mục này sẽ còn lại sau test).
- TC-110 cần DB lỗi thật -> mặc định SKIP (xem hướng dẫn ngay trên test đó).
"""
import os
import random
import string

import pytest
from playwright.sync_api import expect

DEFAULT_BASE = "http://localhost:5000"
MAT_KHAU = "123456"
QUAN_LY = ("quanly1", MAT_KHAU)
ID_KHONG_TON_TAI = 99999


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

    def delete(self, url):
        return self._do("delete", url)


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


@pytest.fixture
def ql(new_api):
    """Client đã đăng nhập quanly1."""
    return new_api(QUAN_LY)


@pytest.fixture
def rac(ql):
    """Danh sách TÊN danh mục test tạo ra -> tự xóa khi test xong."""
    names = []
    yield names
    try:
        for c in lay_ds(ql):
            if c.get("category_name") in names:
                ql.delete(f"/api/categories/{c['category_id']}")
    except Exception:
        pass


def msg(body):
    return (body.get("message") if isinstance(body, dict) else "") or ""


def _rand(n, chars=string.digits):
    return "".join(random.choice(chars) for _ in range(n))


def dang_nhap_ui(page, username, password, cho="#hdrUserBtn"):
    """Đăng nhập qua UI rồi chờ giao diện đích (sau login trang tự reload và
    điều hướng theo vai trò: Customer -> #hdrUserBtn, Seller -> #sellerDashboard,
    Admin/Quản lý -> #adminInterface)."""
    page.goto("/")
    page.locator("#hdrAuthBtn").click()
    page.locator("#loginUsername").wait_for(state="visible", timeout=10000)
    page.fill("#loginUsername", username)
    page.fill("#loginPass", password)
    page.click("#formLogin button[type='submit']")
    expect(page.locator(cho)).to_be_visible(timeout=15000)


def bi_tu_choi(st, body):
    assert st < 500, f"Lỗi server HTTP {st}"
    assert body.get("status") is not True, f"API lại cho phép: {body}"


# ---------- tiện ích danh mục ----------
def lay_ds(api):
    st, b = api.get("/api/categories")
    assert st == 200 and b.get("status") is True, f"HTTP {st} {b}"
    return b["data"]


def tim_dm(api, ten):
    return next((c for c in lay_ds(api) if c.get("category_name") == ten), None)


def dm_theo_id(api, cid):
    return next((c for c in lay_ds(api) if c.get("category_id") == cid), None)


def ten_dm(tien_to="DM TC "):
    return tien_to + _rand(8, string.ascii_letters)


def ten_dai(n):
    """Tên đúng n ký tự, duy nhất."""
    return "D" + _rand(n - 1, string.ascii_letters)


def tao_dm(ql, rac, ten, fee=5):
    rac.append(ten)
    st, b = ql.post("/api/categories", {"name": ten, "phi_san": fee})
    assert b.get("status") is True, f"Không tạo được danh mục '{ten}': HTTP {st} {b}"
    dm = tim_dm(ql, ten)
    assert dm, f"Tạo xong nhưng không thấy '{ten}' trong danh sách"
    return dm


def tao_seller(new_api):
    """Customer mới -> gửi yêu cầu -> quanly1 duyệt -> trả client Seller có shop."""
    qlc = new_api(QUAN_LY)
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
    st, b = qlc.get("/api/seller-requests")
    rid = next(r["request_id"] for r in b["data"] if r.get("shop_name") == shop)
    st, b = qlc.post(f"/api/duyet-seller/{rid}", {})
    assert b.get("status") is True, f"Không duyệt được: {b}"
    return new_api((username, MAT_KHAU))


def kiem_tra_ui_danh_muc(page, ds):
    """Trang chủ hiển thị đủ danh mục (sidebar + dropdown tìm kiếm)."""
    ten = {c["category_name"] for c in ds}
    expect(page.locator("#filterCatList label")).to_have_count(len(ds), timeout=10000)
    expect(page.locator("#searchCategorySelect option")).to_have_count(len(ds) + 1)
    hien = {t.strip() for t in page.locator("#filterCatList label").all_inner_texts()}
    assert hien == ten, f"Sidebar hiển thị {hien}, kỳ vọng {ten}"


def mo_tab_danh_muc_ql(page):
    dang_nhap_ui(page, "quanly1", MAT_KHAU, "#adminInterface")
    expect(page.locator("#pane-categories")).to_be_visible(timeout=10000)
    expect(page.locator("#tblAdminCategoriesBody tr").first).to_be_visible(timeout=10000)


def dong_theo_ten(page, ten):
    page.fill("#catSearchFilter", ten)
    return page.locator("#tblAdminCategoriesBody tr", has_text=ten)


# ============================================================
# TS-20 — XEM DANH MỤC SẢN PHẨM
# ============================================================
def test_tc107_xem_danh_muc_khong_dang_nhap(new_api, page, actual):
    chuan = lay_ds(new_api(QUAN_LY))
    st, b = new_api().get("/api/categories")
    actual(f"HTTP {st}, status={b.get('status')}, số danh mục={len(b.get('data') or [])}")
    assert st == 200 and b.get("status") is True, f"HTTP {st} {b}"
    assert {c["category_name"] for c in b["data"]} == \
           {c["category_name"] for c in chuan}, "Danh sách công khai không đầy đủ"
    assert all(c.get("category_id") and c.get("category_name") for c in b["data"])

    page.goto("/")
    kiem_tra_ui_danh_muc(page, b["data"])


def test_tc108_xem_danh_muc_customer(new_api, page, actual):
    khach = new_api(("khach1", MAT_KHAU))
    ds = lay_ds(khach)
    cong_khai = lay_ds(new_api())
    actual(f"Customer thấy {len(ds)} danh mục, khách thấy {len(cong_khai)}")
    assert {c["category_name"] for c in ds} == {c["category_name"] for c in cong_khai}

    dang_nhap_ui(page, "khach1", MAT_KHAU)
    page.wait_for_load_state("networkidle")
    kiem_tra_ui_danh_muc(page, ds)
    expect(page.locator("#adminInterface")).to_be_hidden()
    expect(page.locator("#sellerDashboard")).to_be_hidden()
    expect(page.get_by_role("button", name="Thêm danh mục")).to_be_hidden()


@pytest.mark.parametrize("user,cho", [
    pytest.param("seller1", "#sellerDashboard", id="seller1"),
    pytest.param("quanly1", "#adminInterface", id="quanly1"),
    pytest.param("admin", "#adminInterface", id="admin"),
])
def test_tc109_xem_danh_muc_seller_quanly_admin(new_api, page, actual, user, cho):
    ds = lay_ds(new_api((user, MAT_KHAU)))
    cong_khai = lay_ds(new_api())
    actual(f"{user} thấy {len(ds)} danh mục")
    assert {c["category_name"] for c in ds} == {c["category_name"] for c in cong_khai}

    dang_nhap_ui(page, user, MAT_KHAU, cho)
    if user == "quanly1":
        expect(page.locator("#pane-categories")).to_be_visible(timeout=10000)
        expect(page.get_by_role("button", name="Thêm danh mục")).to_be_visible()
        hang = page.locator("#tblAdminCategoriesBody tr").first
        expect(hang.get_by_role("button", name="Sửa")).to_be_visible(timeout=10000)
        expect(hang.get_by_role("button", name="Xóa")).to_be_visible()
    else:
        # Seller/Admin không có chức năng thêm/sửa/xóa danh mục
        expect(page.get_by_role("button", name="Thêm danh mục")).to_be_hidden()


@pytest.mark.skipif(not os.environ.get("POBBY_DB_BROKEN"),
                    reason="Cần giả lập DB lỗi thật. Xem hướng dẫn trong test.")
def test_tc110_loi_truy_xuat_du_lieu(new_api, page, actual):
    """
    Chạy thủ công khi đã làm hỏng bảng Categories:
        1) MySQL:  RENAME TABLE Categories TO Categories_bak;
        2) Windows: set POBBY_DB_BROKEN=1
                    pytest tests/ui/test_107_127.py -k tc110 --base-url http://localhost:5000 -v
        3) MySQL:  RENAME TABLE Categories_bak TO Categories;   (khôi phục!)
    """
    st, b = new_api().get("/api/categories")
    actual(f"HTTP {st}, status={b.get('status')}, message='{msg(b)}', "
           f"data={'rỗng' if not b.get('data') else 'có dữ liệu'}")
    assert st < 500, f"Lỗi 500 không kiểm soát: HTTP {st}"
    assert b.get("status") is False or not b.get("data"), \
        "Phải trả status=False hoặc danh sách rỗng khi DB lỗi"

    page.goto("/")
    expect(page.locator("#userInterface")).to_be_visible()  # ứng dụng không crash


# ============================================================
# TS-21 — TẠO DANH MỤC
# ============================================================
def test_tc111_quan_ly_tao_danh_muc_hop_le(ql, rac, page, actual):
    ten = ten_dm("Đồ gia dụng ")
    rac.append(ten)
    mo_tab_danh_muc_ql(page)

    page.get_by_role("button", name="Thêm danh mục").click()
    page.fill("#catModalName", ten)
    page.fill("#catModalFee", "5")
    page.get_by_role("button", name="Lưu danh mục").click()
    expect(page.locator("#toast")).to_contain_text("✅", timeout=10000)
    actual(f"Toast: '{page.locator('#toast').inner_text()}'")

    hang = dong_theo_ten(page, ten)
    expect(hang).to_have_count(1, timeout=10000)
    expect(hang).to_contain_text("5%")

    dm = tim_dm(ql, ten)
    assert dm is not None and float(dm["platform_fee_percent"]) == 5


@pytest.mark.parametrize("ten", [
    pytest.param("", id="rong"),
    pytest.param("   ", id="toan_khoang_trang"),
])
def test_tc112_ten_danh_muc_rong(ql, rac, actual, ten):
    truoc = len(lay_ds(ql))
    st, b = ql.post("/api/categories", {"name": ten, "phi_san": 5})
    actual(f"Tên='{ten}': HTTP {st}, status={b.get('status')}, message='{msg(b)}'")
    assert st < 500
    assert b.get("status") is False
    assert msg(b).strip(), "Không có thông báo yêu cầu nhập tên"
    assert len(lay_ds(ql)) == truoc, "Vẫn tạo ra danh mục"


def test_tc113_ten_100_ky_tu(ql, rac, actual):
    ten = ten_dai(100)
    assert len(ten) == 100
    rac.append(ten)
    st, b = ql.post("/api/categories", {"name": ten, "phi_san": 5})
    actual(f"HTTP {st}, status={b.get('status')}, message='{msg(b)}'")
    assert b.get("status") is True
    assert tim_dm(ql, ten) is not None


def test_tc114_ten_101_ky_tu(ql, rac, actual):
    ten = ten_dai(101)
    assert len(ten) == 101
    rac.append(ten)
    truoc = len(lay_ds(ql))
    st, b = ql.post("/api/categories", {"name": ten, "phi_san": 5})
    actual(f"HTTP {st}, status={b.get('status')}, message='{msg(b)}'")
    assert st < 500
    assert b.get("status") is False
    assert "100" in msg(b), f"Message không báo giới hạn 100 ký tự: '{msg(b)}'"
    assert tim_dm(ql, ten) is None and len(lay_ds(ql)) == truoc


def test_tc115_ten_danh_muc_trung(ql, rac, actual):
    ten = ten_dm("Đồ gia dụng ")
    tao_dm(ql, rac, ten)
    st, b = ql.post("/api/categories", {"name": ten, "phi_san": 5})
    actual(f"HTTP {st}, status={b.get('status')}, message='{msg(b)}'")
    assert st < 500
    assert b.get("status") is False
    m = msg(b).lower()
    assert any(k in m for k in ("tồn tại", "đã có", "trùng", "sử dụng")), \
        f"Message không báo trùng tên: '{msg(b)}'"
    assert sum(1 for c in lay_ds(ql) if c["category_name"] == ten) == 1


@pytest.mark.parametrize("fee,hop_le", [
    pytest.param(-1, False, id="am_1"),
    pytest.param(51, False, id="51"),
    pytest.param("abc", False, id="abc"),
    pytest.param(0, True, id="bien_0_hop_le"),
    pytest.param(50, True, id="bien_50_hop_le"),
])
def test_tc116_phi_san_ngoai_0_50(ql, rac, actual, fee, hop_le):
    ten = ten_dm()
    rac.append(ten)
    st, b = ql.post("/api/categories", {"name": ten, "phi_san": fee})
    actual(f"Phí sàn={fee!r}: HTTP {st}, status={b.get('status')}, message='{msg(b)}'")
    assert st < 500
    if hop_le:
        assert b.get("status") is True
        dm = tim_dm(ql, ten)
        assert dm and float(dm["platform_fee_percent"]) == float(fee)
    else:
        assert b.get("status") is False
        assert tim_dm(ql, ten) is None, "Vẫn tạo danh mục dù phí sàn sai"


@pytest.mark.parametrize("actor", [
    pytest.param("khach1", id="customer"),
    pytest.param("seller1", id="seller"),
    pytest.param(None, id="chua_dang_nhap"),
])
def test_tc117_tao_danh_muc_actor_khong_phai_quan_ly(new_api, ql, rac, actual, actor):
    api = new_api((actor, MAT_KHAU)) if actor else new_api()
    ten = "Danh mục Test " + _rand(6, string.ascii_letters)
    rac.append(ten)
    st, b = api.post("/api/categories", {"name": ten, "phi_san": 5})
    actual(f"{actor or 'không session'}: HTTP {st}, status={b.get('status')}, "
           f"message='{msg(b)}'")
    bi_tu_choi(st, b)
    assert tim_dm(ql, ten) is None, "Danh mục vẫn bị tạo"


# ============================================================
# TS-22 — CẬP NHẬT DANH MỤC
# ============================================================
def test_tc118_cap_nhat_hop_le(ql, rac, page, actual):
    ten = ten_dm("Đồ gia dụng ")
    dm = tao_dm(ql, rac, ten, 5)
    ten_moi = ten + " 2"
    rac.append(ten_moi)

    mo_tab_danh_muc_ql(page)
    hang = dong_theo_ten(page, ten)
    expect(hang).to_have_count(1, timeout=10000)
    hang.get_by_role("button", name="Sửa").click()
    page.fill("#catModalName", ten_moi)
    page.fill("#catModalFee", "8")
    page.get_by_role("button", name="Lưu danh mục").click()
    expect(page.locator("#toast")).to_contain_text("✅", timeout=10000)
    actual(f"Toast: '{page.locator('#toast').inner_text()}'")

    hang_moi = dong_theo_ten(page, ten_moi)
    expect(hang_moi).to_have_count(1, timeout=10000)
    expect(hang_moi).to_contain_text("8%")

    sau = dm_theo_id(ql, dm["category_id"])
    assert sau["category_name"] == ten_moi and float(sau["platform_fee_percent"]) == 8


@pytest.mark.parametrize("ten", [
    pytest.param("", id="rong"),
    pytest.param("   ", id="toan_khoang_trang"),
])
def test_tc119_cap_nhat_ten_rong(ql, rac, actual, ten):
    dm = tao_dm(ql, rac, ten_dm())
    truoc = dm_theo_id(ql, dm["category_id"])
    st, b = ql.put(f"/api/categories/{dm['category_id']}", {"name": ten, "phi_san": 5})
    actual(f"Tên='{ten}': HTTP {st}, status={b.get('status')}, message='{msg(b)}'")
    assert st < 500
    assert b.get("status") is False
    assert dm_theo_id(ql, dm["category_id"]) == truoc, "Dữ liệu cũ bị thay đổi"


def test_tc120_cap_nhat_ten_101_ky_tu(ql, rac, actual):
    dm = tao_dm(ql, rac, ten_dm())
    truoc = dm_theo_id(ql, dm["category_id"])
    st, b = ql.put(f"/api/categories/{dm['category_id']}",
                   {"name": "A" * 101, "phi_san": 5})
    actual(f"HTTP {st}, status={b.get('status')}, message='{msg(b)}'")
    assert st < 500
    assert b.get("status") is False
    assert "100" in msg(b), f"Message không báo tối đa 100 ký tự: '{msg(b)}'"
    assert dm_theo_id(ql, dm["category_id"]) == truoc, "Dữ liệu cũ bị thay đổi"


def test_tc121_cap_nhat_ten_trung_danh_muc_khac(ql, rac, actual):
    a = tao_dm(ql, rac, ten_dm("DM A "))
    b_ = tao_dm(ql, rac, ten_dm("DM B "))
    truoc = dm_theo_id(ql, a["category_id"])
    st, b = ql.put(f"/api/categories/{a['category_id']}",
                   {"name": b_["category_name"], "phi_san": 5})
    actual(f"A đổi sang tên của B: HTTP {st}, status={b.get('status')}, "
           f"message='{msg(b)}'")
    assert st < 500
    assert b.get("status") is False
    m = msg(b).lower()
    assert any(k in m for k in ("tồn tại", "đã có", "trùng", "sử dụng")), \
        f"Message không báo trùng tên: '{msg(b)}'"
    assert dm_theo_id(ql, a["category_id"]) == truoc, "Dữ liệu A bị thay đổi"


@pytest.mark.parametrize("fee", [
    pytest.param(-1, id="am_1"),
    pytest.param(51, id="51"),
    pytest.param("abc", id="abc"),
])
def test_tc122_cap_nhat_phi_san_ngoai_0_50(ql, rac, actual, fee):
    dm = tao_dm(ql, rac, ten_dm(), 5)
    truoc = dm_theo_id(ql, dm["category_id"])
    st, b = ql.put(f"/api/categories/{dm['category_id']}",
                   {"name": dm["category_name"], "phi_san": fee})
    actual(f"Phí sàn={fee!r}: HTTP {st}, status={b.get('status')}, message='{msg(b)}'")
    assert st < 500
    assert b.get("status") is False
    assert dm_theo_id(ql, dm["category_id"]) == truoc, "Dữ liệu cũ bị thay đổi"


def test_tc123_cap_nhat_danh_muc_khong_ton_tai(ql, actual):
    assert dm_theo_id(ql, ID_KHONG_TON_TAI) is None
    st, b = ql.put(f"/api/categories/{ID_KHONG_TON_TAI}",
                   {"name": ten_dm(), "phi_san": 5})
    actual(f"HTTP {st}, status={b.get('status')}, message='{msg(b)}'")
    assert st < 500, f"Lỗi server HTTP {st}"
    assert b.get("status") is False
    m = msg(b).lower()
    assert any(k in m for k in ("không tìm thấy", "không tồn tại", "không có")), \
        f"Message không báo không tìm thấy: '{msg(b)}'"


# ============================================================
# TS-23 — XÓA DANH MỤC
# ============================================================
def test_tc124_xoa_danh_muc_khong_co_san_pham(ql, rac, page, actual):
    ten = ten_dm("Danh mục_test ")
    dm = tao_dm(ql, rac, ten)
    assert dm["so_san_pham"] == 0

    mo_tab_danh_muc_ql(page)
    hang = dong_theo_ten(page, ten)
    expect(hang).to_have_count(1, timeout=10000)
    page.once("dialog", lambda d: d.accept())      # hộp confirm() "Xóa danh mục ...?"
    hang.get_by_role("button", name="Xóa").click()
    expect(page.locator("#toast")).to_contain_text("✅", timeout=10000)
    actual(f"Toast: '{page.locator('#toast').inner_text()}'")

    expect(hang).to_have_count(0, timeout=10000)
    assert tim_dm(ql, ten) is None, "Danh mục vẫn còn trong danh sách"


def test_tc125_xoa_danh_muc_con_san_pham(new_api, ql, rac, actual):
    seller = tao_seller(new_api)
    dm = tao_dm(ql, rac, ten_dm("DM co SP "))
    st, b = seller.post("/api/seller/san-pham", {
        "name": "SP TC125 " + _rand(5), "emoji": "📦", "description": "test",
        "category_id": dm["category_id"], "price": 10000,
        "old_price": None, "quantity": 1})
    assert b.get("status") is True, f"Không tạo được sản phẩm trong danh mục: {b}"

    truoc = dm_theo_id(ql, dm["category_id"])
    assert truoc["so_san_pham"] >= 1

    st, body = ql.delete(f"/api/categories/{dm['category_id']}")
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert st < 500
    assert body.get("status") is False
    assert "sản phẩm" in msg(body).lower(), \
        f"Message không báo danh mục còn sản phẩm: '{msg(body)}'"
    assert dm_theo_id(ql, dm["category_id"]) == truoc, "Dữ liệu bị thay đổi"


def test_tc126_xoa_danh_muc_khong_ton_tai(ql, actual):
    assert dm_theo_id(ql, ID_KHONG_TON_TAI) is None
    st, b = ql.delete(f"/api/categories/{ID_KHONG_TON_TAI}")
    actual(f"HTTP {st}, status={b.get('status')}, message='{msg(b)}'")
    assert st < 500, f"Lỗi server HTTP {st}"
    assert b.get("status") is False
    m = msg(b).lower()
    assert any(k in m for k in ("không tìm thấy", "không tồn tại", "không có")), \
        f"Message không báo không tìm thấy: '{msg(b)}'"


@pytest.mark.parametrize("actor", [
    pytest.param("khach1", id="customer"),
    pytest.param("seller1", id="seller"),
    pytest.param(None, id="chua_dang_nhap"),
])
def test_tc127_xoa_danh_muc_actor_khong_phai_quan_ly(new_api, ql, rac, actual, actor):
    dm = tao_dm(ql, rac, ten_dm())
    truoc = dm_theo_id(ql, dm["category_id"])
    api = new_api((actor, MAT_KHAU)) if actor else new_api()
    st, b = api.delete(f"/api/categories/{dm['category_id']}")
    actual(f"{actor or 'không session'}: HTTP {st}, status={b.get('status')}, "
           f"message='{msg(b)}'")
    bi_tu_choi(st, b)
    assert dm_theo_id(ql, dm["category_id"]) == truoc, "Danh mục bị xóa/thay đổi"