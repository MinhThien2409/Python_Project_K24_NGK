# Research: Tái cấu trúc vai trò — 4 vai trò duy nhất (001-role-refactor)

**Ngày**: 2026-09-17 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## R1. Schema thực tế vs mô tả trong spec

**Phát hiện** (đọc trực tiếp `Database/database.sql`, `Database/back_up.sql`, code DAO):

- Bảng `Users` trong `database.sql`: cột vai trò là `Role_Id INT NULL` (không FK, cho phép NULL) — code `UserDao`/`PhanQuyenDao` truy vấn bằng `Role_id` (SQL Server không phân biệt hoa/thường nên chạy được, nhưng cần thống nhất tài liệu là `Role_Id`).
- Bảng `Users` trong `database.sql` KHÔNG có cột `trang_thai`, nhưng code `UserDao.dang_nhap`/`lay_danh_sach_user` đã `COALESCE(trang_thai,'active')`; `back_up.sql` ĐÃ có `trang_thai` (`... Role_Id, trang_thai ... VALUES (1, ..., 20, N'active')`). → DB thật đã trôi khỏi `database.sql`.
- Bảng `Roles(RoleId IDENTITY, RoleName)`: 20 dòng (1–20). 4 vai trò chuẩn đã tồn tại đúng ID: Seller=13, Customer=14, Manager=19, Admin=20.
- Bảng `Stores(UserId, IsActive)`: 19+ gian hàng, chủ sở hữu là các user chẵn 2,4,6,8,10,12,14,16,18,20 (mỗi user 1–2 gian hàng) — KHÁC với spec ghi "user 2,3,4 sở hữu gian hàng". Dữ liệu mẫu `Users`: 24 user (ID 1–20, 23–26), user1 Role 20, user2–4 Role 13, còn lại Role 14.
- Bảng `Permissions(UserId, ModuleId, CanView/CanAdd/CanEdit/CanDelete, IsCustom)` + `Modules(ModuleId, ModuleName, ModuleCode)` tồn tại; `PhanQuyenDao.xoa_role` còn tham chiếu bảng `RolePermissions` KHÔNG tồn tại (lỗi tiềm ẩn — càng lý do để xóa).

**Decision**: Lấy `database.sql` + code hiện hành làm sự thật; hiệu chỉnh quy tắc gán Seller thành "mọi user có `Stores.UserId`" (thay vì chỉ 2,3,4); script chuẩn hóa phải sửa được cả lệch `trang_thai` (thêm cột nếu thiếu).

**Rationale**: Script chạy trên DB thật, không chạy trên mô tả spec. Quy tắc theo `Stores` bao trùm được cả trường hợp spec cũ và dữ liệu thật.

**Alternatives considered**: Giữ nguyên quy tắc "chỉ user 2,3,4 → Seller" — REJECT vì sẽ giáng 7 seller thật (user 6–20 có gian hàng) xuống Customer, phá vỡ SC-001 và dữ liệu kiểm thử Seller.

## R2. Tên vai trò Quản lý (clarify 2026-09-17)

**Phát hiện**: `Roles` ID 19 = `N'Manager'` (tiếng Anh); spec yêu cầu 4 tên "Admin, Quản lý, Seller, Customer".

**Decision (sau clarify)**: Xóa bỏ dữ liệu cũ, tạo SQL dữ liệu mẫu mới — tên chuẩn của 4 vai trò được chốt TRONG seed mới (không giữ ID 13/14/19/20 cố định, không ánh xạ tương thích ngược). Tên hiển thị tiếng Việt xử lý ở tầng giao diện.

**Rationale**: Rebuild seed loại bỏ gánh nặng tương thích ngược với 20 vai trò cũ; tên chuẩn duy nhất sống trong seed mới + `database.sql`/`back_up.sql` đồng bộ.

**Alternatives considered**: Giữ `Manager` + ánh xạ hiển thị — REJECT sau clarify vì không còn dữ liệu cũ cần tương thích.

