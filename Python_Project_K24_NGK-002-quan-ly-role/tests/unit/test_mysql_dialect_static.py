# -*- coding: utf-8 -*-
"""Static dialect test — hết cú pháp SQL Server trong back_end (016 US4, T020).

Quét mọi file `.py` trong back_end/ (trừ __pycache__): KHÔNG còn:
- `OUTPUT INSERTED`/`OUTPUT ` (mệnh đề SQL Server không có trong MySQL)
- `GETDATE(` / `SYSDATETIME()` (hàm ngày SQL Server)
- `[dbo]` / `dbo.` (schema SQL Server)
- literal `N'...'` (prefix N cho chuỗi Unicode — SQL Server)

KHÔNG cần DB.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

BACK_END = REPO / "back_end"

MAU_LOI = ("OUTPUT ", "GETDATE(", "SYSDATETIME(", "[dbo]", "dbo.",
           "N'", "N\"")


def _cac_file_py():
    ds = []
    for path in BACK_END.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        ds.append(path)
    assert ds, "Không tìm thấy file .py trong back_end/"
    return sorted(ds)


def _khop_cu_phap(noi_dung):
    """Trả list (vị trí, mẫu) khớp lệnh SQL Server — phân biệt hoa thường cho
    từ khóa (SQL) nhưng chấp nhận `N'` Unicode ở Python."""

    # Chỉ kiểm tra dòng có chứa SQL (INSERT/SELECT/UPDATE/DELETE/VALUES/OUTPUT)
    cac_loi = []
    for i, dong in enumerate(noi_dung.splitlines(), start=1):
        if "INSERT" not in dong and "SELECT" not in dong and \
           "UPDATE" not in dong and "DELETE" not in dong and \
           "OUTPUT" not in dong and "GETDATE" not in dong and \
           "SYSDATETIME" not in dong and "dbo" not in dong:
            continue
        in_str = False
        tam = ""
        for ky in dong:
            if ky in ("'", '"'):
                in_str = not in_str
                tam += ky
                continue
            tam += ky
        # bỏ comment trong dòng (-- hoặc #) để tránh false positive
        tam = tam.split("--")[0].split("#")[0]
        for mau in MAU_LOI:
            if mau in tam:
                cac_loi.append((i, mau))
    return cac_loi


def test_khong_con_output_inserted():
    """Mệnh đề OUTPUT INSERTED (SQL Server) vắng mặt trong mọi câu SQL."""
    for path in _cac_file_py():
        noi_dung = path.read_text(encoding="utf-8")
        for i, dong in enumerate(noi_dung.splitlines(), start=1):
            # Chỉ câu SQL/câu chèn — comment tài liệu (kèm '#') được phép
            co_sql = (
                "INSERT" in dong or "OUTPUT" in dong
                or "VALUES" in dong or "SELECT" in dong
            )
            if co_sql and "OUTPUT INSERTED" in dong and "#" not in dong.split("OUTPUT")[0]:
                assert False, f"{path}:{i} còn OUTPUT INSERTED trong SQL: {dong.strip()}"


def test_khong_con_getdate():
    for path in _cac_file_py():
        noi_dung = path.read_text(encoding="utf-8")
        assert "GETDATE(" not in noi_dung, f"{path} còn GETDATE( (hàm SQL Server)"


def test_khong_con_dbo_schema():
    for path in _cac_file_py():
        noi_dung = path.read_text(encoding="utf-8")
        assert "[dbo]" not in noi_dung and "dbo." not in noi_dung, \
            f"{path} còn schema dbo (SQL Server)"


def test_khong_con_loi_dialect_trong_sql():
    """Mọi mẫu lỗi dialect SQL Server đều vắng mặt trong câu SQL."""
    for path in _cac_file_py():
        noi_dung = path.read_text(encoding="utf-8")
        cac_loi = _khop_cu_phap(noi_dung)
        assert not cac_loi, f"{path} còn lỗi dialect ở dòng {cac_loi}"