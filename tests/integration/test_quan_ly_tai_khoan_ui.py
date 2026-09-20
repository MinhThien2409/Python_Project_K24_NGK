from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ui_quan_tri_khong_co_luong_them_quan_ly():
    html = (ROOT / "templates/index.html").read_text(encoding="utf-8")
    js = (ROOT / "static/js/main.js").read_text(encoding="utf-8")

    assert "openModalTaoQuanLy" not in html
    assert "+ Thêm tài khoản quản lý" not in html
    assert "id=\"quanLyModal\"" not in html
    assert "function openModalTaoQuanLy" not in js
    assert "fetch('http://localhost:5000/api/quan-ly'" not in js
