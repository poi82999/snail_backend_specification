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
        "예약 캘린더",
        "from, to, designer_id, status"
      ],
      [
        "GET /owner/reservations/{id}",
        "예약 상세",
        "-"
      ],
      [
        "POST /owner/reservations/{id}/accept",
        "예약 수락",
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
        "POST /owner/reservations/{id}/complete",
        "완료 처리",
        "-"
      ],
      [
        "POST /owner/reservations/{id}/no-show",
        "노쇼 처리",
        "-"
      ],
      [
        "GET /owner/designers/{id}/schedule",
        "디자이너 스케줄 뷰",
        "from, to"
      ]
    ]
  },
  "page_guides": {
    "7.사장님(웹)_예약": {
      "covers": "예약 캘린더, 예약 상세, 수락/거절, 샵 취소, 완료, 노쇼",
      "related_work": "사장님 웹 예약 관리 화면",
      "how_to_use": "예약 상태별 버튼, 거절/취소 사유 입력, 노쇼 처리 가능 시간, 캘린더 필터를 확인한다"
    }
  }
}
```
