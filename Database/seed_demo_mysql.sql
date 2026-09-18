-- seed_demo_mysql.sql
-- Dữ liệu demo cho database PobbyDB (tách riêng khỏi file tạo bảng).
-- Yêu cầu chạy trước: Database/schema_mysql.sql
--
-- Bộ tài khoản demo (mật khẩu đều là 123456):
--     admin    → Admin
--     quanly1  → Quản lý
--     seller1..3 → Người bán (mỗi seller có 1 gian hàng)
--     khach1..5  → Người mua (khach5 đang bị khóa để test chức năng khóa tài khoản)

USE PobbyDB;

-- ═══════════ VAI TRÒ ═══════════
INSERT INTO Roles (RoleId, RoleName) VALUES
(1, 'Admin'),
(2, 'Quản lý'),
(3, 'Seller'),
(4, 'Customer');

-- ═══════════ TÀI KHOẢN ═══════════
INSERT INTO Users (UserId, FullName, Address, Phone, NationalId, Username, Password, Role_Id, trang_thai) VALUES
(1,  'Nguyễn Văn An',      '120 An Liễng, Phường 12, Hà Nội',        '0901111111', '111111111', 'admin',   '123456', 1, 'active'),
(2,  'Lê Thị Quản Lý',     '12 Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh','0901111112', '111111112', 'quanly1', '123456', 2, 'active'),
(3,  'Trần Văn Bán',       '18A Cộng Hòa, Quận Tân Bình, TP. HCM',  '0901111113', '111111113', 'seller1', '123456', 3, 'active'),
(4,  'Phạm Thị Buôn',      '105 Trần Hưng Đạo, Quận 1, TP. HCM',    '0901111114', '111111114', 'seller2', '123456', 3, 'active'),
(5,  'Hoàng Văn Shop',     'Số 45 Phan Đăng Lưu, Quận Phú Nhuận, TP. HCM', '0901111115', '111111115', 'seller3', '123456', 3, 'active'),
(6,  'Nguyễn Minh Khách',  '88 Võ Văn Ngân, TP. Thủ Đức, TP. HCM',  '0901111116', '111111116', 'khach1',  '123456', 4, 'active'),
(7,  'Trịnh Quỳnh Anh',    '220/15 Nguyễn Trãi, Quận 5, TP. HCM',    '0901111117', '111111117', 'khach2',  '123456', 4, 'active'),
(8,  'Đặng Tuấn Kiệt',     'Số 5 Tôn Đức Thắng, Quận 1, TP. HCM',    '0901111118', '111111118', 'khach3',  '123456', 4, 'active'),
(9,  'Vũ Ngọc Hà',         '15 Ngõ 34 Xuân La, Tây Hồ, Hà Nội',      '0901111119', '111111119', 'khach4',  '123456', 4, 'active'),
(10, 'Lâm Hồng Nhung',     '9B Mai Thị Lựu, Quận 1, TP. HCM',        '0901111120', '111111120', 'khach5',  '123456', 4, 'banned');

-- ═══════════ GIAN HÀNG ═══════════
INSERT INTO Stores (StoreId, StoreName, Address, UserId, Phone, Category, Description, IsActive, CreatedAt) VALUES
(1, 'Shop Điện Tử Anh Minh',  'TP. Hồ Chí Minh', 3, '0902222001', 'Điện thoại', 'Chuyên điện thoại, laptop chính hãng', 1, '2026-09-01 09:00:00'),
(2, 'Shop Thời Trang Xinh',   'TP. Hồ Chí Minh', 4, '0902222002', 'Thời trang', 'Quần áo, giày dép, phụ kiện thời trang', 1, '2026-09-01 09:00:00'),
(3, 'Shop Gia Dụng Gia Đình', 'TP. Hồ Chí Minh', 5, '0902222003', 'Gia dụng',   'Đồ gia dụng, sách và quà tặng',         1, '2026-09-01 09:00:00');

-- ═══════════ DANH MỤC ═══════════
INSERT INTO Categories (CategoryId, CategoryName) VALUES
(1, 'Điện thoại'),
(2, 'Laptop'),
(3, 'Thời trang'),
(4, 'Gia dụng'),
(5, 'Sách'),
(6, 'Đồng hồ');

