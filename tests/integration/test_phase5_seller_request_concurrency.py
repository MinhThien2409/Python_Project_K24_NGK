# -*- coding: utf-8 -*-
"""Phase 5 — T58 duplicate seller request + T63 approval concurrency."""
import threading
from concurrent.futures import ThreadPoolExecutor

import pymysql
import pytest

from back_end.DBconfig import DB_CONFIG
from back_end.DAO.GianHangDao import GianHangDao
from back_end.DAO.GianHangDao import KET_QUA_OK, KET_QUA_DA_XU_LY


def _conn():
    return pymysql.connect(**DB_CONFIG, autocommit=True)


@pytest.fixture
def live_seller_request():
    conn = _conn()
    cur = conn.cursor()
    username = "phase5_live_user"
    cur.execute("SELECT UserId FROM Accounts WHERE Username=%s", (username,))
    old = cur.fetchone()
    if old:
        uid = old[0]
        cur.execute("DELETE FROM SellerRequests WHERE UserId=%s", (uid,))
        cur.execute("DELETE FROM Stores WHERE UserId=%s", (uid,))
        cur.execute("DELETE FROM Accounts WHERE UserId=%s", (uid,))
        cur.execute("DELETE FROM Users WHERE UserId=%s", (uid,))
    cur.execute(
        "INSERT INTO Users (FullName, Address, Phone, NationalId) VALUES (%s,%s,%s,%s)",
        ("Phase5 Test User", "Phase5", "0900000000", "PHASE5000001"),
    )
    uid = cur.lastrowid
    cur.execute(
        "INSERT INTO Accounts (UserId, Username, Password, Role_Id, trang_thai) "
        "VALUES (%s,%s,%s,4,'active')",
        (uid, username, "phase5"),
    )
    cur.execute(
        "INSERT INTO SellerRequests "
        "(UserId, ShopName, BusinessPhone, Category, Description, NationalId, Status) "
        "VALUES (%s,'Phase5 Shop','0900000000','Test','concurrency','PHASE5000001','pending')",
        (uid,),
    )
    rid = cur.lastrowid
    conn.close()
    yield uid, rid
    conn = _conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM SellerRequests WHERE UserId=%s", (uid,))
    cur.execute("DELETE FROM Stores WHERE UserId=%s", (uid,))
    cur.execute("DELETE FROM Accounts WHERE UserId=%s", (uid,))
    cur.execute("DELETE FROM Users WHERE UserId=%s", (uid,))
    conn.close()


def test_t63_two_real_db_connections_only_one_approve(live_seller_request):
    uid, rid = live_seller_request
    barrier = threading.Barrier(2)

    class BlockingDao(GianHangDao):
        def _khoa_don_cho_duyet(self, cursor, request_id, reviewed_by):
            barrier.wait(timeout=10)
            return super()._khoa_don_cho_duyet(cursor, request_id, reviewed_by)

    def approve(reviewer):
        return BlockingDao().duyet_yeu_cau(rid, reviewer)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(approve, [1, 2]))

    assert sorted(results) == [KET_QUA_DA_XU_LY, KET_QUA_OK]

    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT Status, ReviewedBy FROM SellerRequests WHERE RequestId=%s", (rid,))
    row = cur.fetchone()
    assert row[0] == "approved"
    cur.execute("SELECT COUNT(*) FROM Stores WHERE UserId=%s", (uid,))
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT Role_Id FROM Accounts WHERE UserId=%s", (uid,))
    assert cur.fetchone()[0] == 3
    conn.close()


def test_t63_reapproval_is_rejected(live_seller_request):
    uid, rid = live_seller_request
    dao = GianHangDao()
    assert dao.duyet_yeu_cau(rid, 1) == KET_QUA_OK
    assert dao.duyet_yeu_cau(rid, 2) == KET_QUA_DA_XU_LY


def test_t63_reject_after_approve_is_rejected(live_seller_request):
    _, rid = live_seller_request
    dao = GianHangDao()
    assert dao.duyet_yeu_cau(rid, 1) == KET_QUA_OK
    assert dao.tu_choi_yeu_cau(rid, 2, 'too late') == KET_QUA_DA_XU_LY


def test_t58_duplicate_pending_is_server_side(live_seller_request):
    uid, _ = live_seller_request
    from back_end.Model.YeuCau import YeuCau
    result = GianHangDao().gui_yeu_cau_ban_hang(
        YeuCau(UserId=uid, ShopName="Duplicate", BusinessPhone="0900000000",
               Category="Test", Description="dup", NationalId="x")
    )
    assert result == "da_co_pending"


def test_t58_concurrent_submit_same_user_only_one_pending(live_seller_request):
    uid, rid = live_seller_request
    conn = _conn(); cur = conn.cursor()
    cur.execute("DELETE FROM SellerRequests WHERE RequestId=%s", (rid,))
    conn.close()
    from back_end.Model.YeuCau import YeuCau

    barrier = threading.Barrier(2)
    def submit(label):
        barrier.wait(timeout=10)
        return GianHangDao().gui_yeu_cau_ban_hang(
            YeuCau(UserId=uid, ShopName=label, BusinessPhone="0900000000",
                   Category="Test", Description="concurrent", NationalId="x")
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, ["Concurrent A", "Concurrent B"]))
    assert sorted(results) == ["da_co_pending", "ok"]

    conn = _conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM SellerRequests WHERE UserId=%s AND Status='pending'", (uid,))
    assert cur.fetchone()[0] == 1
    conn.close()
