"""
TC-211 .. TC-238  (TS-39 phần cuối, TS-40, TS-41, TS-42, TS-43)
Seller: cập nhật giá / xem đơn / đổi trạng thái đơn / tổng quan / doanh thu theo tháng.

Cách chạy (conftest.py đã có fixture page, login, actual):
    pytest test_tc211_238_seller_don_hang.py -v --base-url http://localhost:5000

Ghi chú:
- Test API dùng APIRequestContext của Playwright (mỗi tài khoản 1 session riêng).
- Test UI dùng fixture `page` + `login` của conftest.
- Đơn hàng được TẠO MỚI qua /api/don-hang/dat-hang (khach1) cho từng test,
  nên không phụ thuộc trạng thái đơn trong seed.
- Không dùng pytest.skip trong thân test (conftest sẽ ghi thành Fail).
"""
import re
import uuid
from datetime import datetime

import pytest
from playwright.sync_api import expect

PW = "123456"
SDT = "0901234567"
NHAN_TT = {
    "Pending": "Chờ duyệt",
    "Confirmed": "Đã xác nhận",
    "Shipping": "Đang giao",
    "Completed": "Hoàn thành",
    "Cancelled": "Đã hủy",
}
ID_KHONG_TON_TAI = 99999999


# ============================================================
# HELPER: API client
# ============================================================
class Client:
    """Bọc APIRequestContext: trả (http_status, body_dict)."""

    def __init__(self, ctx, ma_user=None):
        self.ctx = ctx
        self.ma_user = ma_user

    def _call(self, method, url, **kw):
        r = getattr(self.ctx, method)(url, **kw)
        try:
            body = r.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        return r.status, body

    def get(self, url, params=None):
        return self._call("get", url, params=params)

    def post(self, url, data=None):
        return self._call("post", url, data={} if data is None else data)

    def put(self, url, data=None):
        return self._call("put", url, data={} if data is None else data)


@pytest.fixture
def api(playwright, base_url):
    """api()            -> client chưa đăng nhập
       api("seller1")   -> client đã đăng nhập (sai tài khoản => Fail rõ lý do)"""
    ctxs = []

    def _make(user=None, pw=PW):
        ctx = playwright.request.new_context(base_url=base_url)
        ctxs.append(ctx)
        client = Client(ctx)
        if user:
            st, body = client.post("/api/dang-nhap",
                                   {"tendangnhap": user, "mat_khau": pw})
            assert body.get("status"), (
                f"Không đăng nhập được '{user}' (HTTP {st}): {body.get('message')} "
                f"- kiểm tra tài khoản này đã có trong DB chưa")
            client.ma_user = body["data"]["ma_user"]
        return client

    yield _make
    for c in ctxs:
        c.dispose()


# ============================================================
# HELPER: dữ liệu / nghiệp vụ
# ============================================================
def store_id_cua(client):
    st, b = client.get(f"/api/stores/by-user/{client.ma_user}")
    assert b.get("status"), f"Không lấy được store của user {client.ma_user}: {b}"
    return b["data"]["store_id"]


def lay_san_pham(seller):
    st, b = seller.get("/api/seller/san-pham")
    assert b.get("status"), f"Không lấy được sản phẩm của seller: {b}"
    return b["data"]


def chon_san_pham(seller, min_qty=5):
    """Chọn sản phẩm đang bán, tồn nhiều nhất của shop."""
    ds = [p for p in lay_san_pham(seller)
          if p.get("is_active") and int(p.get("quantity") or 0) >= min_qty]
    assert ds, f"Shop không có sản phẩm đang bán với tồn kho >= {min_qty} (hãy nhập thêm hàng)"
    return max(ds, key=lambda p: int(p["quantity"]))


def ton_kho(client, product_id):
    st, b = client.get(f"/api/products/{product_id}")
    assert b.get("status"), f"Không đọc được sản phẩm {product_id}: {b}"
    return int(b["data"]["quantity"])


def lay_don_shop(seller):
    st, b = seller.get("/api/seller/don-hang")
    assert b.get("status"), f"Không lấy được đơn của shop (HTTP {st}): {b}"
    return b["data"]


def trang_thai_don(seller, order_id):
    for o in lay_don_shop(seller):
        if o["OrderId"] == order_id:
            return o["Status"]
    return None


