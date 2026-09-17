# Feature Specification: Tái cấu trúc vai trò — 4 vai trò duy nhất (Admin, Quản lý, Người bán, Khách hàng)

**Feature Branch**: `001-role-refactor`

**Created**: 2026-09-17

**Status**: Draft

**Input**: User description: "Chỉnh sửa để mỗi tài khoản chỉ có một vai trò duy nhất trong 4 vai trò sau Admin, Người bán hàng, Người mua hàng, Người quản lý. Các chức năng của từng vai trò sẽ được trình bày ở các spec riêng. Đây là spec nền tảng: chuẩn hóa bảng vai trò, gán đúng vai trò cho dữ liệu mẫu, và loại bỏ hệ thống phân quyền ngoại lệ (Permissions/Modules) không còn dùng."

## Hiến chương ràng buộc (Constitution Constraints)

Mọi spec cho dự án Pobby PHẢI tôn trọng Hiến chương Pobby v1.0.0. Các ràng buộc bắt buộc:

- **Nguyên tắc I**: chức năng phải phân bổ được vào Model / DAO / BUS / Controller.
- **Nguyên tắc II**: nếu spec có yêu cầu giao diện, PHẢI nêu rõ dùng lại component và biến
  CSS nào trong `static/css/style.css`; KHÔNG được đề xuất thêm framework UI mới.
- **Nguyên tắc III**: yêu cầu phải diễn đạt được bằng code dễ đọc cho mục đích học tập.
- **Nguyên tắc IV**: mỗi yêu cầu chức năng PHẢI kèm tiêu chí kiểm thử được (đây là đồ án
  môn Kiểm thử phần mềm — test là bắt buộc, không phải tùy chọn).
- **Nguyên tắc V**: nếu chạm tới dữ liệu người dùng/đơn hàng, PHẢI nêu yêu cầu bảo mật.
- **Nguyên tắc VI**: mọi yêu cầu PHẢI nằm trong phạm vi đã ghi ở `BRD_TRD_REPORT.md` mục 1.3.

Nếu một yêu cầu không thể tuân thủ hiến chương, ghi rõ trong mục **Assumptions** kèm lý do.

## Clarifications

### Session 2026-09-17

- Q: User có Role_Id NULL hoặc trỏ tới vai trò không tồn tại thì hệ thống xử lý thế nào? → A: Rà soát database, xóa dữ liệu không phù hợp chuẩn hóa; dữ liệu mới phải phù hợp chuẩn hóa.
- Q: Quy tắc gán Seller — tất cả user sở hữu gian hàng hay chỉ user 2,3,4? → A: Xóa bỏ dữ liệu cũ, tạo SQL dữ liệu mẫu mới.
- Q: Tên vai trò Quản lý trong CSDL — giữ Manager hay đổi Quản lý? → A: Xóa bỏ dữ liệu cũ, tạo SQL dữ liệu mẫu mới (tên chuẩn chốt trong dữ liệu mẫu mới).
- Q: API quản lý vai trò sau chuẩn hóa giữ lại những gì? → A: C - Xóa toàn bộ API roles.
- Q: Tài khoản Admin duy nhất bị khóa nhầm thì khôi phục thế nào? → A: Không ai có quyền khóa Admin; xóa dữ liệu cũ, tạo SQL dữ liệu mẫu mới; thay đổi cấu trúc database nếu cần.

### Session 2026-09-17 (điều chỉnh hướng triển khai)

- Q: Chuẩn hóa vai trò được thực hiện bằng cách nào? → A: **Sửa đổi trực tiếp trên mã nguồn hiện có** — không tạo hàm riêng để chuẩn hóa, không tạo SQL script riêng để chuẩn hóa. Các file nguồn `Database/database.sql`, `Database/back_up.sql` và code được chỉnh sửa thẳng để kết quả chuẩn hóa nằm ngay trong file (4 vai trò chuẩn, user được gán đúng vai trò, bảng `Permissions`/`Modules` biến mất), thay vì cung cấp một script chạy lúc runtime.
- Hệ quả: FR-003/FR-004/FR-009 được thỏa mãn bằng file gốc đã được chỉnh trực tiếp (idempotent theo nghĩa nạp lại `database.sql` luôn cho 4 vai trò chuẩn), không còn sản phẩm bàn giao "script chuẩn hóa". Kiểm thử chuyển sang kiểm tra trực tiếp nội dung `database.sql`/`back_up.sql` + hành vi code.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Chuẩn hóa 4 vai trò duy nhất (Priority: P1)

Là quản trị viên hệ thống, tôi muốn bảng vai trò chỉ còn đúng 4 vai trò chuẩn — **Admin**, **Quản lý**, **Seller**, **Customer** — để mỗi tài khoản trong hệ thống luôn gắn với đúng một vai trò rõ ràng, không còn các vai trò thừa (Kế toán, Marketing, VIP, Shipper...) gây nhiễu khi phân quyền và kiểm thử.

