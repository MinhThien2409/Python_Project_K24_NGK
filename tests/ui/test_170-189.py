"""
TC-170 -> TC-189: xóa giỏ hàng, đặt hàng, lịch sử đơn hàng.
(TC-169 đã có kết quả Pass trong Excel nên không viết lại.)

Dùng conftest.py của bạn: fixture `login(username, password)` và `actual("...")`.
Quy ước tên test: test_tcNNN_... để conftest tự ghi Pass/Fail + Actual result vào Excel.

Nguyên tắc: các case có thay đổi dữ liệu (xóa giỏ, đặt hàng) KHÔNG dùng khach1..5 trong seed
mà tạo khách hàng MỚI bằng /api/dang-ky (username ngẫu nhiên) để test chạy lại được nhiều lần
và không phá giỏ/đơn của tài khoản seed. Chỉ khach1 được dùng cho case chỉ đọc (TC-170, 187, 188).

Sản phẩm seed dùng để test (kho đủ lớn):
    4 Áo Hoodie (shop 2, kho 50)   6 Balo (shop 2, kho 40)
    7 Nồi chiên (shop 3, kho 12)   9 Sách Python (shop 3, kho 100, giá 120.000)
    3 MacBook (shop 1, kho 8)      -> dùng để thử đặt vượt kho
"""
import re
import uuid
from types import SimpleNamespace

import pytest
from playwright.sync_api import expect

PWD = "123456"
P_HOODIE, P_BALO, P_NOI, P_SACH, P_MACBOOK = 4, 6, 7, 9, 3
KHACH1_ID, KHACH2_ID = 6, 7


# ====================================================================== fixtures
@pytest.fixture
def new_customer(playwright, base_url):
    """new_customer() -> khách hàng mới đã đăng nhập: .api (APIRequestContext), .username, .uid."""
    ctxs = []

    def make():
        api = playwright.request.new_context(base_url=base_url)
        ctxs.append(api)
        username = f"tc_{uuid.uuid4().hex[:8]}"
        r = api.post("/api/dang-ky", data={
            "ten_user": "Khách Test Tự Động", "tendangnhap": username,
            "sdt": "0901234567", "mat_khau": PWD})
        assert r.json().get("status") is True, f"Đăng ký thất bại: {r.text()}"
        r = api.post("/api/dang-nhap", data={"tendangnhap": username, "mat_khau": PWD})
        j = r.json()
        assert j.get("status") is True, f"Đăng nhập thất bại: {r.text()}"
        return SimpleNamespace(api=api, username=username, uid=j["data"]["ma_user"])

    yield make
    for c in ctxs:
        c.dispose()


@pytest.fixture
def anon(playwright, base_url):
    """APIRequestContext chưa đăng nhập."""
    ctx = playwright.request.new_context(base_url=base_url)
    yield ctx
    ctx.dispose()


@pytest.fixture
def khach1(playwright, base_url):
    ctx = playwright.request.new_context(base_url=base_url)
    r = ctx.post("/api/dang-nhap", data={"tendangnhap": "khach1", "mat_khau": PWD})
    assert r.json().get("status") is True, r.text()
    yield ctx
    ctx.dispose()


@pytest.fixture
def login(page):
    """Ghi đè fixture `login` của conftest chỉ trong file này.
    Lý do: conftest dùng page.get_by_text("Đăng nhập").first -> khớp cả chữ "Chưa đăng nhập" ở
    topbar (get_by_text không phân biệt hoa/thường, topbar nằm trước nút đăng nhập trong DOM) nên
    đôi khi click trúng topbar, modal không mở, #loginUsername không hiện.
    Ở đây bấm thẳng #hdrAuthBtn và chờ modal mở."""
    def _login(username, password):
        page.goto("/")
        page.wait_for_function("typeof openAuthModal === 'function'")
        page.locator("#hdrAuthBtn").click()
        expect(page.locator("#authModal")).to_have_class(re.compile("show"))
        page.fill("#loginUsername", username)
        page.fill("#loginPass", password)
        page.click("#formLogin button[type='submit']")

    return _login


# ====================================================================== helpers API
def gia_sp(api, pid):
    return float(api.get(f"/api/products/{pid}").json()["data"]["price"])


