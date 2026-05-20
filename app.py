from flask import Flask, request, render_template_string

app = Flask(__name__)

# 1. LỚP GIAO DIỆN (Frontend - HTML & CSS cơ bản)
# Giao diện này tạo ra 2 ô nhập số và 1 nút bấm.
GIAO_DIEN_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Máy Tính Mini</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        .box { border: 2px solid #ccc; padding: 20px; width: 300px; margin: 0 auto; border-radius: 10px; box-shadow: 2px 2px 10px #aaa; }
        input { padding: 10px; width: 80px; font-size: 16px; margin: 5px; text-align: center; }
        button { padding: 10px 20px; font-size: 16px; background-color: #007bff; color: white; border: none; cursor: pointer; border-radius: 5px; }
        button:hover { background-color: #0056b3; }
        .ketqua { color: red; font-size: 24px; font-weight: bold; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Phép Tính Cộng</h2>

        <form method="POST">
            <input type="number" name="so_a" placeholder="Số a" required>
            <b>+</b>
            <input type="number" name="so_b" placeholder="Số b" required>
            <br><br>
            <button type="submit">Tính Tổng</button>
        </form>

        {% if ket_qua is not none %}
            <div class="ketqua">Đáp án: {{ ket_qua }}</div>
        {% endif %}
    </div>
</body>
</html>
"""


# 2. LỚP XỬ LÝ (Backend - Python)
# Đường dẫn '/' này cho phép cả 2 hành động: GET (Vào xem trang) và POST (Bấm nút gửi dữ liệu)
@app.route('/', methods=['GET', 'POST'])
def may_tinh():
    ket_qua_tinh = None

    # Nếu người dùng bấm nút "Tính Tổng" (Phương thức POST được gọi)
    if request.method == 'POST':
        # Lấy dữ liệu từ các ô input (dựa vào thuộc tính name="so_a" và name="so_b")
        a = int(request.form.get('so_a', 0))
        b = int(request.form.get('so_b', 0))

        # Xử lý tính toán
        ket_qua_tinh = a + b

    # Trả giao diện HTML ra màn hình, đồng thời "bơm" biến ket_qua_tinh vào HTML
    return render_template_string(GIAO_DIEN_HTML, ket_qua=ket_qua_tinh)


if __name__ == '__main__':
    app.run(debug=True)