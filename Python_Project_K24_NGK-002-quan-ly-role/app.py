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
app.config['SECRET_KEY'] = os.environ.get('POBBY_SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app, supports_credentials=True)
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
    """Trang chủ, trả về giao diện chính."""
    return render_template('index.html')

# ==========================================
# 1. ĐĂNG KÝ
# ==========================================
@app.route('/api/dang-ky', methods=['POST'])
def register_api():
    """Đăng ký tài khoản khách hàng mới."""
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
    """Đăng nhập, lưu phiên khi thành công."""
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
    """Lấy danh sách tài khoản (quyền Admin — 009 US2)."""
    gate = user_bus.kiem_tra_quyen_xem_danh_sach(session.get('user_id'))
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
    """Cập nhật hồ sơ của chính mình."""
    if request.method == 'OPTIONS':
        return jsonify({"status": True}), 200
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json
    ket_qua = user_bus.cap_nhat_thong_tin_cua_toi(
        session.get('user_id'),
        session.get('user_id'),
        data.get('ten_user'),
        data.get('dia_chi'),
        data.get('sdt'),
        data.get('cmnd')
    )
    if not ket_qua.get('status') and "tài khoản khác" in ket_qua.get('message', ''):
        return jsonify(ket_qua), 403
    return jsonify(ket_qua)

# ==========================================
# 5. ĐỔI MẬT KHẨU
# ==========================================
@app.route('/api/doi-mat-khau', methods=['POST'])
def doi_mat_khau():
    """Đổi mật khẩu của chính mình."""
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json or {}
    ma_user_body = data.get('ma_user')
    if ma_user_body not in (None, "", session.get('user_id')):
        try:
            if int(ma_user_body) != int(session.get('user_id')):
                return jsonify({"status": False,
                                "message": "Không thể thao tác trên tài khoản khác!",
                                "data": None}), 403
        except (TypeError, ValueError):
            return jsonify({"status": False,
                            "message": "Không thể thao tác trên tài khoản khác!",
                            "data": None}), 403
    return jsonify(user_bus.doi_mat_khau_cua_toi(
        nguoi_id     = session.get('user_id'),
        ma_user      = session.get('user_id'),
        mat_khau_cu  = data.get('mat_khau_cu'),
        mat_khau_moi = data.get('mat_khau_moi')
    ))



# Lay user ID
@app.route('/api/stores/by-user/<int:user_id>', methods=['GET'])
def get_store_by_user(user_id):
    """Lấy gian hàng theo mã user."""
    return jsonify(gian_hang_bus.lay_store_theo_user(user_id))
# ==========================================
# 7. GIAN HÀNG / SELLER
# ==========================================
@app.route('/api/dang-ky-gian-hang', methods=['POST'])
def api_dang_ky_gian_hang():
    """Gửi đơn đăng ký gian hàng bán hàng."""
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
    """Lấy danh sách đơn đăng ký bán hàng (quyền Quản lý — 009 US3)."""
    gate = user_bus.kiem_tra_quyen_duyet_seller(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    return jsonify(gian_hang_bus.lay_danh_sach_yeu_cau())


@app.route('/api/duyet-seller/<int:request_id>', methods=['POST'])
def api_duyet_seller(request_id):
    """Duyệt đơn đăng ký bán hàng (quyền Quản lý — 009 US3)."""
    gate = user_bus.kiem_tra_quyen_duyet_seller(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    return jsonify(gian_hang_bus.duyet_yeu_cau(session.get('user_id'), request_id))


@app.route('/api/tu-choi-seller/<int:request_id>', methods=['POST'])
def api_tu_choi_seller(request_id):
    """Từ chối đơn đăng ký bán hàng kèm lý do (quyền Quản lý — 009 US3)."""
    gate = user_bus.kiem_tra_quyen_duyet_seller(session.get('user_id'))
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
    """Lấy toàn bộ danh mục sản phẩm."""
    return jsonify(category_bus.lay_tat_ca())


@app.route('/api/categories', methods=['POST'])
def add_category():
    """Thêm danh mục mới (quyền Quản lý)."""
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json
    return jsonify(category_bus.them_category(data.get('name')))


@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Sửa tên danh mục (quyền Quản lý)."""
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json
    return jsonify(category_bus.sua_category(category_id, data.get('name')))


@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Xóa danh mục (quyền Quản lý)."""
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    return jsonify(category_bus.xoa_category(category_id))

# ==========================================
# 9. SẢN PHẨM
# ==========================================
@app.route('/api/products', methods=['GET'])
def get_products():
    """Lấy danh sách sản phẩm, hỗ trợ tìm kiếm theo từ khóa/danh mục."""
    tu_khoa = request.args.get('q', '', type=str)
    category_id = request.args.get('category_id', None, type=str)
    if tu_khoa or category_id:
        if category_id == "":
            category_id = None
        return jsonify(san_pham_bus.tim_kiem_san_pham(tu_khoa or "", category_id))
    return jsonify(san_pham_bus.lay_tat_ca())


@app.route('/api/products/best-sellers', methods=['GET'])
def get_best_sellers():
    """Lấy top sản phẩm bán chạy cho trang chủ."""
    top = request.args.get('top', 10, type=int)
    return jsonify(san_pham_bus.lay_ban_chay(top))


@app.route('/api/products/store/<int:store_id>', methods=['GET'])
def get_products_by_store(store_id):
    """Lấy sản phẩm của một gian hàng."""
    return jsonify(san_pham_bus.lay_theo_store(store_id))


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_detail(product_id):
    """Lấy chi tiết một sản phẩm theo mã."""
    return jsonify(san_pham_bus.lay_theo_id(product_id))


# ==========================================
# API GIỎ HÀNG
# ==========================================
@app.route('/api/gio-hang/them', methods=['POST'])
def api_them_vao_gio():
    """Thêm sản phẩm vào giỏ hàng của phiên hiện tại."""
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
    """Xóa toàn bộ giỏ hàng của phiên hiện tại."""
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    return jsonify(cart_bus.xoa_toan_bo_gio(session.get('user_id')))


@app.route('/api/gio-hang/<int:user_id>', methods=['GET'])
def api_lay_gio_hang(user_id):
    """Lấy giỏ hàng của chính mình, chặn xem giỏ người khác."""
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
    """Đặt đơn hàng mới từ giỏ, xóa giỏ khi thành công."""
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
    if result.get('status'):
        cart_bus.xoa_toan_bo_gio(session.get('user_id'))
    return jsonify(result)

@app.route('/api/don-hang/hoa-don/<int:order_id>', methods=['GET'])
def api_lay_hoa_don(order_id):
    """Lấy hóa đơn của chính mình, chặn xem hóa đơn người khác."""
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    ket_qua = don_hang_bus.lay_hoa_don_cua_toi(session.get('user_id'), order_id)
    if not ket_qua.get('status') and "không có quyền" in ket_qua.get('message', ''):
        return jsonify(ket_qua), 403
    return jsonify(ket_qua)

# ==========================================
# ==========================================
# API QUẢN LÝ ĐƠN HÀNG (ADMIN)
# ==========================================
# 009: /api/don-hang/tat-ca + /api/don-hang/<id>/trang-thai (quản trị) đã bị gỡ
# (chức năng thuộc Seller /api/seller/don-hang* — xem FR-011 spec 009).

@app.route('/api/don-hang/cua-toi/<int:user_id>', methods=['GET'])
def api_lay_don_hang_cua_toi(user_id):
    """Lấy đơn hàng của chính mình, chặn xem đơn người khác."""
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
    """Xóa một sản phẩm khỏi giỏ hàng."""
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
    """Cập nhật số lượng một món trong giỏ hàng."""
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json
    return jsonify(cart_bus.cap_nhat_so_luong(
        session.get('user_id'),
        data.get('ProductId'),
        data.get('Quantity')
    ))
@app.route('/api/users/<int:ma_user>/status', methods=['PUT'])
def update_user_status(ma_user):
    """Khóa/mở khóa tài khoản Seller/Khách hàng bởi Quản lý."""
    ma_nguoi_thao_tac = session.get('user_id')
    gate = user_bus.kiem_tra_quyen_quan_ly(ma_nguoi_thao_tac)
    if not gate.get('status'):
        return jsonify(gate), 403
    data   = request.json or {}
    status = data.get('status')
    return jsonify(user_bus.cap_nhat_trang_thai(
        ma_nguoi_thao_tac, ma_user, status, "Quản lý"))


# ==========================================
# 4.2. CẤP LẠI MẬT KHẨU (FR-010 / FR-011)
# ==========================================
@app.route('/api/cap-lai-mat-khau', methods=['POST'])
def api_cap_lai_mat_khau():
    """Cấp lại mật khẩu cho user (quyền Quản lý)."""
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json or {}
    return jsonify(user_bus.cap_lai_mat_khau(
        session.get('user_id'),
        data.get('ma_user'),
        data.get('mat_khau_moi') or None
    ))


# ==========================================
# 4.3. QUẢN LÝ TÀI KHOẢN QUẢN LÝ — CHỈ ADMIN (003)
# ==========================================
@app.route('/api/quan-ly', methods=['GET'])
def api_lay_danh_sach_quan_ly():
    """Danh sách chỉ Quản lý, gate Admin-only (FR-005/FR-008)."""
    gate = user_bus.kiem_tra_quyen_admin(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    return jsonify(user_bus.lay_danh_sach_quan_ly())


@app.route('/api/quan-ly', methods=['POST'])
def api_tao_quan_ly():
    """Cấp tài khoản Quản lý mới, gate Admin-only (FR-004/FR-008)."""
    gate = user_bus.kiem_tra_quyen_admin(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json or {}
    return jsonify(user_bus.tao_quan_ly(
        ten_user=data.get('ten_user'),
        tendangnhap=data.get('tendangnhap'),
        mat_khau=data.get('mat_khau'),
        sdt=data.get('sdt'),
        dia_chi=data.get('dia_chi'),
        vai_tro=data.get('vai_tro') or data.get('role') or data.get('ma_nhom_quyen') or data.get('Role_Id'),
    ))


@app.route('/api/quan-ly/<int:ma_user>', methods=['PUT'])
def api_sua_quan_ly(ma_user):
    """Sửa Quản lý, gate Admin-only (FR-006/FR-008)."""
    gate = user_bus.kiem_tra_quyen_admin(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json or {}
    return jsonify(user_bus.sua_quan_ly(
        ma_user=ma_user,
        ten_user=data.get('ten_user'),
        dia_chi=data.get('dia_chi'),
        sdt=data.get('sdt'),
    ))


@app.route('/api/quan-ly/<int:ma_user>', methods=['DELETE'])
def api_xoa_quan_ly(ma_user):
    """Xóa Quản lý, gate Admin-only (FR-007/FR-008)."""
    gate = user_bus.kiem_tra_quyen_admin(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    return jsonify(user_bus.xoa_quan_ly(ma_user))


# ==========================================
# 10. SELLER — SAN PHAM / NHAP HANG / GIA (004 US1+US3)
# ==========================================
def _seller_store_hien_tai():
    """Gate Seller + phan giai store tu session, KHONG tin client."""
    gate = user_bus.kiem_tra_quyen_seller(session.get('user_id'))
    if not gate.get('status'):
        return None, (gate, 403)
    store_kq = gian_hang_bus.lay_store_theo_user(session.get('user_id'))
    if not store_kq.get('status'):
        return None, ({"status": False, "message": "Bạn chưa có gian hàng!",
                       "data": None}, 403)
    return store_kq['data'], None


@app.route('/api/seller/san-pham', methods=['GET'])
def api_seller_lay_san_pham():
    """Seller lấy sản phẩm thuộc shop của mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    store_id = store.get('store_id')
    return jsonify(san_pham_bus.lay_theo_store_cua_seller(store_id))


@app.route('/api/seller/san-pham', methods=['POST'])
def api_seller_them_san_pham():
    """Seller thêm sản phẩm mới vào shop của mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = request.json or {}
    return jsonify(san_pham_bus.them_san_pham_cua_seller(
        session.get('user_id'), store.get('store_id'),
        d.get('name'), d.get('description'), d.get('price'),
        d.get('old_price'), d.get('quantity'), d.get('category_id'),
        d.get('emoji'), d.get('image_url')))


@app.route('/api/seller/san-pham/<int:product_id>', methods=['PUT'])
def api_seller_sua_san_pham(product_id):
    """Seller sửa sản phẩm thuộc shop của mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = request.json or {}
    return jsonify(san_pham_bus.sua_san_pham_cua_seller(
        session.get('user_id'), store.get('store_id'), product_id,
        d.get('name'), d.get('description'), d.get('price'),
        d.get('old_price'), d.get('quantity'), d.get('category_id'),
        d.get('emoji'), d.get('image_url')))


@app.route('/api/seller/san-pham/<int:product_id>/an-hien', methods=['PUT'])
def api_seller_an_hien(product_id):
    """Seller ẩn/hiện sản phẩm thuộc shop của mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = request.json or {}
    return jsonify(san_pham_bus.an_hien_san_pham_cua_seller(
        session.get('user_id'), store.get('store_id'), product_id,
        d.get('is_active', 0)))


@app.route('/api/seller/san-pham/<int:product_id>/nhap-hang', methods=['POST'])
def api_seller_nhap_hang(product_id):
    """Seller nhập thêm tồn kho cho sản phẩm của mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = request.json or {}
    return jsonify(san_pham_bus.nhap_hang(
        session.get('user_id'), store.get('store_id'), product_id,
        d.get('so_luong')))


@app.route('/api/seller/san-pham/<int:product_id>/gia', methods=['PUT'])
def api_seller_doi_gia(product_id):
    """Seller đổi giá bán sản phẩm của mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = request.json or {}
    return jsonify(san_pham_bus.doi_gia_ban(
        session.get('user_id'), store.get('store_id'), product_id,
        d.get('gia_moi')))


# ==========================================
# 11. SELLER — DON HANG (004 US2)
# ==========================================
@app.route('/api/seller/don-hang', methods=['GET'])
def api_seller_lay_don_hang():
    """Seller lấy đơn hàng thuộc shop của mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    return jsonify(don_hang_bus.lay_don_hang_cua_seller(store.get('store_id')))


@app.route('/api/seller/don-hang/<int:order_id>/trang-thai', methods=['PUT'])
def api_seller_cap_nhat_trang_thai(order_id):
    """Seller cập nhật trạng thái đơn thuộc shop của mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = request.json or {}
    return jsonify(don_hang_bus.cap_nhat_trang_thai_cua_seller(
        session.get('user_id'), store.get('store_id'), order_id,
        d.get('status')))


# ==========================================
# 12. SELLER — THONG KE + TRANG SHOP (004 US4+US5)
# ==========================================
@app.route('/api/seller/thong-ke/tong-quan', methods=['GET'])
def api_seller_thong_ke_tong_quan():
    """Seller xem thống kê tổng quan shop của mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    return jsonify(don_hang_bus.lay_thong_ke_cua_seller(store.get('store_id')))


@app.route('/api/seller/thong-ke/doanh-thu-theo-thang', methods=['GET'])
def api_seller_doanh_thu_theo_thang():
    """Seller xem doanh thu theo tháng của shop mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    year = request.args.get('year', 2026, type=int)
    return jsonify(don_hang_bus.lay_doanh_thu_seller_theo_thang(
        store.get('store_id'), year))


@app.route('/api/seller/trang-shop', methods=['GET'])
def api_seller_xem_trang_shop():
    """Seller xem trang shop của mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    return jsonify({"status": True, "data": store})


@app.route('/api/seller/trang-shop', methods=['PUT'])
def api_seller_sua_trang_shop():
    """Seller cập nhật tên/giới thiệu/thâm niên shop của mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = request.json or {}
    return jsonify(gian_hang_bus.cap_nhat_trang_shop(
        session.get('user_id'), store.get('store_id'),
        d.get('ten_shop'), d.get('gioi_thieu'), d.get('tham_nien')))


if __name__ == '__main__':
    app.run(debug=True, port=5000)