# 백엔드 기술 스택 요구사항 명세 v1

> 조언자에게 전달용 문서. 우리가 만들 시스템의 기능 요구사항과 운영 제약을 정리해서, 구체적인 기술 스택/호스팅 구성 추천을 받기 위함.

## 범례

- ✅ **확정**: 이미 결정된 사항. 변경 안 함
- 🟡 **잠정**: 현재 가정. 더 나은 대안 있으면 검토
- ❓ **미정**: 조언/추천 필요

---

## 1. 제품 개요

- **서비스**: 네일 예약 + 커뮤니티 플랫폼 (코드네임 "스네일")
- **클라이언트 구성**:
  - 유저 앱 (iOS, TestFlight) — 검색, 예약, 스네일(커뮤니티 게시물), 리뷰
  - 사장님 웹 (반응형) — 샵/디자이너/디자인/예약 관리
- **타겟 시장**: 한국 (사용자·사장님 모두 한국어)
- **핵심 특징**:
  - 네일 디자인 이미지를 LLM이 자동 분석(태그/색상/스타일 분류) → 검색에 활용
  - 예약 → 사장님 수락 → (계좌이체 샵의 경우) 예약금 입금 → 시술
  - 리뷰/스네일 커뮤니티 (좋아요/댓글/팔로우)

## 2. MVP 규모 추정 🟡

| 지표 | 초기(1~3개월) | 6개월 | 1년 |
|---|---|---|---|
| 유저 가입 수 | ~500 | ~5,000 | ~20,000 |
| 사장님(샵) 수 | ~30 | ~300 | ~1,000 |
| 등록 디자인 수 | ~600 | ~6,000 | ~30,000 |
| 일일 예약 건수 | ~30 | ~500 | ~3,000 |
| 일일 검색 쿼리 | ~1,000 | ~20,000 | ~100,000 |
| 일일 이미지 업로드 | ~100 | ~1,000 | ~5,000 |
| 동시 접속 (peak) | ~50 | ~500 | ~2,000 |

작은 규모로 시작하지만 검색·이미지 트래픽이 빠르게 늘 가능성 있음.

## 3. 시스템 구성요소

필수로 동작해야 할 컴포넌트:

| # | 컴포넌트 | 결정 상태 | 비고 |
|---|---|---|---|
| 1 | API 서버 (REST) | 🟡 가정 | 언어/프레임워크 미정 |
| 2 | 관계형 DB | 🟡 PostgreSQL 가정 | 트랜잭션·UNIQUE 제약·동시성 필요 |
| 3 | **검색 엔진** | ✅ **Elasticsearch + nori** | 한국어 형태소 분석 필수 |
| 4 | 캐시 + 작업 큐 | 🟡 Redis 가정 | 큐 워커도 같은 인스턴스로 |
| 5 | 객체 스토리지 (S3 호환) | 🟡 필요 | 이미지 저장 |
| 6 | CDN | 🟡 필요 | 이미지 전송 가속 |
| 7 | 백그라운드 워커 | 🟡 필요 | LLM 큐 컨슈머, 스케줄러 |
| 8 | LLM 서비스 | ❓ 외부 채택 vs 자체 | Transform + Classify 2단계 |
| 9 | 푸시 발송 (APNs) | ✅ Apple Push | iOS |
| 10 | 카카오 알림톡 발송 | ❓ 채널 선택 | 솔라피/알리고/네이버 SENS/카카오 비즈메시지 등 |
| 11 | 도메인 + SSL 인증서 | ✅ 필요 | HTTPS 필수 |

## 4. 컴포넌트별 요구 스펙

### 4.1 API 서버

- **프로토콜**: REST + JSON
- **인증**: 토큰 기반 (JWT 또는 동급)
  - 유저(Apple Sign In)와 사장님(이메일+비번) 분리
- **표준**:
  - Cursor 기반 페이지네이션 (limit 20 기본, 50 최대)
  - Idempotency-Key 헤더 지원 (예약 생성 등)
  - Rate limit (일반 분당 60, 검색 분당 30, 업로드/예약 더 낮게)
  - ISO 8601 시간, UTC 저장
- **에러 응답 표준화**: `{code, message, field_errors}` 형태
- **언어/프레임워크**: ❓ 추천 받고 싶음
  - 후보: FastAPI(Python), Express/Nest(Node), Spring Boot(Java), Go(Echo/Gin) 등
  - 팀 역량: 백엔드 직접 다룰 수 있음. 한국 시장 일반적 스택 선호
  - LLM 통합·이미지 처리에 유리한 생태계 우선

### 4.2 데이터베이스 (관계형)

- **요구 기능**:
  - 트랜잭션 (예약 더블부킹 방지 — DB UNIQUE + 트랜잭션 잠금)
  - 외래키 제약
  - JSON 컬럼 (business_hours, reservation_policy_snapshot, bank_transfer_guide_snapshot)
  - 인덱스 (소유권 검사용 owner_id, shop_id, reservation 슬롯 검색용 (designer_id, start_datetime))
- **데이터 보관 정책**:
  - 원본 이미지 영구 보관 (LLM 재처리용)
  - soft delete → 30일 후 hard delete 고려
- **백업**: 일 1회 자동 백업 (매니지드 DB 권장)
- **🟡 가정**: PostgreSQL. 다른 RDBMS 권장 시 의견 환영

### 4.3 검색 엔진 — Elasticsearch + nori ✅

핵심 요구:

- **한국어 형태소 분석**: nori 플러그인 (또는 동급) — "프렌치네일" / "프렌치 네일" 동일 토큰화
- **다중 필드 BM25 검색** (필드별 부스트):
  ```
  design.title         ^5.0
  design.owner_tags    ^4.0    (사장님 입력 태그)
  design.ai_tags       ^3.0    (LLM 자동 분류 태그)
  design.description   ^2.0
  shop.name            ^1.5
  shop.region          ^1.5    (예: "강남구", "성수동")
  ```
- **랭킹 보정** (function_score): 인기도(view+favorite+rating) 가중
- **오타 허용** (fuzziness: AUTO)
- **동의어 사전** (synonym 토큰 필터)
- **위치 검색**: geo_point + geo_distance sort
- **하이라이팅** (검색어 강조)
- **인덱스 동기화 패턴**: ❓ 추천 받고 싶음
  - 옵션 1: Transactional Outbox (DB 트랜잭션에 이벤트 적재 → 워커가 ES 반영)
  - 옵션 2: 큐 발행 (Kafka/SQS/Redis Streams) — LLM 분석 큐와 동일 라인
  - 옵션 3: Dual-write (간단하지만 일관성 약함)
- **인덱싱 대상**: Design, Shop, Review (3개 인덱스)

### 4.4 캐시 + 작업 큐

- **캐시 용도**: 디자인 상세, 샵 상세, 인기 디자인 리스트 (TTL 60~600s)
- **큐 용도**:
  - LLM 분석 작업 큐 (디자인 등록/이미지 변경 시 적재 → 워커가 Transform → Classify 순차 처리)
  - 스케줄 작업 (사장님 응답 리마인드 1시간 후 트리거, 일일 통계 등)
- **🟡 가정**: Redis (캐시 + 큐 + pub/sub 동시 활용)
- **대안**: SQS/SNS, Kafka 등 — MVP 규모에선 과할 가능성

### 4.5 객체 스토리지 + CDN

- **저장 대상**:
  - 디자인 이미지 (디자인당 최대 5장, 원본 + 리사이즈본)
  - 스네일 이미지 (게시물당 1~10장)
  - 리뷰 사진 (예약당 0~5장)
  - 프로필 사진 (유저, 디자이너, 샵 대표 이미지)
- **이미지 크기 정책** (이미 확정):
  - 프로필 512px
  - 썸네일 640px
  - 상세 1440px
  - 원본 2048px (LLM 재처리용)
  - 포맷: WebP/JPEG
- **요구 기능**:
  - presigned URL 발급 (클라이언트 직접 업로드)
  - 권한 분리 (원본은 사장님만, 가공본은 공개)
  - CDN 연동 (전송 가속)
- **🟡 가정**: AWS S3 + CloudFront, 또는 Cloudflare R2 + Cloudflare CDN, 또는 NCP Object Storage + CDN. 가격/연동 편의 기준 추천 부탁

### 4.6 이미지 처리 (리사이즈/변환)

