# 5.사장님(웹)_샵관리

사장님 계정, 샵, 디자이너 필드와 사장님 웹 CRUD API를 관리합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "entities": {
    "Owner": [
      [
        "owner_id",
        "UUID",
        "자동",
        "백엔드 생성"
      ],
      [
        "email",
        "string",
        "필수",
        "이메일"
      ],
      [
        "password",
        "string(hash)",
        "필수",
        "8자 이상 등 정책 필요"
      ],
      [
        "owner_name",
        "string",
        "필수",
        "대표자명"
      ],
      [
        "phone",
        "string",
        "필수",
        "카카오 알림톡 수신 번호"
      ],
      [
        "business_number",
        "string",
        "필수",
        "사업자등록번호"
      ],
      [
        "business_license_image",
        "image/pdf",
        "필수",
        "운영자 수동 승인"
      ],
      [
        "verification_status",
        "enum",
        "자동",
        "pending/approved/rejected"
      ]
    ],
    "Shop": [
      [
        "shop_id",
        "UUID",
        "자동",
        "백엔드 생성"
      ],
      [
        "owner_id",
        "UUID",
        "자동",
        "소유자"
      ],
      [
        "name",
        "string",
        "필수",
        "샵 이름"
      ],
      [
        "address",
        "string",
        "필수",
        "도로명 주소 API 검토"
      ],
      [
        "address_detail",
        "string",
        "선택",
        "상세주소"
      ],
      [
        "lat",
        "float",
        "자동",
        "주소 좌표 변환"
      ],
      [
        "lng",
        "float",
        "자동",
        "주소 좌표 변환"
      ],
      [
        "phone",
        "string",
        "필수",
        "샵 전화"
      ],
      [
        "description",
        "text",
        "선택",
        "샵 소개"
      ],
      [
        "thumbnail_url",
        "URL",
        "선택",
        "대표 이미지"
      ],
      [
        "business_hours",
        "JSON",
        "필수",
        "요일별 UI"
      ],
      [
        "auto_accept",
        "bool",
        "필수",
        "예약 자동수락"
      ],
      [
        "reservation_policy",
        "JSON",
        "필수",
        "취소/노쇼/변경 안내 문구와 운영 기준"
      ],
      [
        "rating_avg",
        "float",
        "자동",
        "리뷰 작성 시 재계산"
      ],
      [
        "rating_count",
        "int",
        "자동",
        "리뷰 수"
      ],
      [
        "favorite_count",
        "int",
        "자동",
        "찜한 사람 수"
      ]
    ],
    "Designer": [
      [
        "designer_id",
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
        "name",
        "string",
        "필수",
        "디자이너 이름"
      ],
      [
        "career_years",
        "int",
        "선택",
        "경력"
      ],
      [
        "rank",
        "string",
        "선택",
        "원장/실장/주니어 등"
      ],
      [
        "profile_image_url",
        "URL",
        "선택",
        "프로필 사진"
      ],
      [
        "specialty_tags",
        "string[]",
        "선택",
        "표준 태그"
      ],
      [
        "is_active",
        "bool",
        "필수",
        "퇴사 시 false"
      ]
    ]
  },
  "apis": {
    "owner_auth": [
      [
        "POST /owner/auth/register",
        "사장님 회원가입",
        "email, password, owner_name, phone"
      ],
      [
        "POST /owner/auth/login",
        "사장님 로그인",
        "email, password"
      ],
      [
        "POST /owner/auth/logout",
        "로그아웃",
        "-"
      ],
      [
        "GET /owner/me",
        "내 계정/사업자 인증 상태 조회",
        "-"
      ],
      [
        "PATCH /owner/me",
        "계정 정보 수정",
        "owner_name, phone"
      ],
      [
        "POST /owner/business-verification",
        "사업자 정보/사업자등록증 제출",
        "business_number, business_license_image"
      ]
    ],
    "owner_shop": [
      [
        "POST /owner/shops",
        "샵 생성",
        "name, address, phone, business_hours, reservation_policy"
      ],
      [
        "GET /owner/shops",
        "내가 관리하는 샵 목록",
        "-"
      ],
      [
        "GET /owner/shops/{shop_id}",
        "샵 상세",
        "-"
      ],
      [
        "PATCH /owner/shops/{shop_id}",
        "샵 기본 정보 수정",
        "name, address, phone, description"
      ],
      [
        "PATCH /owner/shops/{shop_id}/business-hours",
        "영업시간 수정",
        "business_hours"
      ],
      [
        "PATCH /owner/shops/{shop_id}/reservation-policy",
        "자동수락/예약 운영 안내 수정",
        "auto_accept, reservation_policy"
      ],
      [
        "PATCH /owner/shops/{shop_id}/images",
        "대표 이미지/샵 이미지 수정",
        "thumbnail_url, image_urls"
      ]
    ],
    "owner_designer": [
      [
        "POST /owner/shops/{shop_id}/designers",
        "디자이너 추가",
        "name, rank, career_years, specialty_tags"
      ],
      [
        "GET /owner/shops/{shop_id}/designers",
        "디자이너 목록",
        "-"
      ],
      [
        "GET /owner/designers/{designer_id}",
        "디자이너 상세",
        "-"
      ],
      [
        "PATCH /owner/designers/{designer_id}",
        "디자이너 정보 수정",
        "name, rank, profile_image_url, is_active"
      ],
      [
        "PATCH /owner/designers/{designer_id}/schedule",
        "주간 근무시간 수정",
        "weekly_schedule"
      ],
      [
        "POST /owner/designers/{designer_id}/time-off",
        "특정일 휴무/임시 불가 시간 등록",
        "date, start_time, end_time, reason"
      ],
      [
        "DELETE /owner/designers/{designer_id}",
        "퇴사/비활성화 처리",
        "-"
      ]
    ]
  },
  "page_guides": {
    "5.사장님(웹)_샵관리": {
      "covers": "사장님 계정, 사업자 인증, 샵 정보, 영업시간, 예약 운영 안내, 디자이너, 스케줄",
      "related_work": "사장님 웹 가입, 샵 설정, 디자이너 관리, 근무시간 관리",
      "how_to_use": "사장님이 직접 입력하기 쉬운 UI인지, 사업자 승인 전 제한 화면이 필요한지, 영업시간/예약 운영 안내 입력 방식이 자연스러운지 확인한다"
    }
  }
}
```
