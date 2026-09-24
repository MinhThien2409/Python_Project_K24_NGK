-- LEGACY 006-remove-reviews (2026-09-18): file SQL Server cu, KHONG dong bo bat buoc voi schema MySQL moi; nguon su that la Database/schema_mysql.sql + seed_demo_mysql.sql + Database/sql/006_remove_rating.sql; KHONG dung file nay de ghi de schema MySQL; cot [Rating] chi con gia tri lich su.
USE [master]
GO
/****** Object:  Database [PobbyDB]    Script Date: 6/15/2026 4:38:00 PM ******/
CREATE DATABASE [PobbyDB]
 CONTAINMENT = NONE
 ON  PRIMARY 
( NAME = N'PobbyDB', FILENAME = N'D:\SQL_Sever\MSSQL16.SQLEXPRESS\MSSQL\DATA\PobbyDB.mdf' , SIZE = 8192KB , MAXSIZE = UNLIMITED, FILEGROWTH = 65536KB )
 LOG ON 
( NAME = N'PobbyDB_log', FILENAME = N'D:\SQL_Sever\MSSQL16.SQLEXPRESS\MSSQL\DATA\PobbyDB_log.ldf' , SIZE = 8192KB , MAXSIZE = 2048GB , FILEGROWTH = 65536KB )
 WITH CATALOG_COLLATION = DATABASE_DEFAULT, LEDGER = OFF
