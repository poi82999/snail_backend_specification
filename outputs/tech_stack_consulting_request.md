# s-nail 기술 스택 컨설팅 요청

**To** 기술 스택 컨설턴트
**From** 신민석 (백엔드)
**소요** 15~20분
**응답 형식** 각 질문에 선택 + 한두 줄 근거

---

## 1. 한 줄 요약

**네일 디자인을 통합 검색·예약하고, 본인 네일 스타일을 공유하는 커뮤니티 모바일 서비스**

- **iOS 유저 앱** + **반응형 사장님 웹** + **백엔드 API** + **LLM 분석 서버** 4축 구조
- **8주 안에 MVP → 2026.07.18 데모데이** (VC 시연)
- 운영 비용 **월 50만원 이내**

---

## 2. 프로젝트 요약

| 항목 | 값 |
| --- | --- |
| 서비스 | 네일 디자인 검색 + 결제 없는 예약 + 스타일 공유 커뮤니티 |
| 구조 | iOS 유저앱 / 사장님 반응형 웹 / 백엔드 API / LLM 분석 서버 |
| 일정 | 2026.07.18 데모데이 (8주) |
| 트래픽 | 동시 100명, 디자인 500개, 베타 100~200명 |
| 외부 의존 | LLM 분석 서버(자체), APNs, 카카오 알림톡, S3 |
| 운영 예산 | 월 50만원 이내 |
| 데이터 성격 | 강한 관계형, 트랜잭션 필수 (예약 7상태 머신, UNIQUE 제약) |
| 까다로운 부분 | 예약 상태머신 / LLM 비동기(5~30s) / 자연어 검색 / 이미지 파이프라인 |

---

## 3. 팀 구성

| 멤버 | 역할 |
| --- | --- |
| 신민석 | 백엔드 + LLM 연동 + 인프라 |
| 곽민지 | iOS 유저앱 |
| 안유진 | UI 디자이너 + 사장님 웹 프론트 겸임 |
| 김예은 | 팀장 + 영업 + LLM 모델 |

---

## 4. 락된 항목 (검토 제외)

- 유저 클라이언트: iOS (Apple Sign In, TestFlight)
- 사장님 클라이언트: 반응형 웹
- 결제: MVP 제외
- 사장님 알림: 카카오 알림톡 / 유저 알림: APNs
- DB: PostgreSQL 단일 통합 (회의 "DB 2개 분리"안 폐기)
- 백엔드 기반: Node.js 20 + NestJS + Prisma + Redis/BullMQ + S3/CloudFront

---

## 5. 팀이 원래 던졌던 결정 항목 (참고)

| # | 항목 | 입장 |
| --- | --- | --- |
| 1 | 클라우드 선택 (AWS/GCP/etc) | 아무거나 OK, 월 50만원 내 운영 가능했으면 |
| 2 | 백엔드 언어/프레임워크 | 편한 걸로 |
| 3 | DB 종류 (Postgres/MySQL/Mongo) | 회의에선 "DB 2개 분리"로 합의 → 단일 통합으로 폐기 |
| 4 | LLM 서빙 방식 | 자체 GPU vs 외부 API — 8주 일정 고려 |
| 5 | 작업 큐 시스템 | LLM 비동기 처리용 |
| 6 | 이미지 저장소 + CDN | S3 + CloudFront? R2? |
| 7 | 배포/CI-CD | TestFlight + 백엔드 배포 |

---

# 결정 요청

## Q1. 클라우드 사업자

**조건**: 월 50만원 이내, 1인 운영, 국내 사용자, RDS·Redis·Meilisearch 호스팅 필요

- A. AWS Seoul
- B. Naver Cloud
- C. Railway / Render
- D. 기타

**선택**:
**근거**:

---

## Q2. 백엔드 언어

**조건**: 1인 백엔드, 외부 LLM 통신 다수, 카카오 알림톡 연동, 8주 일정

