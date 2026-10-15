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
-- Dumping data for table `accounts`
--

LOCK TABLES `accounts` WRITE;
/*!40000 ALTER TABLE `accounts` DISABLE KEYS */;
INSERT INTO `accounts` VALUES (1,1,'admin','123456',1,'active'),(2,2,'quanly1','123456',2,'active'),(3,3,'seller1','123456',3,'active'),(4,4,'seller2','123456',3,'active'),(5,5,'seller3','123456',3,'active'),(6,6,'khach1','123456',4,'active'),(7,7,'khach2','123456',4,'active'),(8,8,'khach3','123456',4,'active'),(9,9,'khach4','123456',4,'active'),(10,10,'khach5','123456',4,'banned'),(11,11,'1','123456',4,'active'),(12,12,'sellertest','123456',3,'active'),(13,13,'sellertest1','123456',3,'active');
/*!40000 ALTER TABLE `accounts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `cartitems`
--

LOCK TABLES `cartitems` WRITE;
/*!40000 ALTER TABLE `cartitems` DISABLE KEYS */;
INSERT INTO `cartitems` VALUES (1,9,1,120000.00),(2,9,2,120000.00),(3,5,1,2200000.00),(4,9,1,120000.00);
/*!40000 ALTER TABLE `cartitems` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `carts`
--

LOCK TABLES `carts` WRITE;
/*!40000 ALTER TABLE `carts` DISABLE KEYS */;
INSERT INTO `carts` VALUES (1,6,120000.00,'2026-09-05 10:00:00'),(2,8,240000.00,'2026-09-06 11:30:00'),(3,9,2200000.00,'2026-09-07 14:00:00'),(4,11,120000.00,'2026-10-15 11:03:14');
/*!40000 ALTER TABLE `carts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,'Điện thoại',10.00),(2,'Laptop',5.00),(3,'Thời trang',0.00),(4,'Gia dụng',0.00),(5,'Sách',0.00),(6,'Đồng hồ',0.00),(7,'Phụ kiện công nghệ',5.00),(8,'Quà tặng',0.00),(9,'Máy tính bảng',5.00),(10,'Tai nghe',5.00),(11,'Bàn phím',5.00),(12,'Chuột máy tính',5.00),(13,'Màn hình máy tính',5.00),(14,'Máy in',5.00),(15,'Đồ gia dụng nhà bếp',0.00),(16,'Mỹ phẩm',0.00),(17,'Giày dép',0.00),(18,'Đồ chơi trẻ em',0.00);
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `orderitems`
--

LOCK TABLES `orderitems` WRITE;
/*!40000 ALTER TABLE `orderitems` DISABLE KEYS */;
INSERT INTO `orderitems` VALUES (1,1,1,'iPhone 15 Pro Max','?',1,32000000.00,32000000.00),(2,1,4,'Áo Hoodie Local Brand','?',2,450000.00,900000.00),(3,2,7,'Nồi chiên không dầu','?',1,2500000.00,2500000.00),(4,2,8,'Máy xay sinh tố','?',1,1150000.00,1150000.00),(5,3,3,'MacBook Air M3','?',1,31000000.00,31000000.00),(6,4,10,'Đồng hồ Casio','⌚',1,1800000.00,1800000.00),(7,5,25,'Áo thun basic cotton','?',1,180000.00,180000.00),(8,6,45,'Hộp quà tặng handmade','?',1,280000.00,280000.00);
/*!40000 ALTER TABLE `orderitems` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` VALUES (1,'Completed',25000.00,NULL,6,'Nguyễn Minh Khách','0901111116','88 Võ Văn Ngân, TP. Thủ Đức, TP. HCM','COD',NULL,32900000.00,0.00,32925000.00,NULL,'2026-09-08 09:15:00','2026-09-10 17:00:00'),(2,'Shipping',25000.00,NULL,7,'Trịnh Quỳnh Anh','0901111117','220/15 Nguyễn Trãi, Quận 5, TP. HCM','MOMO',NULL,3650000.00,0.00,3675000.00,NULL,'2026-09-12 10:00:00',NULL),(3,'Shipping',25000.00,NULL,8,'Đặng Tuấn Kiệt','0901111118','Số 5 Tôn Đức Thắng, Quận 1, TP. HCM','BANK',NULL,31000000.00,0.00,31025000.00,NULL,'2026-09-15 15:30:00',NULL),(4,'Cancelled',25000.00,NULL,9,'Vũ Ngọc Hà','0901111119','15 Ngõ 34 Xuân La, Tây Hồ, Hà Nội','COD',NULL,1800000.00,0.00,1825000.00,NULL,'2026-09-09 08:00:00','2026-09-09 08:20:00'),(5,'Shipping',25000.00,NULL,6,'Nguyễn Minh Khách','0901111116','88 Võ Văn Ngân, TP. Thủ Đức, TP. HCM','Bank',NULL,180000.00,0.00,205000.00,NULL,'2026-10-15 09:34:37',NULL),(6,'Pending',25000.00,NULL,6,'Nguyễn Minh Khách','0901111116','88 Võ Văn Ngân, TP. Thủ Đức, TP. HCM','COD',NULL,280000.00,0.00,305000.00,NULL,'2026-10-15 09:47:52',NULL);
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (1,'iPhone 15 Pro Max',10,32000000.00,1,1,'Hàng chính hãng VN/A, bảo hành 12 tháng',35000000.00,'images/products/iphone-15-pro-max.png',120,'?',1),(2,'Samsung Galaxy S25',15,25000000.00,1,1,'Mới nhất 2026, tích hợp AI thông minh',28000000.00,'images/products/samsung.jpg',85,'?',1),(3,'MacBook Air M3',8,31000000.00,2,1,'Chip M3 siêu mạnh mẽ, pin trâu 18 tiếng',34000000.00,'images/products/macbook.jpg',42,'?',1),(4,'Áo Hoodie Local Brand',50,450000.00,3,2,'Chất liệu cotton 100% thoáng mát, form rộng',650000.00,'images/products/hoodie-local-brand.png',320,'?',1),(5,'Giày Sneaker Nike',30,2200000.00,3,2,'Giày thể thao nam nữ, êm chân, bền bỉ',2800000.00,'images/products/giay-nike-air-max.png',98,'?',1),(6,'Balo Du Lịch',40,900000.00,3,2,'Chống nước nhẹ, nhiều ngăn tiện dụng',1200000.00,'images/products/tui_xach.png',115,'?',1),(7,'Nồi chiên không dầu',12,2500000.00,4,3,'Dung tích 5L, công nghệ Rapid Air',3200000.00,'images/products/noi-chien-khong-dau.jpg',64,'?',1),(8,'Máy xay sinh tố',20,1150000.00,4,3,'Cối thủy tinh 1.5L, 6 lưỡi dao',1500000.00,NULL,130,'?',1),(9,'Sách Lập trình Python',100,120000.00,5,3,'Giáo trình thực hành từ con số 0',180000.00,'images/products/sach-python.jpg',890,'?',1),(10,'Đồng hồ Casio',22,1800000.00,6,3,'Chống nước 50m, tuổi thọ pin 10 năm',2200000.00,'images/products/dong-ho-casio.jpg',53,'⌚',1),(11,'iPhone 15 128GB',20,22000000.00,1,1,'Chính hãng VN/A, màn hình Dynamic Island, bảo hành 12 tháng',24500000.00,NULL,210,'?',1),(12,'Samsung Galaxy Z Flip6',9,18500000.00,1,1,'Màn hình gập độc đáo, camera AI, pin 4000mAh',21990000.00,NULL,47,'?',1),(13,'Xiaomi 14T',25,11900000.00,1,1,'Camera Leica, sạc nhanh 67W, màn hình AMOLED 144Hz',13990000.00,NULL,76,'?',1),(14,'OPPO Reno12',18,9990000.00,1,1,'Thiết kế mỏng nhẹ, camera chân dung 50MP, sạc nhanh 80W',11490000.00,NULL,64,'?',1),(15,'Dell XPS 13',6,29500000.00,2,1,'Intel Core Ultra 7, RAM 16GB, SSD 512GB, màn hình OLED',32000000.00,NULL,18,'?',1),(16,'ASUS ROG Strix G16',5,38900000.00,2,1,'Laptop gaming RTX 4060, RAM 16GB, màn hình 165Hz',42000000.00,NULL,12,'?',1),(17,'Lenovo ThinkPad E14',14,17200000.00,2,1,'Bền bỉ cho văn phòng, Core i5, RAM 16GB, SSD 512GB',19000000.00,NULL,33,'?',1),(18,'MacBook Pro 14 M3',0,42000000.00,2,1,'Chip M3 Pro, màn hình Liquid Retina XDR (TẠM HẾT HÀNG)',45000000.00,NULL,25,'?',1),(19,'Tai nghe AirPods Pro 2',40,5490000.00,7,1,'Chống ồn chủ động, cổng sạc USB-C, bảo hành 12 tháng',6200000.00,NULL,310,'?',1),(20,'Sạc nhanh Anker 65W',80,690000.00,7,1,'Công nghệ GaN, 3 cổng sạc, tương thích laptop và điện thoại',890000.00,NULL,520,'?',1),(21,'Chuột Logitech MX Master 3S',35,2190000.00,7,1,'Chuột không dây công thái học, cuộn siêu nhanh, kết nối 3 máy',2590000.00,NULL,140,'?️',1),(22,'Bàn phím cơ Keychron K2',28,1890000.00,7,1,'Layout 75%, kết nối Bluetooth + USB-C, hot-swap switch',2200000.00,NULL,95,'⌨️',1),(23,'Ốp lưng iPhone 15 Pro Max',150,250000.00,7,1,'Chống sốc, trong suốt không ố vàng, hỗ trợ sạc MagSafe',350000.00,NULL,780,'?',1),(24,'Pin dự phòng 20000mAh',60,590000.00,7,1,'Sạc nhanh 22.5W, 2 cổng ra (TẠM ẨN ĐỂ KIỂM TRA LẠI HÀNG)',790000.00,NULL,410,'?',0),(25,'Áo thun basic cotton',199,180000.00,3,2,'Cotton 100% co giãn 4 chiều, nhiều màu, form regular',250000.00,NULL,1200,'?',1),(26,'Áo sơ mi Oxford nam',80,420000.00,3,2,'Vải Oxford dày dặn, không nhăn, phù hợp đi làm',550000.00,NULL,260,'?',1),(27,'Quần jeans slim fit',70,550000.00,3,2,'Denim co giãn nhẹ, ống côn, bền màu',750000.00,NULL,310,'?',1),(28,'Váy hoa nhí vintage',45,390000.00,3,2,'Chất voan mềm mại, dáng chữ A, phong cách nữ tính',520000.00,NULL,180,'?',1),(29,'Áo khoác bomber',35,780000.00,3,2,'Lót lưới thoáng khí, chống gió nhẹ, unisex',990000.00,NULL,90,'?',1),(30,'Giày Adidas Ultraboost',20,3400000.00,3,2,'Đế Boost êm ái, thích hợp chạy bộ và đi hằng ngày',4200000.00,NULL,55,'?',1),(31,'Dép sandal quai ngang',90,220000.00,3,2,'Đế EVA siêu nhẹ, chống trơn trượt, nhiều size',300000.00,NULL,430,'?',1),(32,'Mũ lưỡi trai thêu logo',120,120000.00,3,2,'Vải kaki dày, khóa điều chỉnh sau, nhiều màu',160000.00,NULL,340,'?',1),(33,'Kính mát thời trang',55,350000.00,3,2,'Tròng chống tia UV400, gọng nhựa dẻo bền',480000.00,NULL,120,'?️',1),(34,'Túi tote canvas',100,160000.00,3,2,'Vải canvas dày, có túi nhỏ bên trong, in hình tối giản',220000.00,NULL,390,'?',1),(35,'Thắt lưng da bò',0,290000.00,3,2,'Da bò thật, khóa kim loại (TẠM HẾT HÀNG)',390000.00,NULL,70,'?',1),(36,'Nồi cơm điện tử 1.8L',25,1650000.00,4,3,'Lòng nồi chống dính 5 lớp, 12 chế độ nấu, hẹn giờ',2100000.00,NULL,150,'?',1),(37,'Bàn ủi hơi nước',40,450000.00,4,3,'Công suất 2000W, đế gốm chống dính, tự ngắt an toàn',600000.00,NULL,110,'?',1),(38,'Máy lọc không khí',10,3900000.00,4,3,'Lọc bụi mịn PM2.5, phù hợp phòng 30m², vận hành êm',4800000.00,NULL,38,'?',1),(39,'Bộ nồi inox 3 món',30,980000.00,4,3,'Inox 304 đáy từ, dùng được trên bếp từ và bếp gas',1350000.00,NULL,205,'?',1),(40,'Sách Clean Code (bản dịch)',60,189000.00,5,3,'Nghệ thuật viết code sạch dành cho lập trình viên',250000.00,NULL,340,'?',1),(41,'Sách Đắc Nhân Tâm',150,86000.00,5,3,'Cuốn sách kinh điển về nghệ thuật giao tiếp và ứng xử',120000.00,NULL,1500,'?',1),(42,'Sách Nhà Giả Kim',130,79000.00,5,3,'Hành trình đi tìm vận mệnh của chàng chăn cừu Santiago',105000.00,NULL,980,'?',1),(43,'Đồng hồ Citizen Eco-Drive',8,5900000.00,6,3,'Năng lượng ánh sáng, không cần thay pin, kính sapphire',7200000.00,NULL,22,'⌚',1),(44,'Đồng hồ Daniel Wellington',15,3200000.00,6,3,'Thiết kế tối giản, dây da thay được, chống nước 3ATM',4000000.00,NULL,47,'⌚',1),(45,'Hộp quà tặng handmade',49,280000.00,8,3,'Hộp quà gồm nến thơm, thiệp và hoa khô, gói sẵn',360000.00,NULL,160,'?',1),(46,'Gấu bông Teddy 60cm',40,320000.00,8,3,'Bông gòn mềm mại, an toàn cho trẻ em, có thể giặt',420000.00,NULL,230,'?',1),(47,'Iphone Duo',10,36000000.00,1,4,'',40000000.00,NULL,0,'?',1),(48,'Bánh kém',10,190000.00,8,5,'d',200000.00,NULL,0,'?',1);
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'Admin'),(2,'Quản lý'),(3,'Seller'),(4,'Customer');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `sellerrequests`
--

LOCK TABLES `sellerrequests` WRITE;
/*!40000 ALTER TABLE `sellerrequests` DISABLE KEYS */;
INSERT INTO `sellerrequests` VALUES (1,8,'Shop Trái Cây Sạch','0912345001','Thực phẩm','pending','2026-09-10 09:00:00',NULL,NULL,NULL,'Nhập trái cây sạch về bán sỉ và lẻ','123124125',NULL),(2,9,'Xưởng Gỗ Mộc','0912345002','Nội thất','pending','2026-09-11 09:00:00',NULL,NULL,NULL,'Bàn ghế gỗ công nghiệp','1412412',NULL),(3,12,'FPT Shop','0523067705','Laptop','approved','2026-10-15 13:55:03','2026-10-15 13:55:21',2,NULL,'123','123456789',NULL),(4,13,'Bánh ABC','0905153570','Quà tặng','approved','2026-10-15 14:07:23','2026-10-15 14:07:37',2,NULL,NULL,'123456789','Tỉnh Khánh Hòa');
/*!40000 ALTER TABLE `sellerrequests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `stockreceiptitems`
--

LOCK TABLES `stockreceiptitems` WRITE;
/*!40000 ALTER TABLE `stockreceiptitems` DISABLE KEYS */;
INSERT INTO `stockreceiptitems` VALUES (1,1,47,10,3600000.00),(2,2,48,10,21304.00);
/*!40000 ALTER TABLE `stockreceiptitems` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `stockreceipts`
--

LOCK TABLES `stockreceipts` WRITE;
/*!40000 ALTER TABLE `stockreceipts` DISABLE KEYS */;
INSERT INTO `stockreceipts` VALUES (1,4,NULL,NULL,12,'2026-10-15 13:56:15',36000000.00,''),(2,5,NULL,NULL,13,'2026-10-15 14:08:50',213040.00,'');
/*!40000 ALTER TABLE `stockreceipts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `stores`
--

LOCK TABLES `stores` WRITE;
/*!40000 ALTER TABLE `stores` DISABLE KEYS */;
INSERT INTO `stores` VALUES (1,'Shop Điện Tử Anh Minh','Thành phố Hồ Chí Minh',3,'0902222001','Điện thoại','Chuyên điện thoại, laptop chính hãng',1,'2026-09-01 09:00:00',NULL),(2,'Shop Thời Trang Xinh','Thành phố Hồ Chí Minh',4,'0902222002','Thời trang','Quần áo, giày dép, phụ kiện thời trang',1,'2026-09-01 09:00:00',NULL),(3,'Shop Gia Dụng Gia Đình','Thành phố Hồ Chí Minh',5,'0902222003','Gia dụng','Đồ gia dụng, sách và quà tặng',1,'2026-09-01 09:00:00',NULL),(4,'FPT Shop','Thành phố Hồ Chí Minh',12,'0523067705','Laptop','123',1,'2026-10-15 13:55:21',NULL),(5,'Bánh ABC','Tỉnh Khánh Hòa',13,'0905153570','Quà tặng',NULL,1,'2026-10-15 14:07:37',NULL);
/*!40000 ALTER TABLE `stores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `suppliers`
--

LOCK TABLES `suppliers` WRITE;
/*!40000 ALTER TABLE `suppliers` DISABLE KEYS */;
/*!40000 ALTER TABLE `suppliers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Nguyễn Văn An','120 An Liễng, Phường 12, Hà Nội','0901111111','111111111'),(2,'Lê Thị Quản Lý','12 Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh','0901111112','111111112'),(3,'Trần Văn Bán','18A Cộng Hòa, Quận Tân Bình, TP. HCM','0901111113','111111113'),(4,'Phạm Thị Buôn','105 Trần Hưng Đạo, Quận 1, TP. HCM','0901111114','111111114'),(5,'Hoàng Văn Shop','Số 45 Phan Đăng Lưu, Quận Phú Nhuận, TP. HCM','0901111115','111111115'),(6,'Nguyễn Minh Khách','88 Võ Văn Ngân, TP. Thủ Đức, TP. HCM','0901111116','111111116'),(7,'Trịnh Quỳnh Anh','220/15 Nguyễn Trãi, Quận 5, TP. HCM','0901111117','111111117'),(8,'Đặng Tuấn Kiệt','Số 5 Tôn Đức Thắng, Quận 1, TP. HCM','0901111118','111111118'),(9,'Vũ Ngọc Hà','15 Ngõ 34 Xuân La, Tây Hồ, Hà Nội','0901111119','111111119'),(10,'Lâm Hồng Nhung','9B Mai Thị Lựu, Quận 1, TP. HCM','0901111120','111111120'),(11,'Huy','TP.HCM','0523067705','123456789'),(12,'Nguyễn Văn Shop','12 Võ Văn Tần, Phường Ngọc Hà, Thành phố Hà Nội','0523067705','123456789'),(13,'Nguyễn Thị Minh Châu','12 An Dương Vương, Phường Tây Nha Trang, Tỉnh Khánh Hòa','0905153570','123456789');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `voucher`
--

LOCK TABLES `voucher` WRITE;
/*!40000 ALTER TABLE `voucher` DISABLE KEYS */;
/*!40000 ALTER TABLE `voucher` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `voucherproduct`
--

LOCK TABLES `voucherproduct` WRITE;
/*!40000 ALTER TABLE `voucherproduct` DISABLE KEYS */;
/*!40000 ALTER TABLE `voucherproduct` ENABLE KEYS */;
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

-- Dump completed on 2026-10-15 14:38:10
