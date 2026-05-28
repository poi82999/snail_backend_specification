# 🧑‍✈️ 백엔드 하위 에이전트 운영 계획 (MVP)

> 총괄: Claude (백엔드 리드)
> 실행: 도메인별 하위 에이전트 8개
> 대상 완성도: MVP — 데모데이 시연 가능한 백엔드 API

---

## 1. 진단 결과 (요약)

- ✅ **모델/마이그레이션/Enums/인프라**는 거의 완성. 새 테이블을 만들 일 거의 없음 → 충돌 위험 ↓
- 🔴 **서비스 + API 라우터 + 워커**가 비어있음 → 도메인별로 채우면 됨
- 🟡 **공통 플랫폼 일부** (Apple Sign In, GCS, arq job, idempotency)는 모든 도메인이 의존 → 선행 필요

---

## 2. MVP 범위 매트릭스

`spec_canonical/user_scenarios_v3_mvp.txt` 기준으로 도메인을 7개로 분리한다.

| 도메인 | 사용자 시나리오 | 책임 |
|---|---|---|
| Auth & Identity | §1, §9 | Apple Sign In(유저), 이메일/PW(사장님), 사업자 인증 제출, 프로필 |
| Shop & Designer | §9 | 1샵 등록, 영업시간, 디자이너, 스케줄, 휴무 |
| Design & Search | §2, §3, §10 | 디자인 CRUD, ES 검색, 디자인 상세, 찜 |
| Reservation | §4, §5, §6, §11 | 가용시간 계산, 예약 생성, 상태 전이, idempotency, 충돌 방지 |
| LLM Pipeline | §10 | OpenAI Vision (Transform→Classify), 임베딩, ES 재인덱싱 트리거 |
| Notification | §4, §11 | 카카오 알림톡, APNs, 사장님 알림함, 발송 이력 |
| Community | §7, §8, §11.12 | 스네일, 댓글/좋아요/팔로우, 리뷰, 신고 |

어드민(§12)은 MVP에서 별도 라우터 없이 SQL 직접 작업 → 에이전트 제외.

---

## 3. 에이전트 구획 (8개)

### Wave 0 — 단독 실행
| # | 에이전트 | 역할 |
|---|---|---|
| **A0** | **Platform Agent** | 공통 인프라/유틸 (Apple Sign In, GCS, arq, idempotency, request_id, 페이지네이션 유틸, 공용 테스트 픽스처) |

### Wave 1 — Platform 완료 후 병렬
| # | 에이전트 | 역할 |
|---|---|---|
| **A1** | **Auth & Identity Agent** | `routers/auth.py`, `users.py`, `owners.py` + 인증/프로필 서비스 |
| **A2** | **Shop & Designer Agent** | `routers/shops.py`, `designers.py` + 샵/디자이너/스케줄 서비스 |
| **A3** | **Community Agent** | `routers/snails.py`, `comments.py`, `reviews.py`, `reports.py` + 서비스 |

### Wave 2 — Auth+Shop 완료 후
| # | 에이전트 | 역할 |
|---|---|---|
| **A4** | **Design & Search Agent** | `routers/designs.py`, `search.py` + 디자인 CRUD, ES 검색 쿼리 |

### Wave 3 — Design 완료 후
| # | 에이전트 | 역할 |
|---|---|---|
| **A5** | **Reservation Agent** | `routers/reservations.py` + 가용시간/생성/상태전이/충돌 |
| **A6** | **LLM Pipeline Agent** | `services/llm_service.py`, `workers/llm_pipeline.py` + 프롬프트 |

### Wave 4 — Reservation+LLM 완료 후
| # | 에이전트 | 역할 |
|---|---|---|
| **A7** | **Notification Agent** | `services/notification_service.py`, `kakao_client.py`, `apns_client.py`, `workers/notification_sender.py`, `routers/notifications.py` |

### Wave 5 — 전체 완료 후
| # | 에이전트 | 역할 |
|---|---|---|
| **A8** | **QA & Integration Agent** | e2e 시나리오, 통합 테스트, seed 스크립트, 데모 데이터 |

---

## 4. 의존성 그래프

```
A0 Platform
  │
  ├── A1 Auth ─────┬── A2 Shop ──── A4 Design+Search ──┬── A5 Reservation ──┐
  │                │                                    │                    │
  │                │                                    └── A6 LLM ──────────┤
  │                │                                                         │
  └── A3 Community ─────────────────────────────────────────────────────────┤
                                                                             │
                                                       A7 Notification ──────┤
                                                                             │
                                                              A8 QA ─────────┘
```

**병렬 가능 조합**:
- A1 + A2 + A3 (Platform 완료 후)
- A5 + A6 (Design 완료 후)
- A8은 마지막 단독

---

## 5. 충돌 방지 / 조정 규칙

### 5.1 파일 소유권
- **각 에이전트는 자신이 소유한 도메인 외 파일 수정 금지**
- 공통 파일(`app/main.py`, `app/api/v1/__init__.py`, `app/core/*`)은 **Platform Agent만 수정**. 다른 에이전트는 라우터 등록이 필요할 때 명시적 보고 후 Platform이 패치
- `app/models/*.py`는 **수정 금지** (모델은 이미 확정). 새 컬럼이 정말 필요하면 보고
- `alembic/versions/*` — 새 마이그레이션이 필요한 에이전트만 새 파일 생성, 절대 기존 파일 수정 X

### 5.2 마이그레이션 룰
- 기존 `0001_initial_extensions` + `0900_initial_schema` 체인을 변경 금지
- 새 마이그레이션 파일명: `YYYYMMDD_HHMM_<slug>.py`, 반드시 down_revision 명시
- 보고 없이 만든 마이그레이션은 머지 거절

### 5.3 라우터 등록
- 각 도메인 라우터는 `app/api/v1/<domain>.py`에 정의
- `app/api/v1/__init__.py` 등록은 **Platform이 일괄 처리** (PR 머지 시 Platform이 한 줄 추가)
- 임시로 직접 등록해야 하면 명확히 보고

