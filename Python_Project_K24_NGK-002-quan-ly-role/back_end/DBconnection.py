# config/db_config.py
#
# Tầng kết nối MySQL dùng chung cho toàn dự án.
# - Dùng driver PyMySQL (đã đổi từ pyodbc/SQL Server sang MySQL).
# - Cursor trả về wrapper cho phép:
#     + Truy cập cột theo thuộc tính / chỉ số như pyodbc (row.TenCot, row[0]).
#     + Placeholder `?` tự động chuyển thành `%s` của PyMySQL.
#     + `cursor.lastrowid` hoạt động như SQL Server `OUTPUT INSERTED.Id`.
import logging

import pymysql
from pymysql.cursors import DictCursor

from back_end.DBconfig import DB_CONFIG

logger = logging.getLogger(__name__)


class _Row:
    """Dòng dữ liệu hỗ trợ truy cập theo tên cột & theo chỉ số (như pyodbc)."""

    def __init__(self, columns, values):
        """Khởi tạo dòng dữ liệu với danh sách cột và giá trị."""
        self._columns = list(columns)
        # Bản đồ tên cột → chỉ số, đối chiếu KHÔNG phân biệt hoa/thường
        self._luoi = {f"{c}".lower(): i for i, c in enumerate(self._columns)}
        self._values = list(values)

    def __getattr__(self, name):
        """Truy cập giá trị cột theo tên thuộc tính không phân biệt hoa thường."""
        try:
            return self._values[self._luoi[name.lower()]]
        except KeyError:
            raise AttributeError(f"Row không có cột '{name}'")

    def __getitem__(self, key):
        """Lấy giá trị cột theo chỉ số hoặc tên cột."""
        if isinstance(key, int):
            return self._values[key]
        return self.__getattr__(key)

    def __iter__(self):
        """Duyệt qua các giá trị của dòng dữ liệu."""
        return iter(self._values)

    def __len__(self):
        """Trả về số cột của dòng dữ liệu."""
        return len(self._values)

    def keys(self):
        """Trả về danh sách tên cột của dòng dữ liệu."""
        return self._columns

    def as_dict(self):
        """Chuyển dòng dữ liệu thành từ điển tên cột và giá trị."""
        return {c: v for c, v in zip(self._columns, self._values)}


class MySQLCursor:
    """Wrapper quanh PyMySQL cursor để giữ API quen thuộc của pyodbc."""

    def __init__(self, cursor):
        """Khởi tạo cursor bao quanh cursor PyMySQL gốc."""
        self._cursor = cursor
        self._columns = []

    def _dan_hoi(self, sql):
        """Đổi placeholder `?` (pyodbc) → `%s` (PyMySQL)."""
        if "?" in sql:
            return sql.replace("?", "%s")
        return sql

    def execute(self, sql, params=None):
        """Thực thi câu lệnh SQL và lưu tên cột trả về."""
        self._cursor.execute(self._dan_hoi(sql), params or ())
        self._columns = [col[0] for col in self._cursor.description or ()]
        return self

    def executemany(self, sql, seq_of_params):
        """Thực thi cùng câu lệnh SQL cho nhiều bộ tham số."""
        self._cursor.executemany(self._dan_hoi(sql), seq_of_params or ())
        return self

    def fetchone(self):
        """Lấy một dòng kết quả dưới dạng đối tượng _Row."""
        row = self._cursor.fetchone()
        if row is None:
            return None
        return _Row(self._columns or self._ten_cot(), row)

    def _ten_cot(self):
        """Lấy danh sách tên cột từ mô tả cursor hiện tại."""
        return [col[0] for col in self._cursor.description or ()]

    def fetchall(self):
        """Lấy toàn bộ dòng kết quả dưới dạng danh sách _Row."""
        if not self._columns:
            self._columns = self._ten_cot()
        return [_Row(self._columns, row) for row in self._cursor.fetchall()]

    # ── Thuộc tính mô phỏng pyodbc ──────────────────────────────────────────
    @property
    def rowcount(self):
        """Trả về số dòng bị ảnh hưởng bởi câu lệnh vừa chạy."""
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        """Trả về mã tự tăng của dòng vừa chèn."""
        return self._cursor.lastrowid

    @property
    def description(self):
        """Trả về mô tả cột của truy vấn hiện tại."""
        return self._cursor.description

    def close(self):
        """Đóng cursor MySQL một cách an toàn."""
        try:
            self._cursor.close()
        except Exception:
            pass


class MySQLConnection:
    """Wrapper quanh kết nối PyMySQL — giữ API như pyodbc (cursor/commit/...)."""

    def __init__(self, conn):
        """Khởi tạo kết nối bao quanh đối tượng PyMySQL gốc."""
        self._conn = conn

    def cursor(self):
        """Tạo cursor MySQL bọc trong MySQLCursor."""
        return MySQLCursor(self._conn.cursor())

    def commit(self):
        """Xác nhận giao dịch hiện tại vào cơ sở dữ liệu."""
        self._conn.commit()

    def rollback(self):
        """Hủy bỏ giao dịch hiện tại và hoàn tác thay đổi."""
        self._conn.rollback()

    def close(self):
        """Đóng kết nối cơ sở dữ liệu một cách an toàn."""
        try:
            self._conn.close()
        except Exception:
            pass


class DBconnection:
    @staticmethod
    def get_connection():
        """Tạo và trả về kết nối MySQL dùng chung cho dự án."""
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
            logger.exception("Lỗi kết nối Database MySQL: %s", e)
            return None