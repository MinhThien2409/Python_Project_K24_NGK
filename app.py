# app.py

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from back_end.BUS.UserBus import UserBus
from back_end.BUS.PhanQuyenBus import PhanQuyenBus
from back_end.Model.GianHang import GianHang
from back_end.Model.YeuCau import YeuCau
from back_end.BUS.GianHangBus import GianHangBus
from back_end.BUS.DanhMucBus import DanhMucBus
from back_end.BUS.SanPhamBus import SanPhamBus




app = Flask(__name__)
# Dòng này cho phép mọi cổng (3000, 5500, 63342...) đều được gọi vào Flask
CORS(app, resources={r"/*": {"origins": "*"}})

category_bus = DanhMucBus()

# Khởi tạo bộ não BUS
user_bus = UserBus()
phan_quyen_bus = PhanQuyenBus()
gian_hang_bus = GianHangBus()
san_pham_bus = SanPhamBus()


# ==========================================
# 0. API HIỂN THỊ GIAO DIỆN CHÍNH (TRANG CHỦ)
# ==========================================
@app.route('/')
def home():
    # Lệnh này sẽ tìm file index.html trong thư mục templates và hiển thị lên trình duyệt
    return render_template('index.html')

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


@app.route('/api/cap-nhat-profile', methods=['POST', 'OPTIONS'])
def cap_nhat_profile():
    # Xử lý lệnh "gõ cửa" thăm dò của trình duyệt
    if request.method == 'OPTIONS':
        return jsonify({"status": True}), 200

    data = request.json
    ma_user = data.get('ma_user')
    ten_user = data.get('ten_user')
    sdt = data.get('sdt')
    dia_chi = data.get('dia_chi')
    cmnd = data.get('cmnd')

    # Gọi hàm cập nhật từ UserBus
    ket_qua = user_bus.cap_nhat_user(ma_user, ten_user, dia_chi, sdt, cmnd)
    return jsonify(ket_qua)


@app.route('/api/dang-ky-gian-hang', methods=['POST'])
def api_dang_ky_gian_hang():
    data = request.json
    req = YeuCau(
        UserId       = data.get('UserId'),
        ShopName     = data.get('StoreName'),
        BusinessPhone= data.get('Phone'),
        Category     = data.get('Category'),
        Description  = data.get('Description'),
        NationalId   = data.get('NationalId')
    )
    return jsonify(gian_hang_bus.dang_ky_gian_hang(req))

@app.route('/api/seller-requests', methods=['GET'])
def api_lay_yeu_cau():
    return jsonify(gian_hang_bus.lay_danh_sach_yeu_cau())

@app.route('/api/duyet-seller/<int:request_id>', methods=['POST'])
def api_duyet_seller(request_id):
    data = request.json
    reviewed_by = data.get('reviewed_by')  # UserId của Admin
    return jsonify(gian_hang_bus.duyet_yeu_cau(request_id, reviewed_by))

@app.route('/api/tu-choi-seller/<int:request_id>', methods=['POST'])
def api_tu_choi_seller(request_id):
    data = request.json
    return jsonify(gian_hang_bus.tu_choi_yeu_cau(
        request_id,
        data.get('reviewed_by'),
        data.get('ly_do', '')
    ))

# ─── ROUTE: LẤY QUYỀN CỦA MỘT NHÓM ─────────────────────────
@app.route('/api/quyen-cua-nhom/<int:ma_nhom>', methods=['GET'])
def quyen_cua_nhom(ma_nhom):
    try:
        result = phan_quyen_bus.lay_quyen_cua_nhom(ma_nhom)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": False, "message": f"Lỗi server: {str(e)}"}), 500


# ─── ROUTE: LƯU QUYỀN CHO MỘT NHÓM ──────────────────────────
@app.route('/api/cap-quyen-nhom', methods=['POST'])
def cap_quyen_nhom():
    try:
        data = request.get_json()
        role_id     = data.get('role_id')
        permissions = data.get('permissions', [])

        if not role_id:
            return jsonify({"status": False, "message": "Thiếu role_id!"}), 400

        loi = []
        for p in permissions:
            result = phan_quyen_bus.cap_nhat_quyen(
                ma_nhom      = role_id,
                ma_chuc_nang = p.get('ma_chuc_nang'),
                xem          = p.get('xem',  False),
                them         = p.get('them', False),
                sua          = p.get('sua',  False),
                xoa          = p.get('xoa',  False)
            )
            if not result['status']:
                loi.append(p.get('ma_chuc_nang'))

        if loi:
            return jsonify({"status": False, "message": f"Lỗi khi lưu chức năng ID: {loi}"})

        return jsonify({"status": True, "message": f"Đã lưu quyền cho nhóm ID {role_id} thành công!"})

    except Exception as e:
        return jsonify({"status": False, "message": f"Lỗi server: {str(e)}"}), 500


@app.route('/api/ap-dung-quyen-nhom-cho-user', methods=['POST'])
def ap_dung_quyen_nhom_cho_user():
        data = request.get_json()
        ma_user = data.get('ma_user')
        if not ma_user:
            return jsonify({"status": False, "message": "Thiếu ma_user!"}), 400

        ket_qua = phan_quyen_bus.ap_dung_quyen_nhom_cho_user(ma_user)
        return jsonify(ket_qua)
# Thêm vào app.py
@app.route('/api/doi-mat-khau', methods=['POST'])
def doi_mat_khau():
    data = request.json
    ket_qua = user_bus.doi_mat_khau(
        ma_user     = data.get('ma_user'),
        mat_khau_cu = data.get('mat_khau_cu'),
        mat_khau_moi= data.get('mat_khau_moi')
    )
    return jsonify(ket_qua)
@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify(category_bus.lay_tat_ca())

@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.json
    return jsonify(category_bus.them_category(data.get('name')))

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    data = request.json
    return jsonify(category_bus.sua_category(category_id, data.get('name')))

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    return jsonify(category_bus.xoa_category(category_id))
# ==========================================
# API SẢN PHẨM
# ==========================================
@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(san_pham_bus.lay_tat_ca())

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_detail(product_id):
    return jsonify(san_pham_bus.lay_theo_id(product_id))

@app.route('/api/products/store/<int:store_id>', methods=['GET'])
def get_products_by_store(store_id):
    return jsonify(san_pham_bus.lay_theo_store(store_id))

@app.route('/api/products/best-sellers', methods=['GET'])
def get_best_sellers():
    return jsonify(san_pham_bus.lay_ban_chay())

@app.route('/api/products', methods=['POST'])
def add_product():
    d = request.json
    return jsonify(san_pham_bus.them_san_pham(
        ten        = d.get('name'),
        mo_ta      = d.get('description'),
        gia        = d.get('price'),
        gia_goc    = d.get('old_price'),
        so_luong   = d.get('quantity'),
        rating     = d.get('rating'),
        emoji      = d.get('emoji'),
        category_id= d.get('category_id'),
        store_id   = d.get('store_id')
    ))

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    d = request.json
    return jsonify(san_pham_bus.sua_san_pham(
        product_id = product_id,
        ten        = d.get('name'),
        mo_ta      = d.get('description'),
        gia        = d.get('price'),
        gia_goc    = d.get('old_price'),
        so_luong   = d.get('quantity'),
        rating     = d.get('rating'),
        emoji      = d.get('emoji'),
        category_id= d.get('category_id'),
        store_id   = d.get('store_id')
    ))

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    return jsonify(san_pham_bus.xoa_san_pham(product_id))
if __name__ == '__main__':
    app.run(debug=True, port=5000)
