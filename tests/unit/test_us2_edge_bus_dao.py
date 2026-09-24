"""Unit test ca biên BUS validate + DAO trả lỗi — 007 T028.

Rỗng/None/số âm/trùng khóa/quyền hạn: DAO lỗi trả {}/[],
BUS gán status/message Việt, không lộ stack trace.

KHÔNG chạm PobbyDB thật.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from back_end.BUS.DanhMucBus import DanhMucBus
from back_end.BUS.DonHangBus import DonHangBus
from back_end.DAO.DonHangDao import DonHangDao


class StubDanhMucRong:
    def lay_tat_ca(self):
        return []

    def kiem_tra_ten_ton_tai(self, ten, tru_id=None):
        return False

    def dem_san_pham(self, category_id):
        return None

    def them(self, category):
        return True

    def sua(self, category):
        return True

    def xoa(self, category_id):
        return True


def test_danh_muc_ten_rong_bi_chan_tieng_viet():
    bus = DanhMucBus()
    bus.dao = StubDanhMucRong()
    for xau in ("", "   ", None):
        r = bus.them_category(xau)
        assert r["status"] is False
        assert isinstance(r["message"], str) and len(r["message"]) > 0
        assert "Traceback" not in r.get("message", "")


def test_danh_muc_ten_101_ky_tu_bi_chan():
    bus = DanhMucBus()
    bus.dao = StubDanhMucRong()
    r = bus.them_category("a" * 101)
    assert r["status"] is False


def test_don_hang_thieu_thong_tin_nguoi_nhan():
    from back_end.Model.DonHang import DonHang
    bus = DonHangBus()
    bus.dao = StubDanhMucRong()  # không dùng tới vì validate chặn trước
    dh = DonHang(UserId=1, ReceiverName="", ReceiverPhone="09",
                 ShippingAddress="", PaymentMethod="COD",
                 SubTotal=100, TotalAmount=100)
    dh.Items = []
    r = bus.tao_don_hang(dh)
    assert r["status"] is False
    assert "Traceback" not in r["message"]


def test_dao_loi_ket_noi_tra_pure(monkeypatch):
    """Mất kết nối: DAO thống kê/doanh thu trả {}/[] thuần."""
    import back_end.DAO.DonHangDao as mod
    monkeypatch.setattr(mod.DBconnection, "get_connection",
                        staticmethod(lambda *a, **k: None))
    dao = DonHangDao()
    assert dao.lay_thong_ke_tong_quan() == {}
    assert dao.lay_doanh_thu_theo_thang(2026) == []
    assert dao.lay_don_hang_cua_user(1) == []


def test_dao_exception_tra_pure_khong_status(monkeypatch):
    """Cursor lỗi: DAO trả {}/[] thuần, KHÔNG bọc status."""
    import back_end.DAO.DonHangDao as mod

    class CurHong:
        def execute(self, *a, **k):
            raise RuntimeError("boom")

        def close(self):
            pass

    class ConnHong:
        def cursor(self):
            return CurHong()

        def close(self):
            pass

    monkeypatch.setattr(mod.DBconnection, "get_connection",
                        staticmethod(lambda *a, **k: ConnHong()))
    dao = DonHangDao()
    assert dao.lay_thong_ke_tong_quan() == {}
    assert dao.lay_doanh_thu_theo_thang(2026) == []
