# 13.알림

APNs, 카카오 알림톡 등 알림 종류를 관리합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "notifications": [
    [
      "신규 예약 요청",
      "사장님",
      "카카오 알림톡 + 알림함"
    ],
    [
      "예약 수락/입금 안내 (계좌이체 예약금 안내 샵은 payment_pending 상태에서 예약금 금액 + 계좌 정보 포함)",
      "유저",
      "APNs"
    ],
    [
      "유저 [입금 완료] 알림 — 사장님에게 통장 확인 요청",
      "사장님",
      "카카오 알림톡 + 알림함"
    ],
    [
      "입금 확인 완료 / 예약 확정",
      "유저",
      "APNs"
    ],
    [
      "사장님 예약 응답 권고 리마인드 — pending이 1시간 이상 방치된 경우 알림 1회 (자동 만료 X, 수동수락 샵만 해당)",
      "사장님",
      "카카오 알림톡 + 알림함"
    ],
    [
      "예약 거절",
      "유저",
      "APNs"
    ],
    [
      "D-1 리마인드",
      "유저",
      "APNs"
    ],
    [
      "D-Day 리마인드",
      "유저",
      "APNs"
    ],
    [
      "유저 예약 취소",
      "사장님",
      "카카오 알림톡 + 알림함"
    ],
    [
      "샵 측 취소",
      "유저",
      "APNs"
    ],
    [
      "리뷰/스네일 작성 권유",
      "유저",
      "APNs"
    ],
    [
      "디자인 분석 완료",
      "사장님",
      "카카오 알림톡 + 알림함"
    ],
    [
      "디자인 분석 실패",
      "사장님",
      "카카오 알림톡 + 알림함"
    ],
    [
      "내 스네일에 좋아요",
      "유저",
      "APNs"
    ],
    [
      "내 스네일에 댓글",
      "유저",
      "APNs"
    ],
    [
      "내 리뷰에 샵 답변",
      "유저",
      "APNs"
    ],
    [
      "본인 샵 태그 스네일",
      "사장님",
      "카카오 알림톡 + 알림함"
    ],
    [
      "새 리뷰 작성됨",
      "사장님",
      "카카오 알림톡 + 알림함"
    ],
    [
      "팔로우 알림",
      "유저",
      "APNs"
    ]
  ],
  "entities": {
    "OwnerNotification": [
      [
        "notification_id",
        "UUID",
        "자동",
        "백엔드 생성"
      ],
      [
        "owner_id",
        "UUID",
        "필수",
        "수신 사장님"
      ],
      [
        "type",
        "enum",
        "필수",
        "reservation_new / reservation_cancelled / payment_notified / payment_confirmed / pending_remind / design_analysis_done / design_analysis_failed / snap_tagged / review_new / review_replied 등"
      ],
      [
        "title",
        "string",
        "필수",
        "알림함 리스트에 표시할 제목"
      ],
      [
        "body",
        "text",
        "선택",
        "본문 미리보기"
      ],
      [
        "deeplink_target",
        "string",
        "선택",
        "클릭 시 이동할 사장님 웹 경로. 예: /reservations/{id}, /designs/{id}, /reviews/{id}"
      ],
      [
        "related_resource_type",
        "enum",
        "선택",
        "reservation / design / review / snap. 필터/그룹핑용"
      ],
      [
        "related_resource_id",
        "UUID",
        "선택",
        "참조 리소스 ID"
      ],
      [
        "is_read",
        "bool",
        "자동",
        "기본 false. 사장님이 알림 클릭 또는 [모두 읽음] 호출 시 true"
      ],
      [
        "read_at",
        "timestamp",
        "자동",
        "읽음 처리 시각"
      ],
      [
        "kakao_sent_at",
        "timestamp",
        "자동",
        "카카오 알림톡 전송 시각 (전송 실패해도 알림함에는 적재)"
      ],
      [
        "created_at",
        "timestamp",
        "자동",
        "발생 시각"
      ]
    ]
  },
  "apis": {
    "owner_notification": [
      [
        "GET /owner/notifications",
        "사장님 알림함 목록 (최신순)",
        "is_read, type, cursor"
      ],
      [
        "GET /owner/notifications/unread-count",
        "미읽음 알림 개수 — 대시보드/헤더 뱃지용",
        "-"
      ],
      [
        "PATCH /owner/notifications/{notification_id}/read",
        "단건 읽음 처리",
        "-"
      ],
      [
        "POST /owner/notifications/read-all",
        "전체 읽음 처리",
        "-"
      ]
    ]
  },
  "page_guides": {
    "13.알림": {
      "covers": "유저 APNs, 사장님 카카오 알림톡 + 알림함(in-app inbox), 예약/리뷰/스네일/LLM 분석 알림, 예약금/계좌 안내 및 [입금 완료] 알림",
      "related_work": "앱 푸시, 사장님 카톡 알림, 사장님 웹 알림함 화면, 알림 딥링크, 예약금/계좌 정보 포함 푸시",
      "how_to_use": "알림 문구, 딥링크 목적지, 너무 잦은 알림을 묶을 기준을 확인한다. 사장님 알림은 카카오 알림톡과 OwnerNotification 알림함 양쪽에 동시 적재한다(웹푸시는 MVP 제외). 계좌이체 예약금 안내 푸시는 예약금 금액 + 계좌 정보가 푸시 본문에 들어가는지 별도 화면 진입인지 정한다. 사장님 응답 리마인드는 pending 1시간 경과 시 1회 발송(수동수락 샵만 해당, 운영 후 시간값 재조정 가능)"
    }
  }
}
```
