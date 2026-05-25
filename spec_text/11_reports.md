# 11.커뮤니티_신고

신고/모더레이션 필드를 관리합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "entities": {
    "Report": [
      [
        "report_id",
        "UUID",
        "자동",
        "백엔드 생성"
      ],
      [
        "reporter_id",
        "UUID",
        "필수",
        "u_xxx 또는 o_xxx"
      ],
      [
        "target_type",
        "enum",
        "필수",
        "snap/comment/review/user/shop"
      ],
      [
        "target_id",
        "UUID",
        "필수",
        "신고 대상 ID"
      ],
      [
        "reason_code",
        "enum",
        "필수",
        "spam/abuse/sexual/copyright/other"
      ],
      [
        "reason_detail",
        "text",
        "선택",
        "상세"
      ],
      [
        "status",
        "enum",
        "자동",
        "pending/reviewing/resolved"
      ],
      [
        "resolved_action",
        "enum",
        "선택",
        "none/hide/delete/ban"
      ]
    ]
  },
  "page_guides": {
    "11.커뮤니티_신고": {
      "covers": "스네일/댓글/리뷰/유저/샵 신고와 운영 처리",
      "related_work": "신고 버튼, 신고 사유 선택, 운영자 모더레이션",
      "how_to_use": "신고 사유 문구, 신고 완료 안내, 신고 후 콘텐츠 표시 여부를 확인한다"
    }
  }
}
```
