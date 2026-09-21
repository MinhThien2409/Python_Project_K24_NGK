-- schema_mysql.sql
-- Chỉ tạo cấu trúc database PobbyDB (không kèm dữ liệu).
-- Dữ liệu demo nằm riêng ở Database/seed_demo_mysql.sql.
--
-- Cách dùng:
--     mysql -u root -p < Database/schema_mysql.sql
--     mysql -u root -p < Database/seed_demo_mysql.sql
-- Lưu ý: chạy lại sẽ DROP và tạo mới toàn bộ database PobbyDB.

DROP DATABASE IF EXISTS PobbyDB;
CREATE DATABASE PobbyDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE PobbyDB;

CREATE TABLE Roles (
    RoleId   INT AUTO_INCREMENT PRIMARY KEY,
    RoleName VARCHAR(100) NOT NULL
);

CREATE TABLE Users (
    UserId     INT AUTO_INCREMENT PRIMARY KEY,
    FullName   VARCHAR(100) NOT NULL,
    Address    VARCHAR(255) NULL,
    Phone      VARCHAR(20)  NULL,
    NationalId VARCHAR(20)  NULL
);

-- ═══════════ TÀI KHOẢN (tách ra khỏi Users) ═══════════
CREATE TABLE Accounts (
    AccountId   INT AUTO_INCREMENT PRIMARY KEY,
    UserId      INT NOT NULL UNIQUE,
    Username    VARCHAR(50)  NOT NULL UNIQUE,
    Password    VARCHAR(255) NOT NULL,
    Role_Id     INT          NULL,
    trang_thai  VARCHAR(10)  NULL DEFAULT 'active',
    CONSTRAINT FK_Accounts_Users      FOREIGN KEY (UserId) REFERENCES Users (UserId),
    CONSTRAINT FK_Accounts_Roles       FOREIGN KEY (Role_Id) REFERENCES Roles (RoleId),
    CONSTRAINT CK_Accounts_Admin_KhongDuocKhoa  CHECK (NOT (trang_thai = 'banned' AND Role_Id = 1))
);

CREATE TABLE Stores (
    StoreId     INT AUTO_INCREMENT PRIMARY KEY,
    StoreName   VARCHAR(150) NOT NULL,
    Address     VARCHAR(255) NULL,
    UserId      INT          NOT NULL,
    Phone       VARCHAR(20)  NULL,
    Category    VARCHAR(50)  NULL,
    Description VARCHAR(500) NULL,
    IsActive    TINYINT(1)   NOT NULL DEFAULT 1,
    CreatedAt   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_Stores_UserId FOREIGN KEY (UserId) REFERENCES Users (UserId)
);

CREATE TABLE Categories (
    CategoryId   INT AUTO_INCREMENT PRIMARY KEY,
    CategoryName VARCHAR(100) NOT NULL
);

CREATE TABLE Products (
    ProductId   INT AUTO_INCREMENT PRIMARY KEY,
    ProductName VARCHAR(200) NOT NULL,
    Quantity    INT          NULL DEFAULT 0,
    Price       DECIMAL(18, 2) NOT NULL,
    CategoryId  INT          NOT NULL,
    StoreId     INT          NOT NULL,
    Description VARCHAR(1000) NULL,
    OldPrice    DECIMAL(18, 2) NULL,
    ImageUrl    VARCHAR(500) NULL,
    SoldCount   INT          NULL DEFAULT 0,
    Emoji       VARCHAR(10)   NULL,
    IsActive    TINYINT(1)   NULL DEFAULT 1,
    CONSTRAINT FK_Products_Categories FOREIGN KEY (CategoryId) REFERENCES Categories (CategoryId),
    CONSTRAINT FK_Products_Stores     FOREIGN KEY (StoreId)    REFERENCES Stores (StoreId)
);

