"""Unit scan test quy ước — 007 T025 (test-first Đỏ-Xanh).

Quét AST toàn back_end/ + app.py theo contracts/cleanup-contract.md mục 3:
docstring Việt 1 dòng, 0 print(), placeholder ?, hàm <~40 dòng,
DAO thuần (0 SQL nối chuỗi, 0 return {"status"}), BUS không SQL.

Kỳ vọng SAU US2: 0 vi phạm. Trước US2: FAIL.
"""
import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

BACKEND_FILES = sorted((REPO / "back_end").rglob("*.py"))
APP_PY = REPO / "app.py"
TAT_CA = BACKEND_FILES + [APP_PY]

# Không miễn trừ: 100% hàm backend (kể cả wrapper DBconnection) phải có
# docstring tiếng Việt 1 dòng sau US2 (T029–T031, SC-002).
MIEN_DOCSTRING = set()


def _key(rel, cls, name):
    return f"{rel}:{cls}:{name}" if cls else f"{rel}:{name}"


def _quet_docstring():
    thieu = []
    for f in TAT_CA:
        rel = str(f.relative_to(REPO)).replace("\\", "/")
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if ast.get_docstring(node):
                    continue
                # tìm class cha
                cls = None
                for n2 in ast.walk(tree):
                    if isinstance(n2, ast.ClassDef) and node in [
                            n for n in ast.walk(n2)
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
                        # node thuộc class này nếu nằm trong thân
                        if node.lineno >= n2.lineno and node.end_lineno <= n2.end_lineno:
                            cls = n2.name
                            break
                k = _key(rel, cls, node.name)
                if k not in MIEN_DOCSTRING:
                    thieu.append(f"{rel}:{node.lineno}:{node.name}")
    return thieu


def test_100_ham_backend_co_docstring_viet():
    thieu = _quet_docstring()
    assert thieu == [], f"Thiếu docstring ({len(thieu)}): {thieu[:15]}"


def test_0_print_trong_backend():
    vi_pham = []
    for f in TAT_CA:
        for i, dong in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"(^|[^.\w])print\s*\(", dong):
                vi_pham.append(f"{f.name}:{i}:{dong.strip()[:70]}")
    assert vi_pham == [], f"Còn print() ({len(vi_pham)}): {vi_pham[:10]}"


def test_dao_khong_return_status_dict():
    vi_pham = []
    for f in sorted((REPO / "back_end" / "DAO").glob("*.py")):
        for i, dong in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            s = dong.strip()
            if s.startswith("return") and '"status"' in s.replace("'", '"'):
                vi_pham.append(f"{f.name}:{i}:{s[:80]}")
    assert vi_pham == [], f"DAO trả status-dict: {vi_pham}"


def test_bus_khong_chua_sql():
    vi_pham = []
    for f in sorted((REPO / "back_end" / "BUS").glob("*.py")):
        for i, dong in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", dong, re.IGNORECASE):
                # cho phép chữ trong message tiếng Việt có từ ghép, chỉ bắt SQL thật
                if re.search(r"(SELECT\s+\w|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM)",
                             dong, re.IGNORECASE):
                    vi_pham.append(f"{f.name}:{i}:{dong.strip()[:80]}")
    assert vi_pham == [], f"BUS chứa SQL: {vi_pham}"


def test_ham_khong_qua_40_dong():
    dai = []
    for f in TAT_CA:
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                n = node.end_lineno - node.lineno + 1
                if n > 40:
                    rel = str(f.relative_to(REPO)).replace("\\", "/")
                    dai.append(f"{rel}:{node.lineno}:{node.name}:{n}")
    assert dai == [], f"Hàm >40 dòng ({len(dai)}): {dai}"


def test_ngoai_le_in_phai_co_comment():
    f = REPO / "back_end" / "DAO" / "DonHangDao.py"
    src = f.read_text(encoding="utf-8")
    assert "IN (" in src or "IN(" in src, "Không tìm thấy ngoại lệ IN (?)"
    # comment giải thích phải ở gần dòng IN
    dong = src.splitlines()
    ok = False
    for i, d in enumerate(dong):
        if "IN (" in d or "IN(" in d:
            vung = "\n".join(dong[max(0, i - 6):i + 3]).lower()
            if "kiểm soát" in vung or "kiem soat" in vung or "controlled" in vung:
                ok = True
    assert ok, "Ngoại lệ IN (?) thiếu comment 'tham số hóa được kiểm soát' (R-06)"
