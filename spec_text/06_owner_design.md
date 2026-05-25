# 6.사장님(웹)_디자인

디자인/이미지 필드와 디자인 관리 API를 관리합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "entities": {
    "Design": [
      [
        "design_id",
        "UUID",
        "자동",
        "백엔드 생성"
      ],
      [
        "shop_id",
        "UUID",
        "자동",
        "소속 샵"
      ],
      [
        "title",
        "string",
        "필수",
        "디자인 이름"
      ],
      [
        "description",
        "text",
        "선택",
        "설명/홍보 문구"
      ],
      [
        "base_price",
        "int",
        "필수",
        "가격"
      ],
      [
        "duration_minutes",
        "int",
        "필수",
        "예약 슬롯 계산"
      ],
      [
        "available_designer_ids",
        "UUID[]",
        "필수",
        "자동 배정 후보"
      ],
      [
        "owner_tags",
        "string[]",
        "선택",
        "사장님 태그"
      ],
      [
        "ai_tags",
        "string[]",
        "자동",
        "LLM 2단계 결과"
      ],
      [
        "ai_color_palette",
        "string[]",
        "자동",
        "LLM 2단계 결과"
      ],
      [
        "ai_style_category",
        "enum",
        "자동",
        "simple/glamour/..."
      ],
      [
        "status",
        "enum",
        "자동",
        "draft/transforming/classifying/active/failed/hidden"
      ],
      [
        "favorite_count",
        "int",
        "자동",
        "찜 수"
      ],
      [
        "view_count",
        "int",
        "자동",
        "조회수"
      ],
      [
        "created_at",
        "timestamp",
        "자동",
        "등록일"
      ]
    ],
    "DesignImage": [
      [
        "image_id",
        "UUID",
        "자동",
        "백엔드 생성"
      ],
      [
        "design_id",
        "UUID",
        "자동",
        "소속 디자인"
      ],
      [
        "original_url",
        "URL",
        "필수",
        "원본. 사장님만 접근"
      ],
      [
        "cropped_url",
        "URL",
        "자동",
        "LLM 1단계 결과"
      ],
      [
        "sort_order",
        "int",
        "필수",
        "0이 썸네일"
      ],
      [
        "ai_transform_status",
        "enum",
        "자동",
        "pending/done/failed"
      ],
      [
        "ai_classify_status",
        "enum",
        "자동",
        "pending/done/failed"
      ]
    ]
  },
  "apis": {
    "owner_design": [
      [
        "POST /owner/shops/{shop_id}/designs",
        "디자인 등록",
        "title, price, duration, designers, images"
      ],
      [
        "GET /owner/shops/{shop_id}/designs",
        "디자인 목록",
        "status, cursor"
      ],
      [
        "GET /owner/designs/{design_id}",
        "디자인 상세/LLM 분석 상태 조회",
        "-"
      ],
      [
        "PATCH /owner/designs/{design_id}",
        "디자인 정보 수정",
        "title, description, price, duration, designers, tags"
      ],
      [
        "POST /owner/designs/{design_id}/images",
        "디자인 이미지 추가",
        "image_urls"
      ],
      [
        "DELETE /owner/designs/{design_id}/images/{image_id}",
        "디자인 이미지 삭제",
        "-"
      ],
      [
        "POST /owner/designs/{design_id}/reanalyze",
        "LLM 재분석 요청",
        "-"
      ],
      [
        "PATCH /owner/designs/{design_id}/visibility",
        "노출/숨김 변경",
        "visible"
      ],
      [
        "DELETE /owner/designs/{design_id}",
        "디자인 삭제 또는 숨김 처리",
        "-"
      ]
    ]
  },
  "page_guides": {
    "6.사장님(웹)_디자인": {
      "covers": "디자인 등록, 가격, 소요시간, 가능 디자이너, 이미지, LLM 분석 상태",
      "related_work": "사장님 웹 디자인 등록/수정/숨김/삭제, 이미지 업로드, LLM 재분석",
      "how_to_use": "분석 중/실패/완료 상태를 어떻게 보여줄지, 디자인 삭제와 숨김을 어떻게 구분할지 확인한다"
    }
  }
}
```
