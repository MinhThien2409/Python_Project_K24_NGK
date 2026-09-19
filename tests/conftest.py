import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from back_end.Model.User import User


VAI_TRO_CHUAN = ["Admin", "Quản lý", "Seller", "Customer"]


@pytest.fixture
def cac_vai_tro_chuan():
    """4 vai trò chuẩn theo seed mới (FR-001)."""
    return list(VAI_TRO_CHUAN)


@pytest.fixture
def user_mau():
    """Tạo một User mẫu thường dùng trong unit test BUS."""
    return User(
        ma_user=1,
        ma_nhom_quyen=1,
        ten_user="Nguyễn Văn An",
        sdt="0123456789",
        dia_chi="Hà Nội",
        cmnd="001099012345",
        tendangnhap="user1",
        mat_khau="123456"
    )


class MockUserDao:
    """Mock tầng DAO cho UserBus — KHÔNG chạm PobbyDB thật.

    Cho phép cấu hình user trả về của dang_nhap theo từng kịch bản test;
    lay_thong_tin_user trả trang_thai/Role_Id theo tham số cấu hình.
    """

    def __init__(self, user=None, banned=None, role_none=False,
                 thong_tin=None, mat_khau_moi_ok=True, trang_thai_ok=True,
                 so_admin=1, ton_tai_tendangnhap=False, them_quan_ly_ok=True,
                 danh_sach_quan_ly=None, cap_nhat_quan_ly_ok=True,
                 xoa_quan_ly_ok=True):
        self.user = user
        self.banned = banned
        self.role_none = role_none
        self.thong_tin = thong_tin
        self.mat_khau_moi_ok = mat_khau_moi_ok
        self.trang_thai_ok = trang_thai_ok
        self.so_admin = so_admin
        self.ton_tai_tendangnhap = ton_tai_tendangnhap
        self.them_quan_ly_ok = them_quan_ly_ok
        self.danh_sach_quan_ly = danh_sach_quan_ly
        self.cap_nhat_quan_ly_ok = cap_nhat_quan_ly_ok
        self.xoa_quan_ly_ok = xoa_quan_ly_ok

    def dang_nhap(self, username, password):
        if self.role_none:
            return {"role_none": True}
        if self.banned:
            return {"banned": True}
        # Không có user cấu hình (thiếu đầu vào) → như DB không tìm thấy dòng.
        if self.user is None:
            return None
        # Mật khẩu không khớp → như DB trả về không có dòng (UserBus từ chối).
        if self.user.mat_khau != password:
            return None
        return self.user

    def kiem_tra_tendangnhap_ton_tai(self, tendangnhap):
        return self.ton_tai_tendangnhap

    def lay_ten_vai_tro_theo_id(self, role_id):
        mapping = {
            1: "Admin",
            2: "Quản lý",
            3: "Seller",
            4: "Customer"
        }
        return mapping.get(role_id)

    def lay_vai_tro_user(self, role_id):
        return self.lay_ten_vai_tro_theo_id(role_id)

    def lay_thong_tin_user(self, ma_user):
        if self.thong_tin is not None:
            return self.thong_tin
        if self.user:
            role = self.user.ma_nhom_quyen
        else:
            role = 4
        return {
            "UserId": ma_user,
            "Role_Id": role,
            "trang_thai": "banned" if self.banned else "active",
        }

    def cap_nhat_mat_khau(self, ma_user, mat_khau_moi):
        return self.mat_khau_moi_ok

    def cap_nhat_trang_thai(self, ma_user, trang_thai):
        return self.trang_thai_ok

    def dem_admin(self):
        """Đếm số tài khoản Admin (Role_Id=1) — mock cho SC-001."""
        return self.so_admin

    def them_quan_ly(self, ten_user, dia_chi, sdt, tendangnhap, mat_khau):
        """Thêm tài khoản Quản lý — mock, trả id giả khi thành công."""
        if not self.them_quan_ly_ok:
            return None
        return 100

    def lay_danh_sach_quan_ly(self):
        """Danh sách chỉ Quản lý, không mật khẩu — mock."""
        if self.danh_sach_quan_ly is not None:
            return self.danh_sach_quan_ly
        return []

    def cap_nhat_quan_ly(self, ma_user, ten_user, dia_chi, sdt):
        """Cập nhật Quản lý — mock."""
        return self.cap_nhat_quan_ly_ok

    def xoa_quan_ly(self, ma_user):
        """Xóa cứng Quản lý — mock."""
        return self.xoa_quan_ly_ok


class MockDanhMucDao:
    """Mock tầng DAO cho DanhMucBus — KHÔNG chạm PobbyDB thật."""

    def __init__(self, danh_sach=None, ton_tai=False, so_san_pham=0, ket_qua_ghi=True):
        self.danh_sach = danh_sach or []
        self.ton_tai = ton_tai
        self.so_san_pham = so_san_pham
        self.ket_qua_ghi = ket_qua_ghi

    def lay_tat_ca(self):
        return self.danh_sach

    def kiem_tra_ten_ton_tai(self, ten, tru_id=None):
        return self.ton_tai

    def dem_san_pham(self, category_id):
        return self.so_san_pham

    def them(self, category):
        return self.ket_qua_ghi

    def sua(self, category):
        return self.ket_qua_ghi

    def xoa(self, category_id):
        return self.ket_qua_ghi


