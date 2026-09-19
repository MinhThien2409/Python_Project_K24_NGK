# -*- coding: utf-8 -*-
"""Test tĩnh kiểm tra 2 file dump Database/database.sql và Database/back_up.sql
theo chuẩn mới: chỉ còn 4 vai trò (1=Admin, 2=Quản lý, 3=Seller, 4=Customer),
không còn bảng Permissions/Modules, mọi Users chỉ tham chiếu vai trò hợp lệ,
user1 luôn là Admin, chủ gian hàng là Seller, và có ràng buộc
CK_Users_Admin_KhongDuocKhoa (T007, T008, T012, T016 liên quan seed dữ liệu)."""

import io
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DUMP_DIR = REPO_ROOT / "Database"

DUMP_FILES = ["database.sql", "back_up.sql"]

ROLE_ID_ADMIN = 1
ROLE_ID_QUAN_LY = 2
ROLE_ID_SELLER = 3
ROLE_ID_CUSTOMER = 4
ROLE_IDS_HOP_LE = {ROLE_ID_ADMIN, ROLE_ID_QUAN_LY, ROLE_ID_SELLER, ROLE_ID_CUSTOMER}

TEN_VAI_TRO = {
    ROLE_ID_ADMIN: "Admin",
    ROLE_ID_QUAN_LY: "Quản lý",
    ROLE_ID_SELLER: "Seller",
    ROLE_ID_CUSTOMER: "Customer",
}

CK_ADMIN_NOT_BANNED = "Admin_KhongDuocKhoa"

RE_ROLE = re.compile(
    r"INSERT \[dbo\]\.\[Roles\] \(\[RoleId\], \[RoleName\]\) VALUES \((\d+), N'([^']*)'\)"
)
# 008-split-user-table: hồ sơ ở bảng Users (5 cột), đăng nhập ở bảng Accounts (6 cột)
RE_USER_HO_SO = re.compile(
    r"INSERT \[dbo\]\.\[Users\] [^\n]*?VALUES \((\d+), N'[^']*', (?:N'[^']*'|NULL), "
    r"(?:N'[^']*'|NULL), (?:N'[^']*'|NULL)\)"
)
RE_ACCOUNT = re.compile(
    r"INSERT \[dbo\]\.\[Accounts\] [^\n]*?VALUES \((\d+), N'[^']*', N'[^']*', (\d+)(?:, N'[^']*')?\)"
)
RE_STORE = re.compile(
    r"INSERT \[dbo\]\.\[Stores\] [^\n]*?VALUES \("
    r"(\d+), N'[^']*', (?:N'[^']*'|NULL), (\d+), (?:N'[^']*'|NULL), "
    r"(?:N'[^']*'|NULL), (?:N'[^']*'|NULL), (\d+), CAST\(N'[^']*' AS DateTime\)\)"
)


def load_dump(ten_file):
    duong_dan = DUMP_DIR / ten_file
    assert duong_dan.exists(), f"Thiếu file dump: {duong_dan}"
    raw = duong_dan.read_bytes()
    if raw[:2] == b"\xff\xfe":
        return raw.decode("utf-16")
    if raw[:3] == b"\xef\xbb\xbf":
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8-sig", errors="replace")


def _lay_roles(noi_dung):
    return {int(i): ten for i, ten in RE_ROLE.findall(noi_dung)}


def _lay_users(noi_dung):
    """Vai trò của từng người dùng lấy từ Accounts (Role_Id nằm ở bảng đăng nhập)."""
    return {int(uid): int(role) for uid, role in RE_ACCOUNT.findall(noi_dung)}

def _lay_ho_so(noi_dung):
    """Danh sách UserId có hồ sơ ở bảng Users."""
    return {int(uid) for uid in RE_USER_HO_SO.findall(noi_dung)}


def _lay_stores(noi_dung):
    return [(int(sid), int(uid), int(active)) for sid, uid, active in RE_STORE.findall(noi_dung)]


