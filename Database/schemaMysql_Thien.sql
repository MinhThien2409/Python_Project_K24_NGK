-- MySQL dump 10.13  Distrib 9.7.0, for Win64 (x86_64)
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
--

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
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `ThongBaoId` int NOT NULL AUTO_INCREMENT,
  `UserId` int NOT NULL,
  `NoiDung` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `OrderId` int DEFAULT NULL,
  `DaDoc` tinyint(1) NOT NULL DEFAULT '0',
  `CreatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ThongBaoId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
  `Address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`RequestId`),
  KEY `FK_SellerRequests_UserId` (`UserId`),
  CONSTRAINT `FK_SellerRequests_UserId` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `voucher`
--

DROP TABLE IF EXISTS `voucher`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `voucher` (
  `VoucherId` int NOT NULL AUTO_INCREMENT,
  `SellerId` int NOT NULL,
  `Code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `DiscountType` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `DiscountValue` decimal(18,2) NOT NULL,
  `MinOrderValue` decimal(18,2) NOT NULL DEFAULT '0.00',
  `MaxDiscount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `StartDate` datetime NOT NULL,
  `EndDate` datetime NOT NULL,
  `Quantity` int NOT NULL DEFAULT '0',
  `UsedQuantity` int NOT NULL DEFAULT '0',
  `IsActive` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`VoucherId`),
  UNIQUE KEY `Code` (`Code`),
  KEY `IX_Voucher_SellerId` (`SellerId`),
  CONSTRAINT `FK_Voucher_Seller` FOREIGN KEY (`SellerId`) REFERENCES `stores` (`StoreId`),
  CONSTRAINT `CK_Voucher_Date` CHECK ((`StartDate` <= `EndDate`)),
  CONSTRAINT `CK_Voucher_Max` CHECK ((`MaxDiscount` >= 0)),
  CONSTRAINT `CK_Voucher_Min` CHECK ((`MinOrderValue` >= 0)),
  CONSTRAINT `CK_Voucher_Quantity` CHECK (((`Quantity` >= 0) and (`UsedQuantity` >= 0) and (`UsedQuantity` <= `Quantity`))),
  CONSTRAINT `CK_Voucher_Type` CHECK ((`DiscountType` in (_utf8mb4'PERCENT',_utf8mb4'FIXED'))),
  CONSTRAINT `CK_Voucher_Value` CHECK ((((`DiscountType` = _utf8mb4'PERCENT') and (`DiscountValue` > 0) and (`DiscountValue` <= 100)) or ((`DiscountType` = _utf8mb4'FIXED') and (`DiscountValue` > 0))))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `voucherproduct`
--

DROP TABLE IF EXISTS `voucherproduct`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `voucherproduct` (
  `VoucherId` int NOT NULL,
  `ProductId` int NOT NULL,
  PRIMARY KEY (`VoucherId`,`ProductId`),
  KEY `IX_VoucherProduct_ProductId` (`ProductId`),
  CONSTRAINT `FK_VoucherProduct_Product` FOREIGN KEY (`ProductId`) REFERENCES `products` (`ProductId`),
  CONSTRAINT `FK_VoucherProduct_Voucher` FOREIGN KEY (`VoucherId`) REFERENCES `voucher` (`VoucherId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-15 14:39:26
