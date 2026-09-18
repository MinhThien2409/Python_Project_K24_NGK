"""Unit test US1 — 007 T012 (test-first Đỏ-Xanh).

Quét tham chiếu chết backend + file rac ở nhánh chính.
KHÔNG cần DB: đọc file nguồn dạng text.

Kỳ vọng SAU US1: 0 file rac, 0 hàm chết sót, giữ lại
ChucNang/NhomQuyen/ReviewedBy (nghiệp vụ duyệt-seller, R-01/R-02).
Trước US1: test file rac FAIL (file còn tồn tại).
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

BACKEND_DIRS = [REPO / "back_end" / "BUS", REPO / "back_end" / "DAO",
                REPO / "back_end" / "Model"]
APP_PY = REPO / "app.py"
MAIN_JS = REPO / "static" / "js" / "main.js"
INDEX_HTML = REPO / "templates" / "index.html"


def _toan_repo_text():
    """Toàn bộ text nguồn để tìm tham chiếu (py + js + html)."""
    parts = [APP_PY.read_text(encoding="utf-8")]
    for d in BACKEND_DIRS:
        for f in sorted(d.glob("*.py")):
            parts.append(f.read_text(encoding="utf-8"))
    parts.append(MAIN_JS.read_text(encoding="utf-8"))
    parts.append(INDEX_HTML.read_text(encoding="utf-8"))
    return "\n".join(parts)


# ── T012a: file rac không còn ở nhánh chính (FR-003) ──
def test_khong_con_git_tutorial_txt():
    assert not (REPO / "Git_Tutorial.txt").exists(), \
        "Git_Tutorial.txt phải bị xóa/khỏi nhánh chính (R-07)"


def test_khong_con_pptx_ban_nhap():
    rac = list(REPO.glob("*.pptx"))
    assert rac == [], f"Còn file .pptx ở nhánh chính: {rac} (R-07)"


def test_khong_con_brd_trd_report_plan():
    assert not (REPO / "BRD_TRD_REPORT_PLAN.md").exists(), \
        "BRD_TRD_REPORT_PLAN.md phải bị xóa/lưu trữ (R-07)"


def test_khong_con_sql_bak_nhi_phan():
    assert not (REPO / "Database" / "sql.bak").exists(), \
        "Database/sql.bak (dump nhị phân) phải bị xóa/lưu trữ (T008)"


# ── T012b: ChucNang/NhomQuyen CHẾT thật → phải xóa (T017, R-02) ──
# Kết luận đối chiếu 2026-09-18: 0 tham chiếu trong backend/app.py/
# static/templates/Database/tests (hệ phân quyền cũ đã bỏ ở spec 002,
# vai trò nay dùng Role_Id trực tiếp). ReviewedBy (duyệt-seller) GIỮ.
def test_chuc_nang_nhom_quyen_chet_da_xoa():
    assert not (REPO / "back_end" / "Model" / "ChucNang.py").exists(), \
        "ChucNang.py chết (0 tham chiếu) phải bị xóa (T017)"
    assert not (REPO / "back_end" / "Model" / "NhomQuyen.py").exists(), \
        "NhomQuyen.py chết (0 tham chiếu) phải bị xóa (T017)"
    text = _toan_repo_text()
    assert "ChucNang" not in text, "Còn sót tham chiếu ChucNang"
    assert "NhomQuyen" not in text, "Còn sót tham chiếu NhomQuyen"


# ── T012c: giữ lại nghiệp vụ duyệt-seller, không xóa nhầm (R-01/R-02) ──
def test_reviewed_by_la_duyet_seller_duoc_giu():
    text = _toan_repo_text()
    assert "ReviewedBy" in text, "ReviewedBy (duyệt-seller) phải được GIỮ (R-01)"
    yeucau = (REPO / "back_end" / "Model" / "YeuCau.py").read_text(encoding="utf-8")
    assert "ReviewedBy" in yeucau or "reviewed" in yeucau.lower()
PATTERN_RATING = re.compile(r"danh.?gia|danhgia|rating", re.IGNORECASE)


def test_backend_khong_con_rating_that():
    ngoai_le = ("preview", "reviewedby", "reviewed_by", "reviewed_by,",
                "renderrecentorderspreview", "recentorderspreview")
    vi_pham = []
    for d in BACKEND_DIRS:
        for f in sorted(d.glob("*.py")):
            for i, dong in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if PATTERN_RATING.search(dong):
                    nho = dong.lower()
                    if any(k in nho for k in ngoai_le):
                        continue
                    vi_pham.append(f"{f.name}:{i}:{dong.strip()[:80]}")
    assert vi_pham == [], f"Còn sót rating thật trong backend: {vi_pham}"
