# -*- coding: utf-8 -*-
"""Phase 3 static — hủy đơn + doanh thu Completed + UI lịch sử/thông báo (text)."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))


def _doc(duong_dan):
    return (REPO / duong_dan).read_text(encoding="utf-8")


# ── Backend: doanh thu Completed theo items ──────────────────────────────

def test_dao_doanh_thu_seller_completed_theo_items():
    """Phase 3 §4: tổng seller = Completed, SUM(qty*unitprice), theo store."""
    src = _doc("back_end/DAO/DonHangDao.py")
    assert "oi.Quantity * oi.UnitPrice" in src
    assert "o.Status = 'Completed'" in src
    assert "p.StoreId = %s" in src
    vung = src[src.index("_thong_ke_chinh_cua_store"):]
    vung = vung[:vung.index("def ", 10)]
    assert "<> 'Cancelled'" not in vung


def test_dao_co_kho_thong_bao():
    """Phase 3 §5: DAO có bảng + CRUD thông báo, placeholder %s."""
    src = _doc("back_end/DAO/DonHangDao.py")
    for ham in ["_dam_bao_bang_thong_bao", "tao_thong_bao",
                "lay_thong_bao_cua_user", "danh_dau_thong_bao_da_doc"]:
        assert ham in src, f"thiếu {ham} trong DonHangDao"
    assert "CREATE TABLE IF NOT EXISTS Notifications" in src


def test_bus_huy_don_va_cam_seller_huy():
    """Phase 3 §2+§3: BUS có hủy customer + chặn seller hủy sau Pending."""
    src = _doc("back_end/BUS/DonHangBus.py")
    for ham in ["huy_don_hang_cua_customer", "lay_thong_bao_cua_user",
                "danh_dau_thong_bao_da_doc"]:
        assert ham in src, f"thiếu {ham} trong DonHangBus"
    assert "Seller chỉ được hủy đơn đang ở trạng thái Chờ duyệt!" in src


def test_app_co_route_huy_va_thong_bao():
    """Phase 3: route /huy + /thong-bao tồn tại, route cắt vẫn vắng mặt."""
    src = _doc("app.py")
    assert "/api/don-hang/<int:order_id>/huy" in src
    assert "/api/thong-bao/cua-toi" in src
    assert "/api/thong-bao/danh-dau-da-doc" in src
    assert "api_cap_nhat_trang_thai" not in src


# ── Frontend ─────────────────────────────────────────────────────────────

def test_js_huy_don_qua_modal_va_endpoint_huy():
    """Phase 3 §2+§5: modal xác nhận + endpoint /huy + refresh thông báo."""
    src = _doc("static/js/main.js")
    for ham in ["moXacNhanHuyDon", "xacNhanHuyDon", "huyDonHangCuaToi",
                "taiThongBao", "moThongBao", "markAllRead",
                "danhDauThongBaoDaDoc"]:
        assert ham in src, f"thiếu {ham} trong main.js"
    assert "/api/don-hang/${orderId}/huy" in src
    assert "confirmCancelModal" in src
    assert "/api/thong-bao/cua-toi" in src
    assert "/api/thong-bao/danh-dau-da-doc" in src


def test_js_huy_don_khong_goi_trang_thai_cu():
    """Phase 3 §2: huyDonHangCuaToi không còn gọi endpoint đã cắt."""
    src = _doc("static/js/main.js")
    vung = src[src.index("async function huyDonHangCuaToi"):]
    vung = vung[:vung.index("// Phase 3: chuông thông báo")]
    assert "/trang-thai" not in vung


def test_js_seller_chi_huy_duoc_pending():
    """Phase 3 §3: bảng seller chỉ hiện nút Hủy ở Pending."""
    src = _doc("static/js/main.js")
    assert "if (o.Status === 'Pending' || o.Status === 'Confirmed'" not in src
    assert "seller chỉ được hủy đơn đang Chờ duyệt" in src


def test_js_lich_su_don_day_du_thong_tin():
    """Phase 3 §1: card lịch sử có đơn giá/SL/tạm tính/nhãn thanh toán."""
    src = _doc("static/js/main.js")
    assert "PAYMENT_LABEL" in src
    assert "i.UnitPrice" in src
    assert "o.SubTotal" in src
    assert "Giữ lại đơn" not in src  # nút này nằm ở template


def test_html_co_modal_xac_nhan_va_chuong():
    """Phase 3 §1+§5: modal xác nhận + nút chuông + badge + filter gọn."""
    html = _doc("templates/index.html")
    for token in ["confirmCancelModal", "confirmCancelContent",
                  "xacNhanHuyDon", "hdrNotifBtn", "notifBadge",
                  "markAllRead", "notifContent", "flex-wrap:wrap; gap:10px"]:
        assert token in html, f"thiếu {token} trong index.html"
