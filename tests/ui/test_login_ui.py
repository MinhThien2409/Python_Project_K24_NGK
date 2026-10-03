"""
Test tự động cho các test case còn thiếu, đếm từ dưới lên (TC-269 -> TC-258).

Yêu cầu fixture trong conftest.py (giống test_tc009 của bạn):
    page  : Playwright page (đã mở base URL của app)
    login : login(username, password)  -> đăng nhập qua modal

Các selector nằm trong dict SEL bên dưới. Mình chưa thấy index.html/main.js nên
phải đoán theo nhãn tiếng Việt trong file Excel. Nếu locator nào sai, chỉ cần
sửa ở một chỗ duy nhất là SEL.
"""
import re

import pytest
from playwright.sync_api import expect

# ---------------------------------------------------------------- selector
SEL = {
    "toast": "#toast",
    "logout_btn": "text=Đăng xuất",
    # Kênh Người Bán
    "seller_tabs": ["Tổng quan", "Sản phẩm", "Nhập hàng", "Đơn hàng", "Trang shop", "Giá bán"],
    "seller_tab": lambda page, name: page.locator(".seller-menu, .sidebar, nav").get_by_text(name, exact=True).first,
    "seller_active_tab": ".seller-menu .active, .sidebar .active, nav .active",
    "seller_pane_visible": ".tab-pane.active, .pane.active, .seller-pane.active",
    # modal
    "modal_close": ".modal .close, .modal-close, .modal button:has-text('✕')",
    # form sản phẩm
    "btn_add_product": "text=+ Thêm sản phẩm",
    "inp_product_name": "#productName, input[name='name']",
    "inp_product_price": "#productPrice, input[name='price']",
    "inp_product_original": "#productOriginalPrice, input[name='original_price'], input[name='oldPrice']",
    "inp_product_emoji": "#productEmoji, input[name='emoji']",
    "btn_save": "button:has-text('Lưu')",
    "product_modal_title": ".modal h2, .modal h3, .modal-title",
    # tab Nhập hàng
    "import_search": "#importSearch, #importTable-search, input[placeholder*='Tìm']",
    "import_row": "#importTable tbody tr, #tab-import tbody tr",
    "import_history": "#importHistory, #import-history",
    # tab Trang shop
    "shop_name": "#shopName, input[name='shop_name'], input[name='name']",
    "shop_desc": "#shopDesc, textarea[name='description'], textarea",
    "shop_image": "#shopImage, input[name='image'], input[name='logo']",
}

SELLER = ("seller1", "123456")
CUSTOMER = ("khach1", "123456")
MANAGER = ("quanly1", "123456")
ADMIN = ("admin", "123456")


def _open_seller_tab(page, name):
    SEL["seller_tab"](page, name).click()


# =====================================================================
# TC-269  Chống XSS ở tên shop và giới thiệu shop  (TS-54)
# =====================================================================
XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<SCRIPT>alert(1)</SCRIPT>",
    "<img src=x onerror=alert(1)>",
    '<img src=x ONERROR =alert(1)>',
    "javascript:alert(1)",
]
XSS_IMAGE_URLS = ["javascript:alert(1)", "data:text/html,<script>alert(1)</script>"]


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_tc269_chong_xss_ten_shop_va_gioi_thieu(page, login, payload):
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))

    login(*SELLER)
    _open_seller_tab(page, "Trang shop")

    page.locator(SEL["shop_name"]).fill(payload[:150])
    page.locator(SEL["shop_desc"]).fill(payload[:500])
    page.locator(SEL["btn_save"]).first.click()
    page.wait_for_timeout(500)

    # Xem lại ở Tổng quan -> không được có alert chạy
    _open_seller_tab(page, "Tổng quan")
    page.wait_for_timeout(500)

    assert dialogs == [], f"XSS đã thực thi, alert: {dialogs}"
    # Chuỗi phải hiển thị dạng text hoặc đã bị loại, không được sinh ra thẻ <script>/<img> mới
    assert page.locator("img[src='x']").count() == 0


