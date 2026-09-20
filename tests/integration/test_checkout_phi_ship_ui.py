from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_checkout_tinh_phi_ship_theo_store_id_duy_nhat():
    js = (ROOT / "static/js/main.js").read_text(encoding="utf-8")

    assert "new Set" in js
    assert "StoreId" in js
    assert "soShop" in js
    assert "currentShippingFee = phiCoBan * soShop" in js
    assert "checkoutShipText" in js
