-- fix_utf8mb4.sql
-- Khôi phục dữ liệu tiếng Việt bị lỗi mojibake trong PobbyDB.
--
-- NGUYÊN NHÂN: khi import schema_mysql.sql + seed_demo_mysql.sql bằng `mysql`
-- mà KHÔNG chỉ định `--default-character-set=utf8mb4`, client trên Windows mặc
-- định dùng mã trang CP850 → chuỗi UTF-8 (bytes đúng) bị hiểu nhầm thành CP850
-- rồi lưu vào cột utf8mb4 → nhìn thấy dạng "Quß║ún l├¢", "─Éiß╗çn thoß║íi".
--
-- CÁCH SỬA (ngược lại đúng chuỗi chuyển đổi hỏng):
--     CONVERT(BINARY(CONVERT(cot USING cp850)) USING utf8mb4)
--   - CONVERT(cot USING cp850) : ánh xạ từng ký tự mojibake về đúng BYTE UTF-8 gốc
--   - BINARY(...)              : coi kết quả là chuỗi byte
--   - ... USING utf8mb4        : giải mã các byte đó thành UTF-8 đúng
--
-- AN TOÀN (chạy lại được, không phá dữ liệu đã đúng):
--   Mỗi cột được chuyển THEO ĐIỀU KIỆN RIÊNG qua CASE, chỉ khi:
--       1) không NULL,
--       2) toàn bộ ký tự vừa trong CP850 (không tạo ký tự thay thế '?'),
--       3) phép chuyển ngược làm THAY ĐỔI giá trị (COLLATE utf8mb4_unicode_ci
--          để so sánh đồng nhất với collation cột, tránh lỗi 1267).
--   Dữ liệu ASCII thuần / tiếng Việt đã lưu ĐÚNG / NULL → giữ nguyên.
--   WHERE chỉ chạy UPDATE trên dòng có ≥ 1 cột bị lỗi.
--
-- CÁCH CHẠY:
--     mysql -u root -p --default-character-set=utf8mb4 < Database/fix_utf8mb4.sql

USE PobbyDB;

-- 1) Roles
UPDATE Roles
SET RoleName = CASE
    WHEN RoleName IS NOT NULL
     AND INSTR(CONVERT(RoleName USING cp850), '?') = 0
     AND CONVERT(BINARY(CONVERT(RoleName USING cp850)) USING utf8mb4)
         COLLATE utf8mb4_unicode_ci <> RoleName
    THEN CONVERT(BINARY(CONVERT(RoleName USING cp850)) USING utf8mb4)
    ELSE RoleName END
WHERE RoleName IS NOT NULL
  AND INSTR(CONVERT(RoleName USING cp850), '?') = 0
  AND CONVERT(BINARY(CONVERT(RoleName USING cp850)) USING utf8mb4)
      COLLATE utf8mb4_unicode_ci <> RoleName;

