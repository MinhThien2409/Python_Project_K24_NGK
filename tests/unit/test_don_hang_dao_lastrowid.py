# -*- coding: utf-8 -*-
"""Unit test DonHangDao._chen_order_lay_id dùng cursor.lastrowid (016 US4 T021).

- SQL INSERT KHÔNG còn mệnh đề `OUTPUT INSERTED.OrderId` (cú pháp SQL Server).
- Hàm trả `cursor.lastrowid` (PyMySQL) thay vì `fetchone()[0]`.
- KHÔNG gọi `fetchone()` trên cursor sau khi chèn đơn.
- Tao_don_hang cấp OrderId mới cho OrderItems từ lastrowid.

Dùng fake cursor/connection — KHÔNG chạm PobbyDB thật.
"""

from back_end.DAO.DonHangDao import DonHangDao
from back_end.Model.DonHang import DonHang
from back_end.Model.OrderItem import OrderItem


class FakeCursor:
    """Cursor ghi nhận SQL + lastrowid cấu hình; fetchone() đánh dấu lỗi."""

    def __init__(self, lastrowid=441, rowcount=1):
        self.lastrowid = lastrowid
        self.sql_log = []
        self.param_log = []
        self.rowcount = rowcount
        self.da_goi_fetchone = False
        self.da_goi_fetchall = False

    def execute(self, sql, params=None):
        self.sql_log.append(sql)
        self.param_log.append(params)
        return self.rowcount

    def fetchone(self):
        self.da_goi_fetchone = True
        return None

    def fetchall(self):
        self.da_goi_fetchall = True
        return []

    @property
    def description(self):
        return None

    def close(self):
        pass


class FakeConn:
    def __init__(self, cursor):
        self.cursor_ = cursor
        self.commit_count = 0
        self.rollback_count = 0
        self.closed = False

    def cursor(self):
        return self.cursor_

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.closed = True


def _don_hang(ma=1):
    don = DonHang(
        Status="Pending", ShippingFee=30000, UserId=ma, ReceiverName="Khách",
        ReceiverPhone="0900000000", ShippingAddress="Hà Nội",
        PaymentMethod="COD", SubTotal=200000, DiscountAmount=0,
        TotalAmount=230000, Note=None,
    )
    don.Items = [OrderItem(ProductId=10, ProductName="Hoa Hồng", Emoji="🌹",
                           Quantity=2, UnitPrice=100000, TotalPrice=200000)]
    return don


# ── T021 phần 1: _chen_order_lay_id trả lastrowid, không OUTPUT, không fetchone ──
def test_chen_order_lay_id_khong_output_inserted():
    dao = DonHangDao()
    cur = FakeCursor(lastrowid=441)
    don = _don_hang()

    ma = dao._chen_order_lay_id(cur, don)

    assert ma == 441
    # SQL không còn mệnh đề OUTPUT INSERTED.OrderId (SQL Server)
    assert "OUTPUT" not in cur.sql_log[0]
    # Vẫn dùng placeholder ? cho wrapper DBconnection
    assert "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)" in cur.sql_log[0]
    # Không gọi fetchone() để lấy id
    assert cur.da_goi_fetchone is False


def test_chen_order_lay_id_params_giu_nguyen():
    dao = DonHangDao()
    cur = FakeCursor(lastrowid=55)
    don = _don_hang()

    dao._chen_order_lay_id(cur, don)

    params = cur.param_log[0]
    assert params[0] == "Pending"           # Status
    assert params[2] == 1                   # UserId
    assert params[3] == "Khách"             # ReceiverName
    assert params[10] is None               # Note


# ── T021 phần 2: tao_don_hang dùng lastrowid cho FK OrderItems + commit ──
def test_tao_don_hang_dung_lastrowid_gan_cho_items(monkeypatch):
    from back_end.DBconnection import DBconnection

    cur = FakeCursor(lastrowid=888)
    fake_conn = FakeConn(cur)
    monkeypatch.setattr(DBconnection, "get_connection",
                        staticmethod(lambda: fake_conn))

    dao = DonHangDao()
    ket_qua = dao.tao_don_hang([_don_hang(ma=7)])

    assert ket_qua == [888]
    assert fake_conn.commit_count == 1
    # Không fetchone() trong luồng chèn đơn
    assert cur.da_goi_fetchone is False
    # Câu lệnh chèn OrderItems dùng OrderId = lastrowid
    sql_items = [s for s in cur.sql_log
                 if s.lstrip().startswith("INSERT INTO OrderItems")]
    assert len(sql_items) == 1
    # Lệnh trừ kho cũng chạy
    assert any("UPDATE Products" in s for s in cur.sql_log)


def test_tao_don_hang_rollback_khi_loi(monkeypatch):
    from back_end.DBconnection import DBconnection

    class LoiCursor(FakeCursor):
        def execute(self, sql, params=None):
            self.sql_log.append(sql)
            if sql.lstrip().startswith("INSERT INTO OrderItems"):
                raise RuntimeError("Lỗi cú pháp DB thật")
            return 1

    cur = LoiCursor(lastrowid=888)
    fake_conn = FakeConn(cur)
    monkeypatch.setattr(DBconnection, "get_connection",
                        staticmethod(lambda: fake_conn))

    dao = DonHangDao()
    ket_qua = dao.tao_don_hang([_don_hang(ma=7)])

    assert ket_qua is False
    assert fake_conn.rollback_count == 1
    assert fake_conn.commit_count == 0