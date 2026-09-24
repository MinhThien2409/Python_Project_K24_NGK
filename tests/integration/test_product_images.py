# -*- coding: utf-8 -*-
"""Test đối chiếu seed-đĩa + API image_url (spec 014) — viết TRƯỚC implementation.

Test bất biến (contract `contracts/product-images.md`):
- Seed `Database/seed_demo_mysql.sql` cột ImageUrl khớp 100% bảng mapping
  (9 dòng có giá trị, ProductId 8 = NULL) — FR-001/FR-002.
- Mọi ImageUrl khác NULL đều trỏ tới file THẬT trên đĩa trong
  `static/images/products/`, tên khớp CHÍNH XÁC (phân biệt hoa/thường) — FR-005.
- Giá trị là đường dẫn tương đối `images/products/<ten-file>`:
  không tiền tố `/static/`, không `/` đầu dòng, không URL tuyệt đối.
- Frontend giữ pattern fallback `p.image_url ? <img /static/...> : emoji`
  tại mọi vị trí render (FR-004, US3) — main.js hiện có 14 lần `p.image_url`
  trên 7 vị trí ternary/if (line ~404, 502, 1042, 1449, 1582, 3208, 3447).
- (Cần DB chạy) `GET /api/products` trả `image_url` khớp mapping (US2) —
  tự bỏ qua nếu PobbyDB không kết nối được.
"""
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

SEED = REPO / "Database" / "seed_demo_mysql.sql"
IMAGES = (REPO / "static" / "images" / "products")
JS = (REPO / "static" / "js" / "main.js").read_text(encoding="utf-8")

# Bảng mapping chuẩn (contracts/product-images.md + data-model.md mục 2)
MAPPING = {
    1: "images/products/iphone-15-pro-max.png",
    2: "images/products/samsung.jpg",
    3: "images/products/macbook.jpg",
    4: "images/products/hoodie-local-brand.png",
    5: "images/products/giay-nike-air-max.png",
    6: "images/products/tui_xach.png",
    7: "images/products/noi-chien-khong-dau.jpg",
    8: None,
    9: "images/products/sach-python.jpg",
    10: "images/products/dong-ho-casio.jpg",
}

COT_PRODUCTS = [
    "ProductId", "ProductName", "Quantity", "Price", "CategoryId", "StoreId",
    "Description", "OldPrice", "ImageUrl", "SoldCount", "Emoji", "IsActive",
]


def _doc_seed_products():
    """Đọc seed, trả dict {ProductId: ImageUrl} từ khối INSERT INTO Products."""
    text = SEED.read_text(encoding="utf-8")
    # Cắt khối từ dòng "INSERT INTO Products" đến hết câu lệnh (trước ';')
    header = text.index("INSERT INTO Products")
    end = text.index(";", header)
    block = text[header:end]
    # Các dòng VALUES mỗi sản phẩm bắt đầu bằng '(' và kết thúc bằng ')'
    rows = {}
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("("):
            continue
        fields = _tach_truong(line.strip("(").strip(")").rstrip(","))
        gia_tri = fields[COT_PRODUCTS.index("ImageUrl")].strip()
        if len(gia_tri) >= 2 and gia_tri[0] == gia_tri[-1] == "'":
            gia_tri = gia_tri[1:-1]  # bỏ cặp nháy đơn bao quanh
        rows[int(fields[COT_PRODUCTS.index("ProductId")])] = gia_tri
    return rows


def _tach_truong(dong):
    """Tách dòng VALUES thành các trường, tôn trọng chuỗi nháy đơn có dấu phẩy."""
    fields, cur, in_str = [], [], False
    for ch in dong:
        if ch == "'":
            in_str = not in_str
        if ch == "," and not in_str:
            fields.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        fields.append("".join(cur).strip())
    return fields


# ── FR-001/FR-002 + contract muc 1: seed khớp bảng mapping ───
def test_seed_products_khop_mapping():
    rows = _doc_seed_products()
    assert set(rows) == set(MAPPING), (
        f"Seed Products thiếu/thừa ProductId so với mapping: {set(rows) ^ set(MAPPING)}"
    )
    for pid, ky_vong in MAPPING.items():
        thuc_te = rows[pid]
        thuc_te = None if thuc_te.upper() == "NULL" else thuc_te
        assert thuc_te == ky_vong, (
            f"ProductId {pid}: ImageUrl thực tế={thuc_te!r}, kỳ vọng={ky_vong!r}"
        )


