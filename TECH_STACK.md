# 🛠️ 스네일 백엔드 기술 스택 — MVP (8주)

> 백엔드 1인 운영 · 데모데이 목표 · 월 운영비 50만원 이내
> 작성일: 2026-05-27 · 대상 버전: MVP v1

---

## 0. TL;DR

| 레이어 | 선택 | 핵심 이유 |
|---|---|---|
| 클라우드 | **GCP (Seoul, asia-northeast3)** | $300 크레딧, Cloud SQL 안정성, MVP 트래픽 e2-micro 충분 |
| 런타임 | **Python 3.12 + FastAPI 0.115** | LLM 친화적, 타입 힌트, OpenAPI 자동 생성 |
| ORM | **SQLAlchemy 2.0 + Alembic** | async 지원, 마이그레이션 표준 |
| DB / 검색 | **PostgreSQL 16 (Cloud SQL) + pg_trgm + pgvector + ai_tags ARRAY GIN** | 검색 엔진 미도입(1인 운영 부담 ↓). 한국어 자연어는 LLM이 ai_tags에 동의어/분위기까지 풍부 부여 + pgvector 의미 검색으로 대체 |
| 캐시/큐 | **Redis 7 (GCE Docker)** | 캐시 + FastAPI BackgroundTasks 보조 |
| 저장소 | **GCS (Google Cloud Storage)** | 이미지/원본 영구 보관 + Signed URL |
| LLM | **OpenAI GPT-4o-mini (Vision)** | 500회/8주 규모 ₩5만 이내 |
| 인증 | **Apple Sign In + JWT (PyJWT)** | 명세서 v3 기준 |
| 알림 | **카카오 알림톡 (Bizppurio/Aligo)** + **APNs** | 사장님은 알림톡, 유저는 푸시 |
| 배포 | **Docker + GitHub Actions → GCE** | 컨테이너 단일화, 무료 티어 GHA |
| 모니터링 | **Sentry (Free) + GCP Cloud Logging** | 에러/로그 분리 |

---

## 1. 인프라 — GCP

### 1.1 리소스 구성

| 리소스 | 사양 | 월 예상 비용 | 비고 |
|---|---|---|---|
| GCE `e2-small` (앱 서버) | 2 vCPU(공유), 2GB RAM | ~$13 | Docker로 FastAPI + Redis 띄움 |
| Cloud SQL PostgreSQL 16 | db-f1-micro, 10GB SSD | ~$10 | HA 없음(MVP), 일일 백업 |
| GCS Standard | 50GB 가정 | ~$1 | 디자인 이미지 |
| Cloud Load Balancing | (옵션, 도메인 SSL용) | $18+ | **MVP는 Caddy로 대체** ← 추천 |
| Egress | ~50GB | ~$5 | |
| **합계** | | **~$30 (₩4만)** | $300 크레딧으로 8주 완전 무료 |

> 💡 **Cloud Run 대신 GCE 선택 이유**: Redis 같이 띄우고, Cold start 없고, Cloud SQL Proxy를 Sidecar로 묶기 쉬움. 트래픽 늘면 Cloud Run으로 이전.

