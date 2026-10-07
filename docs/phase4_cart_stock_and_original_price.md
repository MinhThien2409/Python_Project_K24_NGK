# Phase 4 — T111 + T96

## Phạm vi

- T111: cộng dồn quantity theo ProductId khi kiểm tồn và trừ kho ở checkout.
- T96: chặn trạng thái giá gốc bất thường; OldPrice chỉ tồn tại khi là giá gốc thực sự cao hơn giá bán.

Không thay đổi phạm vi sang T58/T63/T26 hoặc các phase sau.

## T111 — Aggregate quantity

Luồng server:

1. DonHangDao._nap_du_lieu_san_pham_checkout() lấy toàn bộ ProductId và khóa row bằng SELECT ... FOR UPDATE.
2. Server cộng dồn Quantity theo ProductId.
3. Kiểm total_quantity <= Products.Quantity.
4. Sau khi kiểm tồn hợp lệ, server reload ProductName/Price từ DB và tính lại TotalPrice, SubTotal, TotalAmount.
5. _chen_items_tru_kho() vẫn snapshot từng OrderItem nhưng chỉ thực hiện một UPDATE trừ kho cho mỗi ProductId, với tổng quantity.
6. Voucher cũng cộng dồn quantity của ProductId đủ điều kiện trước khi kiểm tồn.

Ví dụ: payload có cùng ProductId với quantity 3 + 4, tồn kho 5 → từ chối với requested 7; không thể chia nhỏ payload để vượt kiểm tồn.

## T96 — Giá gốc bất thường

Invariant server:

- Price > 0.
- Nếu OldPrice có giá trị: OldPrice > Price > 0.
- Không có giảm giá: OldPrice = NULL.
- OldPrice <= 0, OldPrice == Price, hoặc OldPrice < Price → từ chối.

Áp dụng cho Seller tạo sản phẩm, sửa sản phẩm, cập nhật giá. DAO cap_nhat_gia() cũng kiểm tra quan hệ giá trước khi ghi.

Backend tự tính discount percent từ giá thật; không tin discount_percent từ client.

## Test

File mới: tests/integration/test_phase4_cart_stock_and_original_price.py

Bao phủ duplicate ProductId vượt tồn; duplicate ProductId trong tồn; trừ kho theo aggregate; tamper duplicate payload qua API; aggregate quantity + server price reload; giá gốc hợp lệ; OldPrice bằng/lower/zero/negative; create/edit product với OldPrice bất thường; tắt giảm giá xóa OldPrice; BUS không cho payload bất thường đi tới DAO.

## Kết quả

- Phase 4 targeted regression + Phase 3 authority + Phase 4 price API: 23 passed.
- Full unit + integration: 882 passed, 13 failed, 1 warning.
- 13 failure là nhóm baseline đã tồn tại trước Phase 4, gồm mock giỏ hàng thiếu lay_gio_hang_id, các assertion dialect cũ và Phase 8 static assertion; không phải regression của T111/T96.
- node --check static/js/main.js: PASS.
- py_compile: PASS.
- git diff --check: PASS.
- Playwright runtime T111: duplicate 6 + 5 cho ProductId 1 với tồn 10 bị server từ chối, báo còn 10.
- Playwright runtime T96: Seller sửa ProductId 1 với Price = OldPrice = 32,000,000 bị server từ chối: Giá gốc phải lớn hơn giá bán!

## Ghi chú

pytest.ini chứa addopts = --headed --slowmo 300, nên verification headless/CLI được chạy bằng -o addopts='' để pytest không truyền option Playwright không phù hợp cho test backend.