# ── FR-005 / US3: mọi ImageUrl ≠ NULL phải trỏ file thật trên đĩa ──
def test_moi_image_url_khong_null_co_file_tren_dia():
    rows = _doc_seed_products()
    for pid, url in rows.items():
        if url.upper() == "NULL":
            continue
        ten = Path(url).name
        assert (IMAGES / ten).is_file(), (
            f"ProductId {pid}: '{url}' → file '{ten}' KHÔNG tồn tại trong "
            f"static/images/products/ (tên phải khớp chính xác hoa/thường)."
        )


# ── Contract muc 2: đường dẫn tương đối, không tiền tố /static/ ──
def test_image_url_la_duong_dan_tuong_doi():
    rows = _doc_seed_products()
    for pid, url in rows.items():
        if url.upper() == "NULL":
            continue
        assert url.startswith("images/products/"), (
            f"ProductId {pid}: '{url}' phải bắt đầu bằng images/products/"
        )
        assert not url.startswith("/static/"), (
            f"ProductId {pid}: '{url}' KHÔNG được chứa tiền tố /static/"
        )
        assert not url.startswith("/"), f"ProductId {pid}: '{url}' không được bắt đầu bằng /"
        assert "://" not in url, f"ProductId {pid}: '{url}' không được là URL tuyệt đối"


# ── FR-004 / US3: mọi vị trí render giữ pattern fallback emoji ──
def _cac_vi_tri_render_p_image_url():
    """Trả về các vị trí ternary/if của p.image_url dùng để render ảnh."""
    marks = set()
    for mau in ["p.image_url ? ", "if (p.image_url)"]:
        marks.update(m.start() for m in re.finditer(re.escape(mau), JS))
    # Ternary viết xuống dòng: `p.image_url` rồi xuống dòng `? `
    for m in re.finditer(r"p\.image_url[\s\n]*\?\s*[`<(']", JS):
        marks.add(m.start())
    return sorted(marks)


def test_frontend_giu_pattern_fallback_emoji_cho_anh():
    vi_tri = _cac_vi_tri_render_p_image_url()
    assert len(vi_tri) >= 6, (
        f"main.js chỉ còn {len(vi_tri)} vị trí render ảnh (kỳ vọng nhiều pane "
        f"cửa hàng/người bán/quản lý/chi tiết)."
    )
    for pos in vi_tri:
        block = JS[pos:pos + 900]
        # (a) img phải gắn đúng tiền tố /static/
        assert ("/static/${p.image_url}" in block
                or "'/static/' + p.image_url" in block), (
            f"Vị trí {pos}: img không dùng tiền tố /static/ + image_url"
        )
        # (b) nhánh fallback emoji phải còn
        assert "p.emoji || '📦'" in block, (
            f"Vị trí {pos}: thiếu fallback emoji (p.emoji || '📦')"
        )


# ── US2 (cần DB chạy): GET /api/products trả image_url khớp mapping ──
def test_api_products_tra_image_url_khop_mapping(monkeypatch):
    from back_end.DBconnection import DBconnection
    from back_end.BUS.SanPhamBus import SanPhamBus
    from back_end.DAO.SanPhamDao import SanPhamDao
    import app as app_module
    conn = DBconnection.get_connection()
    if conn is None:
        pytest.skip("PobbyDB không kết nối được — bỏ qua kiểm tra API (có thể chạy lại khi DB lên).")
    cur = conn.cursor()
    try:
        bus = SanPhamBus()
        bus.dao = SanPhamDao()
        monkeypatch.setattr(app_module, "san_pham_bus", bus)
        with app_module.app.test_client() as client:
            resp = client.get("/api/products")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        tra_ve = {p["id"]: p["image_url"] for p in data}
        hop_le = {pid: url for pid, url in tra_ve.items() if url}
        assert len(hop_le) == 9, (
            f"API trả {len(hop_le)} sản phẩm có image_url (kỳ vọng 9): {tra_ve}"
        )
        for pid, url in hop_le.items():
            assert url == MAPPING[pid], (
                f"API ProductId {pid}: image_url={url!r}, kỳ vọng={MAPPING[pid]!r}"
            )
        assert tra_ve[8] is None or tra_ve[8] == "", (
            f"ProductId 8 phải có image_url null/trống, thực tế={tra_ve.get(8)!r}"
        )
    finally:
        cur.close()
        conn.close()