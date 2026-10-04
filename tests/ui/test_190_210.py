"""
TC-190 -> TC-210: lịch sử/hóa đơn đơn hàng, nhập hàng, lịch sử nhập hàng, cập nhật giá bán.

Nguyên tắc dữ liệu:
- Các case của Seller (nhập hàng, đổi giá) KHÔNG đụng sản phẩm seed: mỗi test tự tạo 1 sản phẩm mới
  (tên ngẫu nhiên, tồn kho 0) cho seller1/seller2 bằng /api/seller/san-pham, và tự ẨN sản phẩm đó khi
  test xong (is_active=0) để không làm bẩn trang công khai.
- Case "chưa có đơn" dùng khách hàng MỚI (khach4 trong seed thực ra có đơn #4).
- Case chỉ đọc dùng khach1/khach2/seller1/seller2 của seed.
- TC-203 cần tài khoản seller_nostore (Seller chưa có gian hàng). Seed KHÔNG có, hãy tạo trong DB trước
  (Accounts Role_Id=3 nhưng không có dòng Stores); nếu không test sẽ Fail kèm ghi chú.
"""
import re
import uuid
from types import SimpleNamespace

import pytest
from playwright.sync_api import expect

PWD = "123456"
KHACH1_ID, KHACH2_ID = 6, 7


# ====================================================================== fixtures
@pytest.fixture
def login(page):
    """Ghi đè fixture login của conftest trong file này: bấm thẳng #hdrAuthBtn và chờ modal mở
    (get_by_text("Đăng nhập").first có thể khớp chữ "Chưa đăng nhập" ở topbar)."""
    def _login(username, password):
        page.goto("/")
        page.wait_for_function("typeof openAuthModal === 'function'")
        page.locator("#hdrAuthBtn").click()
        expect(page.locator("#authModal")).to_have_class(re.compile("show"))
        page.fill("#loginUsername", username)
        page.fill("#loginPass", password)
        page.click("#formLogin button[type='submit']")

    return _login


@pytest.fixture
def api_as(playwright, base_url):
    """api_as('seller1') -> APIRequestContext đã đăng nhập; api_as() -> chưa đăng nhập."""
    ctxs = []

    def make(user=None, pwd=PWD):
        ctx = playwright.request.new_context(base_url=base_url)
        ctxs.append(ctx)
        if user:
            r = ctx.post("/api/dang-nhap", data={"tendangnhap": user, "mat_khau": pwd})
            assert r.json().get("status") is True, f"Đăng nhập API {user} thất bại: {r.text()}"
        return ctx

    yield make
    for c in ctxs:
        c.dispose()


@pytest.fixture
def khach_moi(playwright, base_url):
    """Khách hàng mới tinh (chưa có giỏ/đơn): .username, .uid, .api"""
    ctxs = []

    def make():
        api = playwright.request.new_context(base_url=base_url)
        ctxs.append(api)
        username = f"tc_{uuid.uuid4().hex[:8]}"
        r = api.post("/api/dang-ky", data={"ten_user": "Khách Test Tự Động", "tendangnhap": username,
                                           "sdt": "0901234567", "mat_khau": PWD})
        assert r.json().get("status") is True, r.text()
        j = api.post("/api/dang-nhap", data={"tendangnhap": username, "mat_khau": PWD}).json()
        assert j.get("status") is True
        return SimpleNamespace(api=api, username=username, uid=j["data"]["ma_user"])

    yield make
    for c in ctxs:
        c.dispose()


@pytest.fixture
def tao_san_pham(api_as):
    """tao_san_pham(seller_ctx, gia=500000) -> product_id của sản phẩm mới (tồn 0). Tự ẩn khi xong test."""
    da_tao = []

    def make(seller, gia=500000):
        ten = f"SP_TC_{uuid.uuid4().hex[:8]}"
        r = seller.post("/api/seller/san-pham", data={
            "name": ten, "emoji": "📦", "description": "sản phẩm test tự động",
            "category_id": 1, "price": gia, "old_price": None, "quantity": 0})
        assert r.json().get("status") is True, f"Không tạo được sản phẩm test: {r.text()}"
        ds = seller.get("/api/seller/san-pham").json()["data"]
        pid = next(p["id"] for p in ds if p["name"] == ten)
        da_tao.append((seller, pid))
        return pid

    yield make
    for seller, pid in da_tao:
        try:
            seller.put(f"/api/seller/san-pham/{pid}/an-hien", data={"is_active": 0})
        except Exception:
            pass