def tao_don(khach, product_ids, qty=1):
    """Đặt hàng (1 lần checkout) -> list [{order_id, store_id, ...}] (tách theo shop)."""
    items = [{"ProductId": pid, "ProductName": f"SP {pid}", "Emoji": "📦",
              "Quantity": qty, "UnitPrice": 0, "TotalPrice": 0}
             for pid in product_ids]
    st, b = khach.post("/api/don-hang/dat-hang", {
        "ReceiverName": "Nguyen Test", "ReceiverPhone": SDT,
        "ShippingAddress": "1 Duong Test, Quan 1, TP HCM",
        "PaymentMethod": "COD", "ShippingFee": 25000, "Items": items})
    assert b.get("status"), f"Không tạo được đơn test: {b.get('message')}"
    return b["data"]["orders"]


def tao_don_pending(khach, seller, qty=1):
    """Tạo 1 đơn Pending chứa sản phẩm của `seller`."""
    sp = chon_san_pham(seller, min_qty=qty + 3)
    orders = tao_don(khach, [sp["id"]], qty)
    return {"order_id": orders[0]["order_id"], "product_id": sp["id"],
            "price": float(sp["price"]), "qty": qty}


def doi_trang_thai(seller, order_id, status):
    return seller.put(f"/api/seller/don-hang/{order_id}/trang-thai", {"status": status})


LUONG = ["Pending", "Confirmed", "Shipping", "Completed"]


def dua_den(seller, order_id, dich):
    """Đưa đơn từ Pending tới trạng thái `dich` theo đúng luồng."""
    if dich == "Cancelled":
        st, b = doi_trang_thai(seller, order_id, "Cancelled")
        assert b.get("status"), f"Setup hủy đơn thất bại: {b}"
        return
    for nxt in LUONG[1:LUONG.index(dich) + 1]:
        st, b = doi_trang_thai(seller, order_id, nxt)
        assert b.get("status"), f"Setup chuyển {nxt} thất bại: {b}"


def doanh_thu(seller):
    st, b = seller.get("/api/seller/thong-ke/tong-quan")
    assert b.get("status"), f"Không lấy được tổng quan: {b}"
    return float(b["data"]["doanh_thu"])


def tien_items(order):
    return sum(float(i["Quantity"]) * float(i["UnitPrice"]) for i in order.get("Items", []))


def ky_vong_theo_thang(don_list, year):
    """Doanh thu từng tháng = tổng items của đơn Completed trong tháng."""
    kq = {m: 0.0 for m in range(1, 13)}
    for o in don_list:
        if o["Status"] != "Completed":
            continue
        created = str(o.get("CreatedAt") or "")
        if not created.startswith(str(year)):
            continue
        kq[int(created[5:7])] += tien_items(o)
    return kq


def thang_tu_api(body):
    return {int(m["thang"]): float(m["doanh_thu"]) for m in body["data"]}


def chi_so_digits(text):
    return int(re.sub(r"\D", "", text) or 0)


def tao_shop_moi(api):
    """Tạo seller + gian hàng MỚI (chưa có sản phẩm/đơn) qua luồng đăng ký -> Quản lý duyệt."""
    suffix = uuid.uuid4().hex[:8]
    user, shop = f"selnew_{suffix}", f"Shop Test {suffix}"
    anon = api()
    st, b = anon.post("/api/dang-ky", {"ten_user": "Seller Moi", "tendangnhap": user,
                                       "sdt": SDT, "mat_khau": PW,
                                       "dia_chi": "1 Duong Test, TP HCM"})
    assert b.get("status"), f"Setup: đăng ký tài khoản mới lỗi: {b.get('message')}"
    c = api(user)
    st, b = c.post("/api/cap-nhat-profile", {"ten_user": "Seller Moi", "dia_chi": "1 Duong Test, TP HCM",
                                             "sdt": SDT, "cmnd": "079" + str(uuid.uuid4().int)[:9]})
    assert b.get("status"), f"Setup: cập nhật hồ sơ lỗi: {b.get('message')}"
    st, cats = c.get("/api/categories")
    cat = cats["data"][0]
    st, b = c.post("/api/dang-ky-gian-hang", {"StoreName": shop, "Phone": SDT,
                                              "Category": cat.get("category_name") or cat.get("name"),
                                              "Description": "Shop test tự động"})
    assert b.get("status"), f"Setup: gửi đơn đăng ký gian hàng lỗi: {b.get('message')}"
    ql = api("quanly1")
    st, b = ql.get("/api/seller-requests")
    req = next((r for r in b.get("data", []) if r.get("shop_name") == shop), None)
    assert req, "Setup: không thấy đơn đăng ký vừa gửi"
    st, b = ql.post(f"/api/duyet-seller/{req['request_id']}", {})
    assert b.get("status"), f"Setup: duyệt seller lỗi: {b.get('message')}"
    seller = api(user)  # đăng nhập lại để nhận vai trò Seller
    st, b = seller.get("/api/seller/san-pham")
    assert b.get("status"), f"Setup: shop mới chưa dùng được kênh Seller: {b}"
    return {"user": user, "shop": shop, "client": seller, "category_id": cat.get("category_id")}