### 1.2 네트워크/보안
- **VPC**: default + Cloud SQL은 **Private IP** (Cloud SQL Auth Proxy 사용)
- **방화벽**: GCE 인스턴스는 443(HTTPS)만 외부 노출
- **도메인/SSL**: Cloudflare DNS + Caddy 2 (Let's Encrypt 자동)
- **시크릿**: **GCP Secret Manager** (DB 비번, OpenAI 키, JWT secret, Apple p8)

### 1.3 디렉토리 구조 (GCE 인스턴스)
```
/opt/snail/
├── docker-compose.yml      # api, redis, caddy
├── .env                    # Secret Manager에서 startup-script로 주입
├── Caddyfile
└── data/
    └── redis/              # AOF 영속
```

---

## 2. 애플리케이션 스택

### 2.1 핵심 라이브러리

```txt
# requirements.txt (백엔드 앱)
python = "3.12"

# 웹 프레임워크
fastapi==0.115.0
uvicorn[standard]==0.32.0
gunicorn==23.0.0              # uvicorn worker 관리

# DB / ORM
sqlalchemy[asyncio]==2.0.36
alembic==1.13.3
asyncpg==0.30.0
pgvector==0.3.6               # 의미 검색 (OpenAI embedding 1536d)

# 검증/직렬화
pydantic==2.9.2
pydantic-settings==2.6.0

# 인증
pyjwt[crypto]==2.9.0
cryptography==43.0.3
passlib[bcrypt]==1.7.4        # 추후 일반 로그인 대비

# LLM / HTTP
openai==1.54.0
httpx==0.27.2
tenacity==9.0.0               # 재시도

# 캐시/큐
redis[hiredis]==5.1.1

# GCP
google-cloud-storage==2.18.2
google-cloud-secret-manager==2.21.0

# 알림
firebase-admin==6.5.0         # APNs는 FCM 경유 (또는 PyAPNs2)

# 관측
sentry-sdk[fastapi]==2.18.0
structlog==24.4.0

# 개발/테스트
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
httpx==0.27.2                 # TestClient
ruff==0.7.2                   # lint + format
mypy==1.13.0
```

### 2.2 프로젝트 구조

```
snail-backend/
├── app/
│   ├── main.py                    # FastAPI 인스턴스, 미들웨어
│   ├── core/
│   │   ├── config.py              # pydantic-settings
│   │   ├── security.py            # JWT, Apple Sign In 검증
│   │   ├── database.py            # async engine, session
│   │   ├── redis.py
│   │   └── logging.py             # structlog 설정
│   ├── api/
│   │   ├── deps.py                # Depends: get_db, get_current_user
│   │   ├── errors.py              # 공통 에러 핸들러
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── shops.py           # 사장님 샵
│   │       ├── designers.py
│   │       ├── designs.py         # 디자인 + LLM 트리거
│   │       ├── reservations.py
│   │       ├── snails.py          # 커뮤니티
│   │       ├── reviews.py
│   │       ├── reports.py
│   │       ├── notifications.py
│   │       └── llm_callbacks.py   # LLM 비동기 결과 콜백
│   ├── models/                    # SQLAlchemy 모델
│   │   ├── user.py
│   │   ├── shop.py
│   │   └── ...
│   ├── schemas/                   # Pydantic 입출력
│   │   └── ...
│   ├── services/                  # 도메인 로직
│   │   ├── auth_service.py
│   │   ├── reservation_service.py # 시간 충돌 검증
│   │   ├── search_service.py      # pg_trgm + ARRAY GIN + pgvector 가중합
│   │   ├── llm_service.py         # OpenAI 호출
│   │   └── notification_service.py
│   ├── workers/                   # BackgroundTasks 핸들러
│   │   ├── llm_pipeline.py        # Transform + Classify
│   │   └── notification_sender.py
│   └── utils/
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── scripts/
│   ├── seed.py                    # 더미 디자인 500개
│   └── reindex_embeddings.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .github/workflows/
│   ├── ci.yml
│   └── deploy.yml
├── pyproject.toml
├── requirements.txt
└── README.md
```

### 2.3 FastAPI 부트스트랩 핵심 설정

```python
# app/main.py 핵심
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    await init_redis()
    yield
    await close_db_pool()

app = FastAPI(
    title="Snail API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENV != "prod" else None,  # prod 비공개
)

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, ...)
app.include_router(api_v1_router, prefix="/api/v1")
```

```python
# gunicorn 실행 (Dockerfile CMD)
# CPU 2개 가정 → workers = 2*CPU + 1, async라 적게
gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w 3 \
  -b 0.0.0.0:8000 \
  --timeout 60 \
  --graceful-timeout 30
```

---

## 3. 데이터 레이어

### 3.1 PostgreSQL 확장

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;       -- 오타/유사도
CREATE EXTENSION IF NOT EXISTS btree_gin;     -- 복합 인덱스
```

### 3.2 핵심 인덱스 전략

| 테이블 | 컬럼 | 인덱스 타입 | 용도 |
|---|---|---|---|
| `designs.name` | text | **GIN (pg_trgm)** | 오타 허용 검색 |
| `designs.tags` | text[] | **GIN** | 태그 다중 매칭 |
| `reservations.(designer_id, start_at)` | composite | btree | 시간 충돌 검증 |
| `snails.created_at DESC` | btree | 피드 페이지네이션 |

> 검색은 별도 엔진 없이 PostgreSQL 내 인덱스로만 수행. 의미 검색은 pgvector(OpenAI embedding) 담당.

### 3.3 마이그레이션 정책
- `alembic revision --autogenerate` 후 **반드시 수동 리뷰** (drop 위험)
- 운영 적용은 GitHub Actions `deploy.yml`에서 `alembic upgrade head` 자동 실행
- 롤백 마이그레이션은 작성하되, 운영에서는 forward-only 원칙

### 3.4 트랜잭션 / 동시성
- 예약 충돌 방지: `SELECT ... FOR UPDATE` + `tstzrange` overlap 체크
- 또는 `EXCLUDE USING gist (designer_id WITH =, slot WITH &&)` 제약

---

## 4. LLM 파이프라인

### 4.1 흐름

```
[사장님 웹]
  ↓ POST /designs (이미지 업로드)
[FastAPI]
  ↓ GCS 업로드 → designs INSERT (status=pending)
  ↓ BackgroundTasks.add_task(run_llm_pipeline, design_id)
  ↓ return 202 { design_id, status: "pending" }

[BackgroundTask worker]
  1. OpenAI Vision: Transform (네일 영역 마스킹/추출 프롬프트)
  2. OpenAI Vision: Classify (태그/색상/스타일)
  3. OpenAI embedding 생성 후 designs.embedding 업데이트 (검색 인덱스 별도 불필요)
  4. UPDATE designs SET status='done', tags=..., embedding=...

[사장님 웹]
  ↓ GET /designs/{id} 폴링 (2초 간격, 최대 60초)
  ← status 변경 감지 시 결과 표시
```

### 4.2 호출 모듈

```python
# app/services/llm_service.py 골격
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
async def classify_design(image_url: str) -> ClassifyResult:
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_schema", "json_schema": CLASSIFY_SCHEMA},
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": CLASSIFY_PROMPT},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }],
        temperature=0.1,
        max_tokens=500,
    )
    return ClassifyResult.model_validate_json(resp.choices[0].message.content)
