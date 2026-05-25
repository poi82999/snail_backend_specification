import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GITHUB_BLOB_BASE = "https://github.com/poi82999/snail_backend_specification/blob/main"
SPEC_TEXT_DIR = ROOT / "spec_text"
FRONT_SPEC_PATH = ROOT / "references" / "snail_owner_webapp_spec_v1.md"
OUTPUT_DIR = ROOT / "outputs"
DOCS_DIR = ROOT / "docs"
INDEX_JSON_PATH = OUTPUT_DIR / "owner_webapp_backend_index.json"
INDEX_HTML_PATH = OUTPUT_DIR / "owner_webapp_backend_index.html"
SHARED_HTML_PATH = DOCS_DIR / "owner_webapp_backend_index.html"
AI_TEXT_PATH = OUTPUT_DIR / "owner_webapp_backend_index.ai.txt"
SHARED_AI_TEXT_PATH = DOCS_DIR / "owner_webapp_backend_index.ai.txt"


OWNER_SECTION_MAP = [
    {
        "id": "1",
        "title": "회원가입 / 로그인",
        "front_sections": ["1", "1-1", "1-2", "1-3", "1-4"],
        "summary": "사장님 계정 생성, 사업자 인증, 로그인/로그아웃, 비밀번호 재설정 흐름.",
        "backend_files": ["spec_text/05_owner_shop.md", "spec_text/16_common_api_auth.md"],
        "entities": {
            "Owner": [
                "email",
                "password",
                "owner_name",
                "phone",
                "business_number",
                "business_license_image",
                "verification_status",
            ]
        },
        "apis": {
            "owner_auth": [
                "POST /owner/auth/register",
                "POST /owner/auth/login",
                "POST /owner/auth/logout",
                "GET /owner/me",
                "PATCH /owner/me",
                "POST /owner/business-verification",
                "POST /owner/auth/password-reset/request",
                "POST /owner/auth/password-reset/confirm",
            ]
        },
        "keywords": ["auth", "owner", "verification", "password-reset"],
        "checkpoints": [
            "FORBIDDEN과 VERIFICATION_REQUIRED를 프론트에서 서로 다른 안내로 분기해야 함.",
            "사업자 인증 rejected 상태는 같은 제출 API로 재제출하면 pending으로 돌아감.",
        ],
    },
    {
        "id": "2",
        "title": "샵 설정",
        "front_sections": ["2", "2-1", "2-2", "2-3", "2-4"],
        "summary": "샵 기본 정보, 영업시간, 예약 운영 정책, 현장결제/계좌이체 설정.",
        "backend_files": ["spec_text/05_owner_shop.md", "spec_text/16_common_api_auth.md"],
        "entities": {
            "Shop": [
                "name",
                "address",
                "address_detail",
                "region",
                "lat",
                "lng",
                "phone",
                "description",
                "thumbnail_url",
                "image_urls",
                "visibility",
                "business_hours",
                "auto_accept",
                "reservation_policy",
                "payment_method",
                "deposit_amount",
                "bank_name",
                "bank_account_number",
                "bank_account_holder",
            ]
        },
        "apis": {
            "owner_shop": [
                "POST /owner/shop",
                "GET /owner/shop",
                "PATCH /owner/shop",
                "PATCH /owner/shop/business-hours",
                "PATCH /owner/shop/reservation-policy",
                "PATCH /owner/shop/payment-method",
                "PATCH /owner/shop/images",
                "PATCH /owner/shop/visibility",
            ]
        },
        "keywords": ["shop", "business-hours", "payment-method", "deposit"],
        "checkpoints": [
            "MVP는 1사장님=1샵 단수 구조이며 사장님 웹 API는 /owner/shop 기준으로 사용.",
            "auto_accept=true이면 bank_transfer_guide 조합은 백엔드도 VALIDATION_ERROR로 거부.",
        ],
    },
    {
        "id": "3",
        "title": "디자이너 관리",
        "front_sections": ["3", "3-1", "3-2", "3-3", "3-4"],
        "summary": "디자이너 추가/수정, 전문 태그, 주간 근무시간, 임시 불가 시간, 비활성화.",
        "backend_files": ["spec_text/05_owner_shop.md"],
        "entities": {
            "Designer": [
                "designer_id",
                "shop_id",
                "name",
                "career_years",
                "rank",
                "profile_image_url",
                "specialty_tags",
                "is_active",
            ]
        },
        "apis": {
            "owner_designer": [
                "POST /owner/designers",
                "GET /owner/designers",
                "GET /owner/designers/{designer_id}",
                "PATCH /owner/designers/{designer_id}",
                "PATCH /owner/designers/{designer_id}/schedule",
                "POST /owner/designers/{designer_id}/time-off",
                "DELETE /owner/designers/{designer_id}",
            ]
        },
        "keywords": ["designer", "schedule", "time-off"],
        "checkpoints": [
            "specialty_tags는 현재 자유 입력 string[]이며 검색 대상이 아니라 디스플레이 메타데이터.",
            "비활성 디자이너의 기존 confirmed 예약 처리 방식은 화면에서 별도 안내가 필요.",
        ],
    },
    {
        "id": "4",
        "title": "디자인 등록 및 관리",
        "front_sections": ["4", "4-1", "4-2", "4-3", "4-4", "4-5"],
        "summary": "디자인 등록, 이미지 업로드, owner_tags, LLM 분석 상태, 재분석, 노출/숨김/삭제.",
        "backend_files": ["spec_text/06_owner_design.md", "spec_text/12_llm.md", "spec_text/16_common_api_auth.md"],
        "entities": {
            "Design": [
                "title",
                "description",
                "base_price",
                "duration_minutes",
                "available_designer_ids",
                "owner_tags",
                "ai_tags",
                "ai_color_palette",
                "ai_style_category",
                "visibility",
                "ai_analysis_status",
                "ai_analysis_started_at",
                "ai_analysis_completed_at",
            ],
            "DesignImage": [
                "original_url",
                "cropped_url",
                "sort_order",
                "ai_transform_status",
                "ai_classify_status",
            ],
        },
        "apis": {
            "owner_design": [
                "POST /owner/designs",
                "GET /owner/designs",
                "GET /owner/designs/{design_id}",
                "PATCH /owner/designs/{design_id}",
                "POST /owner/designs/{design_id}/images",
                "DELETE /owner/designs/{design_id}/images/{image_id}",
                "POST /owner/designs/{design_id}/reanalyze",
                "PATCH /owner/designs/{design_id}/visibility",
                "DELETE /owner/designs/{design_id}",
            ]
        },
        "keywords": ["design", "llm", "image", "owner_tags", "reanalyze"],
        "checkpoints": [
            "디자인 이미지는 프론트와 백엔드 API 모두 최대 5장 제한으로 맞춤.",
            "사장님 화면은 pending+in_progress를 '분석 중' 한 상태로 묶어 표시.",
        ],
    },
    {
        "id": "5",
        "title": "예약 관리",
        "front_sections": ["5", "5-1", "5-2", "5-3", "5-4", "5-5", "5-6", "5-7", "5-8", "5-9"],
        "summary": "월간 캘린더, 예약 상세, 수락/거절/취소/완료/노쇼, 입금 확인 요청 뱃지.",
        "backend_files": ["spec_text/07_owner_reservation.md", "spec_text/04_user_discovery_reservation.md"],
        "entities": {
            "Reservation": [
                "reservation_id",
                "user_id",
                "shop_id",
                "design_id",
                "designer_id",
                "start_datetime",
                "end_datetime",
                "duration_minutes",
                "status",
                "total_price",
                "reservation_policy_snapshot",
                "payment_method_snapshot",
                "deposit_amount_snapshot",
                "bank_transfer_guide_snapshot",
                "user_payment_notified_at",
                "owner_payment_confirmed_at",
                "reminder_sent_at",
                "user_request_memo",
                "cancel_reason",
                "cancelled_at",
                "completed_at",
                "no_show_at",
            ]
        },
        "apis": {
            "owner_reservation": [
                "GET /owner/reservations",
                "GET /owner/reservations/export",
                "GET /owner/reservations/{id}",
                "POST /owner/reservations/{id}/accept",
                "POST /owner/reservations/{id}/reject",
                "POST /owner/reservations/{id}/cancel",
                "POST /owner/reservations/{id}/payment-confirmed",
                "POST /owner/reservations/{id}/complete",
                "POST /owner/reservations/{id}/no-show",
                "GET /owner/designers/{id}/schedule",
            ]
        },
        "keywords": ["reservation", "calendar", "payment-confirmed", "no-show"],
        "checkpoints": [
            "CSV export는 API 후보가 있지만 MVP 1차 출시 제외로 표시되어야 함.",
            "입금 확인 요청 뱃지는 status/payment snapshot/입금 알림/사장님 확인 시각 4조건을 모두 봄.",
        ],
    },
    {
        "id": "6",
        "title": "리뷰 관리",
        "front_sections": ["6", "6-1", "6-2"],
        "summary": "본인 샵 리뷰 목록, 평균 별점/리뷰 수, 정렬, 리뷰 답변 작성/수정/삭제.",
        "backend_files": ["spec_text/10_reviews.md", "spec_text/07_owner_reservation.md"],
        "entities": {
            "Review": [
                "review_id",
                "reservation_id",
                "shop_id",
                "design_id",
                "author_user_id",
                "rating",
                "content",
                "image_urls",
                "shop_reply",
                "shop_reply_at",
                "created_at",
            ]
        },
        "apis": {
            "review": [
                "GET /owner/reviews",
                "GET /shops/{id}/reviews",
                "POST /reviews/{id}/reply",
                "PATCH /reviews/{id}/reply",
                "DELETE /reviews/{id}/reply",
            ],
            "owner_dashboard": ["GET /owner/dashboard/summary"],
        },
        "keywords": ["review", "reply", "rating"],
        "checkpoints": [
            "사장님 전용 리뷰 목록 API는 별도 /owner 경로가 아니라 현재 GET /shops/{id}/reviews를 사용.",
            "대시보드의 unanswered_review_count는 shop_reply IS NULL 기준.",
        ],
    },
    {
        "id": "7",
        "title": "스네일 확인",
        "front_sections": ["7", "7-1", "7-2"],
        "summary": "본인 샵이 태그된 스네일 조회, 샵 계정 댓글 작성/수정/삭제.",
        "backend_files": ["spec_text/08_snail.md", "spec_text/09_comments_likes_follows.md", "spec_text/13_notifications.md"],
        "entities": {
            "Snap": [
                "snap_id",
                "author_user_id",
                "caption",
                "image_urls",
                "tagged_shop_id",
                "tagged_design_id",
                "tagged_designer_id",
                "like_count",
                "comment_count",
                "created_at",
            ],
            "Comment": [
                "comment_id",
                "snap_id",
                "author_type",
                "author_user_id",
                "author_shop_id",
                "content",
                "created_at",
            ],
        },
        "apis": {
            "snap": ["GET /owner/snaps", "GET /shops/{id}/snaps", "GET /snaps/{id}"],
            "comment_like_follow": [
                "GET /snaps/{id}/comments",
                "POST /snaps/{id}/comments",
                "PATCH /comments/{id}",
                "DELETE /comments/{id}",
            ],
        },
        "keywords": ["snap", "comment", "shop-badge"],
        "checkpoints": [
            "사장님 전용 스네일 목록 API는 현재 /owner 경로가 아니라 GET /shops/{id}/snaps를 사용.",
            "샵 계정 댓글은 Comment.author_type/author_shop_id로 구분.",
        ],
    },
    {
        "id": "8",
        "title": "대시보드",
        "front_sections": ["8", "8-1"],
        "summary": "오늘 예약 수, 신규 예약 요청 수, 미답변 리뷰 수, 최근 스네일 태그 수.",
        "backend_files": ["spec_text/07_owner_reservation.md"],
        "entities": {},
        "apis": {"owner_dashboard": ["GET /owner/dashboard/summary"]},
        "keywords": ["dashboard", "summary"],
        "checkpoints": [
            "4개 지표는 단일 API에서 내려주며 캐싱 TTL 60초 권장.",
            "각 지표 클릭 시 이동할 필터 상태를 프론트 라우팅에 맞춰 고정해야 함.",
        ],
    },
    {
        "id": "9",
        "title": "알림",
        "front_sections": ["9", "9-1", "9-2", "9-3"],
        "summary": "카카오 알림톡, 사장님 웹 알림함, 미읽음 뱃지, 딥링크, 모두 읽음.",
        "backend_files": ["spec_text/13_notifications.md"],
        "entities": {
            "OwnerNotification": [
                "notification_id",
                "owner_id",
                "type",
                "title",
                "body",
                "deeplink_target",
                "related_resource_type",
                "related_resource_id",
                "is_read",
                "read_at",
                "created_at",
                "kakao_sent_at",
            ]
        },
        "apis": {
            "owner_notification": [
                "GET /owner/notifications",
                "GET /owner/notifications/unread-count",
                "PATCH /owner/notifications/{notification_id}/read",
                "POST /owner/notifications/read-all",
            ]
        },
        "keywords": ["notification", "kakao", "inbox", "deep-link"],
        "checkpoints": [
            "웹푸시는 MVP 제외. 카카오 알림톡 + 웹 알림함 조합.",
            "알림 클릭 시 딥링크 이동과 읽음 처리가 함께 필요.",
        ],
    },
    {
        "id": "10",
        "title": "미정 / 추가 확인 필요 항목",
        "front_sections": ["10"],
        "summary": "프론트 명세의 미정 항목과 백엔드 의사결정 기록/체크리스트 연결.",
        "backend_files": ["spec_text/14_decisions.md", "spec_text/15_checklist.md"],
        "entities": {},
        "apis": {},
        "keywords": ["decision", "checklist", "todo"],
        "checkpoints": [
            "프론트 문서 하단 v1.1 확정 사항은 백엔드 decisions와 계속 동기화해야 함.",
            "미정 항목은 사라지지 않게 체크리스트 또는 의사결정 기록으로 옮겨 관리.",
        ],
    },
]