# ---------- helper UI ----------
def vao_kenh_seller(page, login, user):
    login(user, PW)
    page.wait_for_selector("#sellerDashboard", state="visible", timeout=15000)


def vao_kenh_seller_chua_co_store(page, login, user):
    """Seller chưa có store: đợi khôi phục phiên xong (hienThiGiaoDienTheoVaiTro đặt
    #userInterface.style.display='block'), rồi mới bấm 'Kênh Người Bán'.
    Nếu bấm sớm, hàm khôi phục sẽ ẩn lại dashboard => #smenu-orders không hiển thị."""
    login(user, PW)
    page.wait_for_function(
        "document.getElementById('userInterface').style.display === 'block'", timeout=15000)
    page.wait_for_selector("#hdrGoSellerBtn", state="visible", timeout=15000)
    page.click("#hdrGoSellerBtn")
    page.wait_for_selector("#sellerDashboard", state="visible", timeout=10000)


def mo_tab_don_hang_ui(page):
    page.click("#smenu-orders")
    expect(page.locator("#tblSellerOrdersBody")).not_to_contain_text("Đang tải", timeout=10000)


# ============================================================
# TS-39 — TC-211
# ============================================================
def test_tc211_doi_gia_product_khong_ton_tai(api, actual):
    seller = api("seller1")
    cac_payload = [
        {"gia_goc": 100000, "giam_gia": False},
        {"gia_goc": 100000, "gia_khuyen_mai": 50000, "giam_gia": True},
        {"gia_moi": 100000},
    ]
    ket_qua = []
    for p in cac_payload:
        st, b = seller.put(f"/api/seller/san-pham/{ID_KHONG_TON_TAI}/gia", p)
        ket_qua.append((st, b))
    actual("; ".join(f"HTTP {st}, status={b.get('status')}, msg='{b.get('message')}'"
                     for st, b in ket_qua))
    for st, b in ket_qua:
        assert st < 500, f"Lỗi 500 khi product không tồn tại: {b}"
        assert b.get("status") is False, f"Phải từ chối, nhưng nhận: {b}"


# ============================================================
# TS-40 — Xem đơn hàng của gian hàng (TC-212 .. TC-215)
# ============================================================
def test_tc212_seller_xem_don_hang_cua_shop(page, login, api, actual):
    s1 = api("seller1")
    tao_don_pending(api("khach1"), s1)           # đảm bảo shop chắc chắn có đơn
    don_api = lay_don_shop(s1)
    assert don_api, "Shop seller1 không có đơn"

    vao_kenh_seller(page, login, "seller1")
    mo_tab_don_hang_ui(page)
    ma_tren_ui = page.locator("#tblSellerOrdersBody tr td:first-child").all_inner_texts()
    ma_tren_ui = {t.strip() for t in ma_tren_ui}
    ma_api = {f"#{o['OrderId']}" for o in don_api}
    actual(f"UI hiển thị {len(ma_tren_ui)} đơn, API trả {len(ma_api)} đơn")
    assert ma_tren_ui == ma_api, f"UI {ma_tren_ui} khác API {ma_api}"

    dong = page.locator("#tblSellerOrdersBody tr").first
    expect(dong.locator(".badge-status")).to_be_visible()           # có trạng thái
    mot_don = don_api[0]
    assert mot_don["ReceiverName"] in page.locator("#tblSellerOrdersBody").inner_text()
    assert mot_don["ReceiverPhone"] in page.locator("#tblSellerOrdersBody").inner_text()


def test_tc213_seller_khong_co_store_xem_don(page, login, api, actual):
    ns = api("seller_nostore")
    st, b = ns.get("/api/seller/don-hang")
    actual(f"API: HTTP {st}, status={b.get('status')}, msg='{b.get('message')}'")
    assert st == 403 and b.get("status") is False
    assert "gian hàng" in (b.get("message") or "").lower()
    assert not b.get("data")

    vao_kenh_seller_chua_co_store(page, login, "seller_nostore")
    mo_tab_don_hang_ui(page)
    noi_dung = page.locator("#tblSellerOrdersBody").inner_text()
    ma_don = page.locator("#tblSellerOrdersBody tr td:first-child").all_inner_texts()
    actual(f"UI: '{noi_dung.strip()}'")
    assert "gian hàng" in noi_dung.lower()
    assert not any(t.strip().startswith("#") for t in ma_don), "Không được hiện đơn của shop khác"