### 5.4 공통 규약 (모든 에이전트)
- **에러**: `raise AppError("CODE", "메시지", HTTPStatus.XXX)` 만 사용 (직접 HTTPException 금지)
- **인증**: `Depends(current_user_id)` / `Depends(current_owner_id)` 사용
- **DB 세션**: `Depends(db_session)` 사용, 트랜잭션은 서비스 레이어에서 명시적 관리
- **로깅**: `structlog.get_logger()` 만 사용
- **시간**: 모든 datetime은 `timezone-aware (UTC)`, 직렬화는 ISO8601
- **에러 응답 envelope**: `app/schemas/common.py`의 `ErrorResponse` 사용
- **페이지네이션**: cursor 기반 (Platform Agent가 제공할 유틸 사용)
- **Idempotency**: **모든 POST/PATCH/DELETE 라우터에 `Idempotency-Key` 헤더 필수** (없으면 400). `app/utils/idempotency.py`의 dependency 사용. GET/HEAD/OPTIONS는 면제. 예외 필요 시 리드에 보고
- **OAuth Identity**: 신규 SNS 로그인은 `users.apple_sub` 컬럼이 아니라 별도 `user_oauth_identities(user_id, provider, provider_sub, email)` 테이블 사용 (A1이 도입)

### 5.5 코드 품질 게이트 (DoD)
모든 에이전트의 PR이 머지되려면:
1. `ruff check .` 통과
2. `ruff format --check .` 통과
3. `mypy app` 통과
4. `alembic upgrade head` 후 `alembic downgrade -1 && upgrade head` 무사 통과
5. 추가한 서비스/라우터에 대한 단위 테스트 ≥ 1개
6. 통합 테스트 (실제 PG/Redis) ≥ 1개 (CRUD라면 happy path 1개)

### 5.5.1 검증 실행 — 항상 이 한 줄만 쓴다
```powershell
.\scripts\check.ps1
```
이 스크립트가 자동 처리:
- `.venv\Scripts` 를 PATH에 추가 → ruff/mypy/alembic/pytest 그냥 명령어로 동작
- `DATABASE_URL=...?ssl=disable` 주입 → Windows 한글 사용자 경로(asyncpg SSL 자동탐색 버그) 회피
- 표준 ENV/REDIS_URL/JWT_SECRET 주입

**금지**: 개별로 `ruff check .` 만 따로 돌리거나, 환경변수를 매번 다른 값으로 export하지 말 것. `.\scripts\check.ps1` 한 번이 표준.

DB 없는 정적 검사만: `.\scripts\check.ps1 -SkipDb`
특정 단계만: `.\scripts\check.ps1 -Only ruff`

### 5.6 보고 프로토콜
각 에이전트는 작업 완료 시 다음 형식으로 리포트:
```
## 완료 작업
- ...

## 변경 파일
- ...

## 새 마이그레이션
- (없음 / 파일명)

## 라우터 등록 요청
- app/api/v1/__init__.py에 추가 필요: include_router(xxx_router)

## 블로커 / 가정
- ...

## 테스트 결과
- ruff/mypy/pytest 결과
```

---

## 6. 에이전트별 초기 프롬프트

> 각 에이전트는 cold start이므로 프롬프트가 self-contained여야 한다.
> 공통 헤더와 도메인별 본문으로 구성한다.

### 6.0 공통 헤더 템플릿 (모든 에이전트에 prepend)

```
당신은 Snail (네일 예약 + 커뮤니티 MVP) 백엔드 도메인 에이전트입니다.
백엔드 리드(나)가 부여한 도메인 범위만 작업합니다. 다른 도메인은 건드리지 마세요.

[필수 사전 읽기]
- /TECH_STACK.md (스택 전반)
- /AGENTS_PLAN.md §5 조정 규칙 (절대 위반 금지)
- /spec_canonical/user_scenarios_v3_mvp.txt (도메인 비즈니스 규칙)
- /backend/app/api/errors.py (AppError 사용법)
- /backend/app/api/deps.py (current_user_id / current_owner_id)
- /backend/app/models/enums.py (모든 상태 enum)
- /backend/app/models/__init__.py + 본인 도메인 모델 파일

[금지사항]
- 본인 도메인 외 파일 수정 금지
- app/models/*.py 수정 금지 (모델은 확정)
- 기존 마이그레이션 수정 금지
- app/main.py, app/api/v1/__init__.py 수정 금지 (라우터 등록은 보고)
- HTTPException 직접 사용 금지 → AppError 사용
- print() 금지 → structlog 사용
- 동기 DB 호출 금지 → asyncpg / SQLAlchemy async

[DoD]
- ruff check . / ruff format --check . / mypy app 전부 통과
- 추가 코드의 단위 테스트 + 통합 테스트 각 1개 이상
- 작업 완료 시 §5.6 보고 양식대로 리포트
```

---

### A0. Platform Agent

