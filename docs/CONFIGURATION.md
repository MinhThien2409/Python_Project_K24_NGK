# Configuration

## Database
DBconfig.py tạo DB_CONFIG. Template DBconfig.example.py có:

| Key | Environment variable | Fallback trong example |
|---|---|---|
| host | POBBY_DB_HOST | localhost |
| port | POBBY_DB_PORT | 3306 |
| user | POBBY_DB_USER | root |
| password | POBBY_DB_PASSWORD | 12345 |
| database | POBBY_DB_NAME | pobbydb |
| charset | — | utf8mb4 |

DBconfig.py là local configuration và được Git ignore. Giá trị local có thể khác template.

PowerShell:
    $env:POBBY_DB_HOST="localhost"
    $env:POBBY_DB_PORT="3306"
    $env:POBBY_DB_USER="root"
    $env:POBBY_DB_PASSWORD="your-password"
    $env:POBBY_DB_NAME="PobbyDB"

Không commit password thật.

## Flask SECRET_KEY
app.py hiện dùng fallback:
    os.environ.get("POBBY_SECRET_KEY", "dev-secret-key-change-in-production")

POBBY_SECRET_KEY vì vậy không mandatory theo implementation.

## Debug
Direct run hiện tại:
    app.run(debug=True, port=5000)

Phase 6 giữ nguyên behavior này. Phase 7 không sửa code.

## Dependencies
requirements.txt: Flask, Flask-Cors, gunicorn, pymysql, cryptography, pytest.

Có gunicorn dependency nhưng inventory không tìm thấy Procfile/config deployment riêng, nên không ghi command production như một fact.

## Security/configuration considerations
- SECRET_KEY fallback còn tồn tại.
- DB password fallback còn tồn tại trong configuration.
- Debug mode còn bật khi direct-run.
- Đây là current behavior, không phải claim production-safe.
