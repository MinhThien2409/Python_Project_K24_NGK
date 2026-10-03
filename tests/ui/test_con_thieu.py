"""
Test tự động cho các test case còn thiếu (đếm từ TC-001 trở xuống).
Viết dựa trên app.py, main.js, index.html và seed_demo_mysql.sql thật.

Cách chạy (app phải đang chạy: python app.py -> http://127.0.0.1:5000, DB đã seed):
    pytest tests/ui/test_con_thieu.py --headed --slowmo 300      # xem trình duyệt chạy
    pytest tests/ui/test_con_thieu.py                            # chạy ngầm

Kết quả Pass/Fail + Actual Result được conftest.py ghi vào Excel (cột H và G).
  - Tên test phải có dạng test_tcNNN_... (NNN = 3 chữ số) để map đúng Test Case ID.
  - Mỗi TC có thể có nhiều test/tham số: chỉ cần 1 cái Fail thì TC là Fail.
  - Dùng fixture `actual("...")` để ghi Actual Result (gọi TRƯỚC assert).

Chưa viết: TC-012 (cần tài khoản Role_Id NULL tạo tay trong DB).
"""
import re
import uuid

import pytest
from playwright.sync_api import expect

PWD = "123456"
DEFAULT_URL = "http://127.0.0.1:5000"  # Flask: app.run(port=5000)

# Mã user theo seed_demo_mysql.sql
ID = {"admin": 1, "quanly1": 2, "seller1": 3, "khach1": 6, "khach2": 7}
KHACH1_CMND = "111111116"  # dùng để khôi phục hồ sơ khach1 sau TC-028

LAND = {
    "admin": "#adminInterface",
    "quanly1": "#adminInterface",
    "seller1": "#sellerDashboard",
}
VAI_TRO = {"admin": "Admin", "quanly1": "Quản lý", "seller1": "Seller", "khach1": "Customer"}


# ============================================================ fixtures
@pytest.fixture
def app_url(request):
    try:
        url = request.getfixturevalue("base_url")
    except pytest.FixtureLookupError:
        url = None
    return url or DEFAULT_URL


@pytest.fixture
def open_app(page, app_url):
    page.goto(app_url)
    page.wait_for_load_state("domcontentloaded")


ui = pytest.mark.usefixtures("open_app")


@pytest.fixture
def errors(page):
    bag = {"js": [], "http5xx": []}
    page.on("pageerror", lambda e: bag["js"].append(str(e)))
    page.on("response", lambda r: bag["http5xx"].append(f"{r.status} {r.url}") if r.status >= 500 else None)
    return bag


@pytest.fixture
def api_factory(playwright, app_url):
    """api_factory('khach1') -> APIRequestContext đã đăng nhập; api_factory() -> chưa đăng nhập."""
    ctxs = []

    def make(user=None, pwd=PWD):
        ctx = playwright.request.new_context(base_url=app_url)
        ctxs.append(ctx)
        if user:
            r = ctx.post("/api/dang-nhap", data={"tendangnhap": user, "mat_khau": pwd})
            assert r.ok and r.json().get("status") is True, f"Đăng nhập API {user} thất bại: {r.text()}"
        return ctx

    yield make
    for c in ctxs:
        c.dispose()


# ============================================================ helpers UI
def ui_login(page, username, password=PWD):
    page.locator("#hdrAuthBtn").click()
    page.locator("#loginUsername").fill(username)
    page.locator("#loginPass").fill(password)
    page.locator("#formLogin button[type='submit']").click()


def login_as(page, username, password=PWD):
    ui_login(page, username, password)
    expect(page.locator(LAND.get(username, "#hdrUserBtn"))).to_be_visible()


def ui_logout(page):
    for panel in ("#adminInterface", "#sellerDashboard"):
        if page.locator(panel).is_visible():
            page.locator(f"{panel} button:has-text('Đăng xuất')").click()
            return
    page.locator("#hdrUserBtn").click()
    page.locator("#profileModal button:has-text('Đăng xuất')").click()


def expect_logged_out(page):
    expect(page.locator("#hdrAuthBtn")).to_be_visible()
    expect(page.locator("#hdrUserBtn")).to_be_hidden()
    expect(page.locator("#adminInterface")).to_be_hidden()
    expect(page.locator("#sellerDashboard")).to_be_hidden()


def can_login(api_factory, username, password):
    """True nếu đăng nhập API thành công (dùng để kiểm tra mật khẩu/trạng thái không đổi)."""
    ctx = api_factory()
    r = ctx.post("/api/dang-nhap", data={"tendangnhap": username, "mat_khau": password})
    return r.status < 500 and r.json().get("status") is True


