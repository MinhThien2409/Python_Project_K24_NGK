"""Unit test Phase 4 — static check JS/template (UX ho tro, backend chot).

Khong khoi dong server, khong cham DB.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

ROOT = Path(__file__).resolve().parent.parent.parent
JS = (ROOT / "static" / "js" / "main.js").read_text(encoding="utf-8")
HTML = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")


def _doan_js(ten_ham):
    m = re.search(rf"(?:async\s+)?function\s+{ten_ham}\b", JS)
    assert m, f"thieu ham {ten_ham}"
    return JS[m.start():m.start() + 4000]


# ── Price tab: gia goc / KM / checkbox ──
def test_bang_gia_co_gia_goc_km_checkbox():
    assert "Giá khuyến mãi" in HTML
    assert "Giá gốc" in HTML
    assert "giaGoc-" in JS and "giaKM-" in JS and "chkGiam-" in JS


def test_doi_gia_gui_discount_model_va_validate_km_nho_hon_goc():
    doan = _doan_js("sellerDoiGia")
    assert "gia_goc" in doan and "gia_khuyen_mai" in doan and "giam_gia" in doan
    assert "nhỏ hơn giá gốc" in doan
    # JS chi DOC discount_percent tu response de hien thi, khong GUI di.
    m = re.search(r"payload\s*=\s*(\{[^}]*\})", doan)
    assert m and "discount_percent" not in m.group(1)


# ── My Products: khoa Gia/Ton khi sua ──
def test_modal_khoa_gia_ton_kho_seller_sua():
    assert "khoaGiaTonKhoSellerMode" in JS
    assert "sellerPriceNote" in HTML
    # Chi giu mot implementation Seller-specific sau khi don duplicate.
    assert JS.count("function openEditSellerProduct(productId)") == 1
    assert JS.count("khoaGiaTonKhoSellerMode(true)") == 1


def test_seller_sua_khong_gui_gia_ton_kho():
    idx = JS.find("handleSaveProduct = async function")
    assert idx != -1
    doan = JS[idx:idx + 2500]
    # Nhanh edit (isEdit) khong gui price/old_price/quantity.
    m = re.search(r"if\s*\(!isEdit\)\s*\{([^}]*)\}", doan, re.S)
    assert m and "price" in m.group(1)


# ── Nhap bulk: autocomplete / dong / tao moi / khong gui NewStock ──
def test_phieu_nhap_nhieu_dong_co_autocomplete_va_tao_moi():
    assert "phieuNhapRows" in HTML and "submitPhieuNhap" in HTML
    for ham in ("themDongNhap", "xoaDongNhap", "goiYSanPham",
                "chonSanPhamNhap", "taoSanPhamVaNhap", "submitPhieuNhap"):
        assert ham in JS, f"thieu {ham}"
    assert "tim-kiem?q=" in JS
    assert "tao-va-nhap" in JS


def test_doi_ten_sau_chon_reset_selection():
    doan = _doan_js("goiYSanPham")
    assert "dataset.productId = ''" in doan


def test_submit_khong_gui_new_stock_hay_discount():
    idx = JS.find("async function submitPhieuNhap")
    doan = JS[idx:idx + 3500]
    thap = doan.lower()
    assert "new_stock" not in thap and "newstock" not in thap
    assert "discount_percent" not in thap
    assert "so nguyen" in doan.lower() or "nguyên" in doan
