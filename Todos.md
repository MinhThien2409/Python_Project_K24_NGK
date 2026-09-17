Dự án hiện nay có các chỗ cần chỉnh sửa như sau, có thể lập nhiều specs nếu cần thiết. Chia thành các plan để dễ bám sát
# Chung
- Loại bỏ chức năng đánh giá và các UI liên quan
- Bổ sung vai trò người Quản lý với các chức năng Quản lý danh mục sản phẩm chung, Xét duyệt người bán hàng, Khóa tài khoản vi phạm, Cấp lại mật khẩu
- Chỉnh sửa để mỗi tài khoản chỉ có một vai trò duy nhất trong 4 vai trò sau Admin, Người bán hàng, Người mua hàng, Người quản lý. Các chức năng của từng vai trò sẽ được trình bày dưới đây

# Admin
- Là tài khoản có quyền admin duy nhất
- Có chức năng duy nhất cấp tài khoản có vai trò Quản lý và xóa sửa

# Quản lý
- Có các chức năng Quản lý danh mục sản phẩm chung, Xét duyệt người bán hàng, Khóa tài khoản vi phạm, Cấp lại mật khẩu

# Người bán
- Có chức năng Quản lý sản phẩm của shop đang bán, Quản lý đơn hàng, Quản lý nhập hàng, Xem thống kê, Chỉnh sửa trang người bán (tên shop, giới thiệu shop, thâm niên), Quản lý giá bán

# Khách hàng
- Có chức năng Tìm kiếm và xem sản phẩm, Thêm xóa sửa giỏ hàng, Thanh toán, Xem hóa đơn (sau khi thanh toán hoàn tất và khi xem chi tiết lịch sử mua), Xem lịch sử mua (có hiển thị tình trạng đơn hàng), Chỉnh sửa thông tin các nhân và mật khẩu

# Xóa bỏ các phần dư thừa trong dự án, tái cấu trúc và chuẩn hóa

Hãy lập các specs để từ từ triển khai các phần trên