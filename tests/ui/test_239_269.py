"""
TC-239 .. TC-269  (TS-44 .. TS-54: giao diện + kiểm tra bổ sung từ Word)

Chạy:  pytest test_tc239_269_ui_bo_sung.py -v --base-url http://localhost:5000
(conftest.py cần có fixture page, login, actual như các file trước)

Quy ước:
- Không dùng pytest.skip trong thân test (conftest sẽ ghi thành Fail).
- TC có chữ "ghi nhận" trong Excel: chỉ ghi vào actual(), không assert phần chưa chốt.
- Dữ liệu cần thiết (sản phẩm tồn 0/3, đang ẩn, > 12 sản phẩm, shop mới...) được tự tạo.
"""
import re
import time
import uuid

import pytest
from playwright.sync_api import expect

PW = "123456"
SDT = "0901234567"
SHOW = re.compile(r"\bshow\b")
ACTIVE = re.compile(r"\bactive\b")
ID_KHONG_TON_TAI = 99999999


# ============================================================
# HELPER: API
# ============================================================
class Client:
    def __init__(self, ctx, ma_user=None):
        self.ctx = ctx
        self.ma_user = ma_user

    def _call(self, method, url, **kw):
        r = getattr(self.ctx, method)(url, **kw)
        try:
            body = r.json()
        except Exception:
            body = {}
        return r.status, (body if isinstance(body, dict) else {})

    def get(self, url, params=None):
        return self._call("get", url, params=params)

    def post(self, url, data=None):
        return self._call("post", url, data={} if data is None else data)

    def put(self, url, data=None):
        return self._call("put", url, data={} if data is None else data)


@pytest.fixture
def api(playwright, base_url):
    ctxs = []

    def _make(user=None, pw=PW):
        ctx = playwright.request.new_context(base_url=base_url)
        ctxs.append(ctx)
        client = Client(ctx)
        if user:
            st, body = client.post("/api/dang-nhap", {"tendangnhap": user, "mat_khau": pw})
            assert body.get("status"), (
                f"Không đăng nhập được '{user}' (HTTP {st}): {body.get('message')} "
                f"- kiểm tra tài khoản này đã có trong DB chưa")
            client.ma_user = body["data"]["ma_user"]
        return client

    yield _make
    for c in ctxs:
        c.dispose()


def digits(text):
    return int(re.sub(r"\D", "", text or "") or 0)


def login_data(api, user, pw=PW):
    """Dữ liệu trả về khi đăng nhập (ten_user, sdt, dia_chi, cmnd...) - đọc lại giá trị đã lưu."""
    st, b = api().post("/api/dang-nhap", {"tendangnhap": user, "mat_khau": pw})
    return b.get("data") or {}


def dang_nhap_duoc(api, user, pw=PW):
    st, b = api().post("/api/dang-nhap", {"tendangnhap": user, "mat_khau": pw})
    return bool(b.get("status"))


def lay_san_pham(seller):
    st, b = seller.get("/api/seller/san-pham")
    assert b.get("status"), f"Không lấy được sản phẩm seller: {b}"
    return b["data"]


def chon_san_pham(seller, min_qty=5):
    ds = [p for p in lay_san_pham(seller)
          if int(p.get("is_active") or 0) and int(p.get("quantity") or 0) >= min_qty]
    assert ds, f"Shop không có sản phẩm đang bán tồn >= {min_qty}"
    return max(ds, key=lambda p: int(p["quantity"]))


def san_pham_cong_khai(api):
    st, b = api().get("/api/products")
    assert b.get("status"), b
    return b["data"]


def tao_san_pham(seller, ten, price=100000, qty=5, old_price=None, emoji="📦", image_url=None):
    """-> (ok, body, product_id)"""
    st, cats = seller.get("/api/categories")
    cid = cats["data"][0]["category_id"]
    st, b = seller.post("/api/seller/san-pham", {
        "name": ten, "description": "test tự động", "price": price, "old_price": old_price,
        "quantity": qty, "category_id": cid, "emoji": emoji, "image_url": image_url})
    pid = None
    if b.get("status"):
        pid = next((p["id"] for p in lay_san_pham(seller) if p["name"] == ten), None)
    return bool(b.get("status")), b, pid


def an_san_pham(seller, pid, is_active=0):
    return seller.put(f"/api/seller/san-pham/{pid}/an-hien", {"is_active": is_active})


def tao_don(khach, product_ids, qty=1):
    items = [{"ProductId": pid, "ProductName": f"SP {pid}", "Emoji": "📦",
              "Quantity": qty, "UnitPrice": 0, "TotalPrice": 0} for pid in product_ids]
    st, b = khach.post("/api/don-hang/dat-hang", {
        "ReceiverName": "Nguyen Test", "ReceiverPhone": SDT,
        "ShippingAddress": "1 Duong Test, Quan 1, TP HCM",
        "PaymentMethod": "COD", "ShippingFee": 25000, "Items": items})
    assert b.get("status"), f"Không tạo được đơn test: {b.get('message')}"
    return b["data"]["orders"]


def tao_sp_het_hang(seller, khach, ten=None):
    """Tạo sản phẩm tồn 0 (tạo tồn 1 rồi khách mua hết) - không phụ thuộc BUS cho phép tồn 0."""
    ten = ten or f"SP het hang {uuid.uuid4().hex[:6]}"
    ok, b, pid = tao_san_pham(seller, ten, 100000, 1)
    assert ok, f"Setup: tạo sản phẩm lỗi: {b.get('message')}"
    tao_don(khach, [pid], 1)
    return pid, ten


def dat_gio(khach, sellers):
    """Xóa giỏ rồi thêm 1 sản phẩm của mỗi seller (mỗi shop 1 sản phẩm, SL 1)."""
    khach.post("/api/gio-hang/xoa-tat-ca")
    ids = []
    for s in sellers:
        sp = chon_san_pham(s)
        st, b = khach.post("/api/gio-hang/them", {"UserId": khach.ma_user, "ProductId": sp["id"],
                                                  "Quantity": 1, "UnitPrice": sp["price"]})
        assert b.get("status"), f"Setup: thêm giỏ lỗi: {b.get('message')}"
        ids.append(sp["id"])
    return ids


def don_cua_toi(khach):
    st, b = khach.get(f"/api/don-hang/cua-toi/{khach.ma_user}")
    assert b.get("status"), b
    return b["data"]


def tao_khach_moi(api):
    """Customer mới có đủ hồ sơ (đủ điều kiện đăng ký bán)."""
    suffix = uuid.uuid4().hex[:8]
    user = f"khnew_{suffix}"
    ten = f"Khach Moi {suffix}"
    st, b = api().post("/api/dang-ky", {"ten_user": ten, "tendangnhap": user, "sdt": SDT,
                                        "mat_khau": PW, "dia_chi": "1 Duong Test, TP HCM"})
    assert b.get("status"), f"Setup: đăng ký lỗi: {b.get('message')}"
    c = api(user)
    st, b = c.post("/api/cap-nhat-profile", {"ten_user": ten, "dia_chi": "1 Duong Test, TP HCM",
                                             "sdt": SDT, "cmnd": "079" + str(uuid.uuid4().int)[:9]})
    assert b.get("status"), f"Setup: cập nhật hồ sơ lỗi: {b.get('message')}"
    return {"user": user, "ten": ten, "client": c, "suffix": suffix}


def tao_shop_moi(api):
    k = tao_khach_moi(api)
    c = k["client"]
    shop = f"Shop Test {k['suffix']}"
    st, cats = c.get("/api/categories")
    cat = cats["data"][0]
    st, b = c.post("/api/dang-ky-gian-hang", {"StoreName": shop, "Phone": SDT,
                                              "Category": cat.get("category_name"),
                                              "Description": "Shop test tự động"})
    assert b.get("status"), f"Setup: gửi đơn đăng ký bán lỗi: {b.get('message')}"
    ql = api("quanly1")
    st, b = ql.get("/api/seller-requests")
    req = next((r for r in b.get("data", []) if r.get("shop_name") == shop), None)
    assert req, "Setup: không thấy đơn đăng ký"
    st, b = ql.post(f"/api/duyet-seller/{req['request_id']}", {})
    assert b.get("status"), f"Setup: duyệt seller lỗi: {b.get('message')}"
    seller = api(k["user"])
    return {"user": k["user"], "shop": shop, "client": seller}


def dam_bao_nhieu_san_pham(api, n=13):
    ds = san_pham_cong_khai(api)
    if len(ds) >= n:
        return ds
    s1 = api("seller1")
    for i in range(n - len(ds)):
        ok, b, _ = tao_san_pham(s1, f"SP phan trang {uuid.uuid4().hex[:6]}", 100000 + i, 5)
        assert ok, f"Setup: tạo sản phẩm lỗi: {b.get('message')}"
    return san_pham_cong_khai(api)


