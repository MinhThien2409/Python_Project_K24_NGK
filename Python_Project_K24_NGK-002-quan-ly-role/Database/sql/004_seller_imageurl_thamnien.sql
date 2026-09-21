-- Migration 004: Seller role — ImageUrl + ThamNien (FR-001/FR-009)
-- Chay idempotent: bo qua buoc da co cot (guard IF COL_LENGTH IS NULL).
-- Products.ImageUrl NVARCHAR(500) NULL — anh san pham seller upload (NULL cho du lieu cu).
-- Stores.ThamNien INT NULL + CHECK 0-100 — so nam kinh nghiem seller tu khai.

USE [PobbyDB]
GO

IF COL_LENGTH('dbo.Products', 'ImageUrl') IS NULL
BEGIN
    ALTER TABLE [dbo].[Products] ADD [ImageUrl] [nvarchar](500) NULL;
END
GO

IF COL_LENGTH('dbo.Stores', 'ThamNien') IS NULL
BEGIN
    ALTER TABLE [dbo].[Stores] ADD [ThamNien] [int] NULL;
END
GO

-- CHECK 0-100 cho ThamNien (chua co thi them, co roi thi bo qua)
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CK_Stores_ThamNien_0_100')
BEGIN
    ALTER TABLE [dbo].[Stores]
    ADD CONSTRAINT [CK_Stores_ThamNien_0_100]
    CHECK ([ThamNien] IS NULL OR ([ThamNien] >= 0 AND [ThamNien] <= 100));
END
GO
