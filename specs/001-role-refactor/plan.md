# Implementation Plan: Tái cấu trúc vai trò — 4 vai trò duy nhất

**Branch**: `001-role-refactor` | **Date**: 2026-09-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-role-refactor/spec.md`

## Summary

Chuẩn hóa hệ thống vai trò về đúng 4 vai trò cố định (Admin, Quản lý, Seller, Customer) theo hướng **rebuild seed**: script SQL idempotent trong `Database/sql/` **xóa bỏ dữ liệu cũ không phù hợp** (roles thừa, user có `Role_Id` NULL/lạ, dữ liệu `Permissions`/`Modules`) và **tạo mới SQL dữ liệu mẫu** (user1 → Admin; user sở hữu `Stores.UserId` → Seller; còn lại → Customer; tên vai trò chuẩn chốt trong seed mới). Xóa hoàn toàn cơ chế phân quyền ngoại lệ (DROP bảng `Permissions`/`Modules`, xóa file `PhanQuyenBus.py`/`PhanQuyenDao.py`/`Model/PhanQuyen.py`, xóa 5 endpoint `cap-quyen-*`/`quyen-cua-*`, UI ma trận quyền trong `index.html`/`main.js`) và **xóa toàn bộ API quản lý vai trò** (`/api/roles*`, `/api/users/<id>/role` → 404; 4 vai trò chỉ tồn tại trong seed, không đổi lúc runtime). Không ai có quyền khóa Admin (chặn ở `UserBus.cap_nhat_trang_thai` + thay đổi cấu trúc DB nếu cần). `/api/dang-nhap` trả về vai trò duy nhất để UI phân nhánh.

## Technical Context

**Language/Version**: Python 3.13.7 (`.venv` hiện có; hiến chương ghi 3.11+ — tương thích)

**Primary Dependencies**: Flask, Flask-CORS, pyodbc (xem `requirements.txt`); thêm `pytest` cho test (Nguyên tắc IV)

**Storage**: Microsoft SQL Server (SQLEXPRESS), database `PobbyDB`; schema nguồn sự thật `Database/database.sql`; cột vai trò thực tế là `Users.Role_id` (INT NULL, không FK); bảng `Roles(RoleId IDENTITY, RoleName)` hiện có 20 dòng; bảng `Permissions`/`Modules` sẽ bị DROP; bảng `Stores(UserId, IsActive)` là căn cứ xác định Seller. Theo clarify 2026-09-17: rebuild seed (xóa dữ liệu cũ không phù hợp, tạo SQL dữ liệu mẫu mới với 4 tên vai trò chuẩn); không còn API roles nên không cần giữ ID 13/14/19/20 cố định — ID do seed mới quyết định

**Testing**: pytest, đặt trong `tests/unit/`, `tests/integration/` (chưa tồn tại — plan này tạo mới); test dùng mock tầng DAO + Flask test_client, KHÔNG chạm `PobbyDB` thật

**Target Platform**: Windows, chạy local `http://localhost:5000`

**Project Type**: Web application (Flask backend + Jinja2/vanilla-JS frontend)

**Performance Goals**: P95 API < 200ms; trang tải < 2s (theo `BRD_TRD_REPORT.md` OBJ-05); script chuẩn hóa chạy < 5s trên dữ liệu mẫu

**Constraints**: CSS/JS thuần, không framework UI; không thêm build step; giao diện giữ đúng design system trong `static/css/style.css`; tên bảng/cột giữ `PascalCase` tiếng Anh, KHÔNG đổi tên cột; mọi SQL dùng placeholder `?`; ghi có `commit`/`rollback`/`finally`

**Scale/Scope**: Spec nền tảng cho chuỗi 001–007; chạm FR-001→FR-011 của spec 001 (bản clarify 2026-09-17: rebuild seed, xóa toàn bộ API roles, không ai được khóa Admin)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Kiểm tra theo Hiến chương Pobby v1.0.0. Mọi mục KHÔNG đạt phải được sửa hoặc ghi vào
mục "Complexity Tracking" kèm lý do.