IMPLEMENTATION_GUIDES = {
    "1": [
        "가입 완료 후 `GET /owner/me`로 `verification_status`를 확인하고, `pending/rejected/approved`에 따라 온보딩 화면을 분기한다.",
        "`VERIFICATION_REQUIRED`는 소유권 오류가 아니라 승인 상태 문제이므로 `FORBIDDEN`과 다른 안내 화면으로 연결한다.",
        "비밀번호 재설정은 미가입 이메일도 동일 응답을 보여 사용자 존재 여부가 노출되지 않게 처리한다.",
    ],
    "2": [
        "MVP는 1사장님=1샵이다. 프론트 라우팅과 상태 저장에서 `shop_id`를 직접 들고 다니기보다 `/owner/shop` 단수 리소스로 취급한다.",
        "사업자 승인 전에는 draft 초안 저장을 허용하되, `visibility=active` 공개 전환과 예약 운영 버튼은 승인 후에만 활성화한다.",
        "`auto_accept` 기본값은 `false`이며, `auto_accept=true`일 때 `bank_transfer_guide` 선택지를 비활성화해야 한다.",
    ],
    "3": [
        "디자이너는 내 단수 샵 하위 리소스다. 목록/추가/수정 화면은 `/owner/designers` 계열만 사용하면 된다.",
        "`specialty_tags`는 MVP에서 프론트 입력 UI를 만들지 않아도 되는 선택 필드다. 화면 복잡도를 줄이고 이름/직급/경력/사진/활성 상태에 집중한다.",
        "비활성 디자이너는 신규 예약 후보에서 제외되지만 기존 예약은 남으므로 예약 상세에서 비활성 표시가 필요하다.",
    ],
    "4": [
        "디자인 이미지는 1~5장 제한이다. 프론트 업로드 UI와 백엔드 리소스 반영 API가 같은 제한을 가져야 한다.",
        "`owner_tags`는 선택값이며 수정 API에서도 `owner_tags`로 보낸다. 구버전 `tags` 파라미터를 쓰면 안 된다.",
        "사용자 노출은 `approved owner + active shop + active design + ai_analysis_status=done` 조합이다. 사장님 화면에는 왜 아직 노출되지 않는지 상태별로 설명해야 한다.",
    ],
    "5": [
        "단순 `pending`은 슬롯 hard-lock이 아니다. 사장님 웹은 미처리 pending을 `created_at` 오름차순으로 보여주고, 수락 시점에 충돌을 재검사한다.",
        "계좌이체 샵은 `pending -> payment_pending -> confirmed` 흐름이다. 유저의 [입금 완료]만으로 확정되지 않고 사장의 [입금 확인됨]이 필요하다.",
        "노쇼는 MVP에서 방어적으로 구현한다. `confirmed`이고 시술 시작 30분 이후일 때만 가능하며, 금전/패널티 자동 처리는 하지 않는다.",
    ],
    "6": [
        "사장님 리뷰 화면은 `/owner/reviews`를 기본으로 사용한다. 공개 샵 리뷰 API를 우회해서 내 샵 id를 관리할 필요가 없다.",
        "미답변 리뷰 필터는 `unanswered=true` 또는 대시보드 `unanswered_review_count`와 연결한다.",
        "리뷰 답변은 1개만 허용되므로 작성/수정/삭제 버튼 상태를 `shop_reply` 존재 여부로 분기한다.",
    ],
    "7": [
        "사장님 스네일 화면은 `/owner/snaps`를 기본으로 사용한다. 단수 샵 정책 기준으로 내 샵이 태그된 스네일만 조회한다.",
        "샵 댓글은 같은 댓글 API를 쓰되 서버가 `author_type=shop`, `author_shop_id=내 shop_id`로 기록한다.",
        "스네일 신고는 MVP 제외이므로 화면에서 신고 처리 흐름을 만들지 않는다.",
    ],
    "8": [
        "대시보드 4개 지표는 `/owner/dashboard/summary` 단일 API로 가져온다.",
        "`today_reservation_count`는 `pending + payment_pending + confirmed`를 포함한다.",
        "각 지표 카드 클릭 시 이동할 화면과 필터 상태를 URL query 또는 라우터 state로 고정한다.",
    ],
    "9": [
        "웹푸시는 MVP 제외다. 사장님 알림은 카카오 알림톡과 웹 알림함을 같이 사용한다.",
        "알림 클릭 시 `deeplink_target`으로 이동하고 즉시 단건 읽음 처리 API를 호출한다.",
        "카카오 발송 실패와 무관하게 `OwnerNotification`은 남아야 하므로 알림함을 신뢰 가능한 백업 채널로 다룬다.",
    ],
    "10": [
        "미정 항목은 기능 구현 전에 `14.의사결정기록`으로 옮겨 상태를 관리한다.",
        "정책 수치가 필요한 항목은 API 필드보다 먼저 결정해야 프론트 validation과 에러 문구가 안정된다.",
        "결정이 바뀌면 `spec_text`를 먼저 수정하고 워크북/비주얼라이저를 재생성한다.",
    ],
}


