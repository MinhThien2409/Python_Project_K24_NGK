# Changelog — Cleanup Phases

## Phase 0 — Baseline / Freeze
Thiết lập baseline và nguyên tắc bảo vệ thay đổi.

## Phase 1 — Inventory / Architecture / DB
Inventory codebase, architecture và database; xác định layer và database sources.

## Phase 2 — Database Canonicalization
Thiết lập canonical schema_mysql.sql, seed_demo_mysql.sql và database_mysql.sql. Giữ import_mysql.bat làm tooling và fix_utf8mb4.sql làm recovery utility.

## Phase 3 — Legacy SQL Cleanup
Loại active source set: Database/sql/, Database/sql_thien/SQL_data.sql, Database/sql_thien/SqlAll.sql, Database/database.sql, Database/back_up.sql.

## Phase 4 — Test Alignment / Regression
Căn chỉnh tests theo current behavior. Regression verified: 619 passed, 0 failed, 0 errors.

## Phase 5 — Python Code Cleanup
Loại import không dùng, chuyển một số print() exception logging sang logger và rà soát resource management, SQL parameterization, layer boundaries.

## Phase 6 — Decision Resolution
- SECRET_KEY fallback: giữ nguyên.
- DB password fallback: giữ nguyên.
- debug=True: giữ nguyên.
- ShippingFee: giữ nguyên current behavior; không thêm Admin shipping configuration.
- Seller statistics: fallback từ hardcoded 2026 sang datetime.now().year.
- Client truyền year vẫn được dùng.

Regression sau Phase 6: 619 passed, 0 failed, 0 errors. Compileall PASS; git diff --check PASS.

## Phase 7 — Documentation Reconstruction + Legacy Closure
- Tái dựng documentation từ current implementation, tests, canonical database và configuration.
- Người dùng xác nhận xóa các artifact tài liệu obsolete: BRD_TRD_REPORT.md, BRD_TRD_REPORT_PLAN.md, Git_Tutorial.txt, todos.md, PPTX BRD/TRD và docs/Test_docs.xlsx.
- Reconcile `tests/unit/test_us3_tai_lieu_khop_pham_vi.py`: loại 2 test phụ thuộc BRD obsolete và 1 test phụ thuộc contract `specs/007-project-cleanup/contracts/cleanup-contract.md` không còn tồn tại. Không weaken assertion và không thay đổi production behavior.
- Regression cuối Phase 7: 617 passed, 0 failed, 0 errors.
- Compileall PASS; git diff --check PASS.