def test_tc214_chua_dang_nhap_xem_don(api, actual):
    anon = api()
    st, b = anon.get("/api/seller/don-hang")
    actual(f"HTTP {st}, status={b.get('status')}, msg='{b.get('message')}'")
    assert st in (401, 403), f"Phải từ chối, nhưng HTTP {st}"
    assert b.get("status") is False
    assert not b.get("data")


def test_tc215_khong_lan_don_shop_khac(api, actual):
    s1, s2, khach = api("seller1"), api("seller2"), api("khach1")
    store1, store2 = store_id_cua(s1), store_id_cua(s2)
    sp1, sp2 = chon_san_pham(s1), chon_san_pham(s2)
    # 1 lần checkout 2 shop => sinh 2 đơn tách theo shop
    orders = tao_don(khach, [sp1["id"], sp2["id"]])
    don_a = next(o["order_id"] for o in orders if o["store_id"] == store1)
    don_b = next(o["order_id"] for o in orders if o["store_id"] == store2)

    ds1 = lay_don_shop(s1)
    ma = {o["OrderId"] for o in ds1}
    id_sp_shop1 = {p["id"] for p in lay_san_pham(s1)}
    item_la = [(o["OrderId"], i["ProductId"]) for o in ds1 for i in o["Items"]
               if i["ProductId"] not in id_sp_shop1]
    actual(f"Đơn shop A={don_a}, shop B={don_b}; seller1 thấy {sorted(ma)[-5:]}...; item lạ={item_la}")
    assert don_a in ma, "Seller A phải thấy đơn của shop A"
    assert don_b not in ma, "Seller A không được thấy đơn của shop B"
    assert not item_la, f"Có sản phẩm của shop khác lẫn vào: {item_la}"


# ============================================================
# TS-41 — Cập nhật trạng thái đơn (TC-216 .. TC-227)
# ============================================================
def test_tc216_pending_to_confirmed(page, login, api, actual):
    s1 = api("seller1")
    don = tao_don_pending(api("khach1"), s1)
    oid = don["order_id"]
    st, b = doi_trang_thai(s1, oid, "Confirmed")
    actual(f"Đơn #{oid}: HTTP {st}, status={b.get('status')}, msg='{b.get('message')}'")
    assert b.get("status") is True, b
    assert trang_thai_don(s1, oid) == "Confirmed"

    # danh sách + chi tiết trên UI hiển thị trạng thái mới
    vao_kenh_seller(page, login, "seller1")
    mo_tab_don_hang_ui(page)
    dong = page.locator("#tblSellerOrdersBody tr").filter(
        has=page.locator("td", has_text=re.compile(rf"^#{oid}$")))
    expect(dong).to_have_count(1)
    expect(dong.locator(".badge-status")).to_have_text(NHAN_TT["Confirmed"])
    dong.get_by_text("Xem chi tiết").click()
    expect(page.locator("#sellerOrderDetailContent")).to_contain_text(NHAN_TT["Confirmed"])


def test_tc217_pending_to_cancelled(api, actual):
    s1, khach = api("seller1"), api("khach1")
    sp = chon_san_pham(s1)
    ton_dau = ton_kho(khach, sp["id"])
    oid = tao_don(khach, [sp["id"]], 2)[0]["order_id"]
    ton_sau_dat = ton_kho(khach, sp["id"])
    dt_truoc = doanh_thu(s1)

    st, b = doi_trang_thai(s1, oid, "Cancelled")
    ton_sau_huy = ton_kho(khach, sp["id"])
    dt_sau = doanh_thu(s1)
    actual(f"Đơn #{oid}: status={b.get('status')}; tồn {ton_dau}->{ton_sau_dat}->{ton_sau_huy}; "
           f"doanh thu {dt_truoc}->{dt_sau}")
    assert b.get("status") is True, b
    assert trang_thai_don(s1, oid) == "Cancelled"
    assert ton_sau_dat == ton_dau - 2
    assert ton_sau_huy == ton_dau, "Tồn kho phải được hoàn lại"
    assert dt_sau == pytest.approx(dt_truoc), "Đơn Cancelled không được tính vào doanh thu"


