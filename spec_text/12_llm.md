# 12.LLM명세

LLM Transform/Classify, 태그 사전, 에러 코드, 작업자 질문을 관리합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "llm": {
    "transform": {
      "purpose": "원본 사진에서 네일 영역 추출 + 규격화",
      "suggested_endpoint": "/v1/transform",
      "request_fields": [
        "image_url",
        "image_id",
        "callback_url",
        "options.output_size",
        "options.background"
      ],
      "response_fields": [
        "image_id",
        "status",
        "cropped_image_url",
        "cropped_image_size",
        "confidence",
        "nail_count_detected",
        "processing_time_ms",
        "error_code",
        "error_message"
      ],
      "recommendation": "5초 이내면 동기, 10초 이상이면 비동기 webhook 권장"
    },
    "classify": {
      "purpose": "cropped 이미지에서 태그/색상/스타일 분류",
      "suggested_endpoint": "/v1/classify",
      "request_fields": [
        "image_url",
        "image_id",
        "locale",
        "options.max_tags",
        "options.include_color_palette",
        "options.include_style_category"
      ],
      "response_fields": [
        "image_id",
        "status",
        "tags",
        "color_palette",
        "style_category",
        "nail_shape",
        "confidence_overall",
        "processing_time_ms"
      ]
    },
    "standard_tags": {
      "style": [
        "프렌치",
        "옴브레",
        "그라데이션",
        "마그넷",
        "글리터",
        "큐빅",
        "라인아트",
        "캐릭터",
        "무광",
        "유광"
      ],
      "color": [
        "핑크",
        "레드",
        "누드",
        "블랙",
        "화이트",
        "베이지",
        "블루",
        "그린",
        "옐로우",
        "퍼플",
        "브라운",
        "골드",
        "실버"
      ],
      "mood": [
        "봄",
        "여름",
        "가을",
        "겨울",
        "시크",
        "러블리",
        "심플",
        "글래머",
        "내추럴",
        "키치",
        "모던"
      ],
      "technique": [
        "젤",
        "매니큐어",
        "페디큐어",
        "연장",
        "케어",
        "제거"
      ],
      "shape": [
        "스퀘어",
        "라운드",
        "오벌",
        "아몬드",
        "스틸레토",
        "발레리나"
      ],
      "style_category": [
        "simple",
        "glamour",
        "classic",
        "trendy",
        "chic"
      ],
      "occasion": [
        "웨딩",
        "데일리",
        "파티",
        "오피스",
        "데이트"
      ]
    },
    "error_codes": [
      [
        "NO_NAIL",
        "사진에서 네일이 감지되지 않음",
        "사진에서 네일을 찾지 못했어요. 손이 잘 보이는 사진으로 다시 올려주세요."
      ],
      [
        "LOW_QUALITY",
        "해상도 낮음/블러/조명 부족",
        "사진 화질이 낮아요. 좀 더 선명한 사진으로 시도해주세요."
      ],
      [
        "MULTIPLE_HANDS",
        "여러 명의 손이 섞임",
        "한 사람의 손만 나오는 사진으로 올려주세요."
      ],
      [
        "OBSTRUCTED",
        "네일이 가려짐",
        "네일이 잘 보이도록 다시 촬영해주세요."
      ],
      [
        "INAPPROPRIATE",
        "부적절 콘텐츠 감지",
        "이 사진은 업로드할 수 없습니다."
      ],
      [
        "INTERNAL_ERROR",
        "LLM 내부 에러",
        "잠시 후 다시 시도해주세요."
      ]
    ],
    "worker_questions": [
      "Transform/Classify는 동기 응답인가, 비동기 callback인가",
      "비동기라면 callback URL 호출 시 인증 방식은 무엇인가",
      "평균 처리 시간과 p95 처리 시간은 어느 정도인가",
      "백엔드 timeout은 몇 초로 잡아야 하는가",
      "재시도 가능한 에러와 재시도하면 안 되는 에러는 무엇인가",
      "rate limit 초과 시 어떤 HTTP status와 body를 반환하는가",
      "cropped 이미지는 LLM이 저장하는가, 백엔드 S3에 업로드하는가",
      "LLM이 제공하는 이미지 URL의 만료 시간은 얼마인가",
      "응답에 model_version을 포함할 수 있는가",
      "모델이 업데이트되면 기존 이미지를 재분석해야 하는가",
      "디자인에 이미지가 여러 장일 때 태그 병합은 LLM이 하는가, 백엔드가 하는가",
      "태그는 표준 태그 사전 값만 반환할 수 있는가",
      "confidence가 낮을 때 백엔드가 실패로 처리해야 하는 기준값은 얼마인가"
    ]
  },
  "page_guides": {
    "12.LLM명세": {
      "covers": "네일 이미지 Transform, 태그 Classification, 태그 사전, 에러 코드, callback/재시도/저장 책임",
      "related_work": "LLM API 구현, 백엔드-LLM 연동, 디자인 등록 자동 분석",
      "how_to_use": "LLM 작업자는 실제 API 운영값을 채우고, 프론트/웹은 분석 실패 문구와 재업로드 동선을 확인한다"
    }
  }
}
```