## R3. Thứ tự DROP `Permissions`/`Modules` và xóa code (clarify 2026-09-17: xóa toàn bộ API roles)

**Phát hiện**: `PhanQuyenDao` (9 hàm) + `PhanQuyenBus` (10 hàm) + 5 routes `/api/cap-quyen-*`/`/api/quyen-cua-*` + 4 routes `/api/roles` CUD + 1 route `PUT /api/users/<id>/role` + UI ma trận quyền (`tblPermissionsBody`, `tblGroupPermissionsBody`, `menu-permissions`) + `Model/PhanQuyen.py` đều phục vụ cơ chế ngoại lệ/quản lý roles. FK: `Permissions.UserId → Users`, `Permissions.ModuleId → Roles` (đặt tên gây hiểu lầm, thực chất trỏ Roles), `Modules.ModuleId` tự tham chiếu.

**Decision**: Thứ tự an toàn: (1) xóa code tham chiếu — XÓA FILE `PhanQuyenBus.py`/`PhanQuyenDao.py`/`Model/PhanQuyen.py`, xóa 5 routes ngoại lệ + TOÀN BỘ routes roles (`GET/POST/PUT/DELETE /api/roles`, `PUT /api/users/<id>/role`) khỏi `app.py`, dọn UI — → (2) chạy script DROP FK → DROP TABLE `Permissions`, `Modules` → (3) đồng bộ `database.sql`/`back_up.sql`. Script DROP phải `IF EXISTS` + xóa FK trước để idempotent. Không giữ lại API roles nào (FR-005 sau clarify): 4 vai trò chỉ tồn tại trong seed, không đổi lúc runtime.

**Rationale**: Xóa code trước tránh lỗi runtime "bảng không tồn tại" giữa chừng; xóa toàn bộ API roles loại bỏ mọi đường tạo vai trò thứ 5.

**Alternatives considered**: DROP bảng trước, xóa code sau — REJECT vì mọi request quyền trong lúc chuyển tiếp sẽ 500 thay vì 404 có kiểm soát. Giữ `GET /api/roles` + `PUT /api/users/<id>/role` — REJECT sau clarify (user chọn xóa toàn bộ API roles).

## R4. Hành vi đăng nhập với `Role_Id` NULL / không hợp lệ (clarify 2026-09-17: rebuild seed)

**Phát hiện**: `Users.Role_Id NULL` cho phép; `UserDao.dang_nhap` hiện SELECT `Role_id` thô, không JOIN `Roles`, không xử lý NULL; `UserBus.dang_nhap` trả `ma_nhom_quyen` số, không có tên vai trò → UI không phân nhánh được (vi phạm FR-008).

**Decision (sau clarify)**: Seed mới KHÔNG chứa `Role_Id` NULL/lạ (script rà soát + xóa toàn bộ bản ghi vi phạm — FR-009). `UserDao.dang_nhap` JOIN `Roles` lấy `RoleName` trong cùng 1 query; nếu vẫn gặp `Role_Id` NULL/lạ lúc runtime (DB bị sửa tay) → từ chối đăng nhập với message rõ ràng (không crash). `UserBus.dang_nhap` bổ sung `ten_vai_tro` + `ten_vai_tro_hien_thi` vào `data`. Đăng ký mới (`dang_ky_khach_hang`) gán Customer theo ID của seed mới.

**Rationale**: Sau rebuild seed, NULL/lạ là lỗi dữ liệu nghiêm trọng (không phải trường hợp thường) nên từ chối rõ ràng thay vì fail-safe âm thầm; JOIN một lần rẻ hơn 2 query.

**Alternatives considered**: Fail-safe về Customer — REJECT sau clarify vì che giấu dữ liệu bẩn mà seed mới đã cam kết xóa sạch.

## R5. Không ai được khóa Admin + xóa toàn bộ API roles (FR-005/FR-006 sau clarify)

