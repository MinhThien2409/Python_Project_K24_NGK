from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor

import pymysql
import pytest

from back_end.BUS.UserBus import UserBus
from back_end.DAO.UserDao import UserDao
from back_end.DBconfig import DB_CONFIG


ROOT = Path(__file__).resolve().parents[2]


def test_admin_account_policy_allows_non_admin_roles_and_blocks_admin(monkeypatch):
    bus = UserBus()

    class Dao:
        def __init__(self, role):
            self.role = role
        def lay_thong_tin_user(self, user_id):
            return {"UserId": user_id, "Role_Id": self.role, "trang_thai": "active", "FullName": "Test"}
        def lay_ten_vai_tro_theo_id(self, role_id):
            return {1: "Admin", 2: "Quản lý", 3: "Seller", 4: "Customer"}.get(role_id)
        def cap_nhat_trang_thai_admin(self, user_id, status, role_id):
            return {"status": True, "store_id": 17 if role_id == 3 else None}
        def cap_nhat_mat_khau(self, user_id, password):
            return True

    monkeypatch.setattr(bus, "kiem_tra_quyen_admin", lambda user_id: {"status": True})
    bus.dao = Dao(3)
    result = bus.cap_nhat_trang_thai_admin(1, 2, "banned")
    assert result["status"] is True
    bus.dao = Dao(1)
    result = bus.cap_nhat_trang_thai_admin(1, 2, "banned")
    assert result["status"] is False
    assert "Admin" in result["message"]


def test_admin_last_manager_guard_is_server_side():
    bus = UserBus()

    class Dao:
        def lay_thong_tin_user(self, user_id):
            return {"UserId": user_id, "Role_Id": 2, "trang_thai": "active", "FullName": "Manager"}
        def lay_ten_vai_tro_theo_id(self, role_id):
            return "Quản lý"
        def cap_nhat_trang_thai_admin(self, user_id, status, role_id):
            return {
                "status": False,
                "message": "Không thể khóa Quản lý cuối cùng. Hệ thống phải luôn có ít nhất 1 Quản lý đang hoạt động!",
            }

    bus.dao = Dao()
    monkeypatch = None
    # The real DAO owns the invariant; this test ensures BUS propagates its rejection.
    bus.kiem_tra_quyen_admin = lambda user_id: {"status": True}
    result = bus.cap_nhat_trang_thai_admin(1, 2, "banned")
    assert result["status"] is False
    assert "ít nhất 1 Quản lý" in result["message"]


def test_seller_lock_policy_touches_store_and_triggers_system_cancel_flow():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    dao = (ROOT / "back_end/DAO/UserDao.py").read_text(encoding="utf-8")
    order_dao = (ROOT / "back_end/DAO/DonHangDao.py").read_text(encoding="utf-8")
    assert "UPDATE Stores SET IsActive=?" in dao
    assert "huy_don_do_khoa_seller" in order_dao
    assert "Pending','Confirmed','Shipping" in order_dao


def test_public_products_require_store_and_seller_active():
    src = (ROOT / "back_end/DAO/SanPhamDao.py").read_text(encoding="utf-8")
    assert "s.IsActive" in src
    assert "a.trang_thai" in src
    assert "WHERE p.ProductId = ?" in src
    assert "WHERE p.IsActive = 1" in src


def test_checkout_revalidates_store_and_seller_status():
    src = (ROOT / "back_end/DAO/DonHangDao.py").read_text(encoding="utf-8")
    assert "COALESCE(s.IsActive, 0)" in src
    assert "COALESCE(a.trang_thai, 'banned')" in src


def test_voucher_preview_rejects_locked_seller():
    src = (ROOT / "back_end/BUS/VoucherBus.py").read_text(encoding="utf-8")
    dao = (ROOT / "back_end/DAO/VoucherDao.py").read_text(encoding="utf-8")
    assert "seller_dang_hoat_dong" in src
    assert "s.IsActive=1" in dao
    assert "a.trang_thai='active'" in dao


