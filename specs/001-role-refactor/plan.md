# Implementation Plan: Tái cấu trúc vai trò — 4 vai trò duy nhất

**Branch**: `001-role-refactor` | **Date**: 2026-09-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification từ `/specs/001-role-refactor/spec.md`

## Summary

Chuẩn hóa hệ thống vai trò về đúng 4 vai trò cố định (Admin, Quản lý, Seller, Customer) bằng cách **sửa đổi trực tiếp trên mã nguồn hiện có**: KHÔNG tạo hàm riêng để chuẩn hóa, KHÔNG tạo SQL script riêng để chuẩn hóa (chỉ đạo 2026-09-17). Cụ thể:
- `Database/database.sql` và `Database/back_up.sql` được **chỉnh thẳng**: bảng `Roles` chỉ còn 4 dòng ID cố định **1=Admin, 2=Quản lý, 3=Seller, 4=Customer**; `Users.Role_Id` được remap (user1 → 1; user sở hữu `Stores.UserId` → 3; còn lại → 4); khối `CREATE TABLE` + `INSERT` + ràng buộc của `Permissions`/`Modules` bị xóa khỏi file; `database.sql` được bổ sung thẳng `trang_thai` + `CHECK (NOT (trang_thai = N'banned' AND Role_Id = 1))` (`CK_Users_Admin_KhongDuocKhoa`).
- Xóa hoàn toàn cơ chế phân quyền ngoại lệ: xóa file `PhanQuyenBus.py`/`PhanQuyenDao.py`/`Model/PhanQuyen.py`, xóa 5 endpoint `cap-quyen-*`/`quyen-cua-*`, UI ma trận quyền trong `index.html`/`main.js`.
- Xóa toàn bộ API quản lý vai trò (`/api/roles*`, `/api/users/<id>/role` → 404); 4 vai trò chỉ tồn tại trong file nguồn, không đổi lúc runtime.
- Không ai có quyền khóa Admin (chặn ở `UserBus.cap_nhat_trang_thai` + guard DB `CK_Users_Admin_KhongDuocKhoa`).
- `/api/dang-nhap` trả về vai trò duy nhất (`ten_vai_tro` + `ten_vai_tro_hien_thi`) để UI phân nhánh.
- Kiểm thử (Nguyên tắc IV): static test trực tiếp trên nội dung `database.sql`/`back_up.sql` + unit/integration test với mock DAO; không chạm `PobbyDB` thật.

## Technical Context

**Language/Version**: Python 3.13.7 (`.venv` hiện có; hiến chương ghi 3.11+ — tương thích)

**Primary Dependencies**: Flask, Flask-CORS, pyodbc (xem `requirements.txt`); thêm `pytest` cho test (Nguyên tắc IV)

**Storage**: Microsoft SQL Server (SQLEXPRESS), database `PobbyDB`; schema nguồn sự thật `Database/database.sql` (UTF-16LE có BOM, cấu trúc `INSERT [dbo].[Roles] ([RoleId], [RoleName])` + `INSERT [dbo].[Users] ...`). Cột vai trò thực tế là `Users.Role_Id` (INT NULL, không FK). `Roles` hiện có 20 dòng (1–20; 4 vai trò chuẩn cũ nằm ở Seller=13, Customer=14, Manager=19, Admin=20). `Permissions`/`Modules` sẽ bị **xóa khỏi file nguồn** (không còn script DROP). `Stores(UserId, IsActive)` là căn cứ xác định Seller (chủ `Stores`: `database.sql` → {2,4,6,8,10,12,14,16,18,20}; `back_up.sql` → thêm {13} do Store 23). Theo chỉ đạo 2026-09-17: sửa trực tiếp file nguồn, ID 4 vai trò cố định 1–4, không có script chuẩn hóa riêng.

**Testing**: pytest, đặt trong `tests/unit/`, `tests/integration/`; test dùng mock tầng DAO + Flask test_client + phân tích tĩnh `database.sql`/`back_up.sql`; KHÔNG chạm `PobbyDB` thật
**Target Platform**: Windows, chạy local `http://localhost:5000`
**Project Type**: Web application (Flask backend + Jinja2/vanilla-JS frontend)

**Performance Goals**: P95 API < 200ms; trang tải < 2s (theo `BRD_TRD_REPORT.md` OBJ-05); không có script runtime nên không chịu chi phí chuẩn hóa lúc chạy

**Constraints**: CSS/JS thuần, không framework UI; không thêm build step; giao diện giữ đúng design system trong `static/css/style.css`; tên bảng/cột giữ `PascalCase` tiếng Anh, KHÔNG đổi tên cột; mọi SQL trong code dùng placeholder `?`; ghi có `commit`/`rollback`/`finally`