class MockGianHangDao:
    """Mock tầng DAO cho GianHangBus — KHÔNG chạm PobbyDB thật."""

    def __init__(self, ket_qua_duyet="ok", ket_qua_tu_choi="ok", danh_sach=None):
        self.ket_qua_duyet = ket_qua_duyet
        self.ket_qua_tu_choi = ket_qua_tu_choi
        self.danh_sach = danh_sach or []

    def duyet_yeu_cau(self, request_id, reviewed_by):
        return self.ket_qua_duyet

    def tu_choi_yeu_cau(self, request_id, reviewed_by, ly_do):
        return self.ket_qua_tu_choi

    def lay_danh_sach_yeu_cau(self):
        return self.danh_sach

    def gui_yeu_cau_ban_hang(self, req):
        return True

    def lay_theo_user(self, user_id):
        return None


@pytest.fixture
def mock_user_dao():
    """Fixture trả về factory tạo MockUserDao theo kịch bản."""
    def _tao(user=None, banned=None, role_none=False,
             thong_tin=None, mat_khau_moi_ok=True, trang_thai_ok=True,
             so_admin=1, ton_tai_tendangnhap=False, them_quan_ly_ok=True,
             danh_sach_quan_ly=None, cap_nhat_quan_ly_ok=True,
             xoa_quan_ly_ok=True):
        return MockUserDao(
            user=user, banned=banned, role_none=role_none,
            thong_tin=thong_tin, mat_khau_moi_ok=mat_khau_moi_ok,
            trang_thai_ok=trang_thai_ok, so_admin=so_admin,
            ton_tai_tendangnhap=ton_tai_tendangnhap,
            them_quan_ly_ok=them_quan_ly_ok,
            danh_sach_quan_ly=danh_sach_quan_ly,
            cap_nhat_quan_ly_ok=cap_nhat_quan_ly_ok,
            xoa_quan_ly_ok=xoa_quan_ly_ok
        )
    return _tao


@pytest.fixture
def mock_danh_muc_dao():
    """Fixture trả về factory tạo MockDanhMucDao theo kịch bản."""
    def _tao(danh_sach=None, ton_tai=False, so_san_pham=0, ket_qua_ghi=True):
        return MockDanhMucDao(
            danh_sach=danh_sach, ton_tai=ton_tai,
            so_san_pham=so_san_pham, ket_qua_ghi=ket_qua_ghi
        )
    return _tao


@pytest.fixture
def mock_gian_hang_dao():
    """Fixture trả về factory tạo MockGianHangDao theo kịch bản."""
    def _tao(ket_qua_duyet="ok", ket_qua_tu_choi="ok", danh_sach=None):
        return MockGianHangDao(
            ket_qua_duyet=ket_qua_duyet,
            ket_qua_tu_choi=ket_qua_tu_choi,
            danh_sach=danh_sach
        )
    return _tao


# ── Fake DAO có trạng thái dùng cho integration test (endpoint qua test_client) ──
VAI_TRO_MAP = {1: "Admin", 2: "Quản lý", 3: "Seller", 4: "Customer"}


