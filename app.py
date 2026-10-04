# app.py

import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from back_end.BUS.UserBus import UserBus
from back_end.Model.YeuCau import YeuCau
from back_end.BUS.GianHangBus import GianHangBus
from back_end.BUS.DanhMucBus import DanhMucBus
from back_end.BUS.SanPhamBus import SanPhamBus
from back_end.BUS.GioHangBus import GioHangBus
from back_end.BUS.DonHangBus import DonHangBus
from back_end.BUS.VoucherBus import VoucherBus
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
voucher_bus = VoucherBus()

def _json_body():
    """Đọc body JSON an toàn: trả dict, hoặc None nếu body không phải JSON."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


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
    data = _json_body()
    if data is None:
        return jsonify({"status": False,
                        "message": "Dữ liệu gửi lên không hợp lệ!",
                        "data": None}), 400
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
    data = _json_body()
    if data is None:
        return jsonify({"status": False,
                        "message": "Dữ liệu gửi lên không hợp lệ!",
                        "data": None}), 400
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
    data = _json_body()
    if data is None:
        return jsonify({"status": False,
                        "message": "Dữ liệu gửi lên không hợp lệ!",
                        "data": None}), 400
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
    data = _json_body()
    if data is None:
        return jsonify({"status": False,
                        "message": "Dữ liệu gửi lên không hợp lệ!",
                        "data": None}), 400
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
    """Gửi đơn đăng ký gian hàng bán hàng; user lấy từ session, không tin UserId client."""
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = _json_body()
    if data is None:
        return jsonify({"status": False,
                        "message": "Dữ liệu gửi lên không hợp lệ!",
                        "data": None}), 400
    req = YeuCau(
        UserId        = session.get('user_id'),
        ShopName      = data.get('StoreName'),
        BusinessPhone = data.get('Phone'),
        Category      = data.get('Category'),
        Description   = data.get('Description'),
        NationalId    = None
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
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json or {}
    return jsonify(category_bus.them_category(data.get('name'), data.get('phi_san', 0)))


@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    gate = user_bus.kiem_tra_quyen_quan_ly(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = request.json or {}
    return jsonify(category_bus.sua_category(category_id, data.get('name'), data.get('phi_san', 0)))

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
    min_price = request.args.get('min_price', None, type=str)
    max_price = request.args.get('max_price', None, type=str)
    if tu_khoa or category_id or min_price or max_price:
        if category_id == "":
            category_id = None
        return jsonify(san_pham_bus.tim_kiem_san_pham(
            tu_khoa or "", category_id or None, min_price, max_price))
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
# API VOUCHER — KHÁCH HÀNG
# ==========================================
@app.route('/api/voucher/kiem-tra', methods=['POST'])
def api_voucher_kiem_tra():
    gate=user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'): return jsonify(gate),403
    d=_json_body()
    if d is None:return jsonify({"status":False,"message":"Dữ liệu gửi lên không hợp lệ!","data":None}),400
    return jsonify(voucher_bus.kiem_tra_ap_dung(d.get('voucherCode') or d.get('Code'),d.get('Items')))

# ==========================================
# API VOUCHER — SELLER
# ==========================================
@app.route('/api/voucher', methods=['GET'])
def api_voucher_list():
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    return jsonify(voucher_bus.lay_tat_ca(store.get('store_id')))

@app.route('/api/voucher/<int:voucher_id>', methods=['GET'])
def api_voucher_detail(voucher_id):
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    result = voucher_bus.lay_theo_id(voucher_id, store.get('store_id'))
    return jsonify(result), 200 if result.get('status') else 403

@app.route('/api/voucher', methods=['POST'])
def api_voucher_create():
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = _json_body()
    if d is None:
        return jsonify({"status": False, "message": "Dữ liệu gửi lên không hợp lệ!", "data": None}), 400
    return jsonify(voucher_bus.tao(
        seller_id=store.get('store_id'),
        product_ids=d.get('ProductIds') if d.get('ProductIds') is not None else d.get('product_ids'),
        code=d.get('Code'), name=d.get('Name'), dtype=d.get('DiscountType'),
        value=d.get('DiscountValue'), min_order=d.get('MinOrderValue'),
        max_discount=d.get('MaxDiscount'), start=d.get('StartDate'),
        end=d.get('EndDate'), quantity=d.get('Quantity')))

@app.route('/api/voucher/<int:voucher_id>', methods=['PUT'])
def api_voucher_update(voucher_id):
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = _json_body()
    if d is None:
        return jsonify({"status": False, "message": "Dữ liệu gửi lên không hợp lệ!", "data": None}), 400
    result = voucher_bus.sua(
        voucher_id, store.get('store_id'),
        d.get('ProductIds') if d.get('ProductIds') is not None else d.get('product_ids'),
        code=d.get('Code'), name=d.get('Name'), dtype=d.get('DiscountType'),
        value=d.get('DiscountValue'), min_order=d.get('MinOrderValue'),
        max_discount=d.get('MaxDiscount'), start=d.get('StartDate'),
        end=d.get('EndDate'), quantity=d.get('Quantity'))
    return jsonify(result), 200 if result.get('status') else 403

@app.route('/api/voucher/<int:voucher_id>/toggle', methods=['POST'])
def api_voucher_toggle(voucher_id):
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    result = voucher_bus.toggle(voucher_id, store.get('store_id'))
    return jsonify(result), 200 if result.get('status') else 403

@app.route('/api/voucher/<int:voucher_id>', methods=['DELETE'])
def api_voucher_delete(voucher_id):
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    result = voucher_bus.xoa(voucher_id, store.get('store_id'))
    return jsonify(result), 200 if result.get('status') else 403

# ==========================================
# API GIỎ HÀNG
# ==========================================
@app.route('/api/gio-hang/them', methods=['POST'])
def api_them_vao_gio():
    """Thêm sản phẩm vào giỏ hàng của phiên hiện tại."""
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = _json_body()
    if data is None:
        return jsonify({"status": False,
                        "message": "Dữ liệu gửi lên không hợp lệ!",
                        "data": None}), 400
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
    data = _json_body()
    if data is None:
        return jsonify({"status": False,
                        "message": "Dữ liệu gửi lên không hợp lệ!",
                        "data": None}), 400

    def _so(value, mac_dinh=0.0):
        """Ép số an toàn; giá trị không phải số trả None để reject input."""
        if value in (None, ""):
            return float(mac_dinh)
        try:
            so = float(str(value).strip())
        except (TypeError, ValueError):
            return None
        if so != so or so in (float("inf"), float("-inf")):
            return None
        return so

    def _nguyen(value, mac_dinh=0):
        """Ép số nguyên an toàn; giá trị không hợp lệ trả None."""
        if value in (None, ""):
            return mac_dinh
        try:
            so = float(str(value).strip())
        except (TypeError, ValueError):
            return None
        if so != so or so in (float("inf"), float("-inf")) or not so.is_integer():
            return None
        return int(so)

    voucher_code = str(data.get('voucherCode') or data.get('VoucherCode') or '').strip()
    # Client subtotal/discount/total are intentionally ignored. Product prices and voucher
    # calculation are authoritative in DonHangBus/DonHangDao.
    shipping_fee = _so(data.get('ShippingFee'), 25000)
    if shipping_fee is None or shipping_fee < 0:
        return jsonify({"status": False, "message": "Phí vận chuyển không hợp lệ!", "data": None}), 200
    don_hang_moi = DonHang(
        UserId=session.get('user_id'),
        ReceiverName=str(data.get('ReceiverName') or '').strip(),
        ReceiverPhone=str(data.get('ReceiverPhone') or '').strip(),
        ShippingAddress=str(data.get('ShippingAddress') or '').strip(),
        PaymentMethod=str(data.get('PaymentMethod') or 'COD').strip(),
        ShippingFee=shipping_fee,
        VoucherCode=voucher_code or None
    )
    items=data.get('Items')
    if not isinstance(items,list):
        items=[]
    for item in items:
        if not isinstance(item,dict):
            return jsonify({"status":False,"message":"Thông tin đơn hàng không hợp lệ!","data":None}),200
        qty=_nguyen(item.get('Quantity'),0)
        if qty is None or qty<=0:
            return jsonify({"status":False,"message":"Số lượng sản phẩm không hợp lệ!","data":None}),200
        ma_sp=_nguyen(item.get('ProductId'),0)
        if ma_sp is None or ma_sp<=0:
            return jsonify({"status":False,"message":"Thông tin sản phẩm không hợp lệ!","data":None}),200
        don_hang_moi.Items.append(OrderItem(ProductId=ma_sp,ProductName=str(item.get('ProductName') or f"Sản phẩm #{ma_sp}"),
            Emoji=str(item.get('Emoji') or '📦'),Quantity=qty,UnitPrice=0,TotalPrice=0))
    result=don_hang_bus.tao_don_hang(don_hang_moi)

    if result.get('status'):
        # Phase 2: chỉ xóa các món đã mua, giữ món chưa chọn trong giỏ.
        da_mua = []
        for item in don_hang_moi.Items:
            try:
                da_mua.append(int(item.ProductId))
            except (TypeError, ValueError):
                continue
        cart_bus.xoa_cac_san_pham(session.get('user_id'), da_mua)
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

@app.route('/api/don-hang/<int:order_id>/huy', methods=['PUT'])
def api_customer_huy_don(order_id):
    """Khách tự hủy đơn của mình, backend kiểm tra trạng thái."""
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    ket_qua = don_hang_bus.huy_don_hang_cua_customer(
        session.get('user_id'), order_id)
    if not ket_qua.get('status') and "không có quyền" in ket_qua.get('message', ''):
        return jsonify(ket_qua), 403
    return jsonify(ket_qua)

@app.route('/api/thong-bao/cua-toi', methods=['GET'])
def api_lay_thong_bao_cua_toi():
    """Lấy thông báo đã lưu của chính mình sau đăng nhập lại."""
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    return jsonify(don_hang_bus.lay_thong_bao_cua_user(session.get('user_id')))

@app.route('/api/thong-bao/danh-dau-da-doc', methods=['POST'])
def api_danh_dau_thong_bao_da_doc():
    """Đánh dấu một hoặc toàn bộ thông báo là đã đọc."""
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = _json_body()
    if data is None:
        return jsonify({"status": False,
                        "message": "Dữ liệu gửi lên không hợp lệ!",
                        "data": None}), 400
    return jsonify(don_hang_bus.danh_dau_thong_bao_da_doc(
        session.get('user_id'), data.get('thong_bao_id')))
@app.route('/api/gio-hang/xoa', methods=['POST'])
def api_xoa_khoi_gio():
    """Xóa một sản phẩm khỏi giỏ hàng."""
    gate = user_bus.kiem_tra_nguoi_dung_hoat_dong(session.get('user_id'))
    if not gate.get('status'):
        return jsonify(gate), 403
    data = _json_body()
    if data is None:
        return jsonify({"status": False,
                        "message": "Dữ liệu gửi lên không hợp lệ!",
                        "data": None}), 400
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
    data = _json_body()
    if data is None:
        return jsonify({"status": False,
                        "message": "Dữ liệu gửi lên không hợp lệ!",
                        "data": None}), 400
    return jsonify(cart_bus.cap_nhat_so_luong(
        session.get('user_id'),
        data.get('ProductId'),
        data.get('Quantity')
    ))
@app.route('/api/users/<int:ma_user>/status', methods=['PUT'])
def update_user_status(ma_user):
    """Admin khóa/mở khóa Quản lý; Quản lý khóa/mở khóa Seller/Customer."""
    ma_nguoi_thao_tac = session.get('user_id')
    actor = user_bus.lay_thong_tin_user(ma_nguoi_thao_tac) if ma_nguoi_thao_tac else None
    if not actor:
        return jsonify({"status": False, "message": "Bạn chưa đăng nhập!", "data": None}), 403
    role_name = user_bus.lay_ten_vai_tro_theo_id(actor.get('Role_Id'))
    data = _json_body()
    if data is None:
        return jsonify({"status": False, "message": "Dữ liệu gửi lên không hợp lệ!", "data": None}), 400
    status = data.get('status')
    if role_name == "Admin":
        return jsonify(user_bus.cap_nhat_trang_thai_quan_ly(ma_nguoi_thao_tac, ma_user, status))
    if role_name == "Quản lý":
        return jsonify(user_bus.cap_nhat_trang_thai(ma_nguoi_thao_tac, ma_user, status, "Quản lý"))
    return jsonify({"status": False, "message": "Bạn không có quyền thực hiện chức năng này!", "data": None}), 403


# ==========================================
# 4.2. CẤP LẠI MẬT KHẨU (FR-010 / FR-011)
# ==========================================
@app.route('/api/cap-lai-mat-khau', methods=['POST'])
def api_cap_lai_mat_khau():
    """Admin reset Quản lý về 123456; Quản lý giữ luồng reset Seller/Customer."""
    ma_nguoi_thao_tac = session.get('user_id')
    actor = user_bus.lay_thong_tin_user(ma_nguoi_thao_tac) if ma_nguoi_thao_tac else None
    if not actor:
        return jsonify({"status": False, "message": "Bạn chưa đăng nhập!", "data": None}), 403
    role_name = user_bus.lay_ten_vai_tro_theo_id(actor.get('Role_Id'))
    data = _json_body()
    if data is None:
        return jsonify({"status": False, "message": "Dữ liệu gửi lên không hợp lệ!", "data": None}), 400
    ma_user = data.get('ma_user')
    if role_name == "Admin":
        return jsonify(user_bus.cap_lai_mat_khau_quan_ly(ma_nguoi_thao_tac, ma_user))
    if role_name == "Quản lý":
        return jsonify(user_bus.cap_lai_mat_khau(
            ma_nguoi_thao_tac, ma_user, data.get('mat_khau_moi') or None))
    return jsonify({"status": False, "message": "Bạn không có quyền thực hiện chức năng này!", "data": None}), 403


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


@app.route('/api/seller/san-pham/tim-kiem', methods=['GET'])
def api_seller_tim_kiem_san_pham():
    """Phase 4: autocomplete san pham trong store cua seller (typeahead)."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    tu_khoa = request.args.get('q', '', type=str)
    limit = request.args.get('limit', 10, type=int)
    return jsonify(san_pham_bus.tim_kiem_cua_seller(
        store.get('store_id'), tu_khoa, limit))