@pytest.mark.parametrize("url", XSS_IMAGE_URLS)
def test_tc269_chong_xss_url_anh(page, login, url):
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))

    login(*SELLER)
    _open_seller_tab(page, "Trang shop")

    img = page.locator(SEL["shop_image"])
    if img.count() == 0:
        pytest.skip("Form Trang shop không có ô URL ảnh, cần sửa SEL['shop_image']")
    img.first.fill(url)
    page.locator(SEL["btn_save"]).first.click()
    page.wait_for_timeout(500)

    assert dialogs == []
    assert page.locator("img[src^='javascript:'], img[src^='data:text/html']").count() == 0


# =====================================================================
# TC-268  Khách thấy tồn kho mới sau khi Seller nhập hàng  (TS-53)
# =====================================================================
def test_tc268_khach_thay_kho_moi_sau_nhap_hang(browser, base_url):
    """Cần 2 context riêng (Seller và Customer ở 2 trình duyệt khác nhau)."""
    seller_ctx = browser.new_context()
    cust_ctx = browser.new_context()
    sp, cp = seller_ctx.new_page(), cust_ctx.new_page()
    try:
        # --- Seller nhập hàng cho sản phẩm tồn 0
        sp.goto(base_url)
        _quick_login(sp, *SELLER)
        _open_seller_tab(sp, "Nhập hàng")
        sp.locator(SEL["import_search"]).first.fill("hết hàng")  # sửa theo tên SP tồn 0 thật
        row = sp.locator(SEL["import_row"]).first
        row.locator("input").nth(0).fill("10")  # số lượng
        row.locator("input").nth(1).fill("100000")  # giá nhập
        row.get_by_role("button", name=re.compile("Nhập", re.I)).click()
        expect(sp.locator(SEL["toast"])).to_be_visible()

        # --- Customer thấy còn hàng và thêm đủ 10 vào giỏ
        cp.goto(base_url)
        _quick_login(cp, *CUSTOMER)
        cp.get_by_text("hết hàng").first.click()
        expect(cp.get_by_text(re.compile("Hết hàng", re.I))).to_have_count(0)
        cp.locator("input[type='number']").first.fill("10")
        cp.get_by_role("button", name=re.compile("Thêm vào giỏ", re.I)).click()
        expect(cp.locator(SEL["toast"])).not_to_contain_text("vượt")
    finally:
        seller_ctx.close()
        cust_ctx.close()


def _quick_login(page, user, pwd):
    page.get_by_text("Đăng nhập").first.click()
    page.locator("input[type='text']:visible").first.fill(user)
    page.locator("input[type='password']:visible").first.fill(pwd)
    page.get_by_role("button", name=re.compile("Đăng nhập")).last.click()


# =====================================================================
# TC-267  Nhập hàng: thành tiền trên từng dòng  (TS-53)
# =====================================================================
def test_tc267_nhap_hang_thanh_tien(page, login):
    login(*SELLER)
    _open_seller_tab(page, "Nhập hàng")

    row = page.locator(SEL["import_row"]).first
    qty, price = row.locator("input").nth(0), row.locator("input").nth(1)

    # Mặc định số lượng 10
    expect(qty).to_have_value("10")

    # Đủ dữ liệu -> Thành tiền = 20 * 300000 = 6.000.000
    qty.fill("20")
    price.fill("300000")
    expect(row).to_contain_text(re.compile(r"6[.,]?000[.,]?000"))

    # Thiếu giá hoặc số lượng -> thông báo gợi ý
    price.fill("")
    expect(row).to_contain_text("Nhập giá & số lượng để xem thành tiền")
    price.fill("300000")
    qty.fill("")
    expect(row).to_contain_text("Nhập giá & số lượng để xem thành tiền")

    # Không còn hiển thị Lợi nhuận
    price.fill("99999999")
    qty.fill("10")
    expect(page.get_by_text("Lợi nhuận")).to_have_count(0)


# =====================================================================
# TC-266  Lọc ở tab Nhập hàng, lịch sử nhập độc lập  (TS-53)
# =====================================================================
def test_tc266_loc_nhap_hang_lich_su_doc_lap(page, login):
    login(*SELLER)
    _open_seller_tab(page, "Nhập hàng")

    history = page.locator(SEL["import_history"])
    history_rows_before = history.locator("tr").count()

    for label in ["Hết hàng", "Sắp hết", "Còn hàng", "Tất cả"]:
        page.get_by_role("button", name=re.compile(label, re.I)).first.click()
        page.wait_for_timeout(200)
        # Lịch sử nhập hàng phía dưới không bị lọc theo
        assert history.locator("tr").count() == history_rows_before

    page.locator(SEL["import_search"]).first.fill("zzzzzz")
    page.wait_for_timeout(300)
    assert history.locator("tr").count() == history_rows_before


