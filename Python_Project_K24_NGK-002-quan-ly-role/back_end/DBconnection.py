import logging

import pymysql
from back_end.DBconfig import DB_CONFIG

logger = logging.getLogger(__name__)


class _Row:
    """Row hỗ trợ truy cập theo thuộc tính (row.UserId) và chỉ số (row[0])."""

    def __init__(self, columns, values):
        self._columns = list(columns)
        self._map = {str(c).lower(): i for i, c in enumerate(self._columns)}
        self._values = list(values)

    def __getattr__(self, name):
        idx = self._map.get(name.lower())
        if idx is None:
            raise AttributeError(f"Row không có cột '{name}'")
        return self._values[idx]

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self.__getattr__(key)

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)


class MySQLCursor:
    """Wrapper cursor để giữ tương thích với code DAO cũ (placeholder '?')."""

    def __init__(self, cursor):
        self._cursor = cursor
        self._columns = []

    def _convert_sql(self, sql):
        return sql.replace("?", "%s") if "?" in sql else sql

    def execute(self, sql, params=None):
        self._cursor.execute(self._convert_sql(sql), params or ())
        self._columns = [col[0] for col in (self._cursor.description or ())]
        return self

    def executemany(self, sql, seq_of_params):
        self._cursor.executemany(self._convert_sql(sql), seq_of_params or ())
        return self

    def _column_names(self):
        return [col[0] for col in (self._cursor.description or ())]

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return _Row(self._columns or self._column_names(), row)

    def fetchall(self):
        if not self._columns:
            self._columns = self._column_names()
        return [_Row(self._columns, row) for row in self._cursor.fetchall()]

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
        """Tạo kết nối MySQL dùng chung cho dự án."""
        try:
            conn = pymysql.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                database=DB_CONFIG["database"],
                charset=DB_CONFIG.get("charset", "utf8mb4"),
                autocommit=False,
            )
            return MySQLConnection(conn)
        except Exception as e:
            logger.exception("Lỗi kết nối Database MySQL: %s", e)
            return None