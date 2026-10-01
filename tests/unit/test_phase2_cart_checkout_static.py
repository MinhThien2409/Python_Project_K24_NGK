# -*- coding: utf-8 -*-
"""Phase 2 static — checkbox giỏ + chặn checkout trống + nhóm theo shop (text)."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))


def _doc(duong_dan):
    return (REPO / duong_dan).read_text(encoding="utf-8")


def test_js_co_checkbox_theo_product_id_va_select_all():
    src = _doc("static/js/main.js")
    for ham in ["selectedCartIds", "getSelectedCartItems",
                "toggleCartItemSelection", "toggleSelectAllCart",
                "dongBoLuaChonGioHang", "capNhatNutThanhToan"]:
        assert ham in src, f"thiếu {ham} trong main.js"
    assert "Chọn tất cả" in src


def test_js_chan_checkout_khi_chua_chon():
    src = _doc("static/js/main.js")
    assert "Vui lòng chọn ít nhất một sản phẩm để thanh toán!" in src
    # chặn ở cả mở modal lẫn submit đặt hàng
    assert src.count("Vui lòng chọn ít nhất một sản phẩm để thanh toán!") >= 2


def test_js_tong_tien_va_ship_theo_mon_da_chon_nhom_theo_shop():
    src = _doc("static/js/main.js")
    assert "nhomTheoShop" in src
    assert "getSoShopTrongGio" in src
    assert "chỉ tính trên món được chọn" in src or \
        "ĐƯỢC CHỌN" in src


def test_js_chan_phuong_thuc_khong_ho_tro():
    src = _doc("static/js/main.js")
    assert "CAC_PHUONG_THUC_HO_TRO" in src
    assert "Phương thức thanh toán này hiện chưa được hỗ trợ!" in src


def test_checkout_hien_canh_bao_phuong_thuc_unsupported():
    html = _doc("templates/index.html")
    assert "paymentUnsupportedNote" in html
    assert "paymentUnsupportedNote" in _doc("static/js/main.js")
