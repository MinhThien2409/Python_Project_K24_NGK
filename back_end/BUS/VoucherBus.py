from datetime import datetime
from back_end.DAO.VoucherDao import VoucherDao
from back_end.Model.Voucher import Voucher


class VoucherBus:
    def __init__(self):
        self.dao = VoucherDao()

    @staticmethod
    def normalize_code(v):
        return str(v or "").strip().upper()

    @staticmethod
    def _date(v):
        if isinstance(v, datetime):
            return v
        for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
            try:
                return datetime.strptime(str(v or "").strip(), f)
            except ValueError:
                pass
        return None

    @staticmethod
    def _product_ids(values):
        if not isinstance(values, (list, tuple)):
            return None
        result = []
        seen = set()
        for value in values:
            try:
                pid = int(value)
            except (TypeError, ValueError):
                return None
            if pid <= 0:
                return None
            if pid not in seen:
                seen.add(pid)
                result.append(pid)
        return result

    def validate(self, code, name, dtype, value, min_order, max_discount,
                 start, end, quantity, used=None, seller_id=None):
        code = self.normalize_code(code)
        name = str(name or "").strip()
        dtype = str(dtype or "").strip().upper()

        if not code:
            return None, "Mã voucher không được để trống!"
        if len(code) > 50:
            return None, "Mã voucher quá dài!"
        if not name:
            return None, "Tên voucher không được để trống!"
        if len(name) > 150:
            return None, "Tên voucher quá dài!"
        if dtype not in ("PERCENT", "FIXED"):
            return None, "Loại giảm giá không hợp lệ! Chỉ hỗ trợ PERCENT hoặc FIXED."

        try:
            value = float(value)
        except (TypeError, ValueError):
            return None, "Giá trị giảm giá không hợp lệ!"
        if dtype == "PERCENT" and not 0 < value <= 100:
            return None, "Giảm theo phần trăm phải lớn hơn 0 và không quá 100%!"
        if dtype == "FIXED" and value <= 0:
            return None, "Giảm cố định phải lớn hơn 0!"

        try:
            min_order = float(min_order)
        except (TypeError, ValueError):
            return None, "Giá trị đơn tối thiểu không hợp lệ!"
        if min_order < 0:
            return None, "Giá trị đơn tối thiểu không được âm!"

        try:
            max_discount = float(max_discount or 0)
        except (TypeError, ValueError):
            return None, "Giảm tối đa không hợp lệ!"
        if max_discount < 0:
            return None, "Giảm tối đa không được âm!"

        s = self._date(start)
        e = self._date(end)
        if not s or not e:
            return None, "Thời gian hiệu lực không hợp lệ!"
        if s > e:
            return None, "Thời gian bắt đầu phải trước hoặc bằng thời gian kết thúc!"

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return None, "Số lượng voucher không hợp lệ!"
        if quantity < 0:
            return None, "Số lượng voucher không được âm!"

        if used is not None:
            try:
                used = int(used)
            except (TypeError, ValueError):
                return None, "UsedQuantity không hợp lệ!"
            if used < 0 or used > quantity:
                return None, "UsedQuantity phải từ 0 đến Quantity!"

        try:
            seller_id = int(seller_id)
        except (TypeError, ValueError):
            return None, "Seller không hợp lệ!"
        if seller_id <= 0:
            return None, "Seller không hợp lệ!"

        return Voucher(
            SellerId=seller_id,
            Code=code,
            Name=name,
            DiscountType=dtype,
            DiscountValue=value,
            MinOrderValue=min_order,
            MaxDiscount=max_discount,
            StartDate=s,
            EndDate=e,
            Quantity=quantity,
            UsedQuantity=0 if used is None else used,
            IsActive=True
        ), None

    def _check_owner(self, voucher_id, seller_id):
        old = self.dao.lay_theo_id(voucher_id)
        if not old:
            return None, {"status": False, "message": "Không tìm thấy voucher!"}
        if int(old["SellerId"]) != int(seller_id):
            return None, {"status": False, "message": "Bạn không có quyền thao tác trên voucher này!"}
        return old, None

    def kiem_tra_ap_dung(self, code, items):
        code = self.normalize_code(code)
        if not code:
            return {"status": False, "message": "Vui lòng nhập mã voucher!"}
        if not isinstance(items, list) or not items:
            return {"status": False, "message": "Vui lòng chọn sản phẩm để áp dụng voucher!"}

        normalized = []
        for item in items:
            if not isinstance(item, dict):
                return {"status": False, "message": "Thông tin sản phẩm không hợp lệ!"}
            try:
                pid = int(item.get("ProductId"))
                qty = int(item.get("Quantity"))
            except (TypeError, ValueError):
                return {"status": False, "message": "Thông tin sản phẩm không hợp lệ!"}
            if pid <= 0 or qty <= 0:
                return {"status": False, "message": "Số lượng sản phẩm không hợp lệ!"}
            normalized.append((pid, qty))

        v = self.dao.lay_theo_code(code)
        if not v:
            return {"status": False, "message": "Voucher không tồn tại!"}

        now = datetime.now()
        if not v["IsActive"]:
            return {"status": False, "message": "Voucher đã bị vô hiệu hóa!"}
        seller_active_check = getattr(self.dao, "seller_dang_hoat_dong", None)
        if callable(seller_active_check) and not seller_active_check(v["SellerId"]):
            return {"status": False, "message": "Voucher của gian hàng đang bị khóa!"}
        start = self._date(v["StartDate"])
        end = self._date(v["EndDate"])
        if start and now < start:
            return {"status": False, "message": "Voucher chưa bắt đầu!"}
        if end and now > end:
            return {"status": False, "message": "Voucher đã hết hạn!"}
        if v["UsedQuantity"] >= v["Quantity"]:
            return {"status": False, "message": "Voucher đã hết lượt!"}

        ids = [pid for pid, _ in normalized]
        table = self.dao.lay_gia_san_pham_theo_voucher(v["VoucherId"], ids)
        subtotal = 0.0
        eligible_ids = set(table.get("eligible_ids", []))
        for pid, qty in normalized:
            if pid not in eligible_ids:
                continue
            sp = table["products"].get(pid)
            if not sp or not sp["is_active"]:
                return {"status": False, "message": "Sản phẩm không còn kinh doanh!"}
            if qty > sp["quantity"]:
                return {"status": False, "message": "Sản phẩm không đủ tồn kho!"}
            subtotal += sp["price"] * qty

        if subtotal <= 0:
            return {"status": False, "message": "Voucher không áp dụng cho sản phẩm trong giỏ hàng!"}
        if subtotal < v["MinOrderValue"]:
            return {"status": False, "message": "Đơn hàng chưa đạt giá trị tối thiểu để sử dụng Voucher!"}

        if v["DiscountType"] == "PERCENT":
            discount = subtotal * v["DiscountValue"] / 100
            if v["MaxDiscount"] > 0:
                discount = min(discount, v["MaxDiscount"])
        else:
            discount = min(v["DiscountValue"], subtotal)
        discount = max(0.0, min(discount, subtotal))

        return {
            "status": True,
            "message": "Voucher hợp lệ!",
            "data": {
                "Code": v["Code"],
                "SellerId": v["SellerId"],
                "ProductIds": sorted(eligible_ids.intersection(ids)),
                "Subtotal": subtotal,
                "DiscountAmount": discount,
                "MinOrderValue": v["MinOrderValue"]
            }
        }

    def lay_tat_ca(self, seller_id):
        return {"status": True, "data": self.dao.lay_tat_ca(seller_id)}

    def lay_theo_id(self, i, seller_id):
        d, error = self._check_owner(i, seller_id)
        if error:
            return error
        return {"status": True, "data": d}

    def tao(self, seller_id, product_ids, **kw):
        product_ids = self._product_ids(product_ids)
        if not product_ids:
            return {"status": False, "message": "Voucher phải áp dụng ít nhất một Product!"}

        v, e = self.validate(**kw, seller_id=seller_id)
        if e:
            return {"status": False, "message": e}
        if self.dao.code_ton_tai(v.Code):
            return {"status": False, "message": f"Mã voucher '{v.Code}' đã tồn tại!"}

        result = self.dao.them(v, product_ids)
        if result == "invalid_product":
            return {"status": False, "message": "Có Product không tồn tại hoặc không thuộc Seller của Voucher!"}
        if result != "ok":
            return {"status": False, "message": "Không thể tạo voucher!"}
        return {"status": True, "message": "Tạo voucher thành công!"}

    def sua(self, i, seller_id, product_ids, **kw):
        old, error = self._check_owner(i, seller_id)
        if error:
            return error
        product_ids = self._product_ids(product_ids)
        if not product_ids:
            return {"status": False, "message": "Voucher phải áp dụng ít nhất một Product!"}

        v, e = self.validate(**kw, seller_id=seller_id, used=old["UsedQuantity"])
        if e:
            return {"status": False, "message": e}
        if v.Quantity < v.UsedQuantity:
            return {"status": False, "message": "Quantity không được nhỏ hơn UsedQuantity!"}

        v.VoucherId = i
        v.SellerId = old["SellerId"]
        v.IsActive = old["IsActive"]
        if self.dao.code_ton_tai(v.Code, tru_id=i):
            return {"status": False, "message": f"Mã voucher '{v.Code}' đã tồn tại!"}

        result = self.dao.sua(v, product_ids)
        if result == "invalid_product":
            return {"status": False, "message": "Có Product không tồn tại hoặc không thuộc Seller của Voucher!"}
        if result != "ok":
            return {"status": False, "message": "Không thể cập nhật voucher!"}
        return {"status": True, "message": "Cập nhật voucher thành công!"}

    def toggle(self, i, seller_id):
        _, error = self._check_owner(i, seller_id)
        if error:
            return error
        ok = self.dao.toggle(i, seller_id)
        return {"status": ok, "message": "Đã cập nhật trạng thái voucher!" if ok else "Không thể cập nhật trạng thái voucher!"}

    def xoa(self, i, seller_id):
        old, error = self._check_owner(i, seller_id)
        if error:
            return error
        if old["UsedQuantity"] > 0:
            return {"status": False, "message": "Voucher đã được sử dụng, không thể xóa. Hãy vô hiệu hóa voucher."}
        result = self.dao.xoa(i, seller_id)
        return {"status": result == "ok", "message": "Đã xóa voucher!" if result == "ok" else "Không thể xóa voucher!"}
