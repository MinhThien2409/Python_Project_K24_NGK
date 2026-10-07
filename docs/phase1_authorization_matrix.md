# Phase 1 — Server-side Authorization Matrix (T150)

## Identity rule

Protected APIs derive the acting identity from Flask session user_id, then reload the user/role from the server-side user source. Client-supplied UserId, Role, Role_Id, SellerId, or StoreId must not be used to elevate identity.

## Matrix

| API group | Authentication | Required role | Resource ownership | Status |
|---|---|---|---|---|
| GET /api/users | Yes | Admin / Quản lý | N/A | PASS |
| POST /api/cap-nhat-profile | Yes + active | Any active user | Self | PASS |
| POST /api/doi-mat-khau | Yes + active | Any active user | Self | PASS |
| GET /api/stores/by-user/<id> | Yes + active | Any active user | Self | HARDENED in Phase 1 |
| GET /api/seller-requests | Yes + active | Quản lý | N/A | PASS |
| POST /api/duyet-seller/<id> | Yes + active | Quản lý | Request resource | PASS |
| POST /api/tu-choi-seller/<id> | Yes + active | Quản lý | Request resource | PASS |
| Category POST/PUT/DELETE | Yes + active | Quản lý | N/A | PASS |
| Seller product/inventory/price APIs | Yes + active | Seller | Server-derived StoreId | PASS |
| Seller voucher CRUD/toggle | Yes + active | Seller | Server-derived StoreId | PASS |
| Seller order/statistics/shop APIs | Yes + active | Seller | Server-derived StoreId | PASS |
| PUT /api/users/<id>/status | Yes + active | Admin / Quản lý | Target rules in BUS | HARDENED in Phase 1 |
| POST /api/cap-lai-mat-khau | Yes + active | Admin / Quản lý | Target rules in BUS | HARDENED in Phase 1 |
| Customer cart/order/notification APIs | Yes + active | Authenticated user | Session-derived user | PASS |

## Phase 1 changes

1. Added _active_user() in app.py as a shared active-session guard.
2. Hardened /api/stores/by-user/<user_id> so an authenticated user can only resolve their own store.
3. Applied the active-session guard before account status and password-reset operations.
4. Added regression tests covering authentication, role gates, banned sessions, forged role/identity fields, and store ownership.

## Verification

- Phase 1 authorization tests: 13 passed.
- Playwright runtime:
  - anonymous store lookup: 403;
  - Seller forged Role=Admin against account-status API: 403;
  - Seller own store lookup: 200;
  - Seller other-user store lookup: 403.
- python -m py_compile app.py tests/integration/test_phase1_server_authorization.py: PASS.
- node --check static/js/main.js: PASS.
- git diff --check: PASS.

## Known baseline failures outside Phase 1

The existing integration/unit suite currently has 13 failures unrelated to the Phase 1 authorization changes, including legacy fake-cart DAO interfaces and pre-existing static/JS assertions. They are not modified by Phase 1.