# ====================================================================== helpers
def sp_cong_khai(anon, pid):
    """Thông tin sản phẩm công khai (không cần đăng nhập)."""
    return anon.get(f"/api/products/{pid}").json()["data"]


def ton_kho(anon, pid):
    return int(sp_cong_khai(anon, pid)["quantity"])


def gia(anon, pid):
    return float(sp_cong_khai(anon, pid)["price"])


def lich_su(seller):
    j = seller.get("/api/seller/lich-su-nhap-hang").json()
    return j.get("data") or []


def nhap(seller, pid, so_luong, gia_nhap=None, ghi_chu=None):
    r = seller.post(f"/api/seller/san-pham/{pid}/nhap-hang",
                    data={"so_luong": so_luong, "gia_nhap": gia_nhap, "ghi_chu": ghi_chu})
    return r.status, r.json()


def doi_gia(seller, pid, kieu, gia_tri):
    """kieu='gia_goc' (Phase 4, như giao diện) hoặc 'gia_moi' (legacy)."""
    if kieu == "gia_goc":
        payload = {"gia_goc": gia_tri, "giam_gia": False}
    else:
        payload = {"gia_moi": gia_tri}
    r = seller.put(f"/api/seller/san-pham/{pid}/gia", data=payload)
    return r.status, r.json()


def vn(n):
    """Định dạng tiền giống toLocaleString('vi-VN') trong main.js: 32925000 -> '32.925.000'."""
    return f"{int(round(float(n))):,}".replace(",", ".")


def don_dau_tien(ctx, uid):
    ds = ctx.get(f"/api/don-hang/cua-toi/{uid}").json().get("data") or []
    assert ds, f"User {uid} chưa có đơn nào trong DB (cần có sẵn để chạy test này)"
    return ds[0]


# =====================================================================
# TC-190  User không có đơn xem lịch sử   (TS-35)
# =====================================================================
def test_tc190_user_khong_co_don(page, login, khach_moi, actual):
    loi_js, loi_5xx = [], []
    page.on("pageerror", lambda e: loi_js.append(str(e)))
    page.on("response", lambda r: loi_5xx.append(r.url) if r.status >= 500 else None)

    c = khach_moi()
    login(c.username, PWD)
    expect(page.locator("#hdrHistoryBtn")).to_be_visible()
    page.locator("#hdrHistoryBtn").click()

    noi_dung = page.locator("#orderHistoryContent")
    expect(noi_dung).to_contain_text("Bạn chưa có đơn hàng nào")
    so_the = noi_dung.locator("span", has_text=re.compile(r"^Đơn #\d+$")).count()
    actual(f"Thông báo hiển thị='{noi_dung.inner_text().strip()[:60]}'; số đơn hiển thị={so_the}; "
           f"lỗi JS={loi_js}; lỗi 5xx={loi_5xx}")
    assert so_the == 0
    assert loi_js == [] and loi_5xx == []


# =====================================================================
# TC-191  Chủ đơn xem hóa đơn   (TS-36)
# =====================================================================
def test_tc191_chu_don_xem_hoa_don(page, login, base_url, actual):
    login("khach1", PWD)
    expect(page.locator("#hdrHistoryBtn")).to_be_visible()

    ds = page.request.get(f"{base_url}/api/don-hang/cua-toi/{KHACH1_ID}").json().get("data") or []
    assert ds, "khach1 chưa có đơn nào trong DB"
    oid = int(ds[0]["OrderId"])
    d = page.request.get(f"{base_url}/api/don-hang/hoa-don/{oid}").json()["data"]
    items = d.get("Items") or d.get("items") or []

    page.locator("#hdrHistoryBtn").click()
    the = page.locator("#orderHistoryContent > div", has_text=re.compile(rf"Đơn #{oid}\b"))
    the.get_by_role("button", name=re.compile("Xem hóa đơn")).click()
    expect(page.locator("#invoiceModal")).to_have_class(re.compile("show"))
    text = re.sub(r"\s+", " ", page.locator("#invoiceContent").inner_text())

    thieu = []
    mong_doi = [f"#{oid}", str(d["Status"]), str(d["ReceiverName"]), str(d["ReceiverPhone"]),
                str(d["ShippingAddress"]), str(d["PaymentMethod"]),
                vn(d["SubTotal"]) + "đ", vn(d["ShippingFee"]) + "đ", vn(d["TotalAmount"]) + "đ"]
    for it in items:
        mong_doi += [str(it["ProductName"]), f"× {it['Quantity']}", vn(it["TotalPrice"]) + "đ"]
    for m in mong_doi:
        if m not in text:
            thieu.append(m)
    actual(f"Hóa đơn đơn #{oid}: thiếu trên giao diện={thieu or 'không'}")
    assert thieu == [], f"Hóa đơn thiếu thông tin: {thieu}"


