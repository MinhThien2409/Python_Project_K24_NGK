"""
Test TC-149 -> TC-169 (TS-27 .. TS-32): cập nhật SP (SP không tồn tại), ẩn/hiện SP,
thêm giỏ, xem giỏ, cập nhật số lượng giỏ, xóa item giỏ.

Chạy (cùng conftest.py ghi kết quả vào Excel):
    pytest tests/ui/test_149_169.py --base-url http://127.0.0.1:5000 -v

Yêu cầu: Flask chạy, DB đã seed. Tài khoản: seller1, seller2, khach1, khach2, khach4 (mật khẩu 123456).
Lưu ý: mỗi test giỏ hàng tự đăng ký 1 khách mới (kh<hex>) nên chạy song song (-n) vẫn an toàn;
các tài khoản này nằm lại trong DB. SP/đơn test tự dọn sau khi chạy.
"""
import uuid

import pytest
from playwright.sync_api import expect

PW = "123456"


# ============================================================
# HELPER
# ============================================================
def _json(resp):
    try:
        return resp.json()
    except Exception:
        return {}


def _fmt(resp, j):
    return f"HTTP {resp.status}, status={j.get('status')}, message='{j.get('message')}'"


def _tien(v):
    return f"{int(round(float(v))):,}".replace(",", ".") + "đ"


