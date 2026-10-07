# Phase 7 — Seller Lock Effects

## Account → Store
Seller lock updates:
1. Accounts.trang_thai = banned
2. Stores.IsActive = 0
Unlock reverses only those account/store states.

## Product visibility
Public product access is filtered by:
- Product.IsActive = 1
- Store.IsActive = 1
- Seller account status = active
Products are not deleted and are not mass-enabled during unlock.

## Cart and checkout
Existing cart items are retained. Checkout reloads authoritative Product state under row lock and rejects products whose Store or Seller is inactive.

## Voucher
Voucher preview and checkout both require the owning Store and Seller account to be active. Voucher records are not deleted or automatically toggled, preserving their original IsActive state.

## Orders
For the locked Seller's Store:
- Pending → Cancelled
- Confirmed → Cancelled
- Shipping → Cancelled
- Completed → unchanged
- Cancelled → unchanged
Cancellation uses the system flow and restores stock for cancelled orders. Customer notification is best-effort and cannot invalidate the state change.

## UI
The Admin account table reuses the existing Pobby admin-card/table/filter/action components. Seller and Customer rows receive the same lock/reset action pattern already used for Manager accounts; Admin rows remain read-only.