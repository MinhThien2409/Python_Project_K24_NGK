# Architecture

## Luồng tổng thể
    templates/static
          |
          v
        app.py
          |
          v
         BUS
          |
          v
         DAO
          |
          v
     DBconnection
          |
          v
       PyMySQL
          |
          v
        MySQL

## app.py
Flask entry point/controller. Nhận HTTP request, kiểm tra session/gate, gọi BUS, trả JSON hoặc render templates/index.html. Không trực tiếp thực hiện SQL.

## BUS
back_end/BUS chứa business logic, validation, authorization và điều phối DAO. Ví dụ: checkout, tách đơn theo shop, trạng thái đơn và seller statistics.

## DAO
back_end/DAO chứa truy vấn/persistence MySQL. Dữ liệu đầu vào được truyền bằng parameters. Một số f-string trong DonHangDao chỉ tạo số lượng placeholder, không nội suy ID vào giá trị SQL.

## Model
back_end/Model chứa entity/data objects. Database schema source of truth là Database/schema_mysql.sql.

## DBconnection
back_end/DBconnection.py dùng PyMySQL và cung cấp wrapper cursor/connection, gồm placeholder ? -> %s, commit, rollback, lastrowid và row access theo tên/index.

## DBconfig
back_end/DBconfig.py là local configuration; DBconfig.example.py là template. Hỗ trợ POBBY_DB_HOST, POBBY_DB_PORT, POBBY_DB_USER, POBBY_DB_PASSWORD, POBBY_DB_NAME.

## templates/static
templates chứa HTML/Jinja; static chứa CSS, JavaScript và assets.

## Authorization boundary
Route cần quyền gọi gate trong BUS. Seller routes phân giải store từ user/session hiện tại thay vì tin store ID do client tự chọn.

Các mô tả cũ về React, PostgreSQL, JWT, microservices hoặc SQL Server không phản ánh architecture hiện tại.
