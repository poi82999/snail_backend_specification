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
      "사장님 수락/자동수락",
      "예약 완료"
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
      "process_note": "결제 없이 예약 요청 생성. 샵 자동수락이면 즉시 확정",
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
      "next_status": "confirmed",
      "process_note": "금전 처리 없음",
      "user_app_display": "예약 완료",
      "owner_web_display": "확정 예약 표시",
      "collaborator_check": "수락 후 버튼 상태"
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
      "current_status": "confirmed",
      "actor": "owner",
      "action": "샵 사정 취소",
      "api": "POST /owner/reservations/{id}/cancel",
      "next_status": "cancelled_by_shop",
      "process_note": "사장님이 확정 예약 취소",
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
      "process_note": "앱 내 금전 처리 없이 노쇼 상태 표시",
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
      "pending 또는 confirmed 예약과 겹치는 디자이너 제외",
      "rejected/cancelled_by_user/cancelled_by_shop 예약은 슬롯 점유에서 제외",
      "유저가 디자이너를 선택하지 않으면 가능한 디자이너 중 랜덤 배정",
      "가능한 디자이너가 0명이면 예약 불가"
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
      "예약 전후 버퍼 시간 설정 위치"
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
        "pending/confirmed/rejected/cancelled_by_user/cancelled_by_shop/no_show/completed"
      ],
      [
        "total_price",
        "int",
        "자동",
        "예약 시점 총액 스냅샷"
      ],
      [
        "reservation_policy_snapshot",
        "JSON",
        "자동",
        "예약 시점 예약 운영 안내 스냅샷"
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
        "통합 검색",
        "q, region, duration_min, duration_max, price_min, price_max, colors[], moods[], sort, cursor"
      ],
      [
        "GET /designs/search",
        "디자인 검색",
        "q, tags[], colors[], moods[], price_min, price_max, duration_min, duration_max, shop_id, sort, cursor"
      ],
      [
        "GET /shops/search",
        "샵 검색",
        "q, region, lat, lng, radius, cursor"
      ],
      [
        "GET /reviews/search",
        "리뷰 검색",
        "q, tags[]"
      ],
      [
        "GET /tags/suggest",
        "태그 자동완성",
        "q"
      ],
      [
        "GET /tags/popular",
        "인기 태그",
        "-"
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
        "design_id, designer_id?, start_datetime, user_request_memo, Idempotency-Key header"
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
      ]
    ]
  },
  "page_guides": {
    "4.유저(앱)_탐색예약": {
      "covers": "검색, 피드, 디자인 상세, 찜, 예약 요청, 예약 상태, 가용 시간",
      "related_work": "앱 홈, 검색 결과, 디자인 상세, 예약 시간 선택, 예약 요청, 내 예약 화면",
      "how_to_use": "각 상태에서 어떤 버튼을 보여줄지, 예약 충돌/예약 취소/사장님 거절을 어떻게 보여줄지 확인한다"
    }
  }
}
```
