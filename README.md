# Pobby Shop — Dự án Web Thương mại Điện tử

> Hệ thống web thương mại điện tử đa vai trò (Admin / Quản lý / Seller / Customer) bằng Python + Flask, kết nối MySQL.

## 🏗️ Kiến trúc

```
Python_Project_K24/
├── app.py                    # Flask app + API routes (controller)
├── back_end/
│   ├── DBconfig.py           # Cấu hình MySQL (từ DBconfig.example.py)
│   ├── DBconnection.py       # Connection pool + wrapper cursor
│   ├── BUS/                  # Business logic (UserBus, DonHangBus, ...)
│   ├── DAO/                  # Data Access Object (truy cận MySQL)
│   └── Model/                # Lớp thực thể (User, SanPham, DonHang, ...)
├── templates/
│   └── index.html            # Giao diện chính (Jinja2)
├── static/
│   ├── css/style.css         # CSS design system
│   ├── js/main.js            # Frontend JS
│   └── images/products/      # Ảnh sản phẩm
├── Database/
│   ├── database.sql          # Schema chính
│   ├── schema_mysql.sql      # Schema MySQL chi tiết
│   ├── seed_demo_mysql.sql   # Dữ liệu mẫu
│   └── back_up.sql           # Bản sao lưu
├── tests/
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests (API)
├── specs/                    # Tài liệu thiết kế theo role
│   ├── 001-role-refactor/
│   ├── 002-quan-ly-role/
│   ├── 003-admin-role/
│   ├── 004-seller-role/
│   ├── 005-customer-role/
│   ├── 006-remove-reviews/
│   └── 007-project-cleanup/
├── requirements.txt
├── progress.md               # Tiến độ phát triển
└── BRD_TRD_REPORT.md         # Tài liệu đề cập / báo cáo
```

## 🚀 Cài đặt

### 1. Tạo môi trường ảo

```bash
python -m venv .venv
```

### 2. Kích hoạt môi trường

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 3. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 4. Cấu hình cơ sở dữ liệu

```bash
cp back_end/DBconfig.example.py back_end/DBconfig.py
```

Chỉnh sửa `back_end/DBconfig.py` với thông tin MySQL của bạn:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "mat_khau_cua_ban",
    "database": "PobbyDB",
    "charset": "utf8mb4",
}
```

### 5. Tạo cơ sở dữ liệu

Dùng đúng 2 file MySQL (`schema_mysql.sql` + `seed_demo_mysql.sql`), LUÔN kèm
`--default-character-set=utf8mb4` để tiếng Việt không bị hỏng (lỗi mojibake
"Quß║ún l├¢" xảy ra khi client mặc định dùng CP850 trên Windows):

```bash
mysql -u root -p --default-character-set=utf8mb4 < Database/schema_mysql.sql
mysql -u root -p --default-character-set=utf8mb4 PobbyDB < Database/seed_demo_mysql.sql
```

> Trên Windows có thể chạy luôn `Database/import_mysql.bat` (hỏi mật khẩu MySQL).
>
> Nếu dữ liệu hiện có đã bị lỗi tiếng Việt, chạy script sửa mã hóa:
> `mysql -u root -p --default-character-set=utf8mb4 < Database/fix_utf8mb4.sql`
> (dữ liệu sẽ được chuyển ngược CP850 → UTF-8 về đúng bản gốc, an toàn chạy lại).

## ▶️ Chạy dự án

### Chạy server phát triển

```bash
python app.py
```

Mở trình duyệt truy cập: [http://localhost:5000](http://localhost:5000)

### Cấu hình biến môi trường (tùy chọn)

```bash
# Windows
$env:POBBY_SECRET_KEY="your-secret-key"
$env:POBBY_DB_HOST="localhost"
$env:POBBY_DB_USER="root"
$env:POBBY_DB_PASSWORD="mat_khau"
$env:POBBY_DB_NAME="PobbyDB"
```

## 🧪 Chạy test

```bash
# Chạy toàn bộ test
pytest -v

# Chạy unit test
pytest tests/unit/ -v

# Chạy integration test
pytest tests/integration/ -v

# Chạy test theo spec
pytest tests/ -v -k "test_dang_nhap"
```

## 📋 Tính năng chính

| Vai trò | Tính năng |
|---------|-----------|
| **Admin** | Quản lý người dùng, khóa/mở khóa tài khoản, phân quyền vai trò |
| **Quản lý** | Quản lý danh mục, sản phẩm, đơn hàng |
| **Seller** | Quản lý cửa hàng, xử lý đơn hàng, theo dõi doanh thu |
| **Customer** | Đăng ký/đăng nhập, duyệt sản phẩm, giỏ hàng, thanh toán |

## 🔧 Công nghệ sử dụng

- **Backend**: Python 3, Flask, PyMySQL
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Database**: MySQL
- **Testing**: pytest, pytest-cov

## 📊 Trạng thái phát triển

Xem chi tiết trong [`progress.md`](progress.md)

| Spec | Trạng thái | Test |
|------|-----------|------|
| 002-quan-ly-role | ⏸️ Đang chặn | 132 PASS |
| 003-admin-role | ✅ Hoàn tất | 212/212 PASS |
| 004-seller-role | ✅ Hoàn tất | 277/277 PASS |
| 005-customer-role | ✅ Hoàn tất | 335/335 PASS |
| 006-remove-reviews | ✅ Hoàn tất | 354/354 PASS |
| 007-project-cleanup | ✅ Hoàn tất | 405/405 PASS |

## 📝 License

Dự án cho mục đích học tập — Kiểm thử phần mềm (K24).