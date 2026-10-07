# Phase 2 ? Ownership + XSS Hardening

## Scope
- T139: ownership is checked before status for seller order status changes.
- T73/T153: server-controlled text rendered into HTML is escaped with `escHtml()`.

## T139
`DonHangBus.cap_nhat_trang_thai_cua_seller()` now checks `don_thuoc_store(order_id, store_id)` before reading `Status`. A foreign order therefore returns an ownership error without exposing whether the order is Pending/Completed/Cancelled.

## XSS
`static/js/main.js` uses the existing `escHtml()` encoder for high-risk server text in seller orders, shop information, profile attributes, voucher fields, invoices, order history, notifications, admin messages and product emoji/text render paths. The encoder covers `&`, `<`, `>`, `"` and `'`.

## Verification
- Phase 2 security regression: PASS.
- Seller order regression: PASS.
- Product image regression: PASS.
- `node --check static/js/main.js`: PASS.
- `python -m py_compile`: PASS.
- `git diff --check`: PASS.
- Playwright runtime: `escHtml()` encoded script/img payloads without executable HTML.

## Known baseline failures
The full unit/integration suite still contains the previously known cart fake-DAO interface failures and SQL-dialect/static assertions. These are unrelated to Phase 2. The Python Playwright package is unavailable in the current environment, so the repository's pytest UI collection cannot run; browser verification was performed through Playwright MCP.