def ton_kho(api, pid):
    return int(api.get(f"/api/products/{pid}").json()["data"]["quantity"])


def ten_sp(api, pid):
    return api.get(f"/api/products/{pid}").json()["data"]["name"]


def them_vao_gio(c, pid, qty):
    r = c.api.post("/api/gio-hang/them",
                   data={"ProductId": pid, "Quantity": qty, "UnitPrice": gia_sp(c.api, pid)})
    assert r.json().get("status") is True, f"Không thêm được SP {pid} vào giỏ: {r.text()}"


def id_trong_gio(c):
    j = c.api.get(f"/api/gio-hang/{c.uid}").json()
    return {int(i.get("ProductId") or i.get("product_id")) for i in (j.get("data") or [])}


def ds_don(c):
    j = c.api.get(f"/api/don-hang/cua-toi/{c.uid}").json()
    return j.get("data") or []


def dat_hang(c, items, **override):
    """Gọi API đặt hàng. items: list dict {ProductId, Quantity, ...}. Trả (http_status, json)."""
    payload = {
        "ReceiverName": "Nguyễn Văn A", "ReceiverPhone": "0901234567",
        "ShippingAddress": "1 Lê Lợi, Q1", "PaymentMethod": "COD", "ShippingFee": 25000,
        "Items": items,
    }
    payload.update(override)
    r = c.api.post("/api/don-hang/dat-hang", data=payload)
    return r.status, r.json()


def mo_gio(page):
    """Mở giỏ SAU KHI giỏ đã tải xong (badge > 0). openCart() chỉ vẽ giỏ 1 lần lúc mở nên nếu mở
    sớm hơn lúc loadCartFromServer() xong thì panel hiện 'đang trống' dù badge đã có số."""
    expect(page.locator("#hdrUserBtn")).to_be_visible()
    expect(page.locator("#cartBadge")).not_to_have_text("0")
    page.locator(".hdr-btn", has_text="Giỏ hàng").click()
    expect(page.locator("#cartItemsList input[type='checkbox']").first).to_be_visible()


def mo_checkout(page, login, c):
    """Đăng nhập UI bằng khách mới -> mở giỏ -> mở form thanh toán."""
    login(c.username, PWD)
    mo_gio(page)
    page.locator("#btnCheckoutTrigger").click()
    expect(page.locator("#checkoutModal")).to_have_class(re.compile("show"))


def dien_form(page, ten="Nguyễn Văn A", sdt="0901234567", dia_chi="1 Lê Lợi, Q1"):
    page.fill("#chkName", ten)
    page.fill("#chkPhone", sdt)
    page.fill("#chkAddress", dia_chi)


# =====================================================================
# TC-170  Xóa item không tồn tại trong giỏ   (TS-32)
# =====================================================================
def test_tc170_xoa_item_khong_ton_tai(khach1, actual):
    r = khach1.post("/api/gio-hang/xoa", data={"ProductId": 99999})
    j = r.json()
    actual(f"HTTP {r.status}, status={j.get('status')}, message='{j.get('message')}'")
    assert r.status < 500
    assert j["status"] is False


# =====================================================================
# TC-171  Giỏ không tồn tại   (TS-32)   (khách mới chưa từng thêm gì vào giỏ)
# =====================================================================
def test_tc171_xoa_item_gio_khong_ton_tai(new_customer, actual):
    c = new_customer()
    r = c.api.post("/api/gio-hang/xoa", data={"ProductId": P_HOODIE})
    j = r.json()
    actual(f"HTTP {r.status}, status={j.get('status')}, message='{j.get('message')}'")
    assert r.status < 500
    assert j["status"] is False


# =====================================================================
# TC-172  Chưa đăng nhập xóa item   (TS-32)
# =====================================================================
def test_tc172_xoa_item_chua_dang_nhap(anon, actual):
    r = anon.post("/api/gio-hang/xoa", data={"ProductId": P_HOODIE})
    j = r.json()
    actual(f"HTTP {r.status}, status={j.get('status')}, message='{j.get('message')}'")
    assert r.status in (401, 403)
    assert j["status"] is False


