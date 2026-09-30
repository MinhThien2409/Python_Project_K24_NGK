# Pobby Shop

Pobby là ứng dụng web thương mại điện tử đa vai trò, xây dựng bằng Python/Flask, PyMySQL và MySQL. Tài liệu này được tái dựng từ implementation hiện tại.

## Tính năng chính
- Đăng ký, đăng nhập, đăng xuất, phiên và hồ sơ.
- Quản lý user, trạng thái tài khoản và tài khoản Quản lý theo quyền.
- Đăng ký/duyệt/từ chối Seller và quản lý gian hàng.
- Danh mục, sản phẩm, giỏ hàng và đặt hàng.
- Checkout nhiều shop: backend nhóm item theo shop và tạo các đơn tương ứng.
- Seller quản lý sản phẩm, tồn kho, giá, đơn hàng, trang shop và thống kê.
- Backend chấp nhận COD, Bank, Momo và VNPay.

## Công nghệ
Python, Flask, Flask-CORS, PyMySQL, MySQL, HTML/CSS/JavaScript, pytest. gunicorn có trong requirements nhưng không có deployment configuration riêng.

## Cài đặt
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt

Tạo cấu hình local:
    Copy-Item back_end\DBconfig.example.py back_end\DBconfig.py

Environment variables database: POBBY_DB_HOST, POBBY_DB_PORT, POBBY_DB_USER, POBBY_DB_PASSWORD, POBBY_DB_NAME.

## Database
Fresh setup:
    mysql -u root -p --default-character-set=utf8mb4 < Database/schema_mysql.sql
    mysql -u root -p --default-character-set=utf8mb4 PobbyDB < Database/seed_demo_mysql.sql

Windows có thể dùng Database/import_mysql.bat. schema_mysql.sql có DROP/CREATE database nên chỉ dùng khi chủ động tái tạo database. database_mysql.sql là combined schema + seed. fix_utf8mb4.sql là recovery utility.

## Chạy
    python app.py

Direct Flask run dùng port 5000. Mở http://localhost:5000.

## Test
    pytest
    pytest tests/unit/
    pytest tests/integration/

Current verified regression:
    617 passed
    0 failed
    0 errors

Syntax:
    python -m compileall -q app.py back_end

Whitespace:
    git diff --check

## Hành vi quan trọng
Seller statistics:
- Có year trong request -> dùng năm được truyền.
- Không có year -> datetime.now().year.
- Không còn fallback cố định 2026.

ShippingFee vẫn theo implementation hiện tại: request cung cấp ShippingFee; backend kiểm tra phí không âm và khi tách đơn nhiều shop phân bổ tổng phí theo số shop. Phase 7 không thay đổi behavior này.

## Known limitations
- POBBY_SECRET_KEY có fallback trong app.py.
- Database configuration có fallback values.
- python app.py vẫn chạy Flask với debug=True.
- ShippingFee chưa có cơ chế cấu hình bởi Admin.
- Không có deployment configuration riêng để xác nhận quy trình production cụ thể.

Chi tiết: docs/ARCHITECTURE.md, docs/DATABASE.md, docs/TESTING.md, docs/CONFIGURATION.md, docs/CHANGELOG.md.
