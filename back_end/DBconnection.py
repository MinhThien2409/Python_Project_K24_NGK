# config/db_config.py
#
# Tầng kết nối MySQL dùng chung cho toàn dự án.
# - Dùng driver PyMySQL (đã đổi từ pyodbc/SQL Server sang MySQL).
# - Cursor trả về wrapper cho phép:
#     + Truy cập cột theo thuộc tính / chỉ số như pyodbc (row.TenCot, row[0]).
#     + Placeholder `?` tự động chuyển thành `%s` của PyMySQL.
#     + `cursor.lastrowid` hoạt động như SQL Server `OUTPUT INSERTED.Id`.
import pymysql
from pymysql.cursors import DictCursor

from back_end.DBconfig import DB_CONFIG


class _Row:
    """Dòng dữ liệu hỗ trợ truy cập theo tên cột & theo chỉ số (như pyodbc)."""

    def __init__(self, columns, values):
        self._columns = list(columns)
        # Bản đồ tên cột → chỉ số, đối chiếu KHÔNG phân biệt hoa/thường
        self._luoi = {f"{c}".lower(): i for i, c in enumerate(self._columns)}
        self._values = list(values)

    def __getattr__(self, name):
        try:
            return self._values[self._luoi[name.lower()]]
        except KeyError:
            raise AttributeError(f"Row không có cột '{name}'")

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self.__getattr__(key)

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def keys(self):
        return self._columns

    def as_dict(self):
        return {c: v for c, v in zip(self._columns, self._values)}


class MySQLCursor:
    """Wrapper quanh PyMySQL cursor để giữ API quen thuộc của pyodbc."""

    def __init__(self, cursor):
        self._cursor = cursor
        self._columns = []

    def _dan_hoi(self, sql):
        """Đổi placeholder `?` (pyodbc) → `%s` (PyMySQL)."""
        if "?" in sql:
            return sql.replace("?", "%s")
        return sql

    def execute(self, sql, params=None):
        self._cursor.execute(self._dan_hoi(sql), params or ())
        self._columns = [col[0] for col in self._cursor.description or ()]
        return self

    def executemany(self, sql, seq_of_params):
        self._cursor.executemany(self._dan_hoi(sql), seq_of_params or ())
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return _Row(self._columns or self._ten_cot(), row)

    def _ten_cot(self):
        return [col[0] for col in self._cursor.description or ()]

    def fetchall(self):
        if not self._columns:
            self._columns = self._ten_cot()
        return [_Row(self._columns, row) for row in self._cursor.fetchall()]

    # ── Thuộc tính mô phỏng pyodbc ──────────────────────────────────────────
    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        try:
            self._cursor.close()
        except Exception:
            pass


class MySQLConnection:
    """Wrapper quanh kết nối PyMySQL — giữ API như pyodbc (cursor/commit/...)."""

    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return MySQLCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass


class DBconnection:
    @staticmethod
    def get_connection():
        try:
            conn = pymysql.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                database=DB_CONFIG["database"],
                charset=DB_CONFIG["charset"],
                autocommit=False,
            )
            return MySQLConnection(conn)
        except Exception as e:
            print("Lỗi kết nối Database MySQL:", e)
            return None