```
역할: Snail 백엔드의 공통 플랫폼 유틸을 구축합니다.
다른 모든 에이전트가 이 결과물을 의존합니다.

[현재 상태]
- app/core/{config,database,redis,search,security,logging}.py 존재
- app/core/security.py는 decode_token만 있음. Apple Sign In, owner password 해싱 미구현
- app/api/errors.py, deps.py, middleware.py 존재 (request_id 등)
- app/workers/settings.py 존재 (arq settings) — 실제 worker 엔트리는 없음
- app/schemas/common.py에 ErrorBody/ErrorResponse만

[작업 범위]
1. app/core/security.py 확장
   - Apple Sign In id_token 검증 (Apple JWKS fetch + 캐싱, RS256, audience/issuer 검증)
   - Owner 비밀번호 해싱 (passlib bcrypt)
   - JWT 발급 함수 issue_access_token / issue_refresh_token (actor_type, sub, exp)

2. app/core/gcs.py 신규
   - GCS Signed URL 발급 (PUT 업로드용, 5분 만료)
   - upload_target_type 별로 버킷 prefix 분기
   - 업로드 완료 후 메타데이터 등록 헬퍼

3. app/workers/main.py 신규
   - arq WorkerSettings (Redis 연결, on_startup/shutdown, 잡 등록 placeholder)
   - 잡 등록은 import 기반 (각 도메인 에이전트가 추가)

4. app/utils/pagination.py 신규
   - Cursor 기반 페이지네이션 (base64 인코딩 cursor: created_at + id)
   - PageParams (size 기본 20, 최대 50), PageResult[T]

5. app/utils/idempotency.py 신규
   - Idempotency-Key 헤더 처리: 동일 actor + key + request_hash → 캐시된 응답 반환
   - IdempotencyKey 테이블 활용 (이미 정의됨)
   - decorator `@idempotent` 또는 dependency 형태로 제공

6. app/utils/image.py 신규
   - Pillow로 EXIF orientation 정규화 + 1024px 리사이즈

7. app/api/v1/__init__.py에 라우터 자리 마련 (placeholder import 주석)
8. tests/conftest.py 확장:
   - DB 세션 픽스처 (테스트마다 트랜잭션 롤백)
   - Redis 픽스처 (flushdb)
   - 인증 클라이언트 픽스처 (user_token, owner_token)
   - Apple Sign In mock 픽스처
   - OpenAI/GCS/Kakao 외부 API mock 픽스처

[참고]
- Apple Sign In 검증 절차: https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_rest_api
- 키 페치 캐싱은 in-memory + 1시간 TTL로 충분 (MVP)
- arq 패턴: https://arq-docs.helpmanual.io/

[금지]
- 도메인 로직 작성 금지 (라우터, 서비스 등). 너는 인프라만 만든다.

[DoD]
- 신규 모듈마다 unit test 1개 이상 (Apple JWKS는 mock, GCS는 mock)
- 모든 다른 도메인 에이전트가 import할 수 있어야 함
```

---

### A1. Auth & Identity Agent

```
역할: 유저(Apple Sign In) + 사장님(이메일/비밀번호) 인증 도메인을 구현합니다.

[의존]
- A0 Platform Agent 완료 (app/core/security.py 확장본, GCS, conftest 픽스처)
- app/models/accounts.py (User, Owner, BusinessVerification, PasswordResetToken, UserDeviceToken)

[작업 범위]
1. app/schemas/auth.py
   - AppleSignInRequest, AppleSignInResponse (access/refresh)
   - OwnerSignupRequest, OwnerLoginRequest, OwnerLoginResponse
   - PasswordResetRequest, PasswordResetConfirmRequest
   - RefreshTokenRequest
2. app/schemas/users.py + app/schemas/owners.py
   - UserPublic, UserMe, UserUpdate (닉네임, 프로필 이미지, 관심 태그)
   - OwnerMe, OwnerUpdate, BusinessVerificationSubmit
3. app/services/auth_service.py
   - apple_sign_in(id_token) → upsert User → JWT 발급
   - owner_signup / owner_login / password_reset
   - refresh_token rotation
4. app/services/user_service.py + owner_service.py
   - get_me / update_me / device token register / unregister
   - business_verification 제출 (이미지 GCS Signed URL은 Platform 제공)
5. app/api/v1/auth.py
   - POST /auth/apple
   - POST /auth/owner/signup, /auth/owner/login
   - POST /auth/owner/password-reset, /auth/owner/password-reset/confirm
   - POST /auth/refresh
   - POST /auth/logout
6. app/api/v1/users.py
   - GET /me, PATCH /me
   - POST /me/device-tokens, DELETE /me/device-tokens/{token}
7. app/api/v1/owners.py
   - GET /owners/me, PATCH /owners/me
   - POST /owners/me/business-verification

[비즈니스 규칙 (spec §1, §9)]
- 만 14세 미만 차단 (Apple birth_date 없음 → 정책 화면 동의 체크)
- Apple email-relay 주소 그대로 저장 OK
- owner는 사업자 인증 approved 전엔 샵 등록 차단 (Shop Agent와 협의된 규칙)

[금지]
- shops/designers 관련 로직 작성 금지 (A2가 처리)
```

---

### A2. Shop & Designer Agent

```
역할: 사장님의 샵, 영업시간, 디자이너, 스케줄 관리를 구현합니다.

[의존]
- A0 Platform 완료
- A1 Auth 완료 (current_owner_id 사용)
- app/models/shop.py (Shop, ShopImage, ShopBusinessHour, Designer, DesignerSchedule, DesignerTimeOff)

[작업 범위]
1. app/schemas/shops.py
   - ShopCreate, ShopUpdate, ShopMe, ShopPublic (앱 노출용)
   - ShopBusinessHourSet (요일별 [open, close, breaks])
   - ShopImageCreate
2. app/schemas/designers.py
   - DesignerCreate, DesignerUpdate, DesignerPublic
   - DesignerScheduleSet (주간 근무시간)
   - DesignerTimeOffCreate (특정일 휴무/임시 불가)
3. app/services/shop_service.py
   - 1사장님 1샵 강제
   - 영업시간 충돌 검증 (open < close, break 포함)
   - auto_accept ↔ payment_method 정합성 검증 (reservation_policy.validate_shop_payment_policy 사용)
4. app/services/designer_service.py
   - 디자이너 CRUD, 스케줄 / 휴무 등록
   - 비활성 디자이너는 신규 예약 불가지만 기존 예약은 유지
5. app/api/v1/shops.py
   - POST /shops (최초 등록, 사업자 approved 필요)
   - GET /shops/me, PATCH /shops/me
   - POST /shops/me/images, DELETE /shops/me/images/{id}
   - PUT /shops/me/business-hours
   - GET /shops/{shop_id} (앱용 공개 조회)
6. app/api/v1/designers.py
   - GET/POST /shops/me/designers
   - PATCH/DELETE /shops/me/designers/{id}
   - PUT /shops/me/designers/{id}/schedule
   - POST/DELETE /shops/me/designers/{id}/time-off

[비즈니스 규칙 (spec §9, §11)]
- 사장님 1명당 1샵 (DB unique 제약 + 서비스 가드)
- 디자인을 1개 이상 가진 디자이너 삭제 시 soft-disable로 변경
- 영업시간/스케줄 변경 시 기존 confirmed 예약은 그대로 유지, 신규 슬롯 계산만 영향

[금지]
- design 관련 작성 금지 (A4)
- reservation 관련 작성 금지 (A5)
```

