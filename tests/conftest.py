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

    Cho phép cấu hình user trả về của dang_nhap theo từng kịch bản test.
    """

    def __init__(self, user=None, banned=None, role_none=False):
        self.user = user
        self.banned = banned
        self.role_none = role_none

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


@pytest.fixture
def mock_user_dao():
    """Fixture trả về factory tạo MockUserDao theo kịch bản."""
    def _tao(user=None, banned=None, role_none=False):
        return MockUserDao(user=user, banned=banned, role_none=role_none)
    return _tao