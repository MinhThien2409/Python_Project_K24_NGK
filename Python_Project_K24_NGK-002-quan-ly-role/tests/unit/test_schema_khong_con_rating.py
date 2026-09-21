"""Unit test US3 schema — 006 T019 (test-first Đỏ-Xanh).

Không cần DB: đọc file SQL dạng text.
Kỳ vọng SAU implement: schema/seed không còn Rating.
Trước implement: FAIL vì còn cột Rating.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))


def _doc(duong_dan):
    return (REPO / duong_dan).read_text(encoding="utf-8")


def test_schema_khong_con_cot_rating():
    src = _doc("Database/schema_mysql.sql")
    assert "Rating" not in src


def test_seed_khong_con_rating():
    src = _doc("Database/seed_demo_mysql.sql")
    assert "Rating" not in src


def test_migration_drop_rating_ton_tai():
    mig = REPO / "Database/sql/006_remove_rating.sql"
    assert mig.exists(), "thiếu migration Database/sql/006_remove_rating.sql"
    src = mig.read_text(encoding="utf-8")
    assert "DROP COLUMN Rating" in src