SCREEN_PLAYBOOKS = {
    "1": {
        "api_sequence": [
            "앱 진입 시 저장된 토큰이 있으면 `GET /owner/me`를 먼저 호출한다.",
            "토큰이 없거나 401이면 로그인 화면을 보여준다.",
            "회원가입 제출 시 `POST /owner/auth/register`를 호출하고 성공하면 사업자 인증 제출 화면으로 이동한다.",
            "로그인 성공 후 다시 `GET /owner/me`를 호출해 `verification_status` 기준으로 화면을 분기한다.",
            "사업자 인증 제출 또는 재제출은 `POST /owner/business-verification`로 처리한다.",
        ],
        "ui_events": [
            ["회원가입 버튼", "POST /owner/auth/register", "가입 완료 후 사업자 인증 화면 이동", "VALIDATION_ERROR면 필드별 메시지 표시"],
            ["로그인 버튼", "POST /owner/auth/login -> GET /owner/me", "승인 상태에 맞는 첫 화면 이동", "401이면 이메일/비밀번호 확인 안내"],
            ["사업자 인증 제출", "POST /owner/business-verification", "pending 안내 화면 표시", "파일/사업자번호 오류를 입력칸 아래 표시"],
            ["비밀번호 재설정 요청", "POST /owner/auth/password-reset/request", "항상 같은 완료 안내 표시", "서버 오류만 공통 오류 표시"],
        ],
        "states": [
            "anonymous: 로그인/회원가입만 노출",
            "pending: 초안 작성 가능, 공개/예약 처리 버튼 비활성화",
            "rejected: 반려 사유 표시 + 재제출 버튼 노출",
            "approved: 대시보드와 운영 기능 진입 허용",
        ],
        "qa": [
            "토큰 없이 `/owner/me` 호출 실패 시 로그인 화면으로 이동하는지 확인",
            "pending 계정으로 공개 버튼을 눌렀을 때 `VERIFICATION_REQUIRED` 안내가 나오는지 확인",
            "rejected 계정에서 재제출 후 pending 화면으로 바뀌는지 확인",
            "미가입 이메일 비밀번호 재설정 요청도 동일한 완료 문구를 보여주는지 확인",
        ],
    },
    "2": {
        "api_sequence": [
            "샵 설정 화면 진입 시 `GET /owner/shop`을 호출한다.",
            "샵이 없으면 빈 초안 폼을 보여주고 저장 시 `POST /owner/shop`을 호출한다.",
            "샵이 있으면 기본 정보 수정은 `PATCH /owner/shop`, 영업시간은 `PATCH /owner/shop/business-hours`로 나눈다.",
            "예약 정책은 `PATCH /owner/shop/reservation-policy`, 결제 방식은 `PATCH /owner/shop/payment-method`로 저장한다.",
            "공개/숨김 토글은 `PATCH /owner/shop/visibility`를 호출하되 승인 전에는 버튼을 비활성화한다.",
        ],
        "ui_events": [
            ["기본 정보 저장", "PATCH /owner/shop 또는 POST /owner/shop", "저장 완료 토스트 + 화면 값 갱신", "주소/전화번호 오류를 필드별 표시"],
            ["영업시간 저장", "PATCH /owner/shop/business-hours", "캘린더/예약 가능 시간 재계산 안내", "시간 겹침 오류 표시"],
            ["결제 방식 저장", "PATCH /owner/shop/payment-method", "결제 안내 미리보기 갱신", "계좌 필수값 누락 표시"],
            ["공개 토글", "PATCH /owner/shop/visibility", "active/hidden 배지 갱신", "VERIFICATION_REQUIRED면 인증 안내 모달 표시"],
        ],
        "states": [
            "no_shop: 샵 초안 생성 폼",
            "draft_allowed: 승인 전 초안 수정 가능",
            "active: 고객 검색/예약 진입 가능",
            "hidden: 고객에게 숨김, 사장님 수정은 가능",
        ],
        "qa": [
            "승인 전 샵 초안 저장은 성공하지만 공개 전환은 막히는지 확인",
            "`auto_accept=true`와 `bank_transfer_guide` 조합을 프론트에서 선택 불가로 막는지 확인",
            "계좌이체 선택 시 예약금/은행/계좌번호/예금주가 모두 필수인지 확인",
            "이미지 저장 후 새로고침해도 썸네일과 이미지 목록이 유지되는지 확인",
        ],
    },
    "3": {
        "api_sequence": [
            "디자이너 관리 화면 진입 시 `GET /owner/designers`를 호출한다.",
            "추가 버튼은 `POST /owner/designers`, 상세 진입은 `GET /owner/designers/{designer_id}`를 호출한다.",
            "기본 정보 수정은 `PATCH /owner/designers/{designer_id}`로 저장한다.",
            "주간 근무시간은 `PATCH /owner/designers/{designer_id}/schedule`, 임시 휴무는 `POST /owner/designers/{designer_id}/time-off`로 저장한다.",
            "삭제/비활성화 버튼은 `DELETE /owner/designers/{designer_id}`를 호출한 뒤 목록을 다시 불러온다.",
        ],
        "ui_events": [
            ["디자이너 추가", "POST /owner/designers", "목록 상단에 새 디자이너 표시", "이름/직급 필수 오류 표시"],
            ["근무시간 저장", "PATCH /owner/designers/{designer_id}/schedule", "예약 가능 시간 갱신 안내", "시간 범위 오류 표시"],
            ["임시 휴무 추가", "POST /owner/designers/{designer_id}/time-off", "해당 날짜 예약 불가 표시", "이미 예약이 있으면 충돌 안내"],
            ["비활성화", "DELETE /owner/designers/{designer_id}", "신규 예약 후보에서 제외", "기존 예약 존재 시 안내 표시"],
        ],
        "states": [
            "active: 신규 예약 후보에 노출",
            "inactive: 기존 예약은 남기고 신규 후보에서 제외",
            "empty: 디자이너 없음 안내 + 추가 버튼",
        ],
        "qa": [
            "디자이너가 0명일 때 빈 상태와 추가 버튼이 보이는지 확인",
            "비활성 디자이너가 디자인 가능 디자이너 선택지에서 빠지는지 확인",
            "근무시간 변경 후 예약 가능 슬롯 화면이 갱신되는지 확인",
            "임시 휴무일에 신규 예약이 막히는지 확인",
        ],
    },
    "4": {
        "api_sequence": [
            "디자인 목록 진입 시 `GET /owner/designs?visibility=&ai_analysis_status=`를 호출한다.",
            "등록 폼 저장 시 이미지 1~5장과 필수값을 검증한 뒤 `POST /owner/designs`를 호출한다.",
            "상세 화면은 `GET /owner/designs/{design_id}`로 최신 AI 분석 상태를 조회한다.",
            "수정 저장은 `PATCH /owner/designs/{design_id}`를 호출한다.",
            "이미지 추가/삭제 후에는 `POST /owner/designs/{design_id}/images` 또는 `DELETE /owner/designs/{design_id}/images/{image_id}`를 호출하고 분석 상태를 pending으로 보여준다.",
            "재분석 버튼은 `POST /owner/designs/{design_id}/reanalyze`를 호출한다.",
        ],
        "ui_events": [
            ["디자인 등록", "POST /owner/designs", "목록으로 이동 + 분석 중 배지 표시", "필수값/이미지 개수 오류 표시"],
            ["이미지 추가", "POST /owner/designs/{design_id}/images", "이미지 목록 갱신 + 분석 중 전환", "5장 초과 시 업로드 막기"],
            ["재분석", "POST /owner/designs/{design_id}/reanalyze", "분석 중 배지로 변경", "failed가 아니어도 수동 재분석 허용 여부 확인"],
            ["공개/숨김", "PATCH /owner/designs/{design_id}/visibility", "active/hidden 배지 갱신", "승인 전이면 인증 안내"],
        ],
        "states": [
            "pending/in_progress: 분석 중, 고객에게 아직 노출되지 않음",
            "done + active: 고객 노출 가능",
            "failed: 분석 실패, 재분석 또는 이미지 교체 버튼 표시",
            "hidden: 사장님만 볼 수 있음",
        ],
        "qa": [
            "이미지 0장 또는 6장 이상 등록이 프론트에서 막히는지 확인",
            "등록 직후 분석 완료 전까지 고객 노출 가능 문구가 나오지 않는지 확인",
            "AI 분석 실패 상태에서 재분석 버튼이 보이는지 확인",
            "`owner_tags` 없이도 등록 가능한지 확인",
        ],
    },
    "5": {
        "api_sequence": [
            "예약 화면 진입 시 `GET /owner/reservations?from=&to=&status=`를 호출한다.",
            "상세 모달을 열 때 `GET /owner/reservations/{id}`로 최신 상태를 다시 조회한다.",
            "수락은 `POST /owner/reservations/{id}/accept`, 거절은 `POST /owner/reservations/{id}/reject`를 호출한다.",
            "계좌이체 예약에서 입금 확인 버튼은 `POST /owner/reservations/{id}/payment-confirmed`를 호출한다.",
            "완료/노쇼/취소는 각각 complete/no-show/cancel API를 호출한 뒤 목록과 상세를 다시 불러온다.",
        ],
        "ui_events": [
            ["예약 수락", "POST /owner/reservations/{id}/accept", "현장결제면 confirmed, 계좌이체면 payment_pending 표시", "CONFLICT면 이미 선점된 시간 안내"],
            ["입금 확인", "POST /owner/reservations/{id}/payment-confirmed", "confirmed로 변경 + 캘린더 확정 표시", "이미 처리된 예약이면 새로고침 안내"],
            ["예약 거절", "POST /owner/reservations/{id}/reject", "rejected로 변경 + 목록에서 제거 또는 상태 갱신", "필수 사유 누락 표시"],
            ["노쇼 처리", "POST /owner/reservations/{id}/no-show", "no_show 배지 표시", "시작 30분 전이면 버튼 비활성화"],
        ],
        "states": [
            "pending: 사장님 수락/거절 대기, created_at 오름차순 표시",
            "payment_pending: 유저 입금 및 사장 확인 대기",
            "confirmed: 예약 확정, 완료/노쇼 가능 시점 대기",
            "completed/no_show/cancelled/rejected: 읽기 중심 상태",
        ],
        "qa": [
            "pending 목록이 예약 요청 생성 순서대로 보이는지 확인",
            "유저가 [입금 완료]를 눌러도 confirmed가 되지 않고 사장 확인 버튼이 남는지 확인",
            "동일 시간대 중복 수락 시 CONFLICT 안내가 나오는지 확인",
            "confirmed 예약 시작 30분 전에는 노쇼 버튼이 비활성화되는지 확인",
        ],
    },
    "6": {
        "api_sequence": [
            "리뷰 화면 진입 시 `GET /owner/reviews?sort=&unanswered=&cursor=`를 호출한다.",
            "대시보드 미답변 리뷰 카드에서 진입하면 `unanswered=true`를 붙인다.",
            "답변 작성은 `POST /reviews/{id}/reply`, 수정은 `PATCH /reviews/{id}/reply`, 삭제는 `DELETE /reviews/{id}/reply`를 호출한다.",
            "답변 변경 후 해당 리뷰 row 또는 목록을 다시 불러온다.",
        ],
        "ui_events": [
            ["답변 작성", "POST /reviews/{id}/reply", "답변 영역 표시 + 미답변 뱃지 제거", "이미 답변 있으면 수정 모드로 전환"],
            ["답변 수정", "PATCH /reviews/{id}/reply", "수정된 답변 표시", "권한 오류면 내 샵 리뷰가 아님 안내"],
            ["답변 삭제", "DELETE /reviews/{id}/reply", "미답변 상태로 변경", "삭제 확인 모달 제공"],
            ["정렬 변경", "GET /owner/reviews", "목록 재조회", "빈 결과면 빈 상태 표시"],
        ],
        "states": [
            "unanswered: 답변 작성 버튼 표시",
            "answered: 수정/삭제 버튼 표시",
            "empty: 리뷰 없음 또는 미답변 없음 안내",
        ],
        "qa": [
            "리뷰당 답변이 1개만 작성되는지 확인",
            "미답변 필터에서 답변 작성 후 목록에서 사라지거나 상태가 바뀌는지 확인",
            "정렬 변경 후 cursor가 초기화되는지 확인",
            "내 샵이 아닌 리뷰 답변 시 권한 오류가 처리되는지 확인",
        ],
    },
    "7": {
        "api_sequence": [
            "스네일 화면 진입 시 `GET /owner/snaps?cursor=`를 호출한다.",
            "게시물 상세은 `GET /snaps/{id}`로 불러온다.",
            "댓글 목록은 `GET /snaps/{id}/comments`를 호출한다.",
            "샵 계정 댓글 작성/수정/삭제는 comments API를 그대로 사용한다.",
        ],
        "ui_events": [
            ["스네일 상세 열기", "GET /snaps/{id}", "이미지/태그/댓글 영역 표시", "삭제된 게시물이면 목록에서 제거"],
            ["샵 댓글 작성", "POST /snaps/{id}/comments", "샵 뱃지 붙은 댓글 추가", "빈 댓글 입력 방지"],
            ["댓글 수정", "PATCH /comments/{id}", "수정된 댓글 반영", "내 샵 댓글이 아니면 버튼 숨김"],
            ["댓글 삭제", "DELETE /comments/{id}", "댓글 목록 갱신", "삭제 확인 모달 제공"],
        ],
        "states": [
            "tagged_snap: 내 샵이 태그된 게시물",
            "shop_comment: author_type=shop 댓글로 표시",
            "empty: 태그된 스네일 없음 안내",
        ],
        "qa": [
            "내 샵이 태그된 스네일만 보이는지 확인",
            "샵 댓글에 일반 유저와 다른 뱃지가 붙는지 확인",
            "내가 작성하지 않은 댓글에는 수정/삭제 버튼이 없는지 확인",
            "MVP 제외인 신고 플로우가 화면에 노출되지 않는지 확인",
        ],
    },
    "8": {
        "api_sequence": [
            "대시보드 진입 시 `GET /owner/dashboard/summary`를 호출한다.",
            "카드 클릭 시 해당 기능 화면으로 이동하고 필요한 query filter를 붙인다.",
            "새 예약 요청 카드는 예약 화면 `status=pending`, 미답변 리뷰 카드는 리뷰 화면 `unanswered=true`로 이동한다.",
        ],
        "ui_events": [
            ["오늘 예약 카드", "라우팅", "예약 화면 오늘 날짜 필터", "데이터 0건이면 빈 상태"],
            ["신규 예약 요청 카드", "라우팅", "예약 화면 pending 필터", "필터가 URL에 남는지 확인"],
            ["미답변 리뷰 카드", "라우팅", "리뷰 화면 unanswered=true", "답변 후 숫자 갱신"],
            ["최근 스네일 카드", "라우팅", "스네일 화면 이동", "목록 빈 상태 표시"],
        ],
        "states": [
            "loading: 카드 skeleton 표시",
            "loaded: 4개 지표 표시",
            "empty_zero: 0도 정상 수치로 표시",
        ],
        "qa": [
            "대시보드 API 한 번으로 4개 카드가 모두 채워지는지 확인",
            "카드 클릭 시 올바른 필터가 적용되는지 확인",
            "새로고침해도 필터 상태가 유지되는지 확인",
            "API 실패 시 카드별 공통 오류 상태가 보이는지 확인",
        ],
    },
    "9": {
        "api_sequence": [
            "알림함 진입 시 `GET /owner/notifications?cursor=`를 호출한다.",
            "상단 뱃지는 `GET /owner/notifications/unread-count`를 호출해 표시한다.",
            "알림 클릭 시 먼저 `PATCH /owner/notifications/{notification_id}/read`를 호출하고 `deeplink_target`으로 이동한다.",
            "모두 읽음은 `POST /owner/notifications/read-all`을 호출한 뒤 unread count를 0으로 갱신한다.",
        ],
        "ui_events": [
            ["알림 클릭", "PATCH read + 라우팅", "읽음 처리 후 관련 화면 이동", "이동 대상이 없으면 알림 상세만 표시"],
            ["모두 읽음", "POST /owner/notifications/read-all", "모든 알림 읽음 상태 + 뱃지 0", "실패 시 재시도 토스트"],
            ["더 보기", "GET /owner/notifications?cursor=", "다음 페이지 append", "has_next=false면 버튼 숨김"],
        ],
        "states": [
            "unread: 강조 표시 + 뱃지 카운트 포함",
            "read: 일반 표시",
            "empty: 알림 없음 안내",
        ],
        "qa": [
            "읽지 않은 알림 클릭 후 뱃지 숫자가 줄어드는지 확인",
            "deeplink_target이 예약/리뷰/스네일 화면으로 올바르게 이동하는지 확인",
            "모두 읽음 후 새로고침해도 읽음 상태가 유지되는지 확인",
            "카카오 실패와 무관하게 웹 알림함에는 알림이 남는지 확인",
        ],
    },
    "10": {
        "api_sequence": [
            "구현 전 미정 항목을 `spec_text/14_decisions.md`와 `spec_text/15_checklist.md`에서 확인한다.",
            "미정 항목이 화면 구현에 영향을 주면 프론트 임의 결정 대신 백엔드/기획 확인을 요청한다.",
            "결정이 바뀌면 `python tools\\build_all_collaboration_outputs.py`로 HTML과 AI 요약을 다시 생성한다.",
        ],
        "ui_events": [
            ["미정 정책 발견", "API 호출 없음", "결정 필요 목록에 기록", "임의 구현 금지"],
            ["결정 반영", "문서 재생성", "HTML/AI 요약 갱신", "Notion 링크 업데이트 여부 확인"],
        ],
        "states": [
            "open: 아직 결정 필요",
            "decided: 구현 가능",
            "changed: 기존 구현 영향 확인 필요",
        ],
        "qa": [
            "미정 정책이 코드에 하드코딩되지 않았는지 확인",
            "결정 변경 후 관련 화면의 버튼/문구/API 호출이 함께 바뀌었는지 확인",
            "HTML과 AI 요약을 재생성해 Notion 링크가 최신인지 확인",
        ],
    },
}


