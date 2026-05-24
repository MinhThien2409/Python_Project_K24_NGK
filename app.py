# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from BUS.UserBus import UserBus

app = Flask(__name__)
# BẬT CORS: Cho phép mọi frontend gửi dữ liệu vào API này
CORS(app)

# Khởi tạo bộ não BUS
user_bus = UserBus()


@app.route('/api/register', methods=['POST'])
def register_api():
    # Lấy dữ liệu JSON từ Frontend gửi lên
    data = request.json

    # Ném vào tầng BUS để kiểm tra và lưu
    ket_qua = user_bus.dang_ky_khach_hang(
        ten_user=data.get('ten_user'),
        dia_chi=data.get('dia_chi'),
        sdt=data.get('sdt'),
        tendangnhap=data.get('tendangnhap'),
        mat_khau=data.get('mat_khau')
    )

    # Trả kết quả về lại cho trình duyệt (status và message)
    return jsonify(ket_qua)


if __name__ == '__main__':
    app.run(debug=True, port=5000)