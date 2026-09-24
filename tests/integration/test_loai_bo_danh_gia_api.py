"""Integration test US2 endpoint — 006 T008/T013 (test-first Đỏ-Xanh).

Fake DAO in-memory — KHÔNG chạm PobbyDB thật.
Kỳ vọng SAU implement: GET không còn khóa rating; POST/PUT kèm rating vẫn 200 và không lưu.
Trước implement: FAIL vì response còn khóa rating.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from back_end.Model.User import User
from tests.conftest import FakeUserDaoBus


class FakeSanPhamKhongRating:
    """Fake SanPham DAO không còn rating (kỳ vọng SAU implement)."""

    def __init__(self):
        self.san_pham = {
            1: {"id": 1, "name": "Tai nghe Bluetooth", "description": "ANC",
                "price": 890000.0, "old_price": 1200000.0, "quantity": 40,
                "sold": 10, "emoji": "📦", "image_url": None,
                "category_id": 14, "category_name": "Âm thanh",
                "store_id": 6, "shop": "Shop Test", "is_active": True},
        }
        self.next_id = 2

    def lay_tat_ca(self):
        return [dict(v) for v in self.san_pham.values() if v.get("is_active")]

    def lay_theo_id(self, product_id):
        sp = self.san_pham.get(int(product_id))
        return dict(sp) if sp else None

    def lay_theo_store(self, store_id):
        return [dict(v) for v in self.san_pham.values()
                if v.get("store_id") == int(store_id)]

    def tim_kiem(self, tu_khoa, category_id=None):
        kw = (tu_khoa or "").strip().lower()
        ket_qua = []
        for sp in self.san_pham.values():
            if not sp.get("is_active"):
                continue
            if kw and kw not in (sp.get("name") or "").lower():
                continue
            ket_qua.append(dict(sp))
        return ket_qua

    def lay_ban_chay(self, top=10):
        ds = sorted(self.san_pham.values(), key=lambda x: x.get("sold", 0), reverse=True)
        return [dict(v) for v in ds[:int(top or 10)]]

    def kiem_tra_category_ton_tai(self, category_id):
        return True

    def them(self, sp):
        # SAU implement Model không còn Rating → assert ở đây
        assert not hasattr(sp, "Rating"), "Model SanPham vẫn còn field Rating"
        nid = self.next_id
        self.next_id += 1
        self.san_pham[nid] = {
            "id": nid, "name": sp.ProductName, "description": sp.Description,
            "price": float(sp.Price), "old_price": float(sp.OldPrice) if sp.OldPrice else None,
            "quantity": int(sp.Quantity or 0), "sold": 0,
            "emoji": sp.Emoji, "image_url": sp.ImageUrl,
            "category_id": int(sp.CategoryId), "category_name": "",
            "store_id": int(sp.StoreId), "shop": "Shop Test", "is_active": True,
        }
        return nid

    def sua(self, sp):
        assert not hasattr(sp, "Rating"), "Model SanPham vẫn còn field Rating"
        cur = self.san_pham.get(int(sp.ProductId))
        if not cur:
            return False
        cur.update({"name": sp.ProductName, "price": float(sp.Price)})
        return True


def _client_moi(customer_client):
    users = {"khach": User(ma_user=5, ma_nhom_quyen=4, ten_user="Khách",
                           sdt="0903", dia_chi="HN", cmnd="3",
                           tendangnhap="khach", mat_khau="123456")}
    thong_tin = {5: {"UserId": 5, "FullName": "Khách", "Role_Id": 4, "trang_thai": "active"}}
    user_dao = FakeUserDaoBus(users=users, thong_tin=thong_tin, mat_khau={"khach": "123456"})
    sp_store = FakeSanPhamKhongRating()
    return customer_client(user_dao=user_dao, san_pham_store=sp_store), sp_store


# ── T013: GET list/detail không còn khóa rating ──
def test_get_list_khong_con_khoa_rating(customer_client):
    client, _ = _client_moi(customer_client)
    r = client.get("/api/products")
    assert r.status_code == 200
    assert r.json["status"] is True
    assert len(r.json["data"]) > 0
    for item in r.json["data"]:
        assert "rating" not in item, f"item còn khóa rating: {item}"
        assert "Rating" not in item


def test_get_detail_khong_con_khoa_rating(customer_client):
    client, _ = _client_moi(customer_client)
    r = client.get("/api/products/1")
    assert r.status_code == 200
    assert r.json["status"] is True
    assert "rating" not in r.json["data"]
    assert "Rating" not in r.json["data"]


# ── T013: POST/PUT kèm rating vẫn 200 và không lưu ──
def test_post_kem_rating_van_200_va_khong_luu(customer_client):
    client, store = _client_moi(customer_client)
    payload = {"name": "Loa Mini", "description": "Bass mạnh", "price": 500000,
               "old_price": 700000, "quantity": 20, "emoji": "📦",
               "image_url": None, "category_id": 14, "store_id": 6,
               "rating": 4.9}
    r = client.post("/api/products", json=payload)
    assert r.status_code in (404, 405)  # 009 FR-011: route write admin đã gỡ


def test_put_kem_rating_van_200_va_khong_luu(customer_client):
    client, store = _client_moi(customer_client)
    payload = {"name": "Tai nghe Pro", "description": "ANC", "price": 990000,
               "old_price": 1200000, "quantity": 30, "emoji": "📦",
               "image_url": None, "category_id": 14, "store_id": 6,
               "rating": "xxx"}
    r = client.put("/api/products/1", json=payload)
    assert r.status_code in (404, 405)  # 009 FR-011: route write admin đã gỡ


# ── T008: sort/filter không còn tùy chọn rating ──
def test_tim_kiem_api_khong_con_sort_rating(customer_client):
    client, _ = _client_moi(customer_client)
    r = client.get("/api/products?q=tai nghe")
    assert r.status_code == 200
    assert r.json["status"] is True
    for item in r.json["data"]:
        assert "rating" not in item
