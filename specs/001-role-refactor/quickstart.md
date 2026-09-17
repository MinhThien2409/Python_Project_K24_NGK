# Quickstart: kiểm chứng 001-role-refactor

**Branch**: `001-role-refactor` | **Spec**: [spec.md](./spec.md) | **Contracts**: [contracts.md](./contracts.md)

## Điều kiện

- SQL Server (SQLEXPRESS) + DB `PobbyDB` từ `Database/database.sql`.
- Python `.venv` đã kích hoạt; cài test: `pip install pytest`.

## 1. Chuẩn hóa vai trò — sửa trực tiếp file nguồn (FR-001→FR-004, FR-009, FR-010)

Không còn script chuẩn hóa riêng (chỉ đạo 2026-09-17): `Database/database.sql` và `Database/back_up.sql`
**được sửa trực tiếp** để chứa sẵn dữ liệu chuẩn hóa. Kiểm chứng trực tiếp nội dung 2 file (SC-001):

```sql
-- database.sql / back_up.sql: chỉ còn đúng 4 dòng Roles
--   INSERT [dbo].[Roles] ([RoleId], [RoleName]) VALUES (1, N'Admin')
--   ... (2, N'Quản lý'), (3, N'Seller'), (4, N'Customer')
-- Mọi dòng INSERT [dbo].[Users] ... đều có Role_Id ∈ {1,2,3,4}; không có NULL/lạ.
-- UserId=1 → Role_Id=1 (Admin); user có Stores.UserId → Role_Id=3 (Seller); còn lại → 4.
-- Không còn khối CREATE TABLE/INSERT [dbo].[Permissions] và [dbo].[Modules].
-- database.sql có cột trang_thai + CHECK (NOT (trang_thai = N'banned' AND Role_Id = 1)).
```

Sau khi nạp `database.sql` vào `PobbyDB`, truy vấn xác nhận:

```sql
SELECT RoleId, RoleName FROM Roles ORDER BY RoleId;
-- Kỳ vọng: đúng 4 dòng chuẩn 1=Admin, 2=Quản lý, 3=Seller, 4=Customer
SELECT COUNT(*) AS mo_coi FROM Users u LEFT JOIN Roles r ON u.Role_Id = r.RoleId WHERE u.Role_Id IS NULL OR r.RoleId IS NULL;
-- Kỳ vọng: 0
SELECT UserId, Role_Id FROM Users WHERE UserId = 1;            -- Kỳ vọng: 1 (Admin)
SELECT DISTINCT UserId FROM Stores;                             -- mọi ID này có vai trò Seller (3)
```

## 2. Test tự động (FR-011, SC-004) — viết TRƯỚC code, chạy cho xanh

```powershell
pytest tests/unit/test_chuan_hoa_file_nguon.py -v
pytest tests/integration/test_dang_nhap_vai_tro.py tests/integration/test_xoa_quyen_ngoai_le.py -v
pytest -v
```

- Unit: `database.sql`/`back_up.sql` chứa đúng 4 vai trò (ID 1–4), mọi user `Role_Id` hợp lệ,
  không còn `Permissions`/`Modules`, có `CK_Users_Admin_KhongDuocKhoa`; đăng nhập trả đúng
  `ten_vai_tro` 4 vai trò; `Role_Id` NULL/lạ → từ chối rõ ràng; `cap_nhat_trang_thai` chặn khóa Admin
  ("Không ai có quyền khóa tài khoản Admin!"); đăng ký mới gán Customer (ID 4).
- Integration: POST `/api/dang-nhap` user1→Admin, seller→Seller, customer→Customer, banned (non-admin)→từ chối; 5 endpoint ngoại lệ + toàn bộ `/api/roles*` + `/api/users/<id>/role` → **404**.

## 3. Kiểm tra UI (SC-005)

1. `python app.py` → mở `http://localhost:5000`.
2. Không còn menu "🔐 Quản lý phân quyền", không còn `pane-permissions` / bảng nhóm quyền.
3. Đăng nhập user1 (Admin) / seller / customer → đúng bộ chức năng, không lỗi console (3 giao diện Customer/Seller/Admin hiển thị như trước).

## 4. Soát mã nguồn (SC-002)

```powershell
Select-String -Pattern "cap-quyen-ngoai-le|cap-quyen-nhom|quyen-cua-user|quyen-cua-nhom|ap-dung-quyen|Permissions|Modules|PhanQuyen|/api/roles|cap_nhat_vai_tro" -Path app.py, back_end -Recurse
# Kỳ vọng: 0 kết quả trong backend (database.sql/back_up.sql không phải nơi chứa code; không còn khối Permissions/Modules)
```

## Ghi chú nợ kỹ thuật (ngoài phạm vi, đã ghi nhận)

- Mật khẩu plaintext + hardcode `sa/123` trong `DBconnection.py` — xử lý ở spec riêng.
- Cột `trang_thai` đã được bổ sung trực tiếp vào `database.sql`; `database.sql`/`back_up.sql` nhất quán theo FR-010.
