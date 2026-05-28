# 예약 상태 흐름 (MVP 확정안)

> 사용자 결정 #1 (AGENTS_PLAN.md §11): 백엔드는 실제 PG 결제를 매개하지 않지만, 사장님이 예약금 입금을 확인 후 승인하는 플로우는 유지한다.
> A5 Reservation Agent는 이 문서를 기준으로 구현한다.

---

## 1. 두 가지 결제 모드

| Shop.payment_method | 의미 | 흐름 |
|---|---|---|
| `on_site` | 시술 당일 현장 결제 | 예약금 안내 없음. 수락 → 즉시 confirmed |
| `bank_transfer_guide` | 사장님 계좌로 예약금 입금 (사장님이 수동 확인) | 수락 → payment_pending → 사장님이 입금 확인 후 confirmed |

**제약**: `Shop.auto_accept=true` 인 경우 반드시 `payment_method=on_site` (사장님이 자동 수락하면 입금 확인 단계가 없으므로). `reservation_policy.validate_shop_payment_policy`가 이미 강제함.

---

## 2. 상태 전이 다이어그램

### 2.1 on_site 샵

```
유저 예약 요청
   ↓
pending
   ↓ (사장님 수락 또는 auto_accept=true)
confirmed
   ↓ (시술 완료 시점에 사장님이 액션)
completed
```

분기 (어디서든 가능):
- `pending` → `rejected` (사장님 거절)
- `pending` → `cancelled_by_user` (유저 취소)
- `confirmed` → `cancelled_by_user` / `cancelled_by_shop`
- `confirmed` → `no_show` (시작 30분 후부터 사장님 액션 가능)

### 2.2 bank_transfer_guide 샵

```
유저 예약 요청
   ↓
pending
   ↓ (사장님 수락)
payment_pending
   ↓ (사장님이 입금 확인 후 confirm-payment 액션)
confirmed
   ↓ (시술 완료)
completed
```

분기:
- `pending` / `payment_pending` → `rejected` / `cancelled_by_user` / `cancelled_by_shop` 동일

---

## 3. 수락 시점 스냅샷 (snapshot)

사장님이 수락하는 순간 다음을 `Reservation`에 스냅샷한다 (이후 Shop 정책이 바뀌어도 이 예약에는 영향 없음).

| 필드 | 소스 |
|---|---|
| `payment_method_snapshot` | `Shop.payment_method` |
| `deposit_amount_snapshot` | `Shop.deposit_amount` (on_site면 NULL) |
| `bank_snapshot` | `{ "bank_name", "account_number", "account_holder" }` JSONB (on_site면 NULL) |
| `reservation_policy_snapshot` | `Shop.reservation_policy` (취소/노쇼 안내 문구) |

---

## 4. 슬롯 점유 (exclusion constraint)

| 상태 | 디자이너 슬롯 잠금 | 사유 |
|---|---|---|
| `pending` | ❌ | 같은 슬롯에 여러 pending 가능 (먼저 수락된 1건만 confirmed) |
| `payment_pending` | ✅ | 사장님이 수락한 시점부터 슬롯 보장 |
| `confirmed` | ✅ | |
| 기타 (rejected/cancelled/no_show/completed) | ❌ | |

PostgreSQL exclusion constraint:
```sql
EXCLUDE USING gist (
    designer_id WITH =,
    tstzrange(start_at, end_at, '[)') WITH &&
)
WHERE (status IN ('payment_pending', 'confirmed'))
```

유저 활성 예약 중복 차단 (한 유저가 겹치는 시간에 여러 예약 못 잡음):
```sql
EXCLUDE USING gist (
    user_id WITH =,
    tstzrange(start_at, end_at, '[)') WITH &&
)
WHERE (status IN ('pending', 'payment_pending', 'confirmed'))
```

이미 `services/reservation_policy.py`의 `SLOT_LOCK_STATUSES`, `ACTIVE_USER_RESERVATION_STATUSES`에 정의됨.

---

## 5. 사장님 라우터 액션

| 액션 | 시작 상태 | 종료 상태 | 비고 |
|---|---|---|---|
| `POST /shops/me/reservations/{id}/accept` | pending | on_site → confirmed / bank_transfer_guide → payment_pending | 스냅샷 작성 |
| `POST /shops/me/reservations/{id}/confirm-payment` | payment_pending | confirmed | bank_transfer_guide만, 사장님이 입금 확인 후 |
| `POST /shops/me/reservations/{id}/reject` | pending | rejected | rejected_reason 필수 |
| `POST /shops/me/reservations/{id}/cancel` | confirmed | cancelled_by_shop | cancelled_reason 필수 |
| `POST /shops/me/reservations/{id}/no-show` | confirmed | no_show | 시작 30분 후부터 가능 |
| `POST /shops/me/reservations/{id}/complete` | confirmed | completed | 시술 완료 표시, 유저 리뷰 작성 가능해짐 |

## 6. 유저 라우터 액션

| 액션 | 시작 상태 | 종료 상태 |
|---|---|---|
| `POST /reservations` | (생성) | pending 또는 즉시 confirmed (auto_accept=true & on_site) |
| `POST /me/reservations/{id}/cancel` | pending / payment_pending / confirmed | cancelled_by_user |

> `payment_pending` 단계에서 유저는 입금을 진행하지만, 별도 백엔드 API 없음 — 사장님 확인이 다음 단계 트리거.

---

## 7. 알림 트리거 (A7 Notification Agent 참고)

| 이벤트 | 받는 사람 | 채널 | 템플릿 키 |
|---|---|---|---|
| 예약 생성 | 사장님 | 카카오 알림톡 + inbox | RESERVATION_REQUESTED |
| 수락 (on_site) | 유저 | APNs | RESERVATION_CONFIRMED |
| 수락 (bank_transfer_guide → payment_pending) | 유저 | APNs | RESERVATION_PAYMENT_REQUIRED (입금 안내 + bank_snapshot 포함) |
| 입금 확인 (payment_pending → confirmed) | 유저 | APNs | RESERVATION_CONFIRMED |
| 거절 | 유저 | APNs | RESERVATION_REJECTED |
| 사장님 취소 | 유저 | APNs | RESERVATION_CANCELLED_BY_SHOP |
| 시술 전날/당일 | 유저 | APNs | RESERVATION_REMINDER |

---

## 8. MVP에서 의도적으로 제외 (결정 #2)

- 노쇼/취소 누적 카운터 (User 컬럼) — **추가 금지**
- 노쇼 반복 시 경고 문구
- 노쇼 반복 시 예약 요청 제한
- 잦은 취소 시 안내

필요 시 `SELECT COUNT(*) FROM reservations WHERE user_id=? AND status='no_show'` 같이 ad-hoc 집계로 갈음.
