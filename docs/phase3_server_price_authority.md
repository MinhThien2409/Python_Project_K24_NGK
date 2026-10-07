# Phase 3 — Server-side Price & Checkout Authority

Scope: T154, T127, T128.

## Result

The checkout path now treats ProductId + Quantity as purchase intent. Money and product state are reloaded from the database inside the checkout transaction.

### T154 / T127

DonHangDao.tao_don_hang() now starts the transaction by:

1. collecting all ProductId values;
2. SELECT ... FOR UPDATE from Products;
3. reloading ProductName, Price, Quantity and IsActive;
4. rejecting missing, hidden/inactive or insufficient-stock products;
5. overwriting OrderItem.UnitPrice and OrderItem.TotalPrice;
6. recalculating each order SubTotal and pre-voucher TotalAmount;
7. only then processing the voucher and inserting the order snapshot.

Client-supplied UnitPrice, TotalPrice, SubTotal, DiscountAmount and TotalAmount cannot become the authoritative order values.

The existing voucher path remains server-side: it locks the voucher, reloads eligible product truth, calculates the discount and snapshots the resulting discount/total.

### T128

A product that is no longer active is rejected by the authoritative checkout reload. This check occurs after the transaction starts and before Orders/OrderItems are committed, so hiding a product after it was added to the cart does not permit checkout.

## Regression coverage

New file:

tests/integration/test_phase3_server_price_authority.py

Coverage includes:

- forged money fields are ignored;
- multi-item/multi-shop totals are recalculated;
- current DB price wins over stale client price;
- hidden product is rejected;
- product hidden after cart add is rejected;
- client cannot override stock;
- authoritative DAO query uses FOR UPDATE.

The existing voucher regression suite also continues to cover server-side voucher discount calculation and voucher rollback semantics.

## Runtime verification

Playwright checkout was exercised with a real logged-in customer. A forged request sent:

- UnitPrice = 1
- SubTotal = 1
- DiscountAmount = 999999
- TotalAmount = 2
- ProductName = FAKE

for a real product.

The server returned a successful order total of 145000, not 2. The invoice API then returned:

- UnitPrice = 120000
- TotalPrice = 120000
- SubTotal = 120000
- DiscountAmount = 0
- ShippingFee = 25000
- TotalAmount = 145000

This demonstrates that the order snapshot is server-derived.

## Verification

- Phase 3 targeted tests: PASS
- Full unit/integration suite: 871 passed, 13 failed
- The 13 full-suite failures are the same pre-existing baseline failures from before Phase 3; no new Phase 3 regression was observed.
- node --check static/js/main.js: PASS
- python -m py_compile: PASS
- git diff --check: PASS

## Non-scope

T111/T96 remain Phase 4.
T58/T63 remain Phase 5.
T26 remains Phase 6.
T44–T52 remain Phase 7.
T146–T149 remain Phase 8.
