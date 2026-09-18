Dự án hiện nay có các chỗ cần chỉnh sửa như sau, có thể lập nhiều specs nếu cần thiết. Chia thành các plan để dễ bám sát.
Bạn được toàn quyền chỉnh sửa và thay đổi mã nguồn. Không được phép tạo các hàm chuẩn hóa riêng biệt.
# Chung
- Khắc phục lỗi hiển thị hình ảnh sản phẩm (nếu trong thư mục có sẵn hình ảnh, nếu không có bỏ qua công việc này).
- Trong database, thực hiện chia tách table `user`. `Username`, `Password`, `Role_ID`, `trang_thai` sẽ nằm ở table riêng. Điều này nhằm tách riêng thông tin tài khoản và thông tin đăng nhập.
- Các tài khoản có vai trò đặc biệt như `Admin` với `Role_ID` = 1, `Quản lý` với `Role_ID` = 2 và `Seller` với `Role_ID` = 3 không cần chức năng chọn Chế độ xem và Quay lại trang mua sắm. Do đó hãy xóa bỏ 2 chức năng này đi.
- Xóa bỏ các chức năng dư thừa mà tôi không đề cập đến của từng vai trò `Role_ID`. Các vai trò chỉ được phép truy cập đến chức năng mà tôi đề cập dưới đây:

## Admin
- Chỉ có chức năng Quản lý xem danh sách Người bán/khách hàng/quản lý.
- Thêm, xoá, sửa người quản lý.

## Quản lý
- Có các chức năng Quản lý danh mục sản phẩm chung, Xét duyệt người bán hàng, Khoá tài khoản vi phạm, Cấp lại mật khẩu.


## Người bán
- Có chức năng Quản lý sản phẩm đang bán, Quản lý đơn hàng, Quản lý nhập hàng, Xem thống kê, Chỉnh sửa trang người bán, Quản lý giá bán

## Khách hàng
- Có chức năng Tìm kiếm và xem sản phẩm, Thêm xoá sửa giỏ hàng, Thanh toán, Xem hoá đơn, Xem lịch sử mua, Chỉnh sửa thông tin cá nhân và mật khẩu.

- Khi thực hiện đăng nhập và đăng xuất hoàn tất, hãy reload lại trang để tải giao diện mới và chuyển hướng về trang chủ. Đảm bảo xóa toàn bộ thông tin đăng nhập cũ khi đăng xuất.
- Ở các vai trò `Admin`, `Quản lý`, `Seller`, các chức năng xem danh sách bất kì đều sẽ có bộ lọc tùy chỉnh nằm phía trên list, dạng dropdown. Nếu có nhiều bộ lọc thì xếp chúng nằm cùng hàng, nếu quá nhiều có thể xuống dòng nhưng đảm bảo thẳng hàng, thẳng cột.

# Seller
- Thực hiện sửa đổi giao diện, thiết kế tương tự trang `Admin` và `Quản lý`.
- Chức năng chỉnh sửa trang shop sẽ được tách riêng. Không nằm trong tab Tổng quan gian hàng.
- Chức năng chỉnh sửa giá sẽ được tách riêng. Không nằm trong tab Sản phẩm.

# Khách hàng
- Hiện tại giỏ hàng đang có ràng buộc chỉ mua từ 1 shop duy nhất, hãy xóa bỏ ràng buộc này và cho phép mua từ nhiều shop khác nhau. Sửa đổi chức năng Hóa đơn, Mua hàng, Thanh toán và các chức năng có liên quan cho phù hợp.
- Chức năng `Xác nhận Đặt hàng ngay` đang báo lỗi hệ thống bận, hãy chỉnh sửa. Biết luồng hoạt động mua hàng tôi dự tính như sau:
Khách hàng chọn sản phẩm muốn thêm vào giỏ hàng (có thể chọn nhiều, từ nhiều shop) --> Khách hàng mở giỏ hàng và chọn các sản phẩm muốn thanh toán --> Khách hàng bấm nút `Tiến hành đặt hàng & Thanh toán` --> Hệ thống hiển thị `Thông tin đặt hàng & Thanh toán` --> Khách hàng bấm nút `Xác nhận Đặt hàng ngay` --> Hệ thống chuyển sang giao diện Xem lại hóa đơn mua hàng.
- Giao diện hiển thị số lượng sản phẩm trong giỏ hàng hiển thị `NaN` hãy chỉnh sửa.