def dam_bao_trang_thai_san_pham(api, seller, khach):
    """seller có sản phẩm: tồn 0, tồn 1-5, đang ẩn."""
    ds = lay_san_pham(seller)
    act = lambda p: int(p.get("is_active") or 0)
    if not any(int(p["quantity"]) == 0 and act(p) for p in ds):
        tao_sp_het_hang(seller, khach)
    if not any(1 <= int(p["quantity"]) <= 5 and act(p) for p in ds):
        ok, b, _ = tao_san_pham(seller, f"SP sap het {uuid.uuid4().hex[:6]}", 100000, 3)
        assert ok, b
    if not any(not act(p) for p in ds):
        ok, b, pid = tao_san_pham(seller, f"SP an {uuid.uuid4().hex[:6]}", 100000, 10)
        assert ok, b
        an_san_pham(seller, pid, 0)
    return lay_san_pham(seller)


# ============================================================
# HELPER: UI
# ============================================================
def vao_trang_chu(page):
    page.goto("/")
    page.wait_for_function(
        "document.querySelectorAll('#userProductsGrid .product-card, #userProductsGrid .empty-state').length>0",
        timeout=10000)


def ids_the(page):
    ds = page.eval_on_selector_all("#userProductsGrid .product-card",
                                   "els=>els.map(e=>e.getAttribute('onclick'))")
    return [int(re.search(r"openProductDetail\((\d+)\)", o).group(1)) for o in ds]


def gia_the(page):
    return [digits(t) for t in page.locator("#userProductsGrid .card-price").all_inner_texts()]


def da_ban_the(page):
    return [digits(t) for t in page.locator("#userProductsGrid .card-footer span").all_inner_texts()]


def xoa_bo_loc(page):
    page.click(".apply-btn")


def doi_userinterface(page):
    """Đợi khôi phục phiên xong (hienThiGiaoDienTheoVaiTro đặt display='block')."""
    page.wait_for_function(
        "document.getElementById('userInterface').style.display === 'block'", timeout=15000)


def dang_nhap_khach_ui(page, login, user="khach1"):
    login(user, PW)
    doi_userinterface(page)


def vao_kenh_seller(page, login, user):
    login(user, PW)
    page.wait_for_selector("#sellerDashboard", state="visible", timeout=15000)


def vao_admin(page, login, user):
    login(user, PW)
    page.wait_for_selector("#adminInterface", state="visible", timeout=15000)


def dang_xuat_ui(page):
    page.evaluate("handleLogout()")
    page.wait_for_selector("#hdrAuthBtn", state="visible", timeout=15000)


def mo_checkout(page):
    page.click('button[onclick="openCart()"]')
    page.click("#btnCheckoutTrigger")
    expect(page.locator("#checkoutModal")).to_have_class(SHOW)


def doi_gio(page, so_mon):
    expect(page.locator("#cartBadge")).to_have_text(str(so_mon), timeout=10000)


def mo_modal_them_sp_seller(page):
    page.click('button[onclick="openAddSellerProductModal()"]')
    expect(page.locator("#adminProductModal")).to_have_class(SHOW)
    expect(page.locator("#prodCategory option").first).to_be_attached(timeout=10000)


# ============================================================
# TS-44 — Modal Đăng nhập/Đăng ký
# ============================================================
def test_tc239_modal_dang_nhap_dang_ky(page, api, actual):
    page.goto("/")
    page.click("#hdrAuthBtn")
    expect(page.locator("#authModal")).to_have_class(SHOW)
    expect(page.locator("#formLogin")).to_have_class(ACTIVE)

    page.click("#tabRegister")
    expect(page.locator("#formRegister")).to_have_class(ACTIVE)
    expect(page.locator("#formLogin")).not_to_have_class(ACTIVE)
    ids = page.eval_on_selector_all("#formRegister input", "els=>els.map(e=>e.id)")
    nhan = " ".join(page.locator("#formRegister label").all_inner_texts()).lower()
    actual(f"Các ô form Đăng ký: {ids}; nhãn: {nhan}")
    assert ids == ["regName", "regUsername", "regPhone", "regPass"], "Form phải có đúng 4 ô"
    assert "địa chỉ" not in nhan
    assert page.locator("#regPhone").get_attribute("required") is None, "Ô SĐT không có thuộc tính required"

    page.click("#tabLogin")
    expect(page.locator("#formLogin")).to_have_class(ACTIVE)
    page.click("#authModal .modal-close")
    expect(page.locator("#authModal")).not_to_have_class(SHOW)
    page.click("#hdrAuthBtn")
    expect(page.locator("#authModal")).to_have_class(SHOW)

    user = f"customer_ui01_{uuid.uuid4().hex[:6]}"
    page.click("#tabRegister")
    page.fill("#regName", "Nguyễn Văn K")
    page.fill("#regUsername", user)
    page.fill("#regPass", "123456")
    page.click("#formRegister button[type='submit']")
    expect(page.locator("#toast")).to_contain_text("Vui lòng điền đầy đủ", timeout=8000)
    toast = page.locator("#toast").inner_text()
    actual(f"Toast: '{toast}'")
    assert "SĐT" in toast
    assert not dang_nhap_duoc(api, user), "Không được tạo tài khoản khi thiếu SĐT"


def test_tc240_dang_ky_sdt_sai_dinh_dang(page, api, actual):
    ghi = []
    for sdt in ("abc", "123", "123456789012"):
        user = f"customer_ui04_{uuid.uuid4().hex[:8]}"
        st, b = api().post("/api/dang-ky", {"ten_user": "Nguyễn Văn K", "tendangnhap": user,
                                            "sdt": sdt, "mat_khau": PW})
        tao_duoc = dang_nhap_duoc(api, user)
        ghi.append(f"API sdt={sdt!r}: status={b.get('status')}, msg='{b.get('message')}', tạo TK={tao_duoc}")
        assert b.get("status") is False, f"SĐT {sdt!r} phải bị từ chối"
        assert "số điện thoại không hợp lệ" in (b.get("message") or "").lower()
        assert not tao_duoc

    page.goto("/")
    page.click("#hdrAuthBtn")
    page.click("#tabRegister")
    for sdt in ("abc", "123", "123456789012"):
        page.fill("#regName", "Nguyễn Văn K")
        page.fill("#regUsername", f"customer_ui04_{uuid.uuid4().hex[:8]}")
        page.fill("#regPhone", sdt)
        page.fill("#regPass", "123456")
        page.click("#formRegister button[type='submit']")
        expect(page.locator("#toast")).to_contain_text("Số điện thoại không hợp lệ", timeout=8000)
        ghi.append(f"UI sdt={sdt!r}: '{page.locator('#toast').inner_text()}'")
    actual("; ".join(ghi))


# ============================================================
# TS-45 — Cập nhật hồ sơ
# ============================================================
def _cap_nhat_ho_so(k, goc, **ghi_de):
    body = {"ten_user": goc["ten_user"], "dia_chi": goc.get("dia_chi"),
            "sdt": goc.get("sdt"), "cmnd": goc.get("cmnd")}
    body.update(ghi_de)
    return k.post("/api/cap-nhat-profile", body)


def test_tc241_sdt_khoang_trang(api, actual):
    k = api("khach3")
    goc = login_data(api, "khach3")
    try:
        st, b = _cap_nhat_ho_so(k, goc, sdt=" 0912345678 ")
        sau = login_data(api, "khach3").get("sdt")
        actual(f"HTTP {st}, status={b.get('status')}, msg='{b.get('message')}'; "
               f"SĐT sau khi lưu={sau!r} (gốc {goc.get('sdt')!r})")
        assert st < 500
        if b.get("status"):
            assert sau == "0912345678", f"Phải cắt khoảng trắng, đang lưu {sau!r}"
        else:
            assert sau == goc.get("sdt"), "Bị từ chối thì SĐT không được đổi"
    finally:
        _cap_nhat_ho_so(k, goc)


def test_tc242_cmnd_tuy_y(api, actual):
    k = api("khach3")
    goc = login_data(api, "khach3")
    ghi = []
    luu_duoc_sai = []
    try:
        for cmnd in ("ABC123xyz", "1" * 50, "!@#$%^&*"):
            st, b = _cap_nhat_ho_so(k, goc, cmnd=cmnd)
            sau = login_data(api, "khach3").get("cmnd")
            ghi.append(f"cmnd={cmnd[:12]!r}: status={b.get('status')}, msg='{b.get('message')}', "
                       f"đã lưu={str(sau)[:12]!r}")
            assert st < 500, f"CMND {cmnd[:12]!r}: server lỗi HTTP {st}"
            if b.get("status") and sau == cmnd:
                luu_duoc_sai.append(cmnd[:12])
        # Excel TC-242: chỉ ghi nhận hệ thống có chặn hay không, không assert từ chối
        ghi.append("Kết luận: " + (f"THIẾU KIỂM TRA CMND - lưu được giá trị sai {luu_duoc_sai}"
                                   if luu_duoc_sai else "hệ thống có chặn CMND không hợp lệ"))
    finally:
        actual("; ".join(ghi))
        _cap_nhat_ho_so(k, goc)      # trả hồ sơ khach3 về như cũ

# ============================================================
# TS-46 — Duyệt / lọc / sắp xếp / phân trang sản phẩm phía khách
# ============================================================
def test_tc243_logo_pobby_reset(page, actual):
    loi = []
    page.on("pageerror", lambda e: loi.append(str(e)))
    vao_trang_chu(page)
    page.fill("#userSearchInput", "áo")
    page.evaluate("goToPage(2)")
    page.click("header a.logo")
    page.wait_for_timeout(500)
    keyword = page.input_value("#userSearchInput")
    trang = page.evaluate("currentPage")
    actual(f"Lỗi JS: {loi}; keyword sau khi bấm logo='{keyword}'; currentPage={trang}")
    assert not loi, f"Console có lỗi: {loi}"
    assert keyword == "" and trang == 1, "Bấm logo phải về trang chủ và reset lọc"


