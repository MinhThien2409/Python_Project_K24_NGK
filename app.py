# app.py

import os
import secrets

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from back_end.BUS.UserBus import UserBus
from back_end.Model.GianHang import GianHang
from back_end.Model.YeuCau import YeuCau
from back_end.BUS.GianHangBus import GianHangBus
from back_end.BUS.DanhMucBus import DanhMucBus
from back_end.BUS.SanPhamBus import SanPhamBus
from back_end.BUS.GioHangBus import GioHangBus
from back_end.BUS.DonHangBus import DonHangBus
from back_end.Model.DonHang import DonHang
from back_end.Model.OrderItem import OrderItem

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('POBBY_SECRET_KEY') or secrets.token_hex(16)
CORS(app, resources={r"/*": {"origins": "*"}})

# ── Khởi tạo BUS ──────────────────────────────────────────────
user_bus       = UserBus()
gian_hang_bus  = GianHangBus()
category_bus   = DanhMucBus()
san_pham_bus   = SanPhamBus()
cart_bus = GioHangBus()
don_hang_bus = DonHangBus()

# ==========================================
# 0. TRANG CHỦ
# ==========================================
@app.route('/')
def home():
    return render_template('index.html')

# ==========================================
# 1. ĐĂNG KÝ
# ==========================================
@app.route('/api/dang-ky', methods=['POST'])
def register_api():
    data = request.json
    return jsonify(user_bus.dang_ky_khach_hang(
        ten_user   = data.get('ten_user'),
        dia_chi    = data.get('dia_chi'),
        sdt        = data.get('sdt'),
        tendangnhap= data.get('tendangnhap'),
        mat_khau   = data.get('mat_khau')
    ))

# ==========================================
# 2. ĐĂNG NHẬP
# ==========================================
@app.route('/api/dang-nhap', methods=['POST'])
def login_api():
    data = request.json
    ket_qua = user_bus.dang_nhap(
        tendangnhap= data.get('tendangnhap'),
        mat_khau   = data.get('mat_khau')
    )
    if ket_qua.get('status'):
        session['user_id'] = ket_qua['data']['ma_user']
    return jsonify(ket_qua)


@app.route('/api/phien', methods=['GET'])
def api_phien():
    """Trả thông tin phiên đăng nhập hiện tại (FR-009 / phien.contract)."""
    ma_user = session.get('user_id')
    if not ma_user:
        return jsonify({"status": False, "message": "Bạn chưa đăng nhập!", "data": None})
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(ma_user)
    if not gate.get('status'):
        return jsonify(gate)
    thong_tin = user_bus.lay_thong_tin_user(ma_user)
    ten_vai_tro = user_bus.lay_ten_vai_tro_theo_id(thong_tin.get('Role_Id'))
    return jsonify({
        "status": True,
        "message": "",
        "data": {
            "ma_user": ma_user,
            "ten_user": thong_tin.get('FullName'),
            "ma_nhom_quyen": thong_tin.get('Role_Id'),
            "ten_vai_tro": ten_vai_tro,
            "ten_vai_tro_hien_thi": ten_vai_tro,
            "trang_thai": thong_tin.get('trang_thai') or 'active',
            "sdt": thong_tin.get('Phone'),
            "dia_chi": thong_tin.get('Address'),
        }
    })


@app.route('/api/dang-xuat', methods=['POST'])
def api_dang_xuat():
    """Xóa toàn bộ phiên đăng nhập."""
    session.clear()
    return jsonify({"status": True, "message": "Đã đăng xuất."})

# ==========================================
# 3. DANH SÁCH USER
# ==========================================
@app.route('/api/users', methods=['GET'])
def get_users_api():
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    ket_qua = user_bus.lay_danh_sach_user()
    if isinstance(ket_qua, dict) and "data" in ket_qua:
        return jsonify(ket_qua)
    return jsonify({"status": True, "data": ket_qua})

# ==========================================
# 4. CẬP NHẬT PROFILE
# ==========================================
@app.route('/api/cap-nhat-profile', methods=['POST', 'OPTIONS'])
def cap_nhat_profile():
    if request.method == 'OPTIONS':
        return jsonify({"status": True}), 200
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json
    return jsonify(user_bus.cap_nhat_user(
        session.get('user_id'),
        data.get('ten_user'),
        data.get('dia_chi'),
        data.get('sdt'),
        data.get('cmnd')
    ))

# ==========================================
# 5. ĐỔI MẬT KHẨU
# ==========================================
@app.route('/api/doi-mat-khau', methods=['POST'])
def doi_mat_khau():
    data = request.json
    return jsonify(user_bus.doi_mat_khau(
        ma_user      = data.get('ma_user'),
        mat_khau_cu  = data.get('mat_khau_cu'),
        mat_khau_moi = data.get('mat_khau_moi')
    ))