# =====================================================================
# TC-005  Đăng ký hợp lệ rồi đăng nhập bằng tài khoản mới   (TS-01)
# =====================================================================
@ui
def test_tc005_dang_ky_hop_le_va_dang_nhap(page, actual):
    username = f"customer_tc005_{uuid.uuid4().hex[:6]}"

    page.locator("#hdrAuthBtn").click()
    page.locator("#tabRegister").click()
    page.locator("#regName").fill("Nguyễn Văn M")
    page.locator("#regUsername").fill(username)
    page.locator("#regPhone").fill("0901234568")
    page.locator("#regPass").fill(PWD)
    page.locator("#formRegister button[type='submit']").click()

    expect(page.locator("#toast")).to_contain_text("Đăng ký tài khoản thành công!")
    expect(page.locator("#formLogin")).to_be_visible()
    expect(page.locator("#loginUsername")).to_have_value(username)
    actual(f"Đăng ký '{username}' thành công: hiện toast, chuyển sang form đăng nhập, điền sẵn username")

    page.locator("#loginPass").fill(PWD)
    page.locator("#formLogin button[type='submit']").click()
    expect(page.locator("#hdrUserBtn")).to_be_visible()
    actual("Đăng nhập bằng tài khoản mới thành công, hiển thị nút người dùng")


# =====================================================================
# TC-014  Kiểm tra phiên khi chưa đăng nhập   (TS-03)
# =====================================================================
@ui
def test_tc014_phien_khi_chua_dang_nhap(page, errors, api_factory, actual):
    page.reload()
    expect_logged_out(page)
    expect(page.locator("#topbarUserText")).to_contain_text("Chưa đăng nhập")
    actual(f"UI ở trạng thái chưa đăng nhập; lỗi HTTP 5xx: {len(errors['http5xx'])}")
    assert errors["http5xx"] == [], errors["http5xx"]

    r = api_factory().get("/api/phien")
    body = r.json()
    actual(f"GET /api/phien -> HTTP {r.status}, status={body.get('status')}, data={body.get('data')}")
    assert r.status < 500
    assert body["status"] is False and body["data"] is None


# =====================================================================
# TC-016  Phiên của tài khoản bị khóa   (TS-03)
# =====================================================================
def test_tc016_phien_tai_khoan_bi_khoa(browser, app_url, actual):
    cust_ctx, mgr_ctx = browser.new_context(), browser.new_context()
    cp, mp = cust_ctx.new_page(), mgr_ctx.new_page()

    def tim_khach2():
        mp.locator("#menu-users").click()
        mp.locator("#userSearchFilter").fill("khach2")
        row = mp.locator("#tblAdminUsersBody tr", has_text="@khach2")
        expect(row).to_have_count(1)
        return row

    def bam(label):
        tim_khach2().get_by_role("button", name=re.compile(label)).click()
        expect(mp.locator("#toast")).to_contain_text("khóa tài khoản")

    try:
        cp.goto(app_url)
        login_as(cp, "khach2")

        mp.goto(app_url)
        login_as(mp, "quanly1")
        bam("Khóa")  # active -> banned

        cp.reload()  # dùng phiên cũ (localStorage + cookie)
        expect(cp.locator("#hdrAuthBtn")).to_be_visible()
        expect(cp.locator("#hdrUserBtn")).to_be_hidden()
        actual("Quản lý khóa khach2; reload phiên cũ của khach2 -> về trạng thái chưa đăng nhập")
    finally:
        try:  # trả khach2 về active
            nut = tim_khach2().get_by_role("button", name=re.compile("Mở khóa"))
            if nut.count():
                nut.click()
        except Exception:
            pass
        cust_ctx.close()
        mgr_ctx.close()


# =====================================================================
# TC-017  Phiên sau đăng xuất   (TS-03)
# =====================================================================
@ui
def test_tc017_phien_sau_dang_xuat(page, actual):
    base_url = page.url.rstrip("/")
    login_as(page, "khach1")
    ui_logout(page)
    expect_logged_out(page)
    expect(page.locator("#topbarUserText")).to_contain_text("Chưa đăng nhập")

    r = page.request.get(base_url + "/api/phien")
    st = r.json()["status"]
    actual(f"Sau đăng xuất: UI chưa đăng nhập; GET /api/phien -> status={st}")
    assert st is False

    # Bước 4: Back rồi thử vào lại trang cần đăng nhập.
    # Trình duyệt mở app từ about:blank nên go_back() có thể lùi về trang trống
    # -> phải mở lại app (goto) thay vì reload trang trống.
    page.go_back()
    page.goto(base_url)
    page.wait_for_load_state("domcontentloaded")
    expect_logged_out(page)
    expect(page.locator("#hdrHistoryBtn")).to_be_hidden()

    r2 = page.request.get(base_url + "/api/users")  # API cần đăng nhập phải bị chặn
    actual(f"Sau đăng xuất: UI chưa đăng nhập, /api/phien status=False; "
           f"Back + mở lại app vẫn chưa đăng nhập, ẩn nút lịch sử; GET /api/users -> HTTP {r2.status}")
    assert r2.status == 403


