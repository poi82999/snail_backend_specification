# W0 체크리스트 — 개발 시작 전 1주

작성 기준일: 2026-05-27

---

## ✅ 이미 완료 (Claude가 처리)

### 백엔드 스캐폴드 [`backend/`](backend/)
- [x] Python 프로젝트 설정 — [`pyproject.toml`](backend/pyproject.toml) (ruff + mypy + pytest)
- [x] 의존성 — [`requirements.txt`](backend/requirements.txt), [`requirements-dev.txt`](backend/requirements-dev.txt)
- [x] `.gitignore`, `.env.example`, `.python-version`
- [x] FastAPI 앱 — [`app/main.py`](backend/app/main.py) (lifespan, CORS, Sentry, request_id 미들웨어)
- [x] 설정 — [`app/core/config.py`](backend/app/core/config.py) (pydantic-settings, prod 검증)
- [x] DB/Redis 어댑터 — [`app/core/database.py`](backend/app/core/database.py), [`app/core/redis.py`](backend/app/core/redis.py)
- [x] 로깅 — [`app/core/logging.py`](backend/app/core/logging.py) (structlog JSON)
- [x] 헬스체크 — [`app/api/v1/health.py`](backend/app/api/v1/health.py)
- [x] 에러 핸들러 — [`app/api/errors.py`](backend/app/api/errors.py)
- [x] Base 모델 + Mixin — [`app/models/base.py`](backend/app/models/base.py)
- [x] 단위 테스트 골격 — [`tests/conftest.py`](backend/tests/conftest.py), [`tests/unit/test_config.py`](backend/tests/unit/test_config.py)

### Alembic
- [x] [`alembic.ini`](backend/alembic.ini), [`alembic/env.py`](backend/alembic/env.py) (async)
- [x] 초기 마이그레이션 — pgvector / pg_trgm / uuid-ossp / btree_gin 확장 ([`20260527_0001`](backend/alembic/versions/20260527_0001_initial_extensions.py))

### Docker
- [x] [`docker/Dockerfile`](backend/docker/Dockerfile) — multi-stage, non-root, healthcheck, tini
- [x] [`docker/docker-compose.yml`](backend/docker/docker-compose.yml) — 로컬 (pgvector + redis + api)
- [x] [`docker/docker-compose.prod.yml`](backend/docker/docker-compose.prod.yml) — 운영 (Caddy + Cloud SQL Proxy)
- [x] [`docker/Caddyfile`](backend/docker/Caddyfile) — 보안 헤더, prod /docs 차단
- [x] `.dockerignore`

### CI/CD
- [x] [`.github/workflows/ci.yml`](backend/.github/workflows/ci.yml) — ruff, mypy, pytest(+pg/redis), docker build
- [x] [`.github/workflows/deploy.yml`](backend/.github/workflows/deploy.yml) — GCR push → SSH → compose up → alembic → health check

### 보안
- [x] [`.pre-commit-config.yaml`](backend/.pre-commit-config.yaml) — trailing whitespace, large files, **gitleaks**, ruff, mypy
- [x] [`.gitleaks.toml`](backend/.gitleaks.toml) — OpenAI/GCP/Kakao 키 패턴 추가

### 법무 초안
- [x] [`legal/privacy_policy.draft.md`](legal/privacy_policy.draft.md)
- [x] [`legal/terms_of_service.draft.md`](legal/terms_of_service.draft.md)
- [x] [`legal/README.md`](legal/README.md) — placeholder 안내

### 백엔드 README
- [x] [`backend/README.md`](backend/README.md)

---

## 🙋 사용자가 직접 해야 할 일

> 모두 **외부 계정/결제/심사**가 필요해서 제가 못 합니다.
> 리드타임이 긴 것부터 정렬했습니다.

### A. 사업자 / 법적 준비 (리드타임 1~10일)
- [ ] **사업자등록 신청** (홈택스 또는 세무서 방문 — 1~2일)
- [ ] 통신판매업 신고 (시·군·구청, 사업자등록 후)
- [ ] [`legal/`](legal/) 초안의 `{{...}}` placeholder 전부 채우기
- [ ] **법무 검토** 받기 (개인정보처리방침은 필수)

### B. 결제 계정 (즉시~7일)
- [ ] **GCP 결제계정 생성** + $300 크레딧 활성화
  - [ ] **Billing → Budgets & alerts**에 $50/$80/$100 알림 3단계 등록
  - [ ] Project 생성, Project ID 결정
- [ ] **OpenAI 계정** + 결제수단 등록 + 첫 $5 결제 (Tier-1 진입)
  - [ ] **Settings → Limits → Hard limit $50** 설정
- [ ] **Apple Developer Program 결제** ($99/년)
  - [ ] 개인 vs 사업자(DUNS) 선택 — 사업자가 신뢰도 ↑이지만 리드타임 2주+

