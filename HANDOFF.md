# 🚀 Snail 백엔드 — 세션 핸드오프 (A4 완료 시점)

> 작성: 2026-05-27 (이전 세션 마지막)
> 새 세션 시작 시 **이 문서 + AGENTS_PLAN.md + SCENARIO_GUIDE.md** 만 읽으면 즉시 작업 이어 가능.
> 다른 문서들은 필요할 때만 참조.

---

## 1. 정체 (한 줄)

**Snail = 무신사 SNAP × 캐치테이블의 네일 특화 MVP.**
사용자(민석)는 1인 백엔드, 8주 데모데이 목표. Python 처음 본격 사용. FastAPI + PostgreSQL + GCP.

## 2. 내 역할

**백엔드 총괄 (Lead).** 직접 코드 수정은 거의 안 한다. 다음 4가지만 한다:
1. **계획** — AGENTS_PLAN.md / TECH_STACK.md / SCENARIO_GUIDE.md / RESERVATION_FLOW.md 같은 문서 작성·갱신
2. **codex 프롬프트 작성** — 각 도메인 에이전트가 cold start로 작업할 수 있는 self-contained 프롬프트
3. **Spot check** — codex 보고 받으면 핵심 위반/누락만 표 형식으로 점검
4. **결정 받기** — 모호한 지점은 AskUserQuestion으로 사용자에게 옵션 제시 후 결정 매트릭스에 기록

사용자가 직접 codex 세션에서 코드 작업. 환경 문제로 막히면 사용자가 보고 → 내가 영구 해결책 또는 즉시 워크어라운드 메시지 제공.

## 3. 사용자 작업 스타일 (반드시 준수)

- **토큰/연산 효율 강조** — cold start 반복 최소화, 검수도 spot check 위주
- **결정은 명확히 받고 진행** — 모호한 채로 진행하지 말 것. AskUserQuestion 적극 활용
- **사용자가 사용자 결정 명확히 한 건 절대 번복하지 말 것** — spec_canonical과 충돌 시 사용자 결정 우선 (한 번 ES 사례에서 실수했음 — 반성)
- **자동 spawn 금지** — Agent 도구로 자체 spawn 안 함. 사용자가 codex로 직접 돌림
- **문서/계획 갱신은 내가 직접, 코드 보완은 codex 미니 패치로 위임**

## 4. 진행 상태 — A0~A4 완료 (93 passed)

| 에이전트 | 도메인 | 상태 | 통과 테스트 (누적) |
|---|---|---|---|
| A0 Platform | 보안/GCS/arq/idempotency/pagination/image/conftest | ✅ | 11 |
| A1 Auth | Apple Sign In + Owner email/PW + 사업자 인증 + 약관 동의 | ✅ | 38 |
| A1-PATCH | TermsAcceptance + Idempotency 정책 변경 | ✅ | 38 |
| A2 Shop+Designer | 샵/영업시간/이미지/디자이너/스케줄/휴무 | ✅ | 50 |
| A3 Community | 스네일/댓글/좋아요/팔로우/리뷰/신고/찜 | ✅ | 70 |
| A4 Design+Search | 디자인 CRUD + pg_trgm+pgvector 검색 + 시너님 사전 | ✅ | 93 |
| A5 Reservation | 가용시간 + 상태머신 + payment_pending 흐름 + reservation-stats | ✅ | 151 |
| A6 LLM Pipeline | semaphore/tenacity/cache/usage + processed_image 인터페이스 + reanalyze | ✅ | 161 |
| A7 Notification | 카카오 Bizppurio + FCM/APNs + 사장님 인박스 + 9 trigger 본구현 | ✅ | 170 |
| A8 QA | e2e 13개 + seed 500 디자인 + demo_reset (prod 가드) | ✅ | **183** |
| **백엔드 MVP API** | **🎉 100% 완성** | ✅ | **183** |

**현재 alembic head**: `20260527_1200` (initial_extensions → initial_schema → user_oauth_identities → terms_acceptances → design_search_indexes)

## 5. 7가지 결정 매트릭스 (사용자 확정 — 절대 번복 금지)

`AGENTS_PLAN.md §11` 원본. 요약:

| # | 항목 | 결정 |
|---|---|---|
| 1 | payment_pending 상태 + bank_snapshot | **유지** — 사장님이 입금 확인 후 confirm. PG 결제만 미구현 |
| 2 | 노쇼/취소 누적 카운터 (User 컬럼) | **MVP 제외, 단 이력 조회 API 허용 (B안)** — User 컬럼 금지. `GET /me/reservation-stats`로 reservations COUNT만 |
| 3 | UserBlock 차단 기능 | **MVP 이후, App Store 심사 직전 (W7) 추가** |
| 4 | TermsAcceptance 약관 동의 이력 | **추가 완료** (A1-PATCH) |
| 5 | 이미지 자동 모더레이션 | **신고만** — OpenAI Moderation API 호출 금지 |
| 6 | 푸시 알림 카테고리 on/off | **전체 on/off만** (UserDeviceToken.is_active). 프론트 SETTINGS-01 카테고리 토글 → 1개로 축소 |
| 7 | Idempotency 비인증 정책 | **쓰기 부수효과 있는 것만 필수** — signup/password-reset 필수, login/refresh 면제 |
| 8 | 스네일 비등록 샵 태그 | **불허, FK 유지** — 비등록 샵은 캡션 텍스트로만 |
| 9 | 디자인 이미지 모드 (AI ↔ 원본) | **users.image_view_mode enum 추가** — `{model, wear}`, 클라가 NULL 폴백, A1 미니 패치 + A6 transform 본구현 |

**대기 중인 결정** (프론트/팀장 피드백 대기):
1. 지도/거리 검색 — 도입 여부
2. 추천 알고리즘 — 단순 인기순 vs 개인화
3. 이달의 아트 영역 — 다시 추가할지
4. 샵 영업시간 휴게시간 — 별도 모델 vs 디자이너 휴게로 갈음

이 4개는 A5 진행에 영향 거의 없음 (피드백 후 작은 변경으로 대응 가능).

## 6. 다음 액션 (즉시 실행 가능)

1. **A5 Reservation Agent codex 프롬프트** — 이전 세션 마지막 메시지에 풀로 작성되어 있음 (사용자가 보관). 못 찾으면 새로 작성 — AGENTS_PLAN.md §A5 본문 + 결정 매트릭스 + RESERVATION_FLOW.md 참조해서 만들면 됨
2. A5 완료 보고 받으면 spot check → A6 LLM → A7 Notification → A8 QA 순
3. 프론트/팀장 피드백 도착하면 **`IMPACT_ANALYSIS.md` 절차 따라** §11 갱신 + 영향받는 도메인 patch

## 7. 검증 명령 (반드시 이것만 쓰기)

```powershell
cd backend
.\scripts\check.ps1            # ruff + format + mypy + alembic + pytest 한 번에
.\scripts\check.ps1 -SkipDb    # DB 없이 정적 검사만
.\scripts\check.ps1 -Only ruff # 특정 단계
```

스크립트가 자동 처리:
- `.venv\Scripts` PATH 추가 (ruff/mypy/alembic 그냥 명령어로 동작)
- `DATABASE_URL=...?ssl=disable` 주입 — **Windows 한글 경로 `C:\Users\신민석` 에서 asyncpg가 시스템 SSL cert 자동 탐색 실패** 우회
- ENV / REDIS_URL / JWT_SECRET 기본값 주입

**금지**: 개별로 `ruff check .` 따로 돌리거나 환경변수 매번 다르게 export하지 말 것. `.\scripts\check.ps1` 한 번이 표준.

## 8. 핵심 코딩 규약 (모든 codex 프롬프트에 포함)