CREATE TABLE Carts (
    CartId      INT AUTO_INCREMENT PRIMARY KEY,
    UserId      INT NOT NULL,
    TotalAmount DECIMAL(18, 2) NULL DEFAULT 0,
    CreatedAt   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_Carts_UserId FOREIGN KEY (UserId) REFERENCES Users (UserId)
);

CREATE TABLE CartItems (
    CartId    INT NOT NULL,
    ProductId INT NOT NULL,
    Quantity  INT NOT NULL DEFAULT 1,
    UnitPrice DECIMAL(18, 2) NOT NULL DEFAULT 0,
    PRIMARY KEY (CartId, ProductId),
    CONSTRAINT FK_CartItems_Cart     FOREIGN KEY (CartId)    REFERENCES Carts    (CartId),
    CONSTRAINT FK_CartItems_Product  FOREIGN KEY (ProductId) REFERENCES Products (ProductId)
);

CREATE TABLE SellerRequests (
    RequestId     INT AUTO_INCREMENT PRIMARY KEY,
    UserId        INT NOT NULL,
    ShopName      VARCHAR(255) NOT NULL,
    BusinessPhone VARCHAR(20)  NOT NULL,
    Category      VARCHAR(50)  NOT NULL,
    Status        VARCHAR(50)  NULL DEFAULT 'pending',
    CreatedAt     DATETIME     NULL DEFAULT CURRENT_TIMESTAMP,
    ReviewedAt    DATETIME     NULL,
    ReviewedBy    INT          NULL,
    RejectReason  VARCHAR(500) NULL,
    Description   VARCHAR(500) NULL,
    NationalId    VARCHAR(20)  NULL,
    CONSTRAINT FK_SellerRequests_UserId FOREIGN KEY (UserId) REFERENCES Users (UserId)
);

CREATE TABLE Orders (
    OrderId         INT AUTO_INCREMENT PRIMARY KEY,
    Status          VARCHAR(50) NULL DEFAULT 'Pending',
    ShippingFee     DECIMAL(18, 2) NULL DEFAULT 0,
    CartId          INT NULL,
    UserId          INT NOT NULL DEFAULT 0,
    ReceiverName    VARCHAR(150) NOT NULL DEFAULT '',
    ReceiverPhone   VARCHAR(20)  NOT NULL DEFAULT '',
    ShippingAddress VARCHAR(500) NOT NULL DEFAULT '',
    PaymentMethod   VARCHAR(20)  NOT NULL DEFAULT 'COD',
    VoucherCode     VARCHAR(50)  NULL,
    SubTotal        DECIMAL(18, 2) NOT NULL DEFAULT 0,
    DiscountAmount  DECIMAL(18, 2) NOT NULL DEFAULT 0,
    TotalAmount     DECIMAL(18, 2) NOT NULL DEFAULT 0,
    Note            VARCHAR(500) NULL,
    CreatedAt       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt       DATETIME NULL,
    CONSTRAINT FK_Orders_Cart  FOREIGN KEY (CartId)  REFERENCES Carts (CartId),
    CONSTRAINT FK_Orders_User  FOREIGN KEY (UserId)  REFERENCES Users (UserId)
);

CREATE TABLE OrderItems (
    OrderItemId INT AUTO_INCREMENT PRIMARY KEY,
    OrderId     INT NOT NULL,
    ProductId   INT NOT NULL,
    ProductName VARCHAR(255) NOT NULL DEFAULT '',
    Emoji       VARCHAR(10)  NULL,
    Quantity    INT NOT NULL DEFAULT 1,
    UnitPrice   DECIMAL(18, 2) NOT NULL DEFAULT 0,
    TotalPrice  DECIMAL(18, 2) NOT NULL DEFAULT 0,
    CONSTRAINT FK_OrderItems_Order   FOREIGN KEY (OrderId)   REFERENCES Orders   (OrderId),
    CONSTRAINT FK_OrderItems_Product FOREIGN KEY (ProductId) REFERENCES Products (ProductId)
);