"""
Test TC-128 -> TC-148 (TS-24 .. TS-27): duyệt/tìm kiếm SP, chi tiết SP,
Seller tạo SP, Seller cập nhật SP.

Chạy (cùng conftest.py ghi kết quả vào Excel):
    pytest test_tc128_148.py --base-url http://127.0.0.1:5000 -v
    pytest test_tc128_148.py --base-url http://127.0.0.1:5000 --headed   # xem trình duyệt

Yêu cầu: Flask đang chạy, DB đã seed (seed_demo_mysql.sql).
Tài khoản dùng: seller1/seller2/seller3/khach1 (mật khẩu 123456).
TC-143 cần thêm tài khoản `seller_nostore` (role Seller, KHÔNG có gian hàng).
Đóng file Excel trước khi chạy để conftest ghi được kết quả.
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
    """32000000 -> '32.000.000đ' (giống toLocaleString('vi-VN') ở FE)."""
    return f"{int(round(float(v))):,}".replace(",", ".") + "đ"


def _uniq(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _cat_id(ctx, tu_khoa=None):
    """Trả (category_id, category_name). tu_khoa: tìm tên chứa chuỗi (lowercase)."""
    ds = _json(ctx.get("/api/categories")).get("data") or []
    if tu_khoa:
        for c in ds:
            if tu_khoa in (c.get("category_name") or "").lower():
                return c["category_id"], c["category_name"]
        return None, None
    return (ds[0]["category_id"], ds[0]["category_name"]) if ds else (None, None)


def _tao(ctx, ten, gia=500000, sl=10, cat=None, **extra):
    body = {"name": ten, "description": "SP test tự động", "price": gia,
            "quantity": sl, "category_id": cat, "emoji": "📦"}
    body.update(extra)
    r = ctx.post("/api/seller/san-pham", data=body)
    return r, _json(r)


def _sua(ctx, pid, **body):
    r = ctx.put(f"/api/seller/san-pham/{pid}", data=body)
    return r, _json(r)


def _ds(ctx):
    return _json(ctx.get("/api/seller/san-pham")).get("data") or []


def _lay(ctx, pid):
    return next((p for p in _ds(ctx) if p["id"] == pid), None)


def _public(ctx, **params):
    return _json(ctx.get("/api/products", params=params)).get("data") or []


# ---------- UI helpers ----------
def _mo_trang(page):
    page.goto("/")
    page.wait_for_selector("#userProductsGrid .product-card")


def _ui_names(page):
    """Gom tên SP đang hiển thị, đi qua mọi trang phân trang."""
    page.wait_for_timeout(300)
    names = []
    while True:
        names += page.locator("#userProductsGrid .card-title").all_inner_texts()
        nxt = page.locator("#paginationWrap button", has_text="›")
        if nxt.count() == 0 or nxt.first.is_disabled():
            break
        nxt.first.click()
        page.wait_for_timeout(200)
    return [n.strip() for n in names]


def _tim_ui(page, keyword=None, cat_name=None):
    if cat_name:
        page.select_option("#searchCategorySelect", value=cat_name)
    if keyword is not None:
        page.fill("#userSearchInput", keyword)
        page.press("#userSearchInput", "Enter")
    page.wait_for_timeout(300)


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture
def api_as(playwright, base_url):
    """api_as('seller1') -> (APIRequestContext đã login, data user). api_as() -> chưa đăng nhập."""
    ctxs = []

    def _make(user=None, pw=PW):
        ctx = playwright.request.new_context(base_url=base_url)
        ctxs.append(ctx)
        data = None
        if user:
            r = ctx.post("/api/dang-nhap", data={"tendangnhap": user, "mat_khau": pw})
            j = _json(r)
            if not j.get("status"):
                pytest.fail(f"Không đăng nhập được '{user}' ({j.get('message')}). "
                            f"Kiểm tra seed/tài khoản.")
            data = j.get("data")
        return ctx, data

    yield _make
    for c in ctxs:
        c.dispose()


@pytest.fixture
def don_dep(api_as):
    """Sau test: ẩn các SP test đã tạo để không lẫn vào trang công khai."""
    ds = []
    yield ds
    for ctx, pid in ds:
        try:
            ctx.put(f"/api/seller/san-pham/{pid}/an-hien", data={"is_active": 0})
        except Exception:
            pass


@pytest.fixture
def sp_seller1(api_as, don_dep):
    ctx, _ = api_as("seller1")
    cat, _ = _cat_id(ctx, "gia dụng")
    if cat is None:
        cat, _ = _cat_id(ctx)
    ten = _uniq("SP_test")
    r, j = _tao(ctx, ten, 500000, 10, cat)
    assert j.get("status"), f"Không tạo được SP nền: {_fmt(r, j)}"
    pid = j["product_id"]
    don_dep.append((ctx, pid))
    return {"ctx": ctx, "id": pid, "name": ten, "cat": cat}


# ============================================================
# TS-24: DUYỆT & TÌM KIẾM SẢN PHẨM
# ============================================================
def test_tc128_duyet_danh_sach_khong_filter(page, api_as, actual):
    anon, _ = api_as()
    r = anon.get("/api/products")
    j = _json(r)
    ds = j.get("data") or []

    # id sản phẩm đang ẩn của cả 3 shop
    an = []
    for u in ("seller1", "seller2", "seller3"):
        ctx, _ = api_as(u)
        an += [p["id"] for p in _ds(ctx) if not p.get("is_active")]
    ids_public = {p["id"] for p in ds}

    _mo_trang(page)
    names_ui = _ui_names(page)
    cards = page.locator("#userProductsGrid .product-card")
    thieu = []
    for i in range(min(cards.count(), 12)):
        c = cards.nth(i)
        if not c.locator(".card-title").inner_text().strip():
            thieu.append(f"card{i}: thiếu tên")
        if "đ" not in c.locator(".card-price").inner_text():
            thieu.append(f"card{i}: thiếu giá")
        if not (c.locator(".card-img img").count() or c.locator(".card-img").inner_text().strip()):
            thieu.append(f"card{i}: thiếu ảnh/emoji")

    actual(f"API /api/products: HTTP {r.status}, {len(ds)} SP; UI hiển thị {len(names_ui)} SP; "
           f"SP ẩn (shop1-3): {len(an)}; card thiếu dữ liệu: {thieu or 'không'}")
    assert r.status == 200 and ds
    assert all(p.get("is_active") for p in ds), "Có SP inactive trong danh sách công khai"
    assert not (set(an) & ids_public), "SP ẩn xuất hiện ở danh sách công khai"
    assert sorted(names_ui) == sorted(p["name"] for p in ds), "UI không khớp API"
    assert not thieu


def test_tc129_tim_theo_keyword(page, actual):
    _mo_trang(page)
    _tim_ui(page, keyword="áo")
    names = _ui_names(page)
    _tim_ui(page, keyword="ÁO")
    names_hoa = _ui_names(page)
    actual(f"Keyword 'áo': {len(names)} kết quả {names}; keyword 'ÁO': {len(names_hoa)} kết quả")
    assert names, "Không có kết quả nào cho 'áo'"
    assert all("áo" in n.lower() for n in names), "Có SP không chứa từ khóa"
    assert sorted(names) == sorted(names_hoa), "Tìm kiếm phân biệt hoa/thường"


def test_tc130_loc_theo_category(page, api_as, actual):
    anon, _ = api_as()
    cat_id, cat_name = _cat_id(anon, "gia dụng")
    assert cat_name, "Không có danh mục 'gia dụng' trong DB"
    mong_doi = [p["name"] for p in _public(anon) if p["category_name"] == cat_name]

    _mo_trang(page)
    _tim_ui(page, cat_name=cat_name)
    names = _ui_names(page)
    actual(f"Category '{cat_name}': UI {len(names)} SP, API {len(mong_doi)} SP")
    assert names and sorted(names) == sorted(mong_doi)


def test_tc131_ket_hop_keyword_va_category(page, api_as, actual):
    anon, _ = api_as()
    _, cat_name = _cat_id(anon, "gia dụng")
    assert cat_name, "Không có danh mục 'gia dụng' trong DB"
    mong_doi = [p["name"] for p in _public(anon)
                if p["category_name"] == cat_name and "nồi" in p["name"].lower()]

    _mo_trang(page)
    _tim_ui(page, keyword="nồi", cat_name=cat_name)
    names = _ui_names(page)
    actual(f"Keyword 'nồi' + '{cat_name}': UI {names}, kỳ vọng {mong_doi}")
    assert names and sorted(names) == sorted(mong_doi)


def test_tc132_sp_inactive_khong_hien_cong_khai(page, api_as, don_dep, actual):
    ctx, _ = api_as("seller1")
    anon, _ = api_as()
    cat, _ = _cat_id(ctx)
    ten = _uniq("SP_an")
    r, j = _tao(ctx, ten, 100000, 5, cat)
    assert j.get("status"), _fmt(r, j)
    pid = j["product_id"]
    don_dep.append((ctx, pid))

    truoc = [p["id"] for p in _public(anon, q=ten)]
    ra, ja = ctx.put(f"/api/seller/san-pham/{pid}/an-hien", data={"is_active": 0}), None
    ja = _json(ra)
    sau_ds = [p["id"] for p in _public(anon)]
    sau_q = [p["id"] for p in _public(anon, q=ten)]

    _mo_trang(page)
    _tim_ui(page, keyword=ten)
    ui = _ui_names(page)

    ct = _json(anon.get(f"/api/products/{pid}"))
    actual(f"Trước ẩn: tìm thấy={pid in truoc}; ẩn: {_fmt(ra, ja)}; sau ẩn: trong DS={pid in sau_ds}, "
           f"trong tìm kiếm={pid in sau_q}, UI={ten in ui}; "
           f"GET chi tiết SP ẩn: status={ct.get('status')}")
    assert pid in truoc, "SP active phải tìm thấy trước khi ẩn"
    assert ja.get("status")
    assert pid not in sau_ds and pid not in sau_q
    assert ten not in ui


def test_tc133_category_khong_phu_hop(page, api_as, actual):
    anon, _ = api_as()
    _, cat_name = _cat_id(anon, "thời trang")
    assert cat_name, "Không có danh mục 'thời trang' trong DB"
    assert any("nồi" in p["name"].lower() for p in _public(anon)), "Thiếu SP 'nồi' để test"

    loi = []
    page.on("pageerror", lambda e: loi.append(str(e)))
    _mo_trang(page)
    _tim_ui(page, keyword="nồi", cat_name=cat_name)
    grid = page.locator("#userProductsGrid")
    actual(f"Keyword 'nồi' + '{cat_name}': số card={page.locator('.product-card').count()}, "
           f"nội dung='{grid.inner_text().strip()}', lỗi JS={loi or 'không'}")
    assert page.locator("#userProductsGrid .product-card").count() == 0
    expect(grid).to_contain_text("Không tìm thấy sản phẩm")
    assert not loi


# ============================================================
# TS-25: CHI TIẾT SẢN PHẨM
# ============================================================
def _mo_chi_tiet_ui(page, ten):
    _mo_trang(page)
    page.fill("#userSearchInput", ten)
    page.wait_for_timeout(300)
    page.locator("#userProductsGrid .product-card", has_text=ten).first.click()
    expect(page.locator("#productDetailModal.show")).to_be_visible()
    page.wait_for_selector("#productDetailContent h2")
    return " ".join(page.locator("#productDetailContent").inner_text().split())


def test_tc134_xem_chi_tiet_sp_ton_tai(page, api_as, actual):
    anon, _ = api_as()
    sp = _json(anon.get("/api/products/1")).get("data")
    assert sp, "Không có sản phẩm ID 1"
    text = _mo_chi_tiet_ui(page, sp["name"])
    actual(f"Chi tiết SP #1 '{sp['name']}': hiển thị tên={sp['name'] in text}, "
           f"giá={_tien(sp['price']) in text}")
    assert sp["name"] in text
    assert _tien(sp["price"]) in text


def test_tc135_xem_sp_khong_ton_tai(api_as, actual):
    anon, _ = api_as()
    r = anon.get("/api/products/99999")
    j = _json(r)
    actual(_fmt(r, j))
    assert r.status < 500
    assert r.status == 404 or j.get("status") is False


def test_tc136_thieu_id_san_pham(api_as, actual):
    anon, _ = api_as()
    r1 = anon.get("/api/products/")      # không truyền ID
    r0 = anon.get("/api/products/0")     # ID rỗng/0
    j0 = _json(r0)
    actual(f"GET /api/products/: HTTP {r1.status}; GET /api/products/0: {_fmt(r0, j0)}")
    assert r1.status in (404, 405) or _json(r1).get("status") is False
    assert r1.status < 500 and r0.status < 500
    assert j0.get("status") is False and "ID" in (j0.get("message") or "")


def _db_row(pid):
    """Đọc thẳng DB để đối chiếu; trả None nếu không kết nối được."""
    try:
        from back_end.DBconnection import DBconnection
        conn = DBconnection.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT p.ProductName, p.Price, p.Quantity, p.Description, c.CategoryName, s.StoreName "
            "FROM Products p LEFT JOIN Categories c ON p.CategoryId=c.CategoryId "
            "LEFT JOIN Stores s ON p.StoreId=s.StoreId WHERE p.ProductId = ?", (pid,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return tuple(row) if row else None
    except Exception:
        return None


def test_tc137_kiem_tra_du_lieu_chi_tiet(page, api_as, actual):
    anon, _ = api_as()
    sp = _json(anon.get("/api/products/1")).get("data")
    assert sp, "Không có sản phẩm ID 1"
    text = _mo_chi_tiet_ui(page, sp["name"])

    thieu = []
    if sp["name"] not in text: thieu.append("tên")
    if _tien(sp["price"]) not in text: thieu.append("giá")
    if f"Còn lại: {sp['quantity']}" not in text: thieu.append("tồn kho")
    if sp["description"] and " ".join(sp["description"].split()) not in text: thieu.append("mô tả")
    if sp["category_name"] not in text: thieu.append("danh mục")
    if sp["shop"] not in text: thieu.append("shop")

    db = _db_row(1)
    if db:
        khop_db = (db[0] == sp["name"] and float(db[1]) == sp["price"] and int(db[2]) == sp["quantity"]
                   and (db[3] or "") == sp["description"] and (db[4] or "") == sp["category_name"]
                   and (db[5] or "") == sp["shop"])
        ghi_db = f"đối chiếu DB: {'khớp' if khop_db else 'LỆCH ' + str(db)}"
    else:
        khop_db, ghi_db = True, "không kết nối được DB (chỉ đối chiếu API↔UI)"
    actual(f"UI thiếu/lệch: {thieu or 'không'}; {ghi_db}")
    assert not thieu
    assert khop_db


# ============================================================
# TS-26: SELLER TẠO SẢN PHẨM
# ============================================================
def test_tc138_seller_tao_san_pham_hop_le(api_as, don_dep, actual):
    ctx, user = api_as("seller1")
    cat, cat_name = _cat_id(ctx, "gia dụng")
    if cat is None:
        cat, cat_name = _cat_id(ctx)
    store_id = _json(ctx.get("/api/seller/trang-shop")).get("data", {}).get("store_id")
    ten = _uniq("Nồi cơm 1.8L")
    r, j = _tao(ctx, ten, 500000, 10, cat)
    pid = j.get("product_id")
    if pid:
        don_dep.append((ctx, pid))
    sp = _lay(ctx, pid) if pid else None
    actual(f"{_fmt(r, j)}, product_id={pid}, store_id={sp and sp['store_id']} (store seller1={store_id}), "
           f"có trong danh sách shop={bool(sp)}")
    assert j.get("status") and pid
    assert sp and sp["store_id"] == store_id and sp["quantity"] == 10 and sp["price"] == 500000
    assert sp["category_id"] == cat


@pytest.mark.parametrize("ten", [pytest.param("", id="rong"), pytest.param("   ", id="khoang_trang")])
def test_tc139_ten_san_pham_rong(api_as, actual, ten):
    ctx, _ = api_as("seller1")
    cat, _ = _cat_id(ctx)
    truoc = len(_ds(ctx))
    r, j = _tao(ctx, ten, 500000, 10, cat)
    sau = len(_ds(ctx))
    actual(f"Tên='{ten}': {_fmt(r, j)}; số SP shop {truoc}→{sau}")
    assert j.get("status") is False and "tên" in (j.get("message") or "").lower()
    assert truoc == sau


@pytest.mark.parametrize("gia", [pytest.param(0, id="gia_0"), pytest.param(-1000, id="gia_am")])
def test_tc140_gia_khong_hop_le(api_as, actual, gia):
    ctx, _ = api_as("seller1")
    cat, _ = _cat_id(ctx)
    truoc = len(_ds(ctx))
    r, j = _tao(ctx, _uniq("SP_gia"), gia, 10, cat)
    sau = len(_ds(ctx))
    actual(f"Giá={gia}: {_fmt(r, j)}; số SP shop {truoc}→{sau}")
    assert j.get("status") is False and "lớn hơn 0" in (j.get("message") or "")
    assert truoc == sau


def test_tc141_so_luong_am(api_as, actual):
    ctx, _ = api_as("seller1")
    cat, _ = _cat_id(ctx)
    truoc = len(_ds(ctx))
    r, j = _tao(ctx, _uniq("SP_sl"), 500000, -5, cat)
    sau = len(_ds(ctx))
    actual(f"Số lượng=-5: {_fmt(r, j)}; số SP shop {truoc}→{sau}")
    assert j.get("status") is False and "âm" in (j.get("message") or "")
    assert truoc == sau


def test_tc142_category_store_khong_hop_le(api_as, don_dep, actual):
    ctx, _ = api_as("seller1")
    store_cua_toi = _json(ctx.get("/api/seller/trang-shop")).get("data", {}).get("store_id")
    cat_ok, _ = _cat_id(ctx)

    # (1) category + store đều không tồn tại -> phải bị từ chối
    truoc = len(_ds(ctx))
    r, j = _tao(ctx, _uniq("SP_cat"), 500000, 10, 99999, store_id=99999)
    sau = len(_ds(ctx))
    ghi = [f"category=99999,store=99999: {_fmt(r, j)}; số SP {truoc}→{sau}"]

    # (2) chỉ store_id sai: backend lấy store từ session -> kiểm tra không bị gán sang store 99999
    r2, j2 = _tao(ctx, _uniq("SP_store"), 500000, 10, cat_ok, store_id=99999)
    ghi_store = ""
    ok_store = True
    if j2.get("status"):
        don_dep.append((ctx, j2["product_id"]))
        sp2 = _lay(ctx, j2["product_id"])
        ok_store = bool(sp2) and sp2["store_id"] == store_cua_toi
        ghi_store = (f"store_id=99999 bị BỎ QUA, SP tạo trong store #{sp2 and sp2['store_id']} "
                     f"(store seller1 = #{store_cua_toi})")
    else:
        ghi_store = f"store_id=99999: {_fmt(r2, j2)}"
    actual("; ".join(ghi + [ghi_store]))
    assert r.status < 500 and r2.status < 500
    assert j.get("status") is False and truoc == sau
    assert ok_store, "SP bị gán sai store"


@pytest.mark.parametrize("user", [
    pytest.param("khach1", id="customer"),
    pytest.param("seller_nostore", id="seller_chua_co_store"),
    pytest.param(None, id="chua_dang_nhap"),
])
def test_tc143_actor_khong_phai_seller(api_as, actual, user):
    ctx, _ = api_as(user)
    ten = _uniq("SP_actor")
    r, j = _tao(ctx, ten, 500000, 10, 1)
    anon, _ = api_as()
    tao_ra = [p for p in _public(anon, q=ten)]
    actual(f"{user or 'không session'}: {_fmt(r, j)}; SP được tạo={bool(tao_ra)}")
    assert r.status == 403 and j.get("status") is False
    assert not tao_ra


# ============================================================
# TS-27: SELLER CẬP NHẬT SẢN PHẨM
# ============================================================
def test_tc144_seller_cap_nhat_san_pham_cua_shop(sp_seller1, actual):
    ctx, pid, cat = sp_seller1["ctx"], sp_seller1["id"], sp_seller1["cat"]
    truoc = _lay(ctx, pid)
    ten_moi = _uniq("Nồi cơm 2L")
    r, j = _sua(ctx, pid, name=ten_moi, price=550000, quantity=20, category_id=cat,
                description="Mô tả mới")
    sau = _lay(ctx, pid)
    actual(f"{_fmt(r, j)}; tên '{truoc['name']}'→'{sau['name']}', giá {truoc['price']}→{sau['price']}, "
           f"tồn kho {truoc['quantity']}→{sau['quantity']} (gửi quantity=20), đã bán {sau['sold']}")
    assert j.get("status")
    assert sau["name"] == ten_moi and sau["price"] == 550000
    assert sau["quantity"] == truoc["quantity"], "Tồn kho bị đổi qua cập nhật SP (Phase 4)"
    assert sau["sold"] == truoc["sold"]


def test_tc144_seller_cap_nhat_dung_payload_giao_dien(sp_seller1, actual):
    """FE (handleSaveProduct seller, chế độ sửa) KHÔNG gửi price -> kiểm tra BE có chấp nhận không."""
    ctx, pid, cat = sp_seller1["ctx"], sp_seller1["id"], sp_seller1["cat"]
    truoc = _lay(ctx, pid)
    ten_moi = _uniq("Ten_moi_UI")
    r, j = _sua(ctx, pid, name=ten_moi, emoji="📦", description="Sửa từ UI", category_id=cat)
    sau = _lay(ctx, pid)
    actual(f"Payload UI (name/emoji/description/category_id, không có price): {_fmt(r, j)}; "
           f"tên sau={sau['name']}, giá {truoc['price']}→{sau['price']}")
    assert j.get("status"), "BE từ chối payload sửa của UI (thiếu price)"
    assert sau["name"] == ten_moi and sau["price"] == truoc["price"]


def test_tc145_seller_sua_san_pham_shop_khac(api_as, don_dep, actual):
    c1, _ = api_as("seller1")
    c2, _ = api_as("seller2")
    cat, _ = _cat_id(c2)
    r, j = _tao(c2, _uniq("SP_seller2"), 300000, 5, cat)
    pid = j["product_id"]
    don_dep.append((c2, pid))
    truoc = _lay(c2, pid)

    r, j = _sua(c1, pid, name=_uniq("HACK"), price=1000, quantity=999, category_id=cat)
    sau = _lay(c2, pid)
    actual(f"seller1 sửa SP #{pid} của seller2: {_fmt(r, j)}; "
           f"seller2 thấy: tên '{sau['name']}', giá {sau['price']}, tồn {sau['quantity']}")
    assert r.status < 500 and j.get("status") is False
    assert (sau["name"], sau["price"], sau["quantity"]) == (truoc["name"], truoc["price"], truoc["quantity"])


@pytest.mark.parametrize("ten", [pytest.param("", id="rong"), pytest.param("   ", id="khoang_trang")])
def test_tc146_cap_nhat_ten_rong(sp_seller1, actual, ten):
    ctx, pid, cat = sp_seller1["ctx"], sp_seller1["id"], sp_seller1["cat"]
    truoc = _lay(ctx, pid)
    r, j = _sua(ctx, pid, name=ten, price=truoc["price"], category_id=cat)
    sau = _lay(ctx, pid)
    actual(f"Tên='{ten}': {_fmt(r, j)}; tên sau='{sau['name']}'")
    assert j.get("status") is False
    assert sau["name"] == truoc["name"]


@pytest.mark.parametrize("gia", [pytest.param(0, id="gia_0"), pytest.param(-1, id="gia_am")])
def test_tc147_cap_nhat_gia_khong_hop_le(sp_seller1, actual, gia):
    ctx, pid, cat = sp_seller1["ctx"], sp_seller1["id"], sp_seller1["cat"]
    truoc = _lay(ctx, pid)
    r, j = _sua(ctx, pid, name=truoc["name"], price=gia, category_id=cat)
    sau = _lay(ctx, pid)
    actual(f"Giá={gia}: {_fmt(r, j)}; giá {truoc['price']}→{sau['price']}")
    assert j.get("status") is False
    assert sau["price"] == truoc["price"]


def test_tc148_cap_nhat_so_luong_am(sp_seller1, actual):
    ctx, pid, cat = sp_seller1["ctx"], sp_seller1["id"], sp_seller1["cat"]
    truoc = _lay(ctx, pid)
    r, j = _sua(ctx, pid, name=truoc["name"], price=truoc["price"], quantity=-5, category_id=cat)
    sau = _lay(ctx, pid)
    actual(f"Số lượng=-5: {_fmt(r, j)}; tồn kho {truoc['quantity']}→{sau['quantity']}")
    assert r.status < 500
    # Chấp nhận: từ chối (status=False) HOẶC bỏ qua trường số lượng; tồn kho phải giữ nguyên
    assert sau["quantity"] == truoc["quantity"]
    assert sau["quantity"] >= 0