```

### 4.3 비용 가드레일
- **월 한도**: OpenAI 대시보드에 `$50` 하드 리밋
- **호출 카운터**: Redis `INCR llm:calls:{YYYYMM}` → 일정 초과 시 슬랙 알림
- **이미지 리사이즈**: 업로드 시 1024px로 줄여 토큰 절약 (Pillow)
- **결과 캐시**: 동일 이미지 hash 재호출 방지 (`llm:result:{sha256}`)

### 4.4 폴링 vs Webhook
- **선택: 폴링** (클라이언트가 GET 반복)
- 이유: 외부 노출 webhook 엔드포인트 불필요, 인증 단순화, BackgroundTasks와 자연스러움
- 폴링 간격 가이드: 처음 10초는 2초, 이후 5초 (앱에서 backoff)

---

## 5. 검색 — pg_trgm + ARRAY GIN + pgvector

### 5.1 검색 모드

| 쿼리 유형 | 처리 | 예시 |
|---|---|---|
| 짧은 단어/태그 | ai_tags / owner_tags ARRAY @> 매칭 + GIN | "핑크", "젤" |
| 오타 / 유사어 | pg_trgm similarity (title, description) | "프랜치" → "프렌치" |
| 자연어 문장 | OpenAI embedding → pgvector 코사인 거리 | "여리여리한 핑크 네일" |
| 가중합 | tags*0.4 + trgm*0.2 + vector*0.4 | 혼합 점수 |

### 5.2 인덱싱 시점
- 디자인 등록 시 LLM 분석에서 ai_tags + embedding 생성 → designs row에 직접 저장 (별도 인덱스 동기화 불필요)
- 디자인 수정 시 영향 필드 변경되면 같은 트랜잭션에서 재계산

### 5.3 마이그레이션 트리거 (향후)
- **MVP는 ES 미도입**. 디자인 5K+ **또는** p95 검색 응답 > 500ms 시점에 ES + nori 재검토
- 한국어 형태소 분석의 빈자리는 LLM 분석에서 ai_tags를 동의어/분위기까지 풍부하게 부여하는 방식으로 보완

---

## 6. 알림 시스템

### 6.1 채널 분기

| 대상 | 채널 | 사용 라이브러리 |
|---|---|---|
| 유저(앱) | APNs (직접) | `aioapns` 또는 FCM 경유 `firebase-admin` |
| 사장님(웹) | 카카오 알림톡 | Bizppurio HTTP API (직접 httpx 호출) |
| 사장님 폴백 | SMS | 카카오 실패 시 (선택, MVP 후순위) |

### 6.2 처리 방식
- 모든 알림은 BackgroundTasks 큐잉 → 실패 시 Redis `notif:retry:{id}` 저장
- 실패 재시도는 단순 cron (5분마다 GCE 인스턴스 내 `apscheduler`)
- **대량 발송 없음** → Celery/RQ 도입 보류

---

## 7. CI / CD

### 7.1 GitHub Actions

**ci.yml** (PR 트리거)
```yaml
- ruff check + ruff format --check
- mypy app/
- pytest --cov (PostgreSQL service container 사용)
- docker build (캐시 활용, 푸시 X)
```

**deploy.yml** (main 푸시 트리거)
```yaml
- docker build & push → GCR (Google Container Registry)
- SSH → GCE 인스턴스
- docker compose pull && docker compose up -d
- alembic upgrade head
- 헬스체크 (/health) 통과 확인 → 실패 시 이전 이미지 롤백
```

### 7.2 환경 분리

| 환경 | 위치 | DB | 용도 |
|---|---|---|---|
| local | 개발자 노트북 | Docker Postgres | 일상 개발 |
| staging | (옵션, 없음) | — | MVP는 생략 |
| prod | GCE | Cloud SQL | 실서비스 |

> staging 생략 이유: 1인 운영 + 데모데이 일정. 로컬에서 충분히 테스트하고 prod 직배.
> 대신 **PR마다 ci.yml 통과 강제** + main 머지 전 본인 sanity check.

### 7.3 시크릿 관리
- GitHub Actions: Repository Secrets (`GCP_SA_KEY`, `SSH_KEY` 등)
- 앱 런타임: GCP Secret Manager (인스턴스 startup-script에서 fetch → `.env` 생성)
- `.env`는 절대 git 커밋 금지 (`.gitignore` 강제)

---

## 8. 관측 / 운영

### 8.1 로깅
- `structlog` JSON 출력 → docker logs → Cloud Logging 자동 수집
- 필수 필드: `request_id`, `user_id`, `path`, `status`, `duration_ms`
- LLM 호출은 별도 logger (`llm.classify`, `llm.transform`) — 비용 추적용

### 8.2 에러
- **Sentry** (Free 5K events/월) — FastAPI 미들웨어로 자동 수집
- 4xx는 보내지 않음, 5xx만

### 8.3 헬스체크
- `GET /health` → DB ping + Redis ping + (선택) OpenAI ping
- GCE 인스턴스 부팅 시 Caddy가 `/health` 200 확인 후 트래픽 라우팅

### 8.4 백업
- Cloud SQL 자동 백업 (일 1회, 7일 보관) — 기본 ON 확인
- 디자인 이미지: GCS 버저닝 ON (실수 삭제 복구)

---

## 9. 보안 체크리스트 (MVP 필수)

- [ ] HTTPS 강제 (Caddy 자동)
- [ ] CORS 화이트리스트 (앱 도메인만)
- [ ] JWT 만료 시간: access 1h, refresh 30d
- [ ] Apple p8 키 → Secret Manager
- [ ] OpenAI 키 사용량 모니터링 + 하드 리밋
- [ ] Rate limit: `slowapi` (분당 60 req/IP)
- [ ] SQL 인젝션: SQLAlchemy ORM만 사용 (raw SQL 금지)
- [ ] 이미지 업로드: 확장자 + MIME + 크기(<10MB) 검증
- [ ] Signed URL: GCS 직접 업로드 URL은 5분 만료
- [ ] 사장님 사업자 인증: 수동 검토 (MVP는 본인이 직접 확인)

---

## 10. 8주 일정 가드 (개략)

| 주차 | 인프라 / 백엔드 마일스톤 |
|---|---|
| W1 | GCP 셋업, 도메인/SSL, CI 파이프라인, 빈 FastAPI 배포 |
| W2 | DB 스키마 + Alembic, 인증 (Apple Sign In), 유저 CRUD |
| W3 | 샵/디자이너/디자인 CRUD, GCS 업로드 |
| W4 | LLM 파이프라인 (Transform + Classify + Embedding) |
| W5 | 검색 (pg_trgm + pgvector + ARRAY GIN), 피드 |
| W6 | 예약 (시간 충돌, 상태 전이), 알림톡 연동 |
| W7 | 커뮤니티(스네일), 리뷰, 리포트, APNs, **UserBlock (App Store 심사 대비)** |
| W8 | UX 테스트 피드백 반영, 버그픽스, 데모 시나리오 리허설 |

> 📌 **UserBlock 위치 명시**: 결정 매트릭스 #3에 따라 W7에 추가. App Store UGC 심사 거부 사유 1순위. 모델 + 마이그레이션 + 피드/댓글에서 차단 필터 적용.

---

## 11. 명시적 NOT in MVP

다음은 **8주 안에 손대지 않음** — 함정 회피 목록:

- ❌ Kubernetes / Cloud Run autoscaling
- ❌ Elasticsearch / Meilisearch / OpenSearch (별도 검색 엔진은 5K+ 도달 시 재검토)
- ❌ Celery / RQ / Kafka (BackgroundTasks로 충분)
- ❌ GraphQL (REST + OpenAPI 고정)
- ❌ 자체 GPU LLM 서빙
- ❌ Multi-region / HA Cloud SQL
- ❌ Feature flag 시스템 (Unleash, LaunchDarkly)
- ❌ Microservice 분리 (모놀리식 유지)
- ❌ Admin 백오피스 GUI (MVP는 SQL 직접 + 데이터 grip)

---

## 12. 변경 이력

| 날짜 | 버전 | 변경 |
|---|---|---|
| 2026-05-27 | 1.0 | 최초 작성 (Q1~Q5 결정 반영) |