**Why this priority**: Đây là nền móng cho mọi spec tiếp theo (phân bổ chức năng theo vai trò). Không chuẩn hóa vai trò thì không thể chốt "ai được làm gì" cho các story sau.

**Independent Test**: Có thể kiểm tra độc lập bằng cách truy vấn danh sách vai trò sau khi chạy script chuẩn hóa — chỉ còn đúng 4 dòng với tên chuẩn, và mọi user đều trỏ tới một trong 4 vai trò này.

**Acceptance Scenarios**:

1. **Given** CSDL đang có 20 vai trò thừa, **When** chạy script chuẩn hóa vai trò, **Then** bảng vai trò chỉ còn đúng 4 dòng: Admin, Quản lý, Seller, Customer.
2. **Given** script đã chạy, **When** truy vấn mọi user, **Then** mỗi user có `Role_Id` trỏ tới một trong 4 vai trò chuẩn, không có user nào trỏ tới vai trò đã xóa.
3. **Given** CSDL cũ có user mang vai trò thừa (ví dụ "Kế toán"), **When** script chuẩn hóa chạy, **Then** dữ liệu cũ không phù hợp bị xóa và dữ liệu mẫu mới chỉ chứa user gắn với 4 vai trò chuẩn.

---

### User Story 2 - Gán đúng vai trò cho dữ liệu mẫu (Priority: P1)

Là sinh viên kiểm thử, tôi muốn dữ liệu mẫu được xây dựng mới hoàn toàn phù hợp với mô hình 4 vai trò — user1 là Admin, các user đang sở hữu gian hàng là Seller, phần còn lại là Customer — để các kịch bản kiểm thử theo vai trò có dữ liệu đầu vào đáng tin cậy.

**Why this priority**: Test case theo vai trò cần dữ liệu mẫu đúng ngay từ đầu; sai dữ liệu sẽ làm mọi test phân quyền cho kết quả nhiễu.

**Independent Test**: Có thể kiểm tra độc lập bằng cách đối chiếu từng user với danh sách gian hàng hiện có: user sở hữu `Stores` phải là Seller, user1 phải là Admin, còn lại là Customer.

**Acceptance Scenarios**:

1. **Given** SQL dữ liệu mẫu mới, **When** nạp dữ liệu, **Then** user1 (Nguyễn Văn An) có vai trò Admin.
2. **Given** SQL dữ liệu mẫu mới, **When** nạp dữ liệu, **Then** các user sở hữu gian hàng trong bảng `Stores` có vai trò Seller.
3. **Given** SQL dữ liệu mẫu mới, **When** nạp dữ liệu, **Then** các user còn lại không sở hữu gian hàng có vai trò Customer.

---

### User Story 3 - Loại bỏ hệ thống phân quyền ngoại lệ (Priority: P2)

Là sinh viên phát triển, tôi muốn loại bỏ hoàn toàn cơ chế phân quyền ngoại lệ (bảng `Permissions`, `Modules`, các endpoint cấp quyền ngoài lệ/nhóm, UI quản lý quyền chi tiết) vì mô hình mới chỉ dùng 4 vai trò cố định — giữ lại sẽ gây nhầm lẫn và tăng khối lượng kiểm thử không cần thiết.

**Why this priority**: Không chặn được chức năng nào của 4 vai trò mới, nhưng phải dọn trước khi viết các spec phân quyền theo vai trò để tránh code chết.

**Independent Test**: Có thể kiểm tra độc lập bằng cách gọi các endpoint quyền ngoại lệ cũ (phải trả về lỗi "không tồn tại") và tìm kiếm trong mã nguồn — không còn tham chiếu tới `Permissions`/`Modules`/`cap-quyen-ngoai-le`.

**Acceptance Scenarios**:

1. **Given** hệ thống đang có endpoint `/api/cap-quyen-ngoai-le`, `/api/cap-quyen-nhom`, `/api/quyen-cua-user/<id>`, `/api/quyen-cua-nhom/<id>`, `/api/ap-dung-quyen-nhom-cho-user`, **When** tái cấu trúc xong, **Then** các endpoint này không còn tồn tại (trả về 404).
2. **Given** mã nguồn hiện có `PhanQuyenBus`/`PhanQuyenDao` với các hàm phân quyền ngoại lệ và quản lý vai trò, **When** dọn dẹp xong, **Then** toàn bộ các hàm này bị xóa (không giữ lại hàm nào, vì đã xóa toàn bộ API roles).
3. **Given** giao diện đang có UI quản lý quyền chi tiết (ma trận xem/thêm/sửa/xóa), **When** dọn dẹp xong, **Then** UI này bị loại bỏ khỏi `templates/index.html` và `static/js/main.js`.