def test_tc244_xoa_bo_loc(page, api, actual):
    ds = san_pham_cong_khai(api)
    vao_trang_chu(page)
    page.locator("#filterCatList input").first.check()
    page.select_option("#searchCategorySelect", index=1)
    page.fill("#priceMin", "100000")
    page.fill("#priceMax", "1000000")
    page.check("#chkInStock")
    page.check("#chkOnSale")
    page.select_option("#sortSelect", "price-asc")
    page.fill("#userSearchInput", "nồi")
    page.wait_for_timeout(700)
    xoa_bo_loc(page)
    trang = page.evaluate("currentPage")
    raw = page.evaluate("[document.getElementById('priceMin').dataset.rawValue, "
                        "document.getElementById('priceMax').dataset.rawValue]")
    n_the = len(ids_the(page))
    actual(f"checked={page.locator('#filterCatList input:checked').count()}, "
           f"priceMin='{page.input_value('#priceMin')}', priceMax='{page.input_value('#priceMax')}', raw={raw}, "
           f"dropdown={page.input_value('#searchCategorySelect')}, sort={page.input_value('#sortSelect')}, "
           f"trang={trang}, số thẻ={n_the}/{len(ds)}")
    assert page.locator("#filterCatList input:checked").count() == 0
    assert page.input_value("#priceMin") == "" and page.input_value("#priceMax") == ""
    assert raw in (["", ""], [None, None], ["", None], [None, ""])
    assert page.input_value("#userSearchInput") == ""
    assert page.input_value("#searchCategorySelect") == "all"
    assert page.input_value("#sortSelect") == "default"
    assert not page.is_checked("#chkInStock") and not page.is_checked("#chkOnSale")
    assert trang == 1
    assert n_the == min(12, len(ds)), "Danh sách phải đầy đủ"


def test_tc245_sap_xep(page, api, actual):
    ds = san_pham_cong_khai(api)
    vao_trang_chu(page)
    mac_dinh = ids_the(page)
    ghi = []

    page.select_option("#sortSelect", "price-asc")
    g = gia_the(page)
    ghi.append(f"asc={g[:5]}")
    assert g == sorted(g) and g[0] == min(float(p["price"]) for p in ds), "Giá tăng dần sai"

    page.select_option("#sortSelect", "price-desc")
    g = gia_the(page)
    ghi.append(f"desc={g[:5]}")
    assert g == sorted(g, reverse=True) and g[0] == max(float(p["price"]) for p in ds), "Giá giảm dần sai"

    page.select_option("#sortSelect", "bestseller")
    d = da_ban_the(page)
    ghi.append(f"bán chạy={d[:5]}")
    assert d == sorted(d, reverse=True) and d[0] == max(int(p.get("sold") or 0) for p in ds), "Bán chạy sai"

    page.select_option("#sortSelect", "default")
    assert ids_the(page) == mac_dinh, "'Nổi bật nhất' giữ thứ tự từ API"

    page.select_option("#sortSelect", "newest")
    ghi.append(f"'Mới nhất' giữ nguyên thứ tự API: {ids_the(page) == mac_dinh} (ghi nhận)")
    actual("; ".join(ghi))


def test_tc246_ve_trang_1_khi_doi_loc(page, api, actual):
    ds = dam_bao_nhieu_san_pham(api, 13)
    vao_trang_chu(page)
    ghi = []

    page.evaluate("goToPage(2)")
    assert page.evaluate("currentPage") == 2, "Setup: phải sang được trang 2"
    page.fill("#userSearchInput", "nồi")
    ky_vong = [p for p in ds if "nồi" in p["name"].lower()]
    ghi.append(f"keyword: trang={page.evaluate('currentPage')}, thẻ={len(ids_the(page))}/{len(ky_vong)}")
    assert page.evaluate("currentPage") == 1
    assert len(ids_the(page)) == min(12, len(ky_vong))

    page.fill("#userSearchInput", "")
    page.evaluate("goToPage(2)")
    assert page.evaluate("currentPage") == 2
    cb = page.locator("#filterCatList input").first
    ten_dm = cb.get_attribute("value")
    cb.check()
    ky_vong = [p for p in ds if p.get("category_name") == ten_dm]
    ghi.append(f"danh mục '{ten_dm}': trang={page.evaluate('currentPage')}, thẻ={len(ids_the(page))}/{len(ky_vong)}")
    assert page.evaluate("currentPage") == 1
    assert len(ids_the(page)) == min(12, len(ky_vong))
    cb.uncheck()

    page.evaluate("goToPage(2)")
    assert page.evaluate("currentPage") == 2
    page.select_option("#sortSelect", "price-asc")
    g = gia_the(page)
    ghi.append(f"sort: trang={page.evaluate('currentPage')}, giá đầu={g[:3]}")
    assert page.evaluate("currentPage") == 1
    assert g == sorted(g)
    actual("; ".join(ghi))