GO
ALTER DATABASE [PobbyDB] SET COMPATIBILITY_LEVEL = 160
GO
IF (1 = FULLTEXTSERVICEPROPERTY('IsFullTextInstalled'))
begin
EXEC [PobbyDB].[dbo].[sp_fulltext_database] @action = 'enable'
end
GO
ALTER DATABASE [PobbyDB] SET ANSI_NULL_DEFAULT OFF 
GO
ALTER DATABASE [PobbyDB] SET ANSI_NULLS OFF 
GO
ALTER DATABASE [PobbyDB] SET ANSI_PADDING OFF 
GO
ALTER DATABASE [PobbyDB] SET ANSI_WARNINGS OFF 
GO
ALTER DATABASE [PobbyDB] SET ARITHABORT OFF 
GO
ALTER DATABASE [PobbyDB] SET AUTO_CLOSE ON 
GO
ALTER DATABASE [PobbyDB] SET AUTO_SHRINK OFF 
GO
ALTER DATABASE [PobbyDB] SET AUTO_UPDATE_STATISTICS ON 
GO
ALTER DATABASE [PobbyDB] SET CURSOR_CLOSE_ON_COMMIT OFF 
GO
ALTER DATABASE [PobbyDB] SET CURSOR_DEFAULT  GLOBAL 
GO
ALTER DATABASE [PobbyDB] SET CONCAT_NULL_YIELDS_NULL OFF 
GO
ALTER DATABASE [PobbyDB] SET NUMERIC_ROUNDABORT OFF 
GO
ALTER DATABASE [PobbyDB] SET QUOTED_IDENTIFIER OFF 
GO
ALTER DATABASE [PobbyDB] SET RECURSIVE_TRIGGERS OFF 
GO
ALTER DATABASE [PobbyDB] SET  ENABLE_BROKER 
GO
ALTER DATABASE [PobbyDB] SET AUTO_UPDATE_STATISTICS_ASYNC OFF 
GO
ALTER DATABASE [PobbyDB] SET DATE_CORRELATION_OPTIMIZATION OFF 
GO
ALTER DATABASE [PobbyDB] SET TRUSTWORTHY OFF 
GO
ALTER DATABASE [PobbyDB] SET ALLOW_SNAPSHOT_ISOLATION OFF 
GO
ALTER DATABASE [PobbyDB] SET PARAMETERIZATION SIMPLE 
GO
ALTER DATABASE [PobbyDB] SET READ_COMMITTED_SNAPSHOT OFF 
GO
ALTER DATABASE [PobbyDB] SET HONOR_BROKER_PRIORITY OFF 
GO
ALTER DATABASE [PobbyDB] SET RECOVERY SIMPLE 
GO
ALTER DATABASE [PobbyDB] SET  MULTI_USER 
GO
ALTER DATABASE [PobbyDB] SET PAGE_VERIFY CHECKSUM  
GO
ALTER DATABASE [PobbyDB] SET DB_CHAINING OFF 
GO
ALTER DATABASE [PobbyDB] SET FILESTREAM( NON_TRANSACTED_ACCESS = OFF ) 
GO
ALTER DATABASE [PobbyDB] SET TARGET_RECOVERY_TIME = 60 SECONDS 
GO
ALTER DATABASE [PobbyDB] SET DELAYED_DURABILITY = DISABLED 
GO
ALTER DATABASE [PobbyDB] SET ACCELERATED_DATABASE_RECOVERY = OFF  
GO
ALTER DATABASE [PobbyDB] SET QUERY_STORE = ON
GO
ALTER DATABASE [PobbyDB] SET QUERY_STORE (OPERATION_MODE = READ_WRITE, CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30), DATA_FLUSH_INTERVAL_SECONDS = 900, INTERVAL_LENGTH_MINUTES = 60, MAX_STORAGE_SIZE_MB = 1000, QUERY_CAPTURE_MODE = AUTO, SIZE_BASED_CLEANUP_MODE = AUTO, MAX_PLANS_PER_QUERY = 200, WAIT_STATS_CAPTURE_MODE = ON)
GO
USE [PobbyDB]
GO
/****** Object:  Table [dbo].[CartItems]    Script Date: 6/15/2026 4:38:00 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[CartItems](
	[CartId] [int] NOT NULL,
	[ProductId] [int] NOT NULL,
	[Quantity] [int] NOT NULL,
	[UnitPrice] [decimal](18, 2) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[CartId] ASC,
	[ProductId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Carts]    Script Date: 6/15/2026 4:38:01 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Carts](
	[CartId] [int] IDENTITY(1,1) NOT NULL,
	[UserId] [int] NOT NULL,
	[TotalAmount] [decimal](18, 2) NULL,
	[CreatedAt] [datetime] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[CartId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Categories]    Script Date: 6/15/2026 4:38:01 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Categories](
	[CategoryId] [int] IDENTITY(1,1) NOT NULL,
	[CategoryName] [nvarchar](100) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[CategoryId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[OrderItems]    Script Date: 6/15/2026 4:38:01 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[OrderItems](
	[OrderItemId] [int] IDENTITY(1,1) NOT NULL,
	[OrderId] [int] NOT NULL,
	[ProductId] [int] NOT NULL,
	[ProductName] [nvarchar](255) NOT NULL,
	[Emoji] [nvarchar](10) NULL,
	[Quantity] [int] NOT NULL,
	[UnitPrice] [decimal](18, 2) NOT NULL,
	[TotalPrice] [decimal](18, 2) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[OrderItemId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Orders]    Script Date: 6/15/2026 4:38:01 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Orders](
	[OrderId] [int] IDENTITY(1,1) NOT NULL,
	[Status] [nvarchar](50) NULL,
	[ShippingFee] [decimal](18, 2) NULL,
	[CartId] [int] NULL,
	[UserId] [int] NOT NULL,
	[ReceiverName] [nvarchar](150) NOT NULL,
	[ReceiverPhone] [varchar](20) NOT NULL,
	[ShippingAddress] [nvarchar](500) NOT NULL,
	[PaymentMethod] [varchar](20) NOT NULL,
	[VoucherCode] [nvarchar](50) NULL,
	[SubTotal] [decimal](18, 2) NOT NULL,
	[DiscountAmount] [decimal](18, 2) NOT NULL,
	[TotalAmount] [decimal](18, 2) NOT NULL,
	[Note] [nvarchar](500) NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NULL,
PRIMARY KEY CLUSTERED 
(
	[OrderId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Products]    Script Date: 6/15/2026 4:38:01 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Products](
	[ProductId] [int] IDENTITY(1,1) NOT NULL,
	[ProductName] [nvarchar](200) NOT NULL,
	[Quantity] [int] NULL,
	[Price] [decimal](18, 2) NOT NULL,
	[CategoryId] [int] NOT NULL,
	[StoreId] [int] NOT NULL,
	[Description] [nvarchar](1000) NULL,
	[OldPrice] [decimal](18, 2) NULL,
	[Rating] [decimal](3, 1) NULL,
	[SoldCount] [int] NULL,
	[Emoji] [nvarchar](10) NULL,
	[IsActive] [bit] NULL,
PRIMARY KEY CLUSTERED 
(
	[ProductId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Roles]    Script Date: 6/15/2026 4:38:01 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Roles](
	[RoleId] [int] IDENTITY(1,1) NOT NULL,
	[RoleName] [nvarchar](100) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[RoleId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[SellerRequests]    Script Date: 6/15/2026 4:38:01 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[SellerRequests](
	[RequestId] [int] IDENTITY(1,1) NOT NULL,
	[UserId] [int] NOT NULL,
	[ShopName] [nvarchar](255) NOT NULL,
	[BusinessPhone] [nvarchar](20) NOT NULL,
	[Category] [nvarchar](50) NOT NULL,
	[Status] [nvarchar](50) NULL,
	[CreatedAt] [datetime] NULL,
	[ReviewedAt] [datetime] NULL,
	[ReviewedBy] [int] NULL,
	[RejectReason] [nvarchar](500) NULL,
	[Description] [nvarchar](500) NULL,
	[NationalId] [nvarchar](20) NULL,
PRIMARY KEY CLUSTERED 
(
	[RequestId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Stores]    Script Date: 6/15/2026 4:38:01 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Stores](
	[StoreId] [int] IDENTITY(1,1) NOT NULL,
	[StoreName] [nvarchar](150) NOT NULL,
	[Address] [nvarchar](255) NULL,
	[UserId] [int] NOT NULL,
	[Phone] [varchar](20) NULL,
	[Category] [varchar](50) NULL,
	[Description] [nvarchar](500) NULL,
	[IsActive] [bit] NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[StoreId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Users]    Script Date: 6/15/2026 4:38:01 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Users](
	[UserId] [int] IDENTITY(1,1) NOT NULL,
	[FullName] [nvarchar](100) NOT NULL,
	[Address] [nvarchar](255) NULL,
	[Phone] [varchar](20) NULL,
	[NationalId] [varchar](20) NULL,
 CONSTRAINT [PK__Users__1788CC4C09072FA0] PRIMARY KEY CLUSTERED 
(
	[UserId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

-- ───── TÁI KHOÁN (tách ra khôi Users) ────────
CREATE TABLE [dbo].[Accounts](
	[AccountId] [int] IDENTITY(1,1) NOT NULL,
	[UserId] [int] NOT NULL,
	[Username] [nvarchar](50) NOT NULL,
	[Password] [varchar](255) NOT NULL,
	[Role_Id] [int] NULL,
	[trang_thai] [varchar](10) NULL,
 CONSTRAINT [PK__Accounts__3214BF380C6526F1] PRIMARY KEY CLUSTERED 
(
	[AccountId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
, CONSTRAINT [UQ__Accounts__3214BF380C6526F2] UNIQUE NONCLUSTERED 
(
	[UserId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
, CONSTRAINT [UQ__Accounts__3214BF380C6526F3] UNIQUE NONCLUSTERED 
(
	[Username] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
, CONSTRAINT [FK_Accounts_Users] FOREIGN KEY( [UserId]) REFERENCES [Users] ([UserId]) ON DELETE RESTRICT ON UPDATE RESTRICT
, CONSTRAINT [FK_Accounts_Roles] FOREIGN KEY( [Role_Id]) REFERENCES [Roles] ([RoleId]) ON DELETE RESTRICT ON UPDATE RESTRICT,
 CONSTRAINT [CK_Accounts_Admin_KhongDuocKhoa] CHECK (NOT (trang_thai = N'banned' AND Role_Id = 1))
) ON [PRIMARY]
GO
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (1, 1, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (1, 19, 1, CAST(180000.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (2, 4, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (3, 5, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (4, 6, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (5, 7, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (6, 8, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (7, 9, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (8, 10, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (9, 11, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (10, 12, 2, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (11, 13, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (12, 17, 1, CAST(18000000.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (12, 19, 1, CAST(180000.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (12, 20, 3, CAST(3200000.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (13, 17, 1, CAST(18000000.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (13, 18, 1, CAST(250000.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (14, 11, 1, CAST(2500000.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (14, 16, 1, CAST(2100000.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (15, 17, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (16, 18, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (17, 19, 2, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (18, 20, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (19, 2, 1, CAST(0.00 AS Decimal(18, 2)))
INSERT [dbo].[CartItems] ([CartId], [ProductId], [Quantity], [UnitPrice]) VALUES (20, 3, 1, CAST(0.00 AS Decimal(18, 2)))
GO
SET IDENTITY_INSERT [dbo].[Carts] ON 

INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (1, 1, CAST(180000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (2, 2, CAST(450000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (3, 3, CAST(2200000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (4, 4, CAST(890000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (5, 5, CAST(350000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (6, 6, CAST(1500000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (7, 7, CAST(1200000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (8, 8, CAST(120000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (9, 9, CAST(2500000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (10, 10, CAST(15000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (11, 11, CAST(350000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (12, 12, CAST(27780000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (13, 13, CAST(18250000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (14, 14, CAST(4600000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (15, 15, CAST(18000000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (16, 16, CAST(250000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (17, 17, CAST(180000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (18, 18, CAST(3200000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (19, 19, CAST(25000000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (20, 20, CAST(31000000.00 AS Decimal(18, 2)), CAST(N'2026-06-07T19:51:38.473' AS DateTime))
INSERT [dbo].[Carts] ([CartId], [UserId], [TotalAmount], [CreatedAt]) VALUES (21, 26, CAST(0.00 AS Decimal(18, 2)), CAST(N'2026-06-15T16:00:26.690' AS DateTime))
SET IDENTITY_INSERT [dbo].[Carts] OFF
GO
SET IDENTITY_INSERT [dbo].[Categories] ON 

INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (1, N'Điện thoại')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (2, N'Laptop')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (3, N'Thời trang')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (4, N'Giày dép')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (5, N'Phụ kiện')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (6, N'Mỹ phẩm')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (7, N'Sách')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (8, N'Gia dụng')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (9, N'Thực phẩm')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (10, N'Thể thao')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (11, N'Đồng hồ')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (12, N'Túi xách')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (13, N'Gaming')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (14, N'Tai nghe')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (15, N'Chuột máy tính')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (16, N'Bàn phím')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (17, N'Máy ảnh')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (18, N'Đồ chơi')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (19, N'Thú cưng')
INSERT [dbo].[Categories] ([CategoryId], [CategoryName]) VALUES (20, N'Nội thất')
SET IDENTITY_INSERT [dbo].[Categories] OFF
GO
SET IDENTITY_INSERT [dbo].[OrderItems] ON 

INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (4, 25, 14, N'Sản phẩm', N'📦', 2, CAST(1800000.00 AS Decimal(18, 2)), CAST(3600000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (5, 25, 17, N'Sản phẩm', N'📦', 1, CAST(18000000.00 AS Decimal(18, 2)), CAST(18000000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (6, 25, 19, N'Sản phẩm', N'📦', 3, CAST(180000.00 AS Decimal(18, 2)), CAST(540000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (7, 25, 20, N'Sản phẩm', N'📦', 3, CAST(3200000.00 AS Decimal(18, 2)), CAST(9600000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (8, 27, 12, N'Sản phẩm #12', N'📦', 1, CAST(15000.00 AS Decimal(18, 2)), CAST(15000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (9, 27, 13, N'Sản phẩm #13', N'📦', 1, CAST(350000.00 AS Decimal(18, 2)), CAST(350000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (10, 27, 14, N'Sản phẩm #14', N'📦', 1, CAST(1800000.00 AS Decimal(18, 2)), CAST(1800000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (11, 27, 16, N'Sản phẩm #16', N'📦', 1, CAST(2100000.00 AS Decimal(18, 2)), CAST(2100000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (12, 27, 20, N'Sản phẩm #20', N'📦', 1, CAST(3200000.00 AS Decimal(18, 2)), CAST(3200000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (13, 28, 15, N'Sản phẩm #15', N'📦', 1, CAST(950000.00 AS Decimal(18, 2)), CAST(950000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (14, 28, 16, N'Sản phẩm #16', N'📦', 1, CAST(2100000.00 AS Decimal(18, 2)), CAST(2100000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (15, 28, 17, N'Sản phẩm #17', N'📦', 1, CAST(18000000.00 AS Decimal(18, 2)), CAST(18000000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (16, 28, 18, N'Sản phẩm #18', N'📦', 1, CAST(250000.00 AS Decimal(18, 2)), CAST(250000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (17, 28, 20, N'Sản phẩm #20', N'📦', 1, CAST(3200000.00 AS Decimal(18, 2)), CAST(3200000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (18, 29, 15, N'Sản phẩm #15', N'📦', 1, CAST(950000.00 AS Decimal(18, 2)), CAST(950000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (19, 29, 16, N'Sản phẩm #16', N'📦', 2, CAST(2100000.00 AS Decimal(18, 2)), CAST(4200000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (20, 29, 17, N'Sản phẩm #17', N'📦', 1, CAST(18000000.00 AS Decimal(18, 2)), CAST(18000000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (21, 29, 18, N'Sản phẩm #18', N'📦', 1, CAST(250000.00 AS Decimal(18, 2)), CAST(250000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (22, 29, 20, N'Sản phẩm #20', N'📦', 1, CAST(3200000.00 AS Decimal(18, 2)), CAST(3200000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (23, 30, 17, N'Sản phẩm #17', N'📦', 1, CAST(18000000.00 AS Decimal(18, 2)), CAST(18000000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (24, 30, 20, N'Sản phẩm #20', N'📦', 3, CAST(3200000.00 AS Decimal(18, 2)), CAST(9600000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (25, 31, 17, N'Sản phẩm #17', N'📦', 1, CAST(18000000.00 AS Decimal(18, 2)), CAST(18000000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (26, 31, 18, N'Sản phẩm #18', N'📦', 1, CAST(250000.00 AS Decimal(18, 2)), CAST(250000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (27, 32, 11, N'Nồi chiên không dầu', N'📦', 1, CAST(2500000.00 AS Decimal(18, 2)), CAST(2500000.00 AS Decimal(18, 2)))
INSERT [dbo].[OrderItems] ([OrderItemId], [OrderId], [ProductId], [ProductName], [Emoji], [Quantity], [UnitPrice], [TotalPrice]) VALUES (28, 32, 16, N'PS5 Controller', N'📦', 1, CAST(2100000.00 AS Decimal(18, 2)), CAST(2100000.00 AS Decimal(18, 2)))
SET IDENTITY_INSERT [dbo].[OrderItems] OFF
GO
SET IDENTITY_INSERT [dbo].[Orders] ON 

INSERT [dbo].[Orders] ([OrderId], [Status], [ShippingFee], [CartId], [UserId], [ReceiverName], [ReceiverPhone], [ShippingAddress], [PaymentMethod], [VoucherCode], [SubTotal], [DiscountAmount], [TotalAmount], [Note], [CreatedAt], [UpdatedAt]) VALUES (25, N'Pending', CAST(40000.00 AS Decimal(18, 2)), NULL, 12, N'Trần Khánh Vy', N'0901111122', N'Tây Ninh', N'COD', NULL, CAST(28140000.00 AS Decimal(18, 2)), CAST(0.00 AS Decimal(18, 2)), CAST(28180000.00 AS Decimal(18, 2)), NULL, CAST(N'2026-06-07T20:36:30.863' AS DateTime), NULL)
INSERT [dbo].[Orders] ([OrderId], [Status], [ShippingFee], [CartId], [UserId], [ReceiverName], [ReceiverPhone], [ShippingAddress], [PaymentMethod], [VoucherCode], [SubTotal], [DiscountAmount], [TotalAmount], [Note], [CreatedAt], [UpdatedAt]) VALUES (27, N'Pending', CAST(25000.00 AS Decimal(18, 2)), NULL, 14, N'Phan Quốc Khánh', N'0901111124', N'120 An Dương Vương', N'MOMO', NULL, CAST(5365000.00 AS Decimal(18, 2)), CAST(0.00 AS Decimal(18, 2)), CAST(5390000.00 AS Decimal(18, 2)), NULL, CAST(N'2026-06-07T20:57:51.443' AS DateTime), NULL)
INSERT [dbo].[Orders] ([OrderId], [Status], [ShippingFee], [CartId], [UserId], [ReceiverName], [ReceiverPhone], [ShippingAddress], [PaymentMethod], [VoucherCode], [SubTotal], [DiscountAmount], [TotalAmount], [Note], [CreatedAt], [UpdatedAt]) VALUES (28, N'Cancelled', CAST(25000.00 AS Decimal(18, 2)), NULL, 13, N'Lý Hải Nam', N'0901111123', N'Đồng Nai', N'MOMO', NULL, CAST(23550000.00 AS Decimal(18, 2)), CAST(0.00 AS Decimal(18, 2)), CAST(23575000.00 AS Decimal(18, 2)), NULL, CAST(N'2026-06-07T21:01:31.260' AS DateTime), CAST(N'2026-06-07T21:01:38.230' AS DateTime))
INSERT [dbo].[Orders] ([OrderId], [Status], [ShippingFee], [CartId], [UserId], [ReceiverName], [ReceiverPhone], [ShippingAddress], [PaymentMethod], [VoucherCode], [SubTotal], [DiscountAmount], [TotalAmount], [Note], [CreatedAt], [UpdatedAt]) VALUES (29, N'Pending', CAST(25000.00 AS Decimal(18, 2)), NULL, 13, N'Lý Hải Nam', N'0901111123', N'290 An Dương Vương', N'MOMO', NULL, CAST(25650000.00 AS Decimal(18, 2)), CAST(0.00 AS Decimal(18, 2)), CAST(25675000.00 AS Decimal(18, 2)), NULL, CAST(N'2026-06-07T21:02:47.840' AS DateTime), NULL)
INSERT [dbo].[Orders] ([OrderId], [Status], [ShippingFee], [CartId], [UserId], [ReceiverName], [ReceiverPhone], [ShippingAddress], [PaymentMethod], [VoucherCode], [SubTotal], [DiscountAmount], [TotalAmount], [Note], [CreatedAt], [UpdatedAt]) VALUES (30, N'Pending', CAST(25000.00 AS Decimal(18, 2)), NULL, 12, N'Trần Khánh Vy', N'0901111122', N'Tây Ninh', N'COD', NULL, CAST(27600000.00 AS Decimal(18, 2)), CAST(0.00 AS Decimal(18, 2)), CAST(27625000.00 AS Decimal(18, 2)), NULL, CAST(N'2026-06-14T09:00:11.507' AS DateTime), NULL)
INSERT [dbo].[Orders] ([OrderId], [Status], [ShippingFee], [CartId], [UserId], [ReceiverName], [ReceiverPhone], [ShippingAddress], [PaymentMethod], [VoucherCode], [SubTotal], [DiscountAmount], [TotalAmount], [Note], [CreatedAt], [UpdatedAt]) VALUES (31, N'Confirmed', CAST(25000.00 AS Decimal(18, 2)), NULL, 13, N'Lý Hải Nam', N'0901111123', N'Số 45 Phan Đăng Lưu, Phường 7, Quận Phú Nhuận, TP. Hồ Chí Minh', N'BANK', NULL, CAST(18250000.00 AS Decimal(18, 2)), CAST(0.00 AS Decimal(18, 2)), CAST(18275000.00 AS Decimal(18, 2)), NULL, CAST(N'2026-06-15T15:51:02.247' AS DateTime), CAST(N'2026-06-15T15:56:55.747' AS DateTime))
INSERT [dbo].[Orders] ([OrderId], [Status], [ShippingFee], [CartId], [UserId], [ReceiverName], [ReceiverPhone], [ShippingAddress], [PaymentMethod], [VoucherCode], [SubTotal], [DiscountAmount], [TotalAmount], [Note], [CreatedAt], [UpdatedAt]) VALUES (32, N'Pending', CAST(25000.00 AS Decimal(18, 2)), NULL, 14, N'Phan Quốc Khánh', N'0901111124', N'88 Võ Văn Ngân, Phường Bình Thọ, TP. Thủ Đức, TP. Hồ Chí Minh', N'MOMO', NULL, CAST(4600000.00 AS Decimal(18, 2)), CAST(0.00 AS Decimal(18, 2)), CAST(4625000.00 AS Decimal(18, 2)), NULL, CAST(N'2026-06-15T16:30:28.390' AS DateTime), NULL)
SET IDENTITY_INSERT [dbo].[Orders] OFF
GO
SET IDENTITY_INSERT [dbo].[Products] ON 

INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (1, N'iPhone 15 Pro Max', 10, CAST(32000000.00 AS Decimal(18, 2)), 1, 1, N'Hàng chính hãng VN/A, bảo hành 12 tháng', CAST(35000000.00 AS Decimal(18, 2)), CAST(4.9 AS Decimal(3, 1)), 1500, N'📱', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (2, N'Samsung Galaxy S25', 15, CAST(25000000.00 AS Decimal(18, 2)), 1, 2, N'Mới nhất 2026, tích hợp AI thông minh', CAST(28000000.00 AS Decimal(18, 2)), CAST(4.8 AS Decimal(3, 1)), 850, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (3, N'MacBook Air M3', 8, CAST(31000000.00 AS Decimal(18, 2)), 2, 5, N'Chip M3 siêu mạnh mẽ, pin trâu 18 tiếng', CAST(34000000.00 AS Decimal(18, 2)), CAST(5.0 AS Decimal(3, 1)), 420, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (4, N'Áo Hoodie Local Brand', 50, CAST(450000.00 AS Decimal(18, 2)), 3, 1, N'Chất liệu cotton 100% thoáng mát, form rộng', CAST(650000.00 AS Decimal(18, 2)), CAST(4.3 AS Decimal(3, 1)), 3200, N'🧥', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (5, N'Giày Sneaker Nike', 30, CAST(2200000.00 AS Decimal(18, 2)), 4, 3, N'Giày thể thao nam nữ, êm chân, bền bỉ', CAST(2800000.00 AS Decimal(18, 2)), CAST(4.7 AS Decimal(3, 1)), 980, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (6, N'Tai nghe Bluetooth', 40, CAST(890000.00 AS Decimal(18, 2)), 14, 6, N'Chống ồn chủ động ANC, pin 30h', CAST(1200000.00 AS Decimal(18, 2)), CAST(4.6 AS Decimal(3, 1)), 1150, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (7, N'Chuột Logitech G102', 60, CAST(350000.00 AS Decimal(18, 2)), 15, 6, N'Chuột gaming quốc dân, LED RGB', CAST(450000.00 AS Decimal(18, 2)), CAST(4.8 AS Decimal(3, 1)), 4500, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (8, N'Bàn phím cơ AKKO', 25, CAST(1500000.00 AS Decimal(18, 2)), 16, 6, N'Switch gõ êm, keycap PBT siêu bền', CAST(1900000.00 AS Decimal(18, 2)), CAST(4.9 AS Decimal(3, 1)), 670, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (9, N'Son môi Dior', 20, CAST(1200000.00 AS Decimal(18, 2)), 6, 7, N'Màu đỏ rượu quyến rũ, lì và mịn môi', CAST(1450000.00 AS Decimal(18, 2)), CAST(4.5 AS Decimal(3, 1)), 2100, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (10, N'Sách Python cơ bản', 100, CAST(120000.00 AS Decimal(18, 2)), 7, 8, N'Giáo trình thực hành lập trình từ con số 0', CAST(180000.00 AS Decimal(18, 2)), CAST(4.4 AS Decimal(3, 1)), 890, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (11, N'Nồi chiên không dầu', 12, CAST(2500000.00 AS Decimal(18, 2)), 8, 10, N'Dung tích 5L, công nghệ Rapid Air', CAST(3200000.00 AS Decimal(18, 2)), CAST(4.7 AS Decimal(3, 1)), 640, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (12, N'Bánh snack', 200, CAST(15000.00 AS Decimal(18, 2)), 9, 18, N'Vị phô mai béo ngậy, giòn rụm', CAST(25000.00 AS Decimal(18, 2)), CAST(4.1 AS Decimal(3, 1)), 8500, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (13, N'Áo bóng đá', 35, CAST(350000.00 AS Decimal(18, 2)), 10, 17, N'Vải thun lạnh, thấm hút mồ hôi tốt', CAST(500000.00 AS Decimal(18, 2)), CAST(4.5 AS Decimal(3, 1)), 1200, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (14, N'Đồng hồ Casio', 22, CAST(1800000.00 AS Decimal(18, 2)), 11, 20, N'Chống nước 50m, tuổi thọ pin 10 năm', CAST(2200000.00 AS Decimal(18, 2)), CAST(4.8 AS Decimal(3, 1)), 530, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (15, N'Túi xách nữ', 18, CAST(950000.00 AS Decimal(18, 2)), 12, 19, N'Da PU cao cấp, kiểu dáng Hàn Quốc', CAST(1250000.00 AS Decimal(18, 2)), CAST(4.3 AS Decimal(3, 1)), 940, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (16, N'PS5 Controller', 14, CAST(2100000.00 AS Decimal(18, 2)), 13, 6, N'Tay cầm DualSense chính hãng Sony', CAST(2400000.00 AS Decimal(18, 2)), CAST(4.9 AS Decimal(3, 1)), 760, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (17, N'Camera Sony', 6, CAST(18000000.00 AS Decimal(18, 2)), 17, 2, N'Cảm biến Full-frame, quay phim 4K', CAST(22500000.00 AS Decimal(18, 2)), CAST(5.0 AS Decimal(3, 1)), 120, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (18, N'Gấu bông Teddy', 45, CAST(250000.00 AS Decimal(18, 2)), 18, 16, N'Lông mềm mịn, không rụng, cao 1m2', CAST(350000.00 AS Decimal(18, 2)), CAST(4.6 AS Decimal(3, 1)), 2300, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (19, N'Thức ăn cho chó', 55, CAST(180000.00 AS Decimal(18, 2)), 19, 15, N'Vị bò nướng thơm ngon, túi zip 2kg', CAST(220000.00 AS Decimal(18, 2)), CAST(4.7 AS Decimal(3, 1)), 1650, N'📦', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (20, N'Bàn học gỗ', 10, CAST(3200000.00 AS Decimal(18, 2)), 20, 1, N'Gỗ MDF chống ẩm, chân sắt sơn tĩnh điện', CAST(3800000.00 AS Decimal(18, 2)), CAST(4.2 AS Decimal(3, 1)), 310, N'🪑', 1)
INSERT [dbo].[Products] ([ProductId], [ProductName], [Quantity], [Price], [CategoryId], [StoreId], [Description], [OldPrice], [Rating], [SoldCount], [Emoji], [IsActive]) VALUES (21, N'Xiaomi Pro 123', 1229, CAST(10000000.00 AS Decimal(18, 2)), 1, 1, N'DT', CAST(12000000.00 AS Decimal(18, 2)), CAST(4.0 AS Decimal(3, 1)), 0, N'📱', 0)
SET IDENTITY_INSERT [dbo].[Products] OFF
GO
SET IDENTITY_INSERT [dbo].[Roles] ON 

INSERT [dbo].[Roles] ([RoleId], [RoleName]) VALUES (1, N'Admin')
INSERT [dbo].[Roles] ([RoleId], [RoleName]) VALUES (2, N'Quản lý')
INSERT [dbo].[Roles] ([RoleId], [RoleName]) VALUES (3, N'Seller')
INSERT [dbo].[Roles] ([RoleId], [RoleName]) VALUES (4, N'Customer')
SET IDENTITY_INSERT [dbo].[Roles] OFF
GO
SET IDENTITY_INSERT [dbo].[SellerRequests] ON 

INSERT [dbo].[SellerRequests] ([RequestId], [UserId], [ShopName], [BusinessPhone], [Category], [Status], [CreatedAt], [ReviewedAt], [ReviewedBy], [RejectReason], [Description], [NationalId]) VALUES (3, 12, N'FPT Shop', N'05123123', N'Điện thoại', N'pending', CAST(N'2026-06-14T09:16:08.757' AS DateTime), NULL, NULL, NULL, N'bán đt', N'123124125')
INSERT [dbo].[SellerRequests] ([RequestId], [UserId], [ShopName], [BusinessPhone], [Category], [Status], [CreatedAt], [ReviewedAt], [ReviewedBy], [RejectReason], [Description], [NationalId]) VALUES (4, 13, N'Shop đồ võ thuật Nam Lý', N'09055544433', N'Thể thao', N'pending', CAST(N'2026-06-14T09:17:12.133' AS DateTime), NULL, NULL, NULL, N'bán toàn bộ dụng cụ tập luyện võ thuật', N'1412412')
SET IDENTITY_INSERT [dbo].[SellerRequests] OFF
GO
SET IDENTITY_INSERT [dbo].[Stores] ON 

INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (1, N'Pobby Fashion', N'TP.HCM', 2, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (2, N'Tech World', N'Hà Nội', 4, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (3, N'Sneaker Hub', N'Đà Nẵng', 6, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (4, N'Phone Store', N'Cần Thơ', 8, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (5, N'Laptop City', N'Hải Phòng', 10, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (6, N'Gaming Gear', N'Biên Hòa', 12, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (7, N'Beauty Shop', N'Vũng Tàu', 14, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (8, N'Book Store', N'Huế', 16, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (9, N'Coffee House', N'Nha Trang', 18, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (10, N'Home Decor', N'Long An', 20, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (11, N'Fashion Mall', N'Bình Dương', 2, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (12, N'Apple Center', N'Tây Ninh', 4, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (13, N'Smart Tech', N'Đồng Nai', 6, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (14, N'Mini Mart', N'An Giang', 8, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (15, N'Pet Shop', N'Kiên Giang', 10, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (16, N'Toy World', N'Bến Tre', 12, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (17, N'Sports Store', N'Quảng Nam', 14, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (18, N'Fresh Food', N'Quảng Ngãi', 16, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (19, N'Luxury Shop', N'Đắk Lắk', 18, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (20, N'Watch Store', N'Phú Quốc', 20, NULL, NULL, NULL, 1, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (21, N'Bánh ABC', N'', 4, NULL, NULL, NULL, 0, CAST(N'2026-06-06T23:49:31.780' AS DateTime))
INSERT [dbo].[Stores] ([StoreId], [StoreName], [Address], [UserId], [Phone], [Category], [Description], [IsActive], [CreatedAt]) VALUES (22, N'Apple Store China', NULL, 4, N'123456', N'Ði?n tho?i', N'bán đt', 1, CAST(N'2026-06-07T21:05:05.400' AS DateTime))
SET IDENTITY_INSERT [dbo].[Stores] OFF
GO
SET IDENTITY_INSERT [dbo].[Users] ON
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (1, N'Nguyễn Văn An', N'120 An Liễng, Phường 12,Hà Nội', N'0901111111', N'111111111')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (2, N'Trần Thị Bình', N'Số 12 Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh', N'0901111112', N'111111112')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (3, N'Lê Minh Khoa', N'105 Trần Hưng Đạo, Phường Cầu Ông Lãnh, Quận 1, TP. Hồ Chí Minh', N'0901111113', N'1111111134')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (4, N'Phạm Hoàng Nam', N'220/15 Nguyễn Trãi, Phường 3, Quận 5, TP. Hồ Chí Minh', N'0901111114', N'111111114')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (5, N'Đỗ Thanh Tùng', N'18A Cộng Hòa, Phường 4, Quận Tân Bình, TP. Hồ Chí Minh', N'0901111115', N'111111115')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (6, N'Ngô Gia Huy', N'Số 45 Phan Đăng Lưu, Phường 7, Quận Phú Nhuận, TP. Hồ Chí Minh', N'0901111116', N'111111116')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (7, N'Võ Quốc Bảo', N'88 Võ Văn Ngân, Phường Bình Thọ, TP. Thủ Đức, TP. Hồ Chí Minh', N'0901111117', N'111111117')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (8, N'Bùi Nhật Minh', N'Số 5 Tôn Đức Thắng, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh', N'0901111118', N'111111118')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (9, N'Hoàng Ngọc Lan', N'Số 12 Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh', N'0901111119', N'111111119')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (10, N'Đặng Gia Linh', N'105 Trần Hưng Đạo, Phường Cầu Ông Lãnh, Quận 1, TP. Hồ Chí Minh', N'0901111120', N'111111120')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (11, N'Nguyễn Minh Châu', N'220/15 Nguyễn Trãi, Phường 3, Quận 5, TP. Hồ Chí Minh', N'0901111121', N'111111121')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (12, N'Trần Khánh Vy', N'18A Cộng Hòa, Phường 4, Quận Tân Bình, TP. Hồ Chí Minh', N'0901111122', N'111111122')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (13, N'Lý Hải Nam', N'Số 45 Phan Đăng Lưu, Phường 7, Quận Phú Nhuận, TP. Hồ Chí Minh', N'0901111123', N'111111123')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (14, N'Phan Quốc Khánh', N'88 Võ Văn Ngân, Phường Bình Thọ, TP. Thủ Đức, TP. Hồ Chí Minh', N'0901111124', N'111111124')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (15, N'Đinh Hoài Thương', N'Số 5 Tôn Đức Thắng, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh', N'0901111125', N'111111125')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (16, N'Nguyễn Đức Mạnh', N'123 Nguyễn Đình Chiểu, Phường 6, Quận 3, TP. Hồ Chí Minh', N'0901111126', N'111111126')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (17, N'Tạ Mỹ Tiên', N'9B Mai Thị Lựu, Phường Đa Kao, Quận 1, TP. Hồ Chí Minh', N'0901111127', N'111111127')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (18, N'Vũ Thành Đạt', N'Số 34 Lê Duẩn, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh', N'0901111128', N'111111128')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (19, N'Lâm Hoàng Phúc', N'Số 8 Tôn Thất Thuyết, Phường Mỹ Đình 2, Quận Nam Từ Liêm, Hà Nội', N'0901111129', N'111111129')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (20, N'Châu Ngọc Mai', N'15 Ngõ 34 Xuân La, Phường Xuân La, Quận Tây Hồ, Hà Nội', N'0901111130', N'111111130')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (23, N'Trần Văn A', N'56 Nguyễn Thái Học, Phường Điện Biên, Quận Ba Đình, Hà Nội', N'123', NULL)
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (24, N'Nguyễn Văn Tèo', N'102 Thái Hà, Phường Trung Liệt, Quận Đống Đa, Hà Nội', N'09051553', N'123456')
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (25, N'Nguyễn Trung Tín', NULL, N'09051553', NULL)
INSERT [dbo].[Users] ([UserId], [FullName], [Address], [Phone], [NationalId]) VALUES (26, N'Nguyễn Trung Tín', NULL, N'09051553', NULL)
SET IDENTITY_INSERT [dbo].[Users] OFF
-- 008 tach bang: tai khoan dang nhap gom o bang Accounts (UserId 1-1, khong cascade)
SET IDENTITY_INSERT [dbo].[Accounts] ON
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (1, N'user1', N'123456', 1, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (2, N'user2', N'123456', 3, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (3, N'user3', N'123456', 4, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (4, N'user4', N'123456', 3, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (5, N'user5', N'123456', 4, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (6, N'user6', N'123456', 3, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (7, N'user7', N'123456', 4, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (8, N'user8', N'123456', 3, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (9, N'user9', N'123456', 4, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (10, N'user10', N'123456', 3, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (11, N'user11', N'123456', 4, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (12, N'user12', N'123456', 3, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (13, N'user13', N'123456', 4, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (14, N'user14', N'123456', 3, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (15, N'user15', N'123456', 4, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (16, N'user16', N'123456', 3, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (17, N'user17', N'123456', 4, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (18, N'user18', N'123456', 3, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (19, N'user19', N'123456', 4, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (20, N'user20', N'123456', 3, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (23, N'a123', N'123456', 4, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (24, N'teo123', N'123456', 4, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (25, N'thaytin123', N'123456', 4, N'active')
INSERT [dbo].[Accounts] ([UserId], [Username], [Password], [Role_Id], [trang_thai]) VALUES (26, N'thaytin1234', N'123456', 4, N'banned')
SET IDENTITY_INSERT [dbo].[Accounts] OFF
GO
SET ANSI_PADDING ON
GO
ALTER TABLE [dbo].[CartItems] ADD  DEFAULT ((0)) FOR [UnitPrice]
GO
ALTER TABLE [dbo].[Carts] ADD  DEFAULT ((0)) FOR [TotalAmount]
GO
ALTER TABLE [dbo].[Carts] ADD  DEFAULT (getdate()) FOR [CreatedAt]
GO
ALTER TABLE [dbo].[OrderItems] ADD  DEFAULT ('') FOR [ProductName]
GO
ALTER TABLE [dbo].[OrderItems] ADD  DEFAULT ((1)) FOR [Quantity]
GO
ALTER TABLE [dbo].[OrderItems] ADD  DEFAULT ((0)) FOR [UnitPrice]
GO
ALTER TABLE [dbo].[OrderItems] ADD  DEFAULT ((0)) FOR [TotalPrice]
GO
ALTER TABLE [dbo].[Orders] ADD  DEFAULT (N'Pending') FOR [Status]
GO
ALTER TABLE [dbo].[Orders] ADD  DEFAULT ((0)) FOR [ShippingFee]
GO
ALTER TABLE [dbo].[Orders] ADD  DEFAULT ((0)) FOR [UserId]
GO
ALTER TABLE [dbo].[Orders] ADD  DEFAULT ('') FOR [ReceiverName]
GO
ALTER TABLE [dbo].[Orders] ADD  DEFAULT ('') FOR [ReceiverPhone]
GO
ALTER TABLE [dbo].[Orders] ADD  DEFAULT ('') FOR [ShippingAddress]
GO
ALTER TABLE [dbo].[Orders] ADD  DEFAULT ('COD') FOR [PaymentMethod]
GO
ALTER TABLE [dbo].[Orders] ADD  DEFAULT ((0)) FOR [SubTotal]
GO
ALTER TABLE [dbo].[Orders] ADD  DEFAULT ((0)) FOR [DiscountAmount]
GO
ALTER TABLE [dbo].[Orders] ADD  DEFAULT ((0)) FOR [TotalAmount]
GO
ALTER TABLE [dbo].[Orders] ADD  DEFAULT (getdate()) FOR [CreatedAt]
GO
ALTER TABLE [dbo].[Products] ADD  DEFAULT ((0)) FOR [Quantity]
GO
ALTER TABLE [dbo].[Products] ADD  DEFAULT ((0)) FOR [SoldCount]
GO
ALTER TABLE [dbo].[Products] ADD  DEFAULT ((1)) FOR [IsActive]
GO
ALTER TABLE [dbo].[SellerRequests] ADD  DEFAULT ('pending') FOR [Status]
GO
ALTER TABLE [dbo].[SellerRequests] ADD  DEFAULT (getdate()) FOR [CreatedAt]
GO
ALTER TABLE [dbo].[Stores] ADD  DEFAULT ((1)) FOR [IsActive]
GO
ALTER TABLE [dbo].[Stores] ADD  DEFAULT (getdate()) FOR [CreatedAt]
GO
ALTER TABLE [dbo].[Accounts] ADD  DEFAULT ('active') FOR [trang_thai]
GO
ALTER TABLE [dbo].[CartItems]  WITH CHECK ADD FOREIGN KEY([CartId])
REFERENCES [dbo].[Carts] ([CartId])
GO
ALTER TABLE [dbo].[CartItems]  WITH CHECK ADD FOREIGN KEY([ProductId])
REFERENCES [dbo].[Products] ([ProductId])
GO
ALTER TABLE [dbo].[Carts]  WITH CHECK ADD  CONSTRAINT [FK__Carts__UserId__44FF419A] FOREIGN KEY([UserId])
REFERENCES [dbo].[Users] ([UserId])
GO
ALTER TABLE [dbo].[Carts] CHECK CONSTRAINT [FK__Carts__UserId__44FF419A]
GO
ALTER TABLE [dbo].[OrderItems]  WITH CHECK ADD FOREIGN KEY([OrderId])
REFERENCES [dbo].[Orders] ([OrderId])
GO
ALTER TABLE [dbo].[OrderItems]  WITH CHECK ADD FOREIGN KEY([ProductId])
REFERENCES [dbo].[Products] ([ProductId])
GO
ALTER TABLE [dbo].[Orders]  WITH CHECK ADD FOREIGN KEY([CartId])
REFERENCES [dbo].[Carts] ([CartId])
GO
ALTER TABLE [dbo].[Products]  WITH CHECK ADD FOREIGN KEY([CategoryId])
REFERENCES [dbo].[Categories] ([CategoryId])
GO
ALTER TABLE [dbo].[Products]  WITH CHECK ADD FOREIGN KEY([StoreId])
REFERENCES [dbo].[Stores] ([StoreId])
GO
ALTER TABLE [dbo].[Products]  WITH CHECK ADD  CONSTRAINT [FK_Products_Categories] FOREIGN KEY([CategoryId])
REFERENCES [dbo].[Categories] ([CategoryId])
GO
ALTER TABLE [dbo].[Products] CHECK CONSTRAINT [FK_Products_Categories]
GO
ALTER TABLE [dbo].[Products]  WITH CHECK ADD  CONSTRAINT [FK_Products_Stores] FOREIGN KEY([StoreId])
REFERENCES [dbo].[Stores] ([StoreId])
GO
ALTER TABLE [dbo].[Products] CHECK CONSTRAINT [FK_Products_Stores]
GO
ALTER TABLE [dbo].[SellerRequests]  WITH CHECK ADD FOREIGN KEY([UserId])
REFERENCES [dbo].[Users] ([UserId])
GO
ALTER TABLE [dbo].[Stores]  WITH CHECK ADD  CONSTRAINT [FK__Stores__UserId__3A81B327] FOREIGN KEY([UserId])
REFERENCES [dbo].[Users] ([UserId])
GO
ALTER TABLE [dbo].[Stores] CHECK CONSTRAINT [FK__Stores__UserId__3A81B327]
GO
USE [master]
GO
ALTER DATABASE [PobbyDB] SET  READ_WRITE 
GO

GO
-- Trigger dam bao chi ton tai mot tai khoan Admin (user1) --
-- 008 tach bang: Role_Id da chuyen sang Accounts, trigger chay tren Accounts --
CREATE TRIGGER [dbo].[TRG_Accounts_ChiMotAdmin]
ON [dbo].[Accounts]
AFTER INSERT, UPDATE
AS
BEGIN
  IF ((SELECT COUNT(*) FROM [dbo].[Accounts] WHERE [Role_Id] = 1) > 1)
  BEGIN ROLLBACK TRANSACTION; THROW 50001, NChi ton tai mot tai khoan Admin!, 1; END
END
GO