# =====================================================================
# TC-192  Xem đơn không tồn tại   (TS-36)
# =====================================================================
def test_tc192_xem_hoa_don_khong_ton_tai(api_as, actual):
    r = api_as("khach1").get("/api/don-hang/hoa-don/99999")
    j = r.json()
    actual(f"HTTP {r.status}, status={j.get('status')}, message='{j.get('message')}'")
    assert r.status < 500
    assert j["status"] is False
    assert not j.get("data")


# =====================================================================
# TC-193  Xem hóa đơn của user khác   (TS-36)
# =====================================================================
def test_tc193_xem_hoa_don_user_khac(api_as, actual):
    oid_khach2 = int(don_dau_tien(api_as("khach2"), KHACH2_ID)["OrderId"])
    r = api_as("khach1").get(f"/api/don-hang/hoa-don/{oid_khach2}")
    j = r.json()
    actual(f"khach1 xem đơn #{oid_khach2} của khach2: HTTP {r.status}, status={j.get('status')}, "
           f"message='{j.get('message')}', có dữ liệu={bool(j.get('data'))}")
    assert r.status == 403
    assert j["status"] is False
    assert not j.get("data")


# =====================================================================
# TC-194  Chưa đăng nhập xem hóa đơn   (TS-36)
# =====================================================================
def test_tc194_xem_hoa_don_chua_dang_nhap(api_as, actual):
    r = api_as().get("/api/don-hang/hoa-don/1")
    j = r.json()
    actual(f"HTTP {r.status}, status={j.get('status')}, message='{j.get('message')}'")
    assert r.status in (401, 403)
    assert j["status"] is False
    assert not j.get("data")


# =====================================================================
# TC-195  Nhập hàng hợp lệ + giá vốn bình quân gia quyền   (TS-37)
# =====================================================================
def test_tc195_nhap_hang_hop_le(api_as, tao_san_pham, actual):
    s1, anon = api_as("seller1"), api_as()
    pid = tao_san_pham(s1)
    # Lần nhập đầu để có "tồn cũ × giá vốn cũ": 10 cái @ 100.000
    code0, j0 = nhap(s1, pid, 10, 100000)
    assert j0["status"] is True, j0

    kho_truoc = ton_kho(anon, pid)
    so_ban_ghi_truoc = len([h for h in lich_su(s1) if h["product_id"] == pid])

    code, j = nhap(s1, pid, 20, 300000, "nhập test TC-195")
    kho_sau = ton_kho(anon, pid)
    ban_ghi = [h for h in lich_su(s1) if h["product_id"] == pid]
    moi = ban_ghi[0] if ban_ghi else {}

    # Giá vốn bình quân gia quyền (Phase 4): chỉ đối chiếu được nếu API sản phẩm trả trường giá vốn
    sp = next(p for p in s1.get("/api/seller/san-pham").json()["data"] if p["id"] == pid)
    truong_von = [k for k in sp if re.search(r"cost|von|vốn", k, re.I)]
    mong_doi_von = (10 * 100000 + 20 * 300000) / 30
    ghi_chu_von = "API không trả trường giá vốn bình quân nên chưa đối chiếu được"
    if truong_von:
        gia_tri_von = float(sp[truong_von[0]] or 0)
        ghi_chu_von = f"giá vốn[{truong_von[0]}]={gia_tri_von:.2f} (mong đợi {mong_doi_von:.2f})"

    actual(f"HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; "
           f"kho {kho_truoc}->{kho_sau}; bản ghi lịch sử {so_ban_ghi_truoc}->{len(ban_ghi)}, "
           f"bản ghi mới nhất: SL={moi.get('quantity')}, giá={moi.get('unit_cost')}; {ghi_chu_von}")

    assert j["status"] is True
    assert kho_sau == kho_truoc + 20
    assert len(ban_ghi) == so_ban_ghi_truoc + 1          # đúng 1 bản ghi mới
    assert int(moi["quantity"]) == 20 and float(moi["unit_cost"]) == 300000
    if truong_von:
        assert gia_tri_von == pytest.approx(mong_doi_von, rel=1e-3)