# =====================================================================
# TC-173  Xóa toàn bộ giỏ có dữ liệu   (TS-33)
# =====================================================================
def test_tc173_xoa_toan_bo_gio_co_du_lieu(page, login, base_url, new_customer, actual):
    c = new_customer()
    them_vao_gio(c, P_HOODIE, 1)
    them_vao_gio(c, P_BALO, 1)
    assert len(id_trong_gio(c)) == 2

    login(c.username, PWD)
    expect(page.locator("#hdrUserBtn")).to_be_visible()
    co_nut = page.get_by_text("Xóa toàn bộ").count() > 0

    r = page.request.post(f"{base_url}/api/gio-hang/xoa-tat-ca")  # cùng session với trình duyệt
    j = r.json()
    con_lai = id_trong_gio(c)

    page.reload()
    page.locator(".hdr-btn", has_text="Giỏ hàng").click()
    giao_dien_trong = page.locator("#cartItemsList").get_by_text("Giỏ hàng của bạn đang trống").count() == 1

    actual(f"UI có nút 'Xóa toàn bộ giỏ hàng'={co_nut} (test gọi API xoa-tat-ca); "
           f"status={j.get('status')}; item còn lại trong giỏ={len(con_lai)}; UI hiển thị trống={giao_dien_trong}")
    assert j["status"] is True
    assert con_lai == set()
    assert giao_dien_trong


# =====================================================================
# TC-174  Xóa giỏ rỗng   (TS-33)
# =====================================================================
def test_tc174_xoa_gio_rong(new_customer, actual):
    # Trường hợp 1: giỏ ĐÃ CÓ nhưng không còn item -> xóa tiếp phải xử lý an toàn (thành công)
    c = new_customer()
    them_vao_gio(c, P_SACH, 1)
    assert c.api.post("/api/gio-hang/xoa-tat-ca").json()["status"] is True  # làm giỏ rỗng
    r = c.api.post("/api/gio-hang/xoa-tat-ca")
    j = r.json()

    # Trường hợp 2: user CHƯA TỪNG có dòng giỏ nào -> chỉ cần không lỗi 500 và có thông báo rõ ràng
    c2 = new_customer()
    r2 = c2.api.post("/api/gio-hang/xoa-tat-ca")
    j2 = r2.json()

    actual(f"Giỏ rỗng (đã có giỏ): HTTP {r.status}, status={j.get('status')}, message='{j.get('message')}'; "
           f"Chưa có giỏ: HTTP {r2.status}, status={j2.get('status')}, message='{j2.get('message')}'")
    assert r.status < 500 and j["status"] is True
    assert r2.status < 500 and str(j2.get("message", "")).strip() != ""


# =====================================================================
# TC-175  Chưa đăng nhập xóa toàn bộ giỏ   (TS-33)
# =====================================================================
def test_tc175_xoa_toan_bo_chua_dang_nhap(anon, actual):
    r = anon.post("/api/gio-hang/xoa-tat-ca")
    j = r.json()
    actual(f"HTTP {r.status}, status={j.get('status')}, message='{j.get('message')}'")
    assert r.status in (401, 403)
    assert j["status"] is False


# =====================================================================
# TC-176  Ownership xóa toàn bộ giỏ   (TS-33)
# =====================================================================
def test_tc176_ownership_xoa_toan_bo_gio(new_customer, actual):
    a, b = new_customer(), new_customer()
    them_vao_gio(a, P_HOODIE, 1)
    them_vao_gio(b, P_BALO, 1)

    r = a.api.post("/api/gio-hang/xoa-tat-ca", data={"user_id": b.uid, "UserId": b.uid})
    gio_b = id_trong_gio(b)
    actual(f"HTTP {r.status}; giỏ của B sau khi A gọi xóa với user_id của B: {sorted(gio_b)} (kỳ vọng còn SP {P_BALO})")
    assert r.status < 500
    assert gio_b == {P_BALO}, "Giỏ của người dùng khác bị xóa!"