class FakeUserDaoBus:
    """Fake DAO User có trạng thái (users / thong_tin / mat_khau) cho integration test."""

    def __init__(self, users=None, thong_tin=None, mat_khau=None):
        self.users = users or {}
        self.thong_tin = thong_tin or {}
        self.mat_khau = mat_khau or {}

    def dang_nhap(self, username, password):
        user = self.users.get(username)
        if not user:
            return None
        # Ưu tiên mật khẩu đã cập nhật trong self.mat_khau (sau đổi/cấp lại),
        # fallback về user.mat_khau ban đầu. Sửa lỗi: trước đây so user.mat_khau
        # trước nên mật khẩu mới luôn bị từ chối.
        expected = self.mat_khau.get(username, user.mat_khau)
        if expected != password:
            return None
        thong_tin = self.thong_tin.get(user.ma_user, {})
        if username in getattr(self, "_bang_ban", {}) or thong_tin.get('trang_thai') == 'banned':
            return {"banned": True}
        if username in getattr(self, "_bang_role_none", {}):
            return {"role_none": True}
        return user

    def lay_thong_tin_user(self, ma_user):
        return self.thong_tin.get(ma_user)

    def lay_ten_vai_tro_theo_id(self, role_id):
        return VAI_TRO_MAP.get(role_id)

    def lay_danh_sach_user(self):
        """Danh sách user KHÔNG bao giờ chứa mật khẩu (FR-011)."""
        return [
            {
                "ma_user": user.ma_user,
                "ten_user": user.ten_user,
                "tendangnhap": username,
                "sdt": user.sdt,
                "ma_nhom_quyen": user.ma_nhom_quyen,
                "ten_nhom_quyen": VAI_TRO_MAP.get(user.ma_nhom_quyen),
                "trang_thai": (self.thong_tin.get(user.ma_user) or {}).get("trang_thai") or "active",
            }
            for username, user in sorted(self.users.items())
        ]

    def cap_nhat_mat_khau(self, ma_user, mat_khau_moi):
        for username, user in self.users.items():
            if user.ma_user == ma_user:
                user.mat_khau = mat_khau_moi
                self.mat_khau[username] = mat_khau_moi
                thong_tin = self.thong_tin.get(ma_user)
                if isinstance(thong_tin, dict):
                    thong_tin["Password"] = mat_khau_moi
                return True
        return False

    def cap_nhat_user(self, ma_user, ten_user, dia_chi, sdt, cmnd):
        """UPDATE profile in-memory cho test customer (005 US5)."""
        for username, user in self.users.items():
            if user.ma_user == ma_user:
                user.ten_user = ten_user
                user.dia_chi = dia_chi
                user.sdt = sdt
                thong_tin = self.thong_tin.get(ma_user) or {}
                thong_tin["FullName"] = ten_user
                thong_tin["Address"] = dia_chi
                thong_tin["Phone"] = sdt
                self.thong_tin[ma_user] = thong_tin
                return True
        return False

    def cap_nhat_trang_thai(self, ma_user, trang_thai):
        thong_tin = self.thong_tin.get(ma_user)
        if not thong_tin:
            return False
        thong_tin['trang_thai'] = trang_thai
        return True

    def kiem_tra_tendangnhap_ton_tai(self, tendangnhap):
        """Tên đăng nhập duy nhất toàn hệ thống (mọi vai trò còn tồn tại)."""
        return tendangnhap in self.users

    def dem_admin(self):
        """Đếm Admin cho SC-001."""
        return sum(1 for u in self.users.values() if u.ma_nhom_quyen == 1)

    def them_quan_ly(self, ten_user, dia_chi, sdt, tendangnhap, mat_khau):
        """INSERT Quản lý in-memory, trả id mới."""
        from back_end.Model.User import User
        ma_moi = max([u.ma_user for u in self.users.values()] + [0]) + 1
        self.users[tendangnhap] = User(
            ma_user=ma_moi, ma_nhom_quyen=2, ten_user=ten_user,
            sdt=sdt, dia_chi=dia_chi, cmnd=None,
            tendangnhap=tendangnhap, mat_khau=mat_khau,
        )
        self.thong_tin[ma_moi] = {
            "UserId": ma_moi, "FullName": ten_user, "Phone": sdt,
            "Address": dia_chi, "Role_Id": 2, "trang_thai": "active",
            "Username": tendangnhap, "Password": mat_khau,
        }
        self.mat_khau[tendangnhap] = mat_khau
        return ma_moi

    def lay_danh_sach_quan_ly(self):
        """Danh sách chỉ Quản lý, KHÔNG mật khẩu."""
        ket_qua = []
        for username, user in sorted(self.users.items()):
            if user.ma_nhom_quyen != 2:
                continue
            thong_tin = self.thong_tin.get(user.ma_user) or {}
            ket_qua.append({
                "ma_user": user.ma_user,
                "ten_user": user.ten_user,
                "tendangnhap": username,
                "sdt": user.sdt,
                "dia_chi": user.dia_chi,
                "ma_nhom_quyen": 2,
                "ten_nhom_quyen": "Quản lý",
                "trang_thai": thong_tin.get("trang_thai") or "active",
            })
        return ket_qua

    def cap_nhat_quan_ly(self, ma_user, ten_user, dia_chi, sdt):
        """UPDATE chỉ FullName/Address/Phone, điều kiện Role_Id=2."""
        for username, user in self.users.items():
            if user.ma_user == ma_user and user.ma_nhom_quyen == 2:
                user.ten_user = ten_user
                user.dia_chi = dia_chi
                user.sdt = sdt
                thong_tin = self.thong_tin.get(ma_user) or {}
                thong_tin["FullName"] = ten_user
                thong_tin["Address"] = dia_chi
                thong_tin["Phone"] = sdt
                self.thong_tin[ma_user] = thong_tin
                return True
        return False

    def xoa_quan_ly(self, ma_user):
        """DELETE cứng điều kiện Role_Id=2."""
        for username, user in list(self.users.items()):
            if user.ma_user == ma_user and user.ma_nhom_quyen == 2:
                del self.users[username]
                self.thong_tin.pop(ma_user, None)
                self.mat_khau.pop(username, None)
                return True
        return False


class FakeDanhMucDao:
    """Fake DAO danh mục có trạng thái in-memory — KHÔNG chạm PobbyDB thật."""

    def __init__(self):
        self.categories = {}
        self.next_id = 1
        self.products = {}

    def lay_tat_ca(self):
        return [{"id": cid, "name": name}
                for cid, name in sorted(self.categories.items())]

    def kiem_tra_ten_ton_tai(self, ten, tru_id=None):
        chuan = (ten or "").strip().lower()
        return any(cid != tru_id and (name or "").strip().lower() == chuan
                   for cid, name in self.categories.items())

    def dem_san_pham(self, category_id):
        if category_id not in self.categories:
            return None
        return self.products.get(category_id, 0)

    def them(self, category):
        self.categories[self.next_id] = category.CategoryName.strip()
        self.next_id += 1
        return True

    def sua(self, category):
        if category.CategoryId not in self.categories:
            return False
        self.categories[category.CategoryId] = category.CategoryName.strip()
        return True

    def xoa(self, category_id):
        if category_id not in self.categories:
            return False
        del self.categories[category_id]
        return True


