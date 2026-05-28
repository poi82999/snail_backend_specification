# Snail Backend

FastAPI 기반 MVP 백엔드 초기 골격입니다. 현재 범위는 API 서버 부트스트랩, 공통 응답/에러 규칙, 관계형 DB 스키마, 로컬 인프라 구성, CI입니다.

## Local Start

```powershell
cd backend
Copy-Item .env.example .env
docker compose -f docker/docker-compose.yml up -d postgres redis
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

헬스체크:

```powershell
curl http://localhost:8000/api/v1/health
```

전체 컨테이너 실행:

```powershell
cd backend
docker compose -f docker/docker-compose.yml up --build
```

## 검증 (단일 명령)

```powershell
.\scripts\check.ps1                 # ruff + format + mypy + alembic + pytest
.\scripts\check.ps1 -SkipDb         # DB 없이 정적 검사만
.\scripts\check.ps1 -Only ruff      # 특정 단계만
```

자동 처리:
- `.venv\Scripts` PATH 추가 (ruff/mypy/alembic이 그냥 명령어로 동작)
- `DATABASE_URL=...?ssl=disable` 주입 — **Windows 한글 사용자 경로**(예: `C:\Users\신민석`)에서 asyncpg가 시스템 SSL cert 자동탐색 중 `OSError [Errno 42] Illegal byte sequence`로 실패하는 문제 우회. 로컬 docker는 평문이라 안전, prod(Cloud SQL Proxy)에서는 `.env` 또는 Secret Manager로 `ssl=require` 덮어쓰기

## Architecture Decisions Applied

- 런타임: Python 3.12 + FastAPI + SQLAlchemy 2 async
- DB: PostgreSQL 16, Alembic migration-first
- 캐시/큐: Redis. LLM/알림 작업 큐는 `arq` 기반으로 확장 예정
- 검색: PostgreSQL pg_trgm + ai_tags ARRAY GIN + pgvector(OpenAI embedding) 조합. ES 미도입
- 저장소: GCS signed URL 방식. 백엔드는 업로드 권한과 메타데이터만 관리
- 알림: 유저 APNs, 사장님 카카오 알림톡 + `owner_notifications` inbox
- 공통 API: `request_id`, 공통 에러 코드, cursor pagination 스키마 준비

## Schema Coverage

초기 마이그레이션 `alembic/versions/20260527_0900_initial_schema.py`는 다음 MVP 도메인을 포함합니다.

- 유저/사장님/사업자 인증/비밀번호 재설정
- 1사장님 1샵, 샵 이미지, 영업시간
- 디자이너, 주간 스케줄, 특정일 휴무
- 디자인, 이미지, 가능 디자이너, LLM 작업 상태
- 예약 상태 머신, 예약금 안내 스냅샷, idempotency
- 스네일, 댓글, 좋아요, 팔로우
- 예약 기반 리뷰, 리뷰 이미지, 사장님 답변
- 신고/모더레이션
- 사장님 알림함, 알림 발송 이력
- presigned upload object 메타데이터

## Important Constraints

- `pending` 예약은 슬롯을 hard-lock하지 않습니다.
- `payment_pending`/`confirmed` 예약만 디자이너 슬롯 exclusion constraint로 중복을 막습니다.
- 유저는 `pending`/`payment_pending`/`confirmed` 예약끼리 시간이 겹칠 수 없습니다.
- `auto_accept=true` 샵은 `payment_method=on_site`만 허용합니다.
- 디자인 공개 노출은 `owner approved + shop active + design active + ai done` 조합을 서비스 레이어에서 강제해야 합니다.

## Next Implementation Order

1. Owner auth/register/login/password reset
2. Owner shop/designer/design CRUD
3. Reservation creation + accept/reject/payment-confirmed transitions
4. LLM job worker + design reanalysis
5. Design search API (pg_trgm + ARRAY GIN + pgvector)
6. Notification sender + owner inbox API