@pytest.fixture(params=DUMP_FILES)
def dump(request):
    return request.param, load_dump(request.param)


@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_file_dump_ton_tai_va_khong_rong(ten_file):
    noi_dung = load_dump(ten_file)
    assert noi_dung.strip(), f"File {ten_file} rỗng"


# ── T007: Chỉ còn 4 vai trò chuẩn ──────────────────────────────────────────────
@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_du_lieu_roles_dung_4_vai_tro_chuan(ten_file):
    roles = _lay_roles(load_dump(ten_file))
    assert set(roles.keys()) == ROLE_IDS_HOP_LE, (
        f"File {ten_file}: vai trò phải đúng {{1,2,3,4}}, thực tế {sorted(roles.keys())}"
    )
    for role_id, role_name in TEN_VAI_TRO.items():
        assert roles[role_id] == role_name, (
            f"File {ten_file}: role {role_id} phải là {role_name!r}, thực tế {roles[role_id]!r}"
        )


@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_khong_con_vai_tro_cu_ngoai_4_vai_tro_chuan(ten_file):
    noi_dung = load_dump(ten_file)
    role_ids_du = [role_id for role_id in range(5, 21)
                   if re.search(rf"INSERT \[dbo\]\.\[Roles\][^\n]*\) VALUES \({role_id}, N'", noi_dung)]
    assert not role_ids_du, f"File {ten_file}: vẫn còn vai trò cũ {sorted(role_ids_du)}"
    for tu_khoa in ("Warehouse Staff", "Content Creator", "Kiểm duyệt", "Shipper"):
        assert tu_khoa not in noi_dung, f"File {ten_file}: vẫn còn tên vai trò cũ {tu_khoa!r}"


# ── T008: Mọi Users chỉ tham chiếu 4 vai trò; user1 luôn là Admin ─────────────
@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_moi_user_chi_tham_chieu_vai_tro_hop_le(ten_file):
    users = _lay_users(load_dump(ten_file))
    assert users, f"File {ten_file}: không tìm thấy dòng INSERT Accounts nào"
    sai = {uid: role for uid, role in users.items() if role not in ROLE_IDS_HOP_LE}
    assert not sai, f"File {ten_file}: users có Role_Id ngoài {{1,2,3,4}}: {sai}"

@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_hai_bang_sinh_1_1(ten_file):
    """008: mỗi hồ sơ Users khớp đúng một dòng Accounts (UserId 1-1, không mồ côi)."""
    noi_dung = load_dump(ten_file)
    ho_so = _lay_ho_so(noi_dung)
    tai_khoan = _lay_users(noi_dung)
    assert ho_so and tai_khoan, (
        f"File {ten_file}: Users hồ sơ hoặc Accounts không có dòng INSERT nào"
    )
    assert ho_so == set(tai_khoan), (
        f"File {ten_file}: UserId hai bảng lệch nhau — thiếu hồ sơ {sorted(ho_so ^ set(tai_khoan))}"
    )


@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_user1_luon_la_admin(ten_file):
    users = _lay_users(load_dump(ten_file))
    assert users.get(1) == ROLE_ID_ADMIN, (
        f"File {ten_file}: user1 phải là Admin (Role_Id=1), thực tế {users.get(1)}"
    )


@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_admin_chi_co_mot_nguoi_la_user1(ten_file):
    users = _lay_users(load_dump(ten_file))
    ds_admin = [uid for uid, role in users.items() if role == ROLE_ID_ADMIN]
    assert ds_admin == [ROLE_ID_ADMIN], (
        f"File {ten_file}: chỉ user1 là Admin, thực tế {ds_admin}"
    )


# ── T008: Không còn bảng/đối tượng Permissions, Modules ───────────────────────
@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_khong_con_bang_permissions_modules(ten_file):
    noi_dung = load_dump(ten_file)
    for tu_khoa in (
        "[dbo].[Permissions]",
        "[dbo].[Modules]",
        "UQ__Modules",
        "FK_Modules_Modules",
        "ModuleCode",
    ):
        assert tu_khoa not in noi_dung, f"File {ten_file}: vẫn còn {tu_khoa!r}"