def test_tc247_phan_trang(page, api, actual):
    ds = dam_bao_nhieu_san_pham(api, 25)
    n = len(ds)
    so_trang = -(-n // 12)
    vao_trang_chu(page)
    nut = page.locator("#paginationWrap button")
    assert nut.count() == so_trang + 2, f"Cần {so_trang} nút số + ‹ + ›"
    assert len(ids_the(page)) == 12
    truoc, sau = nut.first, nut.last
    assert truoc.is_disabled(), "‹ phải bị khóa ở trang 1"
    kieu = lambda b: (b.get_attribute("style") or "").replace(" ", "")
    assert "color:white" in kieu(nut.nth(1)), "Trang hiện tại phải tô nổi bật"
    trang1 = ids_the(page)

    nut.nth(2).click()
    assert page.evaluate("currentPage") == 2 and ids_the(page) != trang1
    page.wait_for_timeout(1200)
    y = page.locator("#userProductsGrid").bounding_box()["y"]
    page.locator("#paginationWrap button").last.click()
    assert page.evaluate("currentPage") == 3 or so_trang == 2
    page.locator("#paginationWrap button").nth(so_trang).click()
    assert page.evaluate("currentPage") == so_trang
    assert page.locator("#paginationWrap button").last.is_disabled(), "› phải bị khóa ở trang cuối"
    assert len(ids_the(page)) == n - 12 * (so_trang - 1)
    actual(f"{n} sản phẩm, {so_trang} trang; sau khi đổi trang grid.y={y:.0f}")
    assert -10 <= y <= 250, "Đổi trang phải cuộn lên đầu danh sách"

    page.fill("#userSearchInput", ds[0]["name"])
    assert page.locator("#paginationWrap").inner_html().strip() == "", "≤ 12 sản phẩm thì không hiện phân trang"


def test_tc248_loc_khoang_gia(page, api, actual):
    ds = dam_bao_nhieu_san_pham(api, 13)
    vao_trang_chu(page)
    tat_ca = ids_the(page)
    ghi = []

    page.fill("#priceMin", "19900000")
    page.fill("#priceMax", "30000000")
    page.wait_for_timeout(700)  # chờ debounce
    ghi_min = page.input_value("#priceMin")  # đọc sau khi chờ (chuyển dòng này
    ky_vong = [p for p in ds if 19900000 <= float(p["price"]) <= 30000000]
    ghi.append(f"định dạng ô Từ='{ghi_min}'; lọc 19.9tr-30tr: {len(ids_the(page))}/{len(ky_vong)}")

    assert re.fullmatch(r"\d{1,3}([.,]\d{3})+", ghi_min), "Ô giá phải tự định dạng dấu chấm"
    assert all(19900000 <= x <= 30000000 for x in gia_the(page))
    assert len(ids_the(page)) == min(12, len(ky_vong))

    page.fill("#priceMin", "abc")
    page.wait_for_timeout(700)  # thêm dòng này
    assert page.input_value("#priceMin") == ""

    page.fill("#priceMin", "5000000")
    page.wait_for_timeout(700)
    page.fill("#priceMax", "1000000")
    page.wait_for_timeout(700)
    toast = page.locator("#toast").inner_text()
    grid = page.locator("#userProductsGrid").inner_text()
    ghi.append(f"Từ>Đến: toast='{toast}', grid có 'Không tìm thấy'={'Không tìm thấy sản phẩm' in grid}")
    assert "Không tìm thấy sản phẩm" in grid or "không được lớn hơn" in toast, \
        "Từ > Đến phải báo không tìm thấy / báo khoảng giá không hợp lệ"

    xoa_bo_loc(page)
    page.fill("#priceMin", "19900000")
    page.wait_for_timeout(700)
    assert all(x >= 19900000 for x in gia_the(page)), "Chỉ nhập Từ"
    xoa_bo_loc(page)
    page.fill("#priceMax", "1000000")
    page.wait_for_timeout(700)
    assert all(x <= 1000000 for x in gia_the(page)), "Chỉ nhập Đến"

    xoa_bo_loc(page)
    page.fill("#priceMin", "19900000")
    page.wait_for_timeout(700)
    page.fill("#priceMin", "")
    page.wait_for_timeout(700)
    ghi.append(f"Xóa trống ô: trở lại danh sách đầy đủ={ids_the(page) == tat_ca}")
    assert ids_the(page) == tat_ca, "Xóa trống ô thì không còn lọc theo giá cũ"

    page.fill("#priceMin", "19900000")
    xoa_bo_loc(page)
    assert page.input_value("#priceMin") == "" and ids_the(page) == tat_ca
    actual("; ".join(ghi))


def test_tc249_loc_con_hang_dang_giam_gia(page, api, actual):
    s1, khach = api("seller1"), api("khach1")
    tao_sp_het_hang(s1, khach)
    tao_san_pham(s1, f"SP giam gia {uuid.uuid4().hex[:6]}", 100000, 5, old_price=200000)
    tao_san_pham(s1, f"SP khong giam {uuid.uuid4().hex[:6]}", 100000, 5)
    ds = san_pham_cong_khai(api)
    con_hang = lambda p: int(p.get("quantity") or 0) > 0
    dang_giam = lambda p: bool(p.get("old_price")) and float(p["old_price"]) > float(p["price"])
    vao_trang_chu(page)

    def kiem(nhan, dk):
        ky_vong = {p["id"] for p in ds if dk(p)}
        ids = ids_the(page)
        ghi.append(f"{nhan}: UI {len(ids)} / kỳ vọng {len(ky_vong)}")
        assert set(ids) <= ky_vong, f"{nhan}: có sản phẩm không thỏa điều kiện"
        assert len(ids) == min(12, len(ky_vong)), f"{nhan}: sai số lượng"

    ghi = [f"dữ liệu: {sum(1 for p in ds if not con_hang(p))} hết hàng, "
           f"{sum(1 for p in ds if dang_giam(p))} đang giảm"]
    page.check("#chkInStock")
    kiem("Còn hàng", con_hang)
    page.uncheck("#chkInStock")
    page.check("#chkOnSale")
    kiem("Đang giảm giá", dang_giam)
    page.check("#chkInStock")
    kiem("Cả hai", lambda p: con_hang(p) and dang_giam(p))

    sp_giam = next((p for p in ds if dang_giam(p) and con_hang(p)), None)
    assert sp_giam, "Setup: cần sản phẩm đang giảm giá và còn hàng"
    page.locator(f'#filterCatList input[value="{sp_giam["category_name"]}"]').check()
    page.fill("#priceMax", "5000000")
    page.wait_for_timeout(700)
    kiem("Kết hợp danh mục + giá", lambda p: con_hang(p) and dang_giam(p)
         and p["category_name"] == sp_giam["category_name"] and float(p["price"]) <= 5000000)
    actual("; ".join(ghi))


# ============================================================
# TS-47 — Cộng dồn số lượng vượt tồn kho
# ============================================================
def test_tc250_cong_don_vuot_ton_kho(api, actual):
    s1, khach = api("seller1"), api("khach1")
    ok, b, pid = tao_san_pham(s1, f"SP ton 3 {uuid.uuid4().hex[:6]}", 100000, 3)
    assert ok, b
    khach.post("/api/gio-hang/xoa-tat-ca")
    try:
        ghi = []
        for lan in (1, 2):
            st, r = khach.post("/api/gio-hang/them", {"UserId": khach.ma_user, "ProductId": pid,
                                                      "Quantity": 2, "UnitPrice": 100000})
            ghi.append(f"lần {lan}: status={r.get('status')}, msg='{r.get('message')}'")
        st, gio = khach.get(f"/api/gio-hang/{khach.ma_user}")
        sl = sum(int(i.get("Quantity", i.get("quantity", 0)))
                 for i in gio.get("data", []) if int(i.get("ProductId", i.get("product_id", 0))) == pid)
        st, dh = khach.post("/api/don-hang/dat-hang", {
            "ReceiverName": "Nguyen Test", "ReceiverPhone": SDT, "ShippingAddress": "1 Test",
            "PaymentMethod": "COD", "ShippingFee": 25000,
            "Items": [{"ProductId": pid, "ProductName": "x", "Quantity": 4, "UnitPrice": 0, "TotalPrice": 0}]})
        ghi.append(f"SL trong giỏ={sl} (tồn 3); đặt 4: status={dh.get('status')}, msg='{dh.get('message')}'")
        actual("; ".join(ghi))
        assert sl <= 3, f"Giỏ cộng dồn vượt tồn kho: {sl} > 3"
        assert dh.get("status") is False, "Đặt vượt tồn kho phải bị backend chặn"
    finally:
        khach.post("/api/gio-hang/xoa", {"UserId": khach.ma_user, "ProductId": pid})
        an_san_pham(s1, pid, 0)


# ============================================================
# TS-48 — Checkout
# ============================================================
def test_tc251_checkout_doi_tinh_thanh_phi_ship(page, login, api, actual):
    s1, s2, khach = api("seller1"), api("seller2"), api("khach1")
    ghi = []
    dat_gio(khach, [s1])
    dang_nhap_khach_ui(page, login)
    thong_tin = login_data(api, "khach1")
    for so_shop, sellers in ((1, [s1]), (2, [s1, s2])):
        if so_shop == 2:
            dat_gio(khach, sellers)
            page.reload()
            doi_userinterface(page)
        doi_gio(page, so_shop)
        mo_checkout(page)
        assert page.input_value("#chkName") == thong_tin["ten_user"]
        assert page.input_value("#chkPhone") == thong_tin["sdt"]
        assert page.input_value("#chkAddress") == thong_tin["dia_chi"]
        for ma, ten in (("hcm", "TP.HCM"), ("hn", "Hà Nội"), ("dn", "Đà Nẵng"),
                        ("ct", "Cần Thơ"), ("other", "Tỉnh khác")):
            page.select_option("#chkBuyerCity", ma)
            phi = digits(page.inner_text("#shippingFeeDisplay"))
            nhan = page.inner_text("#shippingNote").lower()
            tam_tinh = digits(page.inner_text("#checkoutSubtotalText"))
            tong = digits(page.inner_text("#checkoutTotalText"))
            ky_vong = (25000 if ma == "hcm" else 40000) * so_shop
            ghi.append(f"{so_shop} shop/{ten}: phí={phi} (kỳ vọng {ky_vong})")
            assert phi == ky_vong, f"{so_shop} shop, {ten}: phí {phi} != {ky_vong}"
            assert ("nội thành" if ma == "hcm" else "liên tỉnh") in nhan
            assert tong == tam_tinh + phi, "Tổng thanh toán phải = tạm tính + phí ship"
        page.click("#checkoutModal .modal-close")
        page.evaluate("closeCart()")
    khach.post("/api/gio-hang/xoa-tat-ca")
    actual("; ".join(ghi))


def test_tc252_checkout_phuong_thuc_thanh_toan(page, login, api, actual):
    s1, khach = api("seller1"), api("khach1")
    dat_gio(khach, [s1])
    dang_nhap_khach_ui(page, login)
    doi_gio(page, 1)
    mo_checkout(page)
    khoi = {"bank": "#bankDetailsBlock", "momo": "#momoBlock", "vnpay": "#zalopayBlock"}
    cho_hien = {"COD": None, "Bank": "bank", "Momo": "momo", "VNPay": "vnpay"}
    ghi = []
    for pt, khoi_hien in cho_hien.items():
        page.select_option("#chkPayment", pt)
        hien = [k for k, sel in khoi.items() if page.is_visible(sel)]
        ghi.append(f"{pt}: hiện {hien}")
        assert hien == ([khoi_hien] if khoi_hien else []), f"{pt}: chỉ được hiện đúng 1 khối ({hien})"
        if pt == "Bank":
            txt = page.inner_text("#bankDetailsBlock")
            assert "MB Bank" in txt and "POBBYPAY" in txt
        if pt == "Momo":
            assert "MoMo" in page.inner_text("#momoBlock")
        if pt == "VNPay":
            ghi.append(f"nhãn khối VNPay='{page.inner_text('#zalopayBlock').strip()}' (ghi nhận lệch nhãn ZaloPay)")
    khach.post("/api/gio-hang/xoa-tat-ca")
    actual("; ".join(ghi))


def test_tc253_phi_ship_so_voi_hoa_don(page, login, api, actual):
    s1, s2, khach = api("seller1"), api("seller2"), api("khach1")
    kich_ban = [("A: 1 shop, TP.HCM", [s1], "hcm", 25000),
                ("B: 1 shop, tỉnh khác", [s1], "hn", 40000),
                ("C: 2 shop, TP.HCM", [s1, s2], "hcm", 50000)]
    ghi = []
    for i, (ten, sellers, tinh, ky_vong) in enumerate(kich_ban):
        dat_gio(khach, sellers)
        if i == 0:
            dang_nhap_khach_ui(page, login)
        else:
            page.reload()
            doi_userinterface(page)
        doi_gio(page, len(sellers))
        truoc = {o["OrderId"] for o in don_cua_toi(khach)}
        mo_checkout(page)
        page.select_option("#chkBuyerCity", tinh)
        phi_ui = digits(page.inner_text("#shippingFeeDisplay"))
        page.click('#checkoutModal button[type="submit"]')
        expect(page.locator("#invoiceModal")).to_have_class(SHOW, timeout=15000)
        moi = [o["OrderId"] for o in don_cua_toi(khach) if o["OrderId"] not in truoc]
        phi_hd = 0.0
        for oid in moi:
            st, hd = khach.get(f"/api/don-hang/hoa-don/{oid}")
            phi_hd += float(hd["data"].get("ShippingFee") or 0)
        ghi.append(f"{ten}: UI={phi_ui}, hóa đơn={phi_hd:.0f} ({len(moi)} đơn)")
        assert len(moi) == len(sellers)
        assert phi_ui == ky_vong, f"{ten}: phí ở bước thanh toán {phi_ui} != {ky_vong}"
        assert phi_hd == pytest.approx(phi_ui), f"{ten}: hóa đơn lệch phí ship"
    actual("; ".join(ghi))


def test_tc254_san_pham_bi_an_luc_dat_hang(page, login, api, actual):
    s1, khach = api("seller1"), api("khach1")
    ok, b, pid = tao_san_pham(s1, f"SP se an {uuid.uuid4().hex[:6]}", 100000, 5)
    assert ok, b
    khach.post("/api/gio-hang/xoa-tat-ca")
    st, r = khach.post("/api/gio-hang/them", {"UserId": khach.ma_user, "ProductId": pid,
                                              "Quantity": 1, "UnitPrice": 100000})
    assert r.get("status"), r
    try:
        dang_nhap_khach_ui(page, login)
        doi_gio(page, 1)
        truoc = len(don_cua_toi(khach))
        an_san_pham(s1, pid, 0)                       # Seller ẩn khi khách chưa tải lại trang
        mo_checkout(page)
        page.click('#checkoutModal button[type="submit"]')
        expect(page.locator("#toast")).to_contain_text("không còn kinh doanh", timeout=8000)
        sau = len(don_cua_toi(khach))
        actual(f"Toast: '{page.locator('#toast').inner_text()}'; số đơn {truoc}->{sau}")
        assert sau == truoc, "Không được tạo đơn"
    finally:
        khach.post("/api/gio-hang/xoa-tat-ca")
        an_san_pham(s1, pid, 0)


# ============================================================
# TS-49 — Gửi đơn đăng ký bán nhiều lần
# ============================================================
def test_tc255_gui_don_dang_ky_ban_lan_2(api, actual):
    k = tao_khach_moi(api)
    c, ql = k["client"], api("quanly1")
    shop = f"Shop Thien An {k['suffix']}"
    st, cats = c.get("/api/categories")
    body = {"StoreName": shop, "Phone": SDT, "Category": cats["data"][0]["category_name"],
            "Description": "test"}
    ghi = []
    st, b1 = c.post("/api/dang-ky-gian-hang", body)
    st, b2 = c.post("/api/dang-ky-gian-hang", body)
    ghi.append(f"lần 1: {b1.get('status')}; lần 2: status={b2.get('status')}, msg='{b2.get('message')}'")

    dem = lambda tt: [r for r in ql.get("/api/seller-requests")[1].get("data", [])
                      if r.get("shop_name") == shop and r.get("status") == tt]
    pending = dem("pending")
    ghi.append(f"số đơn pending sau lần 2={len(pending)}")
    assert b1.get("status") is True
    assert b2.get("status") is False, "Đơn thứ 2 khi đang pending phải bị chặn"
    assert "chờ" in (b2.get("message") or "").lower()
    assert len(pending) == 1

    st, r = ql.post(f"/api/tu-choi-seller/{pending[0]['request_id']}", {"ly_do": "Test từ chối"})
    assert r.get("status"), r
    st, b3 = c.post("/api/dang-ky-gian-hang", body)
    ghi.append(f"gửi lại sau từ chối: status={b3.get('status')}, msg='{b3.get('message')}'; "
               f"pending={len(dem('pending'))}, rejected={len(dem('rejected'))}")
    actual("; ".join(ghi))
    assert b3.get("status") is True, "Sau khi bị từ chối phải được gửi lại"
    assert len(dem("pending")) == 1 and len(dem("rejected")) == 1


# ============================================================
# TS-50 — Quản lý danh mục
# ============================================================
def test_tc256_tim_kiem_danh_muc(page, login, api, actual):
    st, b = api().get("/api/categories")
    cats = b["data"]
    ten_mau = next((c["category_name"] for c in cats if "gia" in c["category_name"].lower()),
                   cats[0]["category_name"])
    vao_admin(page, login, "quanly1")
    expect(page.locator("#pane-categories")).to_be_visible()
    tbody = page.locator("#tblAdminCategoriesBody")
    expect(tbody).not_to_contain_text("Đang tải", timeout=10000)
    hang = page.locator("#tblAdminCategoriesBody tr")
    ghi = []
    assert hang.count() == len(cats)

    ky_vong = [c for c in cats if ten_mau.lower() in c["category_name"].lower()]
    for kw in (ten_mau.lower(), ten_mau.upper()):
        page.fill("#catSearchFilter", kw)
        ten_ui = page.locator("#tblAdminCategoriesBody tr td:nth-child(2)").all_inner_texts()
        ghi.append(f"kw='{kw}': {len(ten_ui)} dòng / kỳ vọng {len(ky_vong)}")
        assert len(ten_ui) == len(ky_vong) and all(ten_mau.lower() in t.lower() for t in ten_ui)

    page.fill("#catSearchFilter", "zzzz")
    assert "Không tìm thấy kết quả" in tbody.inner_text()
    page.fill("#catSearchFilter", "")
    assert hang.count() == len(cats), "Xóa keyword phải trả lại đủ danh sách"

    for i, c in enumerate(cats):
        phi = hang.nth(i).locator("td:nth-child(3)").inner_text().strip()
        sl = hang.nth(i).locator("td:nth-child(4)").inner_text().strip()
        assert re.fullmatch(r"\d+(\.\d+)?%", phi), f"Phí sàn '{phi}' phải dạng x%"
        assert sl == f"{c.get('so_san_pham') or 0} sản phẩm", f"Số sản phẩm '{sl}' sai"
    actual("; ".join(ghi))


def test_tc257_doi_phi_san_anh_huong_seller(page, login, api, actual):
    ql = api("quanly1")
    st, b = ql.get("/api/categories")
    cat = b["data"][0]
    fee_goc = float(cat.get("platform_fee_percent") or 0)
    fee_moi = 7 if fee_goc != 7 else 8
    cap_nhat = lambda f: ql.put(f"/api/categories/{cat['category_id']}",
                                {"name": cat["category_name"], "phi_san": f})
    st, r = cap_nhat(fee_moi)
    assert r.get("status"), f"Setup: đổi phí sàn lỗi: {r}"
    try:
        vao_kenh_seller(page, login, "seller1")
        page.click("#smenu-products")
        mo_modal_them_sp_seller(page)
        page.fill("#prodOldPrice", "1000000")
        expect(page.locator("#feeGocBox")).to_be_visible()
        nhan = page.inner_text("#feeGocLabel")
        phi = digits(page.inner_text("#feeGocPhi"))
        thuc = digits(page.inner_text("#feeGocSauPhi"))
        page.click("#adminProductModal .modal-close")
        page.click("#smenu-overview")
        expect(page.locator("#sellerOverviewContent")).not_to_contain_text("Đang tải", timeout=10000)
        tong_quan = page.inner_text("#sellerOverviewContent").lower()
        actual(f"Phí sàn {fee_goc}%->{fee_moi}%: nhãn='{nhan}', phí={phi}, thực nhận={thuc}; "
               f"Tổng quan có 'thu nhập thực tế'={'thu nhập thực tế' in tong_quan}")
        assert f"({fee_moi}%)" in nhan, f"Form sản phẩm phải theo phí sàn mới {fee_moi}%"
        assert phi == 1000000 * fee_moi // 100 and thuc == 1000000 - phi
    finally:
        cap_nhat(fee_goc)


# ============================================================
# TS-51 — Điều hướng, menu theo vai trò, modal, toast
# ============================================================
def test_tc258_menu_theo_vai_tro(page, login, actual):
    ghi = []
    vao_admin(page, login, "admin")
    expect(page.locator("#menu-users")).to_have_class(ACTIVE, timeout=10000)
    hien = {t: page.is_visible(f"#menu-{t}") for t in ("categories", "sellers", "users")}
    ghi.append(f"Admin: {hien}")
    assert hien == {"categories": False, "sellers": False, "users": True}
    assert page.is_visible("#pane-users") and not page.is_visible("#pane-categories")
    assert page.is_visible("#adminInterface .topbar button")
    page.click("#adminInterface .topbar button")
    page.wait_for_selector("#hdrAuthBtn", state="visible", timeout=15000)

    vao_admin(page, login, "quanly1")
    expect(page.locator("#menu-categories")).to_have_class(ACTIVE, timeout=10000)
    hien = {t: page.is_visible(f"#menu-{t}") for t in ("categories", "sellers", "users")}
    ghi.append(f"Quản lý: {hien}")
    assert all(hien.values())
    for tab in ("sellers", "users", "categories"):
        page.click(f"#menu-{tab}")
        expect(page.locator(f"#menu-{tab}")).to_have_class(ACTIVE)
        for khac in {"categories", "sellers", "users"} - {tab}:
            assert not page.is_visible(f"#pane-{khac}")
            assert not re.search(r"\bactive\b", page.get_attribute(f"#menu-{khac}", "class") or "")
        assert page.is_visible(f"#pane-{tab}")
    actual("; ".join(ghi))


def test_tc259_dieu_huong_6_tab_seller(page, login, actual):
    vao_kenh_seller(page, login, "seller1")
    tabs = ["overview", "products", "nhaphang", "orders", "shop", "gia"]
    cho_du_lieu = {
        "overview": "#sellerOverviewContent", "products": "#tblSellerProductsBody",
        "nhaphang": "#spNhapHangBody", "orders": "#tblSellerOrdersBody", "gia": "#tblSellerGiaBody"}
    ghi = []
    for t in tabs:
        page.click(f"#smenu-{t}")
        expect(page.locator(f"#smenu-{t}")).to_have_class(ACTIVE)
        assert page.is_visible(f"#spane-{t}")
        for khac in set(tabs) - {t}:
            assert not page.is_visible(f"#spane-{khac}"), f"Tab {t}: pane {khac} vẫn hiện"
        if t in cho_du_lieu:
            expect(page.locator(cho_du_lieu[t])).not_to_contain_text("Đang tải", timeout=10000)
            assert page.locator(cho_du_lieu[t]).inner_text().strip() != ""
        else:
            expect(page.locator("#sellerShopName")).not_to_have_value("", timeout=10000)
        ghi.append(t)
    actual("Đã duyệt đủ tab: " + ", ".join(ghi))


def test_tc260_dong_modal_va_toast(page, login, api, actual):
    ghi = []

    def dong_mo_lai(ten, modal, mo_fn, sau_dong=None):
        sel = f"#{modal}"
        txt = []
        for lan in (1, 2):
            mo_fn()
            expect(page.locator(sel)).to_have_class(SHOW)
            expect(page.locator(sel)).not_to_contain_text("Đang tải", timeout=10000)
            txt.append(page.inner_text(sel))
            page.click(f"{sel} .modal-close")
            expect(page.locator(sel)).not_to_have_class(SHOW)
            if sau_dong:
                sau_dong()
        ghi.append(f"{ten}: đóng/mở OK")
        assert txt[0] == txt[1], f"{ten}: mở lại bị lẫn dữ liệu"

    # ---- chưa đăng nhập: modal Đăng nhập + toast + bấm ra ngoài ----
    page.goto("/")
    dong_mo_lai("Đăng nhập", "authModal", lambda: page.click("#hdrAuthBtn"))
    page.evaluate("showToast('Toast A'); showToast('Toast B')")
    t0 = time.time()
    expect(page.locator("#toast")).to_have_text("Toast B")
    expect(page.locator("#toast")).to_have_class(SHOW)
    expect(page.locator("#toast")).not_to_have_class(SHOW, timeout=5000)
    dt = time.time() - t0
    ghi.append(f"toast tự ẩn sau {dt:.1f}s")
    assert 2.0 <= dt <= 3.5, f"Toast phải tự ẩn ~2,5s, thực tế {dt:.1f}s"
    page.click("#hdrAuthBtn")
    page.mouse.click(5, 5)
    ghi.append(f"bấm ngoài modal: modal còn mở={'show' in (page.get_attribute('#authModal', 'class') or '')} (ghi nhận)")
    page.click("#authModal .modal-close")

    # ---- Customer ----
    khach = api("khach1")
    dat_gio(khach, [api("seller1")])
    dang_nhap_khach_ui(page, login)
    doi_gio(page, 1)
    dong_mo_lai("Hồ sơ", "profileModal", lambda: page.click("#hdrUserBtn"))
    dong_mo_lai("Chi tiết sản phẩm", "productDetailModal",
                lambda: page.locator("#userProductsGrid .product-card").first.click())
    dong_mo_lai("Lịch sử đơn", "orderHistoryModal", lambda: page.click("#hdrHistoryBtn"))

    def mo_hoa_don():
        page.click("#hdrHistoryBtn")
        page.locator("#orderHistoryContent button", has_text="Xem hóa đơn").first.click()
    dong_mo_lai("Hóa đơn", "invoiceModal", mo_hoa_don,
                sau_dong=lambda: page.click("#orderHistoryModal .modal-close"))

    def mo_checkout_lai():
        page.click('button[onclick="openCart()"]')
        page.click("#btnCheckoutTrigger")
    dong_mo_lai("Checkout", "checkoutModal", mo_checkout_lai,
                sau_dong=lambda: page.evaluate("closeCart()"))
    khach.post("/api/gio-hang/xoa-tat-ca")

    # ---- Seller ----
    dang_xuat_ui(page)
    vao_kenh_seller(page, login, "seller1")

    def mo_chi_tiet_don():
        page.click("#smenu-orders")
        expect(page.locator("#tblSellerOrdersBody")).not_to_contain_text("Đang tải", timeout=10000)
        page.locator("#tblSellerOrdersBody button", has_text="Xem chi tiết").first.click()
    dong_mo_lai("Chi tiết đơn (Seller)", "sellerOrderDetailModal", mo_chi_tiet_don)

    # ---- Quản lý ----
    dang_xuat_ui(page)
    vao_admin(page, login, "quanly1")
    dong_mo_lai("Danh mục", "categoryModal",
                lambda: page.click('button[onclick="openAddCategoryModal()"]'))

    def mo_reset_mk():
        page.click("#menu-users")
        expect(page.locator("#tblAdminUsersBody")).not_to_contain_text("Đang tải", timeout=10000)
        page.locator("#tblAdminUsersBody button", has_text="Cấp lại mật khẩu").first.click()
    dong_mo_lai("Cấp lại mật khẩu", "resetPasswordModal", mo_reset_mk)
    assert not page.is_visible("#resetPasswordResult"), "Mở lại không được còn mật khẩu cũ"
    actual("; ".join(ghi))


# ============================================================
# TS-52 — Quản lý sản phẩm của Seller (UI)
# ============================================================
def test_tc261_loc_san_pham_seller(page, login, api, actual):
    s1, khach = api("seller1"), api("khach1")
    sp = dam_bao_trang_thai_san_pham(api, s1, khach)
    loi_js = []
    page.on("pageerror", lambda e: loi_js.append(str(e)))

    act = lambda p: int(p.get("is_active") or 0)
    ton = lambda p: int(p["quantity"])
    nhom = {
        "all": lambda p: True,
        "in-stock": lambda p: ton(p) > 5,
        "low-stock": lambda p: 1 <= ton(p) <= 5,
        "out-of-stock": lambda p: ton(p) == 0,
    }

    def pill_ky_vong(p):
        if not act(p):
            return "Đang ẩn"
        if ton(p) == 0:
            return "Hết hàng"
        if ton(p) <= 5:
            return "Sắp hết"
        return "Đang bán"

    vao_kenh_seller(page, login, "seller1")
    page.click("#smenu-products")
    hang = page.locator("#tblSellerProductsBody tr")
    expect(page.locator("#tblSellerProductsBody")).not_to_contain_text("Đang tải", timeout=10000)
    ghi = []
    for gia_tri, dk in nhom.items():
        page.select_option("#spFilterStock", gia_tri)
        ky_vong = [p for p in sp if dk(p)]
        ghi.append(f"{gia_tri}: {hang.count()}/{len(ky_vong)} dòng")
        if ky_vong:
            assert hang.count() == len(ky_vong), f"{gia_tri}: sai số dòng (hàng bị nhân đôi?)"
            tonui = [digits(t) for t in page.locator("#tblSellerProductsBody tr td:nth-child(4)").all_inner_texts()]
            assert all(dk({"quantity": t}) for t in tonui)
        else:
            assert "Không tìm thấy kết quả" in page.inner_text("#tblSellerProductsBody")

    page.select_option("#spFilterStock", "all")
    pill_ui = {}
    for i in range(hang.count()):
        ten = hang.nth(i).locator("td:nth-child(2) div").first.inner_text().strip()
        o4 = hang.nth(i).locator("td:nth-child(5)")
        assert "Đã bán:" in o4.inner_text()
        pill_ui[ten] = o4.locator(".badge-status").inner_text().strip()
    for p in sp:
        assert pill_ui.get(p["name"]) == pill_ky_vong(p), f"Pill '{p['name']}' sai: {pill_ui.get(p['name'])}"

    kw = sp[0]["name"][:6]
    page.fill("#spSearchFilter", kw)
    ky_vong = [p for p in sp if kw.lower() in p["name"].lower()]
    assert hang.count() == len(ky_vong)
    page.fill("#spSearchFilter", "zzzzzzzz")
    assert "Không tìm thấy kết quả" in page.inner_text("#tblSellerProductsBody")
    page.fill("#spSearchFilter", "")
    for t in ("overview", "orders", "products", "gia", "products"):
        page.click(f"#smenu-{t}")

    dang_xuat_ui(page)
    shop = tao_shop_moi(api)
    vao_kenh_seller(page, login, shop["user"])
    page.click("#smenu-products")
    expect(page.locator("#tblSellerProductsBody")).to_contain_text("Chưa có sản phẩm nào", timeout=10000)
    actual("; ".join(ghi) + f"; lỗi JS={loi_js}")
    assert not loi_js, f"Console có lỗi JS: {loi_js}"


def test_tc262_form_tinh_gia_giam_gia(page, login, actual):
    vao_kenh_seller(page, login, "seller1")
    page.click("#smenu-products")
    mo_modal_them_sp_seller(page)
    ghi = []

    page.click('button[onclick="setDiscount(10)"]')
    expect(page.locator("#toast")).to_contain_text("Nhập giá gốc trước để giảm giá theo %", timeout=5000)

    page.fill("#prodOldPrice", "500000")
    expect(page.locator("#feeGocBox")).to_be_visible()
    fee = float(page.evaluate("currentCategoryFee"))
    phi = digits(page.inner_text("#feeGocPhi"))
    ghi.append(f"phí sàn danh mục mặc định={fee}%, phí trên giá gốc={phi}")
    assert phi == round(500000 * fee / 100)

    for pct in (5, 10, 20, 30):
        page.click(f'button[onclick="setDiscount({pct})"]')
        gia = int(page.input_value("#prodPrice"))
        assert gia == round(500000 * (1 - pct / 100)), f"-{pct}%: giá bán {gia}"
        assert digits(page.inner_text("#feeBreakThucNhan")) == gia - round(gia * fee / 100)
    gia_truoc = page.input_value("#prodPrice")
    page.fill("#prodDiscount", "100")
    ghi.append(f"% = 100: giá bán {gia_truoc} -> {page.input_value('#prodPrice')}")
    assert page.input_value("#prodPrice") == gia_truoc, "% ≥ 100 không được tự điền"

    # Đổi danh mục -> phí sàn đổi theo
    options = page.eval_on_selector_all("#prodCategory option",
                                        "els=>els.map(e=>({v:e.value, fee:parseFloat(e.dataset.fee||0)}))")
    khac = next((o for o in options if o["fee"] != fee), None)
    if khac:
        page.select_option("#prodCategory", khac["v"])
        nhan = page.inner_text("#feeGocLabel")
        ghi.append(f"đổi danh mục (phí {fee}%->{khac['fee']}%): nhãn='{nhan}'")
        assert f"({int(khac['fee']) if khac['fee'] == int(khac['fee']) else khac['fee']}%)" in nhan, \
            "Đổi danh mục phải cập nhật phí sàn"

    # Giá bán >= giá gốc
    page.fill("#prodPrice", "600000")
    cap_nhat_khi_go = page.is_visible("#feeBreakdownBox") and digits(page.inner_text("#feeBreakGiaBan")) == 600000
    ghi.append(f"gõ tay giá bán: khối Thực nhận tự cập nhật={cap_nhat_khi_go} (ghi nhận)")
    page.fill("#prodOldPrice", "")
    page.fill("#prodOldPrice", "500000")
    expect(page.locator("#feeBreakGiam")).to_contain_text("không hiện giảm giá")
    actual("; ".join(ghi))


def test_tc263_emoji_va_emoji_mac_dinh(page, login, api, actual):
    vao_kenh_seller(page, login, "seller1")
    page.click("#smenu-products")
    mo_modal_them_sp_seller(page)
    assert page.get_attribute("#prodEmoji", "maxlength") == "4"
    page.click('button[onclick="toggleEmojiPicker()"]')
    expect(page.locator("#emojiPicker")).to_be_visible()
    page.locator("#emojiPicker .emoji-grid span").first.click()
    chon = page.input_value("#prodEmoji")
    assert chon != "" and not page.is_visible("#emojiPicker"), "Chọn emoji xong bộ chọn phải đóng"
    page.click('button[onclick="toggleEmojiPicker()"]')
    expect(page.locator("#emojiPicker")).to_be_visible()
    page.click("#prodName")
    assert not page.is_visible("#emojiPicker"), "Bấm ra ngoài phải đóng bộ chọn"

    ten = f"SP emoji test {uuid.uuid4().hex[:6]}"
    page.fill("#prodEmoji", "")
    page.fill("#prodName", ten)
    page.fill("#prodPrice", "100000")
    page.fill("#prodShop", "Thương hiệu test")
    page.click('#adminProductModal button[type="submit"]')
    expect(page.locator("#toast")).to_contain_text("✅", timeout=8000)
    s1 = api("seller1")
    sp = next((p for p in lay_san_pham(s1) if p["name"] == ten), None)
    actual(f"Emoji chọn='{chon}'; sản phẩm tạo: {sp.get('emoji') if sp else 'KHÔNG TẠO ĐƯỢC'}")
    assert sp, "Sản phẩm không được tạo"
    assert sp["emoji"] == "📦", f"Emoji mặc định phải là 📦, thực tế {sp['emoji']!r}"
    assert any(p["name"] == ten and p.get("emoji") == "📦" for p in san_pham_cong_khai(api)), "Trang khách"
    an_san_pham(s1, sp["id"], 0)


def test_tc264_modal_them_sua_san_pham(page, login, api, actual):
    s1 = api("seller1")
    sp_list = lay_san_pham(s1)
    posts = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" and "/api/seller/san-pham" in r.url else None)
    vao_kenh_seller(page, login, "seller1")
    page.click("#smenu-products")
    expect(page.locator("#tblSellerProductsBody")).not_to_contain_text("Đang tải", timeout=10000)
    ghi = []

    mo_modal_them_sp_seller(page)
    expect(page.locator("#adminProductModalTitle")).to_have_text("➕ Thêm sản phẩm vào gian hàng")
    page.click("#adminProductModal .modal-close")

    dong = page.locator("#tblSellerProductsBody tr").first
    ten = dong.locator("td:nth-child(2) div").first.inner_text().strip()
    p = next(x for x in sp_list if x["name"] == ten)
    dong.locator("button", has_text="Sửa").click()
    expect(page.locator("#adminProductModalTitle")).to_have_text("✏️ Chỉnh sửa sản phẩm")
    expect(page.locator("#prodName")).to_have_value(p["name"])
    dm = page.eval_on_selector("#prodCategory", "s=>s.options[s.selectedIndex].text")
    ghi.append(f"Sửa '{p['name']}': danh mục chọn='{dm}' (đúng='{p.get('category_name')}')")
    assert dm == p.get("category_name")
    assert page.get_attribute("#prodStock", "readonly") is not None, "Tồn kho phải chỉ đọc"
    assert int(page.input_value("#prodStock")) == int(p["quantity"])
    page.click("#adminProductModal .modal-close")

    mo_modal_them_sp_seller(page)
    expect(page.locator("#adminProductModalTitle")).to_have_text("➕ Thêm sản phẩm vào gian hàng")
    con_du = {i: page.input_value(f"#{i}") for i in ("prodName", "prodPrice", "prodOldPrice", "prodEmoji", "prodDesc")}
    ghi.append(f"Thêm sau Sửa: ô còn dữ liệu cũ={ {k: v for k, v in con_du.items() if v} }; "
               f"'Nhà bán hàng'='{page.input_value('#prodShop')}' (ghi nhận)")
    assert not any(con_du.values()), f"Các ô phải trống: {con_du}"

    page.fill("#prodName", f"SP thieu thuong hieu {uuid.uuid4().hex[:6]}")
    page.fill("#prodPrice", "100000")
    page.fill("#prodShop", "")
    posts.clear()
    page.click('#adminProductModal button[type="submit"]')
    page.wait_for_timeout(800)
    ghi.append(f"Bỏ trống 'Nhà bán hàng': số request POST={len(posts)}, modal còn mở={page.is_visible('#adminProductModal')}")
    assert not posts and page.is_visible("#adminProductModal"), "Trình duyệt phải chặn lưu khi thiếu ô bắt buộc"
    actual("; ".join(ghi))


def test_tc265_gia_goc_bat_thuong(page, api, actual):
    s1 = api("seller1")
    ghi, ten_tao = [], {}
    for nhan, old in (("gia_goc_nho_hon", 400000), ("bo_trong_gia_goc", None)):
        ten = f"SP {nhan} {uuid.uuid4().hex[:6]}"
        ok, b, pid = tao_san_pham(s1, ten, 500000, 5, old_price=old)
        ghi.append(f"{nhan}: tạo được={ok}, msg='{b.get('message')}'")
        if ok:
            ten_tao[nhan] = (ten, pid)
    vao_trang_chu(page)
    for nhan, (ten, pid) in ten_tao.items():
        page.evaluate(f"openProductDetail({pid})")
        expect(page.locator("#productDetailContent")).not_to_contain_text("Đang tải", timeout=8000)
        co_badge = bool(re.search(r"-\d+%", page.inner_text("#productDetailContent")))
        page.click("#productDetailModal .modal-close")
        page.check("#chkOnSale")
        page.fill("#userSearchInput", ten)
        trong_loc = pid in ids_the(page)
        page.uncheck("#chkOnSale")
        page.fill("#userSearchInput", "")
        ghi.append(f"{nhan}: badge giảm giá={co_badge}, nằm trong lọc 'Đang giảm giá'={trong_loc}")
        assert not co_badge, f"{nhan}: không được hiện % giảm"
        assert not trong_loc, f"{nhan}: không được tính là đang giảm giá"
    for ten, pid in ten_tao.values():
        an_san_pham(s1, pid, 0)
    actual("; ".join(ghi))


# ============================================================
# TS-53 — Nhập hàng
# ============================================================
def test_tc266_loc_tab_nhap_hang(page, login, api, actual):
    s1, khach = api("seller1"), api("khach1")
    sp = dam_bao_trang_thai_san_pham(api, s1, khach)
    st, ls = s1.get("/api/seller/lich-su-nhap-hang")
    for _ in range(max(0, 2 - len(ls.get("data", [])))):
        s1.post(f"/api/seller/san-pham/{sp[0]['id']}/nhap-hang", {"so_luong": 1, "gia_nhap": 1000, "ghi_chu": "test"})
    ton = lambda p: int(p["quantity"])
    nhom = {"all": lambda p: True, "in-stock": lambda p: ton(p) > 5,
            "low-stock": lambda p: 1 <= ton(p) <= 5, "out-of-stock": lambda p: ton(p) == 0}

    vao_kenh_seller(page, login, "seller1")
    page.click("#smenu-nhaphang")
    expect(page.locator("#spNhapHangBody")).not_to_contain_text("Đang tải", timeout=10000)
    lich_su = lambda: page.locator("#tblLichSuNhapHangBody tr").count()
    expect(page.locator("#tblLichSuNhapHangBody")).not_to_contain_text("Đang tải", timeout=10000)
    n_ls = lich_su()
    assert n_ls >= 2
    hang = page.locator("#spNhapHangBody tr")
    ghi = []
    for gia_tri, dk in nhom.items():
        page.select_option("#nhFilterStock", gia_tri)
        ky_vong = [p for p in sp if dk(p)]
        ghi.append(f"{gia_tri}: {hang.count()}/{len(ky_vong)}, lịch sử={lich_su()}")
        if ky_vong:
            assert hang.count() == len(ky_vong)
        else:
            assert "Không tìm thấy kết quả" in page.inner_text("#spNhapHangBody")
        assert lich_su() == n_ls, "Lịch sử nhập hàng không được bị lọc theo"
    page.select_option("#nhFilterStock", "all")
    kw = sp[0]["name"][:6]
    page.fill("#nhSearchFilter", kw)
    assert hang.count() == len([p for p in sp if kw.lower() in p["name"].lower()])
    assert lich_su() == n_ls
    actual("; ".join(ghi))


def test_tc267_thanh_tien_nhap_hang(page, login, api, actual):
    s1 = api("seller1")
    p = chon_san_pham(s1, 1)
    st, r = s1.post(f"/api/seller/san-pham/{p['id']}/nhap-hang", {"so_luong": 1, "gia_nhap": 12345, "ghi_chu": "test"})
    assert r.get("status"), r
    st, ls = s1.get("/api/seller/lich-su-nhap-hang")
    gan_nhat = next((x["unit_cost"] for x in ls["data"] if x["product_id"] == p["id"]), None)

    vao_kenh_seller(page, login, "seller1")
    page.click("#smenu-nhaphang")
    expect(page.locator("#spNhapHangBody")).not_to_contain_text("Đang tải", timeout=10000)
    qty, gia, tom_tat = f"#nhQty{p['id']}", f"#nhGia{p['id']}", f"#nhTomTat{p['id']}"
    ghi = [f"mặc định: SL='{page.input_value(qty)}', giá='{page.input_value(gia)}' (giá nhập gần nhất={gan_nhat})"]
    assert page.input_value(qty) == "10"
    assert float(page.input_value(gia)) == float(gan_nhat), "Giá nhập mặc định = giá nhập gần nhất"

    page.fill(qty, "20")
    page.fill(gia, "300000")
    assert digits(page.inner_text(tom_tat)) == 6000000, "Thành tiền = 20 × 300.000"
    page.fill(gia, "")
    assert "Nhập giá & số lượng để xem thành tiền" in page.inner_text(tom_tat)
    page.fill(gia, "300000")
    page.fill(qty, "")
    assert "Nhập giá & số lượng để xem thành tiền" in page.inner_text(tom_tat)
    page.fill(qty, "10")
    page.fill(gia, str(int(float(p["price"])) * 2))
    dong = page.locator("#spNhapHangBody tr").filter(has=page.locator(f"#nhQty{p['id']}"))
    noi_dung = dong.inner_text().lower()
    ghi.append(f"giá nhập > giá bán: '{page.inner_text(tom_tat).strip()}'")
    assert not re.search(r"lợi nhuận|lãi|lỗ", noi_dung), "Không còn hiển thị lợi nhuận/lãi/lỗ"
    actual("; ".join(ghi))


def test_tc268_khach_thay_ton_kho_moi(page, api, actual):
    s1, khach = api("seller1"), api("khach1")
    pid, ten = tao_sp_het_hang(s1, khach)
    vao_trang_chu(page)
    page.evaluate(f"openProductDetail({pid})")
    expect(page.locator("#productDetailContent")).to_contain_text("Hết hàng", timeout=8000)

    st, r = s1.post(f"/api/seller/san-pham/{pid}/nhap-hang", {"so_luong": 10, "gia_nhap": 50000, "ghi_chu": "test"})
    assert r.get("status"), f"Setup: nhập hàng lỗi: {r}"
    page.reload()
    page.wait_for_function("document.querySelectorAll('#userProductsGrid .product-card').length>0", timeout=10000)
    page.evaluate(f"openProductDetail({pid})")
    expect(page.locator("#productDetailContent")).to_contain_text("Còn lại: 10", timeout=8000)

    khach.post("/api/gio-hang/xoa-tat-ca")
    st, g = khach.post("/api/gio-hang/them", {"UserId": khach.ma_user, "ProductId": pid, "Quantity": 10, "UnitPrice": 100000})
    st, gio = khach.get(f"/api/gio-hang/{khach.ma_user}")
    sl = sum(int(i.get("Quantity", i.get("quantity", 0))) for i in gio.get("data", [])
             if int(i.get("ProductId", i.get("product_id", 0))) == pid)
    actual(f"Sau nhập 10: UI 'Còn lại: 10'; thêm 10 vào giỏ: status={g.get('status')}, SL giỏ={sl}")
    khach.post("/api/gio-hang/xoa-tat-ca")
    an_san_pham(s1, pid, 0)
    assert g.get("status") is True and sl == 10


# ============================================================
# TS-54 — Chống XSS trang gian hàng
# ============================================================
def test_tc269_chong_xss_trang_shop(page, login, api, actual):
    s1 = api("seller1")
    st, goc = s1.get("/api/seller/trang-shop")
    goc = goc["data"]
    dialogs, ghi, sp_tao = [], [], []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))

    # sản phẩm có tên/URL ảnh độc hại (API) - đối chiếu hiển thị ở bước dưới
    for url in (None, "javascript:alert(1)", "data:text/html,<script>alert(1)</script>"):
        ten = "<img src=x onerror=alert(1)>" if url is None else f"XSS anh {uuid.uuid4().hex[:6]}"
        ok, b, pid = tao_san_pham(s1, ten, 100000, 5, image_url=url)
        ghi.append(f"SP url={str(url)[:20]!r}: tạo={ok}, msg='{b.get('message')}'")
        if ok:
            sp_tao.append(pid)

    payloads = ["<script>alert(1)</script>", "<SCRIPT>alert(1)</SCRIPT>", "<img src=x onerror=alert(1)>",
                'x" onerror =alert(1)', "javascript:alert(1)", "onclick=alert(1)", "ONERROR=alert(1)"]
    try:
        vao_kenh_seller(page, login, "seller1")
        for pl in payloads:
            page.click("#smenu-shop")
            expect(page.locator("#sellerShopName")).not_to_have_value("", timeout=10000)
            page.fill("#sellerShopName", pl)
            page.fill("#sellerShopDesc", pl)
            page.click('button[onclick="sellerLuuTrangShop()"]')
            page.wait_for_timeout(800)
            toast = page.locator("#toast").inner_text()
            page.reload()
            page.wait_for_selector("#sellerDashboard", state="visible", timeout=15000)
            expect(page.locator("#sellerOverviewContent")).not_to_contain_text("Đang tải", timeout=10000)
            page.click("#smenu-products")
            expect(page.locator("#tblSellerProductsBody")).not_to_contain_text("Đang tải", timeout=10000)
            ghi.append(f"{pl[:22]!r}: '{toast}'")
            assert page.locator("img[src='x']").count() == 0, f"{pl!r}: thẻ <img src=x> bị chèn vào DOM"
            assert page.locator("[onerror]").count() == 0, f"{pl!r}: có thuộc tính onerror trong DOM"
            assert page.locator("#sellerOverviewContent script").count() == 0
        srcs = page.eval_on_selector_all("img", "els=>els.map(e=>e.getAttribute('src')||'')")
        assert not [s for s in srcs if s.lower().startswith(("javascript:", "data:"))], \
            "URL ảnh javascript:/data: không được render"
        actual(f"Hộp thoại alert xuất hiện: {dialogs}; " + "; ".join(ghi))
        assert not dialogs, f"Có script chạy (alert): {dialogs}"
    finally:
        s1.put("/api/seller/trang-shop", {"ten_shop": goc.get("store_name"),
                                          "gioi_thieu": goc.get("description"),
                                          "tham_nien": goc.get("tham_nien")})
        for pid in sp_tao:
            an_san_pham(s1, pid, 0)