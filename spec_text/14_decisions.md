# 14.의사결정기록

확정 의사결정과 팀 내부 결정 필요 사항을 관리합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "decisions": [
    [
      "커뮤니티 구조",
      "통합 커뮤니티 1개. 디자인 진입 시 그 디자인의 스네일/리뷰 노출"
    ],
    [
      "검색 결과 범위",
      "디자인 + 샵 + 리뷰 + 찜한 사람 수 표시. 디자이너 단독 검색 제외"
    ],
    [
      "디자인 vs 스네일 분리",
      "디자인은 사장님 등록 상품, 스네일은 유저 자유 공유"
    ],
    [
      "디자인 사용자 노출 조건",
      "사용자 검색/피드/디자인 상세 노출은 owner.verification_status=approved AND shop.visibility=active AND design.visibility=active AND design.ai_analysis_status=done 조합을 모두 충족해야 한다. owner_tags는 0~N개 자유 입력(필수 아님)이며 노출 필수 조건에서 제외한다"
    ],
    [
      "디자인 등록 비동기 처리",
      "사장님 [등록] 클릭 → 즉시 200 OK 반환 + DB에 visibility=active, ai_analysis_status=pending으로 저장. LLM 분석은 별도 큐에서 비동기 처리. 사장님은 분석 완료를 기다릴 필요 없음"
    ],
    [
      "사장님 태그 vs AI 태그 분리",
      "owner_tags(사장님 직접 입력, 0~N개 자유)와 ai_tags(LLM 생성, 표준 사전 내)는 다른 필드로 저장. 검색에서 둘 다 활용하되 owner_tags가 더 높은 가중치(사장님 의도 신호로 해석). UI에서 출처 구분 가능하게 설계"
    ],
    [
      "디자인 visibility와 AI 분석 상태 분리",
      "Design.visibility(draft/active/hidden, 사장님 통제)와 Design.ai_analysis_status(pending/in_progress/done/failed, 시스템 통제)는 별도 필드. 검색 노출은 둘의 조합으로 판정"
    ],
    [
      "댓글 권한",
      "댓글/대댓글 누구나 가능, depth 2까지"
    ],
    [
      "리뷰 정책",
      "1예약=1리뷰, 샵 별점만, 사진 최대 5장, 선택"
    ],
    [
      "MVP 예약 결제",
      "MVP 앱은 PG·환불 시스템을 구현하지 않는다. 예약금(deposit) 개념은 채택하되, 샵 등록 시 payment_method를 'on_site'(현장결제 = 예약금 없음, 시술 당일 전액 결제) 또는 'bank_transfer_guide'(계좌이체 예약금 안내) 중 선택한다. 계좌이체 샵은 샵 단위 고정 정액 deposit_amount + 계좌 3필드(bank_name/bank_account_number/bank_account_holder)를 등록하며, 앱은 이를 그대로 노출만 하고 입금 여부는 자동 검증하지 않는다"
    ],
    [
      "자동수락 ⟹ 현장결제 강제",
      "auto_accept=true인 샵은 payment_method=on_site만 허용. 자동수락은 사장님이 매번 관여하지 않는 모드인데 계좌이체 예약금은 입금 모니터링/미입금 수동 취소를 사장님이 책임져야 하는 구조라 충돌. 따라서 샵 옵션 조합은 (자동수락+현장결제), (수동수락+현장결제), (수동수락+계좌이체) 3가지로 제한. (자동수락+계좌이체) 조합은 VALIDATION_ERROR로 거부"
    ],
    [
      "수락/입금확인 확정 흐름",
      "현장결제 샵은 사장님 [수락] 클릭 즉시 status=confirmed. 계좌이체 예약금 안내 샵은 사장님 [수락] 시 status=payment_pending으로 전환하고 유저에게 예약금/계좌 정보를 안내한다. 유저가 [입금 완료]를 누른 뒤 사장님이 통장 확인 후 [입금 확인됨]을 눌러야 status=confirmed가 된다"
    ],
    [
      "유저 [입금 완료] 알림 버튼",
      "계좌이체 예약금 안내 샵의 payment_pending 예약에서만 노출. 유저가 한 번 누르면 사장님에게 카카오 알림톡 + 알림함 적재 + user_payment_notified_at 기록. 재클릭 불가(409). 이 버튼만으로는 confirmed가 되지 않으며, 사장님이 통장 확인 후 [입금 확인됨]을 눌러야 confirmed로 전환"
    ],
    [
      "입금 분쟁 플랫폼 비개입",
      "계좌이체는 앱 밖에서 일어나는 거래이므로 입금 진위·금액·시각·환불 관련 분쟁에 플랫폼이 개입하지 않는다. 환불 테이블·자동 환불 워크플로우는 만들지 않는다. PG 도입 시점에 재검토"
    ],
    [
      "사장님 응답 자동 만료 없음",
      "pending 상태가 시간이 지나도 시스템이 자동으로 거절/취소하지 않는다. 사장님에게 리마인드 알림 1회만 발송. 유저는 pending 상태에서 직접 취소 가능"
    ],
    [
      "사장님 응답 리마인드 기준",
      "pending 예약이 생성 후 1시간 경과해도 응답이 없으면 사장님에게 리마인드 알림(카카오 알림톡 + 알림함) 1회 발송. reservation.reminder_sent_at에 발송 시각 기록 → 재발송 차단. 자동수락 샵(auto_accept=true)에서는 pending 상태가 존재하지 않으므로 발생하지 않음. (프론트와 시간값 추가 협의 가능)"
    ],
    [
      "예약 슬롯 선착순 잠금",
      "단순 pending은 슬롯을 hard-lock하지 않는다. 같은 슬롯에 여러 pending 요청이 생길 수 있으며, 사장님 웹은 미처리 pending 목록을 created_at 오름차순(먼저 예약 요청한 순서)으로 보여준다. 사장님이 수락할 때 슬롯을 재점검하고, 이미 payment_pending/confirmed가 같은 슬롯을 점유하면 409로 막는다"
    ],
    [
      "유저당 동시 예약 1건 제한",
      "한 유저는 시작~종료가 겹치는 다른 pending/payment_pending/confirmed 예약을 동시에 가질 수 없다. 위반 요청은 409"
    ],
    [
      "사장님 웹 단수 샵 정책",
      "MVP는 1사장님=1샵 단수 구조로 구현한다. Shop.owner_id는 UNIQUE이며 사장님 웹 API는 /owner/shop, /owner/designs, /owner/designers처럼 shop_id를 숨긴 단수 샵 기준으로 제공한다. 여러 샵 운영은 계정 여러 개로 처리"
    ],
    [
      "사업자 승인 전 초안 작성",
      "verification_status가 approved가 아니어도 사장님은 샵/디자이너/디자인 초안을 작성할 수 있다. 단, 유저에게 공개되는 active 전환과 예약 접수/예약 처리 API는 approved 이후에만 허용한다"
    ],
    [
      "디자이너 자동 배정",
      "미선택 시 가능한 디자이너 중 랜덤"
    ],
    [
      "사장님 알림 방식",
      "카카오 알림톡 + 사장님 웹 알림함(in-app inbox, OwnerNotification 엔티티). 웹푸시 MVP 제외. 알림함은 모든 사장님 대상 알림을 영속화하여 사장님이 카톡을 놓쳐도 웹 접속 시 다시 확인 가능"
    ],
    [
      "검색 0건 처리",
      "유사 디자인 추천"
    ],
    [
      "이미지 압축",
      "프로필 512, 썸네일 640, 상세 1440, 원본 2048. WebP/JPEG"
    ],
    [
      "데이터 영구성",
      "원본 영구 보관, soft delete 30일 후 hard delete"
    ],
    [
      "시간/버저닝",
      "DB UTC, API ISO 8601, /v1 버저닝, Rate Limit"
    ],
    [
      "예약 동시성",
      "DB UNIQUE + 트랜잭션, 충돌 시 409, Idempotency-Key 필수"
    ],
    [
      "예약 가격 스냅샷",
      "예약 시점 가격을 reservations.total_price에 저장"
    ],
    [
      "검색 엔진 채택",
      "Elasticsearch + nori 플러그인을 MVP부터 도입. 한국어 형태소 분석 필수, 필드 부스팅·BM25·function_score·geo_distance·fuzziness·synonym 등 native 지원. Postgres FTS/Meilisearch는 한국어 정확도 약해 비채택. 자체 호스팅 Docker로 시작 가능($0 추가 비용), 추후 매니지드 이전 검토"
    ],
    [
      "검색 필드 가중치 (시작값)",
      "design.title^5.0 / design.owner_tags^4.0 / design.ai_tags^3.0 / design.description^2.0 / shop.name^1.5 / shop.region^1.5. owner_tags가 ai_tags보다 1.33배 가중(업계 평균 1.2~1.5x 범위). 운영 후 검색 로그 기반 튜닝"
    ],
    [
      "검색 필터 결합 규칙",
      "같은 필드 내 다중값(예: colors=[핑크,레드])은 OR, 다른 필드 간(예: colors AND moods)은 AND. q와 필터 조합은 AND. price/duration 범위는 min ≤ x ≤ max"
    ],
    [
      "검색 정렬 정책",
      "q 있으면 기본 sort=relevance, q 없으면 기본 sort=popular, 클라이언트가 명시한 sort가 있으면 그것 우선. 허용값: relevance/popular/latest/price_asc/price_desc/rating/distance(lat,lng 동반 시)"
    ],
    [
      "검색 0건 폴백",
      "결과 0건 시 응답 data 배열은 [] 유지하고 별도 recommendations 필드에 유사 디자인 N개 채워 반환. 프론트는 '검색 결과가 없습니다' 메시지와 '이 디자인은 어떠세요?' 추천 섹션 분리 노출. 유사 산정은 q 토큰 완화 + ai_tags 매칭"
    ],
    [
      "위치 검색 처리",
      "Shop.region 필드를 주소에서 자동 파싱(예: '서울 강남구'). ES 인덱스에 디자인 문서로 denormalize. 검색 쿼리 q에 '강남' 들어오면 region 매칭. 별도 region=강남구 필터도 지원. distance sort는 lat/lng/radius 동반 시 ES geo_distance"
    ],
    [
      "자동완성/인기 태그 MVP 제외",
      "GET /tags/suggest, GET /tags/popular API 미구현. 위치 검색은 검색 태그(q)로 처리, 별도 자동완성 자료 풀 운영 안 함"
    ],
    [
      "AI 분석 상태 표시 단위",
      "백엔드 DB는 4단계(pending/in_progress/done/failed) 유지. 사장님 화면은 3단계로 묶어 표시(pending+in_progress = '분석 중' / done = '분석 완료' / failed = '분석 실패'). 큐 대기와 처리 중 구분이 사장님에게 큰 의미 없음"
    ],
    [
      "auto_accept 기본값",
      "샵 생성 시 auto_accept 기본값 = false(수동수락). 자동수락은 운영 자신감 생긴 사장님이 명시적으로 켜는 옵션"
    ],
    [
      "샵 사정 취소 사유 필수",
      "POST /owner/reservations/{id}/cancel 호출 시 reason 필수(텍스트 입력). 유저에게 알림과 함께 사유 전달. 거절(reject)의 사유 필수와 통일"
    ],
    [
      "노쇼 처리 MVP 방어적 구현",
      "MVP에서는 노쇼를 금전/패널티 자동 처리와 연결하지 않고 예약 상태 기록으로만 남긴다. 백엔드는 confirmed 예약만, 시술 시작 30분 이후에만 no_show 전환을 허용하고 completed/cancelled/rejected/payment_pending 상태에서는 409로 차단한다"
    ],
    [
      "확정 예약 있는 디자인 삭제 정책",
      "사장님이 DELETE /owner/designs/{id} 호출 시 즉시 hard delete 안 함. visibility=hidden 자동 전환 + soft delete 마킹 → 신규 노출 차단, 기존 confirmed 예약은 그대로 유지. 모든 관련 예약이 완료/취소된 후에야 30일 후 hard delete"
    ],
    [
      "예약 캘린더 일간/주간 뷰",
      "MVP는 월간만. 백엔드 GET /owner/reservations는 from/to 임의 범위 지원하므로 추후 일간/주간 추가 시 백엔드 변경 없음"
    ],
    [
      "리뷰 정렬 옵션",
      "GET /shops/{id}/reviews 의 sort 허용값: latest(기본) / rating_desc / rating_asc. 'helpful'(like_count 기반)은 like_count 필드는 있으나 정렬 옵션은 MVP 제외"
    ],
    [
      "로그인 실패 횟수 제한",
      "사장님 로그인 5회 연속 실패 시 5분 잠금. Redis에 owner_id+IP 기준 카운터 + TTL 5분. 잠금 해제 후 카운터 리셋"
    ],
    [
      "비밀번호 재설정 MVP 포함",
      "사장님 비밀번호 재설정 기능 MVP 포함. 2단계: (1) POST /owner/auth/password-reset/request로 이메일에 토큰 발송 (2) POST /owner/auth/password-reset/confirm으로 토큰+신규 비번 제출. 토큰은 15분 TTL, 1회 사용"
    ],
    [
      "예약금 금액 가이드",
      "deposit_amount 최소 1,000원, 최대 디자인 가격(base_price) 100%까지 허용. 0원은 허용 안 함(예약금 의미 상실). '말이 되는 범위'만 백엔드가 검증, 그 이상의 운영 규약은 추후 서비스 약관으로 처리"
    ],
    [
      "비밀번호 정책",
      "사장님 비밀번호: 8자 이상 + 영문/숫자 조합 1개 이상. 특수문자는 강제 안 함. 너무 흔한 비번 차단은 MVP 제외"
    ],
    [
      "로그아웃 토큰 처리",
      "JWT 사용 시 클라이언트가 access token 삭제 + 서버에 단기 블랙리스트(Redis, 토큰 만료시각까지 TTL). 짧은 access token + refresh token 분리 권장"
    ],
    [
      "이미지 업로드 정책",
      "클라이언트 직접 업로드(presigned URL 방식). 백엔드는 presigned URL 발급 시점에 권한 1회 체크(누가 어디에 업로드하는지). 파일당 최대 10MB 제한. 업로드 완료 후 백엔드 워커가 4단계 리사이즈(프로필 512 / 썸네일 640 / 상세 1440 / 원본 2048) + WebP/JPEG 변환하여 객체 스토리지에 저장. DB에는 URL만 보관"
    ],
    [
      "카카오 알림톡 발송 실패 처리",
      "카톡 발송 실패해도 OwnerNotification 알림함은 적재 (사장님이 웹 접속 시 확인 가능). 발송 실패 로그 보관 + 자동 재시도 3회(지수 backoff: 1s/5s/30s). 최종 실패해도 알림함 적재는 유지"
    ],
    [
      "CSV export MVP 제외",
      "예약 내역 CSV 다운로드는 MVP 1차 출시에서 제외, post-MVP 우선순위 큐로 분류. 사장님 운영 피드백 받고 필요한 컬럼·기간 필터 구체화 후 추가. 백엔드 API는 추가 시 GET /owner/reservations/export?from=&to=&status=&format=csv 형태로 from/to 최대 90일 범위 제한"
    ]
  ],
  "internal_decisions_needed": [
    {
      "topic": "문서 버전 전략",
      "decision_needed": "v3를 계속 수정할지, v4 파일로 분리해 확정본을 만들지 결정",
      "owner": "팀 내부"
    },
    {
      "topic": "향후 결제 기능 범위",
      "decision_needed": "PG(토스/카카오페이 등) 연동 도입 시점 결정. MVP는 결제 미구현, payment_method 안내만",
      "owner": "팀 내부"
    },
    {
      "topic": "예약 운영 안내 문구",
      "decision_needed": "유저에게 보여줄 취소/노쇼/변경/계좌이체 안내 문구 카피 확정 (백엔드는 자리만 제공)",
      "owner": "프론트/기획"
    },
    {
      "topic": "결제 없는 예약 보완 기준 수치",
      "decision_needed": "유저 활성 예약 수 상한 N건, 노쇼/취소 N회 누적 시 제재 정책 수치 결정",
      "owner": "팀 내부"
    },
    {
      "topic": "사장님 응답 리마인드 시간값 재확정",
      "decision_needed": "1시간으로 우선 확정함. 프론트와 협의 후 1h/2h/6h 중 최종 시간값 재확정 가능. 운영 데이터 모니터링 후 조정 권장",
      "owner": "프론트/기획"
    },
    {
      "topic": "계좌이체 예약금 안내 푸시 노출 방식",
      "decision_needed": "수락 푸시 본문에 예약금 금액 + 계좌 정보(은행명/계좌번호/예금주)를 직접 넣을지, 푸시는 짧게 두고 앱 내 예약 상세 화면에서만 노출할지 결정",
      "owner": "프론트"
    },
    {
      "topic": "[입금 완료] 버튼 노출 위치/조건",
      "decision_needed": "예약 상세 화면 어디에 둘지, 클릭 후 비활성 상태의 문구를 어떻게 표시할지 ('사장님이 확인 중입니다' 외)",
      "owner": "프론트"
    },
    {
      "topic": "AI 분석 실패 시 자동 재시도 정책",
      "decision_needed": "ai_analysis_status=failed로 떨어지기 전 자동 재시도 횟수, 간격 결정 (예: 3회 / 지수 backoff). 그리고 최종 실패 시 사장님 알림 시점",
      "owner": "백엔드/LLM"
    },
    {
      "topic": "사장님 태그 입력 가이드",
      "decision_needed": "owner_tags는 0개 허용으로 확정. 권장 개수/최대 개수/태그 길이 제한/금칙어 정책 결정",
      "owner": "팀 내부"
    },
    {
      "topic": "AI 분석 진행 중 사장님 화면 표시",
      "decision_needed": "'분석 중', '곧 노출됩니다' 같은 안내 카피와 예상 소요 시간 표시 여부 결정",
      "owner": "프론트/기획"
    },
    {
      "topic": "예약 슬롯 단위",
      "decision_needed": "15분 단위와 30분 단위 중 MVP 기본값 결정",
      "owner": "팀 내부"
    },
    {
      "topic": "예약 버퍼 시간",
      "decision_needed": "시술 전후 준비/정리 시간을 둘지, 둔다면 어디에 설정할지 결정",
      "owner": "팀 내부"
    },
    {
      "topic": "당일 예약 마감",
      "decision_needed": "몇 시간 전까지 예약 가능한지 기본 정책 결정",
      "owner": "팀 내부"
    },
    {
      "topic": "사장님 휴대폰 인증 추가 도입 여부",
      "decision_needed": "이메일+비번 + 사업자 인증 + (확정) 사업자 승인 전 운영 API 게이트 외에, 휴대폰 인증을 추가로 둘지 결정. MVP 운영 후 사장님 계정 도용 사고 빈도 보고 판단",
      "owner": "팀 내부"
    },
    {
      "topic": "어드민 범위",
      "decision_needed": "MVP에서 실제 어드민을 만들지, 운영자가 DB/내부툴로 처리할지 결정",
      "owner": "팀 내부"
    },
    {
      "topic": "공통 API 형식",
      "decision_needed": "에러 응답, 페이지네이션, cursor, rate limit 문구의 기본안을 백엔드가 먼저 고정할지 결정",
      "owner": "백엔드"
    },
    {
      "topic": "LLM 책임 경계",
      "decision_needed": "이미지 저장, callback 인증, 재시도, 모델 버전 표기를 LLM 작업자가 제안하면 백엔드가 수용하는 방식으로 갈지 결정",
      "owner": "백엔드/LLM"
    }
  ],
  "policies": {
    "search": [
      "검색 엔진: Elasticsearch + nori (MVP부터 도입)",
      "검색 결과 범위는 디자인, 샵, 리뷰",
      "날짜 조건은 검색에서 제외하고 상세/예약 화면에서 가용 시간 조회",
      "찜한 사람 수 표시",
      "디자이너 단독 검색 제외 (Designer.specialty_tags는 디스플레이 전용)",
      "0건 시 응답 data=[] + recommendations 별도 필드 (UI는 빈 결과 메시지 + 추천 섹션 분리)",
      "디자인 검색 대상: visibility=active AND ai_analysis_status=done인 것만. owner_tags는 0개여도 검색/노출 가능",
      "필드 가중치: title^5 / owner_tags^4 / ai_tags^3 / description^2 / shop.name^1.5 / shop.region^1.5",
      "필터 결합: 같은 필드 내 OR, 다른 필드 간 AND",
      "정렬: q있으면 relevance 기본, q없으면 popular 기본, 클라이언트 sort 명시 시 그것 우선. 허용값 relevance/popular/latest/price_asc/price_desc/rating/distance",
      "위치 처리: Shop.region 자동 파싱 + ES 인덱스 denormalize. distance sort는 lat/lng/radius 동반",
      "자동완성/인기 태그 API는 MVP 제외"
    ],
    "design": [
      "사장님 등록은 즉시 응답, AI 분석은 비동기 큐",
      "사용자 노출 조건: owner.verification_status=approved AND shop.visibility=active AND design.visibility=active AND ai_analysis_status=done. owner_tags는 0~N개 자유 입력",
      "owner_tags와 ai_tags는 다른 필드로 보관. 검색 가중치 owner_tags > ai_tags",
      "visibility(사장님 통제, draft/active/hidden)와 ai_analysis_status(시스템 통제, pending/in_progress/done/failed) 분리",
      "AI 분석 실패 시 visibility는 active 유지하되 노출은 안 됨 → 재분석 요청으로 회복 가능",
      "디자인 이미지는 1~5장. 등록/추가 API 모두 총 5장 제한을 백엔드가 검증하며, 이미지 추가/삭제 시 ai_analysis_status를 자동 pending으로 되돌리고 LLM 큐 재투입",
      "사장님 화면에서 AI 분석 상태는 3단계로 표시: '분석 중'(pending+in_progress) / '분석 완료' / '분석 실패'",
      "확정 예약 있는 디자인 삭제 시 hard delete 안 함 — visibility=hidden + soft delete, 관련 예약 완료/취소 후 30일 후 hard delete"
    ],
    "reservation": [
      "디자이너 미선택 시 가능한 디자이너 중 랜덤 배정",
      "MVP 앱은 PG 미구현. 예약금 개념은 채택. 샵당 payment_method ∈ {on_site(예약금 없음), bank_transfer_guide(계좌이체 예약금 안내)}",
      "계좌이체 샵은 샵 단위 고정 정액 deposit_amount + 계좌 3필드(bank_name/bank_account_number/bank_account_holder) 등록",
      "현장결제 샵은 deposit_amount = null, 시술 당일 전액 결제. [입금 완료] 버튼 및 계좌/예약금 안내 UI 모두 비노출",
      "auto_accept=true ⟹ payment_method=on_site 강제. (자동수락+계좌이체) 조합은 VALIDATION_ERROR",
      "현장결제 샵은 사장님 수락 = 예약 확정. 계좌이체 샵은 사장님 수락 후 payment_pending, 유저 [입금 완료] 후 사장님 [입금 확인됨] 처리 시 confirmed",
      "[입금 완료] 버튼은 계좌이체 샵의 payment_pending 예약에서만 노출, 1회만 클릭 가능, 단독으로 confirmed 전환하지 않음",
      "입금 진위·환불 분쟁은 플랫폼 비개입",
      "취소/거절/노쇼는 앱 내 금전 처리 없이 예약 상태로 관리",
      "Idempotency-Key 필수",
      "DB UNIQUE + 트랜잭션으로 더블부킹 방지",
      "단순 pending은 슬롯 hard-lock에서 제외. 사장님 웹 pending 목록은 created_at 오름차순으로 표시하고, 수락 시 payment_pending/confirmed 충돌을 재점검",
      "유저당 같은 시간대 pending/payment_pending/confirmed 동시 예약 1건 제한",
      "예약 시점 가격·결제방식·예약금 금액·계좌 정보(JSON)를 reservations에 스냅샷 저장",
      "활성 예약 수 제한, 노쇼/취소 이력, 리마인드로 노쇼 리스크 보완"
    ],
    "community": [
      "통합 커뮤니티",
      "커뮤니티 탭은 스네일, 랭킹, 팔로잉",
      "스네일은 누구나 작성 가능",
      "디자인 태그 스네일은 디자인 상세에 노출",
      "스네일은 별점이 없고 샵 평점에 반영하지 않음"
    ],
    "review": [
      "1 reservation = 최대 1 review",
      "샵 별점만 저장",
      "디자이너 개별 별점 없음",
      "사진 최대 5장",
      "리뷰 작성은 선택"
    ],
    "notification": [
      "유저는 APNs",
      "사장님은 카카오 알림톡 + 사장님 웹 알림함(OwnerNotification 엔티티)",
      "사장님 알림은 카톡 전송과 동시에 알림함에도 적재. 카톡 전송 실패해도 알림함은 적재됨",
      "카톡 발송 실패 시 자동 재시도 3회 (지수 backoff 1s/5s/30s). 최종 실패 시에도 알림함 적재는 유지",
      "웹푸시는 MVP 제외"
    ],
    "storage": [
      "원본 이미지는 LLM 재처리를 위해 보관",
      "soft delete 후 30일 뒤 hard delete 고려",
      "이미지 업로드는 presigned URL 방식 — 백엔드는 발급 시점 1회 권한 체크, 클라이언트 직접 객체 스토리지 업로드",
      "업로드 파일당 최대 10MB",
      "디자인 이미지는 리소스 API 반영 시 디자인당 총 5장 제한",
      "업로드 완료 후 백엔드 워커가 4단계 리사이즈(512/640/1440/2048) + WebP/JPEG 변환 후 저장"
    ],
    "auth": [
      "사장님 비밀번호 8자 이상 + 영문/숫자 조합 1개 이상 (특수문자 강제 안 함)",
      "사장님 로그인 5회 연속 실패 시 5분 잠금 (Redis 카운터 + TTL)",
      "사장님 비밀번호 재설정 = 이메일 토큰 2단계 (request → confirm, 토큰 15분 TTL 1회 사용)",
      "JWT 사용 시 로그아웃은 클라이언트 토큰 삭제 + 서버 단기 블랙리스트(Redis, 토큰 만료까지 TTL)",
      "verification_status != approved 사장님은 운영 API 차단 (403 VERIFICATION_REQUIRED, 상세 16.공통_API권한 verification_gate)"
    ],
    "standards": [
      "DB 시간은 UTC",
      "API 시간은 ISO 8601",
      "API 버전은 /v1",
      "Rate limit 적용"
    ]
  },
  "page_guides": {
    "14.의사결정기록": {
      "covers": "이미 확정된 정책과 아직 팀 내부 결정이 필요한 항목",
      "related_work": "팀 회의, 정책 확정, 문서 버전 관리",
      "how_to_use": "이미 결정된 내용은 다시 논쟁하지 않고, 미결정 항목만 회의에서 확정한다"
    }
  }
}
```