# =====================================================================
# TC-018  Role hiển thị theo từng vai trò   (TS-03)   (1 TC, 4 tham số)
# =====================================================================
@ui
@pytest.mark.parametrize("username", ["admin", "quanly1", "seller1", "khach1"])
def test_tc018_role_hien_thi(page, username, actual):
    login_as(page, username)

    if username == "admin":
        expect(page.locator("#menu-users")).to_be_visible()
        expect(page.locator("#menu-categories")).to_be_hidden()
        expect(page.locator("#menu-sellers")).to_be_hidden()
    elif username == "quanly1":
        for m in ("#menu-categories", "#menu-sellers", "#menu-users"):
            expect(page.locator(m)).to_be_visible()
    elif username == "seller1":
        expect(page.locator("#userInterface")).to_be_hidden()
    else:
        expect(page.locator("#hdrRegisterSellerBtn")).to_be_visible()
        expect(page.locator("#hdrGoSellerBtn")).to_be_hidden()

    r = page.request.get(page.url.rstrip("/") + "/api/phien")
    data = r.json()["data"]
    actual(f"Vai trò '{data['ten_vai_tro']}', ma_user={data['ma_user']}; menu/giao diện hiển thị đúng vai trò")
    assert data["ten_vai_tro"] == VAI_TRO[username]
    assert data["ma_user"] == ID[username]


# =====================================================================
# TC-020  Đăng xuất khi chưa đăng nhập   (TS-04)
# =====================================================================
@ui
def test_tc020_dang_xuat_khi_chua_dang_nhap(page, errors, api_factory, actual):
    r = api_factory().post("/api/dang-xuat")
    st = r.json().get("status")
    actual(f"POST /api/dang-xuat khi chưa đăng nhập -> HTTP {r.status}, status={st}")
    assert r.status < 500
    assert st is True

    page.reload()
    expect_logged_out(page)
    actual(f"POST /api/dang-xuat -> HTTP {r.status}, status={st}; UI vẫn chưa đăng nhập; "
           f"lỗi HTTP 5xx: {len(errors['http5xx'])}")
    assert errors["http5xx"] == [], errors["http5xx"]


# =====================================================================
# TC-021  Đăng xuất hai lần liên tiếp   (TS-04)
# =====================================================================
@ui
def test_tc021_dang_xuat_hai_lan(page, actual):
    login_as(page, "khach1")
    ui_logout(page)  # lần 1
    expect_logged_out(page)

    base = page.url.rstrip("/")
    r2 = page.request.post(base + "/api/dang-xuat")  # lần 2
    st2 = r2.json().get("status")
    ph = page.request.get(base + "/api/phien").json()["status"]
    actual(f"Đăng xuất lần 2 -> HTTP {r2.status}, status={st2}; /api/phien status={ph}")
    assert r2.status < 500 and st2 is True
    assert ph is False


# =====================================================================
# TC-027  Cập nhật hồ sơ khi chưa đăng nhập   (TS-05)
# =====================================================================
def test_tc027_cap_nhat_ho_so_chua_dang_nhap(api_factory, actual):
    r = api_factory().post("/api/cap-nhat-profile",
                           data={"ten_user": "Nguyễn Văn Z", "sdt": "0901234567"})
    st = r.json().get("status")
    actual(f"POST /api/cap-nhat-profile khi chưa đăng nhập -> HTTP {r.status}, status={st}")
    assert r.status in (401, 403)
    assert st is False


