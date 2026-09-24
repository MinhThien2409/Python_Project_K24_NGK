from back_end.DAO.GioHangDao import GioHangDao


class FakeCursor:
    def __init__(self):
        self.description = [("CartId",), ("ProductId",), ("Quantity",), ("UnitPrice",), ("ProductName",), ("Emoji",), ("ImageUrl",), ("StoreId",)]
        self.sql = ""

    def execute(self, sql, params):
        self.sql = sql
        self.params = params

    def fetchall(self):
        return [(1, 9, 2, 10000, "Bánh", "🍪", None, 3)]

    def close(self):
        pass


class FakeConn:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self):
        return self.cursor_obj

    def close(self):
        pass


def test_lay_chi_tiet_gio_hang_tra_store_id(monkeypatch):
    conn = FakeConn()
    monkeypatch.setattr(
        "back_end.DAO.GioHangDao.DBconnection.get_connection",
        lambda self: conn,
    )

    rows = GioHangDao().lay_chi_tiet_gio_hang(1)

    assert rows[0]["StoreId"] == 3
    assert "p.StoreId AS StoreId" in conn.cursor_obj.sql