def test_tc218_confirmed_to_shipping(api, actual):
    s1 = api("seller1")
    oid = tao_don_pending(api("khach1"), s1)["order_id"]
    dua_den(s1, oid, "Confirmed")
    st, b = doi_trang_thai(s1, oid, "Shipping")
    actual(f"Đơn #{oid}: HTTP {st}, status={b.get('status')}, msg='{b.get('message')}'")
    assert b.get("status") is True, b
    assert trang_thai_don(s1, oid) == "Shipping"


def _seller_huy_don_bi_tu_choi(api, actual, trang_thai):
    """Phase 3: Seller chỉ được hủy đơn Pending. Đơn Confirmed/Shipping => từ chối,
    trạng thái + tồn kho + doanh thu không đổi."""
    s1, khach = api("seller1"), api("khach1")
    sp = chon_san_pham(s1)
    oid = tao_don(khach, [sp["id"]], 2)[0]["order_id"]
    dua_den(s1, oid, trang_thai)
    ton_truoc = ton_kho(khach, sp["id"])
    dt_truoc = doanh_thu(s1)

    st, b = doi_trang_thai(s1, oid, "Cancelled")
    tt_sau, ton_sau, dt_sau = trang_thai_don(s1, oid), ton_kho(khach, sp["id"]), doanh_thu(s1)
    actual(f"Đơn #{oid} ({trang_thai}->Cancelled): HTTP {st}, status={b.get('status')}, "
           f"msg='{b.get('message')}'; trạng thái sau={tt_sau}; tồn {ton_truoc}->{ton_sau}; "
           f"doanh thu {dt_truoc}->{dt_sau}")
    assert st < 500
    assert b.get("status") is False, "Seller không được hủy đơn đã qua Pending"
    assert "chờ duyệt" in (b.get("message") or "").lower()
    assert tt_sau == trang_thai, "Trạng thái đơn không được đổi"
    assert ton_sau == ton_truoc, "Tồn kho không được đổi"
    assert dt_sau == pytest.approx(dt_truoc)


def test_tc219_confirmed_to_cancelled(api, actual):
    _seller_huy_don_bi_tu_choi(api, actual, "Confirmed")


def test_tc220_shipping_to_completed(api, actual):
    s1 = api("seller1")
    don = tao_don_pending(api("khach1"), s1, qty=2)
    oid = don["order_id"]
    dua_den(s1, oid, "Shipping")
    dt_truoc = doanh_thu(s1)          # chưa Completed => chưa tính
    st, b = doi_trang_thai(s1, oid, "Completed")
    dt_sau = doanh_thu(s1)
    don_sau = next(o for o in lay_don_shop(s1) if o["OrderId"] == oid)
    tang = dt_sau - dt_truoc
    actual(f"Đơn #{oid}: status={b.get('status')}; doanh thu {dt_truoc}->{dt_sau} (+{tang}); "
           f"tiền items={tien_items(don_sau)}")
    assert b.get("status") is True, b
    assert don_sau["Status"] == "Completed"
    assert tang == pytest.approx(tien_items(don_sau)), "Doanh thu phải tăng đúng bằng tiền items của đơn"


def test_tc221_shipping_to_cancelled(api, actual):
    _seller_huy_don_bi_tu_choi(api, actual, "Shipping")


def test_tc222_chuyen_sai_luong(api, actual):
    s1 = api("seller1")
    oid = tao_don_pending(api("khach1"), s1)["order_id"]
    ghi = []
    for moi in ("Shipping", "Completed"):                      # Pending bỏ bước
        st, b = doi_trang_thai(s1, oid, moi)
        ghi.append(f"Pending->{moi}: status={b.get('status')}, msg='{b.get('message')}'")
        assert st < 500 and b.get("status") is False, f"Pending->{moi} phải bị từ chối: {b}"
        assert trang_thai_don(s1, oid) == "Pending"
    dua_den(s1, oid, "Confirmed")
    st, b = doi_trang_thai(s1, oid, "Completed")               # Confirmed bỏ bước
    ghi.append(f"Confirmed->Completed: status={b.get('status')}, msg='{b.get('message')}'")
    actual("; ".join(ghi))
    assert st < 500 and b.get("status") is False
    assert trang_thai_don(s1, oid) == "Confirmed"


def test_tc223_completed_la_terminal(api, actual):
    s1 = api("seller1")
    oid = tao_don_pending(api("khach1"), s1)["order_id"]
    dua_den(s1, oid, "Completed")
    ghi = []
    for moi in ("Pending", "Confirmed", "Shipping", "Cancelled"):
        st, b = doi_trang_thai(s1, oid, moi)
        ghi.append(f"Completed->{moi}: status={b.get('status')}, msg='{b.get('message')}'")
        assert st < 500 and b.get("status") is False, f"Completed->{moi} phải bị từ chối: {b}"
        assert trang_thai_don(s1, oid) == "Completed"
    actual("; ".join(ghi))


