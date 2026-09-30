# Testing

## Current regression
Đã verify:
    617 passed
    0 failed
    0 errors

## Test suite
    tests/
      unit/
      integration/

Chạy toàn bộ:
    pytest

Theo nhóm:
    pytest tests/unit/
    pytest tests/integration/

## Verification
    python -m compileall -q app.py back_end
    git diff --check

Compileall và git diff --check đã PASS trong Phase 7 final validation.

## Regression policy
Khi production code thay đổi, chạy regression sau mỗi logical batch. Không sửa tests chỉ để che failure; phải phân biệt stale test và regression trước khi quyết định thay đổi contract.

## Coverage
Không đưa coverage percentage vì Phase 7 không đo coverage.
