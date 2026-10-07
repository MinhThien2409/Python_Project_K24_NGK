from pathlib import Path

BUS = Path('back_end/BUS/DonHangBus.py').read_text(encoding='utf-8')

def test_t139_code_order_is_explicit():
    start = BUS.index('def cap_nhat_trang_thai_cua_seller')
    block = BUS[start:start + 1800]
    assert block.index('don_thuoc_store(order_id, store_id)') < block.index('lay_trang_thai(order_id)')


def test_t139_unit_behavior_ownership_is_first():
    from back_end.BUS.DonHangBus import DonHangBus

    class Dao:
        def __init__(self):
            self.calls = []
        def don_thuoc_store(self, order_id, store_id):
            self.calls.append('ownership')
            return False
        def lay_trang_thai(self, order_id):
            self.calls.append('status')
            return 'Completed'

    bus = DonHangBus.__new__(DonHangBus)
    bus.dao = Dao()
    result = bus.cap_nhat_trang_thai_cua_seller(10, 20, 30, 'Cancelled')
    assert result['status'] is False
    assert 'không thuộc' in result['message']
    assert bus.dao.calls == ['ownership']