@app.route('/api/seller/nhap-hang', methods=['POST'])
def api_seller_nhap_hang_nhieu():
    """Phase 4: nhap nhieu dong 1 phieu (gop duplicate, stock backend tinh)."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = request.json or {}
    return jsonify(san_pham_bus.nhap_hang_nhieu(
        session.get('user_id'), store.get('store_id'),
        d.get('items'), d.get('ghi_chu')))

@app.route('/api/seller/san-pham/tao-va-nhap', methods=['POST'])
def api_seller_tao_va_nhap():
    """Phase 4: tao SP moi tu phieu nhap neu chua ton tai + nhap kho."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = request.json or {}
    return jsonify(san_pham_bus.tao_va_nhap(
        session.get('user_id'), store.get('store_id'),
        d.get('name'), d.get('quantity'), d.get('price'),
        d.get('description'), d.get('category_id'),
        d.get('emoji'), d.get('image_url'),
        d.get('gia_nhap'), d.get('ghi_chu')))

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
    """Seller nhập thêm tồn kho cho sản phẩm của mình, kèm log giao dịch."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = request.json or {}
    return jsonify(san_pham_bus.nhap_hang(
        session.get('user_id'), store.get('store_id'), product_id,
        d.get('so_luong'), d.get('gia_nhap'), d.get('ghi_chu'), d.get('supplier_id')))


@app.route('/api/seller/lich-su-nhap-hang', methods=['GET'])
def api_seller_lich_su_nhap_hang():
    """Seller xem log các lần nhập hàng của gian hàng mình."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    return jsonify(san_pham_bus.lay_lich_su_nhap_hang(store.get('store_id')))


@app.route('/api/seller/san-pham/<int:product_id>/gia', methods=['PUT'])
def api_seller_doi_gia(product_id):
    """Seller đổi giá bán: legacy {gia_moi} + Phase 4 {gia_goc, gia_khuyen_mai, giam_gia}."""
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    d = request.json or {}
    return jsonify(san_pham_bus.doi_gia_ban(
        session.get('user_id'), store.get('store_id'), product_id,
        d.get('gia_moi'), d.get('gia_goc'),
        d.get('gia_khuyen_mai'), d.get('giam_gia')))


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
    store, loi = _seller_store_hien_tai()
    if loi:
        return jsonify(loi[0]), loi[1]
    year_raw = request.args.get('year', '').strip()
    if year_raw == '':
        year = datetime.now().year          # TC-234: không truyền year → năm hiện tại
    else:
        try:
            year = int(year_raw)
        except ValueError:
            return jsonify({"status": False, "message": "Năm không hợp lệ!", "data": []}), 400
    return jsonify(don_hang_bus.lay_doanh_thu_seller_theo_thang(store.get('store_id'), year))

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