- **에러**: `raise AppError("CODE", "한국어 메시지", HTTPStatus.XXX)` — HTTPException 직접 사용 절대 금지
- **인증**: `Depends(current_user_id)` / `Depends(current_owner_id)` 사용
- **DB**: `Depends(db_session)` — SQLAlchemy 2 async, 동기 호출 금지
- **시간**: 모든 datetime은 `timezone-aware UTC`, 직렬화는 ISO8601
- **로깅**: `structlog.get_logger()` 만 사용, print 금지, 민감정보 (PW/토큰/raw_payload) 절대 로깅 금지
- **Idempotency**: 모든 POST/PATCH/DELETE 라우터에 `Idempotency-Key` 헤더 필수. 비인증 API 중 login/refresh만 면제 (결정 #7)
  - `app/api/v1/_idempotency.py`의 `required_idempotency_key` + `with_idempotency` context 사용
- **에러 envelope**: `app/schemas/common.py`의 `ErrorResponse` (자동 처리됨)
- **페이지네이션**: cursor 기반 (`app/utils/pagination.py`)
- **모델 변경 원칙**: 도메인 에이전트는 `app/models/*` 수정 금지. 단 A4의 `designs.embedding` 추가처럼 도메인 핵심 필드는 예외 허용 (마이그레이션 동반 필수)

## 9. 도메인 모델 — 35개 테이블 + Vector 확장

| 영역 | 테이블 |
|---|---|
| Accounts | users, user_oauth_identities, user_device_tokens, owners, business_verifications, password_reset_tokens, terms_acceptances |
| Shop | shops, shop_images, shop_business_hours, designers, designer_schedules, designer_time_offs |
| Design | designs (+ embedding vector(1536) IVFFlat), design_images, design_designers, llm_jobs |
| Reservation | reservations, idempotency_keys |
| Community | snaps, snap_images, snap_likes, comments, comment_likes, user_follows, favorite_designs |
| Review/Report | reviews, review_images, review_replies, reports |
| Notification | owner_notifications, notification_deliveries |
| Ops | upload_objects |

## 10. 주요 문서 인덱스

| 파일 | 용도 | 권한 |
|---|---|---|
| **AGENTS_PLAN.md** | 에이전트 구획, 결정 매트릭스, 조정 규칙 | 내가 직접 갱신 |
| **IMPACT_ANALYSIS.md** | 기능 수정·추가 요청 들어왔을 때 표준 검토 절차 (4단계 + 5분류) | 내가 직접 갱신 |
| **TECH_STACK.md** | 스택 결정 근거, 8주 일정, NOT in MVP | 내가 직접 갱신 |
| **SCENARIO_GUIDE.md** | 프론트/팀장 공유용 시나리오 매트릭스 | 내가 직접 갱신 |
| **W0_CHECKLIST.md** | 사용자가 해야 할 외부 셋업 진행도 체크리스트 | 내가 직접 갱신 |
| **W0_GUIDE.md** | W0 스텝-바이-스텝 실행 매뉴얼 (명령어/링크/트러블슈팅) | 내가 직접 갱신 |
| **backend/docs/RESERVATION_FLOW.md** | A5가 따를 예약 흐름 진리 | 내가 직접 갱신 |
| **backend/docs/ARCHITECTURE.md** | 런타임/모듈 경계 | codex가 갱신 가능 |
| **backend/docs/DB_SCHEMA.md** | 스키마 + 노출 가드 4종 | codex가 갱신 가능 |
| **spec_canonical/backend_spec_v3.canonical.json** | 원래 명세서 (legacy, 사용자 결정과 충돌 시 사용자 결정 우선) | 갱신 신중 |
| **legal/{privacy_policy,terms_of_service}.draft.md** | 약관 초안 (placeholder 사용자가 채울 것) | 사용자 |
| **backend/scripts/check.ps1** | 단일 검증 스크립트 | 거의 변경 안 함 |

## 11. 환경 / 인프라

| 항목 | 상태 |
|---|---|
| 사용자 OS | Windows 11 (PowerShell 7), 한글 사용자 경로 `C:\Users\신민석` |
| Docker Desktop | ✅ 설치되어 있음 (A3 통합 테스트가 PG 사용 성공) |
| 로컬 컨테이너 | `docker compose -f docker/docker-compose.yml up -d postgres redis` (pgvector/pgvector:pg16 + redis 7) |
| GCP 셋업 | 🔴 W0_CHECKLIST.md 참고. 사용자 진행 중 |
| Apple Developer | 🔴 사용자 진행 |
| 카카오 알림톡 | 🔴 사용자 진행 (사업자등록 → 발신프로필 심사 5~10영업일) |
| OpenAI | 🔴 사용자 진행 (Tier-1 진입) |

## 12. 이전 세션에서 학습한 트랩 (반복 금지)

1. **사용자 결정과 spec_canonical 충돌 시 사용자 결정 우선** — ES 도입을 spec_canonical 따라 끌고 가서 다시 회귀해야 했음. 이제 SSOT는 `AGENTS_PLAN.md §11 결정 매트릭스`
2. **Windows 한글 경로 asyncpg SSL 우회** — `.\scripts\check.ps1` + `.env.example`의 `?ssl=disable` 로 해결. 새 에이전트마다 같은 함정 안 빠지게
3. **codex가 `ruff` PATH를 못 찾음** — venv 활성 안 됨. `.\scripts\check.ps1`이 PATH 자동 추가
4. **`payment_pending` 흐름 오해** — 결제 없는 MVP라고 해서 payment_pending까지 제거하면 안 됨. 사장님 입금 확인 흐름은 유지 (결정 #1)
5. **A4 Design+Search 시작 전 search_service 회귀** — ES 코드 다 빼고 placeholder 만들어둔 상태에서 A4가 본구현. 다음에도 정리 → 구현 분리 패턴 유지

## 13. 새 세션 시작 첫 메시지 권장 패턴

사용자가 새 세션 열면 이렇게 시작:

```
[HANDOFF.md] 읽고 이어 작업. A5 Reservation Agent 프롬프트부터 시작하자.
```

또는 사용자가 codex에서 A5 진행 결과를 가져와서:

```
A5 결과: [보고 붙여넣기]
```

내가 할 일:
1. HANDOFF.md + AGENTS_PLAN.md §11 + §A5 + RESERVATION_FLOW.md 빠르게 훑기
2. A5 프롬프트 제공 (없으면 새로 작성) 또는 보고 spot check
3. 통과 시 A6 → A7 → A8 순

## 14. 미해결 / TODO

- [x] ~~프론트/팀장 피드백 도착 시 §11에 4개 결정 추가~~ ✅ 2026-05-28 완료 (#10~#20 추가)
- [x] ~~A5 Reservation 진행~~ ✅ 2026-05-28 완료 (151 passed, +58)
- [x] ~~A6 LLM Pipeline~~ ✅ 2026-05-28 완료 (161 passed, +10)
- [x] ~~A7 Notification~~ ✅ 2026-05-28 완료 (170 passed, +9)
- [x] ~~A8 QA~~ ✅ 2026-05-28 완료 (183 passed, +13 e2e)
- [x] ~~`GET /me/reservation-stats`~~ ✅ 이미 라우터 등록됨 (`backend/app/api/v1/reservations.py:157`)
- [x] ~~`DesignPublic` original_url + processed_url 노출~~ ✅ 확인됨 (`backend/app/schemas/designs.py:41-42`)
- [x] ~~`Snap` 모델 tagged_design_id/shop_id/designer_id 컬럼 + SnapCreate/SnapPublic 노출~~ ✅ 확인됨

### 14.1 A9 패치 묶음 — §11 #10~#20 반영 (작은 것부터)

> 검증 명령: `.\scripts\check.ps1` 한 줄. 각 묶음은 독립 commit/PR 가능.

- [ ] **A9-Patch-A** (XS, 즉시) — SnapFeedQuery 필터 + 리뷰 7일 제약 + popularity_score 1차 변경
  - `SnapFeedQuery`에 `tagged_design_id/shop_id/designer_id: UUID | None` 필드 + 서비스 분기 (DESIGN-01/SHOP-01 섹션 지원)
  - 신규 인덱스 2개: `snaps(tagged_design_id, created_at DESC)`, `snaps(tagged_shop_id, created_at DESC)`
  - `review_service.update_review/delete_review`에 `created_at > now - 7d` 가드 추가, 위반 시 `AppError("REVIEW_EDIT_WINDOW_CLOSED", ..., 403)`
  - `snail_service.py:186` popularity 식을 `(like_count + 2*comment_count) / pow(extract(epoch from now() - created_at)/3600 + 2, 1.5)` ORDER BY로 변경 (save는 A9-Patch-B에서 추가)
- [ ] **A9-Patch-B** (S) — SnapSave 모델 + 저장 토글 API + popularity 최종
  - `SnapSave(user_id, snap_id)` 모델 + 마이그 + 라우터 `POST/DELETE /snails/{id}/save`
  - `Snap.save_count` 컬럼 + 트리거 또는 서비스 카운터
  - popularity 식에 `+ 3*save_count` 추가
- [ ] **A9-Patch-C** (M) — users.image_view_mode enum (결정 #9)
  - 마이그: `users.image_view_mode VARCHAR(10) NOT NULL DEFAULT 'model'` + CHECK in ('model','wear')
  - `UserMe/UserUpdate` 스키마 + `PATCH /me` 처리
- [ ] **A9-Patch-D** (S~M) — 지도 + 위치 태그 (결정 #10, #11)
  - `shops.location_tags TEXT[]` 컬럼 + GIN 인덱스 + 마이그
  - 서울 시드 큐레이션 리스트 상수(`app/services/location_tags.py`): 홍대/성수/강남/명동/이태원 등
  - `GET /shops?bbox=...` 라우터 + 검색 필터 `location_tag` 파라미터
- [ ] **A9-Patch-E** (L, 마지막) — 시술 옵션 도메인 (결정 #12, #13)
  - `DesignOption` 모델 신규 + 마이그
  - 사장님 라우터: `POST/PATCH/DELETE /owner/designs/{id}/options`
  - `Reservation.selected_option_ids JSONB` + 가격·시간 스냅샷
  - `availability_service`: `options` 파라미터로 duration 합산 후 슬롯 재계산
  - `ReservationCreate`에 `selected_option_ids` 추가

### 14.2 미해결 — 결정 보류 또는 일정 이슈

- [ ] W0_CHECKLIST 외부 셋업 — 리드타임 긴 것 (카카오 알림톡 심사) 사용자 진행 중
- [ ] App Store 심사 직전 UserBlock 추가 (W7 마일스톤)
- [ ] MVP 범위 보류 — 피드백 받고 결정:
  - FavoriteShop 모델 (SHOP-01 ♡, SAVE-01 샵 탭)
  - 저장 폴더 (SAVE-01 폴더 탭)
  - 리뷰 별점 분포 집계 API (REVIEW-02)