class FakeGianHangDao:
    """Fake DAO duyệt người bán có trạng thái — KHÔNG chạm PobbyDB thật."""

    def __init__(self, requests=None, stores=None, roles=None):
        self.requests = requests or {}
        self.stores = stores or set()
        self.roles = roles or {}
        self.last_approve = None

    def lay_danh_sach_yeu_cau(self):
        return [dict(r) for r in self.requests.values()]

    def duyet_yeu_cau(self, request_id, reviewed_by):
        req = self.requests.get(request_id)
        if not req:
            return 'khong_tim_thay'
        if req['status'] != 'pending':
            return 'da_xu_ly'
        if self.roles.get(req['user_id']) == 3 or req['user_id'] in self.stores:
            return 'da_la_seller'
        req['status'] = 'approved'
        req['reviewed_by'] = reviewed_by
        self.stores.add(req['user_id'])
        self.roles[req['user_id']] = 3
        self.last_approve = (request_id, req['user_id'])
        return 'ok'

    def tu_choi_yeu_cau(self, request_id, reviewed_by, ly_do):
        req = self.requests.get(request_id)
        if not req:
            return 'khong_tim_thay'
        if req['status'] != 'pending':
            return 'da_xu_ly'
        req['status'] = 'rejected'
        req['reviewed_by'] = reviewed_by
        req['reject_reason'] = ly_do
        return 'ok'

    def gui_yeu_cau_ban_hang(self, req):
        return True

    def lay_theo_user(self, user_id):
        if user_id in self.stores:
            return {"store_id": 1, "store_name": "Shop Test", "phone": "0900000000",
                    "category": "Hoa", "description": ""}
        return None


@pytest.fixture
def app_voi_dao(monkeypatch):
    """Gắn các BUS trong module app với DAO giả — KHÔNG chạm PobbyDB thật."""
    import app as app_module
    from back_end.BUS.UserBus import UserBus
    from back_end.BUS.DanhMucBus import DanhMucBus
    from back_end.BUS.GianHangBus import GianHangBus
    from back_end.BUS.SanPhamBus import SanPhamBus
    from back_end.BUS.DonHangBus import DonHangBus
    from back_end.DAO.UserDao import UserDao

    def _gan(user_dao=None, danh_muc_dao=None, gian_hang_dao=None,
             san_pham_dao=None, don_hang_dao=None):
        if user_dao is not None:
            ub = UserBus()
            ub.dao = user_dao
            monkeypatch.setattr(app_module, "user_bus", ub)
        if danh_muc_dao is not None:
            cb = DanhMucBus()
            cb.dao = danh_muc_dao
            monkeypatch.setattr(app_module, "category_bus", cb)
        if gian_hang_dao is not None:
            gb = GianHangBus()
            gb.dao = gian_hang_dao
            gb.user_dao = user_dao if user_dao is not None else UserDao()
            monkeypatch.setattr(app_module, "gian_hang_bus", gb)
        if san_pham_dao is not None:
            sb = SanPhamBus()
            sb.dao = san_pham_dao
            monkeypatch.setattr(app_module, "san_pham_bus", sb)
        if don_hang_dao is not None:
            db = DonHangBus()
            db.dao = don_hang_dao
            monkeypatch.setattr(app_module, "don_hang_bus", db)
        return user_dao, danh_muc_dao, gian_hang_dao

    return _gan


# ── Mock DAO cho Seller (004) — KHÔNG chạm PobbyDB thật ──
class MockSanPhamDao:
    """Mock SanPhamDao cho unit test BUS seller (ownership + nhap/giá)."""

    def __init__(self, store_cua_sp=None, ton_tai_category=True,
                 san_pham=None, ket_qua_ghi=True, ton_kho_moi=0):
        self.store_cua_sp = store_cua_sp or {}
        self.ton_tai_category = ton_tai_category
        self.san_pham = san_pham
        self.ket_qua_ghi = ket_qua_ghi
        self.ton_kho_moi = ton_kho_moi
        self.goi_nhap_hang = []
        self.goi_doi_gia = []

    def lay_store_id(self, product_id):
        return self.store_cua_sp.get(product_id)

    def lay_theo_id(self, product_id):
        return self.san_pham

    def kiem_tra_category_ton_tai(self, category_id):
        return self.ton_tai_category

    def them(self, sp):
        return 1 if self.ket_qua_ghi else None

    def sua_theo_store(self, sp, store_id):
        return self.ket_qua_ghi

    def an_hien_theo_store(self, product_id, store_id, is_active):
        return self.ket_qua_ghi

    def nhap_hang(self, product_id, store_id, so_luong):
        self.goi_nhap_hang.append((product_id, store_id, so_luong))
        return self.ton_kho_moi if self.ket_qua_ghi else None

    def doi_gia(self, product_id, store_id, gia_moi):
        self.goi_doi_gia.append((product_id, store_id, gia_moi))
        return self.ket_qua_ghi