# =====================================================================
# TC-177  Đặt hàng hợp lệ một shop, chỉ đặt món được tick   (TS-34)
# =====================================================================
def test_tc177_dat_hang_mot_shop_chon_mot_phan(page, login, new_customer, actual):
    c = new_customer()
    them_vao_gio(c, P_HOODIE, 2)  # A: được chọn
    them_vao_gio(c, P_BALO, 1)    # B: bỏ chọn (cùng shop 2)
    kho_a, kho_b = ton_kho(c.api, P_HOODIE), ton_kho(c.api, P_BALO)

    login(c.username, PWD)
    mo_gio(page)
    # Bỏ tick sản phẩm B (Balo)
    page.locator(f"#cartItemsList input[onchange='toggleCartItemSelection({P_BALO})']").click()
    page.locator("#btnCheckoutTrigger").click()
    expect(page.locator("#checkoutModal")).to_have_class(re.compile("show"))

    dien_form(page)
    page.select_option("#chkPayment", "COD")
    page.locator("#checkoutModal button[type='submit']").click()

    expect(page.locator("#invoiceModal")).to_have_class(re.compile("show"))  # hiển thị hóa đơn

    don = ds_don(c)
    ten_a = ten_sp(c.api, P_HOODIE)
    ten_don = {i["ProductName"] for o in don for i in o.get("Items", [])}
    kho_a2, kho_b2 = ton_kho(c.api, P_HOODIE), ton_kho(c.api, P_BALO)
    gio = id_trong_gio(c)
    actual(f"Số đơn={len(don)}, trạng thái={[o['Status'] for o in don]}, SP trong đơn={sorted(ten_don)}; "
           f"kho A {kho_a}->{kho_a2}, kho B {kho_b}->{kho_b2}; giỏ còn={sorted(gio)}")

    assert len(don) == 1 and don[0]["Status"] == "Pending"
    assert ten_don == {ten_a}                      # chỉ có SP được chọn
    assert kho_a2 == kho_a - 2                     # trừ đúng số lượng đã đặt
    assert kho_b2 == kho_b                         # SP không chọn không bị trừ
    assert gio == {P_BALO}                         # chỉ xóa món đã đặt khỏi giỏ


# =====================================================================
# TC-178  Đặt hàng từ nhiều shop: tách đơn theo shop, rollback khi một shop lỗi   (TS-34)
# =====================================================================
def test_tc178_dat_hang_nhieu_shop(new_customer, actual):
    c = new_customer()
    them_vao_gio(c, P_HOODIE, 1)  # shop 2
    them_vao_gio(c, P_NOI, 1)     # shop 3
    kho = {p: ton_kho(c.api, p) for p in (P_HOODIE, P_NOI)}

    code, j = dat_hang(c, [{"ProductId": P_HOODIE, "Quantity": 1}, {"ProductId": P_NOI, "Quantity": 1}])
    don = ds_don(c)
    tap_sp = sorted(sorted({i["ProductName"] for i in o.get("Items", [])}) for o in don)
    actual(f"HTTP {code}, status={j.get('status')}, số đơn tạo={len(don)}, SP theo từng đơn={tap_sp}")

    assert j["status"] is True
    assert len(don) == 2, "Đơn phải tách theo từng shop"
    assert all(len({i["ProductName"] for i in o["Items"]}) == 1 for o in don)
    for o in don:  # tổng tiền từng đơn = tạm tính + ship - giảm giá, tạm tính tính từ giá DB
        sub = sum(float(i["UnitPrice"]) * int(i["Quantity"]) for i in o["Items"])
        assert float(o["SubTotal"]) == pytest.approx(sub)
        assert float(o["TotalAmount"]) == pytest.approx(
            float(o["SubTotal"]) + float(o["ShippingFee"]) - float(o["DiscountAmount"] or 0))
    for p in (P_HOODIE, P_NOI):
        assert ton_kho(c.api, p) == kho[p] - 1


