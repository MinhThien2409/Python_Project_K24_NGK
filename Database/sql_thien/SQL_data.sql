-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: pobbydb
-- ------------------------------------------------------
-- Server version	9.7.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '14a4adbd-4792-11f1-a858-088fc383b81c:1-214';

--
-- Table structure for table `accounts`
--

DROP TABLE IF EXISTS `accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts` (
  `AccountId` int NOT NULL AUTO_INCREMENT,
  `UserId` int NOT NULL,
  `Username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Role_Id` int DEFAULT NULL,
  `trang_thai` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT 'active',
  PRIMARY KEY (`AccountId`),
  UNIQUE KEY `UserId` (`UserId`),
  UNIQUE KEY `Username` (`Username`),
  KEY `FK_Accounts_Roles` (`Role_Id`),
  CONSTRAINT `FK_Accounts_Roles` FOREIGN KEY (`Role_Id`) REFERENCES `roles` (`RoleId`),
  CONSTRAINT `FK_Accounts_Users` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`),
  CONSTRAINT `CK_Accounts_Admin_KhongDuocKhoa` CHECK (((`trang_thai` <> _utf8mb4'banned') or (`Role_Id` <> 1)))
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts`
--

LOCK TABLES `accounts` WRITE;
/*!40000 ALTER TABLE `accounts` DISABLE KEYS */;
INSERT INTO `accounts` VALUES (1,1,'admin','123456',1,'active'),(2,2,'quanly1','123456',2,'active'),(3,3,'seller1','123456',3,'active'),(4,4,'seller2','123456',3,'active'),(5,5,'seller3','123456',3,'active'),(6,6,'khach1','123456',4,'active'),(7,7,'khach2','123456',4,'active'),(8,8,'khach3','123456',4,'active'),(9,9,'khach4','123456',6,'active'),(10,10,'khach5','123456',4,'banned');
/*!40000 ALTER TABLE `accounts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cartitems`
--

DROP TABLE IF EXISTS `cartitems`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cartitems` (
  `CartId` int NOT NULL,
  `ProductId` int NOT NULL,
  `Quantity` int NOT NULL DEFAULT '1',
  `UnitPrice` decimal(18,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`CartId`,`ProductId`),
  KEY `FK_CartItems_Product` (`ProductId`),
  CONSTRAINT `FK_CartItems_Cart` FOREIGN KEY (`CartId`) REFERENCES `carts` (`CartId`),
  CONSTRAINT `FK_CartItems_Product` FOREIGN KEY (`ProductId`) REFERENCES `products` (`ProductId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cartitems`
--

LOCK TABLES `cartitems` WRITE;
/*!40000 ALTER TABLE `cartitems` DISABLE KEYS */;
INSERT INTO `cartitems` VALUES (2,9,2,120000.00),(3,5,1,2200000.00);
/*!40000 ALTER TABLE `cartitems` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `carts`
--

DROP TABLE IF EXISTS `carts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `carts` (
  `CartId` int NOT NULL AUTO_INCREMENT,
  `UserId` int NOT NULL,
  `TotalAmount` decimal(18,2) DEFAULT '0.00',
  `CreatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`CartId`),
  KEY `FK_Carts_UserId` (`UserId`),
  CONSTRAINT `FK_Carts_UserId` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `carts`
--

LOCK TABLES `carts` WRITE;
/*!40000 ALTER TABLE `carts` DISABLE KEYS */;
INSERT INTO `carts` VALUES (1,6,66450000.00,'2026-09-05 10:00:00'),(2,8,240000.00,'2026-09-06 11:30:00'),(3,9,2200000.00,'2026-09-07 14:00:00'),(4,3,0.00,'2026-09-22 02:05:36'),(5,2,0.00,'2026-09-22 02:06:08');
/*!40000 ALTER TABLE `carts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `CategoryId` int NOT NULL AUTO_INCREMENT,
  `CategoryName` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `PlatformFeePercent` decimal(5,2) DEFAULT '0.00',
  PRIMARY KEY (`CategoryId`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,'Điện thoại',10.00),(2,'Laptop',5.00),(3,'Thời trang',0.00),(4,'Gia dụng',0.00),(5,'Sách',0.00),(6,'Đồng hồ',0.00);
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orderitems`
--

DROP TABLE IF EXISTS `orderitems`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orderitems` (
  `OrderItemId` int NOT NULL AUTO_INCREMENT,
  `OrderId` int NOT NULL,
  `ProductId` int NOT NULL,
  `ProductName` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `Emoji` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `Quantity` int NOT NULL DEFAULT '1',
  `UnitPrice` decimal(18,2) NOT NULL DEFAULT '0.00',
  `TotalPrice` decimal(18,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`OrderItemId`),
  KEY `FK_OrderItems_Order` (`OrderId`),
  KEY `FK_OrderItems_Product` (`ProductId`),
  CONSTRAINT `FK_OrderItems_Order` FOREIGN KEY (`OrderId`) REFERENCES `orders` (`OrderId`),
  CONSTRAINT `FK_OrderItems_Product` FOREIGN KEY (`ProductId`) REFERENCES `products` (`ProductId`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orderitems`
--

LOCK TABLES `orderitems` WRITE;
/*!40000 ALTER TABLE `orderitems` DISABLE KEYS */;
INSERT INTO `orderitems` VALUES (1,1,1,'iPhone 15 Pro Max','?',1,32000000.00,32000000.00),(2,1,4,'Áo Hoodie Local Brand','?',2,450000.00,900000.00),(3,2,7,'Nồi chiên không dầu','?',1,2500000.00,2500000.00),(4,2,8,'Máy xay sinh tố','?',1,1150000.00,1150000.00),(5,3,3,'MacBook Air M3','?',1,31000000.00,31000000.00),(6,4,10,'Đồng hồ Casio','⌚',1,1800000.00,1800000.00),(7,5,11,'Iphone Duo','?',22,65550000.00,1442100000.00);
/*!40000 ALTER TABLE `orderitems` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `OrderId` int NOT NULL AUTO_INCREMENT,
  `Status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'Pending',
  `ShippingFee` decimal(18,2) DEFAULT '0.00',
  `CartId` int DEFAULT NULL,
  `UserId` int NOT NULL DEFAULT '0',
  `ReceiverName` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `ReceiverPhone` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `ShippingAddress` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `PaymentMethod` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'COD',
  `VoucherCode` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `SubTotal` decimal(18,2) NOT NULL DEFAULT '0.00',
  `DiscountAmount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `TotalAmount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `Note` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `CreatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` datetime DEFAULT NULL,
  PRIMARY KEY (`OrderId`),
  KEY `FK_Orders_Cart` (`CartId`),
  KEY `FK_Orders_User` (`UserId`),
  CONSTRAINT `FK_Orders_Cart` FOREIGN KEY (`CartId`) REFERENCES `carts` (`CartId`),
  CONSTRAINT `FK_Orders_User` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` VALUES (1,'Completed',25000.00,NULL,6,'Nguyễn Minh Khách','0901111116','88 Võ Văn Ngân, TP. Thủ Đức, TP. HCM','COD',NULL,32900000.00,0.00,32925000.00,NULL,'2026-09-08 09:15:00','2026-09-10 17:00:00'),(2,'Shipping',25000.00,NULL,7,'Trịnh Quỳnh Anh','0901111117','220/15 Nguyễn Trãi, Quận 5, TP. HCM','MOMO',NULL,3650000.00,0.00,3675000.00,NULL,'2026-09-12 10:00:00',NULL),(3,'Pending',25000.00,NULL,8,'Đặng Tuấn Kiệt','0901111118','Số 5 Tôn Đức Thắng, Quận 1, TP. HCM','BANK',NULL,31000000.00,0.00,31025000.00,NULL,'2026-09-15 15:30:00',NULL),(4,'Cancelled',25000.00,NULL,9,'Vũ Ngọc Hà','0901111119','15 Ngõ 34 Xuân La, Tây Hồ, Hà Nội','COD',NULL,1800000.00,0.00,1825000.00,NULL,'2026-09-09 08:00:00','2026-09-09 08:20:00'),(5,'Confirmed',25000.00,NULL,6,'Nguyễn Minh Khách','0901111116','88 Võ Văn Ngân, TP. Thủ Đức, TP. HCM','COD',NULL,1442100000.00,0.00,1442125000.00,NULL,'2026-09-22 22:49:31',NULL);
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `ProductId` int NOT NULL AUTO_INCREMENT,
  `ProductName` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Quantity` int DEFAULT '0',
  `Price` decimal(18,2) NOT NULL,
  `CategoryId` int NOT NULL,
  `StoreId` int NOT NULL,
  `Description` varchar(1000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `OldPrice` decimal(18,2) DEFAULT NULL,
  `ImageUrl` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `SoldCount` int DEFAULT '0',
  `Emoji` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `IsActive` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`ProductId`),
  KEY `FK_Products_Categories` (`CategoryId`),
  KEY `FK_Products_Stores` (`StoreId`),
  CONSTRAINT `FK_Products_Categories` FOREIGN KEY (`CategoryId`) REFERENCES `categories` (`CategoryId`),
  CONSTRAINT `FK_Products_Stores` FOREIGN KEY (`StoreId`) REFERENCES `stores` (`StoreId`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (1,'iPhone 15 Pro Max',10,32000000.00,1,1,'Hàng chính hãng VN/A, bảo hành 12 tháng',35000000.00,'images/products/iphone-15-pro-max.png',120,'?',1),(2,'Samsung Galaxy S25',15,25000000.00,1,1,'Mới nhất 2026, tích hợp AI thông minh',28000000.00,'images/products/samsung.jpg',85,'?',1),(3,'MacBook Air M3',8,31000000.00,2,1,'Chip M3 siêu mạnh mẽ, pin trâu 18 tiếng',34000000.00,'images/products/macbook.jpg',42,'?',1),(4,'Áo Hoodie Local Brand',50,450000.00,3,2,'Chất liệu cotton 100% thoáng mát, form rộng',650000.00,'images/products/hoodie-local-brand.png',320,'?',1),(5,'Giày Sneaker Nike',30,2200000.00,3,2,'Giày thể thao nam nữ, êm chân, bền bỉ',2800000.00,'images/products/giay-nike-air-max.png',98,'?',1),(6,'Balo Du Lịch',40,890000.00,3,2,'Chống nước nhẹ, nhiều ngăn tiện dụng',1200000.00,'images/products/tui_xach.png',115,'?',1),(7,'Nồi chiên không dầu',12,2500000.00,4,3,'Dung tích 5L, công nghệ Rapid Air',3200000.00,'images/products/noi-chien-khong-dau.jpg',64,'?',1),(8,'Máy xay sinh tố',20,1150000.00,4,3,'Cối thủy tinh 1.5L, 6 lưỡi dao',1500000.00,NULL,130,'?',1),(9,'Sách Lập trình Python',100,120000.00,5,3,'Giáo trình thực hành từ con số 0',180000.00,'images/products/sach-python.jpg',890,'?',1),(10,'Đồng hồ Casio',22,1800000.00,6,3,'Chống nước 50m, tuổi thọ pin 10 năm',2200000.00,'images/products/dong-ho-casio.jpg',53,'⌚',1),(11,'Iphone Duo',40,65550000.00,1,1,'',69000000.00,NULL,0,'?',1);
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `RoleId` int NOT NULL AUTO_INCREMENT,
  `RoleName` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`RoleId`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'Admin'),(2,'Quản lý'),(3,'Seller'),(4,'Customer');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sellerrequests`
--

DROP TABLE IF EXISTS `sellerrequests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sellerrequests` (
  `RequestId` int NOT NULL AUTO_INCREMENT,
  `UserId` int NOT NULL,
  `ShopName` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `BusinessPhone` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Category` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `CreatedAt` datetime DEFAULT CURRENT_TIMESTAMP,
  `ReviewedAt` datetime DEFAULT NULL,
  `ReviewedBy` int DEFAULT NULL,
  `RejectReason` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `Description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `NationalId` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`RequestId`),
  KEY `FK_SellerRequests_UserId` (`UserId`),
  CONSTRAINT `FK_SellerRequests_UserId` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sellerrequests`
--

LOCK TABLES `sellerrequests` WRITE;
/*!40000 ALTER TABLE `sellerrequests` DISABLE KEYS */;
INSERT INTO `sellerrequests` VALUES (1,8,'Shop Trái Cây Sạch','0912345001','Thực phẩm','pending','2026-09-10 09:00:00',NULL,NULL,NULL,'Nhập trái cây sạch về bán sỉ và lẻ','123124125'),(2,9,'Xưởng Gỗ Mộc','0912345002','Nội thất','pending','2026-09-11 09:00:00',NULL,NULL,NULL,'Bàn ghế gỗ công nghiệp','1412412');
/*!40000 ALTER TABLE `sellerrequests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stockreceiptitems`
--

DROP TABLE IF EXISTS `stockreceiptitems`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stockreceiptitems` (
  `ItemId` int NOT NULL AUTO_INCREMENT,
  `ReceiptId` int NOT NULL,
  `ProductId` int NOT NULL,
  `Quantity` int NOT NULL,
  `UnitCost` decimal(18,2) DEFAULT NULL,
  PRIMARY KEY (`ItemId`),
  KEY `ReceiptId` (`ReceiptId`),
  KEY `ProductId` (`ProductId`),
  CONSTRAINT `stockreceiptitems_ibfk_1` FOREIGN KEY (`ReceiptId`) REFERENCES `stockreceipts` (`ReceiptId`),
  CONSTRAINT `stockreceiptitems_ibfk_2` FOREIGN KEY (`ProductId`) REFERENCES `products` (`ProductId`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stockreceiptitems`
--

LOCK TABLES `stockreceiptitems` WRITE;
/*!40000 ALTER TABLE `stockreceiptitems` DISABLE KEYS */;
INSERT INTO `stockreceiptitems` VALUES (1,1,11,10,NULL),(2,2,11,10,199.00),(3,3,11,10,50000000.00);
/*!40000 ALTER TABLE `stockreceiptitems` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stockreceipts`
--

DROP TABLE IF EXISTS `stockreceipts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stockreceipts` (
  `ReceiptId` int NOT NULL AUTO_INCREMENT,
  `StoreId` int NOT NULL,
  `SupplierId` int DEFAULT NULL,
  `SupplierNote` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `CreatedBy` int NOT NULL,
  `CreatedAt` datetime DEFAULT CURRENT_TIMESTAMP,
  `TotalCost` decimal(18,2) DEFAULT '0.00',
  `Note` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`ReceiptId`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stockreceipts`
--

LOCK TABLES `stockreceipts` WRITE;
/*!40000 ALTER TABLE `stockreceipts` DISABLE KEYS */;
INSERT INTO `stockreceipts` VALUES (1,1,NULL,NULL,3,'2026-09-22 23:14:02',0.00,NULL),(2,1,NULL,NULL,3,'2026-09-22 23:24:02',1990.00,''),(3,1,NULL,NULL,3,'2026-09-22 23:56:57',500000000.00,'');
/*!40000 ALTER TABLE `stockreceipts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stores`
--

DROP TABLE IF EXISTS `stores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stores` (
  `StoreId` int NOT NULL AUTO_INCREMENT,
  `StoreName` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `UserId` int NOT NULL,
  `Phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `Category` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `Description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `IsActive` tinyint(1) NOT NULL DEFAULT '1',
  `CreatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ThamNien` int DEFAULT NULL,
  PRIMARY KEY (`StoreId`),
  KEY `FK_Stores_UserId` (`UserId`),
  CONSTRAINT `FK_Stores_UserId` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`),
  CONSTRAINT `CK_Stores_ThamNien_0_100` CHECK (((`ThamNien` is null) or ((`ThamNien` >= 0) and (`ThamNien` <= 100))))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stores`
--

LOCK TABLES `stores` WRITE;
/*!40000 ALTER TABLE `stores` DISABLE KEYS */;
INSERT INTO `stores` VALUES (1,'Shop Điện Tử Anh Minh','TP. Hồ Chí Minh',3,'0902222001','Điện thoại','Chuyên điện thoại, laptop chính hãng',1,'2026-09-01 09:00:00',NULL),(2,'Shop Thời Trang Xinh','TP. Hồ Chí Minh',4,'0902222002','Thời trang','Quần áo, giày dép, phụ kiện thời trang',1,'2026-09-01 09:00:00',NULL),(3,'Shop Gia Dụng Gia Đình','TP. Hồ Chí Minh',5,'0902222003','Gia dụng','Đồ gia dụng, sách và quà tặng',1,'2026-09-01 09:00:00',NULL);
/*!40000 ALTER TABLE `stores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `suppliers`
--

DROP TABLE IF EXISTS `suppliers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `suppliers` (
  `SupplierId` int NOT NULL AUTO_INCREMENT,
  `StoreId` int NOT NULL,
  `Name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `Address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`SupplierId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `suppliers`
--

LOCK TABLES `suppliers` WRITE;
/*!40000 ALTER TABLE `suppliers` DISABLE KEYS */;
/*!40000 ALTER TABLE `suppliers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `UserId` int NOT NULL AUTO_INCREMENT,
  `FullName` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `Phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `NationalId` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`UserId`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Nguyễn Văn An','120 An Liễng, Phường 12, Hà Nội','0901111111','111111111'),(2,'Lê Thị Quản Lý','12 Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh','0901111112','111111112'),(3,'Trần Văn Bán','18A Cộng Hòa, Quận Tân Bình, TP. HCM','0901111113','111111113'),(4,'Phạm Thị Buôn','105 Trần Hưng Đạo, Quận 1, TP. HCM','0901111114','111111114'),(5,'Hoàng Văn Shop','Số 45 Phan Đăng Lưu, Quận Phú Nhuận, TP. HCM','0901111115','111111115'),(6,'Nguyễn Minh Khách','88 Võ Văn Ngân, TP. Thủ Đức, TP. HCM','0901111116','111111116'),(7,'Trịnh Quỳnh Anh','220/15 Nguyễn Trãi, Quận 5, TP. HCM','0901111117','111111117'),(8,'Đặng Tuấn Kiệt','Số 5 Tôn Đức Thắng, Quận 1, TP. HCM','0901111118','111111118'),(9,'Vũ Ngọc Hà','15 Ngõ 34 Xuân La, Tây Hồ, Hà Nội','0901111119','111111119'),(10,'Lâm Hồng Nhung','9B Mai Thị Lựu, Quận 1, TP. HCM','0901111120','111111120');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-23  0:13:04
