# 10.커뮤니티_리뷰

리뷰 필드와 리뷰 API를 관리합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "entities": {
    "Review": [
      [
        "review_id",
        "UUID",
        "자동",
        "백엔드 생성"
      ],
      [
        "reservation_id",
        "UUID",
        "필수",
        "UNIQUE, completed 상태만"
      ],
      [
        "author_user_id",
        "UUID",
        "자동",
        "reservation.user_id와 일치"
      ],
      [
        "shop_id",
        "UUID",
        "자동",
        "평균 별점 갱신용"
      ],
      [
        "design_id",
        "UUID",
        "자동",
        "디자인 상세 노출용"
      ],
      [
        "rating",
        "int",
        "필수",
        "1~5"
      ],
      [
        "content",
        "text",
        "필수",
        "후기"
      ],
      [
        "image_urls",
        "URL[]",
        "선택",
        "0~5장"
      ],
      [
        "tags",
        "string[]",
        "선택",
        "리뷰용 태그 협의"
      ],
      [
        "shop_reply",
        "text",
        "선택",
        "1리뷰당 1답변"
      ],
      [
        "shop_reply_at",
        "timestamp",
        "자동",
        "답변일"
      ],
      [
        "like_count",
        "int",
        "자동",
        "도움됨"
      ],
      [
        "status",
        "enum",
        "자동",
        "active/hidden/deleted"
      ],
      [
        "created_at",
        "timestamp",
        "자동",
        "작성일"
      ]
    ]
  },
  "apis": {
    "review": [
      [
        "GET /reservations/{id}/can-review",
        "리뷰 작성 가능 여부",
        "-"
      ],
      [
        "POST /reservations/{id}/review",
        "리뷰 작성",
        "rating, content, image_urls, tags"
      ],
      [
        "PATCH /reviews/{id}",
        "리뷰 수정",
        "rating, content, image_urls"
      ],
      [
        "DELETE /reviews/{id}",
        "리뷰 삭제",
        "-"
      ],
      [
        "GET /owner/reviews",
        "내 단수 샵 리뷰 목록. 사장님 웹 전용. sort 허용값: latest(기본) / rating_desc / rating_asc, unanswered=true이면 shop_reply IS NULL만 조회",
        "sort, unanswered, cursor"
      ],
      [
        "GET /shops/{id}/reviews",
        "샵 리뷰 목록. sort 허용값: latest(기본) / rating_desc / rating_asc",
        "sort, cursor"
      ],
      [
        "GET /designs/{id}/reviews",
        "디자인 리뷰 목록",
        "cursor"
      ],
      [
        "GET /users/me/reviews",
        "내 리뷰",
        "cursor"
      ],
      [
        "POST /reviews/{id}/reply",
        "샵 답변 작성 (리뷰당 1개). 사장님만",
        "content"
      ],
      [
        "PATCH /reviews/{id}/reply",
        "샵 답변 수정. 사장님만",
        "content"
      ],
      [
        "DELETE /reviews/{id}/reply",
        "샵 답변 삭제. shop_reply와 shop_reply_at을 null로 클리어. 사장님만",
        "-"
      ]
    ]
  },
  "page_guides": {
    "10.커뮤니티_리뷰": {
      "covers": "예약 완료 후 리뷰, 샵 별점, 리뷰 사진, 샵 답변",
      "related_work": "리뷰 작성 화면, 디자인/샵 상세 리뷰 목록, 사장님 리뷰 답변",
      "how_to_use": "리뷰 작성 가능 조건, 사진 5장 제한, 리뷰 수정/삭제 기간, 샵 답변 노출 방식을 확인한다"
    }
  }
}
```
