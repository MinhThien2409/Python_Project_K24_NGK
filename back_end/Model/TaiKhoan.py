# -*- coding: utf-8 -*-
"""POJO Tài khoản đăng nhập — ánh xạ bảng `Accounts` (008-split-user-table).

Chứa TOÀN BỘ thông tin đăng nhập sau khi tách bảng User: `Username`,
`Password`, `Role_Id`, `trang_thai` (xem data-model.md mục 4). Hồ sơ con người
(`ten_user`, `dia_chi`, `sdt`, `cmnd`) thuộc `back_end/Model/User.py`, KHÔNG
nằm trong lớp này — giữ cho hai bảng tách bạch ở tầng model.
"""


class TaiKhoan:
    """Tài khoản đăng nhập (bảng `Accounts`).

    Args:
        ma_tai_khoan: Khoá chính `AccountId` (None trước khi ghi CSDL).
        ma_user: `UserId` — quan hệ 1-1 với hồ sơ `Users` (UNIQUE).
        tendangnhap: `Username` — khoá tự nhiên, duy nhất toàn hệ thống.
        mat_khau: `Password` — mật khẩu đăng nhập.
        ma_nhom_quyen: `Role_Id` — vai trò (1/2/3/4), NULL cho phép role_none.
        trang_thai: `trang_thai` — 'active' | 'banned' (mặc định 'active').
    """

    def __init__(self, ma_tai_khoan=None, ma_user=None, tendangnhap="",
                 mat_khau="", ma_nhom_quyen=None, trang_thai="active"):
        """Khởi tạo tài khoản đăng nhập với các trường của bảng `Accounts`."""
        self.ma_tai_khoan = ma_tai_khoan
        self.ma_user = ma_user
        self.tendangnhap = tendangnhap
        self.mat_khau = mat_khau
        self.ma_nhom_quyen = ma_nhom_quyen
        self.trang_thai = trang_thai if trang_thai else "active"