| # | Cổng (theo Nguyên tắc) | Câu hỏi kiểm tra | Đạt? |
|---|------------------------|------------------|------|
| G1 | I — Kiến trúc ba lớp | Thiết kế có giữ đúng Model → DAO → BUS → Controller? Không có SQL trong BUS, không validate trong `app.py`? | ✅ Đạt — validate vai trò + chặn khóa Admin vào `UserBus`, mọi SQL vào `UserDao`, `app.py` chỉ đọc request + gọi BUS + jsonify; `PhanQuyenBus/Dao` + `Model/PhanQuyen.py` bị xóa hoàn toàn |
| G2 | Techn. Constraints — Hợp đồng API | Endpoint mới trả về `status` + `message` tiếng Việt (+ `data`)? URL theo `/api/` gạch-nối? | ✅ Đạt — không thêm endpoint mới; `/api/dang-nhap` giữ hợp đồng `{status, message, data}`; 5 endpoint ngoại lệ + toàn bộ API roles bị xóa → 404 (hành vi chuẩn Flask) |
| G3 | IV — Kiểm thử bắt buộc | Kế hoạch có unit test BUS + integration test endpoint + test ca biên, viết trước khi code? | ✅ Đạt — quickstart.md quy định test-first: unit BUS (`dang_nhap` theo vai trò, `cap_nhat_trang_thai` chặn khóa Admin, seed validation), integration (đăng nhập 4 vai trò, 404 endpoint roles/quyền cũ), ca biên (Role_Id NULL/lạ bị seed xóa) |
| G4 | II — Giao diện nhất quán | UI chỉ dùng biến CSS sẵn có, font `Be Vietnam Pro`/`Nunito`, KHÔNG thêm framework UI? | ✅ Đạt — chỉ XÓA UI ma trận quyền (`pane-permissions`, `tblPermissionsBody`, `tblGroupPermissionsBody`, `menu-permissions`), không thêm màu/font/component mới |
| G5 | V — An toàn dữ liệu | Truy vấn dùng placeholder `?`, có `commit`/`rollback`/`finally`, không hardcode bí mật, kiểm tra phân quyền? | ✅ Đạt — script SQL + DAO mới dùng placeholder `?`, transaction đầy đủ; không hardcode bí mật mới; lưu ý nợ plaintext/hardcode kết nối đã ghi nhận ở Assumptions |
| G6 | III — Dễ hiểu vì học tập | Hàm có docstring tiếng Việt, tên `snake_case` tiếng Việt, hàm dưới ~40 dòng? | ✅ Đạt — hàm mới (`lay_ten_vai_tro`, `chan_khoa_admin`, validate seed) đặt tên tiếng Việt không dấu, docstring tiếng Việt, < 40 dòng |
| G7 | VI — Đơn giản & phạm vi | Không thêm thư viện/tầng trừu tượng mới, không thêm tính năng ngoài `BRD_TRD_REPORT.md` mục 1.3? | ✅ Đạt — chỉ thêm `pytest` (công cụ test bắt buộc theo Nguyên tắc IV); phạm vi = BR23 đơn giản hóa còn 4 vai trò, đã ghi nhận trong spec Assumptions |

**Kết luận Constitution Check (pre-design)**: PASS — 7/7 cổng đạt, không cần Complexity Tracking.

**Tái kiểm tra sau Phase 1 design (bản clarify 2026-09-17)**: PASS — research.md/data-model.md/contracts/quickstart.md giữ nguyên 7 cổng: SQL chỉ trong DAO + script `Database/sql/`, validate + chặn khóa Admin chỉ trong BUS, response giữ `{status, message, data}` tiếng Việt, test-first với mock (không chạm PobbyDB thật), UI chỉ xóa không thêm, placeholder `?` + transaction đầy đủ, hàm < 40 dòng có docstring tiếng Việt, không thư viện mới ngoài `pytest`.

## Project Structure

### Documentation (this feature)