**Scale/Scope**: Spec nền tảng cho chuỗi 001–007; chạm FR-001→FR-011 của spec 001 (bản chỉ đạo 2026-09-17: sửa trực tiếp file nguồn, xóa toàn bộ API roles, không ai được khóa Admin)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Kiểm tra theo Hiến chương Pobby v1.0.0. Mọi mục KHÔNG đạt phải được sửa hoặc ghi vào
mục "Complexity Tracking" kèm lý do.

| # | Cổng (theo Nguyên tắc) | Câu hỏi kiểm tra | Đạt? |
|---|------------------------|------------------|------|
| G1 | I — Kiến trúc ba lớp | Thiết kế có giữ đúng Model → DAO → BUS → Controller? Không có SQL trong BUS, không validate trong `app.py`? | ✅ Đạt — validate vai trò + chặn khóa Admin vào `UserBus`, mọi SQL vào `UserDao` (JOIN Roles), `app.py` chỉ đọc request + gọi BUS + jsonify; `PhanQuyenBus/Dao` + `Model/PhanQuyen.py` bị xóa hoàn toàn |
| G2 | Techn. Constraints — Hợp đồng API | Endpoint mới trả về `status` + `message` tiếng Việt (+ `data`)? URL theo `/api/` gạch-nối? | ✅ Đạt — không thêm endpoint mới; `/api/dang-nhap` giữ hợp đồng `{status, message, data}` và mở rộng `data` thêm `ten_vai_tro`/`ten_vai_tro_hien_thi`; 5 endpoint ngoại lệ + toàn bộ API roles bị xóa → 404 (hành vi chuẩn Flask) |
| G3 | IV — Kiểm thử bắt buộc | Kế hoạch có unit test BUS + integration test endpoint + test ca biên, viết trước khi code? | ✅ Đạt — quickstart.md quy định test-first: static test nội dung file nguồn (4 vai trò, Role_Id hợp lệ, không còn Permissions/Modules, có CHECK), unit BUS (`dang_nhap` theo vai trò, `cap_nhat_trang_thai` chặn khóa Admin), integration (đăng nhập 4 vai trò, 404 endpoint roles/quyền cũ), ca biên (Role_Id NULL/lạ, banned) |
| G4 | II — Giao diện nhất quán | UI chỉ dùng biến CSS sẵn có, font `Be Vietnam Pro`/`Nunito`, KHÔNG thêm framework UI? | ✅ Đạt — chỉ XÓA UI ma trận quyền (`pane-permissions`, `tblPermissionsBody`, `tblGroupPermissionsBody`, `menu-permissions`), không thêm màu/font/component mới |
| G5 | V — An toàn dữ liệu | Truy vấn dùng placeholder `?`, có `commit`/`rollback`/`finally`, không hardcode bí mật, kiểm tra phân quyền? | ✅ Đạt — DAO sửa dùng placeholder `?`, transaction đầy đủ; không hardcode bí mật mới; lưu ý nợ plaintext/hardcode kết nối đã ghi nhận ở Assumptions; guard chống khóa Admin cả BUS + DB CHECK |
| G6 | III — Dễ hiểu vì học tập | Hàm có docstring tiếng Việt, tên `snake_case` tiếng Việt, hàm dưới ~40 dòng? | ✅ Đạt — hàm mới (`lay_ten_vai_tro`, `chan_khoa_admin`) đặt tên tiếng Việt không dấu, docstring tiếng Việt, < 40 dòng |
| G7 | VI — Đơn giản & phạm vi | Không thêm thư viện/tầng trừu tượng mới, không thêm tính năng ngoài `BRD_TRD_REPORT.md` mục 1.3? | ✅ Đạt — chỉ thêm `pytest` (công cụ test bắt buộc theo Nguyên tắc IV); KHÔNG thêm script chuẩn hóa riêng (chỉ đạo 2026-09-17, đơn giản hơn); phạm vi = BR23 đơn giản hóa còn 4 vai trò, đã ghi nhận trong spec Assumptions |

**Kết luận Constitution Check (pre-design)**: PASS — 7/7 cổng đạt, không cần Complexity Tracking.

