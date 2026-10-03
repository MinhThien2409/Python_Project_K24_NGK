"""
TC-053 -> TC-073  |  TS-10..TS-13: Admin quản lý tài khoản "Quản lý"
(Tạo / Cập nhật / Xóa / Xem danh sách)

LƯU Ý: KHÔNG đặt tên file dạng test_tcNNN... vì conftest.py dò TC ID bằng regex
trên cả nodeid (có tên file) -> sẽ gán sai TC cho mọi test.

Chạy (đã bật Flask ở cổng 5000):
    pytest test_quan_ly_account.py --base-url http://127.0.0.1:5000 -v

Yêu cầu: pytest, pytest-playwright, conftest.py hiện có (ghi kết quả vào Excel).

Ghi chú thiết kế:
- Giao diện hiện KHÔNG còn form tạo/sửa/xóa Quản lý (đã gỡ ở bản 017) nên các
  TC CRUD gọi thẳng API /api/quan-ly (đúng bước "Gọi API" trong test case).
  Các TC kiểm tra "menu" (TC-053, 070, 071) dùng thêm giao diện thật.
- Mỗi client API là 1 APIRequestContext riêng => có cookie session riêng.
- Test tự tạo/dọn dữ liệu (quanly_tc053, quanly2, ...), không phụ thuộc thứ tự chạy.
- Không so khớp nguyên văn thông báo (dễ gãy); chỉ kiểm tra status/HTTP/dữ liệu,
  nội dung message được ghi vào Actual Result.
"""
import random

import pytest
from playwright.sync_api import expect

DEFAULT_BASE = "http://127.0.0.1:5000"
MAT_KHAU = "123456"
ADMIN = ("admin", MAT_KHAU)
ROLE_ADMIN, ROLE_QUAN_LY = 1, 2