def test_tc178_rollback_khi_mot_shop_loi(new_customer, actual):
    c = new_customer()
    them_vao_gio(c, P_HOODIE, 1)
    them_vao_gio(c, P_MACBOOK, 1)
    kho = {p: ton_kho(c.api, p) for p in (P_HOODIE, P_MACBOOK)}

    # Shop 2 hợp lệ, shop 1 đặt vượt kho -> toàn bộ phải thất bại
    code, j = dat_hang(c, [{"ProductId": P_HOODIE, "Quantity": 1},
                           {"ProductId": P_MACBOOK, "Quantity": 9999}])
    don, gio = ds_don(c), id_trong_gio(c)
    actual(f"HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; số đơn={len(don)}; "
           f"kho hoodie {kho[P_HOODIE]}->{ton_kho(c.api, P_HOODIE)}; giỏ còn={sorted(gio)}")

    assert j["status"] is False
    assert len(don) == 0, "Có đơn dở dang sau khi một shop lỗi"
    assert ton_kho(c.api, P_HOODIE) == kho[P_HOODIE]
    assert ton_kho(c.api, P_MACBOOK) == kho[P_MACBOOK]
    assert gio == {P_HOODIE, P_MACBOOK}


# =====================================================================
# TC-179  Thiếu thông tin người nhận   (TS-34)
# =====================================================================
def test_tc179_thieu_thong_tin_nguoi_nhan(page, login, new_customer, actual):
    c = new_customer()
    them_vao_gio(c, P_SACH, 1)

    # 1) Giao diện: bỏ trống cả 3 ô -> không được gửi yêu cầu đặt hàng
    cac_request = []
    page.on("request", lambda r: cac_request.append(r.url) if "/api/don-hang/dat-hang" in r.url else None)
    mo_checkout(page, login, c)
    dien_form(page, ten="", sdt="", dia_chi="")
    page.locator("#checkoutModal button[type='submit']").click()
    page.wait_for_timeout(500)
    ui_chan = len(cac_request) == 0 and "show" in (page.locator("#checkoutModal").get_attribute("class") or "")

    # 2) API: từng trường bị rỗng đều bị từ chối
    ket_qua = []
    for ten, sdt, dc in [("", "0901234567", "1 Lê Lợi"), ("Nguyễn Văn A", "", "1 Lê Lợi"), ("Nguyễn Văn A", "0901234567", "")]:
        code, j = dat_hang(c, [{"ProductId": P_SACH, "Quantity": 1}],
                           ReceiverName=ten, ReceiverPhone=sdt, ShippingAddress=dc)
        ket_qua.append((code, j.get("status")))
    don = ds_don(c)
    actual(f"UI chặn gửi form trống={ui_chan}; API (HTTP, status)={ket_qua}; số đơn tạo={len(don)}")

    assert ui_chan
    assert all(code < 500 and st is False for code, st in ket_qua)
    assert len(don) == 0


# =====================================================================
# TC-180  SĐT người nhận sai format   (TS-34)
# =====================================================================
@pytest.mark.parametrize("sdt", ["123", "abcdefghij"])
def test_tc180_sdt_nguoi_nhan_sai_format(page, login, new_customer, actual, sdt):
    c = new_customer()
    them_vao_gio(c, P_SACH, 1)

    mo_checkout(page, login, c)
    dien_form(page, sdt=sdt)
    page.locator("#checkoutModal button[type='submit']").click()
    toast = page.locator("#toast")
    expect(toast).to_contain_text("không hợp lệ")
    toast_text = toast.inner_text()

    code, j = dat_hang(c, [{"ProductId": P_SACH, "Quantity": 1}], ReceiverPhone=sdt)
    don = ds_don(c)
    actual(f"UI toast='{toast_text}'; API HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; số đơn={len(don)}")

    assert code < 500 and j["status"] is False
    assert len(don) == 0


# =====================================================================
# TC-181  Phương thức thanh toán không hợp lệ   (TS-34)
# =====================================================================
@pytest.mark.parametrize("pttt", ["BITCOIN", ""])
def test_tc181_phuong_thuc_thanh_toan_khong_hop_le(new_customer, actual, pttt):
    c = new_customer()
    them_vao_gio(c, P_SACH, 1)
    kho = ton_kho(c.api, P_SACH)

    code, j = dat_hang(c, [{"ProductId": P_SACH, "Quantity": 1}], PaymentMethod=pttt)
    don, kho2 = ds_don(c), ton_kho(c.api, P_SACH)
    actual(f"PaymentMethod='{pttt}': HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; "
           f"số đơn={len(don)}; kho {kho}->{kho2}")

    assert code < 500
    assert j["status"] is False
    assert len(don) == 0
    assert kho2 == kho