# =====================================================================
# TC-196 / TC-197  Số lượng nhập bằng 0 / âm   (TS-37)
# =====================================================================
@pytest.mark.parametrize("so_luong", [0])
def test_tc196_so_luong_nhap_bang_0(api_as, tao_san_pham, actual, so_luong):
    s1, anon = api_as("seller1"), api_as()
    pid = tao_san_pham(s1)
    kho, ls = ton_kho(anon, pid), len(lich_su(s1))
    code, j = nhap(s1, pid, so_luong, 300000)
    actual(f"SL={so_luong}: HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; "
           f"kho {kho}->{ton_kho(anon, pid)}; lịch sử {ls}->{len(lich_su(s1))}")
    assert code < 500 and j["status"] is False
    assert ton_kho(anon, pid) == kho and len(lich_su(s1)) == ls


@pytest.mark.parametrize("so_luong", [-5])
def test_tc197_so_luong_nhap_am(api_as, tao_san_pham, actual, so_luong):
    s1, anon = api_as("seller1"), api_as()
    pid = tao_san_pham(s1)
    kho, ls = ton_kho(anon, pid), len(lich_su(s1))
    code, j = nhap(s1, pid, so_luong, 300000)
    actual(f"SL={so_luong}: HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; "
           f"kho {kho}->{ton_kho(anon, pid)}; lịch sử {ls}->{len(lich_su(s1))}")
    assert code < 500 and j["status"] is False
    assert ton_kho(anon, pid) == kho and len(lich_su(s1)) == ls


# =====================================================================
# TC-198  Giá nhập âm   (TS-37)
# =====================================================================
def test_tc198_gia_nhap_am(api_as, tao_san_pham, actual):
    s1, anon = api_as("seller1"), api_as()
    pid = tao_san_pham(s1)
    kho, ls = ton_kho(anon, pid), len(lich_su(s1))
    code, j = nhap(s1, pid, 5, -1000)
    actual(f"Giá nhập=-1000: HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; "
           f"kho {kho}->{ton_kho(anon, pid)}; lịch sử {ls}->{len(lich_su(s1))}")
    assert code < 500 and j["status"] is False
    assert ton_kho(anon, pid) == kho and len(lich_su(s1)) == ls


# =====================================================================
# TC-199  Giá nhập sai định dạng   (TS-37)
# =====================================================================
@pytest.mark.parametrize("gia_nhap", ["abc", "12,5,3", "1e"])
def test_tc199_gia_nhap_sai_dinh_dang(api_as, tao_san_pham, actual, gia_nhap):
    s1, anon = api_as("seller1"), api_as()
    pid = tao_san_pham(s1)
    kho, ls = ton_kho(anon, pid), len(lich_su(s1))
    code, j = nhap(s1, pid, 5, gia_nhap)
    actual(f"Giá nhập='{gia_nhap}': HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; "
           f"kho {kho}->{ton_kho(anon, pid)}; lịch sử {ls}->{len(lich_su(s1))}")
    assert code < 500, "Lỗi 500 khi giá nhập sai định dạng"
    assert j["status"] is False
    assert ton_kho(anon, pid) == kho and len(lich_su(s1)) == ls


# =====================================================================
# TC-200  Nhập hàng cho sản phẩm của shop khác   (TS-37)
# =====================================================================
def test_tc200_nhap_hang_san_pham_shop_khac(api_as, tao_san_pham, actual):
    s1, s2, anon = api_as("seller1"), api_as("seller2"), api_as()
    pid2 = tao_san_pham(s2)  # sản phẩm của seller2
    kho, ls2 = ton_kho(anon, pid2), len(lich_su(s2))

    code, j = nhap(s1, pid2, 10, 50000)  # seller1 cố nhập vào sản phẩm của seller2
    actual(f"seller1 nhập vào SP của seller2: HTTP {code}, status={j.get('status')}, "
           f"message='{j.get('message')}'; kho {kho}->{ton_kho(anon, pid2)}; "
           f"phiếu nhập của seller2 {ls2}->{len(lich_su(s2))}")
    assert code < 500 and j["status"] is False
    assert ton_kho(anon, pid2) == kho
    assert len(lich_su(s2)) == ls2


