@echo off
REM ============================================================
REM  import_mysql.bat — Tạo lại database PobbyDB với đúng mã UTF-8
REM
REM  Lưu ý: LUÔN dùng --default-character-set=utf8mb4 để tiếng Việt
REM  không bị lỗi mojibake (client Windows hay mặc định CP850).
REM
REM  Cách chạy: gõ mật khẩu MySQL khi được hỏi.
REM ============================================================

set MYSQL=mysql

echo [1/2] Tao cau truc bang (schema_mysql.sql)...
%MYSQL% -u root -p --default-character-set=utf8mb4 < "%~dp0schema_mysql.sql"
if errorlevel 1 goto :loi
echo       OK.

echo [2/2] Chen du lieu mau (seed_demo_mysql.sql)...
%MYSQL% -u root -p --default-character-set=utf8mb4 PobbyDB < "%~dp0seed_demo_mysql.sql"
if errorlevel 1 goto :loi
echo       OK.

echo.
echo Xong! Kiem tra nhanh tieng Viet:
%MYSQL% -u root -p --default-character-set=utf8mb4 -e "SELECT RoleName FROM PobbyDB.Roles;"
goto :het

:loi
echo.
echo LOI: co buoc import that bai. Kiem tra mat khau / dich vu MySQL da chay.
:het
pause