```text
specs/001-role-refactor/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── dang-nhap.contract.md
│   └── roles.contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
app.py                          # Controller Flask - XÓA 5 routes cap-quyen-*/quyen-cua-* + TOÀN BỘ routes roles (/api/roles*, /api/users/<id>/role); GIỮ /api/dang-nhap (mở rộng data thêm ten_vai_tro)
back_end/
├── DBconnection.py             # KHÔNG đổi (nợ hardcode đã ghi nhận)
├── Model/
│   ├── User.py                 # KHÔNG đổi (ma_nhom_quyen ↔ Users.Role_id)
│   └── PhanQuyen.py            # XÓA file
├── DAO/
│   └── UserDao.py              # SỬA dang_nhap JOIN Roles lấy RoleName; THÊM lay_ten_vai_tro_theo_id; SỬA cap_nhat_trang_thai chặn khóa Admin (kèm guard ở BUS)
│   # PhanQuyenDao.py           # XÓA FILE hoàn toàn (không còn API roles/quyền)
└── BUS/
    └── UserBus.py              # SỬA dang_nhap trả ten_vai_tro + ten_vai_tro_hien_thi; SỬA dang_ky_khach_hang gán Customer theo ID seed mới; SỬA cap_nhat_trang_thai chặn khóa Admin ("Không ai có quyền khóa Admin!")
    # PhanQuyenBus.py           # XÓA FILE hoàn toàn (không còn API roles/quyền)

Database/
├── database.sql                # SỬA: Roles chỉ còn 4 dòng chuẩn (tên chốt trong seed mới); DROP Permissions/Modules; rebuild seed Users/Stores mẫu (user1 Admin, chủ Stores Seller, còn lại Customer); thêm guard chống khóa Admin nếu cần (CHECK/constraint)
├── back_up.sql                 # Đồng bộ với database.sql (FR-010)
└── sql/
    └── 001_chuan_hoa_vai_tro.sql  # MỚI: script idempotent rebuild seed — xóa dữ liệu cũ không phù hợp (roles thừa, user Role NULL/lạ, Permissions/Modules) + tạo mới 4 roles + seed Users/Stores mẫu (FR-003/FR-004/FR-009)

static/js/main.js                # XÓA: loadAndApplyAdminPermissions, renderPermissionsTable, load/savePermissionsData, load/saveGroupPermissions, quản lý nhóm quyền (themNhomQuyen...) + mọi fetch cap-quyen-*/quyen-cua-*/roles

templates/index.html             # XÓA: menu-permissions, pane-permissions, panel quản lý nhóm quyền (tblGroupPermissionsBody, roles CUD)

tests/                           # MỚI (Nguyên tắc IV, viết TRƯỚC implementation)
├── unit/
│   └── test_user_bus_vai_tro.py       # dang_nhap trả đúng ten_vai_tro 4 vai trò; chan_khoa_admin (cap_nhat_trang_thai Admin→banned bị từ chối); dang_ky gán Customer
└── integration/
    ├── test_dang_nhap_vai_tro.py      # đăng nhập 4 vai trò + banned (non-admin) + seed không còn Role NULL/lạ
    └── test_xoa_quyen_ngoai_le.py     # 5 endpoint ngoại lệ + toàn bộ /api/roles* + /api/users/<id>/role → 404; grep backend 0 tham chiếu Permissions/Modules/PhanQuyen
```

**Structure Decision**: Feature chạm `app.py` (xóa routes quyền + roles, giữ `/api/dang-nhap`), `back_end/BUS/UserBus.py` + `back_end/DAO/UserDao.py` (vai trò đăng nhập + chặn khóa Admin), XÓA `back_end/BUS/PhanQuyenBus.py` + `back_end/DAO/PhanQuyenDao.py` + `back_end/Model/PhanQuyen.py`, script rebuild seed `Database/sql/001_chuan_hoa_vai_tro.sql` + đồng bộ `database.sql`/`back_up.sql`, dọn UI `templates/index.html` + `static/js/main.js`, test mới trong `tests/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