# ── T032 (seed): ràng buộc không khóa Admin ───────────────────────────────────
@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_rang_buoc_khong_duoc_khoa_admin(ten_file):
    noi_dung = load_dump(ten_file)
    assert CK_ADMIN_NOT_BANNED in noi_dung, (
        f"File {ten_file}: thiếu ràng buộc {CK_ADMIN_NOT_BANNED}"
    )
    assert "N'banned'" in noi_dung, f"File {ten_file}: thiếu giá trị N'banned' trong CHECK"


@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_rang_buoc_chong_du_lieu_lai(ten_file):
    noi_dung = load_dump(ten_file)
    assert noi_dung.count(CK_ADMIN_NOT_BANNED) == 1, (
        f"File {ten_file}: {CK_ADMIN_NOT_BANNED} phải xuất hiện đúng 1 lần"
    )


# ── T012: Chủ gian hàng (Stores.UserId) là Seller ─────────────────────────────
@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_chu_gian_hang_la_seller(ten_file):
    noi_dung = load_dump(ten_file)
    users = _lay_users(noi_dung)
    stores = _lay_stores(noi_dung)
    assert stores, f"File {ten_file}: không tìm thấy dòng INSERT Stores nào"
    chu_gian_hang = {uid for _, uid, _ in stores}
    cho_sai = {uid for uid in chu_gian_hang if users.get(uid) != ROLE_ID_SELLER}
    assert not cho_sai, (
        f"File {ten_file}: chủ gian hàng {sorted(cho_sai)} không phải Seller"
    )


@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_co_cua_hang_ngung_hoat_dong_cua_seller(ten_file):
    noi_dung = load_dump(ten_file)
    users = _lay_users(noi_dung)
    stores = _lay_stores(noi_dung)
    cua_hang_tat = [sid for sid, uid, active in stores if active == 0]
    assert cua_hang_tat, f"File {ten_file}: cần ít nhất 1 Store có IsActive = 0"
    for sid in cua_hang_tat:
        uid = next(u for s, u, a in stores if s == sid)
        assert users.get(uid) == ROLE_ID_SELLER, (
            f"File {ten_file}: store {sid} ngừng hoạt động nhưng chủ {uid} không phải Seller"
        )


# ── T008/T032 (seed): bảng Accounts có cột trang_thai (database.sql thêm mới) ─
def test_database_sql_co_cot_trang_thai():
    noi_dung = load_dump("database.sql")
    assert re.search(r"\[trang_thai\] \[varchar\]\(10\) NULL", noi_dung), (
        "database.sql cần cột [trang_thai] [varchar](10) NULL"
    )
    assert "DEFAULT ('active') FOR [trang_thai]" in noi_dung, (
        "database.sql cần DEFAULT ('active') FOR [trang_thai]"
    )


def test_back_up_sql_giu_nguyen_cot_trang_thai():
    noi_dung = load_dump("back_up.sql")
    assert re.search(r"\[trang_thai\] \[varchar\]\(10\) NULL", noi_dung)
    assert "DEFAULT ('active') FOR [trang_thai]" in noi_dung


# ── T020 (US2): DEFAULT Status của SellerRequests chuẩn hóa chữ thường ──────
RE_DEFAULT_STATUS = re.compile(
    r"DEFAULT\s+\(\s*'([Pp]ending)'\s*\)\s*FOR\s*\[Status\]"
)


