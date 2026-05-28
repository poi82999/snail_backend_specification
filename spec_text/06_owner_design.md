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
        "사장님이 직접 입력하는 해시태그. 0~N개 자유 입력. 노출 조건에서 제외(0개여도 등록/노출 가능). 검색에서는 ai_tags와 함께 사용되며 더 높은 가중치를 받음 (사장님 의도 신호로 해석)"
      ],
      [
        "ai_tags",
        "string[]",
        "자동",
        "LLM 2단계 결과. owner_tags와 별도 필드로 보관. 검색에서는 두 태그를 모두 사용하되 가중치/표시 분리 가능"
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
        "visibility",
        "enum",
        "자동",
        "draft / active / hidden. 사장님 통제 영역. 기본 active. PATCH /owner/designs/{id}/visibility로 변경"
      ],
      [
        "ai_analysis_status",
        "enum",
        "자동",
        "pending / in_progress / done / failed. 시스템 통제 영역. 사장님 등록 직후 pending → 백그라운드 큐가 처리 → done/failed. failed 시 재분석 가능"
      ],
      [
        "ai_analysis_started_at",
        "timestamp",
        "자동",
        "LLM 큐 처리 시작 시각. UI에서 '분석 중 (X분 경과)' 표시용"
      ],
      [
        "ai_analysis_completed_at",
        "timestamp",
        "자동",
        "AI 분석 완료(done) 시각. failed 시에는 마지막 시도 시각"
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
    ],
    "DesignOption": [
      [
        "option_id",
        "UUID",
        "자동",
        "백엔드 생성"
      ],
      [
        "design_id",
        "UUID",
        "필수",
        "소속 디자인"
      ],
      [
        "kind",
        "enum",
        "필수",
        "옵션 종류. API 값은 extend/removal/care"
      ],
      [
        "name",
        "string",
        "필수",
        "옵션 표시명"
      ],
      [
        "price_delta",
        "int",
        "필수",
        "기본 디자인 가격에 더해지는 금액"
      ],
      [
        "duration_delta_min",
        "int",
        "필수",
        "기본 시술 시간에 더해지는 분 단위 소요시간"
      ],
      [
        "sort_order",
        "int",
        "자동",
        "옵션 노출 순서"
      ],
      [
        "is_active",
        "bool",
        "자동",
        "옵션 사용 여부"
      ]
    ]
  },
  "apis": {
    "owner_design": [
      [
        "POST /owner/designs",
        "내 단수 샵 디자인 등록 (사장님 응답 즉시 200, AI 분석은 백그라운드 큐). 이미지 최대 5장. owner_tags는 선택(0~N개). 등록 직후 visibility=active, ai_analysis_status=pending. 노출은 ai_analysis_status=done + shop.visibility=active + owner.verification_status=approved 이후",
        "title, base_price, duration_minutes, available_designer_ids, images(max 5), owner_tags?"
      ],
      [
        "GET /owner/designs",
        "내 단수 샵 디자인 목록. 필터로 visibility, ai_analysis_status 둘 다 사용 가능. 사장님 화면에서 '분석 중', '분석 실패', '숨김' 탭 구분",
        "visibility, ai_analysis_status, cursor"
      ],
      [
        "GET /owner/designs/{design_id}",
        "디자인 상세/LLM 분석 상태 조회",
        "-"
      ],
      [
        "PATCH /owner/designs/{design_id}",
        "디자인 정보 수정",
        "title, description, base_price, duration_minutes, available_designer_ids, owner_tags"
      ],
      [
        "GET /shops/me/designs/{design_id}/options",
        "디자인 옵션 목록 조회. 예약 시 추가 옵션 선택 UI에 사용",
        "-"
      ],
      [
        "POST /shops/me/designs/{design_id}/options",
        "디자인 옵션 생성. kind는 extend/removal/care, price_delta와 duration_delta_min은 예약 금액/시간 계산에 반영",
        "kind, name, price_delta, duration_delta_min, sort_order"
      ],
      [
        "PATCH /shops/me/designs/{design_id}/options/{option_id}",
        "디자인 옵션 수정",
        "kind?, name?, price_delta?, duration_delta_min?, sort_order?, is_active?"
      ],
      [
        "DELETE /shops/me/designs/{design_id}/options/{option_id}",
        "디자인 옵션 삭제 또는 비활성화",
        "-"
      ],
      [
        "POST /owner/designs/{design_id}/images",
        "디자인 이미지 추가. 디자인당 이미지 최대 5장 제한을 초과하면 VALIDATION_ERROR. 호출 시 백엔드가 design.ai_analysis_status를 pending으로 자동 되돌리고 LLM 큐에 재투입 (이미지 변경 자동 재분석 트리거)",
        "image_urls(max total 5)"
      ],
      [
        "DELETE /owner/designs/{design_id}/images/{image_id}",
        "디자인 이미지 삭제. 삭제 후 최소 1장 이상 남아야 함. 호출 시 design.ai_analysis_status를 pending으로 자동 되돌리고 LLM 큐에 재투입 (이미지 변경 자동 재분석 트리거)",
        "-"
      ],
      [
        "POST /owner/designs/{design_id}/reanalyze",
        "LLM 재분석 요청. ai_analysis_status=failed이거나 사장님이 수동으로 다시 돌리고 싶을 때. pending으로 되돌리고 큐에 재투입",
        "-"
      ],
      [
        "PATCH /owner/designs/{design_id}/visibility",
        "노출/숨김 변경",
        "visibility"
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
      "covers": "디자인 등록, 가격, 소요시간, 가능 디자이너, 디자인 옵션(연장/제거/케어), 이미지(최대 5장), 사장님 태그(선택), AI 분석 상태, 노출 조건, 이미지 변경 자동 재분석",
      "related_work": "사장님 웹 디자인 등록/수정/숨김/삭제, 이미지 업로드, LLM 재분석, 분석 상태 표시",
      "how_to_use": "사장님 태그 입력 UI(0~N개 자유 입력, 검색 가중치 안내 가능), 디자인 옵션 CRUD UI(kind/price_delta/duration_delta_min), 디자인 이미지 1~5장 제한, 분석 중/실패/완료 상태 표시(MVP 사장님 화면은 pending+in_progress를 '분석 중' 한 덩어리로 표시), '아직 사용자에게 노출되지 않음' 안내, 디자인 삭제와 숨김 구분, 분석 실패 시 [재분석] 버튼 노출(POST /owner/designs/{id}/reanalyze)을 확인한다. 사용자 노출은 ai_analysis_status=done + visibility=active + shop.visibility=active + owner.verification_status=approved 조합으로 판정"
    }
  }
}
```