def _uniq(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _g(d, *keys, default=None):
    for k in keys:
        if d.get(k) is not None:
            return d[k]
    return default


def _cat_id(ctx, tu_khoa=None):
    ds = _json(ctx.get("/api/categories")).get("data") or []
    if tu_khoa:
        for c in ds:
            if tu_khoa in (c.get("category_name") or "").lower():
                return c["category_id"], c["category_name"]
        return None, None
    return (ds[0]["category_id"], ds[0]["category_name"]) if ds else (None, None)


# ---------- Seller ----------
def _tao(ctx, ten, gia=500000, sl=10, cat=None):
    r = ctx.post("/api/seller/san-pham", data={
        "name": ten, "description": "SP test tự động", "price": gia,
        "quantity": sl, "category_id": cat, "emoji": "📦"})
    return r, _json(r)


def _sua(ctx, pid, **body):
    r = ctx.put(f"/api/seller/san-pham/{pid}", data=body)
    return r, _json(r)


def _an_hien(ctx, pid, active):
    r = ctx.put(f"/api/seller/san-pham/{pid}/an-hien", data={"is_active": active})
    return r, _json(r)


def _ds(ctx):
    return _json(ctx.get("/api/seller/san-pham")).get("data") or []


def _lay(ctx, pid):
    return next((p for p in _ds(ctx) if p["id"] == pid), None)


def _public(ctx, **params):
    return _json(ctx.get("/api/products", params=params)).get("data") or []


# ---------- Giỏ hàng ----------
def _them(ctx, pid, qty, price=500000):
    r = ctx.post("/api/gio-hang/them", data={"ProductId": pid, "Quantity": qty, "UnitPrice": price})
    return r, _json(r)


def _cap_nhat(ctx, pid, qty):
    r = ctx.post("/api/gio-hang/cap-nhat", data={"ProductId": pid, "Quantity": qty})
    return r, _json(r)


def _xoa(ctx, pid):
    r = ctx.post("/api/gio-hang/xoa", data={"ProductId": pid})
    return r, _json(r)


def _gio(ctx, uid):
    r = ctx.get(f"/api/gio-hang/{uid}")
    return r, _json(r)


def _items(ctx, uid):
    d = _gio(ctx, uid)[1].get("data")
    return d if isinstance(d, list) else []


def _item(ctx, uid, pid):
    return next((i for i in _items(ctx, uid)
                 if int(_g(i, "ProductId", "product_id", default=-1)) == pid), None)


def _qty(it):
    return int(_g(it, "Quantity", "quantity", default=0)) if it else None


def _tong_gio(ctx, uid):
    return sum(int(_g(i, "Quantity", "quantity", default=0)) *
               float(_g(i, "UnitPrice", "unit_price", "price", default=0)) for i in _items(ctx, uid))


# ---------- UI ----------
def _dang_nhap_ui(page, login, user):
    """Đăng nhập UI bằng id cố định (không dùng fixture login: get_by_text khớp nhầm 'Chưa đăng nhập')."""
    page.goto("/")
    page.click("#hdrAuthBtn")
    page.fill("#loginUsername", user)
    page.fill("#loginPass", PW)
    with page.expect_navigation():          # handleLogin gọi location.reload()
        page.click("#formLogin button[type='submit']")
    page.wait_for_selector("#hdrUserBtn", state="visible")
    page.wait_for_load_state("networkidle")


def _mo_gio(page, co_item=True):
    """Mở giỏ sau khi giỏ đã tải xong (openCart chỉ vẽ lại từ biến cart hiện có)."""
    if co_item:
        expect(page.locator("#cartBadge")).not_to_have_text("0")
    page.locator(".hdr-btn", has_text="Giỏ hàng").click()


def _tim_ui(page, ten):
    page.fill("#userSearchInput", ten)
    page.wait_for_timeout(300)


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture
def api_as(playwright, base_url):
    ctxs = []

    def _make(user=None, pw=PW):
        ctx = playwright.request.new_context(base_url=base_url)
        ctxs.append(ctx)
        data = None
        if user:
            r = ctx.post("/api/dang-nhap", data={"tendangnhap": user, "mat_khau": pw})
            j = _json(r)
            if not j.get("status"):
                pytest.fail(f"Không đăng nhập được '{user}' ({j.get('message')}).")
            data = j.get("data")
        return ctx, data

    yield _make
    for c in ctxs:
        c.dispose()


@pytest.fixture
def don_dep(api_as):
    """Sau test: ẩn SP test + xóa SP test khỏi giỏ + hủy đơn test."""
    sp, gio, don = [], [], []
    yield {"sp": sp, "gio": gio, "don": don}
    for ctx, pid in gio:
        try:
            ctx.post("/api/gio-hang/xoa", data={"ProductId": pid})
        except Exception:
            pass
    for ctx, oid in don:
        try:
            ctx.put(f"/api/don-hang/{oid}/huy")
        except Exception:
            pass
    for ctx, pid in sp:
        try:
            ctx.put(f"/api/seller/san-pham/{pid}/an-hien", data={"is_active": 0})
        except Exception:
            pass


@pytest.fixture
def tao_sp(api_as, don_dep):
    """tao_sp(sl=10, gia=500000, seller='seller1') -> dict SP active mới tạo."""
    def _make(sl=10, gia=500000, seller="seller1"):
        ctx, _ = api_as(seller)
        cat, _ = _cat_id(ctx, "gia dụng")
        if cat is None:
            cat, _ = _cat_id(ctx)
        ten = _uniq("Nồi cơm")
        r, j = _tao(ctx, ten, gia, sl, cat)
        assert j.get("status"), f"Không tạo được SP nền: {_fmt(r, j)}"
        pid = j["product_id"]
        don_dep["sp"].append((ctx, pid))
        return {"id": pid, "name": ten, "price": gia, "ctx": ctx, "cat": cat}
    return _make


def _dang_ky_khach(api_as):
    """Tạo khách hàng mới (mỗi test 1 user) để test chạy song song không dẫm giỏ của nhau."""
    anon, _ = api_as()
    user = "kh" + uuid.uuid4().hex[:8]
    sdt = "09" + str(uuid.uuid4().int % 10**8).zfill(8)
    r = anon.post("/api/dang-ky", data={"ten_user": "Khách Test", "tendangnhap": user,
                                         "sdt": sdt, "mat_khau": PW})
    j = _json(r)
    assert j.get("status"), f"Không tạo được khách test: {_fmt(r, j)}"
    ctx, data = api_as(user)
    return {"ctx": ctx, "uid": data["ma_user"], "user": user}


@pytest.fixture
def khach_moi(api_as):
    return lambda: _dang_ky_khach(api_as)


@pytest.fixture
def khach1(api_as, don_dep):
    """Giữ tên 'khach1' cho gọn, nhưng thực chất là khách mới tạo riêng cho test."""
    k = _dang_ky_khach(api_as)
    k["dep"] = don_dep["gio"]
    return k


# ============================================================
# TS-27: CẬP NHẬT SP — product không tồn tại
# ============================================================
def test_tc149_cap_nhat_san_pham_khong_ton_tai(api_as, actual):
    ctx, _ = api_as("seller1")
    cat, _ = _cat_id(ctx)
    r, j = _sua(ctx, 99999, name=_uniq("SP_ma"), price=100000, quantity=1, category_id=cat)
    msg = j.get("message") or ""
    actual(f"{_fmt(r, j)}; nói rõ 'không tồn tại' = {'không tồn tại' in msg.lower()}")
    assert r.status < 500
    assert j.get("status") is False


# ============================================================
# TS-28: ẨN / HIỆN SẢN PHẨM
# ============================================================
def test_tc150_seller_an_san_pham_cua_shop(page, api_as, tao_sp, actual):
    sp = tao_sp()
    anon, _ = api_as()
    truoc = sp["id"] in [p["id"] for p in _public(anon, q=sp["name"])]
    r, j = _an_hien(sp["ctx"], sp["id"], 0)
    trong_db = _lay(sp["ctx"], sp["id"])
    sau_public = sp["id"] in [p["id"] for p in _public(anon)]

    page.goto("/")
    page.wait_for_selector("#userProductsGrid .product-card")
    _tim_ui(page, sp["name"])
    ui_co = page.locator("#userProductsGrid .product-card", has_text=sp["name"]).count() > 0
    actual(f"Trước ẩn: công khai={truoc}; ẩn: {_fmt(r, j)}; is_active={trong_db['is_active']}; "
           f"sau ẩn: trong DS công khai={sau_public}, hiện trên UI={ui_co}")
    assert truoc and j.get("status")
    assert trong_db["is_active"] is False
    assert not sau_public and not ui_co


def test_tc151_seller_hien_san_pham_cua_shop(page, api_as, tao_sp, actual):
    sp = tao_sp()
    anon, _ = api_as()
    _an_hien(sp["ctx"], sp["id"], 0)
    dang_an = sp["id"] not in [p["id"] for p in _public(anon, q=sp["name"])]
    r, j = _an_hien(sp["ctx"], sp["id"], 1)
    trong_db = _lay(sp["ctx"], sp["id"])
    sau_public = sp["id"] in [p["id"] for p in _public(anon, q=sp["name"])]

    page.goto("/")
    page.wait_for_selector("#userProductsGrid .product-card")
    _tim_ui(page, sp["name"])
    ui_co = page.locator("#userProductsGrid .product-card", has_text=sp["name"]).count() > 0
    actual(f"Đang ẩn: không công khai={dang_an}; hiện: {_fmt(r, j)}; is_active={trong_db['is_active']}; "
           f"công khai lại={sau_public}, UI={ui_co}")
    assert dang_an and j.get("status")
    assert trong_db["is_active"] is True
    assert sau_public and ui_co


@pytest.mark.parametrize("hanh_dong", [pytest.param("an", id="an"), pytest.param("hien", id="hien")])
def test_tc152_an_hien_san_pham_shop_khac(api_as, tao_sp, actual, hanh_dong):
    sp2 = tao_sp(seller="seller2")
    c2 = sp2["ctx"]
    c1, _ = api_as("seller1")
    if hanh_dong == "hien":
        _an_hien(c2, sp2["id"], 0)          # SP đang ẩn, seller1 thử bật lại
    truoc = _lay(c2, sp2["id"])["is_active"]
    r, j = _an_hien(c1, sp2["id"], 0 if hanh_dong == "an" else 1)
    sau = _lay(c2, sp2["id"])["is_active"]
    actual(f"seller1 {hanh_dong} SP #{sp2['id']} của seller2: {_fmt(r, j)}; is_active {truoc}→{sau}")
    assert r.status < 500 and j.get("status") is False
    assert truoc == sau


@pytest.mark.parametrize("active", [pytest.param(0, id="an"), pytest.param(1, id="hien")])
def test_tc153_an_hien_san_pham_khong_ton_tai(api_as, actual, active):
    ctx, _ = api_as("seller1")
    r, j = _an_hien(ctx, 99999, active)
    msg = j.get("message") or ""
    actual(f"is_active={active}: {_fmt(r, j)}; nói rõ 'không tồn tại' = {'không tồn tại' in msg.lower()}")
    assert r.status < 500
    assert j.get("status") is False


# ============================================================
# TS-29: THÊM VÀO GIỎ
# ============================================================
def test_tc154_them_san_pham_hop_le_vao_gio(page, login, api_as, tao_sp, khach1, actual):
    sp = tao_sp(sl=10, gia=500000)
    khach1["dep"].append((khach1["ctx"], sp["id"]))

    _dang_nhap_ui(page, login, khach1["user"])
    page.wait_for_selector("#userProductsGrid .product-card")
    _tim_ui(page, sp["name"])
    page.locator("#userProductsGrid .product-card", has_text=sp["name"]).first.click()
    expect(page.locator("#productDetailModal.show")).to_be_visible()
    page.fill("#detailQtyInput", "2")
    page.get_by_role("button", name="Thêm vào giỏ hàng").click()
    _mo_gio(page)
    expect(page.locator("#cartItemsList")).to_contain_text(sp["name"])

    it = _item(khach1["ctx"], khach1["uid"], sp["id"])
    gia_gio = float(_g(it, "UnitPrice", "unit_price", "price", default=-1)) if it else None
    actual(f"Giỏ DB: số lượng={_qty(it)}, giá={gia_gio} (giá DB={sp['price']}); "
           f"UI giỏ hiển thị '{sp['name']}'")
    assert it and _qty(it) == 2
    assert gia_gio == sp["price"]


def test_tc155_them_gio_khi_chua_dang_nhap(page, api_as, tao_sp, actual):
    sp = tao_sp()
    anon, _ = api_as()
    r, j = _them(anon, sp["id"], 1)

    page.goto("/")
    page.wait_for_selector("#userProductsGrid .product-card")
    page.locator("#userProductsGrid .add-cart-btn").first.click()
    hien_modal = page.locator("#authModal.show").count() > 0
    actual(f"API không session: {_fmt(r, j)}; UI bấm '+ Giỏ hàng': mở form đăng nhập={hien_modal}")
    assert r.status == 403 and j.get("status") is False
    assert hien_modal


@pytest.mark.parametrize("sl", [pytest.param(0, id="sl_0"), pytest.param(-1, id="sl_am")])
def test_tc156_so_luong_khong_hop_le(khach1, tao_sp, actual, sl):
    sp = tao_sp()
    khach1["dep"].append((khach1["ctx"], sp["id"]))
    r, j = _them(khach1["ctx"], sp["id"], sl)
    it = _item(khach1["ctx"], khach1["uid"], sp["id"])
    msg = j.get("message") or ""
    actual(f"Số lượng={sl}: {_fmt(r, j)}; có trong giỏ={bool(it)}; "
           f"nói rõ 'lớn hơn 0' = {'lớn hơn 0' in msg}")
    assert r.status < 500 and j.get("status") is False
    assert it is None


def test_tc157_so_luong_vuot_ton_kho(khach1, tao_sp, actual):
    sp = tao_sp(sl=10)
    khach1["dep"].append((khach1["ctx"], sp["id"]))
    r, j = _them(khach1["ctx"], sp["id"], 11)
    it = _item(khach1["ctx"], khach1["uid"], sp["id"])
    actual(f"Tồn 10, thêm 11: {_fmt(r, j)}; có trong giỏ={bool(it)}")
    assert r.status < 500 and j.get("status") is False
    assert it is None


def test_tc158_san_pham_inactive(khach1, tao_sp, actual):
    sp = tao_sp()
    khach1["dep"].append((khach1["ctx"], sp["id"]))
    _an_hien(sp["ctx"], sp["id"], 0)
    r, j = _them(khach1["ctx"], sp["id"], 1)
    it = _item(khach1["ctx"], khach1["uid"], sp["id"])
    actual(f"SP inactive: {_fmt(r, j)}; có trong giỏ={bool(it)}")
    assert r.status < 500 and j.get("status") is False
    assert it is None


def test_tc159_gia_client_khac_gia_db(khach1, tao_sp, don_dep, actual):
    sp = tao_sp(sl=10, gia=500000)
    ctx, uid = khach1["ctx"], khach1["uid"]
    khach1["dep"].append((ctx, sp["id"]))

    # (1) thêm giỏ với giá client = 1000
    r, j = _them(ctx, sp["id"], 1, price=1000)
    it = _item(ctx, uid, sp["id"])
    gia_gio = float(_g(it, "UnitPrice", "unit_price", "price", default=-1)) if it else None
    gio_ok = (it is None) or gia_gio == sp["price"]

    # (2) đặt hàng với UnitPrice/TotalPrice client = 1000
    ro = ctx.post("/api/don-hang/dat-hang", data={
        "ReceiverName": "Khách Test", "ReceiverPhone": "0901111116",
        "ShippingAddress": "88 Võ Văn Ngân, TP. Thủ Đức", "PaymentMethod": "COD",
        "ShippingFee": 25000,
        "Items": [{"ProductId": sp["id"], "ProductName": sp["name"], "Emoji": "📦",
                   "Quantity": 1, "UnitPrice": 1000, "TotalPrice": 1000}]})
    jo = _json(ro)
    don_ok, ghi_don = True, f"đặt hàng: {_fmt(ro, jo)}"
    if jo.get("status"):
        ls = _json(ctx.get(f"/api/don-hang/cua-toi/{uid}")).get("data") or []
        don_tao = [o for o in ls if any(i.get("ProductName") == sp["name"] for i in o.get("Items") or [])]
        for o in don_tao:
            don_dep["don"].append((ctx, o["OrderId"]))
        if not don_tao:
            don_ok = False
            ghi_don += "; không tìm thấy đơn vừa tạo"
        else:
            o = don_tao[0]
            gia_item = float(o["Items"][0].get("UnitPrice") or 0)
            don_ok = gia_item == sp["price"] and float(o.get("SubTotal") or 0) == sp["price"]
            ghi_don += f"; đơn #{o['OrderId']}: giá dòng={gia_item}, SubTotal={o.get('SubTotal')}"
    actual(f"Giá DB={sp['price']}, client gửi 1000. Thêm giỏ: {_fmt(r, j)}, giá trong giỏ={gia_gio}; {ghi_don}")
    assert r.status < 500 and ro.status < 500
    assert gio_ok, "Giỏ hàng nhận giá do client gửi"
    assert don_ok, "Đơn hàng được tạo theo giá client"


# ============================================================
# TS-30: XEM GIỎ HÀNG
# ============================================================
def test_tc160_customer_xem_gio_cua_minh(page, login, tao_sp, khach1, actual):
    sp = tao_sp(gia=500000)
    ctx, uid = khach1["ctx"], khach1["uid"]
    khach1["dep"].append((ctx, sp["id"]))
    _them(ctx, sp["id"], 2)

    r, j = _gio(ctx, uid)
    items = j.get("data") or []
    tong = _tong_gio(ctx, uid)

    _dang_nhap_ui(page, login, khach1["user"])
    _mo_gio(page)
    expect(page.locator("#cartItemsList")).to_contain_text(sp["name"])
    tong_ui = page.locator("#cartTotalText").inner_text().strip()
    actual(f"{_fmt(r, j)}; {len(items)} item; tổng DB={_tien(tong)}, tổng UI={tong_ui}")
    assert r.status == 200 and j.get("status")
    assert _qty(_item(ctx, uid, sp["id"])) == 2
    assert tong_ui == _tien(tong)


def test_tc161_customer_xem_gio_user_khac(api_as, tao_sp, khach1, khach_moi, don_dep, actual):
    k2 = khach_moi()
    c2, uid2 = k2["ctx"], k2["uid"]
    sp = tao_sp()
    don_dep["gio"].append((c2, sp["id"]))
    _them(c2, sp["id"], 1)

    r, j = _gio(khach1["ctx"], uid2)
    data = j.get("data") if isinstance(j.get("data"), list) else []
    ten_lo = [i for i in data if int(_g(i, "ProductId", "product_id", default=-1)) == sp["id"]]
    actual(f"khach1 xem giỏ user #{uid2}: {_fmt(r, j)}; số item trả về={len(data)}; lộ item của khach2={bool(ten_lo)}")
    assert r.status < 500
    assert not ten_lo, "Lộ giỏ hàng của khách khác"
    assert r.status == 403 or j.get("status") is False


def test_tc162_chua_dang_nhap_xem_gio(api_as, actual):
    anon, _ = api_as()
    r, j = _gio(anon, 1)
    actual(_fmt(r, j))
    assert r.status == 403 and j.get("status") is False


def test_tc163_xem_gio_chua_co_item(page, login, khach_moi, actual):
    k = khach_moi()                              # khách mới => giỏ rỗng, không đụng dữ liệu seed
    r, j = _gio(k["ctx"], k["uid"])
    items = j.get("data") if isinstance(j.get("data"), list) else []

    loi = []
    page.on("pageerror", lambda e: loi.append(str(e)))
    _dang_nhap_ui(page, login, k["user"])
    _mo_gio(page, co_item=False)
    text = page.locator("#cartItemsList").inner_text()
    tong_ui = page.locator("#cartTotalText").inner_text().strip()
    actual(f"{_fmt(r, j)}; {len(items)} item; UI: '{' '.join(text.split())}', tổng={tong_ui}, lỗi JS={loi or 'không'}")
    assert r.status == 200 and not items
    assert "trống" in text.lower() and tong_ui == "0đ"
    assert not loi


# ============================================================
# TS-31: CẬP NHẬT SỐ LƯỢNG TRONG GIỎ
# ============================================================
def _gio_san(khach1, tao_sp, sl_ton=10, sl_gio=2, gia=500000):
    sp = tao_sp(sl=sl_ton, gia=gia)
    khach1["dep"].append((khach1["ctx"], sp["id"]))
    r, j = _them(khach1["ctx"], sp["id"], sl_gio, price=gia)
    assert j.get("status"), f"Không thêm được SP nền vào giỏ: {_fmt(r, j)}"
    return sp


def test_tc164_cap_nhat_so_luong_hop_le(khach1, tao_sp, actual):
    sp = _gio_san(khach1, tao_sp, gia=500000)
    ctx, uid = khach1["ctx"], khach1["uid"]
    tong_truoc = _tong_gio(ctx, uid)
    r, j = _cap_nhat(ctx, sp["id"], 3)
    it = _item(ctx, uid, sp["id"])
    tong_sau = _tong_gio(ctx, uid)
    actual(f"{_fmt(r, j)}; số lượng={_qty(it)}; tổng {_tien(tong_truoc)}→{_tien(tong_sau)}")
    assert j.get("status") and _qty(it) == 3
    assert tong_sau - tong_truoc == sp["price"], "Tổng tiền không được tính lại đúng (+1 sản phẩm)"


def test_tc165_cap_nhat_vuot_ton_kho(khach1, tao_sp, actual):
    sp = _gio_san(khach1, tao_sp, sl_ton=10, sl_gio=2)
    ctx, uid = khach1["ctx"], khach1["uid"]
    r, j = _cap_nhat(ctx, sp["id"], 11)
    it = _item(ctx, uid, sp["id"])
    actual(f"Tồn 10, đổi sang 11: {_fmt(r, j)}; số lượng giỏ sau={_qty(it)}")
    assert r.status < 500 and j.get("status") is False
    assert _qty(it) == 2


def test_tc166_quantity_bang_0(khach1, tao_sp, actual):
    sp = _gio_san(khach1, tao_sp, sl_gio=2)
    ctx, uid = khach1["ctx"], khach1["uid"]
    r, j = _cap_nhat(ctx, sp["id"], 0)
    it = _item(ctx, uid, sp["id"])
    actual(f"Quantity=0: {_fmt(r, j)}; item sau: {'đã xóa' if it is None else 'còn, SL=' + str(_qty(it))}")
    assert r.status < 500
    if j.get("status"):
        assert it is None, "Báo thành công nhưng item vẫn còn"     # đặc tả: xóa item
    else:
        assert _qty(it) == 2, "Từ chối nhưng dữ liệu giỏ bị đổi"  # đặc tả: từ chối


def test_tc167_quantity_am(khach1, tao_sp, actual):
    sp = _gio_san(khach1, tao_sp, sl_gio=2)
    ctx, uid = khach1["ctx"], khach1["uid"]
    r, j = _cap_nhat(ctx, sp["id"], -1)
    it = _item(ctx, uid, sp["id"])
    msg = j.get("message") or ""
    actual(f"Quantity=-1: {_fmt(r, j)}; số lượng giỏ sau={_qty(it)}; nói rõ 'lớn hơn 0' = {'lớn hơn 0' in msg}")
    assert r.status < 500 and j.get("status") is False
    assert _qty(it) == 2


def test_tc168_cap_nhat_san_pham_inactive(khach1, tao_sp, actual):
    sp = _gio_san(khach1, tao_sp, sl_gio=2)
    ctx, uid = khach1["ctx"], khach1["uid"]
    _an_hien(sp["ctx"], sp["id"], 0)
    r, j = _cap_nhat(ctx, sp["id"], 3)
    it = _item(ctx, uid, sp["id"])
    msg = (j.get("message") or "").lower()
    canh_bao = any(k in msg for k in ("không khả dụng", "đã ẩn", "ngừng", "hết hàng"))
    actual(f"SP inactive trong giỏ, đổi sang 3: {_fmt(r, j)}; số lượng giỏ sau={_qty(it)}; có cảnh báo={canh_bao}")
    assert r.status < 500
    assert j.get("status") is False or canh_bao, "Cập nhật thành công im lặng trên SP đã ẩn"


# ============================================================
# TS-32: XÓA ITEM KHỎI GIỎ
# ============================================================
def test_tc169_xoa_item_ton_tai(page, login, khach1, tao_sp, actual):
    sp = _gio_san(khach1, tao_sp, sl_gio=2)
    ctx, uid = khach1["ctx"], khach1["uid"]

    _dang_nhap_ui(page, login, khach1["user"])
    _mo_gio(page)
    dong = page.locator("#cartItemsList > div", has_text=sp["name"]).first
    expect(dong).to_be_visible()
    dong.locator("button[title='Xóa sản phẩm']").click()
    page.wait_for_timeout(800)

    con_lai = _item(ctx, uid, sp["id"])
    tong_db = _tong_gio(ctx, uid)
    tong_ui = page.locator("#cartSubtotalText").inner_text().strip()
    con_tren_ui = page.locator("#cartItemsList", has_text=sp["name"]).count() > 0
    actual(f"Sau xóa: còn trong giỏ DB={bool(con_lai)}, còn trên UI={con_tren_ui}; "
           f"tổng DB={_tien(tong_db)}, tổng UI={tong_ui}")
    assert con_lai is None and not con_tren_ui
    assert tong_ui == _tien(tong_db)