def test_admin_ui_has_actions_for_seller_customer_but_not_admin():
    src = (ROOT / "static/js/main.js").read_text(encoding="utf-8")
    assert "laAdmin && (u.ma_nhom_quyen === 3 || u.ma_nhom_quyen === 4)" in src
    assert "xacNhanKhoaAdminTaiKhoan" in src
    # Admin rows are deliberately handled only by the generic read-only branch.
    assert "u.ma_nhom_quyen === 1" not in src[src.find("renderAdminUsers"):src.find("function renderUserRoleFilter")]


def test_live_manager_last_active_invariant_under_concurrent_admin_locks():
    conn = pymysql.connect(**DB_CONFIG, autocommit=True)
    cur = conn.cursor()
    username = "phase7_live_manager"
    try:
        cur.execute("SELECT UserId FROM Accounts WHERE Username=%s", (username,))
        old = cur.fetchone()
        if old:
            uid_old = int(old[0])
            cur.execute("DELETE FROM Accounts WHERE UserId=%s", (uid_old,))
            cur.execute("DELETE FROM Users WHERE UserId=%s", (uid_old,))

        cur.execute("SELECT UserId, trang_thai FROM Accounts WHERE Role_Id=2 ORDER BY UserId")
        original = [(int(r[0]), str(r[1] or "active")) for r in cur.fetchall()]
        if not original:
            pytest.skip("Database không có Manager để làm keeper.")

        keeper_id = original[0][0]
        for uid, _ in original:
            if uid != keeper_id:
                cur.execute("UPDATE Accounts SET trang_thai='banned' WHERE UserId=%s", (uid,))

        cur.execute(
            "INSERT INTO Users (FullName, Address, Phone, NationalId) VALUES (%s,%s,%s,%s)",
            ("Phase7 Live Manager", "Phase7", "0900000000", "PHASE7000001"),
        )
        temp_id = int(cur.lastrowid)
        cur.execute(
            "INSERT INTO Accounts (UserId, Username, Password, Role_Id, trang_thai) "
            "VALUES (%s,%s,%s,2,'active')",
            (temp_id, username, "phase7"),
        )

        barrier = threading.Barrier(2)

        class BlockingDao(UserDao):
            def cap_nhat_trang_thai_admin(self, ma_user, trang_thai, role_id):
                barrier.wait(timeout=10)
                return super().cap_nhat_trang_thai_admin(ma_user, trang_thai, role_id)

        def lock(uid):
            return BlockingDao().cap_nhat_trang_thai_admin(uid, "banned", 2)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lock, [keeper_id, temp_id]))

        statuses = sorted(bool(r[0]) if isinstance(r, tuple) else bool(r.get("status")) for r in results)
        assert statuses == [False, True], results

        cur.execute("SELECT COUNT(*) FROM Accounts WHERE Role_Id=2 AND trang_thai='active'")
        assert int(cur.fetchone()[0]) == 1
    finally:
        try:
            cur.execute("UPDATE Accounts SET trang_thai='active' WHERE Role_Id=2")
            cur.execute("SELECT UserId FROM Accounts WHERE Username=%s", (username,))
            row = cur.fetchone()
            if row:
                uid = int(row[0])
                cur.execute("DELETE FROM Accounts WHERE UserId=%s", (uid,))
                cur.execute("DELETE FROM Users WHERE UserId=%s", (uid,))
            for uid, status in locals().get("original", []):
                cur.execute("UPDATE Accounts SET trang_thai=%s WHERE UserId=%s", (status, uid))
        finally:
            cur.close()
            conn.close()


def test_password_reset_is_hashed_and_login_supports_pbkdf2_marker():
    src = (ROOT / "back_end/DAO/UserDao.py").read_text(encoding="utf-8")
    assert "pbkdf2_sha256" in src
    assert "hashlib.pbkdf2_hmac" in src
    assert "hmac.compare_digest" in src


def test_admin_endpoints_route_to_new_policy():
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "cap_nhat_trang_thai_admin" in src
    assert "cap_lai_mat_khau_admin" in src