class MockDonHangSellerDao:
    """Mock DonHangDao cho unit test BUS seller (luồng + ownership + TK)."""

    def __init__(self, trang_thai=None, thuoc_store=True,
                 thong_ke=None, doanh_thu_thang=None):
        self.trang_thai = trang_thai or {}
        self.thuoc_store = thuoc_store
        self.thong_ke = thong_ke
        self.doanh_thu_thang = doanh_thu_thang
        self.goi_cap_nhat = []

    def lay_trang_thai(self, order_id):
        return self.trang_thai.get(order_id)

    def don_thuoc_store(self, order_id, store_id):
        if isinstance(self.thuoc_store, dict):
            return self.thuoc_store.get(order_id, False)
        return self.thuoc_store

    def cap_nhat_trang_thai(self, order_id, new_status):
        self.goi_cap_nhat.append((order_id, new_status))
        return True

    def lay_thong_ke_cua_seller(self, store_id):
        return self.thong_ke or {"doanh_thu": 0, "tong_don": 0}

    def lay_doanh_thu_seller_theo_thang(self, store_id, year):
        if self.doanh_thu_thang is not None:
            return self.doanh_thu_thang
        return [{"thang": i, "doanh_thu": 0, "so_don": 0} for i in range(1, 13)]


class MockShopDao:
    """Mock GianHangDao cho unit test BUS trang shop (trùng tên + update)."""

    def __init__(self, trung_ten=False, ket_qua_ghi=True, store=None):
        self.trung_ten = trung_ten
        self.ket_qua_ghi = ket_qua_ghi
        self.store = store

    def kiem_tra_ten_shop_trung(self, ten_shop, tru_store_id=None):
        return self.trung_ten

    def cap_nhat_trang_shop(self, store_id, ten, gioi_thieu, tham_nien):
        return self.ket_qua_ghi

    def lay_theo_user(self, user_id):
        return self.store


# ── Fake in-memory cho integration test seller ──
class FakeSanPhamStore:
    """Fake store sản phẩm in-memory: {product_id: dict} + ownership."""

    def __init__(self, san_pham=None, categories=None):
        self.san_pham = san_pham or {}
        self.categories = categories if categories is not None else {1: "Hoa"}
        self.next_id = (max(self.san_pham.keys()) + 1) if self.san_pham else 1

    def lay_store_id(self, product_id):
        sp = self.san_pham.get(product_id)
        return sp.get("store_id") if sp else None

    def lay_theo_id(self, product_id):
        return self.san_pham.get(product_id)

    def kiem_tra_category_ton_tai(self, category_id):
        return category_id in self.categories

    def them(self, sp):
        nid = self.next_id
        self.next_id += 1
        self.san_pham[nid] = {
            "id": nid, "name": sp.ProductName, "price": float(sp.Price),
            "quantity": int(sp.Quantity or 0), "store_id": int(sp.StoreId),
            "category_id": int(sp.CategoryId), "is_active": True,
        }
        return nid

    def sua_theo_store(self, sp, store_id):
        cur = self.san_pham.get(int(sp.ProductId))
        if not cur or cur.get("store_id") != store_id:
            return False
        cur.update({"name": sp.ProductName, "price": float(sp.Price),
                    "quantity": int(sp.Quantity or 0)})
        return True

    def an_hien_theo_store(self, product_id, store_id, is_active):
        cur = self.san_pham.get(int(product_id))
        if not cur or cur.get("store_id") != store_id:
            return False
        cur["is_active"] = bool(is_active)
        return True

    def nhap_hang(self, product_id, store_id, so_luong):
        cur = self.san_pham.get(int(product_id))
        if not cur or cur.get("store_id") != store_id:
            return None
        cur["quantity"] = int(cur.get("quantity") or 0) + int(so_luong)
        return cur["quantity"]

    def doi_gia(self, product_id, store_id, gia_moi):
        cur = self.san_pham.get(int(product_id))
        if not cur or cur.get("store_id") != store_id:
            return False
        gia_cu = float(cur.get("price") or 0)
        if float(gia_moi) < gia_cu:
            cur["old_price"] = gia_cu
        cur["price"] = float(gia_moi)
        return True

    def lay_theo_store(self, store_id):
        return [dict(v) for v in self.san_pham.values()
                if v.get("store_id") == store_id]

    def lay_theo_store_ca_an_hien(self, store_id):
        return self.lay_theo_store(store_id)