- **방식 옵션** ❓:
  1. 자체 처리 (Pillow/sharp 등 라이브러리 + 워커에서 처리)
  2. CDN 측 변환 (Cloudflare Image Resizing, CloudFront Lambda@Edge, ImageKit, Imgix 등)
  3. 외부 서비스 (Cloudinary)
- **선호**: 단순한 자체 처리 또는 CDN 통합형

### 4.7 백그라운드 워커 + 스케줄러

- **워커 작업**:
  - LLM Transform 큐 컨슈머
  - LLM Classify 큐 컨슈머
  - ES 인덱싱 (디자인 CRUD 이벤트)
  - 이미지 리사이즈
  - 카카오 알림톡 / APNs 발송
- **스케줄러 작업**:
  - 사장님 응답 리마인드 (pending 1시간 경과 시 1회)
  - D-1, D-Day 예약 리마인드
  - 일일 통계 집계 (대시보드용)
  - soft delete 30일 후 hard delete 처리
- **🟡 후보**:
  - Celery + Redis broker (Python)
  - BullMQ (Node)
  - 단순 cron + DB 폴링 (MVP 규모)
- **선호**: 단일 워커 인스턴스에 모든 작업을 얹는 단순 구조

## 5. 외부 통합

### 5.1 LLM 서비스 — Transform + Classify

- **Transform**: 원본 이미지에서 네일 영역 추출 + 규격화 → cropped 이미지 반환
- **Classify**: cropped 이미지에서 태그/색상/스타일 분류
- **연동 방식**:
  - 동기 호출 (5초 이내) 또는 비동기 callback (10초 이상) 백엔드가 선택
- **요구**:
  - 한국어 태그 출력 가능 (표준 태그 사전 — `spec_text/12_llm.md` 참조)
  - 에러 코드 6종 (NO_NAIL/LOW_QUALITY/MULTIPLE_HANDS/OBSTRUCTED/INAPPROPRIATE/INTERNAL_ERROR)
- **결정 ❓**: 외부 서비스(예: 자체 fine-tuned 모델 + API) vs 자체 운영. 별도 LLM 작업자가 다룰 영역이지만 백엔드 호출 패턴은 정해야 함

### 5.2 APNs (iOS 푸시)

- Apple Developer 계정 + APNs 인증 키(.p8) 필요
- 토큰 기반 인증 권장 (인증서 방식보다 관리 쉬움)
- 발송량: 예약 확정/취소/리마인드 + 커뮤니티 알림 — 일 수천 건 규모로 시작

### 5.3 카카오 알림톡 발송

- **요구**: 사장님 휴대폰 번호로 알림 발송 (신규 예약, 응답 리마인드, 분석 완료/실패, 입금 알림 등 — `spec_text/13_notifications.md` 참조)
- **선결 조건**:
  - 한국 사업자 등록 필요
  - 발신 프로필 등록 + 알림톡 템플릿 사전 승인 (카카오 측 심사)
- **발송 채널 옵션** ❓:
  - 솔라피 (Solapi) — 간편 API, 종량제
  - 알리고 (Aligo)
  - 네이버 클라우드 SENS
  - 카카오 비즈메시지 직접 연동
- **선호**: API 깔끔하고 가격 합리적인 SaaS형 권장

## 6. 비기능 요구사항

### 6.1 성능

- **API 응답 시간**: p95 < 500ms (일반 조회)
- **검색 응답 시간**: p95 < 1초
- **이미지 업로드**: 클라이언트가 presigned URL로 직접 업로드 → 백엔드 부하 최소
- **LLM 분석**: 비동기 (사용자 대기 안 함). 큐 적재 → 1분 이내 처리 시작 목표
- **한국 사용자 latency**: 한국 region 또는 일본/홍콩 region (왕복 100ms 이내 권장)

### 6.2 가용성

- **MVP 목표**: 99% (월 7.2시간 다운타임 허용)
- **DB**: 자동 백업 + point-in-time recovery 가능하면 좋음
- **무중단 배포**: MVP에선 필수 아님 (몇 분 다운타임 허용)

### 6.3 보안