# ============================================================
# HẠ TẦNG: client API + helper
# ============================================================
class Api:
    """Bọc APIRequestContext: trả (http_status, body_json)."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.me = None  # data đăng nhập (nếu có login)

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
    """new_api() -> client chưa đăng nhập; new_api(("user","pass")) -> đã đăng nhập."""
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


def _g(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) is not None:
            return d[k]
    return None


def u_name(u):
    return _g(u, "tendangnhap", "Username", "username")


def u_id(u):
    return _g(u, "ma_user", "UserId", "user_id")


def u_role(u):
    return _g(u, "ma_nhom_quyen", "Role_Id", "Role_id")


def u_ten(u):
    return _g(u, "ten_user", "FullName")


def ds_quan_ly(admin):
    st, body = admin.get("/api/quan-ly")
    return body.get("data") or [] if isinstance(body, dict) else []


def ds_users(admin):
    st, body = admin.get("/api/users")
    return body.get("data") or [] if isinstance(body, dict) else []


def tim_user(admin, username):
    return next((u for u in ds_users(admin) if u_name(u) == username), None)


def tim_quan_ly(admin, username):
    return next((u for u in ds_quan_ly(admin) if u_name(u) == username), None)


def sdt_ngau_nhien():
    return "0" + "".join(str(random.randint(0, 9)) for _ in range(9))


def payload(username, ten="Trần Quản Lý", mat_khau=MAT_KHAU, **extra):
    d = {
        "ten_user": ten,
        "tendangnhap": username,
        "mat_khau": mat_khau,
        "sdt": sdt_ngau_nhien(),
        "dia_chi": "12 Nguyễn Huệ, Quận 1, TP. HCM",
    }
    d.update(extra)
    return d


def xoa_neu_co(admin, username):
    u = tim_quan_ly(admin, username)
    if u:
        admin.delete(f"/api/quan-ly/{u_id(u)}")


def dam_bao_co(admin, username, ten="Quản Lý Test"):
    """Đảm bảo tài khoản Quản lý tồn tại, trả về dict user."""
    u = tim_quan_ly(admin, username)
    if not u:
        admin.post("/api/quan-ly", payload(username, ten=ten))
        u = tim_quan_ly(admin, username)
    assert u, f"Không thể chuẩn bị tài khoản Quản lý {username}"
    return u


def msg(body):
    return (body.get("message") if isinstance(body, dict) else "") or ""


def dem_theo_role(admin, role):
    return sum(1 for u in ds_users(admin) if u_role(u) == role)


def dang_nhap_ui(page, username, password):
    """Đăng nhập bằng giao diện. Không dùng fixture `login` của conftest vì
    get_by_text("Đăng nhập") khớp nhầm dòng topbar "Chưa đăng nhập"."""
    page.goto("/")
    page.locator("#hdrAuthBtn").click()
    page.locator("#loginUsername").wait_for(state="visible", timeout=10000)
    page.fill("#loginUsername", username)
    page.fill("#loginPass", password)
    page.click("#formLogin button[type='submit']")
    # đăng nhập thành công -> trang reload và nút tài khoản hiện ra
    expect(page.locator("#hdrUserBtn")).to_be_visible(timeout=15000)


# Actor KHÔNG phải Admin (kèm trường hợp chưa đăng nhập)
ACTORS = [
    pytest.param("quanly1", id="quanly1"),
    pytest.param("khach1", id="khach1"),
    pytest.param("seller1", id="seller1"),
    pytest.param(None, id="khong_session"),
]


def lam_actor(new_api, ten):
    return new_api((ten, MAT_KHAU)) if ten else new_api()


def assert_bi_tu_choi(st, body):
    assert st in (401, 403), f"Kỳ vọng HTTP 401/403, thực tế {st}"
    assert body.get("status") is not True, f"API lại cho phép: {body}"


# ============================================================
# TS-10 — TẠO TÀI KHOẢN QUẢN LÝ
# ============================================================
def test_tc053_admin_tao_quan_ly_hop_le(new_api, page, actual):
    admin = new_api(ADMIN)
    xoa_neu_co(admin, "quanly_tc053")  # dọn lần chạy trước

    st, body = admin.post("/api/quan-ly", payload("quanly_tc053"))
    actual(f"Tạo: HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert body.get("status") is True

    # Có trong danh sách Quản lý
    assert tim_quan_ly(admin, "quanly_tc053"), "Không thấy trong danh sách Quản lý"

    # Role = Quản lý, trạng thái active
    u = tim_user(admin, "quanly_tc053")
    assert u, "Không thấy trong /api/users"
    actual(f"Role={u_role(u)}, trang_thai={u.get('trang_thai')}")
    assert u_role(u) == ROLE_QUAN_LY
    assert (u.get("trang_thai") or "active") == "active"

    # Đăng nhập API bằng tài khoản mới
    mgr = new_api(("quanly_tc053", MAT_KHAU))
    assert u_role(mgr.me) == ROLE_QUAN_LY

    # Đăng nhập giao diện -> thấy chức năng của Quản lý
    dang_nhap_ui(page, "quanly_tc053", MAT_KHAU)
    expect(page.locator("#adminInterface")).to_be_visible(timeout=10000)
    expect(page.locator("#menu-categories")).to_be_visible()
    expect(page.locator("#menu-sellers")).to_be_visible()


def test_tc054_tao_username_trung(new_api, actual):
    admin = new_api(ADMIN)
    dam_bao_co(admin, "quanly1")
    truoc = len(ds_users(admin))

    st, body = admin.post("/api/quan-ly", payload("quanly1"))
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert body.get("status") is False
    assert st < 500
    m = msg(body).lower()
    assert any(k in m for k in ("tồn tại", "đã có", "sử dụng")), \
        f"Message không báo trùng tên đăng nhập: '{msg(body)}'"

    sau = ds_users(admin)
    assert len(sau) == truoc, f"Số tài khoản đổi {truoc} -> {len(sau)}"
    assert sum(1 for u in sau if u_name(u) == "quanly1") == 1


def test_tc055_password_duoi_6_ky_tu(new_api, actual):
    admin = new_api(ADMIN)
    xoa_neu_co(admin, "quanly_tc055")

    st, body = admin.post("/api/quan-ly", payload("quanly_tc055", mat_khau="12345"))
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert body.get("status") is False
    assert "6" in msg(body), f"Message không nêu tối thiểu 6 ký tự: '{msg(body)}'"
    assert tim_user(admin, "quanly_tc055") is None, "Tài khoản vẫn bị tạo"


@pytest.mark.parametrize("truong,gia_tri", [
    pytest.param("vai_tro", "Admin", id="vai_tro=Admin"),
    pytest.param("ma_nhom_quyen", 1, id="ma_nhom_quyen=1"),
    pytest.param("role", "Admin", id="role=Admin"),
])
def test_tc056_co_tao_tai_khoan_admin(new_api, actual, truong, gia_tri):
    admin = new_api(ADMIN)
    xoa_neu_co(admin, "admin_tc056")
    admin_truoc = dem_theo_role(admin, ROLE_ADMIN)

    st, body = admin.post("/api/quan-ly",
                          payload("admin_tc056", **{truong: gia_tri}))
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    try:
        assert st < 500
        # Chấp nhận: từ chối, hoặc tạo nhưng ép role Quản lý
        u = tim_user(admin, "admin_tc056")
        if u is not None:
            actual(f"Tài khoản được tạo với Role={u_role(u)}")
            assert u_role(u) == ROLE_QUAN_LY, "Tài khoản tạo ra mang role khác Quản lý"
        assert dem_theo_role(admin, ROLE_ADMIN) == admin_truoc, "Số Admin bị tăng"
    finally:
        xoa_neu_co(admin, "admin_tc056")


@pytest.mark.parametrize("truong,gia_tri", [
    pytest.param("ten_user", "", id="a_ho_ten_trong"),
    pytest.param("tendangnhap", "", id="b_username_trong"),
    pytest.param("mat_khau", "", id="c_mat_khau_trong"),
])
def test_tc057_thieu_truong_bat_buoc(new_api, actual, truong, gia_tri):
    admin = new_api(ADMIN)
    xoa_neu_co(admin, "quanly_tc057")
    truoc = len(ds_users(admin))

    st, body = admin.post("/api/quan-ly",
                          payload("quanly_tc057", **{truong: gia_tri}))
    actual(f"Bỏ trống {truong}: HTTP {st}, status={body.get('status')}, "
           f"message='{msg(body)}'")
    assert body.get("status") is False
    assert st < 500
    assert len(ds_users(admin)) == truoc, "Có tài khoản mới bị tạo"
    assert tim_user(admin, "quanly_tc057") is None


@pytest.mark.parametrize("actor", ACTORS)
def test_tc058_tao_quan_ly_actor_khong_phai_admin(new_api, actual, actor):
    admin = new_api(ADMIN)
    xoa_neu_co(admin, "quanly_tc058")
    truoc = len(ds_users(admin))

    api = lam_actor(new_api, actor)
    st, body = api.post("/api/quan-ly", payload("quanly_tc058"))
    actual(f"Actor={actor or 'không session'}: HTTP {st}, "
           f"status={body.get('status')}, message='{msg(body)}'")
    assert_bi_tu_choi(st, body)
    assert tim_user(admin, "quanly_tc058") is None
    assert len(ds_users(admin)) == truoc


# ============================================================
# TS-11 — CẬP NHẬT TÀI KHOẢN QUẢN LÝ
# ============================================================
def test_tc059_admin_cap_nhat_quan_ly_hop_le(new_api, actual):
    admin = new_api(ADMIN)
    q2 = dam_bao_co(admin, "quanly2", ten="Quản Lý Hai")
    ma = u_id(q2)
    # Đặt về giá trị gốc trước để lần chạy nào cũng có thay đổi thật
    # (MySQL rowcount = 0 khi giá trị không đổi -> BUS báo "không tồn tại")
    admin.put(f"/api/quan-ly/{ma}", {
        "ten_user": "Quản Lý Hai", "dia_chi": "12 Nguyễn Huệ, Quận 1, TP. HCM",
        "sdt": (tim_user(admin, "quanly2") or {}).get("sdt") or sdt_ngau_nhien()})
    truoc = tim_user(admin, "quanly2")

    st, body = admin.put(f"/api/quan-ly/{ma}", {
        "ten_user": "Quản Lý Hai Đã Sửa",
        "dia_chi": "99 Lê Lợi, Quận 1, TP. HCM",
        "sdt": truoc.get("sdt") or sdt_ngau_nhien(),
    })
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert body.get("status") is True

    sau = tim_user(admin, "quanly2")
    actual(f"Họ tên sau khi sửa: '{u_ten(sau)}'")
    assert u_ten(sau) == "Quản Lý Hai Đã Sửa"
    assert u_name(sau) == "quanly2", "Username bị đổi"
    assert u_role(sau) == u_role(truoc) == ROLE_QUAN_LY, "Role bị đổi"
    assert tim_quan_ly(admin, "quanly2"), "Không còn trong danh sách Quản lý"


def test_tc060_cap_nhat_target_la_admin(new_api, actual):
    admin = new_api(ADMIN)
    ma_admin = admin.me["ma_user"]
    truoc = tim_user(admin, "admin")

    st, body = admin.put(f"/api/quan-ly/{ma_admin}",
                         {"ten_user": "Admin Bị Sửa TC060", "dia_chi": "x",
                          "sdt": "0999999999"})
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert body.get("status") is False
    assert st < 500

    sau = tim_user(admin, "admin")
    assert u_ten(sau) == u_ten(truoc), "Thông tin Admin bị thay đổi"
    assert sau.get("sdt") == truoc.get("sdt")


@pytest.mark.parametrize("username", [
    pytest.param("khach1", id="khach1"),
    pytest.param("seller1", id="seller1"),
])
def test_tc061_cap_nhat_target_khong_phai_quan_ly(new_api, actual, username):
    admin = new_api(ADMIN)
    truoc = tim_user(admin, username)
    assert truoc, f"Seed thiếu tài khoản {username}"

    st, body = admin.put(f"/api/quan-ly/{u_id(truoc)}",
                         {"ten_user": "Bị Sửa TC061", "dia_chi": "x",
                          "sdt": "0999999998"})
    actual(f"Target={username}: HTTP {st}, status={body.get('status')}, "
           f"message='{msg(body)}'")
    assert body.get("status") is False
    assert st < 500

    sau = tim_user(admin, username)
    assert u_ten(sau) == u_ten(truoc), "Dữ liệu target bị thay đổi"
    assert sau.get("sdt") == truoc.get("sdt")


def test_tc062_cap_nhat_target_khong_ton_tai(new_api, actual):
    admin = new_api(ADMIN)
    st, body = admin.put("/api/quan-ly/99999",
                         {"ten_user": "Không Tồn Tại", "dia_chi": "x",
                          "sdt": "0999999997"})
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert st < 500, f"Lỗi server HTTP {st}"
    assert body.get("status") is False


@pytest.mark.parametrize("actor", ACTORS)
def test_tc063_cap_nhat_actor_khong_phai_admin(new_api, actual, actor):
    admin = new_api(ADMIN)
    q2 = dam_bao_co(admin, "quanly2", ten="Quản Lý Hai")
    truoc = tim_user(admin, "quanly2")

    api = lam_actor(new_api, actor)
    st, body = api.put(f"/api/quan-ly/{u_id(q2)}",
                       {"ten_user": "Bị Sửa TC063", "dia_chi": "x",
                        "sdt": truoc.get("sdt") or sdt_ngau_nhien()})
    actual(f"Actor={actor or 'không session'}: HTTP {st}, "
           f"status={body.get('status')}, message='{msg(body)}'")
    assert_bi_tu_choi(st, body)
    assert u_ten(tim_user(admin, "quanly2")) == u_ten(truoc), "quanly2 bị đổi"


# ============================================================
# TS-12 — XÓA TÀI KHOẢN QUẢN LÝ
# ============================================================
def test_tc064_admin_xoa_quan_ly_hop_le(new_api, actual):
    admin = new_api(ADMIN)
    u = dam_bao_co(admin, "quanly_tc053", ten="Trần Quản Lý")

    st, body = admin.delete(f"/api/quan-ly/{u_id(u)}")
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert body.get("status") is True

    con = tim_quan_ly(admin, "quanly_tc053")
    if con is not None:  # chấp nhận xóa mềm (vô hiệu hóa)
        actual(f"Vẫn còn trong danh sách, trang_thai={con.get('trang_thai')}")
        assert (con.get("trang_thai") or "") == "banned", \
            "Tài khoản vẫn còn và đang active"


def test_tc065_co_xoa_admin(new_api, actual):
    admin = new_api(ADMIN)
    ma_admin = admin.me["ma_user"]

    st, body = admin.delete(f"/api/quan-ly/{ma_admin}")
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert body.get("status") is False
    assert st < 500

    assert tim_user(admin, "admin"), "Tài khoản Admin biến mất khỏi danh sách"
    new_api(ADMIN)  # đăng nhập lại vẫn được (assert nằm trong new_api)


@pytest.mark.parametrize("muc_tieu", [
    pytest.param("khong_ton_tai", id="user_id_99999"),
    pytest.param("khach1", id="la_customer_khach1"),
])
def test_tc066_xoa_target_khong_hop_le(new_api, actual, muc_tieu):
    admin = new_api(ADMIN)
    truoc = len(ds_users(admin))
    if muc_tieu == "khong_ton_tai":
        ma = 99999
    else:
        k = tim_user(admin, "khach1")
        assert k, "Seed thiếu khach1"
        ma = u_id(k)

    st, body = admin.delete(f"/api/quan-ly/{ma}")
    actual(f"Target={muc_tieu}: HTTP {st}, status={body.get('status')}, "
           f"message='{msg(body)}'")
    assert body.get("status") is False
    assert st < 500
    assert len(ds_users(admin)) == truoc, "Có tài khoản bị xóa"
    if muc_tieu == "khach1":
        assert tim_user(admin, "khach1"), "khach1 đã bị xóa"


@pytest.mark.parametrize("actor", ACTORS)
def test_tc067_xoa_actor_khong_phai_admin(new_api, actual, actor):
    admin = new_api(ADMIN)
    q2 = dam_bao_co(admin, "quanly2", ten="Quản Lý Hai")

    api = lam_actor(new_api, actor)
    st, body = api.delete(f"/api/quan-ly/{u_id(q2)}")
    actual(f"Actor={actor or 'không session'}: HTTP {st}, "
           f"status={body.get('status')}, message='{msg(body)}'")
    assert_bi_tu_choi(st, body)
    assert tim_quan_ly(admin, "quanly2"), "quanly2 đã bị xóa"


def test_tc068_khong_login_duoc_sau_khi_xoa(new_api, actual):
    admin = new_api(ADMIN)
    u = dam_bao_co(admin, "quanly_tc053", ten="Trần Quản Lý")

    st, body = admin.delete(f"/api/quan-ly/{u_id(u)}")
    actual(f"Xóa: HTTP {st}, status={body.get('status')}")
    assert body.get("status") is True

    # Phiên mới, đăng nhập bằng tài khoản đã xóa
    kh = new_api()
    st, body = kh.post("/api/dang-nhap",
                       {"tendangnhap": "quanly_tc053", "mat_khau": MAT_KHAU})
    actual(f"Đăng nhập sau xóa: HTTP {st}, status={body.get('status')}, "
           f"message='{msg(body)}'")
    assert body.get("status") is False

    # Không có phiên được tạo
    st2, phien = kh.get("/api/phien")
    assert phien.get("status") is False, "Vẫn có phiên đăng nhập"


# ============================================================
# TS-13 — XEM DANH SÁCH TÀI KHOẢN QUẢN LÝ
# ============================================================
def test_tc069_admin_xem_danh_sach_quan_ly(new_api, actual):
    admin = new_api(ADMIN)
    dam_bao_co(admin, "quanly2", ten="Quản Lý Hai")

    st, body = admin.get("/api/quan-ly")
    assert st == 200 and body.get("status") is True, f"HTTP {st} {body}"
    ds = body.get("data") or []
    ten_ds = sorted(u_name(u) for u in ds)
    actual(f"Danh sách Quản lý ({len(ds)}): {ten_ds}")

    assert "quanly1" in ten_ds and "quanly2" in ten_ds

    # Đối chiếu với bảng users: tập id phải đúng bằng tập Role = Quản lý
    id_quan_ly = {u_id(u) for u in ds_users(admin) if u_role(u) == ROLE_QUAN_LY}
    id_tra_ve = {u_id(u) for u in ds}
    assert id_tra_ve == id_quan_ly, \
        f"Lệch tập Quản lý: thừa={id_tra_ve - id_quan_ly}, thiếu={id_quan_ly - id_tra_ve}"
    for ten in ("admin", "seller1", "khach1"):
        assert ten not in ten_ds, f"{ten} lẫn trong danh sách Quản lý"


def test_tc070_customer_truy_cap_danh_sach_quan_ly(page, actual):
    dang_nhap_ui(page, "khach1", MAT_KHAU)
    page.wait_for_load_state("networkidle")

    # Không có menu quản trị / menu Danh sách Quản lý
    expect(page.locator("#adminInterface")).to_be_hidden()
    assert page.get_by_text("Danh sách Quản lý").count() == 0

    # Gọi trực tiếp API bằng phiên của trình duyệt
    resp = page.request.get("/api/quan-ly")
    try:
        body = resp.json()
    except Exception:
        body = {}
    actual(f"HTTP {resp.status}, status={body.get('status')}, message='{msg(body)}'")
    assert resp.status in (401, 403)
    assert not body.get("data")


def test_tc071_quan_ly_truy_cap_danh_sach_quan_ly(page, actual):
    dang_nhap_ui(page, "quanly1", MAT_KHAU)
    expect(page.locator("#adminInterface")).to_be_visible(timeout=10000)

    # Không có menu "Danh sách Quản lý" (chỉ Admin)
    assert page.get_by_text("Danh sách Quản lý").count() == 0

    resp = page.request.get("/api/quan-ly")
    try:
        body = resp.json()
    except Exception:
        body = {}
    actual(f"HTTP {resp.status}, status={body.get('status')}, message='{msg(body)}'")
    assert resp.status in (401, 403)
    assert not body.get("data")


def test_tc072_chua_dang_nhap_truy_cap(new_api, actual):
    api = new_api()
    st, body = api.get("/api/quan-ly")
    actual(f"HTTP {st}, status={body.get('status')}, message='{msg(body)}'")
    assert_bi_tu_choi(st, body)
    assert not body.get("data")


def _tim_khoa_nhay_cam(obj, duong_dan=""):
    """Duyệt đệ quy JSON, trả danh sách khóa có dạng mật khẩu/hash."""
    loi = []
    tu_khoa = ("pass", "pwd", "mat_khau", "matkhau", "hash", "secret")
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(t in str(k).lower() for t in tu_khoa):
                loi.append(f"{duong_dan}/{k}")
            loi += _tim_khoa_nhay_cam(v, f"{duong_dan}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            loi += _tim_khoa_nhay_cam(v, f"{duong_dan}[{i}]")
    return loi


def test_tc073_khong_tra_mat_khau(new_api, actual):
    admin = new_api(ADMIN)
    dam_bao_co(admin, "quanly2", ten="Quản Lý Hai")  # đảm bảo có dữ liệu để kiểm

    resp = admin.ctx.get("/api/quan-ly")
    raw = resp.text()
    body = resp.json()
    khoa_loi = _tim_khoa_nhay_cam(body)
    actual(f"HTTP {resp.status}, số bản ghi={len(body.get('data') or [])}, "
           f"khóa nghi lộ mật khẩu={khoa_loi or 'không có'}")

    assert resp.status == 200 and body.get("data"), "Danh sách rỗng/không tải được"
    assert not khoa_loi, f"JSON chứa trường mật khẩu/hash: {khoa_loi}"
    # Mật khẩu seed là plaintext 123456 -> không được xuất hiện làm giá trị
    assert '"123456"' not in raw, "JSON chứa giá trị mật khẩu plaintext '123456'"