class FakeDonHangSellerStore:
    """Fake store đơn hàng in-memory cho integration seller."""

    TRANG_THAI = ['Pending', 'Confirmed', 'Shipping', 'Completed', 'Cancelled']

    def __init__(self, don_hang=None, thuoc=None):
        self.don_hang = don_hang or {}
        self.thuoc = thuoc or {}

    def lay_trang_thai(self, order_id):
        don = self.don_hang.get(int(order_id))
        return don.get("Status") if don else None

    def don_thuoc_store(self, order_id, store_id):
        return store_id in self.thuoc.get(int(order_id), set())

    def cap_nhat_trang_thai(self, order_id, new_status):
        don = self.don_hang.get(int(order_id))
        if not don:
            return False
        don["Status"] = new_status
        return True

    def lay_don_hang_cua_seller(self, store_id):
        return [dict(v) for k, v in self.don_hang.items()
                if store_id in self.thuoc.get(k, set())]

    def lay_thong_ke_cua_seller(self, store_id):
        don = [v for k, v in self.don_hang.items()
               if store_id in self.thuoc.get(k, set())]
        return {"doanh_thu": sum(float(d.get("TotalAmount") or 0) for d in don),
                "tong_don": len(don), "cho_duyet": 0, "dang_giao": 0,
                "hoan_thanh": 0, "da_huy": 0,
                "top_san_pham": [], "don_gan_day": []}

    def lay_doanh_thu_seller_theo_thang(self, store_id, year):
        return [{"thang": i, "doanh_thu": 0, "so_don": 0} for i in range(1, 13)]


class FakeShopStore:
    """Fake store gian hàng in-memory cho integration seller."""

    def __init__(self, stores=None):
        self.stores = stores or {}

    def lay_theo_user(self, user_id):
        for sid, s in self.stores.items():
            if s.get("UserId") == user_id:
                return {"store_id": sid, "store_name": s.get("StoreName"),
                        "phone": s.get("Phone"), "category": s.get("Category"),
                        "description": s.get("Description"),
                        "tham_nien": s.get("ThamNien")}
        return None

    def kiem_tra_ten_shop_trung(self, ten_shop, tru_store_id=None):
        chuan = (ten_shop or "").strip().lower()
        return any(sid != tru_store_id and (s.get("StoreName") or "").strip().lower() == chuan
                   for sid, s in self.stores.items())

    def cap_nhat_trang_shop(self, store_id, ten, gioi_thieu, tham_nien):
        s = self.stores.get(int(store_id))
        if not s:
            return False
        s["StoreName"] = ten
        s["Description"] = gioi_thieu
        s["ThamNien"] = tham_nien
        return True


@pytest.fixture
def seller_client(monkeypatch):
    """Flask test_client voi DAO seller da gan — KHÔNG chạm PobbyDB thật."""
    import app as app_module

    def _tao(user_dao=None, san_pham_store=None, don_hang_store=None, shop_store=None,
             gio_hang_store=None):
        from back_end.BUS.UserBus import UserBus
        from back_end.BUS.SanPhamBus import SanPhamBus
        from back_end.BUS.DonHangBus import DonHangBus
        from back_end.BUS.GianHangBus import GianHangBus
        from back_end.BUS.GioHangBus import GioHangBus
        if user_dao is not None:
            ub = UserBus()
            ub.dao = user_dao
            monkeypatch.setattr(app_module, "user_bus", ub)
        if san_pham_store is not None:
            sb = SanPhamBus()
            sb.dao = san_pham_store
            monkeypatch.setattr(app_module, "san_pham_bus", sb)
        if don_hang_store is not None:
            db = DonHangBus()
            db.dao = don_hang_store
            monkeypatch.setattr(app_module, "don_hang_bus", db)
        if shop_store is not None:
            gb = GianHangBus()
            gb.dao = shop_store
            if user_dao is not None:
                gb.user_dao = user_dao
            monkeypatch.setattr(app_module, "gian_hang_bus", gb)
        if gio_hang_store is not None:
            cb = GioHangBus()
            cb.dao = gio_hang_store
            monkeypatch.setattr(app_module, "cart_bus", cb)
        app_module.app.config["TESTING"] = True
        return app_module.app.test_client()

    return _tao


# ── Mock DAO cho Customer (005) — KHÔNG chạm PobbyDB thật ──
class MockSanPhamTimKiemDao:
    """Mock SanPhamDao cho unit test tim kiem (005 US1)."""

    def __init__(self, danh_sach=None, kho=None):
        self.danh_sach = danh_sach or []
        self.kho = kho or {}

    def lay_tat_ca(self):
        """Tra toan bo SP đang kinh doanh."""
        return list(self.danh_sach)

    def tim_kiem(self, tu_khoa, category_id=None):
        """Loc theo keyword lower + category, chi IsActive=1."""
        kw = (tu_khoa or "").strip().lower()
        ket_qua = []
        for sp in self.danh_sach:
            if not sp.get("is_active", True):
                continue
            if category_id not in (None, "") and sp.get("category_id") != int(category_id):
                continue
            if kw and kw not in (sp.get("name") or "").lower():
                continue
            ket_qua.append(sp)
        return ket_qua

    def lay_thong_tin_kho(self, product_id):
        """Tra {quantity, is_active, price} hoac None."""
        return self.kho.get(int(product_id)) if product_id is not None else None

    def lay_theo_id(self, product_id):
        for sp in self.danh_sach:
            if sp.get("id") == int(product_id):
                return sp
        return None


