# Tasks: Tái cấu trúc vai trò — 4 vai trò duy nhất (001-role-refactor)

**Input**: Tài liệu thiết kế từ `/specs/001-role-refactor/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md)

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: BẮT BUỘC — Hiến chương Pobby Nguyên tắc IV. Test viết TRƯỚC implementation (test-first), chạy bằng `pytest`, đặt trong `tests/unit/` và `tests/integration/`. KHÔNG chạm PobbyDB thật (mock DAO + Flask test_client + phân tích tĩnh nội dung `database.sql`/`back_up.sql`).

**Hướng triển khai (chỉ đạo 2026-09-17)**: Chuẩn hóa vai trò bằng cách **SỬA TRỰC TIẾP file nguồn** — không tạo hàm riêng để chuẩn hóa, không tạo SQL script riêng để chuẩn hóa. Kết quả chuẩn hóa nằm ngay trong `Database/database.sql` và `Database/back_up.sql` (4 vai trò ID 1–4, user được remap, bỏ `Permissions`/`Modules`). Script cũ `Database/sql/001_chuan_hoa_vai_tro.sql` và 2 test cũ phải ĐƯỢC XÓA/thay thế.

## Format: `[ID] [P?] [Story] Mô tả`

- **[P]**: Có thể chạy song song (khác file, không phụ thuộc)
- **[Story]**: User story task thuộc về (US1, US2, US3, US4)
- Luôn kèm đường dẫn file chính xác trong mô tả

## Path Conventions (Pobby)

- Backend: `back_end/Model/`, `back_end/DAO/`, `back_end/BUS/`, controller `app.py`
- Frontend: `templates/index.html`, `static/js/main.js`
- Tests: `tests/unit/`, `tests/integration/`, fixture dùng chung `tests/conftest.py`
- DB (sửa TRỰC TIẾP, không có script chuẩn hóa): `Database/database.sql`, `Database/back_up.sql` (đều UTF-16LE có BOM)

---

## Phase 1: Setup (Hạ tầng dùng chung)

**Mục đích**: Khởi tạo cấu trúc dự án và hạ tầng cơ bản

- [X] T001 Tạo cấu trúc thư mục tests (tests/unit và tests/integration) kèm file __init__.py
- [X] T002 Thêm pytest vào requirements.txt
- [X] T003 [P] Di dời file Database/sql (5MB binary backup) → Database/sql.bak để giải phóng tên thư mục Database/sql

---

## Phase 2: Foundational (Điều kiện tiên quyết chặn)

**Mục đích**: Hạ tầng kiểm thử cốt lõi — BẮT BUỘC hoàn thành trước mọi user story

**⚠️ CRITICAL**: Không user story nào được bắt đầu khi phase này chưa xong

- [X] T004 Tạo mock helper cho UserDao + Flask test_client trong tests/conftest.py (KHÔNG chạm PobbyDB thật)
- [X] T005 [P] Định nghĩa fixture 4 vai trò chuẩn (Admin, Quản lý, Seller, Customer) + MockUserDao (map id 1–4) trong tests/conftest.py
- [X] T006 Chạy pytest -v kiểm tra suite thu thập xanh với tests/conftest.py ở root repo

**Checkpoint**: Foundation sẵn sàng — các user story có thể triển khai song song

---

## Phase 3: User Story 1 - Chuẩn hóa 4 vai trò duy nhất (Priority: P1) 🎯 MVP

**Goal**: `database.sql` + `back_up.sql` sau khi SỬA TRỰC TIẾP chỉ còn đúng 4 vai trò chuẩn (ID 1=Admin, 2=Quản lý, 3=Seller, 4=Customer); 100% `Users.Role_Id` trỏ tới 1 trong 4 vai trò; không còn bảng `Permissions`/`Modules` (FR-001, FR-002, FR-003, FR-009)

**Independent Test**: Phân tích tĩnh `database.sql` + `back_up.sql` — đúng 4 dòng Roles ID 1–4; mọi `INSERT [dbo].[Users]` có `Role_Id` ∈ {1,2,3,4}; không còn chuỗi `Permissions`/`Modules` (SC-001)

### Tests cho User Story 1 (BẮT BUỘC - Nguyên tắc IV) ⚠️

> **LƯU Ý: Viết các test này TRƯỚC, đảm bảo chúng FAIL trước khi implementation**

- [X] T007 [P] [US1] Viết static test: `Database/database.sql` và `Database/back_up.sql` chứa đúng 4 vai trò chuẩn (`INSERT [dbo].[Roles] ([RoleId], [RoleName]) VALUES (1,N'Admin')`, (2,N'Quản lý'), (3,N'Seller'), (4,N'Customer')) và KHÔNG còn vai trò thừa (Kế toán, Marketing, VIP, Shipper, Manager, ...) trong tests/unit/test_chuan_hoa_file_nguon.py
- [X] T008 [P] [US1] Viết static test: mọi `INSERT [dbo].[Users]` trong `database.sql` và `back_up.sql` đều có `Role_Id` ∈ {1,2,3,4} (không có NULL/lạ), user1 (UserId=1) → Role_Id=1, và KHÔNG còn khối `CREATE TABLE [dbo].[Permissions]`/`[dbo].[Modules]`/`INSERT [dbo].[Permissions]`/`INSERT [dbo].[Modules]` trong tests/unit/test_chuan_hoa_file_nguon.py

### Implementation cho User Story 1

- [X] T009 [US1] Sửa trực tiếp `Database/database.sql`: thu bảng `Roles` còn 4 dòng chuẩn ID 1–4; remap `Users.Role_Id` (user1→1, chủ `Stores.UserId` {2,4,6,8,10,12,14,16,18,20} → 3, còn lại → 4); xóa toàn bộ khối `Permissions`/`Modules` (CREATE TABLE + INSERT + FK/index/CHECK)
- [X] T010 [US1] Sửa trực tiếp `Database/back_up.sql` đồng bộ với T009 (FR-010): Roles 4 dòng ID 1–4; remap Users (chủ Stores {2,4,6,8,10,12,13,14,16,18,20} → 3 — Store 23 do user 13 sở hữu); xóa khối `Permissions`/`Modules`
- [X] T011 [US1] Xóa script chuẩn hóa cũ `Database/sql/001_chuan_hoa_vai_tro.sql` và XÓA 2 test cũ trỏ vào script đó: `tests/unit/test_seed_script_tinh.py`, `tests/integration/test_seed_chuan_hoa.py` (đã được thay bằng T007/T008)

**Checkpoint**: User Story 1 hoạt động độc lập, testable

---

## Phase 4: User Story 2 - Gán đúng vai trò cho dữ liệu mẫu (Priority: P1)

**Goal**: Trong `database.sql` + `back_up.sql` (sửa trực tiếp), seed `Users`/`Stores` nhất quán — user1 → Admin(1), mọi chủ `Stores` → Seller(3) (kể cả khi `IsActive=0`), còn lại → Customer(4) (FR-004)

**Independent Test**: Đối chiếu `Users.Role_Id` với `Stores.UserId` trong cả 2 file — user1 → 1, mọi `Stores.UserId` → 3, phần còn lại → 4; có ít nhất 1 Store `IsActive=0` mà chủ vẫn là Seller (SC-001, Edge case)

### Tests cho User Story 2 (BẮT BUỘC - Nguyên tắc IV) ⚠️

> **LƯU Ý: Viết các test này TRƯỚC, đảm bảo chúng FAIL trước khi implementation**

- [X] T012 [P] [US2] Viết static test seed content theo UserId trong `database.sql` + `back_up.sql`: user1→Admin(1), mọi `INSERT [dbo].[Stores]` có `UserId` → Seller(3) (kể cả dòng `IsActive=0`), các user còn lại → Customer(4); có ≥1 Store `IsActive=0` để kiểm chứng Seller giữ vai trò trong tests/unit/test_chuan_hoa_file_nguon.py

### Implementation cho User Story 2

- [X] T013 [US2] Sửa trực tiếp `Database/database.sql`: đảm bảo từng `Users.Role_Id` khớp quy tắc seed theo `Stores.UserId` (user1→1, chủ Stores→3 kể cả IsActive=0, còn lại→4); nếu chưa có, thêm 1 Store `IsActive=0` do user Seller sở hữu
- [X] T014 [US2] Sửa trực tiếp `Database/back_up.sql`: đồng bộ quy tắc seed với T013 (đặc biệt Store 23/user 13 của file này)

**Checkpoint**: User Stories 1 VÀ 2 hoạt động độc lập

---

## Phase 5: User Story 3 - Loại bỏ phân quyền ngoại lệ + toàn bộ API roles (Priority: P2)

**Goal**: Xóa `Permissions`/`Modules` khỏi backend, xóa `PhanQuyenBus`/`PhanQuyenDao`/`Model/PhanQuyen.py` + `UserBus.cap_nhat_vai_tro`, xóa 5 endpoint ngoại lệ + toàn bộ `/api/roles*` + `/api/users/<id>/role` (404), dọn UI ma trận quyền (FR-005, FR-006, FR-007)

**Independent Test**: Gọi 10 endpoint cũ → 404; grep backend 0 tham chiếu cap-quyen-ngoai-le|cap-quyen-nhom|quyen-cua-user|quyen-cua-nhom|ap-dung-quyen|Permissions|Modules|PhanQuyen|/api/roles|cap_nhat_vai_tro (SC-002)

### Tests cho User Story 3 (BẮT BUỘC - Nguyên tắc IV) ⚠️

> **LƯU Ý: Viết các test này TRƯỚC, đảm bảo chúng FAIL trước khi implementation**

- [X] T015 [P] [US3] Viết integration test: 10 endpoint cũ trả 404 (5 endpoint cap-quyen/quyen-cua + GET/POST/PUT/DELETE /api/roles + PUT /api/users/<id>/role) qua Flask test_client trong tests/integration/test_xoa_quyen_ngoai_le.py
- [X] T016 [P] [US3] Viết grep test: 0 tham chiếu cap-quyen-ngoai-le|cap-quyen-nhom|quyen-cua-user|quyen-cua-nhom|ap-dung-quyen|Permissions|Modules|PhanQuyen|/api/roles|cap_nhat_vai_tro trong app.py và thư mục back_end/ trong tests/integration/test_xoa_quyen_ngoai_le.py

### Implementation cho User Story 3

- [X] T017 [US3] Xóa khỏi app.py: 5 route ngoại lệ (`/api/cap-quyen-ngoai-le`, `/api/cap-quyen-nhom`, `/api/quyen-cua-user/<int:ma_user>`, `/api/quyen-cua-nhom/<int:ma_nhom>`, `/api/ap-dung-quyen-nhom-cho-user`), toàn bộ route `/api/roles` (GET/POST/PUT/DELETE), `PUT /api/users/<int:ma_user>/role`, cùng import/khởi tạo `phan_quyen_bus`
- [X] T018 [P] [US3] Xóa file back_end/BUS/PhanQuyenBus.py
- [X] T019 [P] [US3] Xóa file back_end/DAO/PhanQuyenDao.py
- [X] T020 [P] [US3] Xóa file back_end/Model/PhanQuyen.py
- [X] T021 [US3] Xóa phương thức `cap_nhat_vai_tro` khỏi back_end/BUS/UserBus.py và back_end/DAO/UserDao.py (gán vai trò chỉ qua seed — không để code chết; `cap_nhat_trang_thai` GIỮ LẠI để thêm guard Admin ở T030)
- [X] T022 [US3] Xóa UI ma trận quyền khỏi templates/index.html: menu-permissions, pane-permissions, tblPermissionsBody, tblGroupPermissionsBody, panel CUD roles
- [X] T023 [US3] Xóa logic quyền/roles khỏi static/js/main.js: loadAndApplyAdminPermissions, renderPermissionsTable, load/savePermissionsData, load/saveGroupPermissions, themNhomQuyen... và mọi fetch cap-quyen-*/quyen-cua-*/roles

**Checkpoint**: Các user story đều hoạt động độc lập

---

## Phase 6: User Story 4 - Kiểm tra đăng nhập theo vai trò mới (Priority: P2)

**Goal**: `/api/dang-nhap` trả `ten_vai_tro` duy nhất; `Role_Id` NULL/lạ bị từ chối rõ ràng (không crash); chặn khóa Admin ở BUS + DB guard `CK_Users_Admin_KhongDuocKhoa`; đăng ký mới gán Customer(Role_Id=4) (FR-008, FR-009, Edge Cases)

**Independent Test**: Đăng nhập tài khoản mẫu 4 vai trò trả đúng `ten_vai_tro`; banned (non-admin) bị từ chối; khóa Admin bị từ chối ("Không ai có quyền khóa tài khoản Admin!"); Role_Id NULL/lạ bị từ chối (SC-003)

### Tests cho User Story 4 (BẮT BUỘC - Nguyên tắc IV) ⚠️

> **LƯU Ý: Viết các test này TRƯỚC, đảm bảo chúng FAIL trước khi implementation**

- [X] T024 [P] [US4] Viết unit test: UserBus.dang_nhap trả `ten_vai_tro` + `ten_vai_tro_hien_thi` cho cả 4 vai trò chuẩn với mock DAO trong tests/unit/test_user_bus_vai_tro.py
- [X] T025 [P] [US4] Viết unit test: UserBus.cap_nhat_trang_thai TỪ CHỐI khóa Admin ("Không ai có quyền khóa tài khoản Admin!"), dang_ky_khach_hang gán Customer, Role_Id NULL/lạ bị từ chối rõ ràng (không crash) trong tests/unit/test_user_bus_vai_tro.py
- [X] T026 [P] [US4] Viết integration test: POST /api/dang-nhap cho 4 vai trò + banned (non-admin) + Role_Id NULL/lạ bị từ chối qua Flask test_client trong tests/integration/test_dang_nhap_vai_tro.py

### Implementation cho User Story 4

- [X] T027 [US4] Sửa `dang_nhap` trong back_end/DAO/UserDao.py: `LEFT JOIN Roles r ON u.Role_id = r.RoleId` lấy `RoleName` trong cùng 1 query, dùng placeholder `?`, có commit/rollback/finally (giữ hành vi banned)
- [X] T028 [US4] Thêm helper `lay_ten_vai_tro_theo_id(role_id)` trong back_end/DAO/UserDao.py với docstring tiếng Việt (map 1=Admin, 2=Quản lý, 3=Seller, 4=Customer)
- [X] T029 [US4] Sửa `dang_nhap` trong back_end/BUS/UserBus.py: trả `ten_vai_tro` + `ten_vai_tro_hien_thi` vào `data`; Role_Id NULL/lạ → `{"status": False, "message": "Dữ liệu vai trò không hợp lệ! Vui lòng liên hệ quản trị viên.", "data": None}` (không crash)
- [X] T030 [US4] Sửa `cap_nhat_trang_thai` trong back_end/BUS/UserBus.py: nếu user có vai trò Admin → từ chối `{"status": False, "message": "Không ai có quyền khóa tài khoản Admin!"}` (gọi `lay_ten_vai_tro_theo_id`/thông tin user qua DAO, mock friendly)
- [X] T031 [US4] Sửa `dang_ky_khach_hang` trong back_end/BUS/UserBus.py: gán Customer theo Role_Id=4 (bỏ hardcode 14 cũ)
- [X] T032 [US4] Thêm DB guard chống khóa Admin (sửa trực tiếp `Database/database.sql` VÀ `Database/back_up.sql`): CHECK constraint `CK_Users_Admin_KhongDuocKhoa` = `NOT (trang_thai = N'banned' AND Role_Id = 1)`; `database.sql` còn cần thêm cột `trang_thai` (DEFAULT 'active') nếu chưa có

**Checkpoint**: Cả 4 user story testable độc lập; SC-003 kiểm chứng được

---

## Phase 7: Polish & Cross-Cutting Concerns

**Mục đích**: Cải tiến ảnh hưởng nhiều user story

- [X] T033 [P] Chạy kiểm chứng theo specs/001-role-refactor/quickstart.md (phân tích tĩnh database.sql/back_up.sql theo §1, pytest -v, UI 3 vai trò, grep backend 0)
- [X] T034 [P] Soát nhất quán cuối: `Database/database.sql` vs `Database/back_up.sql` (4 Roles ID 1–4, seed Users/Stores đồng bộ, không Permissions/Modules, có CK_Users_Admin_KhongDuocKhoa)
- [X] T035 Chạy toàn bộ pytest -v xanh và tự soát 7 cổng G1–G7 theo specs/001-role-refactor/plan.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Không phụ thuộc — bắt đầu ngay
- **Foundational (Phase 2)**: Phụ thuộc Setup — CHẶN mọi user story
- **User Stories (Phase 3+)**: Đều phụ thuộc Foundational
  - Có thể song song (nếu đủ nhân sự) hoặc tuần tự theo ưu tiên (P1 → P2)
- **Polish (Final Phase)**: Phụ thuộc các user story muốn giao

### User Story Dependencies

- **User Story 1 (P1)**: Sau Foundational — không phụ thuộc story khác; kết quả database.sql/back_up.sql chuẩn là nền cho US2/US4
- **User Story 2 (P1)**: Sau Foundational — mở rộng seed trong cùng 2 file dump của US1 (phải chạy SAU T009/T010); testable độc lập qua static parse
- **User Story 3 (P2)**: Sau Foundational — xóa code độc lập với sửa dump; thứ tự an toàn: xóa code (T017–T023) trước khi rà khối `Permissions`/`Modules` trong dump (đã xử lý ở US1) — research R3
- **User Story 4 (P2)**: Sau Foundational — cần tên vai trò chuẩn ID 1–4 từ US1; testable độc lập với mock

### Trong Từng User Story

- Tests PHẢI viết trước và FAIL trước implementation (Nguyên tắc IV - bắt buộc)
- Thứ tự Model → DAO → BUS → Controller (endpoint) → UI (Nguyên tắc I)
- Core trước integration; hoàn thành story trước khi chuyển sang story ưu tiên kế tiếp

### Cơ Hội Song Song

- Setup tasks [P]: chạy song song
- Foundational tasks [P]: chạy song song (trong Phase 2)
- Tests [P] trong cùng một user story: chạy song song
- Xóa file T018/T019/T020: song song (khác file)
- Unit tests T024/T025/T026: song song (mock-based)

---

## Parallel Example: User Story 3

```bash
# Chạy tất cả test User Story 3 cùng lúc (bắt buộc Nguyên tắc IV):
Task: "Integration test 10 endpoint cũ trả 404 trong tests/integration/test_xoa_quyen_ngoai_le.py"
Task: "Grep test 0 tham chiếu backend trong tests/integration/test_xoa_quyen_ngoai_le.py"

