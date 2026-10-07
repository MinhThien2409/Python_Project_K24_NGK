# Phase 5 — T58 + T63

## T58 — Duplicate Seller Request

Seller registration tiếp tục lấy UserId từ session ở API, không tin UserId client.

Tại DAO, gui_yeu_cau_ban_hang() khóa row Users tương ứng bằng SELECT ... FOR UPDATE trước khi kiểm tra Seller và Pending request. Vì cùng UserId phải tranh chấp cùng row lock, hai request đồng thời không thể cùng vượt qua kiểm tra Pending.

Rule hiện tại được giữ nguyên: request Rejected có thể đăng ký lại; request Pending bị từ chối; tài khoản đã là Seller bị từ chối.

## T63 — Approve concurrency

Duyệt SellerRequest được thực hiện trong một transaction. _khoa_don_cho_duyet() dùng SELECT ... FOR UPDATE trên SellerRequests, kiểm tra Status sau khi lấy lock, rồi update Status=approved. Transaction chỉ commit sau khi tạo Store và nâng Role_Id.

Do đó hai DB connections cùng approve một RequestId chỉ có một transaction nhìn thấy Pending; transaction còn lại chờ lock, đọc trạng thái đã xử lý và trả da_xu_ly. Side effects Store/Role nằm trong cùng transaction với trạng thái request.

Từ chối SellerRequest cũng được harden bằng SELECT ... FOR UPDATE để approve/reject không thể cùng chuyển một Pending request sang hai trạng thái.

## Live verification

Test dùng MySQL thật và DAO tự mở hai DB connections riêng qua ThreadPoolExecutor. Không dùng mock DB cho T63.

Scenarios:

- hai connection approve cùng một request: 1 ok + 1 da_xu_ly;
- kiểm tra DB cuối: đúng 1 Store và Role_Id=3;
- approve lại request đã approved: da_xu_ly;
- concurrent submit cùng UserId khi không có Pending: 1 ok + 1 da_co_pending;
- duplicate Pending server-side: da_co_pending;
- rejected request vẫn có thể đăng ký lại được covered by existing seller registration regression;
- reject sau approve: da_xu_ly.

## Tests

- tests/integration/test_phase5_seller_request_concurrency.py
- tests/integration/test_seller_registration_phase5.py

## Verification

Phase 5 targeted + existing seller registration: PASS.

Full suite được chạy sau implementation; các failure baseline sẽ được phân loại riêng, không đánh đồng với regression của Phase 5.