# =====================================================================
# TC-201  Product không tồn tại   (TS-37)
# =====================================================================
def test_tc201_nhap_hang_product_khong_ton_tai(api_as, actual):
    s1 = api_as("seller1")
    ls = len(lich_su(s1))
    code, j = nhap(s1, 99999, 10, 50000)
    actual(f"HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; lịch sử {ls}->{len(lich_su(s1))}")
    assert code < 500 and j["status"] is False
    assert len(lich_su(s1)) == ls


# =====================================================================
# TC-202  Seller xem lịch sử nhập hàng của store mình   (TS-38)
# =====================================================================
def test_tc202_seller_xem_lich_su_nhap_hang(api_as, tao_san_pham, actual):
    s1, s2 = api_as("seller1"), api_as("seller2")
    pid1, pid2 = tao_san_pham(s1), tao_san_pham(s2)
    assert nhap(s1, pid1, 5, 100000)[1]["status"] is True    # ≥ 2 lần nhập cho shop A
    assert nhap(s1, pid1, 7, 120000)[1]["status"] is True
    assert nhap(s2, pid2, 9, 80000)[1]["status"] is True     # nhập của shop khác, không được lẫn vào

    ls1 = lich_su(s1)
    sp_cua_s1 = {p["id"] for p in s1.get("/api/seller/san-pham").json()["data"]}
    cua_pid1 = [h for h in ls1 if h["product_id"] == pid1]
    lan = [h["product_id"] for h in ls1 if h["product_id"] not in sp_cua_s1]
    thieu_truong = [k for k in ("product_name", "quantity", "unit_cost", "created_at")
                    if any(k not in h for h in cua_pid1)]
    actual(f"Số bản ghi của shop mình cho SP test={len(cua_pid1)}; bản ghi thuộc shop khác bị lẫn={lan}; "
           f"thiếu trường={thieu_truong or 'không'}")
    assert len(cua_pid1) == 2
    assert sorted(int(h["quantity"]) for h in cua_pid1) == [5, 7]
    assert lan == [], "Lịch sử nhập lẫn dữ liệu shop khác"
    assert pid2 not in [h["product_id"] for h in ls1]
    assert thieu_truong == []


# =====================================================================
# TC-203  Seller chưa có store   (TS-38)
# =====================================================================
def test_tc203_seller_chua_co_store(playwright, base_url, actual):
    ctx = playwright.request.new_context(base_url=base_url)
    try:
        r = ctx.post("/api/dang-nhap", data={"tendangnhap": "seller_nostore", "mat_khau": PWD})
        if not r.json().get("status"):
            actual("Chưa có tài khoản seller_nostore (Seller không có gian hàng) trong DB: cần tạo rồi chạy lại")
            pytest.fail("Thiếu dữ liệu test: tài khoản seller_nostore không tồn tại/không đăng nhập được")
        r = ctx.get("/api/seller/lich-su-nhap-hang")
        j = r.json()
        actual(f"HTTP {r.status}, status={j.get('status')}, message='{j.get('message')}', "
               f"số bản ghi trả về={len(j.get('data') or [])}")
        assert r.status in (400, 403)
        assert j["status"] is False
        assert not j.get("data")
    finally:
        ctx.dispose()


# =====================================================================
# TC-204  Chưa đăng nhập xem lịch sử nhập hàng   (TS-38)
# =====================================================================
def test_tc204_lich_su_nhap_chua_dang_nhap(api_as, actual):
    r = api_as().get("/api/seller/lich-su-nhap-hang")
    j = r.json()
    actual(f"HTTP {r.status}, status={j.get('status')}, message='{j.get('message')}'")
    assert r.status in (401, 403)
    assert j["status"] is False
    assert not j.get("data")


