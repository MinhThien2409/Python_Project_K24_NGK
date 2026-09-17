# Contracts: 001-role-refactor

Xem chi tiết: [dang-nhap](./contracts/dang-nhap.contract.md), [roles](./contracts/roles.contract.md).

## Nguyên tắc chung

- Mọi response JSON: `{status: bool, message: str (tiếng Việt), data?: ...}`.
- Endpoint bị xóa (5 endpoint ngoại lệ + toàn bộ API roles `/api/roles*`, `/api/users/<id>/role`) → Flask trả **404** mặc định.
- Không thêm endpoint mới; chỉ thu hẹp hành vi endpoint hiện có (`/api/dang-nhap` mở rộng `data` thêm vai trò).