---

### A3. Community Agent

```
역할: 스네일(SNAP), 댓글, 좋아요, 팔로우, 리뷰, 신고를 구현합니다.

[의존]
- A0 Platform, A1 Auth
- app/models/community.py 전체 (Snap*, Comment*, Review*, Report, UserFollow, FavoriteDesign)

[작업 범위]
1. app/schemas/snails.py (snail = Snap)
   - SnapCreate (이미지, 본문, 태그, 샵/디자인/디자이너/예약 선택 태그)
   - SnapPublic (인증 뱃지: 예약 연결 시 true)
   - SnapFeedQuery (latest/recommended/ranking/following)
2. app/schemas/comments.py, likes.py, follows.py, reviews.py, reports.py
3. app/services/snail_service.py
   - 피드 쿼리 (latest, ranking은 (likes*3 + comments*2 + 최신성) 단순 가중)
   - 인증 뱃지 = 본인의 completed 예약 연결 시 true
4. app/services/comment_service.py / like_service.py / follow_service.py
5. app/services/review_service.py
   - 예약 1건 = 리뷰 1건 (DB unique + 가드)
   - completed 상태에서만 작성 가능 (reservation_policy 의존)
   - 사장님 답변 (ReviewReply) 별도
6. app/services/report_service.py
   - target_type별 분기 (snap/comment/review/user/shop)
   - 어드민 처리는 SQL 직접 → 라우터 단순화
7. app/api/v1/snails.py, comments.py, reviews.py, reports.py, follows.py
   - 표준 RESTful + cursor 페이지네이션
   - 차단/숨김: 본인이 차단한 user의 콘텐츠 피드 제외 (BlockedUser 모델 추가 필요시 보고)

[비즈니스 규칙 (spec §7, §8, §11.12, §12)]
- 리뷰는 샵 평균 별점에 반영, 스네일은 반영 X
- 리뷰 이미지 최대 5장
- App Store 정책: UGC 앱은 신고/차단 필수

[금지]
- 예약 상태 전이 직접 금지 (A5 reservation_service 호출만)
```

---

### A4. Design & Search Agent

```
역할: 디자인 CRUD + PostgreSQL 기반 검색 API를 구현합니다. ES 미도입(사용자 결정).

[의존]
- A0, A1, A2 완료
- app/models/design.py (Design, DesignImage, DesignDesigner, LlmJob)
- app/services/search_service.py (placeholder만 있음 — 본인이 채움)

[검색 전략 (사용자 결정)]
- 별도 검색 엔진 미도입. PostgreSQL 안에서 해결
- 키워드: ai_tags / owner_tags ARRAY @> + GIN 인덱스
- 오타: pg_trgm similarity (title, description)
- 의미: pgvector(OpenAI text-embedding-3-small, 1536d) 코사인 거리
- 가중합 점수: tags*0.4 + trgm*0.2 + vector*0.4

[작업 범위]
1. 새 마이그레이션 (designs.embedding 컬럼 추가):
   - alembic/versions/{YYYYMMDD_HHMM}_add_design_embedding.py
   - down_revision = 현재 head (확인 후 사용)
   - ALTER TABLE designs ADD COLUMN embedding vector(1536) NULL
   - CREATE INDEX ix_designs_embedding ON designs USING ivfflat (embedding vector_cosine_ops) WITH (lists=10)
       * 디자인 500개 규모는 IVFFlat lists=10이 HNSW보다 가볍고 빌드 빠름. 5K+ 시 HNSW로 마이그레이션
   - GIN: designs.ai_tags, owner_tags, color_palette
   - GIN(pg_trgm): designs.title, designs.description
   - app/models/design.py에 embedding 컬럼 추가 (pgvector.sqlalchemy.Vector 사용)
       * 이건 모델 변경이지만 검색 핵심이라 예외 허용 — 추가만, 기존 컬럼 수정 금지

2. app/schemas/designs.py
   - DesignCreate (title, description, base_price, duration_minutes, designer_ids, image_upload_keys, owner_tags)
   - DesignUpdate, DesignMe (사장님용 — 분석 상태 포함), DesignPublic (앱용)

3. app/schemas/search.py
   - SearchQuery (q, region, price_min/max, colors, moods, duration_max, sort, cursor)
   - SearchResult (designs: list[DesignPublic], next_cursor, recommendations: list[DesignPublic])

4. app/services/design_service.py
   - 디자인 생성 시 image_upload_keys 검증 (UploadObject 존재 + owner_id 일치)
   - 등록 직후 ai_analysis_status=pending → LLM 잡 enqueue (A6 인터페이스 사용; A6 미완 시 TODO placeholder)
   - 노출 가드: owner.verification_status=approved + shop.visibility=active +
     design.visibility=active + design.ai_analysis_status=done + deleted_at IS NULL

5. app/services/search_service.py 본구현
   - search_designs(...) PostgreSQL 쿼리 구성:
       * query 있으면: ai_tags ARRAY @> 일부 매칭 + pg_trgm sim + (embedding이 있고 OpenAI 사용 가능하면) cosine distance
         - query → OpenAI embedding은 A0의 OpenAI client가 없으면 일단 빼고 tags+trgm만 (TODO 주석)
       * query 없으면: favorite_count DESC, created_at DESC
       * filter: region exact, colors/moods ARRAY @>, price/duration 범위
       * 노출 가드 4개 조합 WHERE 필수
       * 0건이면 recommendations에 동일 region 최신 5건 채워서 반환
   - search_shops, search_reviews (간단 버전: name pg_trgm)

6. app/api/v1/designs.py
   - GET /designs (검색 통합 — q + filters), GET /designs/{id}
   - POST /shops/me/designs, PATCH/DELETE /shops/me/designs/{id}
   - POST /shops/me/designs/{id}/reanalyze (LLM 재분석 트리거)
   - POST /designs/{id}/favorite, DELETE /designs/{id}/favorite

7. app/api/v1/search.py
   - GET /search (q + filters + scope=designs|shops|reviews)

[비즈니스 규칙 (spec §2, §3, §10)]
- 검색에 날짜 조건 없음 (가용시간은 reservation 측에서)
- 검색 결과 0건이면 유사 디자인 추천 (단순화: 동일 region 최신 5건)
- 사장님은 디자인 숨김/삭제 구분 (visibility=hidden vs soft delete)

[금지]
- LLM 호출 코드 작성 금지 (A6 service만 호출)
- 알림 발송 금지 (A7)
```

