# -*- coding: utf-8 -*-
"""POJO Hồ sơ người dùng — ánh xạ bảng `Users` (008-split-user-table).

SAU khi tách bảng, `Users` chỉ còn hồ sơ con người: `UserId`, `FullName`,
`Address`, `Phone`, `NationalId`. Thông tin đăng nhập (`Username`, `Password`,
`Role_Id`, `trang_thai`) đã chuyển sang bảng `Accounts`
(`back_end/Model/TaiKhoan.py`).
"""


class User:
    """Hồ sơ người dùng (bảng `Users`) — KHÔNG chứa thông tin đăng nhập.

    Args:
        ma_user: `UserId` — khoá chính, khoá ngoại cho Stores/Orders/Carts/...
        ma_nhom_quyen: **Trường đọc từ JOIN** — cột `Role_Id` nằm ở bảng
            `Accounts` (xem data-model.md mục 2/4), KHÔNG phải cột của `Users`.
            `_nap_thong_tin_dang_nhap` gán giá trị từ `Accounts.Role_Id` qua
            JOIN để giữ nguyên khóa JSON cho tầng BUS.
        ten_user: `FullName` — hồ sơ.
        dia_chi: `Address` — hồ sơ.
        sdt: `Phone` — hồ sơ.
        cmnd: `NationalId` — hồ sơ.
        tendangnhap, mat_khau: Các tham số **tạm/thừa kế**: được giữ ở `__init__`
            CHỈ cho tầng ghi (`UserDao.them_user` cần chúng để chèn `Accounts`
            trong cùng giao dịch) và tương thích với dữ liệu test. Nguồn dữ liệu
            thật nằm ở bảng `Accounts` / lớp `TaiKhoan`.
    """

    def __init__(self, ma_user=None, ma_nhom_quyen=2, ten_user=None, dia_chi=None, sdt=None, cmnd=None, tendangnhap=None, mat_khau=None):
        """Khởi tạo hồ sơ người dùng với mã, tên và vai trò (đọc từ JOIN)."""
        self.ma_user = ma_user
        self.ma_nhom_quyen = ma_nhom_quyen
        self.ten_user = ten_user
        self.dia_chi = dia_chi
        self.sdt = sdt
        self.cmnd = cmnd
        # Tạm/thừa kế — chỉ dùng cho tầng ghi `UserDao.them_user` và test cũ.
        self.tendangnhap = tendangnhap
        self.mat_khau = mat_khau