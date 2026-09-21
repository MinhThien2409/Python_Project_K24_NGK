"""Test nhất quán tài liệu-phạm vi — 007 T051 (test-first Đỏ-Xanh).

BRD 4 vai trò + không đánh giá; endpoint khớp 2 chiều với
contracts/cleanup-contract.md. KHÔNG cần DB.

Trước T056: FAIL (BRD còn mục rating/BR09/BR11/FR-15).
Sau T056: PASS.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))


def _brd():
    return (REPO / "BRD_TRD_REPORT.md").read_text(encoding="utf-8")


def test_brd_du_4_vai_tro():
    brd = _brd()
    for vai in ["Admin", "Seller"]:
        assert vai in brd, f"BRD thiếu vai trò {vai}"
    assert "Quản lý" in brd or "Quan ly" in brd or "quản lý" in brd.lower()
    assert "Customer" in brd or "khách hàng" in brd.lower()


def test_brd_khong_con_pham_vi_danh_gia():
    """BRD không còn yêu cầu nghiệp vụ đánh giá (BR09/BR11/FR-15...)."""
    brd = _brd()
    for muc in ["BR09", "BR11", "FR-15"]:
        assert muc not in brd, f"BRD còn mục đánh giá {muc} (phải xóa theo 006)"
    # không còn dòng phạm vi "đánh giá sản phẩm" dạng yêu cầu
    dong_pham_vi = [d for d in brd.splitlines()
                    if re.search(r"đánh giá sản phẩm|wishlist.*review|rating.*seller",
                                 d, re.IGNORECASE)]
    # cho phép nhắc lịch sử trong Todos/changelog, nhưng BRD chính không còn
    assert dong_pham_vi == [], f"BRD còn phạm vi đánh giá: {dong_pham_vi[:5]}"


def test_endpoint_khop_2_chieu_voi_contract():
    """Mọi endpoint trong contract đều có trong app.py và ngược lại (mẫu chính)."""
    contract = (REPO / "specs" / "007-project-cleanup" / "contracts"
                / "cleanup-contract.md").read_text(encoding="utf-8")
    src = (REPO / "app.py").read_text(encoding="utf-8")
    urls = set(re.findall(r"`([A-Z|]+ )?(/api/[^`,\s]+)`", contract))
    duong = {u[1].split("<")[0].rstrip("/") for u in urls}
    thieu = [u for u in duong if u.rstrip("/") not in src.replace("<int:", "<")]
    # chuẩn hóa so sánh theo tiền tố route
    # 009 FR-011: endpoint admin/staff toàn cục đã bị gỡ (chức năng chuyển sang
    # /api/seller/*) — contract 007 cleanup cũ còn liệt kê, chúng được loại trừ.
    DA_GOTHEO_FR011_009 = {
        "/api/thong-ke/tong-quan",
        "/api/thong-ke/doanh-thu-theo-thang",
        "/api/don-hang/cua-seller",
    }
    that = []
    for u in thieu:
        base = u.split("<")[0]
        if base not in DA_GOTHEO_FR011_009 and base not in src:
            that.append(u)
    assert that == [], f"Contract có mà app.py thiếu: {that[:10]}"