### C. 카카오 알림톡 (리드타임 5~10영업일)
- [ ] **카카오톡 채널** 개설 ([center-pf.kakao.com](https://center-pf.kakao.com))
- [ ] **Bizppurio / Aligo / NHN Cloud** 중 발송사 1개 선택 후 가입
- [ ] **알림톡 발신프로필** 등록 → 카카오 심사 (3~7영업일)
- [ ] 알림톡 **템플릿 사전 심사** 신청 (예약확정/거절/리마인드 등) — 템플릿당 2~5영업일

### D. 도메인 / DNS (즉시~1일)
- [ ] 도메인 구입 (가비아, Cloudflare Registrar, Namecheap 등)
- [ ] **Cloudflare**에 도메인 등록 → DNS A 레코드 (GCE IP), `api.xxx` 서브도메인 분리
- [ ] Cloudflare SSL 모드: **Full (strict)** 권장 (Caddy가 자체 LE 발급)

### D-2. 로컬 개발 환경 (🔴 즉시 — A1 통합 테스트도 막혔던 항목)
- [ ] **Docker Desktop for Windows** 설치 — https://www.docker.com/products/docker-desktop/
  - 설치 후 WSL2 백엔드 활성화 (안내 따라가면 자동)
  - PowerShell에서 `docker --version`, `docker compose version` 확인
- [ ] backend 로컬 인프라 기동: `cd backend && docker compose -f docker/docker-compose.yml up -d postgres redis`
- [ ] 통합 테스트 확인: `cd backend && .venv\Scripts\python.exe -m pytest -q`

### E. GitHub (즉시)
- [ ] 새 저장소 생성 (`snail-backend` 또는 기존 repo의 `backend/` 사용)
- [ ] 다음 **Repository Secrets** 등록:
  - `GCP_PROJECT_ID`
  - `GCP_SA_KEY` (서비스 계정 JSON)
  - `GCE_HOST`, `GCE_USER`, `GCE_SSH_PRIVATE_KEY`
  - `CLOUD_SQL_INSTANCE_CONNECTION_NAME`
  - `API_DOMAIN`
- [ ] Branch protection (main): PR 필수 + ci.yml 통과 강제
- [ ] `pre-commit install` 로컬 실행

### F. Apple 개발자 작업 (Apple Dev 가입 후 1~3일)
- [ ] **App ID** 생성 (`com.{{your}}.snail`)
- [ ] **Sign In with Apple** capability 활성화 + **Services ID** 생성
- [ ] **APNs Authentication Key (.p8)** 생성 — Key ID, Team ID 메모
- [ ] **App Store Connect**에 앱 등록 (메타데이터만, 빌드는 W7에)

### G. App Store 준비물 (병행)
- [ ] 앱 아이콘 (1024x1024)
- [ ] 스크린샷 (6.7" / 6.5" / 5.5" iPhone)
- [ ] 앱 설명, 키워드, 카테고리
- [ ] 지원 URL, 마케팅 URL, 개인정보처리방침 URL
- [ ] 심사용 데모 계정 (이용자 1, 사장님 1)

---

## 📅 권장 W0 일정 (1주)

| 일차 | 액션 | 비고 |
|---|---|---|
| Day 1 | 사업자등록 신청 + GCP 결제 + Apple Dev 결제 | 동시 진행 |
| Day 2 | 도메인 구입 + Cloudflare 연결 + 카카오톡 채널 개설 | Bizppurio 가입 |
| Day 3 | OpenAI 결제 + 알림톡 발신프로필 신청 | 심사 대기 시작 |
| Day 4 | 법무 초안 검토 의뢰 (변호사) + GitHub repo + secrets 등록 | |
| Day 5 | Apple 키 발급(.p8) + GCP 프로젝트/Cloud SQL 인스턴스 생성 | |
| Day 6 | 로컬 `docker compose up` 으로 빈 FastAPI 띄우기 확인 | 첫 commit |
| Day 7 | CI 통과 확인 + deploy.yml 첫 시도 (빈 인스턴스로) | W1 시작 준비 완료 |

---

## ⚠️ 시작 전 마지막 점검

- [ ] `.env`가 절대 git에 안 올라가는지 확인 (`git status`로 검증)
- [ ] gitleaks 한 번 돌리기: `pre-commit run gitleaks --all-files`
- [ ] OpenAI/GCP 둘 다 **하드 리밋/예산 알림** 걸려있는지 재확인
- [ ] 1Password 등 비밀번호 관리자에 GCP/OpenAI/Apple/카카오 계정 저장
- [ ] 동료 1명에게 **인스턴스 재시작·로그 보는 법** 공유 (1인 운영 백업)