# =====================================================================
# TC-205  Không truyền store_id   (TS-38)
# =====================================================================
def test_tc205_lich_su_nhap_khong_co_store_id(api_as, actual):
    s1 = api_as("seller1")
    sp_cua_s1 = {p["id"] for p in s1.get("/api/seller/san-pham").json()["data"]}

    r = s1.get("/api/seller/lich-su-nhap-hang")                 # không truyền store_id
    r_khac = s1.get("/api/seller/lich-su-nhap-hang?store_id=2")  # thử ép sang shop khác
    j, j2 = r.json(), r_khac.json()
    lan = [h["product_id"] for h in (j.get("data") or []) if h["product_id"] not in sp_cua_s1]
    lan2 = [h["product_id"] for h in (j2.get("data") or []) if h["product_id"] not in sp_cua_s1]
    actual(f"Không store_id: HTTP {r.status}, status={j.get('status')}, lẫn shop khác={lan}; "
           f"?store_id=2: HTTP {r_khac.status}, status={j2.get('status')}, lẫn shop khác={lan2}")
    assert r.status < 500 and r_khac.status < 500
    assert j["status"] is True and lan == []
    assert lan2 == [], "Tham số store_id làm lộ dữ liệu shop khác"


# =====================================================================
# TC-206  Cập nhật giá bán hợp lệ   (TS-39)
# =====================================================================
def test_tc206_cap_nhat_gia_ban_hop_le(api_as, tao_san_pham, actual):
    s1, anon = api_as("seller1"), api_as()
    pid = tao_san_pham(s1, gia=500000)

    code, j = doi_gia(s1, pid, "gia_goc", 600000)
    gia_ct = gia(anon, pid)  # trang công khai (không cần đăng nhập)
    ds_ct = anon.get("/api/products").json().get("data") or []
    gia_trong_ds = next((float(p["price"]) for p in ds_ct if p["id"] == pid), None)
    actual(f"HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; "
           f"giá công khai (chi tiết)={gia_ct:.0f}, (danh sách)={gia_trong_ds}")

    assert j["status"] is True
    assert gia_ct == 600000
    assert gia_trong_ds == 600000


# =====================================================================
# TC-207 / TC-208 / TC-209  Giá bán không hợp lệ   (TS-39)
# =====================================================================
def _thu_gia_khong_hop_le(api_as, tao_san_pham, actual, kieu, gia_tri):
    s1, anon = api_as("seller1"), api_as()
    pid = tao_san_pham(s1, gia=500000)
    gia_truoc = gia(anon, pid)
    code, j = doi_gia(s1, pid, kieu, gia_tri)
    gia_sau = gia(anon, pid)
    actual(f"[{kieu}] giá gửi={gia_tri!r}: HTTP {code}, status={j.get('status')}, "
           f"message='{j.get('message')}'; giá {gia_truoc:.0f}->{gia_sau:.0f}")
    assert code < 500, "Lỗi 500 khi giá không hợp lệ"
    assert j["status"] is False
    assert gia_sau == gia_truoc


@pytest.mark.parametrize("kieu", ["gia_goc", "gia_moi"])
def test_tc207_gia_bang_0(api_as, tao_san_pham, actual, kieu):
    _thu_gia_khong_hop_le(api_as, tao_san_pham, actual, kieu, 0)


@pytest.mark.parametrize("kieu", ["gia_goc", "gia_moi"])
def test_tc208_gia_am(api_as, tao_san_pham, actual, kieu):
    _thu_gia_khong_hop_le(api_as, tao_san_pham, actual, kieu, -1000)


@pytest.mark.parametrize("kieu", ["gia_goc", "gia_moi"])
@pytest.mark.parametrize("gia_tri", ["abc", "12,5,3"])
def test_tc209_gia_sai_dinh_dang(api_as, tao_san_pham, actual, kieu, gia_tri):
    _thu_gia_khong_hop_le(api_as, tao_san_pham, actual, kieu, gia_tri)


# =====================================================================
# TC-210  Cập nhật giá sản phẩm của shop khác   (TS-39)
# =====================================================================
@pytest.mark.parametrize("kieu", ["gia_goc", "gia_moi"])
def test_tc210_cap_nhat_gia_san_pham_shop_khac(api_as, tao_san_pham, actual, kieu):
    s1, s2, anon = api_as("seller1"), api_as("seller2"), api_as()
    pid2 = tao_san_pham(s2, gia=500000)  # sản phẩm của seller2
    gia_truoc = gia(anon, pid2)

    code, j = doi_gia(s1, pid2, kieu, 99000)  # seller1 cố đổi giá
    gia_sau = gia(anon, pid2)
    actual(f"[{kieu}] seller1 đổi giá SP của seller2: HTTP {code}, status={j.get('status')}, "
           f"message='{j.get('message')}'; giá {gia_truoc:.0f}->{gia_sau:.0f}")
    assert code < 500 and j["status"] is False
    assert gia_sau == gia_truoc