# Lay user ID
@app.route('/api/stores/by-user/<int:user_id>', methods=['GET'])
def get_store_by_user(user_id):
    return jsonify(gian_hang_bus.lay_store_theo_user(user_id))
# ==========================================
# 7. GIAN HÀNG / SELLER
# ==========================================
@app.route('/api/dang-ky-gian-hang', methods=['POST'])
def api_dang_ky_gian_hang():
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json
    req  = YeuCau(
        UserId        = session.get('user_id'),
        ShopName      = data.get('StoreName'),
        BusinessPhone = data.get('Phone'),
        Category      = data.get('Category'),
        Description   = data.get('Description'),
        NationalId    = data.get('NationalId')
    )
    return jsonify(gian_hang_bus.dang_ky_gian_hang(req))


@app.route('/api/seller-requests', methods=['GET'])
def api_lay_yeu_cau():
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    return jsonify(gian_hang_bus.lay_danh_sach_yeu_cau())


@app.route('/api/duyet-seller/<int:request_id>', methods=['POST'])
def api_duyet_seller(request_id):
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    return jsonify(gian_hang_bus.duyet_yeu_cau(session.get('user_id'), request_id))


@app.route('/api/tu-choi-seller/<int:request_id>', methods=['POST'])
def api_tu_choi_seller(request_id):
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json
    return jsonify(gian_hang_bus.tu_choi_yeu_cau(
        session.get('user_id'),
        request_id,
        data.get('ly_do', '') if data else ''
    ))

# ==========================================
# 8. DANH MỤC
# ==========================================
@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify(category_bus.lay_tat_ca())


@app.route('/api/categories', methods=['POST'])
def add_category():
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json
    return jsonify(category_bus.them_category(data.get('name')))


@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json
    return jsonify(category_bus.sua_category(category_id, data.get('name')))


@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    return jsonify(category_bus.xoa_category(category_id))

# ==========================================
# 9. SẢN PHẨM
# ==========================================
@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(san_pham_bus.lay_tat_ca())


@app.route('/api/products/best-sellers', methods=['GET'])
def get_best_sellers():
    top = request.args.get('top', 10, type=int)
    return jsonify(san_pham_bus.lay_ban_chay(top))


@app.route('/api/products/store/<int:store_id>', methods=['GET'])
def get_products_by_store(store_id):
    return jsonify(san_pham_bus.lay_theo_store(store_id))


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_detail(product_id):
    return jsonify(san_pham_bus.lay_theo_id(product_id))


@app.route('/api/products', methods=['POST'])
def add_product():
    d = request.json
    return jsonify(san_pham_bus.them_san_pham(
        ten         = d.get('name'),
        mo_ta       = d.get('description'),
        gia         = d.get('price'),
        gia_goc     = d.get('old_price'),
        so_luong    = d.get('quantity'),
        rating      = d.get('rating'),
        emoji       = d.get('emoji'),
        image_url=d.get('image_url'),
        category_id = d.get('category_id'),
        store_id    = d.get('store_id', 1)
    ))


@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    d = request.json
    return jsonify(san_pham_bus.sua_san_pham(
        product_id  = product_id,
        ten         = d.get('name'),
        mo_ta       = d.get('description'),
        gia         = d.get('price'),
        gia_goc     = d.get('old_price'),
        so_luong    = d.get('quantity'),
        rating      = d.get('rating'),
        emoji       = d.get('emoji'),
        image_url=d.get('image_url'),
        category_id = d.get('category_id'),
        store_id    = d.get('store_id', 1)
    ))


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    return jsonify(san_pham_bus.xoa_san_pham(product_id))


# ==========================================
# API GIỎ HÀNG
# ==========================================
@app.route('/api/gio-hang/them', methods=['POST'])
def api_them_vao_gio():
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json
    result = cart_bus.xu_ly_them_vao_gio(
        session.get('user_id'),
        data.get('ProductId'),
        data.get('Quantity'),
        data.get('UnitPrice'),
        data.get('Force', False)   # ← thêm
    )
    return jsonify(result)

@app.route('/api/gio-hang/xoa-tat-ca', methods=['POST'])
def api_xoa_tat_ca_gio():
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    return jsonify(cart_bus.xoa_toan_bo_gio(session.get('user_id')))


