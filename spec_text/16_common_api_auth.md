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
      "로그인은 되어 있지만 권한이 없는 경우 403 FORBIDDEN",
      "사장님이 로그인은 되어 있지만 verification_status != approved여서 운영 기능 사용이 불가한 경우 403 VERIFICATION_REQUIRED (FORBIDDEN과 별도 코드로 구분 — 프론트가 '사업자 인증을 먼저 완료해주세요' 안내 화면으로 유도)"
    ],
    "verification_gate": {
      "purpose": "사장님 회원가입 직후 verification_status가 approved가 아닌 상태(pending/rejected)에서 운영성 API 호출을 백엔드가 차단하기 위한 게이트. UI 버튼 숨김만으로는 부족하므로 서버 검증 필수",
      "gated_apis": [
        "샵/디자이너/디자인의 visibility=active 공개 전환 API",
        "유저 검색/상세/예약 진입에 노출되는 공개 상태 전환",
        "모든 owner_reservation 쓰기 API (accept/reject/cancel/payment-confirmed/complete/no-show)",
        "예약 접수와 관련된 운영 API"
      ],
      "allowed_without_verification": [
        "POST /owner/auth/register | login | logout",
        "GET /owner/me, PATCH /owner/me (자기 정보 조회/수정 — 연락처 오타 수정 등)",
        "POST /owner/business-verification (사업자 인증 제출 자체)",
        "GET /owner/notifications 계열 (사업자 승인 결과 알림을 받아야 하므로 알림함 조회는 허용)",
        "POST /owner/shop, GET /owner/shop, PATCH /owner/shop 계열의 draft 초안 작성/수정",
        "GET/POST/PATCH/DELETE /owner/designers 및 /owner/designs 계열의 비공개 초안 관리 (단, 공개 전환은 승인 후 가능)",
        "공개 API (검색, 피드, 디자인 상세 등 — 사장님 계정이라도 탐색은 가능)"
      ],
      "error_response": "차단 대상 API 호출 시 HTTP 403 + error.code='VERIFICATION_REQUIRED'. message는 verification_status에 따라 분기 ('승인 대기 중입니다. 초안 작성은 가능하지만 공개/예약 처리는 승인 후 가능합니다' / '반려되었습니다. 사유: ...')",
      "rejected_handling": "verification_status=rejected인 경우 사장님이 POST /owner/business-verification로 재제출 가능. 재제출 시 status는 pending으로 되돌아감"
    }
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
          "권한 없음 (소유권 위반 등)"
        ],
        [
          "VERIFICATION_REQUIRED",
          "사장님 사업자 인증 미완료/반려로 운영 기능 사용 불가"
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
      "검색 0건은 응답 data=[] + recommendations 별도 필드에 유사 디자인 포함",
      "프론트는 빈 결과/유사 추천/필터 초기화 문구 확인"
    ],
    "image_upload": {
      "purpose": "이미지를 클라이언트가 직접 객체 스토리지에 업로드하기 위한 표준 흐름. 백엔드는 업로드 게이트만 제어하고 실제 바이트 트래픽은 받지 않음",
      "flow": [
        "1. 클라이언트가 POST /uploads/presigned로 업로드 의도 표시 (target_type, file_size, content_type)",
        "2. 백엔드가 권한 1회 체크(누가 어디에 업로드하는지, 파일 사이즈 ≤ 10MB, 허용 content-type 검증) → 권한 OK면 presigned URL 발급 (10분 TTL)",
        "3. 클라이언트가 presigned URL로 객체 스토리지에 직접 PUT",
        "4. 업로드 완료 후 클라이언트가 백엔드에 업로드 완료 알림 (해당 리소스 API 호출, 예: POST /owner/designs/{id}/images의 image_urls 파라미터). 디자인 이미지는 최종 DB 반영 시 디자인당 총 5장 제한을 백엔드가 검증",
        "5. 백그라운드 워커가 원본을 4단계로 리사이즈(프로필 512 / 썸네일 640 / 상세 1440 / 원본 2048) + WebP/JPEG 변환하여 저장. DB에는 URL만 보관"
      ],
      "limits": [
        "파일당 최대 10MB",
        "허용 content-type: image/jpeg, image/png, image/webp, image/heic (PDF는 사업자등록증 별도 처리)",
        "presigned URL TTL 10분",
        "동시 업로드 제한: 1요청당 1파일"
      ],
      "permission": "발급 시점에 한 번 검증. 발급 후에는 객체 스토리지가 URL 자체로 검증 (TTL 만료 또는 정해진 키 경로 외 거부)",
      "api": [
        ["POST /uploads/presigned", "presigned URL 발급", "target_type(profile/shop/design/snap/review/business_license), file_size, content_type"]
      ]
    }
  },
  "page_guides": {
    "16.공통_API권한": {
      "covers": "공통 응답 형식, 에러 코드, 페이지네이션, rate limit, 권한 표, 사업자 인증 게이트(verification_gate)",
      "related_work": "모든 프론트 API 연동, 로그인 필요/권한 없음/빈 상태 처리, 사장님 사업자 인증 전 화면 가드",
      "how_to_use": "모든 화면에서 같은 방식으로 에러와 리스트를 처리할 수 있는지 확인한다. 사장님 웹은 verification_status가 approved가 아니어도 초안 작성은 허용하되, 공개 전환과 예약 처리 버튼은 UI에서 막는다. 백엔드는 동일한 룰로 403 VERIFICATION_REQUIRED를 반환하므로 우회 가능성 없음. 에러 코드 분기: FORBIDDEN(소유권 위반) vs VERIFICATION_REQUIRED(인증 미완료) 구분 유도 문구 다르게 처리"
    }
  }
}
```