@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_seller_requests_status_default_chu_thuong(ten_file):
    noi_dung = load_dump(ten_file)
    dong_alter = [dong for dong in noi_dung.splitlines()
                  if "SellerRequests" in dong and "DEFAULT" in dong and "FOR [Status]" in dong]
    assert dong_alter, f"File {ten_file}: thiếu ALTER TABLE SellerRequests ADD DEFAULT ... FOR [Status]"
    for dong in dong_alter:
        hop_le = RE_DEFAULT_STATUS.findall(dong)
        assert hop_le, f"File {ten_file}: dòng không khớp regex {dong.strip()}"
        assert all(gia_tri == "pending" for gia_tri in hop_le), (
            f"File {ten_file}: DEFAULT Status phải là ('pending') chữ thường, thực tế {dong.strip()}"
        )


# ── T031 (US3): ràng buộc mới không khóa Quản lý + không còn Role_id=13 ──────
CK_QUAN_LY_NOT_BANNED = "QuanLy_KhongDuocKhoa"

RE_CHECK_QUAN_LY = re.compile(r"CHECK\s*\(NOT\s*\(trang_thai\s*=\s*N?'banned'\s*AND\s*Role_Id\s*=\s*2\)\)")


@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_rang_buoc_khong_duoc_khoa_quan_ly(ten_file):
    noi_dung = load_dump(ten_file)
    assert CK_QUAN_LY_NOT_BANNED in noi_dung, (
        f"File {ten_file}: thiếu ràng buộc {CK_QUAN_LY_NOT_BANNED}"
    )
    assert RE_CHECK_QUAN_LY.search(noi_dung), (
        f"File {ten_file}: CHECK {CK_QUAN_LY_NOT_BANNED} phải chặn Role_Id=2 bị banned"
    )
    assert noi_dung.count(CK_QUAN_LY_NOT_BANNED) == 1, (
        f"File {ten_file}: {CK_QUAN_LY_NOT_BANNED} phải xuất hiện đúng 1 lần"
    )


def test_khong_con_role_id_13_trong_backend():
    """Grep toàn `back_end/`: không còn lệnh gán Role_id=13 (bug duyệt seller đã sửa)."""
    bat_phep = re.compile(r"Role_?[iI]d\s*=\s*13")
    for duong_dan in REPO_ROOT.joinpath("back_end").rglob("*.py"):
        noi_dung = duong_dan.read_text(encoding="utf-8")
        loi = [dong for dong in noi_dung.splitlines() if bat_phep.search(dong)]
        assert not loi, f"{duong_dan.name}: vẫn còn gán Role_Id=13: {loi}"


# ── T008 (003-US1): seed đúng 1 Admin + trigger + CHECK ───────────────────────
TRIGGER_MOT_ADMIN = "TRG_Accounts_ChiMotAdmin"


@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_seed_chi_mot_admin_user1(ten_file):
    users = _lay_users(load_dump(ten_file))
    ds_admin = [uid for uid, role in users.items() if role == ROLE_ID_ADMIN]
    assert ds_admin == [1], (
        f"File {ten_file}: chỉ user1 là Admin, thực tế {ds_admin}"
    )


@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_co_trigger_chi_mot_admin(ten_file):
    noi_dung = load_dump(ten_file)
    assert TRIGGER_MOT_ADMIN in noi_dung, (
        f"File {ten_file}: thiếu trigger {TRIGGER_MOT_ADMIN}"
    )
    assert noi_dung.count(TRIGGER_MOT_ADMIN) >= 1


@pytest.mark.parametrize("ten_file", DUMP_FILES)
def test_giu_hai_check_chong_khoa_admin_quan_ly(ten_file):
    noi_dung = load_dump(ten_file)
    assert CK_ADMIN_NOT_BANNED in noi_dung
    assert CK_QUAN_LY_NOT_BANNED in noi_dung


def test_khong_ton_tai_route_tao_admin():
    """Không tồn tại endpoint tạo Admin (chỉ POST /api/quan-ly gán cứng Role 2)."""
    noi_dung = REPO_ROOT.joinpath("app.py").read_text(encoding="utf-8")
    assert "tao_admin" not in noi_dung.lower()
    assert "them_admin" not in noi_dung.lower()
    assert "/api/admin" not in noi_dung.lower()