-- ═══════════ SẢN PHẨM ═══════════
INSERT INTO Products (ProductId, ProductName, Quantity, Price, CategoryId, StoreId, Description, OldPrice, ImageUrl, SoldCount, Emoji, IsActive) VALUES
(1,  'iPhone 15 Pro Max',     10,  32000000.00, 1, 1, 'Hàng chính hãng VN/A, bảo hành 12 tháng', 35000000.00, NULL, 120,  '📱', 1),
(2,  'Samsung Galaxy S25',    15,  25000000.00, 1, 1, 'Mới nhất 2026, tích hợp AI thông minh',    28000000.00, NULL, 85,   '📦', 1),
(3,  'MacBook Air M3',        8,   31000000.00, 2, 1, 'Chip M3 siêu mạnh mẽ, pin trâu 18 tiếng',  34000000.00, NULL, 42,   '📦', 1),
(4,  'Áo Hoodie Local Brand', 50,  450000.00,   3, 2, 'Chất liệu cotton 100% thoáng mát, form rộng', 650000.00, NULL, 320, '🧥', 1),
(5,  'Giày Sneaker Nike',     30,  2200000.00,  3, 2, 'Giày thể thao nam nữ, êm chân, bền bỉ',    2800000.00,  NULL, 98,   '📦', 1),
(6,  'Balo Du Lịch',          40,  890000.00,   3, 2, 'Chống nước nhẹ, nhiều ngăn tiện dụng',      1200000.00,  NULL, 115,  '🎒', 1),
(7,  'Nồi chiên không dầu',   12,  2500000.00,  4, 3, 'Dung tích 5L, công nghệ Rapid Air',         3200000.00,  NULL, 64,   '📦', 1),
(8,  'Máy xay sinh tố',       20,  1150000.00,  4, 3, 'Cối thủy tinh 1.5L, 6 lưỡi dao',            1500000.00,  NULL, 130,  '🥤', 1),
(9,  'Sách Lập trình Python', 100, 120000.00,   5, 3, 'Giáo trình thực hành từ con số 0',          180000.00,   NULL, 890,  '📦', 1),
(10, 'Đồng hồ Casio',         22,  1800000.00,  6, 3, 'Chống nước 50m, tuổi thọ pin 10 năm',       2200000.00,  NULL, 53,   '⌚', 1);

-- ═══════════ GIỎ HÀNG ═══════════
INSERT INTO Carts (CartId, UserId, TotalAmount, CreatedAt) VALUES
(1, 6, 900000.00,  '2026-09-05 10:00:00'),
(2, 8, 240000.00,  '2026-09-06 11:30:00'),
(3, 9, 2200000.00, '2026-09-07 14:00:00');

INSERT INTO CartItems (CartId, ProductId, Quantity, UnitPrice) VALUES
(1, 1, 1, 450000.00),
(1, 4, 1, 450000.00),
(2, 9, 2, 120000.00),
(3, 5, 1, 2200000.00);

-- ═══════════ ĐƠN ĐĂNG KÝ BÁN HÀNG ═══════════
INSERT INTO SellerRequests (RequestId, UserId, ShopName, BusinessPhone, Category, Status, CreatedAt, ReviewedAt, ReviewedBy, RejectReason, Description, NationalId) VALUES
(1, 8,  'Shop Trái Cây Sạch', '0912345001', 'Thực phẩm', 'pending', '2026-09-10 09:00:00', NULL, NULL, NULL, 'Nhập trái cây sạch về bán sỉ và lẻ', '123124125'),
(2, 9,  'Xưởng Gỗ Mộc',       '0912345002', 'Nội thất',  'pending', '2026-09-11 09:00:00', NULL, NULL, NULL, 'Bàn ghế gỗ công nghiệp',             '1412412');

-- ═══════════ ĐƠN HÀNG ═══════════
INSERT INTO Orders (OrderId, Status, ShippingFee, CartId, UserId, ReceiverName, ReceiverPhone, ShippingAddress, PaymentMethod, VoucherCode, SubTotal, DiscountAmount, TotalAmount, Note, CreatedAt, UpdatedAt) VALUES
(1, 'Completed', 25000.00, NULL, 6, 'Nguyễn Minh Khách', '0901111116', '88 Võ Văn Ngân, TP. Thủ Đức, TP. HCM', 'COD',  NULL, 32900000.00, 0.00, 32925000.00, NULL, '2026-09-08 09:15:00', '2026-09-10 17:00:00'),
(2, 'Shipping',  25000.00, NULL, 7, 'Trịnh Quỳnh Anh',   '0901111117', '220/15 Nguyễn Trãi, Quận 5, TP. HCM',    'MOMO', NULL, 3650000.00,  0.00, 3675000.00,  NULL, '2026-09-12 10:00:00', NULL),
(3, 'Pending',   25000.00, NULL, 8, 'Đặng Tuấn Kiệt',    '0901111118', 'Số 5 Tôn Đức Thắng, Quận 1, TP. HCM',    'BANK', NULL, 31000000.00, 0.00, 31025000.00, NULL, '2026-09-15 15:30:00', NULL),
(4, 'Cancelled', 25000.00, NULL, 9, 'Vũ Ngọc Hà',        '0901111119', '15 Ngõ 34 Xuân La, Tây Hồ, Hà Nội',     'COD',  NULL, 1800000.00,  0.00, 1825000.00,  NULL, '2026-09-09 08:00:00', '2026-09-09 08:20:00');

INSERT INTO OrderItems (OrderItemId, OrderId, ProductId, ProductName, Emoji, Quantity, UnitPrice, TotalPrice) VALUES
(1, 1,  1, 'iPhone 15 Pro Max',     '📱', 1, 32000000.00, 32000000.00),
(2, 1,  4, 'Áo Hoodie Local Brand', '🧥', 2, 450000.00,   900000.00),
(3, 2,  7, 'Nồi chiên không dầu',   '📦', 1, 2500000.00,  2500000.00),
(4, 2,  8, 'Máy xay sinh tố',       '🥤', 1, 1150000.00,  1150000.00),
(5, 3,  3, 'MacBook Air M3',        '📦', 1, 31000000.00, 31000000.00),
(6, 4, 10, 'Đồng hồ Casio',         '⌚', 1, 1800000.00,  1800000.00);