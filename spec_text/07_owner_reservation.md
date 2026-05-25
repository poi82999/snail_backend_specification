# 7.사장님(웹)_예약

사장님 웹 예약 관리 API를 관리합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "apis": {
    "owner_reservation": [
      [
        "GET /owner/reservations",
        "예약 캘린더 + 미처리 pending 목록. pending 목록은 created_at 오름차순(먼저 예약 요청한 순서)으로 제공해 사장님이 순서대로 응답할 수 있게 함",
        "from, to, designer_id, status, view(calendar|pending_queue), sort=created_at_asc"
      ],
      [
        "GET /owner/reservations/export",
        "예약 내역 다운로드 (post-MVP 우선순위 큐). CSV 포맷으로 내보내기",
        "from, to, status, format=csv"
      ],
      [
        "GET /owner/reservations/{id}",
        "예약 상세",
        "-"
      ],
      [
        "POST /owner/reservations/{id}/accept",
        "예약 수락. 현장결제 샵은 confirmed로 전환, 계좌이체 예약금 안내 샵은 payment_pending으로 전환하고 유저에게 계좌/예약금 안내",
        "-"
      ],
      [
        "POST /owner/reservations/{id}/reject",
        "예약 거절",
        "reason"
      ],
      [
        "POST /owner/reservations/{id}/cancel",
        "샵 예약 취소",
        "reason"
      ],
      [
        "POST /owner/reservations/{id}/payment-confirmed",
        "[입금 확인됨] 처리 — 사장님이 통장에서 입금 확인 후 호출. 조건: status=payment_pending AND payment_method_snapshot=bank_transfer_guide AND user_payment_notified_at != null AND owner_payment_confirmed_at IS NULL. owner_payment_confirmed_at 기록 후 status=confirmed 전환. 그 외 조건에서는 409",
        "-"
      ],
      [
        "POST /owner/reservations/{id}/complete",
        "완료 처리",
        "-"
      ],
      [
        "POST /owner/reservations/{id}/no-show",
        "노쇼 처리. MVP 방어적 구현: status=confirmed AND now >= start_datetime + 30분일 때만 허용, 금전/패널티 자동 처리 없이 상태 기록만 남김",
        "-"
      ],
      [
        "GET /owner/designers/{id}/schedule",
        "디자이너 스케줄 뷰",
        "from, to"
      ]
    ],
    "owner_dashboard": [
      [
        "GET /owner/dashboard/summary",
        "사장님 대시보드 홈 집계. 4개 지표를 한 번에 반환: today_reservation_count (오늘 pending+payment_pending+confirmed 합), pending_count (미처리 pending), unanswered_review_count (shop_reply IS NULL인 본인 샵 리뷰), recent_snap_tag_count (최근 7일 본인 샵 태그된 스네일). 캐싱 TTL 60초 권장",
        "-"
      ]
    ]
  },
  "page_guides": {
    "7.사장님(웹)_예약": {
      "covers": "예약 캘린더, 미처리 pending 목록, 예약 상세, 수락/거절, 샵 취소, [입금 확인됨] 처리, 완료, 노쇼, 사장님 대시보드 집계",
      "related_work": "사장님 웹 예약 관리 화면",
      "how_to_use": "예약 상태별 버튼, 거절/취소 사유 입력, 노쇼 처리 가능 시간, 캘린더 필터를 확인한다. 미처리 pending 예약은 created_at 오름차순으로 목록 노출해 사장님이 먼저 들어온 요청부터 응답하도록 유도한다. 계좌이체 샵에서 사장님이 수락하면 payment_pending이 되고, 유저가 [입금 완료] 누른 예약(user_payment_notified_at != null, owner_payment_confirmed_at IS NULL)은 예약 상세에 '입금 확인 요청' 뱃지 노출 — 사장님이 통장 확인 후 [입금 확인됨] 누르면 confirmed로 전환되고, 미입금이면 [샵 사정 취소]로 처리"
    }
  }
}
```