# =====================================================================
# TC-265  Thêm sản phẩm với giá gốc bất thường  (TS-52)
# =====================================================================
@pytest.mark.parametrize("name,original", [("SP gia goc nho hon", "400000"), ("SP bo trong gia goc", "")])
def test_tc265_gia_goc_bat_thuong(page, login, name, original):
    login(*SELLER)
    _open_seller_tab(page, "Sản phẩm")
    page.locator(SEL["btn_add_product"]).click()

    page.locator(SEL["inp_product_name"]).fill(name)
    page.locator(SEL["inp_product_price"]).fill("500000")
    if original:
        page.locator(SEL["inp_product_original"]).fill(original)
    page.locator(SEL["btn_save"]).first.click()

    # Ghi nhận hành vi thực tế: BUS không chặn, sản phẩm vẫn được lưu
    expect(page.locator(SEL["toast"])).to_be_visible()
    expect(page.get_by_text(name)).to_be_visible()


# =====================================================================
# TC-264  Modal thêm/sửa sản phẩm  (TS-52)
# =====================================================================
def test_tc264_modal_them_sua_san_pham(page, login):
    login(*SELLER)
    _open_seller_tab(page, "Sản phẩm")

    page.locator(SEL["btn_add_product"]).click()
    expect(page.locator(SEL["product_modal_title"]).first).to_contain_text("Thêm sản phẩm vào gian hàng")
    page.locator(SEL["modal_close"]).first.click()

    page.get_by_role("button", name=re.compile("Sửa")).first.click()
    expect(page.locator(SEL["product_modal_title"]).first).to_contain_text("Chỉnh sửa sản phẩm")
    expect(page.locator(SEL["inp_product_name"])).not_to_have_value("")
    stock = page.locator("#productStock, input[name='stock']")
    expect(stock).to_be_disabled()  # Tồn kho chỉ đọc
    page.locator(SEL["modal_close"]).first.click()

    # Mở lại form Thêm: các ô phải trống
    page.locator(SEL["btn_add_product"]).click()
    expect(page.locator(SEL["inp_product_name"])).to_have_value("")
    expect(page.locator(SEL["inp_product_price"])).to_have_value("")
    page.locator(SEL["modal_close"]).first.click()


# =====================================================================
# TC-263  Chọn emoji và emoji mặc định  (TS-52)
# =====================================================================
def test_tc263_emoji_mac_dinh(page, login):
    login(*SELLER)
    _open_seller_tab(page, "Sản phẩm")
    page.locator(SEL["btn_add_product"]).click()

    page.locator(SEL["inp_product_name"]).fill("SP emoji test")
    page.locator(SEL["inp_product_price"]).fill("100000")
    # Không chọn emoji
    page.locator(SEL["btn_save"]).first.click()

    row = page.locator("tr", has_text="SP emoji test").first
    expect(row).to_contain_text("📦")


# =====================================================================
# TC-262  Form sản phẩm: tính giá và giảm giá trực tiếp  (TS-52)
# =====================================================================
def test_tc262_tinh_gia_giam_gia(page, login):
    login(*SELLER)
    _open_seller_tab(page, "Sản phẩm")
    page.locator(SEL["btn_add_product"]).click()

    # Bấm -10% khi chưa nhập giá gốc
    page.get_by_role("button", name="-10%").click()
    expect(page.locator(SEL["toast"])).to_contain_text("Nhập giá gốc trước để giảm giá theo %!")

    # Có giá gốc -> hiện khối Thực nhận, bấm -10% => 450000
    page.locator(SEL["inp_product_original"]).fill("500000")
    expect(page.get_by_text(re.compile("Thực nhận"))).to_be_visible()
    page.get_by_role("button", name="-10%").click()
    expect(page.locator(SEL["inp_product_price"])).to_have_value(re.compile(r"450[.,]?000"))

    # Giá bán >= giá gốc -> dòng cảnh báo
    page.locator(SEL["inp_product_price"]).fill("600000")
    expect(page.get_by_text(re.compile("không hiện giảm giá"))).to_be_visible()