# =====================================================================
# TC-182  Danh sách items trống   (TS-34)
# =====================================================================
def test_tc182_items_trong(new_customer, actual):
    c = new_customer()
    code, j = dat_hang(c, [])
    don = ds_don(c)
    actual(f"HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; số đơn={len(don)}")
    assert code < 500
    assert j["status"] is False
    assert len(don) == 0


# =====================================================================
# TC-183  Tổng tiền client gửi <= 0   (TS-34)
# =====================================================================
@pytest.mark.parametrize("tong", [0, -1000])
def test_tc183_tong_tien_client_khong_hop_le(new_customer, actual, tong):
    c = new_customer()
    them_vao_gio(c, P_SACH, 2)
    gia = gia_sp(c.api, P_SACH)

    code, j = dat_hang(
        c, [{"ProductId": P_SACH, "Quantity": 2, "UnitPrice": tong, "TotalPrice": tong}],
        SubTotal=tong, TotalAmount=tong, DiscountAmount=0)
    don = ds_don(c)

    if j.get("status"):  # chấp nhận đơn thì tổng tiền phải do backend tính lại từ giá DB
        o = don[0]
        mong_doi = gia * 2 + float(o["ShippingFee"]) - float(o["DiscountAmount"] or 0)
        actual(f"Gửi tổng={tong}: backend tạo đơn, SubTotal={o['SubTotal']}, TotalAmount={o['TotalAmount']} "
               f"(tính từ DB={mong_doi})")
        assert len(don) == 1
        assert float(o["TotalAmount"]) > 0
        assert float(o["SubTotal"]) == pytest.approx(gia * 2)
        assert float(o["TotalAmount"]) == pytest.approx(mong_doi)
    else:  # hoặc từ chối hẳn
        actual(f"Gửi tổng={tong}: backend từ chối ('{j.get('message')}'), số đơn={len(don)}")
        assert code < 500 and len(don) == 0


# =====================================================================
# TC-184  Phí vận chuyển âm   (TS-34)
# =====================================================================
def test_tc184_phi_van_chuyen_am(new_customer, actual):
    c = new_customer()
    them_vao_gio(c, P_SACH, 1)
    code, j = dat_hang(c, [{"ProductId": P_SACH, "Quantity": 1}], ShippingFee=-30000)
    don = ds_don(c)
    actual(f"HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; số đơn={len(don)}")
    assert code < 500
    assert j["status"] is False or all(float(o["ShippingFee"]) >= 0 for o in don)
    assert all(float(o["ShippingFee"]) >= 0 for o in don)  # không bao giờ lưu phí âm


# =====================================================================
# TC-185  Sản phẩm hết hàng / không tồn tại   (TS-34)
# =====================================================================
@pytest.mark.parametrize("ten_ca,pid,qty", [
    ("khong_ton_tai", 99999, 1),
    ("vuot_ton_kho", P_MACBOOK, 9999),  # seed không có SP tồn 0, dùng số lượng vượt kho tương đương
])
def test_tc185_san_pham_het_hang_hoac_khong_ton_tai(new_customer, actual, ten_ca, pid, qty):
    c = new_customer()
    them_vao_gio(c, P_SACH, 1)  # giỏ có hàng hợp lệ để chắc chắn lỗi đến từ SP kia
    kho = ton_kho(c.api, P_MACBOOK)

    code, j = dat_hang(c, [{"ProductId": pid, "Quantity": qty}])
    don = ds_don(c)
    actual(f"[{ten_ca}] HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; "
           f"số đơn={len(don)}; kho MacBook {kho}->{ton_kho(c.api, P_MACBOOK)}")

    assert code < 500
    assert j["status"] is False
    assert len(don) == 0
    assert ton_kho(c.api, P_MACBOOK) == kho


