# 9.커뮤니티_댓글

댓글, 좋아요, 팔로우 필드/API를 관리합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "entities": {
    "Comment": [
      [
        "comment_id",
        "UUID",
        "자동",
        "백엔드 생성"
      ],
      [
        "snap_id",
        "UUID",
        "필수",
        "스네일"
      ],
      [
        "parent_comment_id",
        "UUID?",
        "선택",
        "null=depth1, 값=depth2"
      ],
      [
        "author_type",
        "enum",
        "필수",
        "user/shop"
      ],
      [
        "author_user_id",
        "UUID?",
        "조건부",
        "author_type=user"
      ],
      [
        "author_shop_id",
        "UUID?",
        "조건부",
        "author_type=shop"
      ],
      [
        "content",
        "text",
        "필수",
        "댓글 내용"
      ],
      [
        "like_count",
        "int",
        "자동",
        "좋아요"
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
    "comment_like_follow": [
      [
        "GET /snaps/{id}/comments",
        "스네일 댓글 목록",
        "cursor"
      ],
      [
        "POST /snaps/{id}/comments",
        "댓글 작성. 사장님 웹에서 호출하면 본인 단수 샵 계정(author_type=shop, author_shop_id=내 shop_id)으로 작성",
        "content"
      ],
      [
        "POST /comments/{id}/reply",
        "대댓글 작성",
        "content"
      ],
      [
        "PATCH /comments/{id}",
        "댓글 수정",
        "content"
      ],
      [
        "DELETE /comments/{id}",
        "댓글 삭제",
        "-"
      ],
      [
        "POST /snaps/{id}/like",
        "스네일 좋아요",
        "-"
      ],
      [
        "DELETE /snaps/{id}/like",
        "스네일 좋아요 취소",
        "-"
      ],
      [
        "POST /comments/{id}/like",
        "댓글 좋아요",
        "-"
      ],
      [
        "DELETE /comments/{id}/like",
        "댓글 좋아요 취소",
        "-"
      ],
      [
        "POST /users/{id}/follow",
        "유저 팔로우",
        "-"
      ],
      [
        "DELETE /users/{id}/follow",
        "언팔로우",
        "-"
      ],
      [
        "GET /users/me/followers",
        "팔로워 목록",
        "cursor"
      ],
      [
        "GET /users/me/following",
        "팔로잉 목록",
        "cursor"
      ]
    ]
  },
  "page_guides": {
    "9.커뮤니티_댓글": {
      "covers": "댓글, 대댓글, 좋아요, 팔로우, 유저/샵 작성자 구분",
      "related_work": "스네일 상세 댓글 영역, 알림, 팔로우 기능",
      "how_to_use": "댓글 depth 2 UI, 샵 댓글 뱃지, 삭제된 댓글 표시, 좋아요 상태 표시를 확인한다"
    }
  }
}
```
