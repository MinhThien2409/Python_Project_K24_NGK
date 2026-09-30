# -*- coding: utf-8 -*-
"""Kiểm tra source database canonical hiện tại.

Canonical database của project là:
    Database/schema_mysql.sql
    Database/seed_demo_mysql.sql
    Database/database_mysql.sql

Test này không phụ thuộc các dump SQL Server legacy đã được loại khỏi source chính.
"""
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DATABASE_DIR = REPO_ROOT / "Database"

SCHEMA = DATABASE_DIR / "schema_mysql.sql"
SEED = DATABASE_DIR / "seed_demo_mysql.sql"
COMBINED = DATABASE_DIR / "database_mysql.sql"

ROLE_IDS = {1, 2, 3, 4}
ROLE_NAMES = {
    1: "Admin",
    2: "Quản lý",
    3: "Seller",
    4: "Customer",
}


def _read(path):
    assert path.exists(), f"Thiếu canonical database source: {path}"
    return path.read_text(encoding="utf-8")


def _extract_roles(seed):
    match = re.search(
        r"INSERT INTO Roles \(RoleId, RoleName\) VALUES\s*(.*?);",
        seed,
        re.S,
    )
    assert match, "seed_demo_mysql.sql thiếu dữ liệu Roles"
    return {
        int(role_id): role_name
        for role_id, role_name in re.findall(
            r"\((\d+),\s*'([^']+)'\)", match.group(1)
        )
    }


def _extract_account_roles(seed):
    match = re.search(
        r"INSERT INTO Accounts \(UserId, Username, Password, Role_Id, trang_thai\) VALUES\s*(.*?);",
        seed,
        re.S,
    )
    assert match, "seed_demo_mysql.sql thiếu dữ liệu Accounts"
    return {
        int(user_id): int(role_id)
        for user_id, role_id in re.findall(
            r"\((\d+),\s*'[^']+',\s*'[^']+',\s*(\d+),", match.group(1)
        )
    }


def test_canonical_database_sources_ton_tai_va_khong_rong():
    for path in (SCHEMA, SEED, COMBINED):
        assert _read(path).strip(), f"{path.name} rỗng"


def test_canonical_roles_dung_4_vai_tro():
    roles = _extract_roles(_read(SEED))
    assert roles == ROLE_NAMES


def test_canonical_accounts_chi_tham_chieu_vai_tro_hop_le():
    accounts = _extract_account_roles(_read(SEED))
    assert accounts
    assert set(accounts.values()) <= ROLE_IDS
    assert accounts.get(1) == 1
    assert sum(role == 1 for role in accounts.values()) == 1


def test_canonical_store_owner_la_seller():
    seed = _read(SEED)
    store_block = re.search(
        r"INSERT INTO Stores \(StoreId, StoreName, Address, UserId, Phone, Category, Description, IsActive, CreatedAt\) VALUES\s*(.*?);",
        seed,
        re.S,
    )
    assert store_block, "seed_demo_mysql.sql thiếu dữ liệu Stores"
    owners = {
        int(user_id)
        for user_id in re.findall(
            r"\(\d+,\s*'[^']*',\s*'[^']*',\s*(\d+),", store_block.group(1)
        )
    }
    accounts = _extract_account_roles(seed)
    assert owners
    assert all(accounts.get(user_id) == 3 for user_id in owners)


def test_canonical_accounts_co_trang_thai_active_va_banned_demo():
    seed = _read(SEED)
    account_block = re.search(
        r"INSERT INTO Accounts \(UserId, Username, Password, Role_Id, trang_thai\) VALUES\s*(.*?);",
        seed,
        re.S,
    )
    assert account_block
    assert "'active'" in account_block.group(1)
    assert "'banned'" in account_block.group(1)


def test_canonical_seed_khong_con_rating():
    assert "Rating" not in _read(SCHEMA)
    assert "Rating" not in _read(SEED)


def test_khong_con_role_id_13_trong_backend():
    pattern = re.compile(r"Role_?[iI]d\s*=\s*13")
    violations = []
    for path in REPO_ROOT.joinpath("back_end").rglob("*.py"):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                violations.append(f"{path.name}:{line_no}:{line.strip()}")
    assert not violations, f"Còn gán Role_Id=13: {violations}"


def test_khong_ton_tai_route_tao_admin():
    source = REPO_ROOT.joinpath("app.py").read_text(encoding="utf-8")
    assert "tao_admin" not in source.lower()
    assert "them_admin" not in source.lower()
    assert "/api/admin" not in source.lower()
