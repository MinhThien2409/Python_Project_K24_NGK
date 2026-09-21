-- 006_remove_rating.sql
-- Migration loai bo cot Rating khoi Products (006-remove-reviews, US3).
-- Thu tu bat buoc (research Decision 3):
--   Buoc 1: deploy code da ngung doc/ghi Rating (Model/DAO/BUS/app.py/JS/HTML/CSS sach).
--   Buoc 2: moi chay migration nay + dong bo schema_mysql.sql / seed_demo_mysql.sql.
-- Chay: mysql -u root -p PobbyDB < Database/sql/006_remove_rating.sql
-- Luu y: chi chay 1 lan sau khi code sach; neu cot da xoa thi bo qua loi.
USE PobbyDB;
ALTER TABLE Products DROP COLUMN Rating;