def test_tc224_cancelled_la_terminal(api, actual):
    s1 = api("seller1")
    oid = tao_don_pending(api("khach1"), s1)["order_id"]
    dua_den(s1, oid, "Cancelled")
    ghi = []
    for moi in ("Pending", "Confirmed", "Shipping", "Completed"):
        st, b = doi_trang_thai(s1, oid, moi)
        ghi.append(f"Cancelled->{moi}: status={b.get('status')}, msg='{b.get('message')}'")
        assert st < 500 and b.get("status") is False, f"Cancelled->{moi} phải bị từ chối: {b}"
        assert trang_thai_don(s1, oid) == "Cancelled"
    actual("; ".join(ghi))


def test_tc225_status_khong_hop_le(api, actual):
    s1 = api("seller1")
    oid = tao_don_pending(api("khach1"), s1)["order_id"]
    ghi = []
    for gia_tri in ("Done", "", 123):
        st, b = doi_trang_thai(s1, oid, gia_tri)
        ghi.append(f"status={gia_tri!r}: HTTP {st}, msg='{b.get('message')}'")
        assert st < 500, f"Lỗi 500 với status={gia_tri!r}"
        assert b.get("status") is False, f"status={gia_tri!r} phải bị từ chối"
        assert trang_thai_don(s1, oid) == "Pending"
    actual("; ".join(ghi))


def test_tc226_order_khong_ton_tai(api, actual):
    s1 = api("seller1")
    st, b = doi_trang_thai(s1, ID_KHONG_TON_TAI, "Confirmed")
    actual(f"HTTP {st}, status={b.get('status')}, msg='{b.get('message')}'")
    assert st < 500, f"Lỗi 500: {b}"
    assert b.get("status") is False


def test_tc227_order_thuoc_seller_khac(api, actual):
    s1, s2 = api("seller1"), api("seller2")
    oid = tao_don_pending(api("khach1"), s2)["order_id"]       # đơn của shop seller2
    st, b = doi_trang_thai(s1, oid, "Confirmed")
    trang_thai_sau = trang_thai_don(s2, oid)
    actual(f"seller1 đổi đơn #{oid} của seller2: HTTP {st}, status={b.get('status')}, "
           f"msg='{b.get('message')}'; trạng thái sau={trang_thai_sau}")
    assert st < 500
    assert b.get("status") is False, "Seller1 không được đổi đơn của shop khác"
    assert trang_thai_sau == "Pending"


# ============================================================
# TS-42 — Tổng quan gian hàng (TC-228 .. TC-232)
# ============================================================
def test_tc228_tong_quan_co_du_lieu(page, login, api, actual):
    s1 = api("seller1")
    tao_don_pending(api("khach1"), s1)       # có thêm đơn chưa Completed để kiểm tra loại trừ
    don = lay_don_shop(s1)
    sp = lay_san_pham(s1)
    dem = lambda tt: sum(1 for o in don if o["Status"] == tt)
    dt_ky_vong = sum(tien_items(o) for o in don if o["Status"] == "Completed")

    st, b = s1.get("/api/seller/thong-ke/tong-quan")
    d = b.get("data", {})
    actual(f"API: {d}")
    assert b.get("status") is True
    assert float(d["doanh_thu"]) == pytest.approx(dt_ky_vong), "Doanh thu chỉ tính đơn Completed"
    assert d["tong_don"] == len(don)
    assert d["cho_duyet"] == dem("Pending")
    assert d["dang_giao"] == dem("Shipping")
    assert d["hoan_thanh"] == dem("Completed")
    assert d["da_huy"] == dem("Cancelled")
    assert "loi_nhuan" not in d and "profit" not in {k.lower() for k in d}

    # UI
    vao_kenh_seller(page, login, "seller1")
    page.wait_for_selector("#sellerOverviewContent .stats-grid", timeout=10000)
    vals = page.locator("#sellerOverviewContent .stat-val").all_inner_texts()
    toan_bo = page.locator("#sellerOverviewContent").inner_text().lower()
    assert chi_so_digits(vals[0]) == len(sp), "Tổng sản phẩm phải khớp DB"
    assert chi_so_digits(vals[-1]) == int(round(dt_ky_vong)), "Doanh thu UI phải khớp DB"
    assert f"{len(don)} đơn" in toan_bo
    assert "lợi nhuận" not in toan_bo and "profit" not in toan_bo


