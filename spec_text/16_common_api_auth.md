# 16.공통_API권한

공통 응답/에러/페이지네이션/rate limit/권한 모델을 관리합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "auth_permission_model": {
    "purpose": "협업자가 버튼 노출/권한 없음 화면을 판단하고, 백엔드가 서버 권한 검증 기준으로 삼기 위한 모델",
    "actors": [
      [
        "anonymous",
        "비로그인 유저",
        "검색/피드/상세 일부만 볼 수 있음"
      ],
      [
        "user",
        "로그인 유저",
        "예약, 찜, 스네일, 댓글, 리뷰 사용 가능"
      ],
      [
        "owner",
        "사장님 Owner",
        "본인 소유 샵의 정보, 디자이너, 디자인, 예약만 관리 가능"
      ],
      [
        "admin",
        "어드민",
        "신고 처리, 사업자 승인, 콘텐츠 숨김/삭제 가능"
      ],
      [
        "system",
        "시스템",
        "스케줄러, LLM callback, 알림 발송 등 서버 내부 작업"
      ]
    ],
    "permission_matrix": [
      [
        "검색/디자인 상세 보기",
        "가능",
        "가능",
        "가능",
        "가능",
        "비로그인 허용 범위"
      ],
      [
        "예약 생성",
        "불가",
        "가능",
        "불가",
        "불가",
        "로그인 유도 화면"
      ],
      [
        "내 예약 조회",
        "불가",
        "본인만",
        "불가",
        "가능",
        "타인 예약 접근 차단"
      ],
      [
        "예약 수락/거절",
        "불가",
        "불가",
        "본인 샵 예약만",
        "가능",
        "사장님 웹 버튼 노출"
      ],
      [
        "리뷰 작성",
        "불가",
        "본인 completed 예약만",
        "불가",
        "불가",
        "리뷰 작성 가능 조건"
      ],
      [
        "스네일 작성",
        "불가",
        "가능",
        "불가",
        "불가",
        "로그인 유도 화면"
      ],
      [
        "댓글 작성",
        "불가",
        "가능",
        "본인 샵 계정으로 가능",
        "가능",
        "샵 뱃지 표시"
      ],
      [
        "샵 정보 수정",
        "불가",
        "불가",
        "본인 샵만",
        "가능",
        "소유권 오류 문구"
      ],
      [
        "디자이너/디자인 관리",
        "불가",
        "불가",
        "본인 샵만",
        "가능",
        "예약 존재 시 제한 문구"
      ],
      [
        "신고 처리",
        "불가",
        "불가",
        "불가",
        "가능",
        "어드민 MVP 포함 여부"
      ]
    ],
    "error_policy": [
      "로그인이 필요한 경우 401 UNAUTHORIZED",
      "로그인은 되어 있지만 권한이 없는 경우 403 FORBIDDEN"
    ]
  },
  "common_api_rules": {
    "purpose": "프론트엔드가 모든 API를 같은 방식으로 처리할 수 있게 하는 협업 규칙",
    "success_response": {
      "single": {
        "data": "object",
        "request_id": "string"
      },
      "list": {
        "data": "array",
        "page": {
          "next_cursor": "string|null",
          "has_next": "boolean"
        },
        "request_id": "string"
      }
    },
    "pagination": [
      "cursor 기반 페이지네이션",
      "cursor는 프론트가 해석하지 않는 opaque string",
      "첫 요청은 cursor 없이 호출",
      "다음 페이지가 없으면 next_cursor=null, has_next=false",
      "기본 limit 20, 최대 limit 50 제안"
    ],
    "error_response": {
      "shape": {
        "error": {
          "code": "string",
          "message": "string",
          "field_errors": "object|null"
        },
        "request_id": "string"
      },
      "codes": [
        [
          "UNAUTHORIZED",
          "로그인이 필요함"
        ],
        [
          "FORBIDDEN",
          "권한 없음"
        ],
        [
          "NOT_FOUND",
          "리소스 없음"
        ],
        [
          "VALIDATION_ERROR",
          "입력값 오류"
        ],
        [
          "CONFLICT",
          "예약 충돌, 중복 리뷰, 중복 요청 등"
        ],
        [
          "RATE_LIMITED",
          "요청 제한 초과"
        ],
        [
          "INTERNAL_ERROR",
          "서버 오류"
        ]
      ]
    },
    "rate_limit": [
      "MVP 기본안: 로그인 유저 기준 일반 API 분당 60회",
      "검색 API 분당 30회",
      "업로드/예약 생성 계열은 더 낮게 제한",
      "제한 초과 시 HTTP 429와 RATE_LIMITED 반환"
    ],
    "time_format": [
      "API 시간은 ISO 8601 문자열",
      "서버 저장 기준은 UTC",
      "화면 표시는 앱/웹에서 샵 로컬 시간대로 변환"
    ],
    "empty_state": [
      "빈 리스트도 HTTP 200으로 응답",
      "검색 0건은 유사 추천 디자인을 포함할 수 있음",
      "프론트는 빈 결과/유사 추천/필터 초기화 문구 확인"
    ]
  },
  "page_guides": {
    "16.공통_API권한": {
      "covers": "공통 응답 형식, 에러 코드, 페이지네이션, rate limit, 권한 표",
      "related_work": "모든 프론트 API 연동, 로그인 필요/권한 없음/빈 상태 처리",
      "how_to_use": "모든 화면에서 같은 방식으로 에러와 리스트를 처리할 수 있는지 확인한다"
    }
  }
}
```
