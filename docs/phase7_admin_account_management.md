# Phase 7 — Admin Account Management

## Scope
- Admin can lock/unlock/reset Customer, Seller, Manager.
- Admin cannot operate on Admin accounts.
- Target role is reloaded from DB; request body cannot override it.
- Active-session authorization remains server-side.

## Manager invariant
The DAO locks all active Manager rows in a deterministic order before locking the target Manager. Therefore concurrent Admin attempts cannot reduce active Manager count below one.

## Seller lock
- Account becomes banned.
- Seller Store becomes inactive.
- Public product queries require active Product + active Store + active Seller account.
- Seller vouchers are unusable while the Seller is locked.
- Orders in Pending/Confirmed/Shipping are system-cancelled and stock is restored.
- Completed/Cancelled orders remain unchanged.
- Unlock reactivates the Store but never force-enables products/vouchers that were already inactive.

## Password reset
- Admin reset generates a random temporary password.
- The DAO stores a PBKDF2-SHA256 hash.
- The temporary password is returned once to the UI.
- Reset does not unlock a banned account.
- Login remains backward-compatible with legacy plaintext passwords while accepting PBKDF2 reset passwords.

## Authorization regression
Admin still cannot approve/reject Seller Requests; that permission remains Manager-only.

## Validation
- Phase 7 integration tests.
- Existing account-management regressions.
- Live two-connection Manager concurrency test.
- node --check static/js/main.js.
- python -m py_compile.
- git diff --check.