# Chạy tất cả xóa file User Story 3 cùng lúc:
Task: "Xóa file back_end/BUS/PhanQuyenBus.py"
Task: "Xóa file back_end/DAO/PhanQuyenDao.py"
Task: "Xóa file back_end/Model/PhanQuyen.py"
```

---

## Implementation Strategy

### MVP First (Chỉ User Story 1)

1. Hoàn thành Phase 1: Setup
2. Hoàn thành Phase 2: Foundational (CRITICAL - chặn mọi story)
3. Hoàn thành Phase 3: User Story 1
4. **STOP và KIỂM CHỨNG**: Test User Story 1 độc lập (Roles=4, orphan Users=0 qua static parse database.sql/back_up.sql)
5. Deploy/demo nếu sẵn sàng

### Incremental Delivery

1. Xong Setup + Foundational → Foundation ready
2. Thêm User Story 1 → Test độc lập → Deploy/Demo (MVP!)
3. Thêm User Story 2 → Test độc lập → Deploy/Demo
4. Thêm User Story 3 → Test độc lập → Deploy/Demo
5. Thêm User Story 4 → Test độc lập → Deploy/Demo
6. Mỗi story thêm giá trị mà không phá story trước

### Parallel Team Strategy

- Developer A: US1 + US2 (sửa trực tiếp database.sql/back_up.sql + static test)
- Developer B: US3 (xóa routes app.py + xóa 3 file PhanQuyen + cap_nhat_vai_tro + index.html/main.js)
- Developer C: US4 (UserDao.py + UserBus.py + DB Admin guard)
- Tất cả: Phase 7 polish khi các story xong

---

## MVP Scope

- **MVP**: User Story 1 (T001–T011) — database.sql/back_up.sql chỉ còn 4 vai trò, không user mồ côi; kiểm chứng qua quickstart §1 (phân tích tĩnh file)
- **MVP+Seed**: + User Story 2 (T012–T014) — demo đăng nhập theo vai trò khả thi
- **Full 001**: + US3 (xóa phân quyền ngoại lệ) + US4 (đăng nhập + Admin guard) + Polish (T033–T035)

## Notes

- `Database/database.sql` và `Database/back_up.sql` đang ở trạng thái gốc (git restore) — CHƯA được sửa; chỉ sửa bằng thao tác block (header `/****** Object: Table [dbo].[X]` → `GO`), giữ UTF-16 BOM.
- `Database/sql/001_chuan_hoa_vai_tro.sql` (do hướng cũ tạo) PHẢI bị xóa ở T011; `Database/sql.bak` giữ làm lịch sử.
- Role IDs CỐ ĐỊNH 1=Admin, 2=Quản lý, 3=Seller, 4=Customer — T031/T032 dùng ID 4/constraint theo đó, không hardcode ID cũ (13/14/19/20).
- Chủ `Stores`: `database.sql` → {2,4,6,8,10,12,14,16,18,20}; `back_up.sql` → {2,4,6,8,10,12,13,14,16,18,20} (Store 23 do user 13 sở hữu).
- Không còn API roles — KHÔNG tạo lại GET /api/roles hay PUT /api/users/<id>/role.
- `cap_nhat_vai_tro` (BUS + DAO) bị xóa cùng route gán vai trò (roles.contract.md) — không để code chết.
- Tests KHÔNG được chạm PobbyDB thật — mock DAO + Flask test_client + phân tích tĩnh file dump.