**Tái kiểm tra sau Phase 1 design (chỉ đạo 2026-09-17)**: PASS — research.md/data-model.md/contracts/quickstart.md giữ nguyên 7 cổng: SQL chỉ trong DAO (không có script chuẩn hóa riêng — bỏ được chi phí duy trì script), validate + chặn khóa Admin chỉ trong BUS, response giữ `{status, message, data}` tiếng Việt, test-first với mock + phân tích tĩnh file nguồn (không chạm PobbyDB thật), UI chỉ xóa không thêm, placeholder `?` + transaction đầy đủ, hàm < 40 dòng có docstring tiếng Việt, không thư viện mới ngoài `pytest`.

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
app.py                          # Controller Flask - XÓA 5 routes cap-quyen-*/quyen-cua-* + TOÀN BỘ routes roles (/api/roles*, /api/users/<id>/role); GIỮ /api/dang-nhap (data mở rộng ten_vai_tro)
back_end/
├── DBconnection.py             # KHÔNG đổi (nợ hardcode đã ghi nhận)
├── Model/
│   ├── User.py                 # KHÔNG đổi (ma_nhom_quyen ↔ Users.Role_Id)
│   └── PhanQuyen.py            # XÓA file
├── DAO/
│   └── UserDao.py              # SỬA dang_nhap JOIN Roles lấy RoleName; THÊM lay_ten_vai_tro_theo_id; SỬA cap_nhat_trang_thai chặn khóa Admin (kèm guard ở BUS)
│   # PhanQuyenDao.py           # XÓA FILE hoàn toàn (không còn API roles/quyền)
└── BUS/
    └── UserBus.py              # SỬA dang_nhap trả ten_vai_tro + ten_vai_tro_hien_thi; SỬA dang_ky_khach_hang gán Customer (Role_Id=4); SỬA cap_nhat_trang_thai chặn khóa Admin ("Không ai có quyền khóa Admin!")
    # PhanQuyenBus.py           # XÓA FILE hoàn toàn (không còn API roles/quyền)

Database/
├── database.sql                # SỬA TRỰC TIẾP: Roles chỉ còn 4 dòng (1=Admin, 2=Quản lý, 3=Seller, 4=Customer); remap Users.Role_Id (user1→1, chủ Stores→3, còn lại→4); XÓA khối Permissions/Modules (CREATE+INSERT+FK/index/CHECK); THÊM trang_thai + CHECK CK_Users_Admin_KhongDuocKhoa
├── back_up.sql                 # SỬA TRỰC TIẾP đồng bộ với database.sql (FR-010; đã có trang_thai, thêm CHECK)
├── sql.bak                     # Bản gốc 5MB đã dời ra (giữ làm lịch sử)
└── sql/001_chuan_hoa_vai_tro.sql  # XÓA — script chuẩn hóa cũ không còn dùng (chỉ đạo 2026-09-17)

static/js/main.js                # XÓA: loadAndApplyAdminPermissions, renderPermissionsTable, load/savePermissionsData, load/saveGroupPermissions, quản lý nhóm quyền (themNhomQuyen...) + mọi fetch cap-quyen-*/quyen-cua-*/roles

templates/index.html             # XÓA: menu-permissions, pane-permissions, panel quản lý nhóm quyền (tblGroupPermissionsBody, roles CUD)

tests/                           # MỚI (Nguyên tắc IV, viết TRƯỚC implementation)
├── unit/
│   ├── test_chuan_hoa_file_nguon.py   # static test database.sql + back_up.sql: đúng 4 vai trò ID 1–4, User.Role_Id ∈{1,2,3,4}, user1→1, chủ Stores→3, không còn Permissions/Modules, có CK_Users_Admin_KhongDuocKhoa
│   └── test_user_bus_vai_tro.py       # BUS: dang_nhap trả đúng ten_vai_tro 4 vai trò; chan_khoa_admin (cap_nhat_trang_thai Admin→banned bị từ chối); dang_ky gán Customer
└── integration/
    ├── test_dang_nhap_vai_tro.py      # đăng nhập 4 vai trò + banned (non-admin) + Role_Id NULL/lạ → từ chối
    └── test_xoa_quyen_ngoai_le.py     # 5 endpoint ngoại lệ + toàn bộ /api/roles* + /api/users/<id>/role → 404; grep backend 0 tham chiếu Permissions/Modules/PhanQuyen
```

**Structure Decision**: Feature chạm `app.py` (xóa routes quyền + roles, giữ `/api/dang-nhap`), `back_end/BUS/UserBus.py` + `back_end/DAO/UserDao.py` (vai trò đăng nhập + chặn khóa Admin), XÓA `back_end/BUS/PhanQuyenBus.py` + `back_end/DAO/PhanQuyenDao.py` + `back_end/Model/PhanQuyen.py`, SỬA TRỰC TIẾP `Database/database.sql` + `Database/back_up.sql` (4 vai trò + remap user + xóa Permissions/Modules + CHECK; không tạo script chuẩn hóa mới), dọn UI `templates/index.html` + `static/js/main.js`, test mới trong `tests/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |