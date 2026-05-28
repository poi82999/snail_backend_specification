# 4.유저(앱)_탐색예약

검색/피드/예약 API, 예약 엔티티, 상태 전이, 가용 슬롯 규칙을 관리합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "reservation_statuses": [
    [
      "pending",
      "사장님 수락 대기",
      "예약 요청 생성 직후",
      "승인 대기 중"
    ],
    [
      "confirmed",
      "확정",
      "현장결제 샵 사장님 수락/자동수락 또는 계좌이체 샵 입금 확인 완료",
      "예약 완료"
    ],
    [
      "payment_pending",
      "입금 확인 대기",
      "계좌이체 샵에서 사장님이 예약 요청을 수락해 계좌 안내를 보낸 직후",
      "입금 확인 대기"
    ],
    [
      "rejected",
      "거절",
      "사장님 거절",
      "거절됨"
    ],
    [
      "cancelled_by_user",
      "유저 취소",
      "유저 취소",
      "취소됨"
    ],
    [
      "cancelled_by_shop",
      "샵 취소",
      "샵 취소",
      "샵 사정으로 취소됨"
    ],
    [
      "no_show",
      "노쇼",
      "시술 30분 후",
      "노쇼 처리됨"
    ],
    [
      "completed",
      "완료",
      "시술 시간 종료",
      "리뷰 작성하기 유도"
    ]
  ],
  "reservation_state_transitions": [
    {
      "current_status": "before_create",
      "actor": "user",
      "action": "예약 요청 생성",
      "api": "POST /reservations",
      "next_status": "pending 또는 confirmed",
      "process_note": "결제 없이 예약 요청 생성. 기본은 수동수락(false)이라 pending으로 생성. 자동수락 샵은 현장결제만 허용되며 즉시 confirmed",
      "user_app_display": "승인 대기/예약 완료",
      "owner_web_display": "신규 예약 노출",
      "collaborator_check": "예약 요청 중 로딩, 실패 화면"
    },
    {
      "current_status": "pending",
      "actor": "user",
      "action": "예약 취소",
      "api": "DELETE /reservations/{id}",
      "next_status": "cancelled_by_user",
      "process_note": "예약 요청 취소",
      "user_app_display": "취소됨",
      "owner_web_display": "취소 예약 표시",
      "collaborator_check": "취소 전 확인 모달"
    },
    {
      "current_status": "pending",
      "actor": "owner",
      "action": "예약 수락",
      "api": "POST /owner/reservations/{id}/accept",
      "next_status": "confirmed 또는 payment_pending",
      "process_note": "현장결제 샵은 즉시 confirmed. 계좌이체 예약금 안내 샵은 payment_pending으로 전환하고 유저에게 예약금 금액 + 계좌 정보(은행명/계좌번호/예금주)를 안내. 최종 confirmed는 사장님이 통장 확인 후 payment-confirmed를 눌러야 함",
      "user_app_display": "현장결제는 예약 완료. 계좌이체는 입금 안내 + [입금 완료] 버튼",
      "owner_web_display": "현장결제는 확정 예약, 계좌이체는 입금 확인 대기 예약",
      "collaborator_check": "수락 후 결제 방식별 버튼 상태, 계좌이체 안내 노출 UI"
    },
    {
      "current_status": "payment_pending",
      "actor": "user",
      "action": "[입금 완료] 알림 (계좌이체 예약금 안내 예약만)",
      "api": "POST /reservations/{id}/payment-notified",
      "next_status": "payment_pending",
      "process_note": "상태 변경 없음. 사장님에게 카카오 알림톡 + 알림함 적재 + user_payment_notified_at 기록. 한 번만 가능 (재클릭 차단). payment_method_snapshot=on_site인 예약에서는 호출 불가",
      "user_app_display": "사장님이 확인 중입니다 (시한 없음)",
      "owner_web_display": "예약 상세에 '입금 확인 요청' 뱃지 노출 (owner_payment_confirmed_at IS NULL인 동안)",
      "collaborator_check": "버튼 한 번 클릭 후 비활성 처리, 미클릭 상태 UI, 알림톡 문구"
    },
    {
      "current_status": "payment_pending",
      "actor": "owner",
      "action": "[입금 확인됨] 처리 (통장 확인 후)",
      "api": "POST /owner/reservations/{id}/payment-confirmed",
      "next_status": "confirmed",
      "process_note": "owner_payment_confirmed_at 기록 후 status=confirmed. 조건: status=payment_pending AND payment_method_snapshot=bank_transfer_guide AND user_payment_notified_at != null AND owner_payment_confirmed_at IS NULL. 그 외 조건에서는 409. 미입금인 경우 사장님은 이 버튼 대신 [샵 사정 취소]를 눌러야 함",
      "user_app_display": "예약 완료",
      "owner_web_display": "확정 예약 표시 + 뱃지 제거",
      "collaborator_check": "뱃지 클릭 시 [입금 확인됨] / [샵 사정 취소] 두 선택지 모달, 미처리 상태 UI"
    },
    {
      "current_status": "pending",
      "actor": "owner",
      "action": "예약 거절",
      "api": "POST /owner/reservations/{id}/reject",
      "next_status": "rejected",
      "process_note": "사장님이 예약 요청 거절",
      "user_app_display": "거절됨",
      "owner_web_display": "거절 예약 표시",
      "collaborator_check": "거절 사유 입력 여부"
    },
    {
      "current_status": "confirmed",
      "actor": "user",
      "action": "예약 취소",
      "api": "DELETE /reservations/{id}",
      "next_status": "cancelled_by_user",
      "process_note": "확정 예약 취소",
      "user_app_display": "취소됨",
      "owner_web_display": "취소 예약 표시",
      "collaborator_check": "취소 전 안내 문구"
    },
    {
      "current_status": "payment_pending 또는 confirmed",
      "actor": "owner",
      "action": "샵 사정 취소",
      "api": "POST /owner/reservations/{id}/cancel",
      "next_status": "cancelled_by_shop",
      "process_note": "사장님이 입금 대기 또는 확정 예약 취소",
      "user_app_display": "샵 사정으로 취소됨",
      "owner_web_display": "취소 처리 완료",
      "collaborator_check": "사유 필수 여부"
    },
    {
      "current_status": "confirmed",
      "actor": "owner/system",
      "action": "시술 완료 처리",
      "api": "POST /owner/reservations/{id}/complete",
      "next_status": "completed",
      "process_note": "금전 처리 없음",
      "user_app_display": "리뷰 작성 유도",
      "owner_web_display": "완료 예약 표시",
      "collaborator_check": "자동 완료 시점"
    },
    {
      "current_status": "confirmed",
      "actor": "owner",
      "action": "노쇼 처리",
      "api": "POST /owner/reservations/{id}/no-show",
      "next_status": "no_show",
      "process_note": "MVP에서는 앱 내 금전/패널티 자동 처리 없이 노쇼 상태 기록만 남김. 조건: status=confirmed AND now >= start_datetime + 30분. completed/cancelled/rejected/payment_pending 상태에서는 409",
      "user_app_display": "노쇼 처리됨",
      "owner_web_display": "노쇼 예약 표시",
      "collaborator_check": "노쇼 처리 가능 시간"
    },
    {
      "current_status": "completed",
      "actor": "user",
      "action": "리뷰 작성",
      "api": "POST /reservations/{id}/review",
      "next_status": "completed",
      "process_note": "금전 처리 없음",
      "user_app_display": "리뷰 작성 완료",
      "owner_web_display": "새 리뷰 표시",
      "collaborator_check": "리뷰 작성 버튼 노출 기간"
    }
  ],
  "availability_rules": {
    "purpose": "유저 앱 예약 시간 선택 화면과 백엔드 슬롯 계산 기준을 맞추기 위한 기본안",
    "backend_default_rules": [
      "DB는 UTC, 앱/웹 표시는 샵 로컬 시간대 기준",
      "MVP 기본 슬롯 단위는 30분",
      "디자인 duration_minutes로 종료 시간 계산",
      "영업시간 밖 슬롯은 노출하지 않음",
      "샵 휴무일과 디자이너 휴무/비활성 상태 제외",
      "confirmed 또는 payment_pending 예약과 겹치는 디자이너 제외. 단순 pending 예약은 슬롯을 hard-lock하지 않으며, 같은 슬롯의 미처리 요청은 사장님 웹 pending 목록에 생성 순서(created_at 오름차순)로 표시",
      "rejected/cancelled_by_user/cancelled_by_shop 예약은 슬롯 점유에서 제외",
      "유저가 디자이너를 선택하지 않으면 가능한 디자이너 중 랜덤 배정",
      "가능한 디자이너가 0명이면 예약 불가",
      "한 유저는 같은 시간대(시작~종료 겹침)에 다른 pending/payment_pending/confirmed 예약을 가질 수 없음 (유저당 동시 예약 1건 제한)",
      "동시 예약 요청 충돌 시 DB 트랜잭션 잠금으로 한 건만 성공, 진 요청은 409 CONFLICT 응답",
      "사장님 무응답 시 자동 만료 없음. pending 상태에서도 유저는 직접 취소 가능 (DELETE /reservations/{id})",
      "사장님 수락 처리 시 슬롯 재점검 + 트랜잭션 잠금. 이미 payment_pending/confirmed 예약이 같은 슬롯을 점유했으면 409 CONFLICT. 같은 슬롯에 pending 요청이 여러 개 있으면 사장님 웹은 생성 순서로 보여주고 사장이 먼저 들어온 요청부터 처리하도록 유도"
    ],
    "team_decisions_needed": [
      "슬롯 단위를 30분으로 확정할지 15분을 허용할지",
      "당일 예약 마감 시간을 둘지",
      "예약 전후 버퍼 시간을 둘지",
      "임시 휴무/반차 입력 UI를 MVP에 포함할지"
    ],
    "suggested_response_fields": [
      "date",
      "timezone",
      "slot_unit_minutes",
      "slots[].start_datetime",
      "slots[].local_time_label",
      "slots[].available",
      "slots[].available_designer_count",
      "slots[].available_designer_ids"
    ],
    "collaborator_checks": [
      "불가 슬롯을 숨길지 비활성으로 보여줄지",
      "자동 배정 문구를 어디에 표시할지",
      "가능한 디자이너가 0명일 때 빈 상태 문구",
      "당일 예약 마감 기준",
      "예약 전후 버퍼 시간 설정 위치",
      "동시 예약 요청 충돌(409) 시 유저 안내 문구",
      "유저당 같은 시간대 중복 예약 시도 시 안내 문구",
      "사장님 응답 대기(pending) 상태에서 유저 [예약 취소] 버튼 노출 정책"
    ]
  },
  "entities": {
    "Reservation": [
      [
        "reservation_id",
        "UUID",
        "자동",
        "백엔드 생성"
      ],
      [
        "user_id",
        "UUID",
        "필수",
        "예약한 유저"
      ],
      [
        "shop_id",
        "UUID",
        "필수",
        "예약 대상 샵"
      ],
      [
        "design_id",
        "UUID",
        "필수",
        "예약 대상 디자인"
      ],
      [
        "designer_id",
        "UUID",
        "필수",
        "최종 배정 디자이너. 자동 배정이어도 저장"
      ],
      [
        "assigned_by",
        "enum",
        "자동",
        "user/auto"
      ],
      [
        "start_datetime",
        "timestamp",
        "필수",
        "UTC 저장, API는 ISO 8601"
      ],
      [
        "end_datetime",
        "timestamp",
        "자동",
        "start_datetime + duration_minutes"
      ],
      [
        "duration_minutes",
        "int",
        "자동",
        "예약 시점 디자인 소요시간 스냅샷"
      ],
      [
        "status",
        "enum",
        "자동",
        "pending/payment_pending/confirmed/rejected/cancelled_by_user/cancelled_by_shop/no_show/completed"
      ],
      [
        "total_price",
        "int",
        "자동",
        "예약 시점 총액 스냅샷"
      ],
      [
        "selected_option_ids",
        "UUID[]",
        "선택",
        "예약 시 유저가 선택한 디자인 옵션 ID 목록. 옵션 가격/소요시간 delta가 total_price/end_datetime 계산에 반영됨"
      ],
      [
        "reservation_policy_snapshot",
        "JSON",
        "자동",
        "예약 시점 예약 운영 안내 스냅샷"
      ],
      [
        "payment_method_snapshot",
        "enum",
        "자동",
        "예약 시점 샵 결제 방식 스냅샷. on_site(예약금 없음) / bank_transfer_guide(계좌이체 예약금 안내). 사장님이 나중에 바꿔도 기존 예약은 당시 값 유지"
      ],
      [
        "deposit_amount_snapshot",
        "int",
        "자동",
        "예약 시점 예약금 금액 스냅샷. payment_method_snapshot=bank_transfer_guide일 때만 채워짐. 사장님이 샵 deposit_amount를 바꿔도 기존 예약은 당시 금액 유지"
      ],
      [
        "bank_transfer_guide_snapshot",
        "JSON",
        "자동",
        "예약 시점 계좌 정보 스냅샷. payment_method_snapshot=bank_transfer_guide일 때만 채워짐. {bank_name, bank_account_number, bank_account_holder} 형태. 사장님이 계좌를 바꿔도 기존 예약은 당시 정보 그대로 노출"
      ],
      [
        "user_payment_notified_at",
        "timestamp",
        "자동",
        "payment_pending 상태에서 유저가 [입금 완료] 버튼을 누른 시각. null이면 미클릭. 한 번 채워지면 다시 누를 수 없음 (재클릭 차단용)"
      ],
      [
        "owner_payment_confirmed_at",
        "timestamp",
        "자동",
        "사장님이 통장에서 입금 확인 후 [입금 확인됨] 버튼을 누른 시각. payment_pending + user_payment_notified_at != null인 계좌이체 예약에서만 의미 있음. 채워지면 status=confirmed로 전환되고 뱃지 사라짐"
      ],
      [
        "reminder_sent_at",
        "timestamp",
        "자동",
        "사장님 응답 리마인드 알림 발송 시각. pending 상태가 1시간 이상 방치되면 스케줄러가 1회 발송하고 채움. null이면 미발송, 채워지면 재발송 차단"
      ],
      [
        "idempotency_key",
        "string",
        "필수",
        "예약 생성 중복 방지"
      ],
      [
        "user_request_memo",
        "text",
        "선택",
        "유저 요청사항"
      ],
      [
        "cancel_reason",
        "text",
        "선택",
        "취소/거절 사유"
      ],
      [
        "cancelled_at",
        "timestamp",
        "자동",
        "취소 시각"
      ],
      [
        "completed_at",
        "timestamp",
        "자동",
        "완료 시각"
      ],
      [
        "no_show_at",
        "timestamp",
        "자동",
        "노쇼 처리 시각"
      ],
      [
        "created_at",
        "timestamp",
        "자동",
        "예약 생성 시각"
      ]
    ],
    "IdempotencyKey": [
      [
        "key",
        "string",
        "필수",
        "클라이언트가 보낸 Idempotency-Key"
      ],
      [
        "scope",
        "string",
        "필수",
        "예: create_reservation"
      ],
      [
        "actor_type",
        "enum",
        "필수",
        "user/owner/admin/system"
      ],
      [
        "actor_id",
        "UUID",
        "필수",
        "요청 주체 ID"
      ],
      [
        "request_hash",
        "string",
        "필수",
        "요청 body 해시. 다른 body 재사용 방지"
      ],
      [
        "response_status_code",
        "int",
        "자동",
        "완료된 요청의 HTTP status"
      ],
      [
        "response_body_snapshot",
        "JSON",
        "자동",
        "동일 요청 재응답용"
      ],
      [
        "status",
        "enum",
        "자동",
        "processing/completed/failed"
      ],
      [
        "locked_until",
        "timestamp",
        "자동",
        "처리 중 잠금 만료"
      ],
      [
        "expires_at",
        "timestamp",
        "자동",
        "키 보관 만료"
      ],
      [
        "created_at",
        "timestamp",
        "자동",
        "생성 시각"
      ]
    ]
  },
  "apis": {
    "search": [
      [
        "GET /feed",
        "홈 피드",
        "cursor, limit, location_lat, location_lng"
      ],
      [
        "GET /search",
        "통합 검색 (디자인+샵+리뷰 묶음 응답). ES 기반. sort 허용값: relevance(q있을 때 기본)/popular(q없을 때 기본)/latest/price_asc/price_desc/rating/distance",
        "q, region, lat, lng, radius, duration_min, duration_max, price_min, price_max, colors[], moods[], sort, cursor"
      ],
      [
        "GET /designs/search",
        "디자인 검색. ES 기반. 응답 0건 시 recommendations 필드에 유사 디자인 N개 채워 반환(별도 섹션 표시용). sort 허용값: relevance(q있을 때 기본)/popular(q없을 때 기본)/latest/price_asc/price_desc/rating/distance(lat,lng 동반)",
        "q, tags[], colors[], moods[], price_min, price_max, duration_min, duration_max, shop_id, region, lat, lng, radius, sort, cursor"
      ],
      [
        "GET /shops/search",
        "샵 검색. distance sort 시 lat/lng/radius 동반",
        "q, region, lat, lng, radius, sort, cursor"
      ],
      [
        "GET /shops",
        "공개 샵 목록/지도 뷰포트 조회. bbox와 location_tag로 현재 지도 영역 또는 지역 태그에 맞는 샵을 반환",
        "bbox(minLng,minLat,maxLng,maxLat), location_tag"
      ],
      [
        "GET /reviews/search",
        "리뷰 검색",
        "q, tags[]"
      ],
      [
        "GET /designs/{id}",
        "디자인 상세",
        "스네일/리뷰 포함"
      ],
      [
        "GET /shops/{id}",
        "샵 상세",
        "디자이너/디자인/스네일/리뷰 포함"
      ],
      [
        "POST /designs/{id}/favorite",
        "찜하기",
        "-"
      ],
      [
        "DELETE /designs/{id}/favorite",
        "찜 해제",
        "-"
      ],
      [
        "GET /users/me/favorites",
        "내 찜 목록",
        "cursor"
      ]
    ],
    "reservation": [
      [
        "GET /designs/{id}/available-slots",
        "가용 시간 조회",
        "date"
      ],
      [
        "GET /designs/{id}/reservation-info",
        "예약 전 안내 정보 조회",
        "-"
      ],
      [
        "POST /reservations",
        "예약 요청 생성",
        "design_id, designer_id?, start_datetime, selected_option_ids?, user_request_memo, Idempotency-Key header"
      ],
      [
        "GET /reservations/me",
        "내 예약 목록",
        "status"
      ],
      [
        "GET /reservations/{id}",
        "예약 상세",
        "-"
      ],
      [
        "DELETE /reservations/{id}",
        "예약 취소",
        "reason"
      ],
      [
        "POST /reservations/{id}/payment-notified",
        "[입금 완료] 버튼 — payment_pending 상태에서 유저가 계좌이체 후 사장님에게 확인 요청 알림 발송. 예약 status는 변하지 않음. user_payment_notified_at이 채워지면 409 (중복 클릭 차단). payment_method_snapshot=bank_transfer_guide인 예약에서만 허용",
        "-"
      ]
    ]
  },
  "page_guides": {
    "4.유저(앱)_탐색예약": {
      "covers": "검색, 피드, 디자인 상세, 찜, 예약 요청, 예약 상태, 가용 시간, 예약금 금액 + 계좌이체 안내 노출 및 [입금 완료] 버튼 (계좌이체 샵 한정)",
      "related_work": "앱 홈, 검색 결과, 디자인 상세, 예약 시간 선택, 예약 요청, 내 예약 화면, 예약 확정 후 예약금/계좌 안내",
      "how_to_use": "각 상태에서 어떤 버튼을 보여줄지, 예약 충돌/예약 취소/사장님 거절을 어떻게 보여줄지 확인한다. 계좌이체 샵은 사장님 수락 후 payment_pending 상태에서 예약금 금액 + 계좌 정보(은행명/계좌번호/예금주)를 노출하고, 유저 [입금 완료] 이후 사장님 [입금 확인됨] 처리 시 confirmed가 되는 흐름을 확인한다. 현장결제(on_site) 샵에서는 예약금 관련 UI 모두 비노출"
    }
  }
}
```