-- 2) Users
UPDATE Users
SET FullName = CASE
        WHEN FullName IS NOT NULL
         AND INSTR(CONVERT(FullName USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(FullName USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> FullName
        THEN CONVERT(BINARY(CONVERT(FullName USING cp850)) USING utf8mb4)
        ELSE FullName END,
    Address  = CASE
        WHEN Address IS NOT NULL
         AND INSTR(CONVERT(Address USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(Address USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> Address
        THEN CONVERT(BINARY(CONVERT(Address USING cp850)) USING utf8mb4)
        ELSE Address END
WHERE (FullName IS NOT NULL
       AND INSTR(CONVERT(FullName USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(FullName USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> FullName)
   OR (Address IS NOT NULL
       AND INSTR(CONVERT(Address USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(Address USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> Address);

-- 3) Stores
UPDATE Stores
SET StoreName   = CASE
        WHEN StoreName IS NOT NULL
         AND INSTR(CONVERT(StoreName USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(StoreName USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> StoreName
        THEN CONVERT(BINARY(CONVERT(StoreName USING cp850)) USING utf8mb4)
        ELSE StoreName END,
    Address     = CASE
        WHEN Address IS NOT NULL
         AND INSTR(CONVERT(Address USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(Address USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> Address
        THEN CONVERT(BINARY(CONVERT(Address USING cp850)) USING utf8mb4)
        ELSE Address END,
    Category    = CASE
        WHEN Category IS NOT NULL
         AND INSTR(CONVERT(Category USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(Category USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> Category
        THEN CONVERT(BINARY(CONVERT(Category USING cp850)) USING utf8mb4)
        ELSE Category END,
    Description = CASE
        WHEN Description IS NOT NULL
         AND INSTR(CONVERT(Description USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(Description USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> Description
        THEN CONVERT(BINARY(CONVERT(Description USING cp850)) USING utf8mb4)
        ELSE Description END
WHERE (StoreName IS NOT NULL
       AND INSTR(CONVERT(StoreName USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(StoreName USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> StoreName)
   OR (Address IS NOT NULL
       AND INSTR(CONVERT(Address USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(Address USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> Address)
   OR (Category IS NOT NULL
       AND INSTR(CONVERT(Category USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(Category USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> Category)
   OR (Description IS NOT NULL
       AND INSTR(CONVERT(Description USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(Description USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> Description);

-- 4) Categories
UPDATE Categories
SET CategoryName = CASE
    WHEN CategoryName IS NOT NULL
     AND INSTR(CONVERT(CategoryName USING cp850), '?') = 0
     AND CONVERT(BINARY(CONVERT(CategoryName USING cp850)) USING utf8mb4)
         COLLATE utf8mb4_unicode_ci <> CategoryName
    THEN CONVERT(BINARY(CONVERT(CategoryName USING cp850)) USING utf8mb4)
    ELSE CategoryName END
WHERE CategoryName IS NOT NULL
  AND INSTR(CONVERT(CategoryName USING cp850), '?') = 0
  AND CONVERT(BINARY(CONVERT(CategoryName USING cp850)) USING utf8mb4)
      COLLATE utf8mb4_unicode_ci <> CategoryName;

-- 5) Products
UPDATE Products
SET ProductName  = CASE
        WHEN ProductName IS NOT NULL
         AND INSTR(CONVERT(ProductName USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(ProductName USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> ProductName
        THEN CONVERT(BINARY(CONVERT(ProductName USING cp850)) USING utf8mb4)
        ELSE ProductName END,
    Description  = CASE
        WHEN Description IS NOT NULL
         AND INSTR(CONVERT(Description USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(Description USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> Description
        THEN CONVERT(BINARY(CONVERT(Description USING cp850)) USING utf8mb4)
        ELSE Description END,
    ImageUrl     = CASE
        WHEN ImageUrl IS NOT NULL
         AND INSTR(CONVERT(ImageUrl USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(ImageUrl USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> ImageUrl
        THEN CONVERT(BINARY(CONVERT(ImageUrl USING cp850)) USING utf8mb4)
        ELSE ImageUrl END,
    Emoji        = CASE
        WHEN Emoji IS NOT NULL
         AND INSTR(CONVERT(Emoji USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(Emoji USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> Emoji
        THEN CONVERT(BINARY(CONVERT(Emoji USING cp850)) USING utf8mb4)
        ELSE Emoji END
WHERE (ProductName IS NOT NULL
       AND INSTR(CONVERT(ProductName USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(ProductName USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> ProductName)
   OR (Description IS NOT NULL
       AND INSTR(CONVERT(Description USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(Description USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> Description)
   OR (ImageUrl IS NOT NULL
       AND INSTR(CONVERT(ImageUrl USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(ImageUrl USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> ImageUrl)
   OR (Emoji IS NOT NULL
       AND INSTR(CONVERT(Emoji USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(Emoji USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> Emoji);

-- 6) SellerRequests
UPDATE SellerRequests
SET ShopName     = CASE
        WHEN ShopName IS NOT NULL
         AND INSTR(CONVERT(ShopName USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(ShopName USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> ShopName
        THEN CONVERT(BINARY(CONVERT(ShopName USING cp850)) USING utf8mb4)
        ELSE ShopName END,
    Category     = CASE
        WHEN Category IS NOT NULL
         AND INSTR(CONVERT(Category USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(Category USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> Category
        THEN CONVERT(BINARY(CONVERT(Category USING cp850)) USING utf8mb4)
        ELSE Category END,
    RejectReason = CASE
        WHEN RejectReason IS NOT NULL
         AND INSTR(CONVERT(RejectReason USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(RejectReason USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> RejectReason
        THEN CONVERT(BINARY(CONVERT(RejectReason USING cp850)) USING utf8mb4)
        ELSE RejectReason END,
    Description  = CASE
        WHEN Description IS NOT NULL
         AND INSTR(CONVERT(Description USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(Description USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> Description
        THEN CONVERT(BINARY(CONVERT(Description USING cp850)) USING utf8mb4)
        ELSE Description END
WHERE (ShopName IS NOT NULL
       AND INSTR(CONVERT(ShopName USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(ShopName USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> ShopName)
   OR (Category IS NOT NULL
       AND INSTR(CONVERT(Category USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(Category USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> Category)
   OR (RejectReason IS NOT NULL
       AND INSTR(CONVERT(RejectReason USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(RejectReason USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> RejectReason)
   OR (Description IS NOT NULL
       AND INSTR(CONVERT(Description USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(Description USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> Description);

-- 7) Orders
UPDATE Orders
SET ReceiverName    = CASE
        WHEN ReceiverName IS NOT NULL
         AND INSTR(CONVERT(ReceiverName USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(ReceiverName USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> ReceiverName
        THEN CONVERT(BINARY(CONVERT(ReceiverName USING cp850)) USING utf8mb4)
        ELSE ReceiverName END,
    ShippingAddress = CASE
        WHEN ShippingAddress IS NOT NULL
         AND INSTR(CONVERT(ShippingAddress USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(ShippingAddress USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> ShippingAddress
        THEN CONVERT(BINARY(CONVERT(ShippingAddress USING cp850)) USING utf8mb4)
        ELSE ShippingAddress END,
    PaymentMethod   = CASE
        WHEN PaymentMethod IS NOT NULL
         AND INSTR(CONVERT(PaymentMethod USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(PaymentMethod USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> PaymentMethod
        THEN CONVERT(BINARY(CONVERT(PaymentMethod USING cp850)) USING utf8mb4)
        ELSE PaymentMethod END,
    Note            = CASE
        WHEN Note IS NOT NULL
         AND INSTR(CONVERT(Note USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(Note USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> Note
        THEN CONVERT(BINARY(CONVERT(Note USING cp850)) USING utf8mb4)
        ELSE Note END,
    VoucherCode     = CASE
        WHEN VoucherCode IS NOT NULL
         AND INSTR(CONVERT(VoucherCode USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(VoucherCode USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> VoucherCode
        THEN CONVERT(BINARY(CONVERT(VoucherCode USING cp850)) USING utf8mb4)
        ELSE VoucherCode END
WHERE (ReceiverName IS NOT NULL
       AND INSTR(CONVERT(ReceiverName USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(ReceiverName USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> ReceiverName)
   OR (ShippingAddress IS NOT NULL
       AND INSTR(CONVERT(ShippingAddress USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(ShippingAddress USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> ShippingAddress)
   OR (PaymentMethod IS NOT NULL
       AND INSTR(CONVERT(PaymentMethod USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(PaymentMethod USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> PaymentMethod)
   OR (Note IS NOT NULL
       AND INSTR(CONVERT(Note USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(Note USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> Note)
   OR (VoucherCode IS NOT NULL
       AND INSTR(CONVERT(VoucherCode USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(VoucherCode USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> VoucherCode);

-- 8) OrderItems
UPDATE OrderItems
SET ProductName = CASE
        WHEN ProductName IS NOT NULL
         AND INSTR(CONVERT(ProductName USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(ProductName USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> ProductName
        THEN CONVERT(BINARY(CONVERT(ProductName USING cp850)) USING utf8mb4)
        ELSE ProductName END,
    Emoji       = CASE
        WHEN Emoji IS NOT NULL
         AND INSTR(CONVERT(Emoji USING cp850), '?') = 0
         AND CONVERT(BINARY(CONVERT(Emoji USING cp850)) USING utf8mb4)
             COLLATE utf8mb4_unicode_ci <> Emoji
        THEN CONVERT(BINARY(CONVERT(Emoji USING cp850)) USING utf8mb4)
        ELSE Emoji END
WHERE (ProductName IS NOT NULL
       AND INSTR(CONVERT(ProductName USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(ProductName USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> ProductName)
   OR (Emoji IS NOT NULL
       AND INSTR(CONVERT(Emoji USING cp850), '?') = 0
       AND CONVERT(BINARY(CONVERT(Emoji USING cp850)) USING utf8mb4)
           COLLATE utf8mb4_unicode_ci <> Emoji);

-- ═══ Kiểm tra kết quả ═══
SELECT 'Roles' AS bang, RoleName AS gia_tri FROM Roles
UNION ALL SELECT 'Users', FullName FROM Users
UNION ALL SELECT 'Stores', StoreName FROM Stores
UNION ALL SELECT 'Categories', CategoryName FROM Categories
UNION ALL SELECT 'Products', ProductName FROM Products
UNION ALL SELECT 'SellerRequests', ShopName FROM SellerRequests
UNION ALL SELECT 'Orders', ReceiverName FROM Orders
UNION ALL SELECT 'OrderItems', ProductName FROM OrderItems;