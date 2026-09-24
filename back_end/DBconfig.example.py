# DBconfig.example.py
# Sao chép file này thành back_end/DBconfig.py rồi điền mật khẩu MySQL.
# back_end/DBconfig.py đã được thêm vào .gitignore — không commit lên git.

import os

DB_CONFIG = {
    "host": os.environ.get("POBBY_DB_HOST", "localhost"),
    "port": int(os.environ.get("POBBY_DB_PORT", 3306)),
    "user": os.environ.get("POBBY_DB_USER", "root"),
    "password": os.environ.get("POBBY_DB_PASSWORD", "12345"),
    "database": os.environ.get("POBBY_DB_NAME", "pobbydb"),
    "charset": "utf8mb4",
}