---

### A5. Reservation Agent

```
역할: 예약 도메인 — 가용시간 계산, 예약 생성, 상태 전이를 구현합니다. MVP에서 가장 복잡합니다.

[의존]
- A0, A1, A2, A4 완료
- app/models/reservation.py (Reservation, IdempotencyKey)
- app/services/reservation_policy.py (규칙 상수 + helper 이미 있음)

[작업 범위]
1. app/schemas/reservations.py
   - AvailabilityQuery (design_id, date)
   - AvailableSlot (start_at, end_at, available_designer_ids)
   - ReservationCreate (design_id, start_at, designer_id|null, user_request) + Idempotency-Key 헤더
   - ReservationMe (유저용), ReservationOwner (사장님용)
   - ReservationActionRequest (reject_reason, cancel_reason)
2. app/services/availability_service.py
   - calculate_available_slots(design_id, date) →
     1. 샵 영업시간 + 디자이너 근무시간 ∩
     2. - 디자이너 휴무 / time_off
     3. - 기존 SLOT_LOCK_STATUSES 예약 점유 슬롯 (payment_pending / confirmed)
     4. duration_minutes 단위 슬롯으로 잘라 반환
   - 자동 배정 가능 여부 판단
3. app/services/reservation_service.py
   - create_reservation:
     - idempotency 체크 (Platform 유틸)
     - 동시 active 예약 수 제한 (ACTIVE_USER_RESERVATION_STATUSES, MVP 기본 3)
     - 동일 샵 같은날 중복 검증
     - SELECT FOR UPDATE → 슬롯 재검증 → INSERT
     - auto_accept=true이면 즉시 confirmed, 아니면 pending
     - 알림 enqueue (Notification Agent service 호출)
   - owner_accept / owner_reject / shop_cancel / user_cancel / mark_no_show / mark_completed
     - reservation_policy의 next_status_after_owner_accept / can_mark_no_show 사용
4. app/api/v1/reservations.py
   - GET /designs/{id}/availability?date=YYYY-MM-DD
   - POST /reservations (user)
   - GET /me/reservations, GET /me/reservations/{id}
   - POST /me/reservations/{id}/cancel
   - GET /shops/me/reservations (캘린더 쿼리: from, to)
   - POST /shops/me/reservations/{id}/accept
   - POST /shops/me/reservations/{id}/reject
   - POST /shops/me/reservations/{id}/cancel
   - POST /shops/me/reservations/{id}/no-show
   - POST /shops/me/reservations/{id}/complete

[비즈니스 규칙 (spec §4, §5, §11) + §11 결정 매트릭스]
- 예약 흐름 (결정 #1):
   - on_site 샵: pending → (수락) → confirmed → completed
   - bank_transfer_guide 샵: pending → (수락) → payment_pending → (사장님이 입금 확인 → confirm 액션) → confirmed → completed
   - bank_snapshot, deposit_amount_snapshot, payment_method_snapshot 등은 수락 시점에 Shop에서 스냅샷
- pending은 슬롯 hard-lock 안 함 (다른 유저 pending 가능)
- payment_pending / confirmed만 exclusion constraint로 중복 차단
- no-show는 시작 30분 후부터 가능 (can_mark_no_show)
- **노쇼/취소 누적 카운터는 MVP 제외** (결정 #2). User 컬럼 추가 금지. 경고 문구/예약 제한 미구현
- 추가 액션: POST /shops/me/reservations/{id}/confirm-payment (bank_transfer_guide 샵이 payment_pending → confirmed로 이동)

[금지]
- 알림 발송 코드 직접 작성 금지 (A7 service 호출만)
```

---

### A6. LLM Pipeline Agent

