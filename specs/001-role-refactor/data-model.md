# Data Model: 001-role-refactor

**Ngày**: 2026-09-17 | **Nguồn**: [spec.md](./spec.md), [research.md](./research.md)

## Entity 1: Role (Vai trò)

| Thuộc tính | Kiểu SQL | Ràng buộc | Ghi chú |
|---|---|---|---|
| `RoleId` | INT IDENTITY PK | Chỉ tồn tại 4 dòng chuẩn | ID cố định **1=Admin, 2=Quản lý, 3=Seller, 4=Customer** (sửa trực tiếp trong file nguồn) |
| `RoleName` | NVARCHAR(100) NOT NULL | UNIQUE, ∈ {Admin, Quản lý, Seller, Customer} | Tên chuẩn ghi trực tiếp trong file nguồn; hiển thị tiếng Việt ở BUS/UI |

**Validation**: Không còn API roles (FR-005 sau clarify) — không có validate runtime; tính bất biến đảm bảo bởi file nguồn được chỉnh trực tiếp + không tồn tại endpoint tạo/sửa/xóa/gán vai trò.
**State**: bất biến — 4 dòng chuẩn chỉ tồn tại trong file nguồn `database.sql`/`back_up.sql`.
**Quan hệ**: 1 Role ↔ N User qua `Users.Role_Id` (không FK vật lý, đảm bảo bởi file nguồn + không có API đổi vai trò).

## Entity 2: User (Người dùng)

| Thuộc tính | Kiểu SQL | Ràng buộc | Ghi chú |
|---|---|---|---|
| `UserId` | INT IDENTITY PK | — | Script chạy theo `UserId`, không theo tên |
| `FullName`, `Address`, `Phone`, `NationalId`, `Username`, `Password` | hiện có | giữ nguyên | Plaintext password là nợ đã ghi nhận, ngoài phạm vi spec này |
| `Role_Id` | INT NULL | Sau sửa trực tiếp: NOT NULL logic, trỏ 1 trong 4 vai trò chuẩn | File nguồn không chứa NULL/lạ; runtime gặp NULL/lạ → từ chối đăng nhập rõ ràng, không crash |
| `trang_thai` | NVARCHAR(20) NULL → 'active' | ∈ {'active','banned'}; Admin không bao giờ 'banned' | `back_up.sql` đã có; `database.sql` thiếu → thêm thẳng vào file (DEFAULT `'active'`) + `CHECK (NOT (trang_thai = N'banned' AND Role_Id = 1))` tên `CK_Users_Admin_KhongDuocKhoa` |

**Quy tắc file nguồn**: `UserId=1 → Admin(1)`; chủ `Stores` → Seller(3); còn lại → Customer(4). Seller giữ vai trò dù `Stores.IsActive=0`. File tự chứa `Users` + `Stores` nhất quán.
**Đăng nhập**: `UserDao.dang_nhap` JOIN `Roles` trả `ma_nhom_quyen + ten_vai_tro`; banned (non-admin) → từ chối (giữ hành vi cũ); Admin bị khóa → bị chặn từ `cap_nhat_trang_thai` nên không xảy ra.

## Entity 3: Store (Gian hàng) — chỉ đọc

| Thuộc tính | Kiểu | Dùng trong spec này |
|---|---|---|
| `StoreId` PK, `UserId` FK logic → Users, `IsActive` BIT | hiện có | `SELECT DISTINCT UserId FROM Stores` làm căn cứ Seller |

## Entity bị xóa: Permission / Module (+ toàn bộ quản lý roles)

- `Permissions(UserId, ModuleId, CanView/CanAdd/CanEdit/CanDelete, IsCustom)` và `Modules(ModuleId, ModuleName, ModuleCode, ...)` bị xóa khỏi file nguồn (sau khi xóa code tham chiếu). Xóa file `Model/PhanQuyen.py`, `BUS/PhanQuyenBus.py`, `DAO/PhanQuyenDao.py`.
- `PhanQuyenDao.xoa_role` từng DELETE `RolePermissions` (bảng không tồn tại) — xóa cùng toàn bộ file.

## Sơ đồ quan hệ (sau chuẩn hóa)

```mermaid
erDiagram
  ROLES ||--o{ USERS : "1 trong 4 vai tro chuan"
  USERS ||--o{ STORES : "so huu"
  ROLES {
    int RoleId PK "4 dong chuan ID 1-4"
    string RoleName "Admin, Quan ly, Seller, Customer"
  }
  USERS {
    int UserId PK
    int Role_Id "FK logic"
    string trang_thai "active,banned (Admin never banned)"
  }
```
