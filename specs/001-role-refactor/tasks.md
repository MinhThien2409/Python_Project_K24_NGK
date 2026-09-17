# Tasks: Tái cấu trúc vai trò — 4 vai trò duy nhất (001-role-refactor)

**Input**: Design documents from `/specs/001-role-refactor/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md)

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: REQUIRED — Hiến chương Pobby Nguyên tắc IV. Test viết TRƯỚC implementation (test-first), chạy bằng `pytest`, đặt trong `tests/unit/` và `tests/integration/`. KHÔNG chạm PobbyDB thật (mock DAO + Flask test_client).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions (Pobby)

- Backend: `back_end/Model/`, `back_end/DAO/`, `back_end/BUS/`, controller `app.py`
- Frontend: `templates/index.html`, `static/js/main.js`
- Tests: `tests/unit/`, `tests/integration/`
- DB: `Database/database.sql`, `Database/back_up.sql`, script mới `Database/sql/001_chuan_hoa_vai_tro.sql`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create tests directory structure tests/unit and tests/integration with __init__.py files
- [ ] T002 Add pytest to requirements.txt
- [ ] T003 [P] Resolve Database/sql file-vs-directory conflict (Database/sql is currently a 5MB binary backup file — move to Database/sql.bak) to allow Database/sql/001_chuan_hoa_vai_tro.sql directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create pytest mock helpers for UserDao and Flask test_client without touching PobbyDB in tests/conftest.py
- [ ] T005 [P] Define 4 canonical role names seed fixture (Admin, Quản lý, Seller, Customer) in tests/conftest.py
- [ ] T006 Verify pytest collects empty suite green via pytest -v with tests/conftest.py in repository root

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Chuẩn hóa 4 vai trò duy nhất (Priority: P1) 🎯 MVP

**Goal**: Bảng Roles chỉ còn đúng 4 dòng chuẩn; 100% Users.Role_Id trỏ tới 4 vai trò này (FR-001, FR-002, FR-003, FR-009)

**Independent Test**: Truy vấn Roles sau script rebuild seed — đúng 4 dòng; truy vấn Users mồ côi (`LEFT JOIN Roles`) — 0 dòng (SC-001)

### Tests for User Story 1 (REQUIRED - Nguyên tắc IV) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T007 [P] [US1] Static seed-script validation test (assert IF EXISTS, presence of 4 canonical role names, orphan-check SELECT) in tests/unit/test_seed_script_tinh.py
- [ ] T008 [P] [US1] Seed verification test for Roles count=4 and orphan Users=0 by static content parse of Database/sql/001_chuan_hoa_vai_tro.sql (no real DB) in tests/integration/test_seed_chuan_hoa.py

### Implementation for User Story 1

- [ ] T009 [US1] Write idempotent rebuild-seed script Database/sql/001_chuan_hoa_vai_tro.sql (single transaction: DROP FK + DROP Permissions/Modules IF EXISTS, DELETE non-canonical Roles, INSERT missing 4 canonical roles, purge Users with Role_Id NULL/invalid, final verification SELECT)
- [ ] T010 [US1] Sync Database/database.sql to 4 canonical Roles and DROP Permissions/Modules tables
- [ ] T011 [US1] Sync Database/back_up.sql to 4 canonical Roles and DROP Permissions/Modules tables

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Gán đúng vai trò cho dữ liệu mẫu (Priority: P1)

**Goal**: Seed Users/Stores mẫu nhất quán — user1 Admin, mọi chủ Stores là Seller, còn lại Customer (FR-004)

**Independent Test**: Đối chiếu Users với Stores — user1 → Admin, mọi Stores.UserId → Seller (giữ vai trò dù IsActive=0), còn lại → Customer

### Tests for User Story 2 (REQUIRED - Nguyên tắc IV) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US2] Seed content test (user1 Admin, store owners Seller, rest Customer, Seller kept when IsActive=0, keyed by UserId) parsing Database/sql/001_chuan_hoa_vai_tro.sql in tests/integration/test_seed_du_lieu_mau.py

### Implementation for User Story 2

- [ ] T013 [US2] Extend Database/sql/001_chuan_hoa_vai_tro.sql with seed Users/Stores INSERT statements (user1 Admin, store owners Seller, rest Customer) keyed by UserId — include a Store with IsActive=0 to verify Seller retention
- [ ] T014 [US2] Sync seed Users/Stores INSERT statements into Database/database.sql
- [ ] T015 [US2] Sync seed Users/Stores INSERT statements into Database/back_up.sql

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Loại bỏ phân quyền ngoại lệ + toàn bộ API roles (Priority: P2)

**Goal**: Xóa Permissions/Modules, PhanQuyenBus/PhanQuyenDao/Model/PhanQuyen.py + UserBus.cap_nhat_vai_tro, 5 endpoint ngoại lệ + toàn bộ /api/roles* + /api/users/<id>/role (404), dọn UI ma trận quyền (FR-005, FR-006, FR-007)

**Independent Test**: Gọi 10 endpoint cũ → 404; grep backend 0 tham chiếu cap-quyen-ngoai-le|cap-quyen-nhom|quyen-cua-user|quyen-cua-nhom|ap-dung-quyen|Permissions|Modules|PhanQuyen|/api/roles|cap_nhat_vai_tro (SC-002)

### Tests for User Story 3 (REQUIRED - Nguyên tắc IV) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [P] [US3] Integration test deleted endpoints return 404 (5 cap-quyen/quyen-cua endpoints + GET/POST/PUT/DELETE /api/roles + PUT /api/users/<id>/role) in tests/integration/test_xoa_quyen_ngoai_le.py
- [ ] T017 [P] [US3] Backend grep test: zero references to cap-quyen-ngoai-le|cap-quyen-nhom|quyen-cua-user|quyen-cua-nhom|ap-dung-quyen|Permissions|Modules|PhanQuyen|/api/roles|cap_nhat_vai_tro in backend code (app.py, back_end/) in tests/integration/test_xoa_quyen_ngoai_le.py

### Implementation for User Story 3

- [ ] T018 [US3] Remove 5 exception-permission routes, all /api/roles* routes, PUT /api/users/<id>/role, and phan_quyen_bus import/init from app.py
- [ ] T019 [P] [US3] Delete file back_end/BUS/PhanQuyenBus.py
- [ ] T020 [P] [US3] Delete file back_end/DAO/PhanQuyenDao.py
- [ ] T021 [P] [US3] Delete file back_end/Model/PhanQuyen.py
- [ ] T022 [US3] Remove cap_nhat_vai_tro from back_end/BUS/UserBus.py and back_end/DAO/UserDao.py (role assignment only via seed; cap_nhat_trang_thai stays with new Admin guard)
- [ ] T023 [US3] Remove permission matrix UI (menu-permissions, pane-permissions, tblPermissionsBody, tblGroupPermissionsBody, roles CUD panel) from templates/index.html
- [ ] T024 [US3] Remove permission/roles fetch logic (loadAndApplyAdminPermissions, renderPermissionsTable, load/savePermissionsData, load/saveGroupPermissions, themNhomQuyen, cap-quyen/quyen-cua/roles fetches) from static/js/main.js

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Kiểm tra đăng nhập theo vai trò mới (Priority: P2)

**Goal**: /api/dang-nhap trả ten_vai_tro duy nhất của tài khoản; Role NULL/lạ bị từ chối rõ ràng; chặn khóa Admin ở BUS + DB guard; đăng ký mới gán Customer (FR-008, FR-009, Edge Cases)

**Independent Test**: Đăng nhập tài khoản mẫu 4 vai trò trả đúng ten_vai_tro; banned non-admin bị từ chối; khóa Admin bị từ chối; Role NULL/lạ bị từ chối (SC-003)

### Tests for User Story 4 (REQUIRED - Nguyên tắc IV) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T025 [P] [US4] Unit test UserBus.dang_nhap returns ten_vai_tro + ten_vai_tro_hien_thi for 4 canonical roles with mocked DAO in tests/unit/test_user_bus_vai_tro.py
- [ ] T026 [P] [US4] Unit tests: UserBus.cap_nhat_trang_thai refuses to ban Admin ("Không ai có quyền khóa tài khoản Admin!"), dang_ky_khach_hang assigns Customer, Role_Id NULL/invalid rejected clearly in tests/unit/test_user_bus_vai_tro.py
- [ ] T027 [P] [US4] Integration test POST /api/dang-nhap for 4 roles + banned (non-admin) + NULL-role rejection via Flask test_client in tests/integration/test_dang_nhap_vai_tro.py

### Implementation for User Story 4

- [ ] T028 [US4] Update UserDao.dang_nhap in back_end/DAO/UserDao.py to LEFT JOIN Roles for RoleName with placeholder ? and commit/rollback/finally
- [ ] T029 [US4] Add lay_ten_vai_tro_theo_id helper with Vietnamese docstring in back_end/DAO/UserDao.py
- [ ] T030 [US4] Update UserBus.dang_nhap in back_end/BUS/UserBus.py to return ten_vai_tro + ten_vai_tro_hien_thi and reject Role_Id NULL/invalid clearly (no crash)
- [ ] T031 [US4] Guard UserBus.cap_nhat_trang_thai in back_end/BUS/UserBus.py to refuse banning Admin
- [ ] T032 [US4] Update UserBus.dang_ky_khach_hang in back_end/BUS/UserBus.py to assign Customer role id read from new seed (no hardcoded old ID)
- [ ] T033 [US4] Add DB guard against banning Admin (CHECK/constraint, e.g. Admin never 'banned') in Database/sql/001_chuan_hoa_vai_tro.sql and sync to Database/database.sql plus Database/back_up.sql

**Checkpoint**: All 4 user stories independently testable; SC-003 verifiable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Run quickstart.md validation (seed idempotent rerun via sqlcmd, pytest -v, UI 3-role visual check, backend grep zero) per specs/001-role-refactor/quickstart.md
- [ ] T035 [P] Final consistency check of Database/database.sql and Database/back_up.sql (4 Roles, seed Users/Stores synced, no Permissions/Modules tables)
- [ ] T036 Full pytest -v green and constitution gate re-check (G1-G7) per specs/001-role-refactor/plan.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories; script skeleton Database/sql/001_chuan_hoa_vai_tro.sql needed by US2/US4
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Extends US1 seed script file; independently testable via seed content
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Code deletion independent of seed; DROP Permissions/Modules must run after code deletion (research R3)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Needs canonical role names from US1/US2 seed; independently testable with mocks

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Nguyên tắc IV - bắt buộc)
- Model → DAO → BUS → Controller (endpoint) → UI (Nguyên tắc I)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- File deletions T019/T020/T021 can run in parallel (different files)
- Unit tests T025/T026/T027 can run in parallel (mock-based)

---

## Parallel Example: User Story 3

```bash
# Launch all tests for User Story 3 together (bắt buộc theo Nguyên tắc IV):
Task: "Integration test deleted endpoints return 404 in tests/integration/test_xoa_quyen_ngoai_le.py"
Task: "Backend grep test zero references in tests/integration/test_xoa_quyen_ngoai_le.py"

# Launch all deletions for User Story 3 together:
Task: "Delete file back_end/BUS/PhanQuyenBus.py"
Task: "Delete file back_end/DAO/PhanQuyenDao.py"
Task: "Delete file back_end/Model/PhanQuyen.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Roles=4, orphan Users=0)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

- Developer A: US1 + US2 (seed script + database.sql back_up.sql sync)
- Developer B: US3 (app.py routes deletion + 3 file deletions + cap_nhat_vai_tro removal + index.html + main.js)
- Developer C: US4 (UserDao.py + UserBus.py + DB Admin guard)
- All: Phase 7 polish together after stories complete

---

## MVP Scope

- **MVP**: User Story 1 only (T001–T011) — Roles=4 + orphan Users=0 verifiable via quickstart section 1
- **MVP+Seed**: + User Story 2 (T012–T015) — demo login per role possible
- **Full 001**: + US3 (deletion) + US4 (login + Admin guard) + Polish (T034–T036)

## Notes

- `Database/sql` is currently a 5MB binary backup FILE, not a directory — T003 must resolve before T009.
- Role IDs are NOT fixed (13/14/19/20) — canonical names from new seed; T032/T028 must read IDs from seed, not hardcode old IDs.
- No API roles remain — do NOT recreate GET /api/roles or PUT /api/users/<id>/role.
- cap_nhat_vai_tro (BUS + DAO) is removed together with the role-assignment route (roles.contract.md) — do not keep dead code.
- Tests must NOT touch real PobbyDB — mock DAO + Flask test_client only.