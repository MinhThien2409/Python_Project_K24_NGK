# Phase 6 — T26 CMND/CCCD validation

## Requirement

TRD T26 yêu cầu CMND/CCCD phải được kiểm tra định dạng, đề xuất 9 hoặc 12 chữ số, không nhận giá trị tùy ý; dữ liệu này được dùng tự động khi đăng ký gian hàng.

T54/T55 tiếp tục quy định hồ sơ phải có CMND/CCCD và Seller Request lấy giá trị từ hồ sơ, không yêu cầu người dùng nhập lại.

## Implementation

Tạo validator dùng chung:

- `back_end/BUS/validation.py`
- Regex: `^(?:\d{9}|\d{12})$`
- Cho phép đúng 9 hoặc 12 chữ số.
- Reject chữ cái, khoảng trắng giữa số, dấu gạch, sai độ dài và giá trị rỗng khi field bắt buộc.

Seller registration:

`POST /api/dang-ky-gian-hang` → session UserId → User profile → completeness check → T26 format validation → DAO.

Server không sử dụng `NationalId` từ request body. Giá trị lưu SellerRequest luôn được lấy từ profile.

Nếu profile thiếu CMND/CCCD, T54 vẫn trả về danh sách trường thiếu trước khi chạy format validation.

Profile UI được bổ sung `inputmode=numeric`, maxlength 12 và pattern 9/12 chữ số; JavaScript kiểm tra format trước khi gửi. Field profile vẫn có thể để trống ở bước cập nhật hồ sơ; khi đăng ký Seller, T54 bắt buộc phải có.

## Test matrix

Valid:

- 9 digits → PASS
- 12 digits → PASS

Invalid:

- 8 digits
- 10 digits
- 11 digits
- 13 digits
- chữ cái
- khoảng trắng
- khoảng trắng giữa số
- dấu gạch
- empty/null khi required

Seller registration:

- valid 9/12 digits → accepted
- invalid profile NationalId → rejected trước DAO insert
- direct API body gửi NationalId giả → không được tin; server vẫn lấy profile
- concurrent/duplicate Seller Request regression vẫn giữ nguyên

## Verification

Targeted Phase 6 + Phase 5 seller regression:

**32 passed, 1 warning**.

Full unit + integration:

**904 passed, 13 failed, 1 warning**.

13 failure là baseline tồn tại trước Phase 6:

- 10 failure liên quan FakeGioHangStore/MockGioHangDao thiếu `lay_gio_hang_id`
- 2 failure static assertion MySQL placeholder cũ
- 1 failure Phase 8 static assertion

Không có failure mới thuộc T26.

Static checks:

- `node --check static/js/main.js` → PASS
- `py_compile` → PASS
- `git diff --check` → PASS

## Runtime

Playwright đã kiểm tra UI profile/login surface và form Seller. Direct API T26 được kiểm chứng bằng Flask integration test với session user và profile giả lập; request body cố tình gửi NationalId khác nhưng server không sử dụng giá trị đó.

Không thay đổi database schema và không thêm UNIQUE constraint cho NationalId vì T26 chỉ yêu cầu validation format.
