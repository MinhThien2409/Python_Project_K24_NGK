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
                 thong_tin=None, mat_khau_moi_ok=True, trang_thai_ok=True):
        self.user = user
        self.banned = banned
        self.role_none = role_none
        self.thong_tin = thong_tin
        self.mat_khau_moi_ok = mat_khau_moi_ok
        self.trang_thai_ok = trang_thai_ok

    def dang_nhap(self, username, password):
        if self.role_none:
            return {"role_none": True}
        if self.banned:
            return {"banned": True}
        return self.user

    def kiem_tra_tendangnhap_ton_tai(self, tendangnhap):
        return False

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
             thong_tin=None, mat_khau_moi_ok=True, trang_thai_ok=True):
        return MockUserDao(
            user=user, banned=banned, role_none=role_none,
            thong_tin=thong_tin, mat_khau_moi_ok=mat_khau_moi_ok,
            trang_thai_ok=trang_thai_ok
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
        if username in self.mat_khau and self.mat_khau[username] != password:
            return None
        thong_tin = self.thong_tin.get(user.ma_user, {})
        if thong_tin.get('trang_thai') == 'banned':
            return {"banned": True}
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
                self.mat_khau[username] = mat_khau_moi
                return True
        return False

    def cap_nhat_trang_thai(self, ma_user, trang_thai):
        thong_tin = self.thong_tin.get(ma_user)
        if not thong_tin:
            return False
        thong_tin['trang_thai'] = trang_thai
        return True


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
    from back_end.DAO.UserDao import UserDao

    def _gan(user_dao=None, danh_muc_dao=None, gian_hang_dao=None):
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
        return user_dao, danh_muc_dao, gian_hang_dao

    return _gan