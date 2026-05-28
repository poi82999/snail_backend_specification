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
        "소유자. MVP는 1사장님=1샵 단수 구조이므로 owner_id는 Shop에서 UNIQUE"
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
        "region",
        "string",
        "자동",
        "주소에서 자동 파싱한 지역 (예: '서울 강남구', '서울 성동구', '수원시'). 검색 쿼리에 '강남' 들어오면 매칭. ES 인덱스에 디자인 문서로도 denormalize"
      ],
      [
        "location_tags",
        "string[]",
        "선택",
        "샵 위치/상권 태그. 공개 샵 목록 GET /shops의 location_tag 필터와 사장님 웹 샵 설정 표시/수정에 사용"
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
        "대표 이미지. 사장님이 image_urls 중에서 명시적으로 1장을 대표로 지정 (또는 별도 업로드). image_urls와 독립 운영"
      ],
      [
        "image_urls",
        "URL[]",
        "선택",
        "샵 갤러리 이미지 배열. 최대 10장 (외관/인테리어/시술공간 등). 배열 순서 = 표시 순서 (별도 sort_order 없음). thumbnail_url과 독립"
      ],
      [
        "visibility",
        "enum",
        "자동",
        "draft/active/hidden. 사업자 승인 전에는 draft 초안 작성 가능, 공개 노출과 예약 접수는 verification_status=approved AND visibility=active일 때만 허용"
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
        "예약 자동수락. 기본값 false(수동수락). true일 때는 payment_method=on_site로 강제됨(자동수락 ⟹ 현장결제). auto_accept=true AND payment_method=bank_transfer_guide 조합은 VALIDATION_ERROR로 거부"
      ],
      [
        "reservation_policy",
        "JSON",
        "필수",
        "취소/노쇼/변경 안내 문구와 운영 기준"
      ],
      [
        "payment_method",
        "enum",
        "필수",
        "on_site(현장결제, 예약금 없음 — 시술 당일 전액 결제) / bank_transfer_guide(계좌이체 예약금 안내). 샵 등록 시 사장님이 선택"
      ],
      [
        "deposit_amount",
        "int",
        "조건부",
        "예약금 금액(원). payment_method=bank_transfer_guide일 때 필수. 샵 단위 고정 정액(모든 디자인 동일 적용). on_site일 때는 null"
      ],
      [
        "bank_name",
        "string",
        "조건부",
        "은행명. payment_method=bank_transfer_guide일 때 필수 (예: '국민은행')"
      ],
      [
        "bank_account_number",
        "string",
        "조건부",
        "계좌번호. payment_method=bank_transfer_guide일 때 필수 (예: '123-456-789012')"
      ],
      [
        "bank_account_holder",
        "string",
        "조건부",
        "예금주. payment_method=bank_transfer_guide일 때 필수 (예: '홍길동')"
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
        "MVP 프론트 입력 UI 제외 가능. 백엔드 선택 필드로만 유지하는 자유 입력 string[]. 검색 비대상 — 샵 상세 페이지의 디자이너 카드에 표시하는 디스플레이 메타데이터 전용. 표준 태그 사전 강제 안 함"
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
        "사업자 정보/사업자등록증 제출. verification_status=rejected 상태에서 재제출 시 자동으로 pending으로 되돌아감",
        "business_number, business_license_image"
      ],
      [
        "POST /owner/auth/password-reset/request",
        "비밀번호 재설정 요청 1단계 — 이메일에 토큰 발송 (15분 TTL, 1회 사용). 미가입 이메일이어도 동일 응답 (사용자 enumeration 방지)",
        "email"
      ],
      [
        "POST /owner/auth/password-reset/confirm",
        "비밀번호 재설정 2단계 — 토큰 + 신규 비밀번호 제출. 토큰 유효성/만료/사용여부 검증 후 비번 갱신, 토큰 1회용 소진",
        "token, new_password"
      ]
    ],
    "owner_shop": [
      [
        "POST /owner/shop",
        "내 단수 샵 초안 생성. 사업자 승인 전에도 draft 작성 가능. payment_method=bank_transfer_guide면 deposit_amount, bank_name, bank_account_number, bank_account_holder 모두 필수. auto_accept 기본값은 false. auto_accept=true AND payment_method=bank_transfer_guide 조합은 거부(VALIDATION_ERROR)",
        "name, address, phone, business_hours, reservation_policy, payment_method, auto_accept?, deposit_amount?, bank_name?, bank_account_number?, bank_account_holder?"
      ],
      [
        "GET /owner/shop",
        "내 단수 샵 상세/초안 조회",
        "-"
      ],
      [
        "PATCH /owner/shop",
        "내 단수 샵 기본 정보 수정. 사업자 승인 전 draft 수정 가능",
        "name, address, phone, description"
      ],
      [
        "PATCH /owner/shop/business-hours",
        "영업시간 수정",
        "business_hours"
      ],
      [
        "PATCH /owner/shop/reservation-policy",
        "자동수락/예약 운영 안내 수정. auto_accept=true로 전환 시 현재 shop의 payment_method=on_site가 아니면 거부(VALIDATION_ERROR)",
        "auto_accept, reservation_policy"
      ],
      [
        "PATCH /owner/shop/payment-method",
        "결제 방식 변경 (현장결제 ↔ 계좌이체 예약금 안내) 및 예약금/계좌 정보 수정. bank_transfer_guide로 전환 시 deposit_amount + 계좌 3필드 모두 필수, 또한 현재 shop의 auto_accept=true면 거부(VALIDATION_ERROR — 자동수락 ⟹ 현장결제 강제)",
        "payment_method, deposit_amount?, bank_name?, bank_account_number?, bank_account_holder?"
      ],
      [
        "PATCH /owner/shop/images",
        "대표 이미지/샵 이미지 수정",
        "thumbnail_url, image_urls"
      ],
      [
        "PATCH /owner/shop/visibility",
        "샵 공개/숨김 전환. active 전환은 verification_status=approved일 때만 허용. 공개 상태에서만 유저 검색/상세/예약 진입 가능",
        "visibility"
      ]
    ],
    "owner_designer": [
      [
        "POST /owner/designers",
        "내 단수 샵 디자이너 추가",
        "name, rank, career_years, profile_image_url?, specialty_tags?"
      ],
      [
        "GET /owner/designers",
        "내 단수 샵 디자이너 목록",
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
      "covers": "사장님 계정, 사업자 인증, 샵 정보, 영업시간, 예약 운영 안내, 결제 방식(현장결제 = 예약금 없음 / 계좌이체 예약금 안내), 예약금 금액, 계좌 정보(은행명/계좌번호/예금주), 자동수락⟹현장결제 강제 룰, 디자이너, 스케줄",
      "related_work": "사장님 웹 가입, 샵 설정, 결제 방식 선택, 예약금/계좌 입력, 디자이너 관리, 근무시간 관리, 사업자 인증 게이트",
      "how_to_use": "MVP는 1사장님=1샵 단수 구조로 구현한다. 사장님이 직접 입력하기 쉬운 UI인지, 영업시간/예약 운영 안내/결제 방식 입력 방식이 자연스러운지 확인한다. 계좌이체 선택 시 예약금 금액과 은행명/계좌번호/예금주 3필드 입력 UI 및 유저 측 노출 미리보기를 제공한다. 자동수락 기본값은 false(수동수락)이며, 토글 ON 시 결제수단 선택지에서 계좌이체 비활성화 + 안내(자동수락⟹현장결제 강제). verification_status != approved인 사장님도 샵/디자이너/디자인 초안 작성은 가능하지만, visibility=active 공개 전환과 예약 처리 API는 403 VERIFICATION_REQUIRED로 차단한다"
    }
  }
}
```
