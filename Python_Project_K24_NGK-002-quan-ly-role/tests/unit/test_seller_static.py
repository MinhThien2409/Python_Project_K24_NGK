"""Static test seller schema + contract — US polish (T055/T056/T058).

Khong can DB: doc file nguon dang text, assert placeholder + hop dong.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))


def _doc(duong_dan):
    return (REPO / duong_dan).read_text(encoding="utf-8")


def _bo_dong_log(src):
    """Loai dong logging truoc khi soi `%s` SQL (007: DAO dung logging)."""
    return "\n".join(
        d for d in src.splitlines()
        if "log" not in d.lower()
    )


# ── T055: ImageUrl + ThamNien co mat ──
def test_model_co_imageurl_va_thamnien():
    san_pham = _doc("back_end/Model/SanPham.py")
    gian_hang = _doc("back_end/Model/GianHang.py")
    assert "ImageUrl" in san_pham
    assert "ThamNien" in gian_hang


def test_migration_co_guard_va_check():
    mig = _doc("Database/sql/004_seller_imageurl_thamnien.sql")
    assert "IF COL_LENGTH" in mig
    assert "ImageUrl" in mig
    assert "ThamNien" in mig
    assert "0" in mig and "100" in mig


# ── T055: SQL moi toan placeholder ? (khong noi chuoi, khong %s) ──
# 006-remove-reviews Decision 4 + Complexity Tracking G7: SanPhamDao chay MySQL
# that (DBconnection.py pymysql, ? → %s, lastrowid) nen dung LIMIT + lastrowid,
# KHONG dung TOP (?) / OUTPUT INSERTED (dialect SQL Server cu).
def test_dao_seller_khong_con_mysql_dialect():
    dao_sp = _bo_dong_log(_doc("back_end/DAO/SanPhamDao.py"))
    assert "%s" not in dao_sp
    assert "TOP (" not in dao_sp and "TOP(" not in dao_sp
    assert "OUTPUT INSERTED" not in dao_sp
    assert "LIMIT" in dao_sp
    assert "lastrowid" in dao_sp


def test_dao_seller_dung_placeholder():
    for f in ["back_end/DAO/SanPhamDao.py", "back_end/DAO/DonHangDao.py",
              "back_end/DAO/GianHangDao.py"]:
        src = _doc(f)
        # khong noi chuoi vao SQL: khong co f-string chua SELECT/UPDATE/INSERT
        for m in re.finditer(r'f""".*?(SELECT|UPDATE|INSERT).*?"""', src, re.S | re.I):
            raise AssertionError(f"{f} noi chuoi SQL: {m.group(0)[:80]}")
        for m in re.finditer(r"f'''.*?(SELECT|UPDATE|INSERT).*?'''", src, re.S | re.I):
            raise AssertionError(f"{f} noi chuoi SQL: {m.group(0)[:80]}")


def test_ownership_trong_where():
    dao_sp = _doc("back_end/DAO/SanPhamDao.py")
    assert "AND StoreId" in dao_sp
    dao_dh = _doc("back_end/DAO/DonHangDao.py")
    assert "p.StoreId" in dao_dh


# ── T055: khong route seller nao tin store_id client ──
def test_seller_route_khong_doc_store_id_client():
    app = _doc("app.py")
    seller_doan = app[app.find("10. SELLER"):]
    assert "d.get('store_id')" not in seller_doan
    assert 'd.get("store_id")' not in seller_doan


# ── T056: 8+ route seller tra status/message tieng Viet + data ──
def test_du_8_route_seller():
    app = _doc("app.py")
    routes = re.findall(r"@app\.route\('/api/seller/[^']*'", app)
    assert len(routes) >= 8, f"chi co {len(routes)} route seller"


def test_bus_seller_tra_hop_dong():
    for f in ["back_end/BUS/SanPhamBus.py", "back_end/BUS/DonHangBus.py",
              "back_end/BUS/GianHangBus.py"]:
        src = _doc(f)
        assert '"status"' in src and '"message"' in src


def test_gate_that_bai_403():
    app = _doc("app.py")
    seller_doan = app[app.find("10. SELLER"):]
    assert "403" in seller_doan


# ── T058: nhap_hang atomic + an SP giu snapshot ──
def test_nhap_hang_atomic_quantity_cong():
    dao = _doc("back_end/DAO/SanPhamDao.py")
    assert "Quantity = Quantity + ?" in dao
    assert "WHERE ProductId = ? AND StoreId = ?" in dao


def test_an_sp_giu_snapshot_don_cu():
    dao_sp = _doc("back_end/DAO/SanPhamDao.py")
    assert "IsActive" in dao_sp
    dao_dh = _doc("back_end/DAO/DonHangDao.py")
    # don cu doc tu OrderItems snapshot, khong join Products de loc an
    assert "OrderItems" in dao_dh
