# 8.커뮤니티_스네일

스네일(Snap) 필드와 스네일 API를 관리합니다. 엔드포인트명은 /snaps를 유지합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "entities": {
    "Snap": [
      [
        "snap_id",
        "UUID",
        "자동",
        "백엔드 생성"
      ],
      [
        "author_user_id",
        "UUID",
        "필수",
        "유저만"
      ],
      [
        "caption",
        "text",
        "선택",
        "본문"
      ],
      [
        "image_urls",
        "URL[]",
        "필수",
        "1~10장"
      ],
      [
        "tags",
        "string[]",
        "선택",
        "자유 vs 표준 협의"
      ],
      [
        "tagged_shop_id",
        "UUID",
        "선택",
        "받은 샵"
      ],
      [
        "tagged_design_id",
        "UUID",
        "선택",
        "디자인 상세 노출"
      ],
      [
        "tagged_designer_id",
        "UUID",
        "선택",
        "샵 태그된 경우"
      ],
      [
        "tagged_reservation_id",
        "UUID",
        "선택",
        "인증 뱃지 후보"
      ],
      [
        "like_count",
        "int",
        "자동",
        "좋아요"
      ],
      [
        "save_count",
        "int",
        "자동",
        "저장 수. POST /snails/{snap_id}/save 토글 결과로 증가/감소"
      ],
      [
        "saved_by_me",
        "bool",
        "자동",
        "현재 로그인 유저가 저장했는지 여부. SnapPublic 응답에서만 의미 있음"
      ],
      [
        "comment_count",
        "int",
        "자동",
        "댓글"
      ],
      [
        "view_count",
        "int",
        "자동",
        "조회수"
      ],
      [
        "popularity_score",
        "float",
        "자동",
        "랭킹 탭용"
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
    "snap": [
      [
        "GET /snaps/feed?tab=latest",
        "스네일 탭",
        "cursor"
      ],
      [
        "GET /snaps/feed?tab=ranking",
        "랭킹 탭",
        "period"
      ],
      [
        "GET /snaps/feed?tab=following",
        "팔로잉 탭",
        "cursor"
      ],
      [
        "POST /snaps",
        "스네일 작성",
        "caption, image_urls, tags, tagged_*"
      ],
      [
        "GET /snaps/{id}",
        "스네일 상세",
        "-"
      ],
      [
        "POST /snails/{snap_id}/save",
        "스네일 저장 토글",
        "Idempotency-Key header"
      ],
      [
        "GET /snaps/me",
        "내 스네일",
        "cursor"
      ],
      [
        "GET /users/{id}/snaps",
        "유저 스네일",
        "cursor"
      ],
      [
        "GET /designs/{id}/snaps",
        "특정 디자인 받은 스네일",
        "cursor"
      ],
      [
        "GET /owner/snaps",
        "내 단수 샵이 태그된 스네일 목록. 사장님 웹 전용",
        "cursor"
      ],
      [
        "GET /shops/{id}/snaps",
        "특정 샵 태그 스네일",
        "cursor"
      ],
      [
        "PATCH /snaps/{id}",
        "스네일 수정",
        "caption, tags"
      ],
      [
        "DELETE /snaps/{id}",
        "스네일 삭제",
        "-"
      ]
    ]
  },
  "page_guides": {
    "8.커뮤니티_스네일": {
      "covers": "스네일 피드, 랭킹, 팔로잉, 스네일 작성, 샵/디자인/예약 태그",
      "related_work": "앱 커뮤니티 탭, 스네일 작성/상세 화면",
      "how_to_use": "스네일 작성 시 태그 선택 UI, 인증 뱃지, 디자인 상세에 노출되는 조건을 확인한다"
    }
  }
}
```