```
역할: 디자인 등록 시 OpenAI Vision 분석 파이프라인을 arq 워커로 구현합니다.

[의존]
- A0, A4 완료
- app/models/design.py (Design, LlmJob)
- app/workers/settings.py (이미 있음)

[작업 범위]
1. app/services/llm_service.py
   - AsyncOpenAI 클라이언트 (asyncio.Semaphore로 동시성 5 제한)
   - tenacity 재시도 (429 / 5xx만, exp backoff)
   - transform(image_url) → masked_image_url (또는 메타데이터)
   - classify(image_url) → {tags, colors, moods, style, nail_shape, confidence}
   - embed(text) → vector (text-embedding-3-small, 1536d)
2. app/workers/llm_pipeline.py
   - arq job: analyze_design(ctx, design_id)
     - LlmJob INSERT (queued → running)
     - transform → classify → (선택) embed
     - Design 업데이트 (ai_tags, color_palette, ai_analysis_status=done, ai_model_version)
     - LlmJob 완료 처리
     - 성공 시 → ES 재인덱스 잡 enqueue (A4 search_service.upsert_design_document 호출)
     - 실패 시 → ai_analysis_status=failed, ai_error_code, ai_error_message
3. app/workers/main.py 업데이트 (Platform이 만든 entry에 job 등록)
4. prompts/ 디렉토리
   - prompts/classify.md (시스템 + 사용자 프롬프트, 표준 태그 사전 포함)
   - 표준 태그 사전은 references/snail_llm_pipeline_integration_guide.md 참고
5. 비용 가드
   - 이미지 1024px 리사이즈는 Platform util 사용
   - 동일 이미지 hash → Redis 캐시 결과 재사용 (1일 TTL)
   - 월간 호출 카운터 INCR (이미 운영 가드)
6. app/api/v1/designs.py에 추가될 reanalyze 라우터에서 enqueue되는 잡 명세 제공

[비즈니스 규칙 (spec §10)]
- 분석 중 → 사장님에게는 "분석 중" 상태, 앱에는 미노출
- 분석 실패 → 사장님 화면에 실패 사유 + 재분석 버튼
- 재분석은 사장님 트리거만 (자동 재시도는 LlmJob attempts ≤ 3까지 자동)

[금지]
- design CRUD 로직 작성 금지 (A4)
- 알림 발송 금지 (A7)
```

---

### A7. Notification Agent

```
역할: 카카오 알림톡(사장님) + APNs(유저) + 사장님 인박스 + 발송 이력을 구현합니다.

[의존]
- A0, A1, A2, A5 완료
- app/models/notification.py (NotificationDelivery, OwnerNotification)

[작업 범위]
1. app/services/notification_service.py
   - send_to_user(user_id, template_key, payload) → APNs 인큐
   - send_to_owner(owner_id, template_key, payload) → 알림톡 + OwnerNotification INSERT (인박스)
2. app/services/apns_client.py
   - firebase-admin 사용 (FCM 경유 가장 단순) 또는 aioapns 직접
   - device token 조회 → 발송 → 결과 기록
3. app/services/kakao_client.py
   - Bizppurio HTTP API 래퍼 (httpx)
   - 템플릿 코드 + 변수 → 발송
   - 발신프로필 키는 settings.KAKAO_SENDER_KEY
4. app/workers/notification_sender.py
   - arq job: send_notification(ctx, delivery_id) — 실패 시 NotificationDelivery 상태 갱신, 재시도
5. app/utils/notification_templates.py
   - 템플릿 키 enum + payload 스키마
   - 예: RESERVATION_REQUESTED, RESERVATION_CONFIRMED, RESERVATION_REJECTED, RESERVATION_REMINDER
6. app/api/v1/notifications.py
   - GET /shops/me/notifications (인박스 cursor 페이지네이션)
   - PATCH /shops/me/notifications/{id}/read

[비즈니스 규칙 (spec §4.15, §11)]
- 알림톡은 사전 심사된 템플릿만 가능 — 운영 전 사용자가 카카오 심사 통과 확인 필요
- 광고성 단어 금지 (정보성만)
- 발송 실패 시 5분 후 1회 재시도 (재시도 큐 단순)

[금지]
- 다른 도메인 비즈니스 로직 작성 금지 (호출만)
- 외부 API 키 하드코딩 금지 (settings 사용)
```

---

### A8. QA & Integration Agent (범위 축소)

```
역할: **도메인 간 e2e 시나리오 + 시드/데모 데이터**만 책임집니다.
도메인 내부 테스트는 각 도메인 에이전트가 이미 작성했으므로 중복 작성 금지.

[의존]
- A0~A7 전부 완료 (각 도메인의 service/router/integration test 완료)

[작업 범위 — 도메인 간 시나리오만]
1. tests/e2e/ — 여러 도메인을 가로지르는 시나리오만
   - test_owner_full_onboarding.py (가입 → 사업자 인증 → 샵 → 디자이너 → 디자인 등록 → LLM 분석 → ES 인덱싱 → 앱 검색 노출)
   - test_reservation_full_flow.py (앱 검색 → 디자인 상세 → 가용시간 → 예약 → 알림톡 발송 → 사장님 수락 → 리마인드 → 완료 → 리뷰)
   - test_reservation_concurrency.py (같은 슬롯에 동시 예약 요청 → 1건만 성공, 알림은 1건만)
   - test_idempotency_e2e.py (POST /reservations 같은 Idempotency-Key 재전송 → 동일 응답, 부수효과 없음)
   - test_state_machine_paths.py (pending→reject, confirmed→shop_cancel, confirmed→no_show, confirmed→completed→review)
   - test_natural_language_search.py ("여리여리한 핑크 네일" → ai_tags 매칭 확인)

2. scripts/seed.py
   - 사장님 5명, 샵 5개, 디자이너 15명, 디자인 500개(이미지 placeholder + AI 메타 미리 채움 — LLM mock), 유저 20명, 스네일 30개, 리뷰 50건

3. scripts/demo_reset.py
   - 데모 직전 truncate + seed

4. tests/e2e/README.md — 시나리오 ↔ spec_canonical 매핑표

[규칙]
- 외부 API는 conftest 픽스처 mock (A0가 제공)
- 실제 PG/Redis/ES는 docker-compose
- 도메인 내부 단위/통합 테스트는 절대 중복 작성 금지 (도메인 에이전트가 이미 작성)

[금지]
- 도메인 코드 수정 금지 — 버그 발견 시 해당 도메인 에이전트에게 패치 위임 (리드에게 보고)
```

---

## 9. 검수 / 토큰 효율 전략

### 9.1 에이전트 self-verify (1차 게이트)
각 에이전트는 작업 마지막에 본인이 직접 실행:
```bash
cd backend
ruff check .                    # 통과해야 보고 가능
ruff format --check .
mypy app
pytest -q                       # 본인 추가 테스트만이라도
```
실패하면 보고에 "PARTIAL — 다음 실패: ..." 명시.

