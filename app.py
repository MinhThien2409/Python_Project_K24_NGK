# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from BUS.UserBus import UserBus
from BUS.PhanQuyenBus import PhanQuyenBus

app = Flask(__name__)
# Dòng này cho phép mọi cổng (3000, 5500, 63342...) đều được gọi vào Flask
CORS(app, resources={r"/*": {"origins": "*"}})

# Khởi tạo bộ não BUS
user_bus = UserBus()
phan_quyen_bus = PhanQuyenBus()

# ==========================================
# 1. API ĐĂNG KÝ TÀI KHOẢN
# ==========================================
@app.route('/api/dang-ky', methods=['POST'])
def register_api():
    data = request.json
    ket_qua = user_bus.dang_ky_khach_hang(
        ten_user=data.get('ten_user'),
        dia_chi=data.get('dia_chi'),
        sdt=data.get('sdt'),
        tendangnhap=data.get('tendangnhap'),
        mat_khau=data.get('mat_khau')
    )
    return jsonify(ket_qua)

# ==========================================
# 2. API ĐĂNG NHẬP
# ==========================================
@app.route('/api/dang-nhap', methods=['POST'])
def login_api():
    data = request.json
    ket_qua = user_bus.dang_nhap(
        tendangnhap=data.get('tendangnhap'),
        mat_khau=data.get('mat_khau')
    )
    return jsonify(ket_qua)


# 3. API LẤY DANH SÁCH USER CHO DROP-DOWN
# ==========================================
@app.route('/api/users', methods=['GET'])
def get_users_api():
    ket_qua = user_bus.lay_danh_sach_user()

    # BỘ LỌC THÔNG MINH:
    # Nếu kết quả đã là một Dictionary có chứa "data" -> Trả về luôn
    if isinstance(ket_qua, dict) and "data" in ket_qua:
        return jsonify(ket_qua)

    # Nếu kết quả chỉ là một cái List (danh sách) -> Tự động bọc thêm status và data cho JS đọc được
    return jsonify({
        "status": True,
        "data": ket_qua
    })
# ==========================================
# 4. API LƯU CẤU HÌNH PHÂN QUYỀN NGOẠI LỆ
# ==========================================
@app.route('/api/cap-quyen-ngoai-le', methods=['POST'])
def save_permissions_api():
    data = request.json
    ma_user = data.get('ma_user')
    danh_sach_quyen = data.get('permissions', [])

    if not ma_user:
        return jsonify({"status": False, "message": "Vui lòng chọn tài khoản cần phân quyền!"})

    thanh_cong = True
    for quyen in danh_sach_quyen:
        res = phan_quyen_bus.cap_quyen_ngoai_le(
            ma_user=ma_user,
            ma_chuc_nang=quyen.get('ma_chuc_nang'),
            xem=quyen.get('xem', False),
            them=quyen.get('them', False),
            sua=quyen.get('sua', False),
            xoa=quyen.get('xoa', False)
        )
        if not res['status']:
            thanh_cong = False
            break

    if thanh_cong:
        return jsonify({"status": True, "message": "Đã lưu cấu hình phân quyền thành công!"})
    else:
        return jsonify({"status": False, "message": "Có lỗi xảy ra trong quá trình lưu quyền."})
# ==========================================
# 5. API LẤY DANH SÁCH QUYỀN CỦA 1 USER
# ==========================================
@app.route('/api/quyen-cua-user/<int:ma_user>', methods=['GET'])
def get_user_permissions_api(ma_user):
    # Gọi xuống PhanQuyenBus
    ket_qua = phan_quyen_bus.lay_quyen_cua_user(ma_user)
    return jsonify(ket_qua)

if __name__ == '__main__':
    app.run(debug=True, port=5000)