**Phát hiện**: `UserBus.cap_nhat_trang_thai` hiện cho phép khóa bất kỳ user nào (kể cả Admin); `PhanQuyenBus.them_role/sua_role/xoa_role` không có guard; `xoa_role` còn DELETE bảng ma `RolePermissions` (sẽ lỗi).

**Decision (sau clarify)**: XÓA FILE `PhanQuyenBus.py`/`PhanQuyenDao.py` (không giữ guard nào — không còn API roles để guard). Chặn khóa Admin ở `UserBus.cap_nhat_trang_thai`: nếu user thuộc vai trò Admin → `{"status": False, "message": "Không ai có quyền khóa tài khoản Admin!"}`; script seed bổ sung guard cấu trúc DB nếu cần (ví dụ CHECK/constraint ngăn `trang_thai='banned'` cho Admin). Không còn `cap_nhat_vai_tro` qua API (route bị xóa); gán vai trò chỉ qua seed.

**Rationale**: Chặn ở BUS để trả message tiếng Việt đúng hợp đồng API (G2) và dễ unit test không cần DB; guard DB là lớp phòng thủ thứ hai.

**Alternatives considered**: Giữ API roles + guard `VAI_TRO_CHUAN` — REJECT sau clarify (user chọn xóa toàn bộ API roles).

## R6. Chiến lược test không cần SQL Server thật (Nguyên tắc IV)

**Phát hiện**: Chưa có thư mục `tests/`; CI/máy chấm có thể không có SQL Server; `DBconnection.get_connection` hardcode `sa/123`.

**Decision**: Unit test mock `UserDao`/`PhanQuyenDao` bằng `unittest.mock.MagicMock` (test validate BUS thuần); integration test dùng Flask `app.test_client()` + mock DAO trả dữ liệu mẫu (test hợp đồng JSON + 404 routes đã xóa); script SQL test bằng phân tích tĩnh (assert `IF EXISTS`, `IN (13,14,19,20)`, idempotent) + chạy thử trên SQLite chuyển đổi cú pháp tối thiểu nếu cần. Thêm `pytest` vào `requirements.txt`.

**Rationale**: Đúng hiến chương "test KHÔNG chạm PobbyDB thật"; mock giữ test nhanh, xanh trên mọi máy.

**Alternatives considered**: Dựng SQL Server test riêng — REJECT vì nặng, không khả thi trên máy chấm, vi phạm YAGNI (G7).

## R7. Idempotent script rebuild seed (clarify 2026-09-17)

**Decision**: `Database/sql/001_chuan_hoa_vai_tro.sql` rebuild seed trong 1 transaction, mỗi bước `IF EXISTS`/điều kiện nên chạy N lần an toàn: B1 — DROP FK → DROP TABLE `Permissions`, `Modules` (IF EXISTS); B2 — `DELETE Roles WHERE RoleName NOT IN (4 tên chuẩn)` rồi `INSERT` thiếu 4 vai trò chuẩn (theo tên chốt trong seed mới); B3 — xóa user có `Role_Id` NULL/lạ (sau khi đã xóa roles thừa) + xóa dữ liệu mẫu cũ không phù hợp; B4 — tạo mới seed `Users`/`Stores` mẫu (user1 → Admin; chủ `Stores` → Seller; còn lại → Customer); B5 — thêm `trang_thai` nếu thiếu + guard chống khóa Admin (nếu cần); B6 — `SELECT` kiểm chứng cuối (đếm Roles=4, Users mồ côi=0).

**Rationale**: Một file duy nhất; xóa trước — tạo mới sau đảm bảo seed sạch; `NOT IN (4 tên chuẩn)` bắt mọi vai trò thừa kể cả dữ liệu tương lai.

## R1b. Quy tắc Seller trong seed mới (clarify 2026-09-17)

**Decision**: Seed mới tự chứa cả `Users` và `Stores` nhất quán (chủ `Stores` ↔ user Seller), không suy luận từ dữ liệu cũ. Quy tắc tài liệu: user1 → Admin; user sở hữu gian hàng → Seller; còn lại → Customer.
