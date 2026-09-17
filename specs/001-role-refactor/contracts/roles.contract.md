# Contract: Roles API (sau 001-role-refactor — XÓA TOÀN BỘ, clarify 2026-09-17)

## Endpoint GIỮ LẠI

Không có. Toàn bộ API quản lý vai trò bị xóa; 4 vai trò chuẩn chỉ tồn tại trong file nguồn `database.sql`/`back_up.sql`, không thể thay đổi lúc runtime.

## Endpoint BỊ XÓA → 404

| Method + URL | Lý do xóa |
|---|---|
| POST /api/cap-quyen-ngoai-le | Phân quyền ngoại lệ (FR-006) |
| POST /api/cap-quyen-nhom | Phân quyền ngoại lệ (FR-006) |
| GET /api/quyen-cua-user/<id> | Phân quyền ngoại lệ (FR-006) |
| GET /api/quyen-cua-nhom/<id> | Phân quyền ngoại lệ (FR-006) |
| POST /api/ap-dung-quyen-nhom-cho-user | Phân quyền ngoại lệ (FR-006) |
| GET /api/roles | Quản lý vai trò (FR-005 — xóa toàn bộ API roles) |
| POST /api/roles | Quản lý vai trò (FR-005) |
| PUT /api/roles/<id> | Quản lý vai trò (FR-005) |
| DELETE /api/roles/<id> | Quản lý vai trò (FR-005) |
| PUT /api/users/<ma_user>/role | Gán vai trò qua API (FR-005 — vai trò chỉ từ seed) |

## Code bị xóa

- XÓA FILE `back_end/BUS/PhanQuyenBus.py`, `back_end/DAO/PhanQuyenDao.py`, `back_end/Model/PhanQuyen.py`.
- XÓA `phan_quyen_bus` + toàn bộ routes trên khỏi `app.py`.
- `UserBus.cap_nhat_vai_tro` (gán vai trò qua API) bị xóa cùng route; `UserBus.cap_nhat_trang_thai` GIỮ LẠI + thêm guard chặn khóa Admin.
