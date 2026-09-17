# Contract: POST /api/dang-nhap (sau 001-role-refactor)

**Giữ nguyên URL + hợp đồng `{status, message, data}`. Chỉ mở rộng `data` thêm vai trò.**

## Request

```json
{ "tendangnhap": "user1", "mat_khau": "123456" }
```

## Response thành công — Admin

```json
{
  "status": true,
  "message": "Chào mừng Nguyễn Văn An trở lại!",
  "data": {
    "ma_user": 1,
    "ten_user": "Nguyễn Văn An",
    "ma_nhom_quyen": 1,
    "ten_vai_tro": "Admin",
    "ten_vai_tro_hien_thi": "Admin",
    "dia_chi": "...",
    "sdt": "...",
    "cmnd": "..."
  }
}
```

## Ánh xạ vai trò (ID cố định ghi trực tiếp trong file nguồn)

| `ma_nhom_quyen` (RoleId) | `ten_vai_tro` (DB) | `ten_vai_tro_hien_thi` (UI) |
|---|---|---|
| 1 | Admin | Admin |
| 2 | Quản lý | Quản lý |
| 3 | Seller | Seller |
| 4 | Customer | Customer |

## Response các trường hợp

| Trường hợp | `status` | `message` | `data` |
|---|---|---|---|
| Thiếu tài khoản/mật khẩu | False | "Vui lòng nhập tài khoản và mật khẩu!" | None |
| Sai thông tin | False | "Tên đăng nhập hoặc mật khẩu không chính xác!" | None |
| Bị khóa (`banned`, non-admin) | False | "Tài khoản của bạn đã bị khóa! ..." (giữ nguyên) | None |
| `Role_Id` NULL/lạ (DB bị sửa tay sau seed) | False | "Dữ liệu vai trò không hợp lệ! Vui lòng liên hệ quản trị viên." | None |

## Nguồn dữ liệu

`UserDao.dang_nhap` JOIN `Roles` (`LEFT JOIN Roles r ON u.Role_id = r.RoleId`) để lấy `RoleName` trong cùng 1 query; không query 2 lần.