def test_tc229_tong_quan_shop_khong_co_du_lieu(page, login, api, actual):
    shop = tao_shop_moi(api)
    st, b = shop["client"].get("/api/seller/thong-ke/tong-quan")
    d = b.get("data", {})
    actual(f"Shop mới '{shop['shop']}': {d}")
    assert b.get("status") is True, b
    for k in ("doanh_thu", "tong_don", "cho_duyet", "dang_giao", "hoan_thanh", "da_huy"):
        assert float(d[k]) == 0, f"{k} phải bằng 0, thực tế {d[k]}"
    assert "loi_nhuan" not in d

    vao_kenh_seller(page, login, shop["user"])
    expect(page.locator("#sellerOverviewContent")).not_to_contain_text("Đang tải", timeout=10000)
    noi_dung = page.locator("#sellerOverviewContent").inner_text().lower()
    assert "lỗi" not in noi_dung and "❌" not in noi_dung, f"UI báo lỗi: {noi_dung}"
    assert "lợi nhuận" not in noi_dung


def test_tc230_tong_quan_seller_chua_co_store(page, login, api, actual):
    ns = api("seller_nostore")
    st, b = ns.get("/api/seller/thong-ke/tong-quan")
    actual(f"API: HTTP {st}, status={b.get('status')}, msg='{b.get('message')}'")
    assert st == 403 and b.get("status") is False
    assert "gian hàng" in (b.get("message") or "").lower()
    assert not b.get("data")

    vao_kenh_seller_chua_co_store(page, login, "seller_nostore")
    expect(page.locator("#sellerOverviewContent")).not_to_contain_text("Đang tải", timeout=10000)
    noi_dung = page.locator("#sellerOverviewContent").inner_text()
    actual(f"UI: '{noi_dung.strip()}'")
    assert "gian hàng" in noi_dung.lower()
    assert page.locator("#sellerOverviewContent .stats-grid").count() == 0, "Không được hiện số liệu"


def test_tc231_chua_dang_nhap_xem_tong_quan(api, actual):
    st, b = api().get("/api/seller/thong-ke/tong-quan")
    actual(f"HTTP {st}, status={b.get('status')}, msg='{b.get('message')}'")
    assert st in (401, 403), f"Phải từ chối, nhưng HTTP {st}"
    assert b.get("status") is False
    assert not b.get("data")


def test_tc232_ownership_thong_ke(api, actual):
    s1, s2 = api("seller1"), api("seller2")
    store1, store2 = store_id_cua(s1), store_id_cua(s2)
    st0, goc = s1.get("/api/seller/thong-ke/tong-quan")
    ghi = []
    for params in ({"store_id": store2}, {"storeId": store2}):
        st, b = s1.get("/api/seller/thong-ke/tong-quan", params=params)
        ghi.append(f"{params}: HTTP {st}, store_id trả về={b.get('data', {}).get('store_id')}")
        assert st < 500
        if b.get("status"):                      # nếu không từ chối thì chỉ được trả số liệu shop mình
            assert b["data"].get("store_id") == store1, "Lộ thống kê shop khác"
            assert b["data"] == goc["data"], "Số liệu phải y hệt thống kê của chính shop seller1"
    actual("; ".join(ghi) + f"; seller1.store={store1}, seller2.store={store2}")


# ============================================================
# TS-43 — Doanh thu theo tháng (TC-233 .. TC-238)
# ============================================================
URL_DT = "/api/seller/thong-ke/doanh-thu-theo-thang"


def test_tc233_doanh_thu_nam_hop_le(api, actual):
    s1, khach = api("seller1"), api("khach1")
    # tạo thêm 1 đơn Completed + 1 đơn Pending để chắc chắn có dữ liệu cả 2 loại
    hoan_tat = tao_don_pending(khach, s1)["order_id"]
    dua_den(s1, hoan_tat, "Completed")
    tao_don_pending(khach, s1)

    st, b = s1.get(URL_DT, params={"year": 2026})
    don = lay_don_shop(s1)
    ky_vong = ky_vong_theo_thang(don, 2026)
    thuc_te = thang_tu_api(b)
    actual(f"HTTP {st}; thực tế={thuc_te}; kỳ vọng={ky_vong}")
    assert b.get("status") is True, b
    assert sorted(thuc_te) == list(range(1, 13)), "Phải đủ 12 tháng"
    for m in range(1, 13):
        assert thuc_te[m] == pytest.approx(ky_vong[m]), f"Tháng {m} lệch"
    assert any(v > 0 for v in thuc_te.values()), "Phải có ít nhất 1 tháng có doanh thu"
    assert any(v == 0 for v in thuc_te.values()), "Tháng không có đơn Completed phải = 0"