- HTTPS 필수 (Let's Encrypt 등 무료 인증서로 충분)
- 사장님 비밀번호: bcrypt/argon2 해싱
- 개인정보: 한국 개인정보보호법(PIPA) 준수
- 이미지 부적절 콘텐츠 차단 (LLM INAPPROPRIATE 코드 단계에서 처리)
- 권한 모델: 5종 (anonymous/user/owner/admin/system) — `spec_text/16_common_api_auth.md` 참조
- 사업자 인증 게이트: verification_status=approved 아닌 사장님은 운영 API 차단 (403 VERIFICATION_REQUIRED)
- 환경 변수 관리 (시크릿): 클라우드 시크릿 매니저 또는 .env 파일

### 6.4 운영

- **로그 수집**: 최소한 stdout → 클라우드 로그 (CloudWatch, Stackdriver, NCP Cloud Log 등)
- **모니터링**: 응답 시간, 에러율, DB 커넥션, ES 헬스체크 정도
- **알림**: 다운 시 슬랙/이메일 알림
- **CI/CD**: Git push → 자동 빌드/배포 (GitHub Actions 등)
- **환경 분리**: 최소 dev / prod 2단계, 가능하면 staging 추가

## 7. 한국 시장 특수 요구사항

- **사용자 latency**: 한국 IDC 또는 가까운 region (도쿄/홍콩) 우선
- **사업자 등록**: 카카오 알림톡 채널 등록을 위해 한국 사업자 등록증 필수
- **세금계산서**: 클라우드 비용 세금계산서 발행 가능하면 가산점 (NCP/카페24 등 국내 클라우드 유리)
- **결제 (운영 비용)**: 한국 카드/계좌이체 결제 지원 (해외 클라우드도 가능하지만 일부 마찰)
- **PG/결제 미구현**: MVP는 자체 결제 시스템 미구현. 카드 토큰화/PG 연동은 추후. 따라서 PCI-DSS 등 결제 규제 대상 아님

## 8. 미결정 — 조언자에게 추천 받고 싶은 항목

조언자가 우선적으로 의견 주시면 좋은 항목들:

1. **백엔드 언어/프레임워크 선택**
   - 한국 시장에서 채용 풀, 생태계, LLM/이미지 처리 라이브러리, 성능 종합 고려
2. **호스팅 사업자**
   - AWS Seoul vs NCP vs GCP Seoul vs 단순 VPS(Vultr/Lightsail 등)
   - MVP 비용 $30~100/월 범위에서 최적
3. **DB 매니지드 vs 자체 호스팅**
   - 매니지드 DB의 비용/편의 vs 단일 VM에 컨테이너로 띄우기
4. **Elasticsearch 호스팅**
   - 자체 호스팅 Docker vs Bonsai vs AWS OpenSearch vs Elastic Cloud
   - 매니지드 vs 직접 운영 트레이드오프
5. **객체 스토리지 + CDN 조합**
   - S3+CloudFront vs Cloudflare R2+CDN vs NCP Object Storage+CDN
   - 트래픽당 비용 비교
6. **카카오 알림톡 발송 채널**
   - 솔라피 vs 알리고 vs 네이버 SENS 등 — API 품질/가격
7. **큐/스케줄러 구현 방식**
   - Redis + Celery/BullMQ vs DB 폴링 + cron vs 클라우드 큐 서비스
8. **인덱스 동기화 패턴**
   - Transactional Outbox vs 직접 dual-write vs 메시지 큐 발행
9. **모니터링/로그 스택**
   - 클라우드 기본 도구 vs Datadog/Sentry/Grafana 같은 SaaS
10. **CI/CD 파이프라인**
    - GitHub Actions vs GitLab CI vs Jenkins 등

## 9. 참고 자료

같은 저장소(`spec_text/`)에 백엔드 협업 명세서 v3 전체가 있습니다. 필요 시 다음 페이지 참조:

- `spec_text/04_user_discovery_reservation.md` — 예약/검색 API와 동시성 정책
- `spec_text/05_owner_shop.md` — 사장님 계정/샵/디자이너 모델
- `spec_text/06_owner_design.md` — 디자인 모델 + AI 분석 상태
- `spec_text/12_llm.md` — LLM Transform/Classify API 요구
- `spec_text/13_notifications.md` — 알림 채널과 트리거
- `spec_text/14_decisions.md` — 의사결정 기록 (확정 정책 모음)
- `spec_text/16_common_api_auth.md` — 공통 응답·에러·권한·rate limit·사업자 인증 게이트

추가 질문 환영합니다.