# =====================================================================
# TC-028  Ownership hồ sơ   (TS-05)
# =====================================================================
def test_tc028_ownership_ho_so(api_factory, actual):
    khach1, khach2 = api_factory("khach1"), api_factory("khach2")
    goc1 = khach1.get("/api/phien").json()["data"]
    ten_khach2_truoc = khach2.get("/api/phien").json()["data"]["ten_user"]

    try:
        r = khach1.post("/api/cap-nhat-profile", data={
            "ma_user": ID["khach2"],  # cố sửa hồ sơ khach2
            "ten_user": "Hacker Test",
            "sdt": goc1["sdt"] or "", "dia_chi": goc1["dia_chi"] or "", "cmnd": KHACH1_CMND,
        })
        ten_khach2_sau = khach2.get("/api/phien").json()["data"]["ten_user"]
        actual(f"khach1 gửi sửa hồ sơ khach2 -> HTTP {r.status}; "
               f"tên khach2 trước='{ten_khach2_truoc}', sau='{ten_khach2_sau}'")
        assert r.status < 500
        assert ten_khach2_sau == ten_khach2_truoc, "Hồ sơ khach2 bị thay đổi!"
    finally:  # khôi phục hồ sơ khach1
        khach1.post("/api/cap-nhat-profile", data={
            "ten_user": goc1["ten_user"], "sdt": goc1["sdt"] or "",
            "dia_chi": goc1["dia_chi"] or "", "cmnd": KHACH1_CMND,
        })


# =====================================================================
# TC-034  Cố đổi mật khẩu tài khoản khác   (TS-06)
# =====================================================================
def test_tc034_doi_mat_khau_tai_khoan_khac(api_factory, actual):
    khach1 = api_factory("khach1")
    r = khach1.post("/api/doi-mat-khau", data={
        "ma_user": ID["khach2"], "mat_khau_cu": PWD, "mat_khau_moi": "hacked123"})
    st = r.json().get("status")
    cu = can_login(api_factory, "khach2", PWD)
    moi = can_login(api_factory, "khach2", "hacked123")
    actual(f"POST /api/doi-mat-khau -> HTTP {r.status}, status={st}; "
           f"khach2 đăng nhập mật khẩu cũ={cu}, mật khẩu 'hacked123'={moi}")
    assert r.status in (200, 400, 403)
    assert st is False
    assert cu, "khach2 không đăng nhập được bằng mật khẩu cũ"
    assert not moi


# =====================================================================
# TC-037 / TC-038 / TC-039  Xem danh sách tài khoản không đủ quyền   (TS-07)
#   Tách riêng từng TC để Excel ghi đúng kết quả cho từng dòng
# =====================================================================
def _check_api_users(api_factory, user, actual):
    r = api_factory(user).get("/api/users")
    body = r.json()
    who = user or "chưa đăng nhập"
    actual(f"GET /api/users ({who}) -> HTTP {r.status}, status={body.get('status')}, "
           f"data={'có dữ liệu' if body.get('data') else 'rỗng'}")
    assert r.status == 403
    assert body["status"] is False
    assert not body.get("data")


def _check_ui_khong_thay_menu(page, username, actual):
    login_as(page, username)
    expect(page.locator("#adminInterface")).to_be_hidden()
    expect(page.locator("#menu-users")).to_be_hidden()
    actual(f"UI {username}: không hiển thị giao diện Admin và menu Quản lý người dùng")


def test_tc037_api_khach1(api_factory, actual):
    _check_api_users(api_factory, "khach1", actual)


@ui
def test_tc037_ui_khach1(page, actual):
    _check_ui_khong_thay_menu(page, "khach1", actual)


def test_tc038_api_seller1(api_factory, actual):
    _check_api_users(api_factory, "seller1", actual)


@ui
def test_tc038_ui_seller1(page, actual):
    _check_ui_khong_thay_menu(page, "seller1", actual)


def test_tc039_api_chua_dang_nhap(api_factory, actual):
    _check_api_users(api_factory, None, actual)


# =====================================================================
# TC-043  Trạng thái ngoài active/banned   (TS-08)
# =====================================================================
@pytest.mark.parametrize("bad", ["deleted", "", 123])
def test_tc043_trang_thai_khong_hop_le(api_factory, bad, actual):
    quanly = api_factory("quanly1")
    r = quanly.put(f"/api/users/{ID['khach2']}/status", data={"status": bad})
    st = r.json().get("status")
    con_active = can_login(api_factory, "khach2", PWD)
    actual(f"PUT status={bad!r} -> HTTP {r.status}, status={st}; khach2 vẫn đăng nhập được={con_active}")
    assert r.status < 500
    assert st is False
    assert con_active


# =====================================================================
# TC-044  Quản lý tự khóa chính mình   (TS-08)
# =====================================================================
def test_tc044_quan_ly_tu_khoa_minh(api_factory, actual):
    quanly = api_factory("quanly1")
    r = quanly.put(f"/api/users/{ID['quanly1']}/status", data={"status": "banned"})
    st = r.json().get("status")
    con_active = can_login(api_factory, "quanly1", PWD)
    actual(f"Quản lý tự khóa mình -> HTTP {r.status}, status={st}; quanly1 vẫn đăng nhập được={con_active}")
    assert r.status < 500
    assert st is False
    assert con_active


