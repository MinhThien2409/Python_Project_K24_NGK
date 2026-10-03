# Database

## Canonical sources
- Database/schema_mysql.sql — canonical schema.
- Database/seed_demo_mysql.sql — canonical demo data.
- Database/database_mysql.sql — combined schema + seed.
- Database/import_mysql.bat — Windows setup/import tooling.
- Database/fix_utf8mb4.sql — recovery/data-repair utility.

Legacy SQL đã bị loại khỏi active source set: database.sql, back_up.sql, Database/sql/, SQL_data.sql, SqlAll.sql.

## Engine
MySQL + PyMySQL. Canonical schema tạo PobbyDB với utf8mb4 và utf8mb4_unicode_ci.

## 14 bảng canonical
1. Roles
2. Users
3. Accounts
4. Stores
5. Categories
6. Products
7. Carts
8. CartItems
9. SellerRequests
10. Orders
11. OrderItems
12. StockReceipts
13. StockReceiptItems
14. Suppliers

## Foreign keys đã xác nhận
- Accounts.UserId -> Users.UserId
- Accounts.Role_Id -> Roles.RoleId
- Stores.UserId -> Users.UserId
- Products.CategoryId -> Categories.CategoryId
- Products.StoreId -> Stores.StoreId
- Carts.UserId -> Users.UserId
- CartItems.CartId -> Carts.CartId
- CartItems.ProductId -> Products.ProductId
- SellerRequests.UserId -> Users.UserId
- Orders.CartId -> Carts.CartId
- Orders.UserId -> Users.UserId
- OrderItems.OrderId -> Orders.OrderId
- OrderItems.ProductId -> Products.ProductId
- StockReceiptItems.ReceiptId -> StockReceipts.ReceiptId
- StockReceiptItems.ProductId -> Products.ProductId

Không suy diễn thêm FK mà schema không khai báo.

## Fresh setup
    mysql -u root -p --default-character-set=utf8mb4 < Database/schema_mysql.sql
    mysql -u root -p --default-character-set=utf8mb4 PobbyDB < Database/seed_demo_mysql.sql

import_mysql.bat chạy đúng hai bước trên. schema_mysql.sql có DROP DATABASE, vì vậy không chạy trên runtime database cần giữ dữ liệu.

database_mysql.sql chỉ là combined source, không phải runtime database riêng.

## Recovery
fix_utf8mb4.sql là utility phục hồi encoding dữ liệu tiếng Việt; không phải bước setup bắt buộc.

## Runtime
Phase 7 không import, seed, reset, migrate hoặc write runtime DB.