# =====================================================================
# TC-261  Lọc và hiển thị danh sách sản phẩm của Seller  (TS-52)
# =====================================================================
def test_tc261_loc_san_pham_seller(page, login):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    login(*SELLER)
    _open_seller_tab(page, "Sản phẩm")

    rows = page.locator("#sellerProductsTable tbody tr, #tab-products tbody tr")
    total = rows.count()
    assert total > 0

    def click_filter(label):
        page.get_by_role("button", name=re.compile(label, re.I)).first.click()
        page.wait_for_timeout(200)

    click_filter("Hết hàng")
    for i in range(rows.count()):
        expect(rows.nth(i)).to_contain_text("Hết hàng")

    click_filter("Sắp hết")
    for i in range(rows.count()):
        expect(rows.nth(i)).to_contain_text("Sắp hết")

    click_filter("Tất cả")
    assert rows.count() == total  # không nhân đôi hàng

    # Tìm không khớp
    page.get_by_placeholder(re.compile("Tìm", re.I)).first.fill("zzzzzz")
    expect(page.get_by_text("Không tìm thấy kết quả")).to_be_visible()

    # Chuyển tab nhiều lần, console không lỗi JS
    for name in ["Nhập hàng", "Sản phẩm", "Tổng quan", "Sản phẩm"]:
        _open_seller_tab(page, name)
    assert errors == [], errors


# =====================================================================
# TC-260  Đóng modal bằng ✕ và hành vi toast  (TS-51)
# =====================================================================
def test_tc260_dong_modal_va_toast(page):
    # Modal Đăng nhập: mở -> đóng bằng ✕ -> mở lại
    page.get_by_text("Đăng nhập").first.click()
    modal = page.locator(".modal:visible, .modal.show, .modal.active").first
    expect(modal).to_be_visible()
    page.locator(SEL["modal_close"]).first.click()
    expect(modal).not_to_be_visible()
    page.get_by_text("Đăng nhập").first.click()
    expect(modal).to_be_visible()

    # Toast: gây 2 thông báo liên tiếp, tự ẩn ~2,5 giây
    page.get_by_role("button", name=re.compile("Đăng nhập")).last.click()  # form trống -> validation/toast
    toast = page.locator(SEL["toast"])
    page.locator("input[type='text']:visible").first.fill("sai")
    page.locator("input[type='password']:visible").first.fill("sai")
    page.get_by_role("button", name=re.compile("Đăng nhập")).last.click()
    expect(toast).to_be_visible()
    page.wait_for_timeout(3500)
    expect(toast).not_to_be_visible()

    # Bấm ra ngoài modal: chỉ ghi nhận hành vi thực tế (không assert đóng/không đóng)
    page.mouse.click(5, 5)


# =====================================================================
# TC-259  Điều hướng 6 tab của Kênh Người Bán  (TS-51)
# =====================================================================
@pytest.mark.parametrize("tab", ["Tổng quan", "Sản phẩm", "Nhập hàng", "Đơn hàng", "Trang shop", "Giá bán"])
def test_tc259_dieu_huong_tab_seller(page, login, tab):
    login(*SELLER)
    _open_seller_tab(page, tab)

    expect(page.locator(SEL["seller_active_tab"]).first).to_contain_text(tab)
    # Chỉ một pane hiển thị
    assert page.locator(SEL["seller_pane_visible"]).count() == 1


# =====================================================================
# TC-258  Menu và màn hình mặc định theo vai trò Admin/Quản lý  (TS-51)
# =====================================================================
def test_tc258_menu_admin(page, login):
    login(*ADMIN)
    expect(page.get_by_text("Quản lý tài khoản").first).to_be_visible()
    expect(page.get_by_text("Quản lý danh mục")).to_have_count(0)
    expect(page.get_by_text("Duyệt người bán")).to_have_count(0)
    expect(page.locator(SEL["logout_btn"]).first).to_be_visible()


def test_tc258_menu_quan_ly(page, login):
    login(*MANAGER)
    for item in ["Quản lý danh mục", "Duyệt người bán", "tài khoản"]:
        expect(page.get_by_text(re.compile(item, re.I)).first).to_be_visible()
    # Mặc định mở "Quản lý danh mục"
    expect(page.locator(".active").first).to_contain_text("danh mục")
    expect(page.locator(SEL["logout_btn"]).first).to_be_visible()