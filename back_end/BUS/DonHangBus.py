from back_end.DAO.DonHangDao import DonHangDao
from back_end.Model.DonHang import DonHang
from datetime import datetime
import re

# Ma tran luong trang thai seller (004 US2) — terminal khong doi duoc
LUONG_TRANG_THAI = {
    "Pending": ("Confirmed", "Cancelled"),
    "Confirmed": ("Shipping", "Cancelled"),
    "Shipping": ("Completed", "Cancelled"),
    "Completed": (),
    "Cancelled": (),
}

# ── 005 US3: hằng số validate thanh toán (đầu file, G6) ──
SDT_REGEX = r"^0\d{9}$"
PHUONG_THUC_HOP_LE = ("COD", "Bank", "Momo", "VNPay")


class DonHangBus:
    def __init__(self):
        """Khởi tạo BUS đơn hàng với DAO mặc định."""
        self.dao = DonHangDao()

    def _nhom_items_theo_shop(self, dh: DonHang):
        """Nhóm Items theo StoreId; trả (ds_don, ds_store_tong) hoặc dict lỗi."""
        product_ids = [item.ProductId for item in dh.Items]
        store_map = self.dao.lay_store_ids_cua_san_pham(product_ids)

        nhom = {}
        for item in dh.Items:
            store_id = store_map.get(int(item.ProductId))
            if store_id is None:
                return {"status": False,
                        "message": f"Không tìm thấy StoreId của sản phẩm '{item.ProductName}'!"}
            nhom.setdefault(int(store_id), []).append(item)

        if not nhom:
            return {"status": False, "message": "Giỏ hàng trống, vui lòng thêm sản phẩm!"}
        tong_ship = float(dh.ShippingFee or 0)
        if tong_ship < 0:
            return {"status": False, "message": "Phí vận chuyển không hợp lệ!"}
        ship_moi_don = tong_ship / len(nhom)

        ds_don = []
        ds_store_tong = []
        for store_id in sorted(nhom):
            items = nhom[store_id]
            sub_total = float(sum(float(i.TotalPrice or 0) for i in items))
            tong_don = sub_total + ship_moi_don
            don = DonHang(
                UserId=dh.UserId, ReceiverName=dh.ReceiverName,
                ReceiverPhone=dh.ReceiverPhone, ShippingAddress=dh.ShippingAddress,
                PaymentMethod=dh.PaymentMethod, VoucherCode=dh.VoucherCode, Status='Pending',
                ShippingFee=ship_moi_don, SubTotal=sub_total,
                DiscountAmount=0,
                TotalAmount=tong_don, Note=dh.Note)
            don.Items = items
            ds_don.append(don)
            ds_store_tong.append((store_id, tong_don))
        return ds_don, ds_store_tong

    def tao_don_hang(self, dh: DonHang):
        """Validate thanh toán, nhóm Items theo shop, tạo N đơn all-or-nothing."""
        if not dh.ReceiverName or not dh.ReceiverPhone or not dh.ShippingAddress:
            return {"status": False, "message": "Vui lòng điền đầy đủ thông tin người nhận hàng!"}

        if not re.match(SDT_REGEX, str(dh.ReceiverPhone or "").strip()):
            return {"status": False, "message": "Số điện thoại người nhận không hợp lệ!"}

        # Phase 1 (Q6): giới hạn độ dài tên/địa chỉ người nhận (authoritative)
        if len(str(dh.ReceiverName or "").strip()) > 100:
            return {"status": False,
                    "message": "Tên người nhận quá dài, tối đa 100 ký tự!"}
        if len(str(dh.ShippingAddress or "").strip()) > 500:
            return {"status": False,
                    "message": "Địa chỉ giao hàng quá dài, tối đa 500 ký tự!"}

        if str(dh.PaymentMethod or "COD") not in PHUONG_THUC_HOP_LE:
            return {"status": False, "message": "Phương thức thanh toán không hợp lệ!"}

        if not isinstance(dh.Items, list) or len(dh.Items) == 0:
            return {"status": False, "message": "Giỏ hàng trống, vui lòng thêm sản phẩm!"}

        # Phase 2: đối chiếu giá/tồn/trạng thái với DB, ghi đè giá client gửi.

        # Phase 1: kiểm tra kiểu/giá trị từng dòng hàng (authoritative)
        for item in dh.Items:
            try:
                so_luong = float(item.Quantity)
            except (TypeError, ValueError):
                return {"status": False,
                        "message": "Số lượng sản phẩm không hợp lệ!"}
            if not so_luong.is_integer() or so_luong <= 0:
                return {"status": False,
                        "message": "Số lượng sản phẩm không hợp lệ!"}
            if item.ProductId in (None, ""):
                return {"status": False,
                        "message": "Thông tin sản phẩm không hợp lệ!"}
            try:
                int(item.ProductId)
            except (TypeError, ValueError):
                return {"status": False,
                        "message": "Thông tin sản phẩm không hợp lệ!"}
            try:
                gia = float(item.UnitPrice or 0)
            except (TypeError, ValueError):
                return {"status": False,
                        "message": "Đơn giá sản phẩm không hợp lệ!"}
            if gia < 0:
                return {"status": False,
                        "message": "Đơn giá sản phẩm không hợp lệ!"}

        loi_db = self._doi_chieu_gia_va_kho(dh)
        if loi_db:
            return loi_db

        if dh.TotalAmount <= 0:
            return {"status": False, "message": "Tổng tiền đơn hàng không hợp lệ!"}
        if float(dh.ShippingFee or 0) < 0:
            return {"status": False, "message": "Phí vận chuyển không hợp lệ!"}

        nhom = self._nhom_items_theo_shop(dh)
        if isinstance(nhom, dict):
            return nhom
        ds_don, ds_store_tong = nhom

        kq = self._tao_toan_bo_don(ds_don, ds_store_tong)
        return kq

    def _doi_chieu_gia_va_kho(self, dh: DonHang):
        """Ghi đè UnitPrice/TotalPrice/SubTotal/TotalAmount theo giá DB.

        Từ chối SP không tồn tại/ẩn/vượt kho. Khi DAO không có nguồn
        đối chiếu (mock/fake cũ) thì bỏ qua để giữ tương thích.
        """
        lay_thong_tin = getattr(self.dao, "lay_thong_tin_san_pham", None)
        if not callable(lay_thong_tin):
            # Compatibility only for legacy mocks that pre-populate authoritative totals.
            # Real DonHangDao always exposes lay_thong_tin_san_pham.
            if float(dh.SubTotal or 0) > 0 and float(dh.TotalAmount or 0) > 0:
                return None
            return {"status": False, "message": "Không thể xác thực giá sản phẩm từ cơ sở dữ liệu!"}
        try:
            bang = lay_thong_tin([int(i.ProductId) for i in dh.Items])
        except (TypeError, ValueError):
            return {"status": False,
                    "message": "Thông tin sản phẩm không hợp lệ!"}
        if not isinstance(bang, dict):
            return None
        for item in dh.Items:
            thong_tin = bang.get(int(item.ProductId))
            ten = item.ProductName or f"#{item.ProductId}"
            if not thong_tin:
                return {"status": False,
                        "message": f"Không tìm thấy sản phẩm {ten}!"}
            if not thong_tin.get("is_active", True):
                return {"status": False, "message": (
                    f"Sản phẩm '{thong_tin.get('name') or ten}' không còn kinh doanh!")}
            ton = int(thong_tin.get("quantity", 0))
            if int(item.Quantity or 0) > ton:
                return {"status": False, "message": (
                    f"Sản phẩm '{thong_tin.get('name') or ten}' "
                    f"chỉ còn {ton} sản phẩm trong kho!")}
            gia_chuan = float(thong_tin.get("price", 0))
            item.UnitPrice = gia_chuan
            item.TotalPrice = int(item.Quantity or 0) * gia_chuan
        dh.SubTotal = float(sum(float(i.TotalPrice or 0) for i in dh.Items))
        dh.TotalAmount = float(dh.SubTotal or 0) + float(dh.ShippingFee or 0) \
            - float(dh.DiscountAmount or 0)
        return None

    def _loi_tu_dao(self, result):
        """Lỗi hết hàng/không tồn tại trả về từ DAO (đã rollback toàn bộ)."""
        if not isinstance(result, dict):
            return None
        if result.get('error') == 'out_of_stock':
            return {"status": False, "message":
                    f"Sản phẩm '{result['product_name']}' chỉ còn {result['available']} sản phẩm trong kho!"}
        if result.get('error') == 'not_found':
            return {"status": False, "message":
                    f"Không tìm thấy sản phẩm {result['product_name']}!"}
        if result.get('error') == 'inactive':
            return {"status": False, "message":
                    f"Sản phẩm '{result['product_name']}' không còn kinh doanh!"}
        return None

    def _tao_toan_bo_don(self, ds_don, ds_store_tong):
        """Gọi DAO tạo N đơn; trả payload thành công/hồi lỗi cụ thể."""
        result = self.dao.tao_don_hang(ds_don)
        loi = self._loi_tu_dao(result)
        if loi:
            return loi
        if isinstance(result, dict) and result.get("error") == "invalid_voucher":
            return {"status": False, "message": result.get("message", "Voucher không hợp lệ!")}
        if not result:
            return {"status": False,
                    "message": "Không thể tạo đơn hàng, vui lòng thử lại sau!"}
        ten_store = self.dao.lay_ten_cua_cac_store([sid for sid, _ in ds_store_tong])
        orders = [
            {"order_id": oid, "store_id": sid,
             "store_name": ten_store.get(sid, f"Shop #{sid}"),
             "total": float(ds_don[idx].TotalAmount or 0)}
            for idx, (oid, (sid, _)) in enumerate(zip(result, ds_store_tong))
        ]
        return {"status": True,
                "message": f"Đặt hàng thành công! {len(result)} đơn hàng đã được tạo.",
                "data": {"order_ids": result, "orders": orders}}

    def lay_don_hang_cua_toi(self, user_id):
        """Lấy danh sách đơn hàng của chính khách đang đăng nhập."""
        if not user_id:
            return {"status": False, "message": "Lỗi xác thực người dùng", "data": []}
        danh_sach = self.dao.lay_don_hang_cua_user(user_id)
        return {"status": True, "data": danh_sach}

    def lay_hoa_don_cua_toi(self, user_id, order_id):
        """Mo hoa don chi tiet cua chinh minh, chan xem don khach khac."""
        if not user_id:
            return {"status": False, "message": "Lỗi xác thực người dùng"}
        chi_tiet = self.dao.lay_chi_tiet_don_hang(order_id)
        if not chi_tiet or not chi_tiet.get("don"):
            return {"status": False, "message": "Không tìm thấy đơn hàng!"}
        don = chi_tiet["don"]
        if int(don.get("UserId", 0)) != int(user_id):
            return {"status": False, "message": "Bạn không có quyền xem hóa đơn này!"}
        return {"status": True, "data": {**don, "Items": chi_tiet.get("items", [])}}

    def huy_don_hang_cua_customer(self, user_id, order_id):
        """Khach tu huy don cua minh, chi Pending moi duoc huy."""
        if not user_id:
            return {"status": False, "message": "Lỗi xác thực người dùng"}
        try:
            ma_don = int(order_id)
        except (TypeError, ValueError):
            return {"status": False, "message": "Không tìm thấy đơn hàng!"}
        chi_tiet = self.dao.lay_chi_tiet_don_hang(ma_don)
        if not chi_tiet or not chi_tiet.get("don"):
            return {"status": False, "message": "Không tìm thấy đơn hàng!"}
        don = chi_tiet["don"]
        try:
            chu_don = int(don.get("UserId", 0))
        except (TypeError, ValueError):
            chu_don = 0
        if chu_don != int(user_id):
            return {"status": False,
                    "message": "Bạn không có quyền hủy đơn hàng này!"}
        hien_tai = don.get("Status")
        if hien_tai != "Pending":
            return {"status": False,
                    "message": self._loi_huy_theo_trang_thai(hien_tai)}
        ok = self.dao.cap_nhat_trang_thai(ma_don, "Cancelled")
        if not ok:
            return {"status": False,
                    "message": "Không thể hủy đơn hàng, vui lòng thử lại sau!"}
        self._bao_huy_don(user_id, ma_don)
        return {"status": True,
                "message": f"Đã hủy đơn hàng #{ma_don} thành công!"}

    def huy_don_do_khoa_seller(self, store_id):
        """System flow khi khóa Seller: chỉ hủy Pending/Confirmed/Shipping."""
        if not store_id:
            return []
        try:
            result = self.dao.huy_don_do_khoa_seller(int(store_id))
        except Exception:
            return []
        # Notification failure không làm ảnh hưởng kết quả nghiệp vụ.
        for item in result or []:
            try:
                tao = getattr(self.dao, "tao_thong_bao", None)
                if callable(tao) and item.get("user_id"):
                    tao(item["user_id"],
                        f"Đơn hàng #{item['order_id']} đã được hủy vì gian hàng của người bán bị khóa.",
                        item["order_id"])
            except Exception:
                pass
        return result or []

    def _loi_huy_theo_trang_thai(self, hien_tai):
        """Tra loi tu choi huy don theo trang thai hien tai."""
        if hien_tai == "Confirmed":
            return "Đơn hàng đã được xác nhận, không thể hủy!"
        if hien_tai == "Shipping":
            return "Đơn hàng đang được giao, không thể hủy!"
        if hien_tai == "Completed":
            return "Đơn hàng đã hoàn thành, không thể hủy!"
        if hien_tai == "Cancelled":
            return "Đơn hàng đã được hủy trước đó!"
        return "Chỉ được hủy đơn ở trạng thái Chờ duyệt!"

    def _bao_huy_don(self, user_id, order_id):
        """Luu thong bao huy don, loi thong bao khong lam hong huy don."""
        tao = getattr(self.dao, "tao_thong_bao", None)
        if not callable(tao):
            return
        try:
            tao(user_id, f"Bạn đã hủy đơn hàng #{order_id} thành công!",
                order_id)
        except Exception:
            return

    def lay_thong_bao_cua_user(self, user_id):
        """Lay thong bao da luu cua khach, chua co kho thi tra rong."""
        if not user_id:
            return {"status": False, "message": "Lỗi xác thực người dùng",
                    "data": []}
        lay = getattr(self.dao, "lay_thong_bao_cua_user", None)
        if not callable(lay):
            return {"status": True, "data": []}
        try:
            danh_sach = lay(user_id) or []
        except Exception:
            danh_sach = []
        return {"status": True, "data": danh_sach}

    def danh_dau_thong_bao_da_doc(self, user_id, thong_bao_id=None):
        """Danh dau mot hoac toan bo thong bao cua khach la da doc."""
        if not user_id:
            return {"status": False, "message": "Lỗi xác thực người dùng"}
        danh_dau = getattr(self.dao, "danh_dau_thong_bao_da_doc", None)
        if not callable(danh_dau):
            return {"status": True,
                    "message": "Đã đánh dấu tất cả thông báo là đã đọc!"}
        try:
            ma_tb = int(thong_bao_id) if thong_bao_id not in (None, "") else None
        except (TypeError, ValueError):
            return {"status": False, "message": "Thông báo không hợp lệ!"}
        try:
            ok = danh_dau(user_id, ma_tb)
        except Exception:
            return {"status": False,
                    "message": "Không thể cập nhật thông báo, vui lòng thử lại sau!"}
        if ok:
            return {"status": True,
                    "message": "Đã đánh dấu thông báo là đã đọc!"}
        return {"status": False, "message": "Không tìm thấy thông báo!"}

    def thay_doi_trang_thai(self, order_id, new_status):
        """Chuyển trạng thái đơn theo luồng, sai luồng thì từ chối."""
        trang_thai_hop_le = ["Pending", "Confirmed", "Shipping", "Completed", "Cancelled"]
        if new_status not in trang_thai_hop_le:
            return {"status": False, "message": "Trạng thái đơn hàng không hợp lệ!"}
        hien_tai = self.dao.lay_trang_thai(order_id)
        if not hien_tai:
            return {"status": False, "message": "Không tìm thấy đơn hàng hoặc có lỗi xảy ra!"}
        if hien_tai in ("Completed", "Cancelled"):
            return {"status": False, "message": "Đơn hàng đã ở trạng thái cuối, không thể thay đổi!"}
        if new_status not in LUONG_TRANG_THAI.get(hien_tai, ()):
            return {"status": False, "message": "Chỉ được chuyển theo luồng trạng thái hợp lệ!"}
        is_success = self.dao.cap_nhat_trang_thai(order_id, new_status)
        if is_success:
            return {"status": True, "message": f"Đã chuyển đơn hàng sang: {new_status}"}
        return {"status": False, "message": "Không tìm thấy đơn hàng hoặc có lỗi xảy ra!"}

    def lay_tat_ca_don_hang(self):
        """Lấy toàn bộ đơn hàng cho trang quản trị."""
        danh_sach = self.dao.lay_tat_ca_don_hang()
        return {"status": True, "data": danh_sach}

    def lay_thong_ke_tong_quan(self):
        """Bọc thống kê thuần của DAO thành envelope chuẩn."""
        du_lieu = self.dao.lay_thong_ke_tong_quan()
        if not isinstance(du_lieu, dict) or not du_lieu:
            return {"status": False,
                    "message": "Không lấy được thống kê, vui lòng thử lại sau!",
                    "data": {}}
        return {"status": True, "data": du_lieu}

    def lay_doanh_thu_theo_thang(self, year):
        """Bọc doanh thu thuần của DAO thành envelope chuẩn."""
        du_lieu = self.dao.lay_doanh_thu_theo_thang(year)
        if not isinstance(du_lieu, list) or not du_lieu:
            return {"status": False,
                    "message": "Không lấy được doanh thu, vui lòng thử lại sau!",
                    "data": []}
        return {"status": True, "data": du_lieu}

    def lay_don_hang_cua_seller(self, store_id):
        """Lấy danh sách đơn có sản phẩm thuộc shop."""
        if not store_id:
            return {"status": False, "message": "Thiếu store_id!", "data": []}
        danh_sach = self.dao.lay_don_hang_cua_seller(store_id)
        return {"status": True, "data": danh_sach}

    def lay_thong_ke_cua_seller(self, store_id):
        """Thong ke tong quan cua shop, gan store_id de phan biet."""
        if not store_id:
            return {"status": False, "message": "Thiếu store_id!", "data": {}}
        data = self.dao.lay_thong_ke_cua_seller(store_id)
        if not data:
            data = {"doanh_thu": 0, "tong_don": 0, "cho_duyet": 0,
                    "dang_giao": 0, "hoan_thanh": 0, "da_huy": 0,
                    "top_san_pham": [], "don_gan_day": []}
        data["store_id"] = store_id
        return {"status": True, "data": data}

    def lay_doanh_thu_seller_theo_thang(self, store_id, year):
        """Doanh thu 12 thang cua shop, dam bao du 12 thang."""
        if not store_id:
            return {"status": False, "message": "Thiếu store_id!", "data": []}
        try:
            nam = int(year or datetime.now().year)
        except (TypeError, ValueError):
            nam = datetime.now().year
        data = self.dao.lay_doanh_thu_seller_theo_thang(store_id, nam)
        if not data:
            data = [{"thang": i, "doanh_thu": 0, "so_don": 0} for i in range(1, 13)]
        return {"status": True, "data": data}

    def cap_nhat_trang_thai_cua_seller(self, nguoi_id, store_id, order_id, trang_thai_moi):
        """Seller chuyen trang thai don cua shop minh theo luong."""
        hop_le = ['Pending', 'Confirmed', 'Shipping', 'Completed', 'Cancelled']
        if trang_thai_moi not in hop_le:
            return {"status": False, "message": "Trạng thái đơn hàng không hợp lệ!"}
        # T139: ownership must be checked before reading/validating Status.
        if not self.dao.don_thuoc_store(order_id, store_id):
            return {"status": False, "message": "Đơn hàng không thuộc gian hàng của bạn!"}
        hien_tai = self.dao.lay_trang_thai(order_id)
        if not hien_tai:
            return {"status": False, "message": "Không tìm thấy đơn hàng hoặc có lỗi xảy ra!"}
        if hien_tai in ("Completed", "Cancelled"):
            return {"status": False, "message": "Trạng thái cuối không thể thay đổi!"}
        # Phase 3: seller chi duoc huy don dang cho duyet; da Confirmed thi khong duoc huy.
        if trang_thai_moi == "Cancelled" and hien_tai != "Pending":
            return {"status": False, "message": "Seller chỉ được hủy đơn đang ở trạng thái Chờ duyệt!"}
        if trang_thai_moi not in LUONG_TRANG_THAI.get(hien_tai, ()):
            return {"status": False, "message": "Chỉ được chuyển theo luồng trạng thái hợp lệ!"}
        ok = self.dao.cap_nhat_trang_thai(order_id, trang_thai_moi)
        if ok:
            return {"status": True, "message": f"Đã chuyển đơn hàng sang: {trang_thai_moi}"}
        return {"status": False, "message": "Không tìm thấy đơn hàng hoặc có lỗi xảy ra!"}
