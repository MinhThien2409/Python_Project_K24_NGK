# -*- coding: utf-8 -*-
"""Kiểm chứng User Story 3: loại bỏ toàn bộ phân quyền ngoại lệ,
quản lý roles và gán vai trò qua API.

- T015: 10 endpoint cũ phải trả 404 (Flask test_client).
- T016: 0 tham chiếu đến Permissions/Modules/PhanQuyen/cap-quyen...
       trong app.py và back_end/.
"""

from pathlib import Path

import pytest

from app import app

REPO_ROOT = Path(__file__).resolve().parents[2]

# Các endpoint phải bị xóa và trả 404 (SC-002)
ENDPOINTS_BI_XOA = [
    ("POST", "/api/cap-quyen-ngoai-le"),
    ("POST", "/api/cap-quyen-nhom"),
    ("GET", "/api/quyen-cua-user/1"),
    ("GET", "/api/quyen-cua-nhom/1"),
    ("POST", "/api/ap-dung-quyen-nhom-cho-user"),
    ("GET", "/api/roles"),
    ("POST", "/api/roles"),
    ("PUT", "/api/roles/1"),
    ("DELETE", "/api/roles/1"),
    ("PUT", "/api/users/1/role"),
]

TU_KHOA_CAM = [
    "cap-quyen-ngoai-le",
    "cap-quyen-nhom",
    "quyen-cua-user",
    "quyen-cua-nhom",
    "ap-dung-quyen",
    "Permissions",
    "Modules",
    "PhanQuyen",
    "/api/roles",
    "cap_nhat_vai_tro",
]


@pytest.fixture(scope="module")
def client():
    app.config.update(TESTING=True)
    return app.test_client()


# ── T015: 10 endpoint cũ trả 404 ──────────────────────────────────────────────
@pytest.mark.parametrize("phuong_thuc,url", ENDPOINTS_BI_XOA, ids=[
    f"{m}-{u}" for m, u in ENDPOINTS_BI_XOA
])
def test_endpoint_cu_tra_404(client, phuong_thuc, url):
    if phuong_thuc == "GET":
        resp = client.get(url)
    elif phuong_thuc == "POST":
        resp = client.post(url, json={})
    elif phuong_thuc == "PUT":
        resp = client.put(url, json={})
    else:
        resp = client.delete(url)
    assert resp.status_code == 404, (
        f"{phuong_thuc} {url} phải trả 404, thực tế {resp.status_code}"
    )


@pytest.fixture(scope="module")
def noi_dung_nguon_cam():
    cac_file = []
    for duong in [REPO_ROOT / "app.py", REPO_ROOT / "back_end"]:
        if duong.is_dir():
            for p in sorted(duong.rglob("*.py")):
                cac_file.append(p)
        else:
            cac_file.append(duong)
    return cac_file


# ── T016: grep backend = 0 tham chiếu ─────────────────────────────────────────
@pytest.mark.parametrize("tu_khoa", TU_KHOA_CAM)
def test_grep_khong_con_tham_chieu_cam(tu_khoa, noi_dung_nguon_cam):
    vi_pham = []
    for p in noi_dung_nguon_cam:
        try:
            noi_dung = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            noi_dung = p.read_text(encoding="utf-8", errors="ignore")
        for i, dong in enumerate(noi_dung.splitlines(), 1):
            if tu_khoa in dong:
                vi_pham.append(f"{p}:{i}: {dong.strip()}")
    assert not vi_pham, (
        f"Vẫn còn {len(vi_pham)} tham chiếu {tu_khoa!r}:\n" + "\n".join(vi_pham[:10])
    )