# =====================================================================
# TC-186  Tạo đơn thất bại giữa chừng -> rollback   (TS-34)
# =====================================================================
def test_tc186_tao_don_that_bai_rollback(new_customer, actual):
    """Không ngắt được DB thật từ test tự động. Mô phỏng: đơn có 1 SP hợp lệ + 1 SP lỗi (không tồn tại)
    nằm sau SP hợp lệ -> giao dịch phải thất bại toàn bộ, không đơn dở dang, kho và giỏ giữ nguyên.
    Kịch bản 'ngắt DB' thật cần kiểm tra thủ công / test tích hợp riêng."""
    c = new_customer()
    them_vao_gio(c, P_HOODIE, 1)
    them_vao_gio(c, P_SACH, 1)
    kho = {p: ton_kho(c.api, p) for p in (P_HOODIE, P_SACH)}

    code, j = dat_hang(c, [{"ProductId": P_HOODIE, "Quantity": 1},
                           {"ProductId": P_SACH, "Quantity": 1},
                           {"ProductId": 99999, "Quantity": 1}])
    don, gio = ds_don(c), id_trong_gio(c)
    kho2 = {p: ton_kho(c.api, p) for p in (P_HOODIE, P_SACH)}
    actual(f"(Mô phỏng lỗi giữa giao dịch) HTTP {code}, status={j.get('status')}, message='{j.get('message')}'; "
           f"số đơn={len(don)}; kho {kho}->{kho2}; giỏ còn={sorted(gio)}")

    assert code < 500
    assert j["status"] is False
    assert len(don) == 0
    assert kho2 == kho
    assert gio == {P_HOODIE, P_SACH}


# =====================================================================
# TC-187  Customer xem lịch sử đơn của mình   (TS-35)
# =====================================================================
def test_tc187_xem_lich_su_don_cua_minh(page, login, base_url, actual):
    login("khach1", PWD)
    expect(page.locator("#hdrHistoryBtn")).to_be_visible()

    j = page.request.get(f"{base_url}/api/don-hang/cua-toi/{KHACH1_ID}").json()
    don_api = j.get("data") or []
    assert don_api, "khach1 chưa có đơn nào trong DB (seed có đơn #1 Completed)"

    page.locator("#hdrHistoryBtn").click()
    the_don = page.locator("#orderHistoryContent span", has_text=re.compile(r"^Đơn #\d+$"))
    expect(the_don.first).to_be_visible()
    ids_ui = [int(t.replace("Đơn #", "")) for t in the_don.all_inner_texts()]
    ids_api = [int(o["OrderId"]) for o in don_api]
    thoi_gian = [str(o["CreatedAt"]) for o in don_api]
    nhan = {"Pending": "Chờ duyệt", "Confirmed": "Đã xác nhận", "Shipping": "Đang giao",
            "Completed": "Hoàn thành", "Cancelled": "Đã hủy"}
    noi_dung = page.locator("#orderHistoryContent").inner_text()
    actual(f"UI hiển thị đơn {ids_ui}; API trả {ids_api}; "
           f"mới nhất trước={thoi_gian == sorted(thoi_gian, reverse=True)}")

    assert ids_ui == ids_api                              # đủ đơn, đúng thứ tự
    assert thoi_gian == sorted(thoi_gian, reverse=True)   # sắp xếp theo thời gian
    assert all(nhan[o["Status"]] in noi_dung for o in don_api)  # có trạng thái
    assert all(int(o.get("UserId", KHACH1_ID)) == KHACH1_ID for o in don_api)


# =====================================================================
# TC-188  Customer xem lịch sử đơn của user khác   (TS-35)
# =====================================================================
def test_tc188_xem_lich_su_don_user_khac(khach1, actual):
    r = khach1.get(f"/api/don-hang/cua-toi/{KHACH2_ID}")
    j = r.json()
    actual(f"HTTP {r.status}, status={j.get('status')}, message='{j.get('message')}', "
           f"số đơn trả về={len(j.get('data') or [])}")
    assert r.status == 403
    assert j["status"] is False
    assert not j.get("data")


# =====================================================================
# TC-189  Chưa đăng nhập xem lịch sử đơn   (TS-35)
# =====================================================================
def test_tc189_xem_lich_su_don_chua_dang_nhap(anon, actual):
    r = anon.get(f"/api/don-hang/cua-toi/{KHACH1_ID}")
    j = r.json()
    actual(f"HTTP {r.status}, status={j.get('status')}, message='{j.get('message')}'")
    assert r.status in (401, 403)
    assert j["status"] is False
    assert not j.get("data")