# =====================================================================
# TC-045  Cố khóa Admin/Quản lý   (TS-08)
# =====================================================================
def test_tc045_khoa_admin(api_factory, actual):
    quanly = api_factory("quanly1")
    r = quanly.put(f"/api/users/{ID['admin']}/status", data={"status": "banned"})
    st = r.json().get("status")
    con_active = can_login(api_factory, "admin", PWD)
    actual(f"Quản lý khóa Admin -> HTTP {r.status}, status={st}; admin vẫn đăng nhập được={con_active}")
    assert r.status < 500
    assert st is False
    assert con_active  # Seed chỉ có 1 Quản lý nên chưa thử "quanly2"


# =====================================================================
# TC-046  Chưa đăng nhập hoặc sai role gọi khóa/mở khóa   (TS-08)
# =====================================================================
@pytest.mark.parametrize("user", [None, "khach1", "seller1"])
def test_tc046_khoa_sai_quyen(api_factory, user, actual):
    r = api_factory(user).put(f"/api/users/{ID['khach2']}/status", data={"status": "banned"})
    st = r.json().get("status")
    con_active = can_login(api_factory, "khach2", PWD)
    actual(f"PUT khóa khach2 bởi {user or 'chưa đăng nhập'} -> HTTP {r.status}, status={st}; "
           f"khach2 vẫn đăng nhập được={con_active}")
    assert r.status == 403
    assert st is False
    assert con_active


# =====================================================================
# TC-048  Cấp lại mật khẩu khi thiếu mã user   (TS-09)
# =====================================================================
def test_tc048_cap_lai_thieu_ma_user(api_factory, actual):
    r = api_factory("quanly1").post("/api/cap-lai-mat-khau", data={"mat_khau_moi": "newpass123"})
    st = r.json().get("status")
    actual(f"Cấp lại mật khẩu thiếu ma_user -> HTTP {r.status}, status={st}")
    assert r.status < 500
    assert st is False


# =====================================================================
# TC-049  Cấp lại cho user không tồn tại   (TS-09)
# =====================================================================
def test_tc049_cap_lai_user_khong_ton_tai(api_factory, actual):
    r = api_factory("quanly1").post("/api/cap-lai-mat-khau",
                                    data={"ma_user": 99999, "mat_khau_moi": "newpass123"})
    st = r.json().get("status")
    actual(f"Cấp lại mật khẩu cho ma_user=99999 -> HTTP {r.status}, status={st}")
    assert r.status < 500
    assert st is False


# =====================================================================
# TC-051  Cấp lại mật khẩu cho Admin   (TS-09)
# =====================================================================
def test_tc051_cap_lai_mat_khau_admin(api_factory, actual):
    quanly = api_factory("quanly1")
    try:
        r = quanly.post("/api/cap-lai-mat-khau",
                        data={"ma_user": ID["admin"], "mat_khau_moi": "newpass123"})
        st = r.json().get("status")
        admin_ok = can_login(api_factory, "admin", PWD)
        actual(f"Cấp lại mật khẩu cho Admin -> HTTP {r.status}, status={st}; "
               f"admin đăng nhập bằng mật khẩu cũ={admin_ok}")
        assert r.status < 500
        assert st is False
        assert admin_ok, "Mật khẩu Admin đã bị đổi!"
    finally:  # nếu app lỡ cho đổi thì trả mật khẩu admin về 123456
        if not can_login(api_factory, "admin", PWD) and can_login(api_factory, "admin", "newpass123"):
            admin = api_factory("admin", "newpass123")
            admin.post("/api/doi-mat-khau", data={"mat_khau_cu": "newpass123", "mat_khau_moi": PWD})


# =====================================================================
# TC-052  Người không phải Quản lý cấp lại mật khẩu   (TS-09)
# =====================================================================
@pytest.mark.parametrize("user", [None, "khach1", "seller1"])
def test_tc052_cap_lai_sai_quyen(api_factory, user, actual):
    r = api_factory(user).post("/api/cap-lai-mat-khau",
                               data={"ma_user": ID["khach2"], "mat_khau_moi": "newpass123"})
    st = r.json().get("status")
    con_pwd_cu = can_login(api_factory, "khach2", PWD)
    actual(f"Cấp lại mật khẩu bởi {user or 'chưa đăng nhập'} -> HTTP {r.status}, status={st}; "
           f"khach2 vẫn đăng nhập bằng mật khẩu cũ={con_pwd_cu}")
    assert r.status == 403
    assert st is False
    assert con_pwd_cu