- A. Node.js 20 + NestJS (잠정)
- B. Python + FastAPI
- C. 기타

**선택**:
**근거**:

---

## Q3. 검색 엔진

**조건**: "여리여리한 핑크 네일" 같은 한국어 자연어 입력 → 태그/동의어/오타 매칭. 디자인 500개, 1인 운영.

- A. Meilisearch (잠정, 추후 ES로 마이그)
- B. PostgreSQL pg_trgm
- C. Elasticsearch + Nori (day 1부터)

**선택**:
**근거**:

---

## Q4. LLM 서빙 ⭐ 가장 중요

**작업**: ①네일 영역 추출(Transform) + ②태그/색상 분류(Classification) 2단계
**호출**: 디자인 등록 시 1회, 처리 5~30초, 누적 500회/8주
**예산**: 월 5만원 이내 희망

**Q4-1 모델 / 서빙 방식**

- A. 외부 Vision API (OpenAI gpt-4o / Claude / Gemini)
- B. HuggingFace Inference API (SAM + CLIP)
- C. 자체 GPU 인스턴스 (AWS g4/g5)
- D. Replicate.com (서버리스 GPU)
- E. 하이브리드 (Segmentation 따로 + 분류 따로)

**선택**:
**근거 / 예상 비용**:

**Q4-2 백엔드 ↔ LLM 통신**

- A. 비동기 webhook (잠정)
- B. 동기 호출 + 폴링
- 인증: HMAC / JWT / 기타

**선택**:

---

## Q5. 데모데이 운영 리스크

**Q5-1 8주 안에 절대 손대면 안 되는 함정 3개**

1.
2.
3.

**Q5-2 데모데이 당일 시연 안정성**

- 무대 와이파이 끊겨도 시연 가능하게 하려면:
- 배포 사고 시 5분 안에 이전 버전 복귀하려면:

**Q5-3 카카오 알림톡 심사 일정**

- 템플릿 심사 보통 며칠:
- 데모 전 발송 테스트 확보하려면 언제 신청:

---

## Q6. 보안 / 운영 최소선

현재 적용 예정: HTTPS, helmet, CORS 화이트리스트, throttler, argon2, JWT, Prisma(SQLi 차단), Presigned URL, Sentry, JSON 로그

- 충분 / 추가 →
- 백업 정책 추천:
- 시크릿 관리 추천:

---

## 백엔드 지뢰 체크

**지뢰 있는 항목만 표시**

| 카테고리 | 선택 | 지뢰? |
| --- | --- | --- |
| 검증/문서 | class-validator + @nestjs/swagger |  |
| 로깅 | nestjs-pino + Sentry |  |
| 시간 | date-fns + date-fns-tz |  |
| ID | UUID v7 (public) / BIGINT (internal) |  |
| HTTP 클라이언트 | @nestjs/axios + axios-retry |  |
| APNs | @parse/node-apn |  |
| 보안 | helmet + @nestjs/throttler(Redis) |  |
| Idempotency | Interceptor + Redis TTL 24h |  |
| 공통 응답 | Global Interceptor data/request_id |  |
| 공통 에러 | Global ExceptionFilter |  |
| 테스트 | Jest + Testcontainers(PG) |  |
| 로컬 환경 | docker-compose (PG/Redis/Meilisearch) |  |
| API 버전 | /v1 prefix |  |

---

## 보너스

- 시스템 아키텍처 다이어그램은 우리가 그림
- 놓친 의사결정 카테고리가 있다면:

---

## 첨부

| 파일 | 용도 |
| --- | --- |
| backend_spec_v3.summary.md | Q4 LLM 명세, 예약 상태표 |
| user_scenarios_v3_mvp.txt | 도메인 상세 (시나리오 173개) |
| 회의록 2026.05.25 | DB 분리안 폐기 배경 |
| 제품요구사항 문서 | 화면별 기능 + 우선순위 |
