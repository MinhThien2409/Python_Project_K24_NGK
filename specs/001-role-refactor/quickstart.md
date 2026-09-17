# Quickstart: kiểm chứng 001-role-refactor

**Branch**: `001-role-refactor` | **Spec**: [spec.md](./spec.md) | **Contracts**: [contracts.md](./contracts.md)

## Điều kiện

- SQL Server (SQLEXPRESS) + DB `PobbyDB` từ `Database/database.sql`.
- Python `.venv` đã kích hoạt; cài test: `pip install pytest`.

## 1. Rebuild seed CSDL (FR-001→FR-004, FR-009, FR-010)

```powershell
sqlcmd -S localhost\SQLEXPRESS -d PobbyDB -i Database/sql/001_chuan_hoa_vai_tro.sql
# Chạy lại lần 2 → vẫn thành công, không lỗi (idempotent)
sqlcmd -S localhost\SQLEXPRESS -d PobbyDB -i Database/sql/001_chuan_hoa_vai_tro.sql
```

Kiểm chứng (SC-001):

```sql
SELECT RoleId, RoleName FROM Roles ORDER BY RoleId;
-- Kỳ vọng: đúng 4 dòng chuẩn của seed mới
SELECT COUNT(*) AS mo_coi FROM Users u LEFT JOIN Roles r ON u.Role_Id = r.RoleId WHERE u.Role_Id IS NULL OR r.RoleId IS NULL;
-- Kỳ vọng: 0
SELECT UserId, Role_Id FROM Users WHERE UserId = 1;            -- Kỳ vọng: vai trò Admin
SELECT DISTINCT UserId FROM Stores;                             -- mọi ID này có vai trò Seller
```

## 2. Test tự động (FR-011, SC-004) — viết TRƯỚC code, chạy cho xanh

```powershell
pytest tests/unit/test_user_bus_vai_tro.py -v
pytest tests/integration/test_dang_nhap_vai_tro.py tests/integration/test_xoa_quyen_ngoai_le.py -v
pytest -v
```

- Unit BUS: đăng nhập trả đúng `ten_vai_tro` 4 vai trò; `Role_Id` NULL/lạ → từ chối rõ ràng; `cap_nhat_trang_thai` chặn khóa Admin ("Không ai có quyền khóa tài khoản Admin!"); đăng ký mới gán Customer.
- Integration: POST `/api/dang-nhap` user1→Admin, seller→Seller, customer→Customer, banned (non-admin)→từ chối; 5 endpoint ngoại lệ + toàn bộ `/api/roles*` + `/api/users/<id>/role` → **404**.

## 3. Kiểm tra UI (SC-005)

1. `python app.py` → mở `http://localhost:5000`.
2. Không còn menu "🔐 Quản lý phân quyền", không còn `pane-permissions` / bảng nhóm quyền.
3. Đăng nhập user1 (Admin) / seller / customer → đúng bộ chức năng, không lỗi console (3 giao diện Customer/Seller/Admin hiển thị như trước).

## 4. Soát mã nguồn (SC-002)

```powershell
Select-String -Pattern "cap-quyen-ngoai-le|cap-quyen-nhom|quyen-cua-user|quyen-cua-nhom|ap-dung-quyen|Permissions|Modules|PhanQuyen|/api/roles|cap_nhat_vai_tro" -Path app.py, back_end -Recurse
# Kỳ vọng: 0 kết quả trong backend (script SQL lịch sử trong Database/ được miễn trừ)
```

## Ghi chú nợ kỹ thuật (ngoài phạm vi, đã ghi nhận)

- Mật khẩu plaintext + hardcode `sa/123` trong `DBconnection.py` — xử lý ở spec riêng.
- Cột `trang_thai` thiếu trong `database.sql` — script 001 tự thêm; `database.sql`/`back_up.sql` được đồng bộ theo.