class MockGioHangDao:
    """Mock GioHangDao cho unit test gio hang (005 US2)."""

    def __init__(self, cart_id=1, kho=None, stores=None, gio_hang=None):
        self.cart_id = cart_id
        self.kho = kho or {}
        self.stores = stores or {}
        self.gio_hang = gio_hang if gio_hang is not None else {}
        self.da_xoa_toan_bo = False

    def lay_hoac_tao_gio_hang(self, user_id):
        return self.cart_id

    def lay_store_id_san_pham(self, product_id):
        return self.stores.get(int(product_id))

    def lay_store_ids_trong_gio(self, cart_id):
        return [{"store_id": s, "store_name": f"Shop {s}"}
                for s in sorted({self.stores.get(pid) for pid in self.gio_hang
                                 if self.stores.get(pid) is not None})]

    def them_vao_gio_hang(self, cart_id, product_id, quantity, unit_price):
        self.gio_hang[int(product_id)] = self.gio_hang.get(int(product_id), 0) + int(quantity)
        return True

    def cap_nhat_tong_tien(self, cart_id):
        return True

    def xoa_toan_bo_gio(self, cart_id):
        self.gio_hang.clear()
        self.da_xoa_toan_bo = True
        return True

    def xoa_khoi_gio(self, cart_id, product_id):
        return self.gio_hang.pop(int(product_id), None) is not None

    def cap_nhat_so_luong(self, cart_id, product_id, quantity):
        if int(product_id) not in self.gio_hang:
            return False
        self.gio_hang[int(product_id)] = int(quantity)
        return True

    def lay_chi_tiet_gio_hang(self, cart_id):
        return [{"ProductId": pid, "Quantity": sl} for pid, sl in self.gio_hang.items()]


class MockDonHangCustomerDao:
    """Mock DonHangDao cho unit test thanh toan/lich su (005 US3/US4)."""

    def __init__(self, don_hang=None, chi_tiet=None, ket_qua_tao=1,
                 store_ids=None):
        self.don_hang = don_hang or {}
        self.chi_tiet = chi_tiet or {}
        self.ket_qua_tao = ket_qua_tao
        self.store_ids = store_ids or {}

    def lay_store_ids_cua_san_pham(self, product_ids):
        return list({self.store_ids.get(int(pid), 1) for pid in (product_ids or [])})

    def tao_don_hang(self, dh, items):
        return self.ket_qua_tao

    def lay_chi_tiet_don_hang(self, order_id):
        don = self.don_hang.get(int(order_id))
        if not don:
            return None
        return {"don": don, "items": self.chi_tiet.get(int(order_id), [])}

    def lay_don_hang_cua_user(self, ma_user):
        ket_qua = [d for d in self.don_hang.values() if d.get("UserId") == ma_user]
        ket_qua.sort(key=lambda d: d.get("CreatedAt", ""), reverse=True)
        return ket_qua


# ── Fake in-memory cho integration test customer ──
class FakeSanPhamTimKiemStore:
    """Fake store san pham in-memory cho tim kiem + kho (005 US1/US2)."""

    def __init__(self, san_pham=None):
        self.san_pham = san_pham or {}

    def lay_tat_ca(self):
        return [dict(v) for v in self.san_pham.values() if v.get("is_active")]

    def tim_kiem(self, tu_khoa, category_id=None):
        kw = (tu_khoa or "").strip().lower()
        ket_qua = []
        for sp in self.san_pham.values():
            if not sp.get("is_active"):
                continue
            if category_id not in (None, "") and sp.get("category_id") != int(category_id):
                continue
            if kw and kw not in (sp.get("name") or "").lower():
                continue
            ket_qua.append(dict(sp))
        return ket_qua

    def lay_thong_tin_kho(self, product_id):
        sp = self.san_pham.get(int(product_id))
        if not sp:
            return None
        return {"quantity": sp.get("quantity", 0),
                "is_active": sp.get("is_active", True),
                "price": sp.get("price", 0)}

    def lay_theo_id(self, product_id):
        sp = self.san_pham.get(int(product_id))
        return dict(sp) if sp else None


class FakeGioHangStore:
    """Fake store gio hang in-memory: {cart_id: {product_id: qty}}."""

    def __init__(self, san_pham=None, gia=None):
        self.san_pham = san_pham or {}
        self.gia = gia or {}
        self.gio = {}

    def _cart(self, cart_id):
        return self.gio.setdefault(int(cart_id), {})

    def lay_hoac_tao_gio_hang(self, user_id):
        return int(user_id)

    def lay_store_id_san_pham(self, product_id):
        sp = self.san_pham.get(int(product_id))
        return sp.get("store_id") if sp else None

    def lay_store_ids_trong_gio(self, cart_id):
        cart = self.gio.get(int(cart_id), {})
        stores = {self.san_pham.get(pid, {}).get("store_id") for pid in cart}
        return [{"store_id": s, "store_name": f"Shop {s}"} for s in sorted(stores) if s]

    def them_vao_gio_hang(self, cart_id, product_id, quantity, unit_price):
        cart = self._cart(cart_id)
        cart[int(product_id)] = cart.get(int(product_id), 0) + int(quantity)
        return True

    def cap_nhat_tong_tien(self, cart_id):
        return True

    def xoa_toan_bo_gio(self, cart_id):
        self.gio[int(cart_id)] = {}
        return True

    def xoa_khoi_gio(self, cart_id, product_id):
        cart = self.gio.get(int(cart_id), {})
        return cart.pop(int(product_id), None) is not None

    def cap_nhat_so_luong(self, cart_id, product_id, quantity):
        cart = self.gio.get(int(cart_id), {})
        if int(product_id) not in cart:
            return False
        cart[int(product_id)] = int(quantity)
        return True

    def lay_chi_tiet_gio_hang(self, cart_id):
        cart = self.gio.get(int(cart_id), {})
        ket_qua = []
        for pid, sl in cart.items():
            sp = self.san_pham.get(int(pid), {})
            ket_qua.append({"CartId": int(cart_id), "ProductId": pid,
                            "Quantity": sl,
                            "UnitPrice": sp.get("price", 0),
                            "ProductName": sp.get("name", ""),
                            "Emoji": sp.get("emoji", "📦")})
        return ket_qua