def test_tc234_khong_truyen_year(api, actual):
    s1 = api("seller1")
    st, b = s1.get(URL_DT)
    nam_nay = datetime.now().year
    st2, b2 = s1.get(URL_DT, params={"year": nam_nay})
    actual(f"HTTP {st}, status={b.get('status')}, msg='{b.get('message')}', "
           f"số tháng={len(b.get('data') or [])}")
    assert st < 500, f"Lỗi 500: {b}"
    if b.get("status"):                          # dùng năm mặc định
        assert len(b["data"]) == 12
        assert thang_tu_api(b) == thang_tu_api(b2), "Mặc định phải là năm hiện tại"
    else:                                        # hoặc báo thiếu year
        assert b.get("message")


def test_tc235_year_khong_phai_so(api, actual):
    """Theo Excel: từ chối, báo năm không hợp lệ.
    (Code hiện tại: request.args.get(type=int) nuốt lỗi -> rơi về năm hiện tại)."""
    s1 = api("seller1")
    st, b = s1.get(URL_DT, params={"year": "abc"})
    actual(f"HTTP {st}, status={b.get('status')}, msg='{b.get('message')}', "
           f"số tháng trả về={len(b.get('data') or [])}")
    assert st < 500, f"Lỗi 500: {b}"
    assert b.get("status") is False or st == 400, "Phải từ chối year='abc'"
    assert not b.get("data")


def test_tc236_khong_co_du_lieu_doanh_thu(api, actual):
    shop = tao_shop_moi(api)
    c = shop["client"]
    st, b = c.get(URL_DT, params={"year": 2026})
    thuc_te = thang_tu_api(b)
    ghi = [f"Shop mới: {len(thuc_te)} tháng, tổng={sum(thuc_te.values())}"]
    assert b.get("status") is True, b
    assert len(thuc_te) == 12 and all(v == 0 for v in thuc_te.values())

    # shop chỉ có đơn CHƯA Completed => vẫn 0
    st, b = c.post("/api/seller/san-pham", {
        "name": f"SP test {uuid.uuid4().hex[:6]}", "description": "test", "price": 100000,
        "old_price": None, "quantity": 5, "category_id": shop["category_id"], "emoji": "📦"})
    assert b.get("status"), f"Setup: thêm sản phẩm lỗi: {b.get('message')}"
    sp = chon_san_pham(c, min_qty=2)
    oid = tao_don(api("khach1"), [sp["id"]])[0]["order_id"]
    dua_den(c, oid, "Shipping")                                    # Pending->Confirmed->Shipping
    st, b = c.get(URL_DT, params={"year": datetime.now().year})
    thuc_te2 = thang_tu_api(b)
    ghi.append(f"Có đơn Shipping chưa Completed: tổng={sum(thuc_te2.values())}")
    actual("; ".join(ghi))
    assert b.get("status") is True and all(v == 0 for v in thuc_te2.values())


def test_tc237_chua_co_store_hoac_chua_login(api, actual):
    st1, b1 = api("seller_nostore").get(URL_DT, params={"year": 2026})
    st2, b2 = api().get(URL_DT, params={"year": 2026})
    actual(f"seller_nostore: HTTP {st1}, msg='{b1.get('message')}'; "
           f"không session: HTTP {st2}, msg='{b2.get('message')}'")
    assert st1 == 403 and b1.get("status") is False and not b1.get("data")
    assert "gian hàng" in (b1.get("message") or "").lower()
    assert st2 in (401, 403) and b2.get("status") is False and not b2.get("data")


def test_tc238_ownership_doanh_thu(api, actual):
    s1, s2 = api("seller1"), api("seller2")
    store2 = store_id_cua(s2)
    st0, goc = s1.get(URL_DT, params={"year": 2026})
    ghi = []
    for params in ({"year": 2026, "store_id": store2}, {"year": 2026, "storeId": store2}):
        st, b = s1.get(URL_DT, params=params)
        ghi.append(f"{params}: HTTP {st}, status={b.get('status')}")
        assert st < 500
        if b.get("status"):
            assert b["data"] == goc["data"], "Phải chỉ là doanh thu của chính shop seller1"
    st_s2, b_s2 = s2.get(URL_DT, params={"year": 2026})
    ghi.append(f"doanh thu shop2 thật={sum(thang_tu_api(b_s2).values())}, "
               f"seller1 nhận được={sum(thang_tu_api(goc).values())}")
    actual("; ".join(ghi))