### 9.2 리드(나) spot check (2차 게이트)
에이전트 보고 수신 후 나는:
- `git diff main...` 변경 파일 목록만 본다 (전체 파일 재독 X)
- 핵심 위반만 체크: AppError 사용 / HTTPException 직접 사용 / 모델 무단 수정 / 라우터 등록 충돌
- 통과하면 다음 웨이브 spawn

### 9.3 후속 웨이브가 자연 검증 (3차)
- 다음 에이전트가 import / 호출하면서 인터페이스 깨짐이 자동으로 드러남
- 별도 verify 에이전트 spawn 안 함 (cold start 비용 절감)

### 9.4 A8 e2e가 최종 안전망 (4차)

### 9.5 토큰 절감 규칙 (모든 에이전트 프롬프트에 포함)
- 본인 도메인 모델 파일만 읽기. 다른 도메인 모델은 필요한 칼럼만 프롬프트에 미리 박아두기
- 이미 읽은 파일 재로딩 금지
- spec_canonical 전문 읽지 말고 해당 도메인 §만 인용해서 프롬프트에 박기
- 코드 작성 전 탐색 라운드는 최대 5회로 제한, 그 이상 필요 시 리드에 보고

---

## 7. 실행 순서 (권장)

| 시점 | 액션 | 검수 |
|---|---|---|
| 1. | `A0 Platform` spawn → 완료 보고 | self-verify + spot check |
| 2. | `A1 Auth`, `A2 Shop`, `A3 Community` 병렬 spawn | self-verify + spot check |
| 3. | `A4 Design+Search` spawn | self-verify + spot check |
| 4. | `A5 Reservation`, `A6 LLM` 병렬 spawn | self-verify + spot check |
| 5. | `A7 Notification` spawn | self-verify + spot check |
| 6. | `A8 QA` spawn → e2e 시나리오 통과 | 최종 게이트 |

각 단계 후 리드:
- `git diff` 변경 파일만 읽고 핵심 위반 체크
- 충돌/누락 발견 시 다음 에이전트 프롬프트에 "주의: A2에서 X 누락 → 너가 보강" 명시
- 별도 patch 에이전트 spawn 지양 (cold start 비용)

---

## 8. 리스크 / 가정

- **에이전트 컨텍스트 한계**: 큰 도메인(A5 Reservation)은 컨텍스트가 빠듯할 수 있음 → 필요시 sub-task로 다시 쪼개기
- **모델 변경 필요 시**: 에이전트가 모델 변경을 보고하면 내가 직접 마이그레이션 + `__init__.py` 업데이트
- **외부 API 미준비**: 실제 키 없이도 mock으로 테스트 가능하도록 설계 (실 호출은 본인이 W0 키 발급 완료 후)
- **명세 변경**: spec_canonical 변경 시 영향받는 에이전트들에게 차이 diff를 전달

---

## 11. 기능 범위 결정 매트릭스 (사용자 확정)

A0~A1 완료 시점에 사용자가 확정한 결정. 모든 에이전트는 이 표를 따른다.

| # | 항목 | 결정 | 영향 에이전트 / 작업 |
|---|---|---|---|
| 1 | **payment_pending 상태 + bank_snapshot 등 결제 안내 필드** | **유지** | A5 Reservation: 흐름 = `pending → (수락) → [on_site면 confirmed / bank_transfer_guide면 payment_pending → (사장님 입금 확인) → confirmed] → completed`. 실제 PG 결제 매개는 미구현, 사장님이 입금 확인 후 confirm 트리거 |
| 2 | **노쇼/취소 누적 카운터 (User 컬럼)** | **MVP 제외 — 단 이력 조회 API만 허용 (B안)** | A5: spec §5.7~5.9 자동 경고/예약 제한 미구현, User 컬럼 추가 금지. 프론트 [PROFILE-01] "노쇼/취소 이력 (n/m)" 표시용으로 `GET /me/reservation-stats` (reservations 테이블 ad-hoc COUNT) 1개 추가 |
| 3 | **UserBlock (유저 차단)** | **MVP 이후, App Store 심사 제출 직전 추가** | TECH_STACK §10 W7 마일스톤에 명시. A3 Community는 현 시점에 만들지 않음 |
| 4 | **TermsAcceptance (약관 동의 이력)** | **추가** | A1 보완 패치 — `terms_acceptances` 모델 + 마이그레이션 + 가입 흐름에서 INSERT. Apple Sign In / Owner signup 두 경로 모두 적용 |
| 5 | **이미지 모더레이션 (NSFW)** | **신고만** (자동 검수 미구현) | A6 LLM: classify 프롬프트에 모더레이션 단계 추가 안 함. A3/A4: Report 모델로 사후 처리만 |
| 6 | **푸시 알림 카테고리 on/off** | **전체 on/off만** (현재 `UserDeviceToken.is_active` 그대로) | A7 Notification: 카테고리별 컬럼 추가 금지. 마케팅 알림은 MVP 미발송. 프론트 [SETTINGS-01] 카테고리별 토글 4개 → 전체 on/off 1개로 축소 |
| 7 | **Idempotency-Key 비인증 API 정책** | **쓰기 부수효과 있는 것만 필수** | A1 보완 패치 — `signup`, `password-reset`, `password-reset/confirm` = 필수 유지 / `login`, `refresh` = 면제. A1 외 도메인은 인증 후이므로 기존 룰(전부 필수) 그대로 |
| 8 | **스네일 비등록 샵 태그 (자유 텍스트)** | **불허, FK 유지** | A3 Community: `Snap.tagged_shop_id` FK 그대로. 비등록 샵은 캡션 텍스트로만 언급 가능. 프론트 [SNAP-02] 샵 검색 결과 0건일 때 "직접 입력" 옵션 제거 |
| 9 | **디자인 이미지 모드 (AI 추출 ↔ 원본)** | **users.image_view_mode enum 추가, 클라가 폴백 처리** | A1 보완 패치: `users.image_view_mode` enum `{model, wear}` 기본 `model` 컬럼 + 마이그레이션 1개 + UserMe/UserUpdate 스키마 + PATCH /me 처리. `model`=processed_url(AI 마스킹), `wear`=original_url(원본). DesignPublic은 양쪽 URL 모두 노출. processed_url=NULL이면 클라가 자동으로 original 표시(서버 분기 X). 디자인 상세 스와이프는 같은 이미지의 두 변형 토글만, 이미지 간 이동은 별도 인디케이터. SIGNUP-01 모델/실착 모드와 동일 개념(통합). A6는 본래 범위인 TRANSFORM 잡으로 processed_url을 채움 |

