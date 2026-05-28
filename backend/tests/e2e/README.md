# A8 E2E Scenarios

Run:

```powershell
pytest tests/e2e -m e2e -v
```

| File | Cross-domain flow | Spec mapping | Decision matrix |
|---|---|---|---|
| `test_owner_full_onboarding.py` | Owner signup, business verification, shop/designer/schedule, design creation, mocked LLM analysis, user Apple Sign In, search discovery | §9, §10, §1, §2 | #7 signup idempotency, #9 processed_url remains nullable |
| `test_reservation_full_flow.py` | Search, design detail, availability, reservation request, owner inbox/notification enqueue, accept, complete, review | §2, §3, §4, §7, §11 | #1 on_site confirmed flow |
| `test_reservation_concurrency.py` | Concurrent reservation POSTs against the same locked slot; exactly one success and one owner notification enqueue | §4, §5 | #1 slot lock statuses |
| `test_idempotency_e2e.py` | Reservation create/cancel idempotency and auth idempotency boundary; demo reset prod guard | §4 | #7 signup required, login exempt |
| `test_state_machine_paths.py` | Reject, user cancel, shop cancel, complete/review, bank-transfer payment confirmation, no-show | §4, §5, §6, §7, §11 | #1 payment_pending branches, #2 stats covered by existing API, #3 no block scenario |
| `test_natural_language_search.py` | Korean natural-language tag search with public exposure guards | §2, §3, §10 | #5 no auto moderation, #9 processed_url not asserted |

Notes:

- These tests intentionally cover only flows that cross domain boundaries.
- Domain-level validation and unit/integration behavior remain covered by A0-A7 tests.
- External APIs are not called. LLM, notification enqueue, Apple Sign In, and storage inputs are mocked or inserted as test data.