---

### User Story 4 - Kiểm tra đăng nhập theo vai trò mới (Priority: P2)

Là người dùng, khi tôi đăng nhập, hệ thống phải nhận diện đúng vai trò duy nhất của tôi và trả về cho giao diện để hiển thị đúng bộ chức năng tương ứng (Admin/Quản lý/Seller/Customer).

**Why this priority**: Đăng nhập là cổng vào của mọi luồng; nếu vai trò trả về sai thì mọi màn hình sau đó sai theo.

**Independent Test**: Đăng nhập lần lượt bằng tài khoản mẫu của từng vai trò và kiểm tra trường vai trò trong phản hồi JSON khớp với vai trò đã gán trong CSDL.

**Acceptance Scenarios**:

1. **Given** user1 có vai trò Admin, **When** đăng nhập bằng user1, **Then** phản hồi đăng nhập chứa vai trò "Admin".
2. **Given** user2 có vai trò Seller, **When** đăng nhập bằng user2, **Then** phản hồi đăng nhập chứa vai trò "Seller".
3. **Given** user5 có vai trò Customer, **When** đăng nhập bằng user5, **Then** phản hồi đăng nhập chứa vai trò "Customer".
4. **Given** một tài khoản bị khóa (banned), **When** đăng nhập, **Then** hệ thống từ chối với thông báo tài khoản đã bị khóa (hành vi hiện có được giữ nguyên).

### Edge Cases

- Một user có `Role_Id` NULL hoặc trỏ tới vai trò không tồn tại → script chuẩn hóa PHẢI rà soát và xóa/gán lại toàn bộ dữ liệu không phù hợp (không để sót bản ghi vi phạm sau khi chạy); dữ liệu tạo mới sau này PHẢI được validate chỉ chấp nhận 4 vai trò chuẩn, không được crash.
- Hai user trùng tên đăng nhập khi gán lại vai trò → script gán vai trò phải chạy theo `UserId`, không theo tên.
- User đang là Seller nhưng gian hàng bị vô hiệu hóa (`IsActive = 0`) → vẫn giữ vai trò Seller (vai trò không tự đổi theo trạng thái gian hàng).
- Xóa vai trò đang được user tham chiếu → không còn API xóa vai trò (đã xóa toàn bộ API roles); 4 vai trò chuẩn chỉ tồn tại trong SQL dữ liệu mẫu.
- Tài khoản Admin không thể bị khóa bởi bất kỳ ai (không có quyền khóa Admin); nếu cần thay đổi cấu trúc database (ví dụ: constraint chống khóa Admin) thì thực hiện trong script chuẩn hóa.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST chỉ còn đúng 4 vai trò trong bảng vai trò: Admin, Quản lý, Seller, Customer; mọi vai trò khác PHẢI bị xóa.
- **FR-002**: Hệ thống MUST đảm bảo mỗi tài khoản chỉ gắn với đúng một vai trò duy nhất (một giá trị `Role_Id` trên mỗi user).
- **FR-003**: Hệ thống MUST cung cấp script chuẩn hóa (trong `Database/`) chuyển đổi dữ liệu cũ sang 4 vai trò mới, chạy được nhiều lần mà không gây lỗi (idempotent).
- **FR-004**: Script chuẩn hóa MUST xóa bỏ dữ liệu mẫu cũ không phù hợp và tạo mới SQL dữ liệu mẫu theo quy tắc: user1 → Admin; user sở hữu gian hàng → Seller; còn lại → Customer.
- **FR-005**: Hệ thống MUST xóa toàn bộ API quản lý vai trò (không còn endpoint tạo/sửa/xóa/gán vai trò qua API); 4 vai trò chuẩn chỉ được tạo bởi SQL dữ liệu mẫu, không thể thay đổi lúc runtime.
- **FR-006**: Hệ thống MUST loại bỏ các endpoint phân quyền ngoại lệ (`/api/cap-quyen-ngoai-le`, `/api/cap-quyen-nhom`, `/api/quyen-cua-user/<id>`, `/api/quyen-cua-nhom/<id>`, `/api/ap-dung-quyen-nhom-cho-user`), toàn bộ endpoint quản lý vai trò (`/api/roles`, `/api/users/<id>/role`) và toàn bộ hàm BUS/DAO liên quan (`PhanQuyenBus`/`PhanQuyenDao` bị xóa hoàn toàn).
- **FR-007**: Hệ thống MUST loại bỏ UI quản lý quyền chi tiết (ma trận xem/thêm/sửa/xóa) khỏi giao diện.
- **FR-008**: Phản hồi đăng nhập MUST chứa vai trò duy nhất của tài khoản để giao diện phân nhánh hiển thị.
- **FR-009**: Script chuẩn hóa MUST rà soát và xóa/gán lại toàn bộ user có `Role_Id` NULL hoặc không hợp lệ (không để sót bản ghi vi phạm); mọi thao tác tạo mới/gán vai trò sau này MUST validate chỉ chấp nhận 4 vai trò chuẩn (không crash, có hành vi xác định).
- **FR-010**: Mọi thay đổi schema PHẢI kèm script cập nhật trong `Database/` và cập nhật `database.sql` + `back_up.sql` đồng bộ.
- **FR-011**: Mỗi yêu cầu trên PHẢI có test: unit test tầng BUS cho validate vai trò, integration test cho endpoint đăng nhập, và test ca biên (Role_Id NULL, vai trò không tồn tại, endpoint roles/quyền cũ trả về 404).