| 10 | **지도/거리 검색** | **줌 기반 viewport (bbox API)** | 신규 작업: `GET /shops?bbox=lat1,lng1,lat2,lng2`. 고정 반경(1/3/5/10km) 미채택. 좌표 컬럼은 이미 존재(`shops.latitude/longitude`), `BETWEEN` 인덱스 활용. PostGIS/ST_ 미사용. 응답은 viewport 안의 샵 핀만 |
| 11 | **위치 태그** | **서울 주요 지역 시스템 큐레이션** | `shops.location_tags TEXT[]` 컬럼 추가 + GIN. MVP는 홍대/성수/강남/명동/이태원 등 한정된 키워드 사전. 사장님이 샵 등록 시 선택. 검색·필터 양쪽에서 사용. 도로명 주소 자동 파싱은 P1 |
| 12 | **시술 옵션 (연장/제거/케어)** | **디자인의 하위 옵션 — 다중 선택 가능, 가격·시간 누적** | 신규 모델 `DesignOption(id, design_id FK, kind enum{extend,removal,care}, name, price_delta, duration_delta_min, sort_order, is_active)`. 사장님이 디자인별로 등록. 예약 시 `Reservation`에 `selected_option_ids JSONB`로 스냅샷(M:N 별도 테이블 안 만듦 — MVP 단순화). availability 계산 시 `duration = design.duration_minutes + Σ option.duration_delta_min`, 가격도 합산. 디자이너 합집합 룰은 그대로 |
| 13 | **예약 시간 선택 UI** | **일별 리스트** (날짜 선택 → 그 날 시간 슬롯 세로 리스트) | 기존 `GET /designs/{id}/availability?date=` 그대로 호환. 응답의 `available_designer_ids` 길이로 프론트가 "여유" 뱃지 표현 가능. 시술 옵션 적용 시 `options=ext,care` 쿼리 파라미터로 duration 합산 후 슬롯 재계산 (#12 동반) |
| 14 | **유사 디자인 추천** | **현재 구현(pg_trgm + pgvector cosine + ai_tags ARRAY 가중합) 유지** | A4가 이미 구현. Jaccard로 퇴화 안 함. 검색 결과 0건 + 디자인 상세 "비슷한 디자인" 두 군데 모두 동일 로직 |
| 15 | **검색 0건 추천** | **현재 구현(`_recommendations` 동일 region 최신 N건) 유지** | A4가 이미 구현. 제거하지 않음. 자동완성/인기 검색어는 별도 (#18에서 MVP 제외) |
| 16 | **popularity_score 공식** | **`(likes·1 + comments·2 + saves·3) / (age_hours + 2)^1.5`** | snail_service 랭킹 정렬 변경. **단 `saves`는 `SnapSave` 모델 신규 도입 후 적용** — SnapSave 미도입 단계에서는 `(likes + 2·comments) / (age_hours + 2)^1.5`로 임시 운영. 배치 미사용, 정렬 시 ORDER BY 식 직접 계산. 1시간 단위로 자연스럽게 감쇠 |
| 17 | **쿠폰 / 초대 코드 / 이벤트** | **MVP 제외** | PROFILE-01 메모에 있던 항목. 도메인 모델 없음. P1 |
| 18 | **검색 자동완성 / 인기 검색어** | **MVP 제외** | `GET /tags/suggest`, `GET /tags/popular` 미구현. 14_decisions의 기존 "자동완성/인기 태그 MVP 제외"와 일치. 단 #15의 0건 폴백은 자동완성과 별개라 유지 |
| 19 | **이달의 아트 영역** | **MVP 제외 (대기 → 배제)** | 홈 큐레이션 섹션 미도입. 인기 디자인은 일반 정렬로 갈음 |
| 20 | **샵 영업시간 휴게시간** | **MVP 제외 (대기 → 배제, 디자이너 휴게로 갈음)** | `ShopBusinessHour`에 break 컬럼 추가 안 함. 점심·휴게는 디자이너 `DesignerSchedule.break_*` 컬럼(이미 존재)으로 처리. 샵 전체 일괄 휴게는 모든 디자이너에 동일 break 설정으로 운영 |

### 11.1 결정 이력

- 2026-05-27: 위 7개 항목 사용자 확정
- 2026-05-27 (후속): 프론트 화면 명세 v2 검토 후 #2 명확화(B안: 이력 조회 API 허용), #6 화면 축소 명시, #8 추가
- 2026-05-28: #9 추가 (디자인 이미지 모드 — AI 추출 ↔ 원본, users.image_view_mode 컬럼 + 클라 폴백)
- 2026-05-28 (A0~A8 완료 후): #10~#20 추가. 지도 줌 기반 viewport / 위치 태그 서울 시드 / 시술 옵션 하위 도메인 / 예약 UI 일별 리스트 / 유사 디자인·0건 추천은 기존 구현 유지 / popularity_score 공식 / 쿠폰·자동완성·이달의 아트·휴게시간 MVP 제외
- 이 표가 spec_canonical과 충돌하면 **이 표를 우선**으로 본다 (사용자 최종 결정)