@app.route('/api/gio-hang/<int:user_id>', methods=['GET'])
def api_lay_gio_hang(user_id):
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    if user_id != session.get('user_id'):
        return jsonify({"status": False,
                        "message": "Không thể thao tác trên tài khoản khác!",
                        "data": None}), 403
    result = cart_bus.lay_thong_tin_gio_hang(user_id)
    return jsonify(result)


# ==========================================
# API ĐƠN HÀNG
# ==========================================
@app.route('/api/don-hang/dat-hang', methods=['POST'])
def api_dat_hang():
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json

    don_hang_moi = DonHang(
        UserId        = session.get('user_id'),
        ReceiverName  = str(data.get('ReceiverName', '')),
        ReceiverPhone = str(data.get('ReceiverPhone', '')),
        ShippingAddress = str(data.get('ShippingAddress', '')),
        PaymentMethod = str(data.get('PaymentMethod', 'COD')),
        SubTotal      = float(data.get('SubTotal', 0)),
        ShippingFee   = float(data.get('ShippingFee', 25000)),
        DiscountAmount= float(data.get('Discount', 0)),
        TotalAmount   = float(data.get('TotalAmount', 0))
    )

    for item in data.get('Items', []):
        qty   = int(item.get('Quantity')  or 0)
        price = float(item.get('UnitPrice') or 0)
        don_hang_moi.Items.append(OrderItem(
            ProductId   = int(item.get('ProductId')    or 0),
            ProductName = str(item.get('ProductName')  or f"Sản phẩm #{item.get('ProductId')}"),
            Emoji       = str(item.get('Emoji')        or '📦'),
            Quantity    = qty,
            UnitPrice   = price,
            TotalPrice  = qty * price
        ))

    result = don_hang_bus.tao_don_hang(don_hang_moi)
    return jsonify(result)

# ==========================================
# API QUẢN LÝ ĐƠN HÀNG (ADMIN)
# ==========================================
@app.route('/api/don-hang/tat-ca', methods=['GET'])
def api_lay_tat_ca_don_hang():
    return jsonify(don_hang_bus.lay_tat_ca_don_hang())

@app.route('/api/don-hang/<int:order_id>/trang-thai', methods=['PUT'])
def api_cap_nhat_trang_thai(order_id):
    data = request.json
    new_status = data.get('status')
    return jsonify(don_hang_bus.thay_doi_trang_thai(order_id, new_status))
@app.route('/api/don-hang/cua-toi/<int:user_id>', methods=['GET'])
def api_lay_don_hang_cua_toi(user_id):
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    if user_id != session.get('user_id'):
        return jsonify({"status": False,
                        "message": "Không thể thao tác trên tài khoản khác!",
                        "data": None}), 403
    return jsonify(don_hang_bus.lay_don_hang_cua_toi(user_id))
@app.route('/api/gio-hang/xoa', methods=['POST'])
def api_xoa_khoi_gio():
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json
    return jsonify(cart_bus.xoa_khoi_gio(
        session.get('user_id'),
        data.get('ProductId')
    ))

@app.route('/api/gio-hang/cap-nhat', methods=['POST'])
def api_cap_nhat_so_luong():
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json
    return jsonify(cart_bus.cap_nhat_so_luong(
        session.get('user_id'),
        data.get('ProductId'),
        data.get('Quantity')
    ))
@app.route('/api/thong-ke/tong-quan', methods=['GET'])
def api_thong_ke_tong_quan():
    return jsonify(don_hang_bus.lay_thong_ke_tong_quan())

@app.route('/api/thong-ke/doanh-thu-theo-thang', methods=['GET'])
def api_doanh_thu_theo_thang():
    year = request.args.get('year', 2026, type=int)
    return jsonify(don_hang_bus.lay_doanh_thu_theo_thang(year))
@app.route('/api/don-hang/cua-seller/<int:store_id>', methods=['GET'])
def api_lay_don_hang_cua_seller(store_id):
    return jsonify(don_hang_bus.lay_don_hang_cua_seller(store_id))
@app.route('/api/users/<int:ma_user>/status', methods=['PUT'])
def update_user_status(ma_user):
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data   = request.json or {}
    status = data.get('status')  # 'active' hoặc 'banned'
    return jsonify(user_bus.cap_nhat_trang_thai(session.get('user_id'), ma_user, status))


# ==========================================
# 4.2. CẤP LẠI MẬT KHẨU (FR-010 / FR-011)
# ==========================================
@app.route('/api/cap-lai-mat-khau', methods=['POST'])
def api_cap_lai_mat_khau():
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json or {}
    return jsonify(user_bus.cap_lai_mat_khau(
        session.get('user_id'),
        data.get('ma_user'),
        data.get('mat_khau_moi') or None
    ))


if __name__ == '__main__':
    app.run(debug=True, port=5000)