class FakeDonHangCustomerStore:
    """Fake store don hang in-memory cho checkout/hoa don/lich su (005 US3/US4)."""

    def __init__(self, san_pham=None, don_hang=None, next_id=1):
        self.san_pham = san_pham or {}
        self.don_hang = don_hang or {}
        self.next_id = next_id

    def lay_store_ids_cua_san_pham(self, product_ids):
        return list({self.san_pham.get(int(pid), {}).get("store_id", 1)
                     for pid in (product_ids or [])})

    def tao_don_hang(self, dh, items):
        for it in items:
            sp = self.san_pham.get(int(it.ProductId))
            if not sp:
                return {"error": "not_found", "product_name": f"#{it.ProductId}"}
            if int(it.Quantity or 0) > int(sp.get("quantity", 0)):
                return {"error": "out_of_stock", "product_name": sp.get("name"),
                        "available": sp.get("quantity", 0)}
        for it in items:
            sp = self.san_pham.get(int(it.ProductId))
            sp["quantity"] = int(sp.get("quantity", 0)) - int(it.Quantity or 0)
        nid = self.next_id
        self.next_id += 1
        self.don_hang[nid] = {"OrderId": nid, "UserId": int(dh.UserId),
                              "Status": "Pending",
                              "ReceiverName": dh.ReceiverName,
                              "ReceiverPhone": dh.ReceiverPhone,
                              "ShippingAddress": dh.ShippingAddress,
                              "PaymentMethod": dh.PaymentMethod,
                              "SubTotal": float(dh.SubTotal or 0),
                              "ShippingFee": float(dh.ShippingFee or 0),
                              "DiscountAmount": float(dh.DiscountAmount or 0),
                              "TotalAmount": float(dh.TotalAmount or 0),
                              "CreatedAt": f"2026-09-18 10:00:{nid:02d}",
                              "Items": [{"ProductId": int(it.ProductId),
                                         "ProductName": it.ProductName,
                                         "Emoji": it.Emoji,
                                         "Quantity": int(it.Quantity or 0),
                                         "UnitPrice": float(it.UnitPrice or 0),
                                         "TotalPrice": float(it.TotalPrice or 0)}
                                        for it in items]}
        return nid

    def lay_chi_tiet_don_hang(self, order_id):
        don = self.don_hang.get(int(order_id))
        if not don:
            return None
        return {"don": don, "items": don.get("Items", [])}

    def lay_don_hang_cua_user(self, ma_user):
        ket_qua = [d for d in self.don_hang.values() if d.get("UserId") == ma_user]
        ket_qua.sort(key=lambda d: d.get("CreatedAt", ""), reverse=True)
        return ket_qua


@pytest.fixture
def customer_client(monkeypatch):
    """Flask test_client voi DAO customer da gan — KHÔNG chạm PobbyDB thật."""
    import app as app_module

    def _tao(user_dao=None, san_pham_store=None, gio_hang_store=None,
             don_hang_store=None):
        from back_end.BUS.UserBus import UserBus
        from back_end.BUS.SanPhamBus import SanPhamBus
        from back_end.BUS.GioHangBus import GioHangBus
        from back_end.BUS.DonHangBus import DonHangBus
        if user_dao is not None:
            ub = UserBus()
            ub.dao = user_dao
            monkeypatch.setattr(app_module, "user_bus", ub)
        if san_pham_store is not None:
            sb = SanPhamBus()
            sb.dao = san_pham_store
            # Gán kho cho GioHangBus khi dùng chung store tìm kiếm
            monkeypatch.setattr(app_module, "san_pham_bus", sb)
        if gio_hang_store is not None:
            cb = GioHangBus()
            cb.dao = gio_hang_store
            # BUS giỏ cần đọc kho qua DAO sản phẩm: gắn dao phụ san_pham_dao
            if san_pham_store is not None:
                cb.san_pham_dao = san_pham_store
            monkeypatch.setattr(app_module, "cart_bus", cb)
        if don_hang_store is not None:
            db = DonHangBus()
            db.dao = don_hang_store
            monkeypatch.setattr(app_module, "don_hang_bus", db)
        app_module.app.config["TESTING"] = True
        return app_module.app.test_client()

    return _tao