### Key Entities *(include if feature involves data)*

- **Role (Vai trò)**: đại diện một vai trò hệ thống; thuộc tính: mã vai trò, tên vai trò. Chỉ tồn tại 4 dòng chuẩn: Admin, Quản lý, Seller, Customer. Không thể xóa 4 dòng này.
- **User (Người dùng)**: người dùng hệ thống; thuộc tính hiện có: mã user, họ tên, địa chỉ, SĐT, CMND, tên đăng nhập, mật khẩu, mã vai trò. Mỗi user có đúng một mã vai trò. Không ai có quyền khóa tài khoản Admin (quy tắc nghiệp vụ); nếu cần, script chuẩn hóa thay đổi cấu trúc database để thực thi quy tắc này. (Cột trạng thái khóa tài khoản sẽ được bổ sung ở spec Quản lý.)
- **Store (Gian hàng)**: gian hàng của người bán; dùng làm căn cứ xác định user nào là Seller khi chuẩn hóa dữ liệu.
- **Permission / Module (Phân quyền ngoại lệ)**: cơ chế cũ (ma trận xem/thêm/sửa/xóa theo module) — bị loại bỏ hoàn toàn khỏi schema, code và UI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Sau chuẩn hóa, bảng vai trò chứa đúng 4 dòng và 100% user có `Role_Id` hợp lệ trỏ tới một trong 4 vai trò đó.
- **SC-002**: 100% endpoint phân quyền ngoại lệ và quản lý vai trò cũ bị loại bỏ (gọi lại trả về 404) và 0 tham chiếu `cap-quyen-ngoai-le`/`Permissions`/`Roles API` còn sót trong mã nguồn backend.
- **SC-003**: Đăng nhập bằng tài khoản mẫu của từng vai trò trả về đúng vai trò trong 100% trường hợp (4/4 vai trò).
- **SC-004**: Toàn bộ test mới (unit + integration + ca biên) chạy PASS; không test nào cũ bị đỏ do thay đổi này.
- **SC-005**: Giao diện sau dọn dẹp không còn màn hình quản lý quyền chi tiết; ba giao diện Customer/Seller/Admin vẫn hiển thị đúng như trước (không hồi quy UI).

## Assumptions

- Quy tắc chuyển đổi vai trò cho dữ liệu cũ: user sở hữu gian hàng → Seller; user1 (Nguyễn Văn An) → Admin; mọi user khác → Customer. Nếu cần gán ai đó làm Quản lý, sẽ làm thủ công sau khi chuẩn hóa (spec Quản lý sẽ mô tả cách Admin tạo tài khoản Quản lý).
- 4 vai trò chuẩn dùng tên thống nhất trong SQL dữ liệu mẫu mới (dữ liệu cũ bị xóa bỏ hoàn toàn); tên hiển thị tiếng Việt xử lý ở tầng giao diện.
- Bảng `Permissions` và `Modules` bị xóa khỏi schema; script xóa phải chạy sau khi code không còn tham chiếu.
- Việc khóa tài khoản (banned) hiện được lưu ở đâu đó ngoài bảng Users (theo code `UserBus`); spec này giữ nguyên cơ chế hiện tại, việc bổ sung cột trạng thái chính thức thuộc spec Quản lý.
- Mật khẩu vẫn plaintext trong giai đoạn này; việc băm mật khẩu là nợ kỹ thuật đã ghi nhận trong hiến chương, xử lý ở spec riêng (Cấp lại mật khẩu của Quản lý sẽ chạm tới vấn đề này).
- Phạm vi tuân thủ `BRD_TRD_REPORT.md` mục 1.3: BR23 (Role & Permission) được đơn giản hóa còn 4 vai trò cố định — đây là quyết định nghiệp vụ có chủ đích của đồ án, ghi nhận tại đây thay vì mở rộng phạm vi.
