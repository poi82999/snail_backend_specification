# 3.유저(앱)_회원

유저 회원가입, 로그인, 프로필 필드 정의를 관리합니다.

## 수정 방법

- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.
- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.
- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.
- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.

```json spec-data
{
  "entities": {
    "User": [
      [
        "user_id",
        "UUID",
        "자동",
        "백엔드 생성"
      ],
      [
        "auth_method",
        "enum",
        "필수",
        "현재 apple"
      ],
      [
        "apple_user_id",
        "string",
        "필수",
        "Apple 검증 후 저장"
      ],
      [
        "nickname",
        "string",
        "필수",
        "닉네임"
      ],
      [
        "profile_image_url",
        "URL",
        "선택",
        "프로필 사진"
      ],
      [
        "bio",
        "string",
        "선택",
        "한 줄 소개"
      ],
      [
        "preferred_tags",
        "string[]",
        "선택",
        "표준 태그 사전 내"
      ],
      [
        "device_token",
        "string",
        "필수",
        "APNs 토큰"
      ],
      [
        "app_version",
        "string",
        "필수",
        "강제 업데이트 판단"
      ],
      [
        "created_at",
        "timestamp",
        "자동",
        "가입일"
      ]
    ]
  },
  "apis": {
    "user_auth": [
      [
        "POST /auth/apple",
        "Apple 로그인 연동",
        "apple_identity_token"
      ],
      [
        "POST /auth/login",
        "일반 로그인 (토큰 발급)",
        "email, password"
      ],
      [
        "POST /auth/refresh",
        "토큰 갱신",
        "refresh_token"
      ],
      [
        "POST /auth/logout",
        "로그아웃",
        "-"
      ]
    ],
    "user_profile": [
      [
        "GET /users/me",
        "내 프로필 조회",
        "-"
      ],
      [
        "PATCH /users/me",
        "내 프로필 수정",
        "nickname, profile_image_url, bio, preferred_tags"
      ],
      [
        "DELETE /users/me",
        "회원 탈퇴",
        "-"
      ]
    ]
  },
  "page_guides": {
    "3.유저(앱)_회원": {
      "covers": "Apple Sign In, 유저 프로필, 닉네임, 프로필 사진, 관심 태그, APNs 토큰",
      "related_work": "앱 로그인/회원가입/프로필 수정 화면",
      "how_to_use": "회원가입 시 꼭 필요한 입력값, 프로필 수정 가능 항목, 닉네임/소개글 검증 규칙을 채운다"
    }
  }
}
```