def read_text(path):
    return path.read_text(encoding="utf-8")


def extract_spec_data_blocks(path):
    text = read_text(path)
    blocks = []
    marker = "```json spec-data"
    start = 0
    while True:
        marker_pos = text.find(marker, start)
        if marker_pos == -1:
            break
        block_start = text.find("\n", marker_pos)
        if block_start == -1:
            break
        block_end = text.find("```", block_start + 1)
        if block_end == -1:
            raise ValueError(f"닫히지 않은 spec-data 코드블록: {path}")
        raw = text[block_start + 1:block_end].strip()
        if raw:
            try:
                blocks.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON 파싱 실패: {path} line {exc.lineno}, col {exc.colno}: {exc.msg}") from exc
        start = block_end + 3
    return blocks


def clean_heading(value):
    value = re.sub(r"[*`#]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def heading_id(title):
    match = re.match(r"(\d+(?:-\d+)?)\.", title)
    if match:
        return match.group(1)
    return title


def extract_front_sections(path):
    text = read_text(path)
    headings = []
    pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    for idx, match in enumerate(matches):
        raw_title = clean_heading(match.group(2))
        if raw_title.startswith("📌"):
            continue
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        headings.append(
            {
                "id": heading_id(raw_title),
                "level": len(match.group(1)),
                "title": raw_title,
                "line": text[: match.start()].count("\n") + 1,
                "body": body,
                "excerpt": body.replace("\n\n", "\n")[:700],
            }
        )
    return headings


def find_line(path, needle):
    if not path.exists() or not needle:
        return None
    for idx, line in enumerate(read_text(path).splitlines(), start=1):
        if needle in line:
            return idx
    return None


def load_backend_data():
    data = {"entities": {}, "apis": {}, "source_files": {}}
    for path in sorted(SPEC_TEXT_DIR.glob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        data["source_files"][rel] = {
            "title": "",
            "entities": [],
            "apis": [],
            "top_keys": [],
        }
        text = read_text(path)
        first_heading = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if first_heading:
            data["source_files"][rel]["title"] = clean_heading(first_heading.group(1))
        for block in extract_spec_data_blocks(path):
            data["source_files"][rel]["top_keys"].extend(block.keys())
            for entity, fields in block.get("entities", {}).items():
                data["entities"].setdefault(entity, {"fields": {}, "source_file": rel})
                data["source_files"][rel]["entities"].append(entity)
                for row in fields:
                    if len(row) < 4:
                        continue
                    field_name, field_type, required, note = row[:4]
                    data["entities"][entity]["fields"][field_name] = {
                        "name": field_name,
                        "type": field_type,
                        "required": required,
                        "note": note,
                        "source_file": rel,
                        "line": find_line(path, f'"{field_name}"'),
                    }
            for group, apis in block.get("apis", {}).items():
                data["apis"].setdefault(group, {"items": {}, "source_file": rel})
                data["source_files"][rel]["apis"].append(group)
                for row in apis:
                    if len(row) < 3:
                        continue
                    endpoint, purpose, params = row[:3]
                    data["apis"][group]["items"][endpoint] = {
                        "endpoint": endpoint,
                        "purpose": purpose,
                        "params": params,
                        "source_file": rel,
                        "line": find_line(path, endpoint),
                    }
    return data


def link_for_source(source_file, line=None):
    if not source_file:
        return ""
    suffix = f"#L{line}" if line else ""
    return f"{GITHUB_BLOB_BASE}/{source_file}{suffix}"


def resolve_mapping(mapping, backend, front_sections):
    front_lookup = {section["id"]: section for section in front_sections}
    resolved_sections = [front_lookup[key] for key in mapping["front_sections"] if key in front_lookup]
    missing_front_sections = [key for key in mapping["front_sections"] if key not in front_lookup]

    field_refs = []
    api_refs = []
    missing_refs = []
    for entity, fields in mapping.get("entities", {}).items():
        entity_data = backend["entities"].get(entity)
        if not entity_data:
            missing_refs.append(f"entity:{entity}")
            continue
        for field in fields:
            field_data = entity_data["fields"].get(field)
            if not field_data:
                missing_refs.append(f"field:{entity}.{field}")
                continue
            field_refs.append({**field_data, "entity": entity, "href": link_for_source(field_data["source_file"], field_data["line"])})

    for group, endpoints in mapping.get("apis", {}).items():
        group_data = backend["apis"].get(group)
        if not group_data:
            missing_refs.append(f"api_group:{group}")
            continue
        for endpoint in endpoints:
            api_data = group_data["items"].get(endpoint)
            if not api_data:
                missing_refs.append(f"api:{group}:{endpoint}")
                continue
            api_refs.append({**api_data, "group": group, "href": link_for_source(api_data["source_file"], api_data["line"])})

    total_expected = sum(len(fields) for fields in mapping.get("entities", {}).values()) + sum(
        len(endpoints) for endpoints in mapping.get("apis", {}).values()
    )
    found = len(field_refs) + len(api_refs)
    coverage = 1.0 if total_expected == 0 else found / total_expected

    return {
        **mapping,
        "implementation_guides": IMPLEMENTATION_GUIDES.get(mapping["id"], []),
        "playbook": SCREEN_PLAYBOOKS.get(mapping["id"], {}),
        "front_refs": resolved_sections,
        "field_refs": field_refs,
        "api_refs": api_refs,
        "missing_front_sections": missing_front_sections,
        "missing_refs": missing_refs,
        "coverage": round(coverage, 3),
        "status": "needs_attention" if missing_refs or missing_front_sections or coverage < 1 else "connected",
    }


def clip_text(value, limit=160):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def build_ai_brief(index):
    lines = [
        "# AI 작업용 요약: 사장님 웹앱 ↔ 백엔드",
        "",
        "이 텍스트는 HTML 전체를 AI 코딩 도구에 붙여넣는 대신 사용할 압축 컨텍스트입니다.",
        "목표: 사장님 웹앱 프론트 구현자가 백엔드 API/필드/상태 규칙을 빠르게 이해하고, 없는 API나 임의 필드를 만들지 않게 합니다.",
        "",
        "공통 원칙:",
        "- 백엔드 원본은 spec_text/*.md이고, 이 요약은 그 원본을 화면 구현 관점으로 압축한 것입니다.",
        "- API endpoint와 필드명은 아래 목록을 우선 사용합니다. 목록에 없는 값이 필요하면 백엔드 담당자에게 확인합니다.",
        "- 에러 처리는 UNAUTHORIZED, FORBIDDEN, VERIFICATION_REQUIRED, VALIDATION_ERROR, CONFLICT, RATE_LIMITED를 화면에서 구분합니다.",
        "- 사장님 사업자 인증 전에는 초안 작성은 허용하지만 공개 전환과 예약 운영 처리는 막습니다.",
        "- 날짜/시간은 서버 UTC 저장, 화면은 샵 로컬 시간대로 표시합니다.",
        "- 리스트는 cursor 기반 페이지네이션을 기본으로 가정합니다.",
        "",
        "핵심 상태 규칙:",
        "- MVP는 1사장님=1샵 단수 구조입니다. 사장님 웹에서는 /owner/shop, /owner/designs, /owner/designers 계열을 우선 사용합니다.",
        "- pending 예약은 슬롯을 완전히 잠그는 상태가 아닙니다. 사장님 수락 시점에 충돌을 다시 확인합니다.",
        "- 계좌이체 예약은 pending -> payment_pending -> confirmed 흐름입니다. 유저의 [입금 완료]만으로 확정되지 않고 사장님 [입금 확인됨]이 필요합니다.",
        "- 디자인 이미지는 1~5장입니다. 이미지 변경 시 AI 분석을 다시 시작합니다.",
        "- 사용자 노출 조건은 owner 승인 + shop active + design active + ai_analysis_status=done 조합입니다.",
        "",
        "기능별 구현 컨텍스트:",
    ]

    for item in index["mappings"]:
        lines.extend(
            [
                "",
                f"## {item['id']}. {item['title']}",
                f"요약: {item['summary']}",
            ]
        )
        if item.get("implementation_guides"):
            lines.append("구현 가이드:")
            lines.extend(f"- {guide}" for guide in item["implementation_guides"])
        if item.get("checkpoints"):
            lines.append("체크포인트:")
            lines.extend(f"- {checkpoint}" for checkpoint in item["checkpoints"])
        playbook = item.get("playbook") or {}
        if playbook.get("api_sequence"):
            lines.append("API 호출 순서:")
            lines.extend(f"- {row}" for row in playbook["api_sequence"])
        if playbook.get("ui_events"):
            lines.append("버튼/이벤트 처리:")
            lines.extend(
                f"- {trigger} -> {api} -> 성공: {success} / 실패: {failure}"
                for trigger, api, success, failure in playbook["ui_events"]
            )
        if playbook.get("states"):
            lines.append("화면 상태:")
            lines.extend(f"- {row}" for row in playbook["states"])
        if playbook.get("qa"):
            lines.append("QA 체크리스트:")
            lines.extend(f"- [ ] {row}" for row in playbook["qa"])
        if item.get("field_refs"):
            field_names = ", ".join(f"{ref['entity']}.{ref['name']}" for ref in item["field_refs"])
            lines.append(f"관련 필드: {field_names}")
        if item.get("api_refs"):
            lines.append("관련 API:")
            lines.extend(
                f"- {ref['endpoint']} : {clip_text(ref.get('purpose'), 120)}"
                for ref in item["api_refs"]
            )

    lines.extend(
        [
            "",
            "프론트 구현 요청 방식:",
            "- 화면 진입 시 호출 API, 버튼 클릭 시 호출 API, 성공 후 화면 변화, 실패 시 문구를 먼저 정리한 뒤 구현합니다.",
            "- 프론트에서 복잡한 상태 조합을 새로 만들지 말고 백엔드 상태값과 available action 규칙을 확인합니다.",
            "- 이미지 업로드, 예약 상태 변경, 결제 확인, AI 분석 상태는 특히 임의 구현을 피합니다.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def build_index():
    if not FRONT_SPEC_PATH.exists():
        raise FileNotFoundError(f"프론트 명세서를 찾을 수 없습니다: {FRONT_SPEC_PATH}")
    frontend_sections = extract_front_sections(FRONT_SPEC_PATH)
    backend = load_backend_data()
    mappings = [resolve_mapping(item, backend, frontend_sections) for item in OWNER_SECTION_MAP]

    all_fields = []
    for entity, entity_data in sorted(backend["entities"].items()):
        for field in entity_data["fields"].values():
            all_fields.append({**field, "entity": entity, "href": link_for_source(field["source_file"], field["line"])})

    all_apis = []
    for group, group_data in sorted(backend["apis"].items()):
        for api in group_data["items"].values():
            all_apis.append({**api, "group": group, "href": link_for_source(api["source_file"], api["line"])})

    index = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": {
            "frontend_spec": FRONT_SPEC_PATH.relative_to(ROOT).as_posix(),
            "backend_spec_dir": SPEC_TEXT_DIR.relative_to(ROOT).as_posix(),
        },
        "stats": {
            "front_sections": len(frontend_sections),
            "mapping_sections": len(mappings),
            "backend_entities": len(backend["entities"]),
            "backend_fields": len(all_fields),
            "api_groups": len(backend["apis"]),
            "apis": len(all_apis),
            "attention_sections": sum(1 for item in mappings if item["status"] != "connected"),
        },
        "mappings": mappings,
        "backend": {
            "source_files": backend["source_files"],
            "fields": all_fields,
            "apis": all_apis,
        },
    }
    index["ai_brief"] = build_ai_brief(index)
    return index


HTML_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>사장님 웹앱 ↔ 백엔드 명세 인덱스</title>
  <style>
    :root {
      --bg: #f5f7fa;
      --panel: #ffffff;
      --line: #d8dee8;
      --text: #17202a;
      --muted: #657386;
      --accent: #0f766e;
      --accent-weak: #e6f4f1;
      --warn: #9a3412;
      --warn-weak: #fff3e8;
      --blue: #1d4ed8;
      --blue-weak: #edf3ff;
      --green: #166534;
      --green-weak: #ecfdf3;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, "Malgun Gothic", sans-serif;
      background: var(--bg);
      color: var(--text);
      font-size: 14px;
    }
    header {
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      padding: 16px 22px;
      display: flex;
      gap: 16px;
      align-items: center;
      justify-content: space-between;
    }
    h1 {
      font-size: 20px;
      margin: 0 0 4px;
      letter-spacing: 0;
    }
    .meta { color: var(--muted); font-size: 12px; }
    .stats { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
    .header-right {
      display: grid;
      gap: 8px;
      justify-items: end;
    }
    .actions {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    .stat {
      border: 1px solid var(--line);
      background: #fafbfc;
      padding: 7px 10px;
      border-radius: 6px;
      min-width: 88px;
    }
    .stat b { display: block; font-size: 16px; }
    main {
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      min-height: calc(100vh - 86px);
    }
    aside {
      border-right: 1px solid var(--line);
      background: var(--panel);
      padding: 16px;
      overflow: auto;
    }
    .content { padding: 18px 22px 36px; overflow: auto; }
    .toolbar {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      margin-bottom: 12px;
    }
    input, select {
      width: 100%;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 6px;
      padding: 9px 10px;
      font: inherit;
    }
    button {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 6px;
      padding: 8px 10px;
      font: inherit;
      cursor: pointer;
    }
    button:hover { border-color: var(--accent); }
    .copy-btn {
      border-color: var(--accent);
      background: var(--accent);
      color: #fff;
      font-weight: 700;
    }
    .copy-btn:hover { filter: brightness(0.96); }
    .text-link {
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 6px;
      padding: 8px 10px;
      color: var(--text);
      font-size: 13px;
    }
    .section-list { display: grid; gap: 8px; }
    .section-item {
      width: 100%;
      text-align: left;
      border: 1px solid var(--line);
      background: #fff;
      padding: 10px;
      border-radius: 6px;
    }
    .section-item.active {
      border-color: var(--accent);
      background: var(--accent-weak);
    }
    .section-title { font-weight: 700; margin-bottom: 5px; }
    .section-summary { color: var(--muted); font-size: 12px; line-height: 1.45; }
    .chips { display: flex; gap: 5px; flex-wrap: wrap; margin-top: 8px; }
    .chip {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--muted);
      padding: 2px 7px;
      font-size: 11px;
      line-height: 18px;
    }
    .chip.good { color: var(--green); background: var(--green-weak); border-color: #bbf7d0; }
    .chip.warn { color: var(--warn); background: var(--warn-weak); border-color: #fed7aa; }
    .detail-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 16px;
    }
    h2 { font-size: 22px; margin: 0 0 6px; letter-spacing: 0; }
    h3 { font-size: 15px; margin: 22px 0 8px; letter-spacing: 0; }
    .summary { color: var(--muted); line-height: 1.55; max-width: 920px; }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .panel {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 6px;
      padding: 12px;
    }
    .panel.full { grid-column: 1 / -1; }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      overflow: hidden;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 8px 9px;
      text-align: left;
      vertical-align: top;
      line-height: 1.45;
    }
    th {
      background: #f8fafc;
      color: #2d3a4a;
      font-size: 12px;
      font-weight: 700;
    }
    tr:last-child td { border-bottom: 0; }
    code {
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      background: #f1f5f9;
      padding: 1px 4px;
      border-radius: 4px;
    }
    a { color: var(--blue); text-decoration: none; }
    a:hover { text-decoration: underline; }
    ul { margin: 0; padding-left: 18px; }
    li { margin: 4px 0; }
    .excerpt {
      white-space: pre-wrap;
      max-height: 260px;
      overflow: auto;
      color: #2d3a4a;
      background: #fbfcfe;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      line-height: 1.55;
    }
    .all-index {
      margin-top: 20px;
      border-top: 1px solid var(--line);
      padding-top: 14px;
    }
    .help-box {
      border: 1px solid #bfdbfe;
      background: var(--blue-weak);
      border-radius: 6px;
      padding: 10px;
      margin-bottom: 12px;
      color: #1e3a8a;
      line-height: 1.5;
      font-size: 12px;
    }
    .index-results {
      display: grid;
      gap: 6px;
      max-height: 320px;
      overflow: auto;
      margin-top: 8px;
    }
    .result-row {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      padding: 8px;
      line-height: 1.45;
    }
    @media (max-width: 980px) {
      header { display: block; }
      .stats { justify-content: flex-start; margin-top: 12px; }
      .header-right { justify-items: start; margin-top: 12px; }
      .actions { justify-content: flex-start; }
      main { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); }
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>사장님 웹앱 ↔ 백엔드 명세 인덱스</h1>
      <div class="meta" id="generatedMeta"></div>
    </div>
    <div class="header-right">
      <div class="stats" id="stats"></div>
      <div class="actions">
        <button class="copy-btn" id="copyAiBriefBtn" type="button">AI 요약 복사</button>
        <a class="text-link" href="owner_webapp_backend_index.ai.txt">AI용 TXT 열기</a>
        <span class="meta" id="copyAiBriefStatus"></span>
      </div>
    </div>
  </header>
  <main>
    <aside>
      <div class="help-box">
        <b>분석 순서</b><br>
        1. 왼쪽 기능 선택<br>
        2. 구현 분석 가이드 확인<br>
        3. 관련 필드와 API 출처로 이동<br>
        4. 프론트 명세 발췌로 화면 요구사항 확인
      </div>
      <div class="toolbar">
        <input id="filterInput" type="search" placeholder="기능, 필드, API 검색">
        <select id="statusFilter" aria-label="상태 필터">
          <option value="all">전체</option>
          <option value="connected">연결됨</option>
          <option value="needs_attention">확인 필요</option>
        </select>
      </div>
      <div class="section-list" id="sectionList"></div>
      <div class="all-index">
        <h3>전체 백엔드 색인</h3>
        <input id="globalSearch" type="search" placeholder="예: payment, owner_tags, /owner/reservations">
        <div class="index-results" id="globalResults"></div>
      </div>
    </aside>
    <section class="content" id="detail"></section>
  </main>
  <script id="index-data" type="application/json">__INDEX_DATA__</script>
  <script>
    const data = JSON.parse(document.getElementById("index-data").textContent);
    let currentId = data.mappings[0]?.id || "";

    const escapeHtml = (value) => String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

    const statusLabel = (item) => item.status === "connected" ? "연결됨" : "확인 필요";
    const statusClass = (item) => item.status === "connected" ? "good" : "warn";
    const sourceLink = (ref) => ref.href
      ? `<a href="${escapeHtml(ref.href)}">${escapeHtml(ref.source_file)}${ref.line ? ":" + ref.line : ""}</a>`
      : escapeHtml(ref.source_file || "");

    const easyFieldMap = {
      verification_status: "사장님 계정이 사업자 인증을 통과했는지 나타냅니다. 승인 전에는 공개/예약 처리를 막는 기준이 됩니다.",
      visibility: "고객에게 보이는지 정하는 공개 상태입니다. draft는 임시저장, active는 공개, hidden은 숨김입니다.",
      auto_accept: "예약 요청을 사장님 확인 없이 자동으로 받을지 정하는 설정입니다. MVP 기본값은 수동 수락입니다.",
      payment_method: "현장결제인지, 계좌이체 예약금 안내인지 정하는 결제 운영 방식입니다.",
      deposit_amount: "계좌이체 예약금으로 안내할 금액입니다.",
      bank_name: "입금 안내에 보여줄 은행명입니다.",
      bank_account_number: "입금 안내에 보여줄 계좌번호입니다.",
      bank_account_holder: "입금 안내에 보여줄 예금주명입니다.",
      owner_tags: "사장님이 직접 붙이는 자유 태그입니다. AI 태그와 별도로 저장해서 검색 의도에 반영합니다.",
      ai_tags: "AI가 표준 태그 사전에서 골라 붙인 태그입니다. 고객 검색과 필터에 사용됩니다.",
      ai_color_palette: "AI가 판단한 대표 색상 목록입니다.",
      ai_style_category: "AI가 판단한 디자인의 큰 스타일 분류입니다.",
      ai_analysis_status: "AI 분석 진행 상태입니다. 사장님 화면의 분석 중/완료/실패 표시 기준입니다.",
      original_url: "사장님이 올린 원본 이미지 주소입니다.",
      cropped_url: "AI가 손톱 영역만 잘라 만든 이미지 주소입니다.",
      ai_transform_status: "원본 이미지에서 손톱 영역을 잘라내는 1단계 성공/실패 상태입니다.",
      ai_classify_status: "잘라낸 이미지에서 태그와 색상을 뽑는 2단계 성공/실패 상태입니다.",
      status: "예약이나 작업이 현재 어느 상태인지 나타냅니다. 화면 버튼 노출과 다음 동작이 이 값으로 갈립니다.",
      user_payment_notified_at: "고객이 [입금 완료]를 눌러 사장님에게 확인 요청을 보낸 시각입니다.",
      owner_payment_confirmed_at: "사장님이 실제 입금을 확인하고 승인한 시각입니다.",
      reservation_policy_snapshot: "예약 당시의 운영 정책을 복사해 둔 값입니다. 나중에 샵 설정이 바뀌어도 기존 예약 기준을 보존합니다.",
      payment_method_snapshot: "예약 당시의 결제 방식을 복사해 둔 값입니다.",
      shop_reply: "리뷰에 사장님이 남긴 답변입니다.",
      deeplink_target: "알림을 클릭했을 때 이동할 화면 위치입니다.",
    };

    const easyApiMap = {
      "POST /owner/auth/register": "사장님 계정을 새로 만드는 가입 API입니다.",
      "GET /owner/me": "로그인한 사장님의 계정 상태와 사업자 인증 상태를 확인합니다.",
      "POST /owner/business-verification": "사업자등록증 등 인증 정보를 제출하거나 재제출합니다.",
      "POST /owner/shop": "사장님 샵 초안을 처음 만듭니다. 승인 전에도 저장은 가능하지만 공개는 막습니다.",
      "GET /owner/shop": "내 단수 샵 정보를 불러옵니다.",
      "PATCH /owner/shop": "샵 이름, 주소, 전화번호 같은 기본 정보를 수정합니다.",
      "PATCH /owner/shop/visibility": "샵을 고객에게 공개하거나 숨깁니다. 사업자 승인 후에만 공개할 수 있습니다.",
      "POST /owner/designs": "새 디자인을 등록합니다. 화면은 바로 저장되고 AI 분석은 뒤에서 진행됩니다.",
      "GET /owner/designs": "내 디자인 목록을 가져옵니다. 분석 중/실패/숨김 탭 구성에 사용합니다.",
      "PATCH /owner/designs/{design_id}": "디자인 제목, 가격, 소요 시간, 사장님 태그를 수정합니다.",
      "POST /owner/designs/{design_id}/images": "디자인 사진을 추가합니다. 총 5장 제한을 넘으면 실패합니다.",
      "POST /owner/designs/{design_id}/reanalyze": "AI 분석 실패 또는 재분석 버튼과 연결됩니다.",
      "PATCH /owner/designs/{design_id}/visibility": "디자인을 고객에게 공개하거나 숨깁니다.",
      "GET /owner/reservations": "사장님 예약 목록과 캘린더를 채우는 API입니다.",
      "POST /owner/reservations/{id}/accept": "사장님이 예약 요청을 수락합니다. 계좌이체면 바로 확정이 아니라 입금 대기 상태가 됩니다.",
      "POST /owner/reservations/{id}/payment-confirmed": "사장님이 실제 입금을 확인하고 예약을 확정합니다.",
      "POST /owner/reservations/{id}/reject": "사장님이 예약 요청을 거절합니다.",
      "POST /owner/reservations/{id}/complete": "시술 완료 처리 버튼과 연결됩니다.",
      "POST /owner/reservations/{id}/no-show": "고객이 오지 않았을 때 노쇼로 표시합니다. MVP에서는 방어적으로 제한합니다.",
      "GET /owner/reviews": "내 샵 리뷰 목록을 보여줍니다.",
      "GET /owner/snaps": "내 샵이 태그된 스네일 게시물을 보여줍니다.",
      "GET /owner/dashboard/summary": "대시보드 숫자 카드들을 한 번에 가져옵니다.",
      "GET /owner/notifications": "사장님 알림함 목록을 가져옵니다.",
    };

    function easyField(ref) {
      return easyFieldMap[ref.name] || ref.note || "-";
    }

    function easyApi(ref) {
      return easyApiMap[ref.endpoint] || ref.purpose || "-";
    }

    function renderStats() {
      document.getElementById("generatedMeta").textContent =
        `${data.source.frontend_spec} / ${data.source.backend_spec_dir} / ${data.generated_at}`;
      const rows = [
        ["기능", data.stats.mapping_sections],
        ["필드", data.stats.backend_fields],
        ["API", data.stats.apis],
        ["확인 필요", data.stats.attention_sections],
      ];
      document.getElementById("stats").innerHTML = rows
        .map(([label, value]) => `<div class="stat"><b>${value}</b>${label}</div>`)
        .join("");
    }

    function searchText(item) {
      return [
        item.id,
        item.title,
        item.summary,
        ...(item.keywords || []),
        ...(item.playbook?.api_sequence || []),
        ...(item.playbook?.states || []),
        ...(item.playbook?.qa || []),
        ...(item.playbook?.ui_events || []).flat(),
        ...(item.field_refs || []).map((ref) => `${ref.entity} ${ref.name} ${ref.note}`),
        ...(item.api_refs || []).map((ref) => `${ref.group} ${ref.endpoint} ${ref.purpose} ${ref.params}`),
      ].join(" ").toLowerCase();
    }

    function renderList() {
      const q = document.getElementById("filterInput").value.trim().toLowerCase();
      const status = document.getElementById("statusFilter").value;
      const items = data.mappings.filter((item) => {
        const okText = !q || searchText(item).includes(q);
        const okStatus = status === "all" || item.status === status;
        return okText && okStatus;
      });
      document.getElementById("sectionList").innerHTML = items.map((item) => `
        <button class="section-item ${item.id === currentId ? "active" : ""}" data-id="${escapeHtml(item.id)}">
          <div class="section-title">${escapeHtml(item.id)}. ${escapeHtml(item.title)}</div>
          <div class="section-summary">${escapeHtml(item.summary)}</div>
          <div class="chips">
            <span class="chip ${statusClass(item)}">${statusLabel(item)}</span>
            <span class="chip">필드 ${item.field_refs.length}</span>
            <span class="chip">API ${item.api_refs.length}</span>
          </div>
        </button>
      `).join("");
      document.querySelectorAll(".section-item").forEach((button) => {
        button.addEventListener("click", () => {
          currentId = button.dataset.id;
          renderList();
          renderDetail();
        });
      });
      if (!items.some((item) => item.id === currentId) && items[0]) {
        currentId = items[0].id;
        renderList();
        renderDetail();
      }
    }

    function renderDetail() {
      const item = data.mappings.find((entry) => entry.id === currentId) || data.mappings[0];
      if (!item) return;
      const implementationGuides = item.implementation_guides?.length
        ? `<ul>${item.implementation_guides.map((row) => `<li>${escapeHtml(row)}</li>`).join("")}</ul>`
        : "<div class='meta'>등록된 구현 가이드 없음</div>";
      const checkpoints = item.checkpoints?.length
        ? `<ul>${item.checkpoints.map((row) => `<li>${escapeHtml(row)}</li>`).join("")}</ul>`
        : "<div class='meta'>등록된 체크 포인트 없음</div>";
      const playbook = item.playbook || {};
      const apiSequence = playbook.api_sequence?.length
        ? `<ol>${playbook.api_sequence.map((row) => `<li>${escapeHtml(row)}</li>`).join("")}</ol>`
        : "<div class='meta'>등록된 API 호출 순서 없음</div>";
      const stateRows = playbook.states?.length
        ? `<ul>${playbook.states.map((row) => `<li>${escapeHtml(row)}</li>`).join("")}</ul>`
        : "<div class='meta'>등록된 화면 상태 없음</div>";
      const qaRows = playbook.qa?.length
        ? `<ul>${playbook.qa.map((row) => `<li><label><input type="checkbox"> ${escapeHtml(row)}</label></li>`).join("")}</ul>`
        : "<div class='meta'>등록된 QA 체크리스트 없음</div>";
      const eventRows = (playbook.ui_events || []).map((row) => `
        <tr>
          <td>${escapeHtml(row[0])}</td>
          <td><code>${escapeHtml(row[1])}</code></td>
          <td>${escapeHtml(row[2])}</td>
          <td>${escapeHtml(row[3])}</td>
        </tr>
      `).join("");
      const missing = [...(item.missing_front_sections || []), ...(item.missing_refs || [])];
      const missingPanel = missing.length
        ? `<div class="panel full"><h3>확인 필요</h3><ul>${missing.map((row) => `<li><code>${escapeHtml(row)}</code></li>`).join("")}</ul></div>`
        : "";
      const frontRows = item.front_refs.map((ref) => `
        <tr>
          <td><code>${escapeHtml(ref.id)}</code></td>
          <td>${escapeHtml(ref.title)}</td>
          <td>${escapeHtml(ref.line)}</td>
        </tr>
      `).join("");
      const fieldRows = item.field_refs.map((ref) => `
        <tr>
          <td><code>${escapeHtml(ref.entity)}.${escapeHtml(ref.name)}</code></td>
          <td>${escapeHtml(easyField(ref))}</td>
          <td>${escapeHtml(ref.note)}</td>
          <td>${sourceLink(ref)}</td>
        </tr>
      `).join("");
      const apiRows = item.api_refs.map((ref) => `
        <tr>
          <td><code>${escapeHtml(ref.endpoint)}</code><div class="meta">${escapeHtml(ref.group)}</div></td>
          <td>${escapeHtml(easyApi(ref))}</td>
          <td>${escapeHtml(ref.purpose)}</td>
          <td>${escapeHtml(ref.params)}</td>
          <td>${sourceLink(ref)}</td>
        </tr>
      `).join("");
      const excerpt = item.front_refs.map((ref) => `# ${ref.title}\\n${ref.excerpt}`).join("\\n\\n");
      document.getElementById("detail").innerHTML = `
        <div class="detail-header">
          <div>
            <h2>${escapeHtml(item.id)}. ${escapeHtml(item.title)}</h2>
            <div class="summary">${escapeHtml(item.summary)}</div>
            <div class="chips">
              ${(item.keywords || []).map((word) => `<span class="chip">${escapeHtml(word)}</span>`).join("")}
            </div>
          </div>
          <span class="chip ${statusClass(item)}">${statusLabel(item)} · ${Math.round(item.coverage * 100)}%</span>
        </div>
        <div class="grid">
          <div class="panel full"><h3>화면별 API 호출 순서</h3>${apiSequence}</div>
          <div class="panel full"><h3>버튼/이벤트 구현 지시서</h3><table><thead><tr><th>화면 이벤트</th><th>호출 API</th><th>성공 시</th><th>실패 시</th></tr></thead><tbody>${eventRows || "<tr><td colspan='4'>등록된 이벤트 없음</td></tr>"}</tbody></table></div>
          <div class="panel"><h3>화면 상태 규칙</h3>${stateRows}</div>
          <div class="panel"><h3>QA 체크리스트</h3>${qaRows}</div>
          <div class="panel full"><h3>구현 분석 가이드</h3>${implementationGuides}</div>
          <div class="panel"><h3>프론트 섹션</h3><table><thead><tr><th>ID</th><th>제목</th><th>라인</th></tr></thead><tbody>${frontRows || "<tr><td colspan='3'>연결된 섹션 없음</td></tr>"}</tbody></table></div>
          <div class="panel"><h3>체크 포인트</h3>${checkpoints}</div>
          ${missingPanel}
          <div class="panel full"><h3>관련 필드</h3><table><thead><tr><th>필드</th><th>쉽게 말하면</th><th>원문 메모</th><th>출처</th></tr></thead><tbody>${fieldRows || "<tr><td colspan='4'>관련 필드 없음</td></tr>"}</tbody></table></div>
          <div class="panel full"><h3>관련 API</h3><table><thead><tr><th>엔드포인트</th><th>쉽게 말하면</th><th>원문 용도</th><th>요청값</th><th>출처</th></tr></thead><tbody>${apiRows || "<tr><td colspan='5'>관련 API 없음</td></tr>"}</tbody></table></div>
          <div class="panel full"><h3>프론트 명세 발췌</h3><div class="excerpt">${escapeHtml(excerpt || "발췌 없음")}</div></div>
        </div>
      `;
    }

    function renderGlobalResults() {
      const q = document.getElementById("globalSearch").value.trim().toLowerCase();
      const target = [...data.backend.fields, ...data.backend.apis];
      const rows = target.filter((item) => {
        if (!q) return false;
        const text = [
          item.entity,
          item.name,
          item.type,
          item.note,
          item.group,
          item.endpoint,
          item.purpose,
          item.params,
          item.source_file,
        ].join(" ").toLowerCase();
        return text.includes(q);
      }).slice(0, 80);
      document.getElementById("globalResults").innerHTML = rows.length
        ? rows.map((item) => {
          const label = item.endpoint
            ? `<code>${escapeHtml(item.endpoint)}</code><div class="meta">${escapeHtml(item.group)} · API</div>`
            : `<code>${escapeHtml(item.entity)}.${escapeHtml(item.name)}</code><div class="meta">${escapeHtml(item.type)} · ${escapeHtml(item.required)}</div>`;
          const body = item.endpoint ? item.purpose : item.note;
          const easy = item.endpoint ? easyApi(item) : easyField(item);
          return `<div class="result-row">${label}<div>${escapeHtml(easy || body)}</div><div class="meta">${escapeHtml(body)}</div><div class="meta">${sourceLink(item)}</div></div>`;
        }).join("")
        : `<div class="meta">검색어를 입력하면 필드/API가 표시됩니다.</div>`;
    }

    async function copyAiBrief() {
      const status = document.getElementById("copyAiBriefStatus");
      try {
        await navigator.clipboard.writeText(data.ai_brief || "");
        status.textContent = "복사됨";
      } catch (error) {
        const textarea = document.createElement("textarea");
        textarea.value = data.ai_brief || "";
        textarea.setAttribute("readonly", "");
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        status.textContent = "복사됨";
      }
      window.setTimeout(() => { status.textContent = ""; }, 1800);
    }

    document.getElementById("filterInput").addEventListener("input", renderList);
    document.getElementById("statusFilter").addEventListener("change", renderList);
    document.getElementById("globalSearch").addEventListener("input", renderGlobalResults);
    document.getElementById("copyAiBriefBtn").addEventListener("click", copyAiBrief);
    renderStats();
    renderList();
    renderDetail();
    renderGlobalResults();
  </script>
</body>
</html>
"""


def write_outputs(index):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_JSON_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    AI_TEXT_PATH.write_text(index["ai_brief"], encoding="utf-8")
    SHARED_AI_TEXT_PATH.write_text(index["ai_brief"], encoding="utf-8")
    json_for_html = json.dumps(index, ensure_ascii=False).replace("</", "<\\/")
    html = HTML_TEMPLATE.replace("__INDEX_DATA__", json_for_html)
    INDEX_HTML_PATH.write_text(html, encoding="utf-8")
    SHARED_HTML_PATH.write_text(html, encoding="utf-8")


def main():
    index = build_index()
    write_outputs(index)
    print(f"saved: {INDEX_JSON_PATH}")
    print(f"saved: {INDEX_HTML_PATH}")
    print(f"saved: {SHARED_HTML_PATH}")
    print(f"saved: {AI_TEXT_PATH}")
    print(f"saved: {SHARED_AI_TEXT_PATH}")
    print(f"sections: {index['stats']['mapping_sections']}")
    print(f"fields: {index['stats']['backend_fields']}")
    print(f"apis: {index['stats']['apis']}")
    print(f"attention_sections: {index['stats']['attention_sections']}")


if __name__ == "__main__":
    main()
