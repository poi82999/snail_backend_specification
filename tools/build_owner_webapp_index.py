import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GITHUB_BLOB_BASE = "https://github.com/poi82999/snail_backend_specification/blob/main"
SPEC_TEXT_DIR = ROOT / "spec_text"
CANONICAL_PATH = ROOT / "spec_canonical" / "backend_spec_v3.canonical.json"
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
                "rating_avg",
                "rating_count",
                "favorite_count",
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
                "favorite_count",
                "view_count",
            ],
            "DesignImage": [
                "image_id",
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
                "assigned_by",
                "idempotency_key",
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
                "status",
                "tags",
                "like_count",
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
            "사장님 전용 리뷰 목록은 `{api:review:reviews}`를 사용합니다. 사장님 토큰만 있으면 자동으로 내 샵 리뷰만 조회됩니다. `{api:review:reviews}`는 일반 고객용이므로 사장님 웹에서는 쓸 필요 없습니다.",
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
            "사장님 전용 스네일 목록은 `{api:snap:snaps}`를 사용합니다. 사장님 토큰만 있으면 자동으로 내 샵이 태그된 스네일만 조회됩니다. `{api:snap:snaps}`는 일반 유저용이므로 사장님 웹에서는 쓸 필요 없습니다.",
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
        "초기 진입: 로컬 스토리지에 토큰이 있다면 가장 먼저 `{api:owner_auth:me}` API를 호출해서 현재 사장님의 가입/승인 상태(`verification_status`)를 확인해주세요.",
        "미인증 처리: 토큰이 아예 없거나 API 호출 결과로 `401 Unauthorized` 에러가 발생한다면, 유저가 당황하지 않게 자연스럽게 '로그인 화면'으로 이동시켜주세요.",
        "인증 상태 분기: `VERIFICATION_REQUIRED` 에러는 '사업자 승인 대기/반려' 상태라는 뜻입니다. 완전 권한이 없는 `FORBIDDEN`과 명확히 구분해서, '사업자 인증 서류 제출 화면'으로 예쁘게 연결시켜주세요.",
        "비밀번호 재설정: 가입되지 않은 이메일로 재설정 요청이 들어오더라도 동일한 완료 메시지를 띄워주세요. (보안상 유저 정보 존재 여부를 노출하지 않기 위함입니다.)"
    ],
    "2": [
        "샵 리소스 단수 취급: 우리 서비스는 사장님 1명당 샵 1개(MVP 기준)만 가집니다. 따라서 프론트 라우팅이나 전역 상태에서 `shop_id`를 복잡하게 들고 다닐 필요 없이 무조건 `/owner/shop` 단수 API를 호출하시면 됩니다.",
        "초안 저장과 공개 전환: 사업자 승인이 나기 전(pending)이라도 샵 정보를 미리 작성하고 임시 저장(draft)할 수는 있어야 합니다. 단, 고객에게 샵을 노출하는 `visibility=active` 버튼이나 예약 운영 시작 버튼은 반드시 승인(approved) 후에만 켤 수 있게 비활성화(disabled) 해주세요.",
        "설정 충돌 방지 UI: [자동 예약 수락(auto_accept=true)]을 켰을 때, 결제 수단 중 [계좌이체 안내(bank_transfer_guide)] 옵션이 아예 클릭되지 않도록 회색으로 막아주세요. 백엔드에서도 거부하겠지만 프론트에서 먼저 막아주는 유저 경험이 핵심입니다."
    ],
    "3": [
        "디자이너 목록 관리: 디자이너는 내 단수 샵에 속한 하위 리소스입니다. 디자이너 목록을 불러오거나 추가/수정할 때는 `/owner/designers` 계열 API만 깔끔하게 사용하시면 됩니다.",
        "전문 태그(specialty_tags) 생략: 현재 이 필드는 단순 텍스트 배열이라 MVP에서는 프론트 입력 UI를 과감히 생략해도 됩니다. 이름, 직급, 경력, 프로필 사진, 활성 상태 등 필수 정보 입력 화면 구성에 먼저 집중해주세요.",
        "비활성 디자이너 표시: 디자이너를 비활성화하면 신규 예약 캘린더의 선택지에서는 사라지지만, 이미 그 디자이너에게 예약된 과거 내역은 남습니다. 따라서 예약 상세 화면에서는 '이 디자이너가 현재 비활성 상태'라는 것을 작은 배지로라도 알려줘야 합니다."
    ],
    "4": [
        "이미지 갯수 검증: 디자인 이미지는 최소 1장에서 최대 5장까지만 등록 가능합니다. 프론트의 업로드 UI 컴포넌트에서도 5장이 차면 업로드 버튼을 숨기거나 비활성화해서 백엔드와 정책을 100% 맞춰주세요.",
        "오너 태그(owner_tags) 주의: 사장님이 직접 다는 태그는 반드시 `owner_tags`라는 키로 배열을 묶어서 보내야 합니다. 과거에 썼던 `tags`라는 이름으로 보내면 백엔드에서 무시되니 주의하세요.",
        "사용자 노출 조건 안내: 사장님이 디자인을 등록했다고 바로 유저 앱에 노출되지 않습니다. [사장님 계정 승인 + 샵 공개 상태 + 디자인 공개 상태 + AI 분석 완료] 4박자가 모두 맞아야 합니다. 따라서 '공개'로 설정되어 있어도 아직 노출 안 되는 상황이라면, 툴팁이나 배지로 'AI 분석 중이라 아직 노출되지 않습니다' 등을 친절하게 안내해주세요."
    ],
    "5": [
        "신규 예약(pending)의 성격: pending 상태는 아직 해당 시간대가 캘린더에서 완벽히 잠긴(hard-lock) 상태가 아닙니다. 사장님 웹에서는 겹치는 시간대의 요청이라도 일단 모두 보여주되(created_at 오름차순), 사장님이 수락 버튼을 누르는 순간 겹치는지 최종 검사(CONFLICT 에러 반환)를 수행해야 합니다.",
        "계좌이체 예약 흐름: [계좌이체 샵]의 경우, 사장님이 예약을 수락하면 `payment_pending`(입금 대기) 상태가 됩니다. 유저가 앱에서 '입금 완료했어요!'를 눌러도 여전히 payment_pending입니다. 사장님이 통장 내역을 확인하고 [입금 확인 완료] 버튼을 눌러줘야 비로소 `confirmed`(확정)가 됩니다.",
        "노쇼(No-show) 버튼 제약: MVP에서는 악의적인 노쇼 처리를 방어하기 위해 예약이 `confirmed` 상태이고, 예약 시작 시간으로부터 30분이 지난 이후에만 노쇼 버튼을 활성화시켜주세요."
    ],
    "6": [
        "내 샵 리뷰 조회: 리뷰 목록을 가져올 때 `/shops/{id}/reviews` (일반 고객용 API)를 쓸 필요가 없습니다. 사장님 토큰을 달고 전용 API인 `/owner/reviews`를 호출하면 알아서 내 샵의 리뷰들만 가져옵니다.",
        "미답변 리뷰 필터 연동: 대시보드의 '미답변 리뷰(unanswered_review_count)' 카드를 클릭해서 리뷰 화면으로 넘어왔다면, 자동으로 `unanswered=true` 쿼리 필터가 적용된 상태로 렌더링되게 해주세요.",
        "답변 버튼 분기: 리뷰당 답변은 1개만 허용됩니다. `shop_reply` 데이터가 비어있다면 [답변 작성] 버튼을, 이미 채워져 있다면 [수정] / [삭제] 버튼을 노출하는 방식으로 화면을 분기해주세요."
    ],
    "7": [
        "스네일 목록 조회: 스네일(커뮤니티) 화면 역시 사장님 토큰을 달고 `/owner/snaps` 전용 API를 호출하면, 굳이 필터링을 복잡하게 하지 않아도 내 샵이 태그된 스네일들만 깔끔하게 모아서 줍니다.",
        "샵 뱃지 달기: 사장님이 스네일에 댓글을 달 때는 일반 유저 댓글 작성 API와 동일한 API를 씁니다. 서버가 알아서 '이건 사장님이 단 댓글이다'라고 인식하고 `author_type=shop`으로 저장해 줍니다. 댓글을 화면에 그릴 때 이 타입이면 '샵 공식' 뱃지를 예쁘게 달아주세요.",
        "신고 기능 제외: 스네일 신고 기능은 MVP 범위에서 제외되었습니다. UI 디자인에 신고 버튼이 있더라도 과감히 숨김 처리하고 기능 구현에 시간을 쓰지 마세요."
    ],
    "8": [
        "대시보드 통합 API: 오늘 예약 수, 신규 요청, 미답변 리뷰, 최근 스네일 태그 등 대시보드의 4개 지표는 `/owner/dashboard/summary` 단일 API 한 방으로 가져와서 카드들을 채워주세요.",
        "오늘 예약 집계 기준: 화면의 '오늘 예약' 숫자는 확정된 것만 의미하지 않습니다. `pending(대기)`, `payment_pending(입금대기)`, `confirmed(확정)` 3가지 상태의 오늘 날짜 예약 건수가 모두 합산되어 내려갑니다.",
        "딥링크 라우팅 유지: 대시보드 카드를 클릭해서 다른 화면(예: 예약 화면)으로 넘어갈 때, URL query parameter나 Router state에 해당 필터 조건(예: status=pending)을 잘 넘겨줘서 새로고침을 하더라도 필터가 풀리지 않게 꽉 잡아주세요."
    ],
    "9": [
        "알림 채널 전략: MVP에서는 브라우저 웹푸시(Web Push) 알림을 지원하지 않습니다. 대신 유저의 카카오 알림톡으로 발송하며, 동시에 웹 알림함(inbox)에 데이터를 차곡차곡 쌓아줍니다. 알림함 종모양 아이콘을 메인 채널로 구성해주세요.",
        "읽음 처리 + 이동 동기화: 유저가 새 알림을 클릭하면, 먼저 `{api:owner_notification:read}` API를 찔러 읽음 처리를 한 직후에, 알림 데이터에 있는 `deeplink_target` URL로 즉시 이동시켜주세요.",
        "알림함의 역할: 가끔 카카오 발송이 실패하더라도 웹 알림함 데이터는 무조건 생성되므로(신뢰성 100%), 사장님이 놓치는 일이 없도록 알림함 UI를 직관적으로 만들어주세요."
    ],
    "10": [
        "미정 정책 발견 시 대처법: 화면을 짜다가 '이 부분은 정책이 없는데 어떻게 하지?' 싶은 부분이 나오면, 절대 프론트엔드 코드에 하드코딩해서 임의로 결정하지 마시고 백엔드/기획 팀원에게 의사결정을 요청해 주세요.",
        "결정 후 UI 반영: 정책 수치가 결정되면 백엔드가 먼저 API 명세와 이 문서를 재생성할 것입니다. 프론트엔드는 반드시 이 문서의 에러 문구나 글자수 제한 등을 기준으로 UI validation 로직을 수정해야 싱크가 틀어지지 않습니다."
    ]
}


SCREEN_PLAYBOOKS = {
    "1": {
        "api_sequence": [
            "[초기 진입]: 사용자가 앱을 켰을 때 로컬 스토리지에 토큰이 있다면, 가장 먼저 `{api:owner_auth:me}` API를 호출해서 현재 사장님의 가입/승인 상태를 확인해주세요.",
            "[미인증 처리]: 토큰이 아예 없거나 API 호출 결과로 `401 Unauthorized` 에러가 발생한다면, 당황하지 않고 자연스럽게 '로그인 화면'으로 이동시켜주세요.",
            "[회원가입 흐름]: 회원가입 폼을 다 채우고 [가입하기] 버튼을 누르면 `{api:owner_auth:register}`를 호출합니다. 성공(200) 응답을 받으면 지체 없이 '사업자 인증 서류 제출 화면'으로 넘겨주시면 됩니다.",
            "[로그인 성공 후]: 토큰을 새로 받았다면 다시 `{api:owner_auth:me}`를 호출하여 `verification_status`를 보고, 승인되었으면 대시보드로, 대기 중이면 안내 화면으로 분기해주세요.",
            "[사업자 서류 제출]: 사업자 등록증 사진과 번호를 입력해 제출(또는 재제출)할 때는 `{api:owner_auth:business-verification}` API를 호출하여 처리합니다.",
            "[비밀번호 재설정 완료]: 이메일에서 재설정 링크를 클릭한 사장님이 새 비밀번호를 입력하고 [변경하기] 버튼을 누르면 `{api:owner_auth:confirm}`을 호출합니다. 토큰은 15분 유효, 1회만 사용 가능합니다."
        ],
        "ui_events": [
            ["[버튼] 회원가입", "POST /owner/auth/register", "가입 성공 토스트를 띄우고 사업자 인증 화면으로 즉시 이동시킵니다.", "백엔드에서 VALIDATION_ERROR가 오면 팝업 대신 입력칸 바로 아래에 빨간 텍스트로 에러 내용을 각각 표시해주세요."],
            ["[버튼] 로그인", "POST /owner/auth/login 호출 후 GET /owner/me 연속 호출", "현재 승인 상태(verification_status)를 확인하여 그에 맞는 첫 화면(대시보드 또는 대기 화면)으로 이동시킵니다.", "401 에러 시 '이메일이나 비밀번호를 다시 확인해주세요'라는 친절한 문구를 입력창 근처에 띄웁니다."],
            ["[버튼] 사업자 인증 제출", "POST /owner/business-verification", "화면을 '사업자 승인 대기 중(pending)' 안내 화면으로 부드럽게 전환시킵니다.", "파일 용량 초과나 사업자번호 형식이 틀렸다면 즉각 인라인 에러 텍스트로 고칠 곳을 알려줍니다."],
            ["[버튼] 비밀번호 재설정 요청", "POST /owner/auth/password-reset/request", "성공이든 미가입 이메일이든 보안을 위해 무조건 '재설정 이메일을 보냈습니다'라는 동일한 완료 모달을 띄웁니다.", "네트워크 단절 등 진짜 서버 오류(500)일 때만 공통 에러 모달을 띄워줍니다."],
            ["[버튼] 새 비밀번호 저장", "POST /owner/auth/password-reset/confirm", "비밀번호 변경 성공 시 '비밀번호가 변경되었습니다' 토스트를 띄우고 로그인 화면으로 자동 이동시킵니다.", "토큰이 만료(15분)되었거나 이미 사용된 토큰이면 '링크가 만료되었습니다. 다시 요청해주세요' 안내와 함께 재설정 요청 화면으로 되돌립니다."]
        ],
        "states": [
            "`anonymous`: 로그인 안 된 유저. 로그인과 회원가입 폼만 노출합니다.",
            "`pending`: 가입 직후 승인 대기. 샵 초안은 작성하게 해주되, [공개 전환]이나 [예약 처리] 등 핵심 비즈니스 버튼은 클릭 못 하게 Disabled 처리합니다.",
            "`rejected`: 서류 반려됨. 반려 사유를 눈에 띄게 붉은 박스로 표시하고 [서류 재제출하기] 버튼을 큼직하게 노출해주세요.",
            "`approved`: 심사 통과. 대시보드와 모든 운영 기능 진입을 허용하는 완전한 사장님 상태입니다."
        ],
        "qa": [
            "개발자 도구에서 토큰을 수동으로 삭제하고 `/owner/me` 호출 시, 빈 화면에서 멈추지 않고 '로그인 화면'으로 잘 리다이렉트 되는지 테스트해주세요.",
            "pending 계정으로 억지로 샵 공개 토글을 눌렀을 때, 일반 403 에러가 아닌 `VERIFICATION_REQUIRED` 코드를 잡아서 '사업자 인증이 필요합니다' 모달을 잘 띄우는지 확인해주세요.",
            "rejected 상태에서 서류를 재제출하면 API 성공 직후 즉시 pending 화면으로 레이아웃이 바뀌는지 눈으로 확인해주세요."
        ]
    },
    "2": {
        "api_sequence": [
            "[초기 진입]: 샵 설정 화면에 들어오면 `{api:owner_shop:shop}`을 호출하여 샵 정보를 가져옵니다.",
            "[초안 폼 렌더링]: 아직 샵 데이터가 404로 없으면 빈 입력 폼을 띄워주고, 폼 작성 후 저장할 때 `{api:owner_shop:shop}`으로 생성합니다.",
            "[부분 수정 분리]: 샵 데이터가 이미 있다면, [기본 정보]는 `{api:owner_shop:shop}`, [영업시간]은 `{api:owner_shop:business-hours}` 로 각각 나누어 저장 버튼과 API를 분리해주세요.",
            "[정책 및 결제]: 마찬가지로 [예약 정책] 탭은 `{api:owner_shop:reservation-policy}`, [결제 방식] 탭은 `{api:owner_shop:payment-method}`로 저장 로직을 분리해 관리합니다.",
            "[이미지 관리]: 대표 이미지(thumbnail_url)와 샵 갤러리 이미지(image_urls, 최대 10장)를 수정할 때는 `{api:owner_shop:images}`를 호출합니다. 이미지 파일 자체는 먼저 `{api:uploads:presigned}`로 업로드 URL을 받아 직접 올린 후, 반환된 URL을 이 API에 넘깁니다.",
            "[공개 상태 토글]: 스위치를 눌러 공개/숨김을 바꿀 때는 `{api:owner_shop:visibility}`를 호출합니다. 단, 아직 사업자 승인 전이라면 이 스위치를 회색으로 막아둬야 합니다."
        ],
        "ui_events": [
            ["[버튼] 샵 기본 정보 저장", "PATCH /owner/shop", "화면 하단에 '저장 완료' 토스트를 띄워주고, 입력된 값으로 화면 상태(Context/Store)를 즉시 갱신합니다.", "주소 누락, 전화번호 포맷 등의 에러는 팝업 대신 각 입력칸 하단에 빨간 안내 문구로 콕 집어 표시해주세요."],
            ["[버튼] 영업시간 저장", "PATCH /owner/shop/business-hours", "저장 성공 시 '영업시간이 변경되어 향후 예약 가능 시간이 재계산됩니다'라는 안내 툴팁을 잠깐 띄워주면 좋습니다.", "시간대가 겹치는 등 논리 오류가 발생하면 캘린더/시간 선택기 쪽에 경고를 표시합니다."],
            ["[버튼] 결제 방식 저장", "PATCH /owner/shop/payment-method", "결제 수단 안내 텍스트나 미리보기 화면을 방금 저장한 내용으로 즉각 업데이트해서 보여줍니다.", "계좌이체를 골랐는데 예금주나 계좌번호 입력칸이 비어있으면 저장 버튼 자체를 막거나 누를 때 입력칸을 붉게 깜빡여주세요."],
            ["[토글] 샵 공개 상태", "PATCH /owner/shop/visibility", "성공 시 헤더의 샵 뱃지를 active(초록색) / hidden(회색)으로 즉시 갈아끼워 줍니다.", "승인이 안 끝났는데(`VERIFICATION_REQUIRED`) 누르려 하면 스위치를 원복시키고 '인증 승인이 필요합니다' 모달을 띄워주세요."]
        ],
        "states": [
            "`no_shop` (서버 응답 404): 아직 샵 데이터를 한 번도 안 만든 상태. GET /owner/shop 호출 시 404가 돌아오면 빈 초안 생성 폼을 띄워주세요.",
            "`draft` (서버 값 visibility=draft): 사업자 승인 대기 중(pending)이라도 텍스트 입력과 임시 저장은 가능합니다. 단, 공개 전환 토글은 Disabled 처리해주세요.",
            "`active` (서버 값 visibility=active): 고객 앱에 노출되고 검색과 예약 진입이 가능한 진짜 샵 운영 상태입니다.",
            "`hidden` (서버 값 visibility=hidden): 사장님이 원해서 임시로 숨긴 상태. 사장님 본인은 수정이 가능하지만 고객에겐 보이지 않습니다."
        ],
        "qa": [
            "사업자 승인 전(pending) 계정으로 로그인한 상태에서 샵 정보를 이것저것 적고 저장을 누르면 성공해야 하고, 샵 공개 토글을 누르면 명확히 막히는지 직접 테스트해주세요.",
            "[예약 정책] 탭에서 `자동 수락` 토글을 켠 상태일 때, [결제 방식] 탭으로 이동하면 `계좌이체 안내` 선택 박스가 회색으로 잠겨서 아예 클릭을 못 하게 막혀있는지 확인해주세요.",
            "계좌이체 옵션을 선택했을 때, 나타나는 4가지 하위 입력칸(예약금액, 은행명, 계좌번호, 예금주)을 다 채우기 전까지는 [저장] 버튼이 활성화되지 않는지 프론트 validation을 확인해주세요."
        ]
    },
    "3": {
        "api_sequence": [
            "[목록 진입]: 디자이너 관리 화면에 진입하면 `{api:owner_designer:designers}` API로 소속 디자이너 목록을 쭉 가져와 리스트업합니다.",
            "[추가 및 상세]: 새 디자이너를 만들 때는 `{api:owner_designer:designers}`, 특정 디자이너 카드를 눌러 상세 화면에 들어갈 때는 `{api:owner_designer:designers}`를 호출합니다.",
            "[기본 정보 수정]: 이름, 프로필 이미지 등은 상세 화면 안에서 `{api:owner_designer:designers}`로 즉시 저장합니다.",
            "[스케줄 관리]: 고정된 주간 근무시간을 바꿀 때는 `{api:owner_designer:schedule}`, 연차 등 임시 휴무일을 찍어줄 때는 `{api:owner_designer:time-off}`를 호출합니다.",
            "[비활성화/삭제]: 퇴사하거나 당분간 쉬는 디자이너는 `{api:owner_designer:designers}`로 처리하고 프론트 목록을 갱신합니다."
        ],
        "ui_events": [
            ["[버튼] 새 디자이너 추가", "POST /owner/designers", "저장 후 목록 화면으로 돌아오면 방금 추가된 디자이너 카드가 목록 상단에 새롭게 보이도록 추가해줍니다.", "이름이나 직급 등 필수값이 비어있으면 폼 에러(인라인 붉은 글씨)를 표시합니다."],
            ["[버튼] 근무시간 변경", "PATCH /owner/designers/{designer_id}/schedule", "저장 후 '예약 가능한 슬롯이 새 근무시간에 맞춰 조정되었습니다' 류의 성공 토스트를 띄웁니다.", "시작 시간이 종료 시간보다 늦게 설정되는 등 범위 오류 시 UI 단에서 빨간색 테두리로 피드백을 줍니다."],
            ["[버튼] 임시 휴무(Time-off) 등록", "POST /owner/designers/{designer_id}/time-off", "성공하면 사장님 스케줄러 캘린더에 해당 날짜 전체를 회색(휴무) 블록으로 덮어 칠해줍니다.", "해당 날짜에 이미 확정된 예약이 존재해서 백엔드가 충돌(CONFLICT)을 뱉으면, '이미 예약된 고객이 있습니다. 예약을 먼저 취소해주세요' 모달을 띄웁니다."],
            ["[버튼] 디자이너 비활성화", "DELETE /owner/designers/{designer_id}", "해당 디자이너를 신규 예약 배정 후보자 리스트에서 즉시 제거(필터링)합니다.", "기존에 이미 이 디자이너에게 예약된 건들이 있다면, 예약 상세 뷰에서 이름 옆에 '(비활성)' 딱지를 붙여 사장님이 헷갈리지 않게 합니다."]
        ],
        "states": [
            "`active`: 정상적으로 일하고 있는 디자이너. 유저 앱에서 예약을 잡을 때 담당자 후보로 노출됩니다.",
            "`inactive`: 퇴사나 장기 휴가로 비활성화된 디자이너. 과거 예약 기록엔 남아있지만, 앞으로의 신규 예약 후보에서는 쏙 빠져야 합니다.",
            "`empty`: 아직 등록된 디자이너가 한 명도 없는 상태. 빈 깡통 화면 대신 귀여운 일러스트와 함께 [첫 디자이너를 등록해보세요!] 같은 유도 버튼을 정중앙에 띄워주세요."
        ],
        "qa": [
            "디자이너가 0명인 초기 상태일 때, 화면이 텅 비어있지 않고 빈 상태(Empty State) 디자인과 추가 버튼이 예쁘게 나오는지 확인해주세요.",
            "방금 비활성화 처리한 디자이너가 예약 등록 시 담당자 선택 드롭다운 목록에서 감쪽같이 사라졌는지 프론트에서 꼼꼼히 확인해주세요.",
            "디자이너의 임시 휴무를 등록한 날짜를 클릭했을 때, '신규 예약 추가' 버튼이 프론트에서 제대로 잠겨있는지 확인해주세요."
        ]
    },
    "4": {
        "api_sequence": [
            "[목록 진입]: 디자인(손톱 포트폴리오) 목록 화면 진입 시 `{api:owner_design:designs}`를 호출합니다. 필터링을 위해 visibility와 ai_analysis_status 쿼리를 활용할 수 있습니다.",
            "[신규 등록]: 디자인 폼에 이미지(1~5장)와 가격, 설명 등을 채우고 [저장]을 누르면 프론트에서 유효성 검사 후 `{api:owner_design:designs}`를 쏩니다.",
            "[상세 및 폴링]: 디자인 카드를 누르면 `{api:owner_design:designs}`를 호출하여 가장 최신의 AI 분석 상태(status)와 결과값을 화면에 뿌려줍니다.",
            "[수정 처리]: 제목이나 가격, 태그 등을 수정하고 저장할 때는 `{api:owner_design:designs}`를 호출합니다.",
            "[사진 교체 시 주의]: 사진을 추가(`POST .../images`)하거나 지울(`DELETE .../images/{id}`) 경우, 백엔드에서 AI 분석 상태를 다시 pending으로 돌려버리므로 화면에서도 뱃지를 즉시 '분석 중 ⏳'으로 덮어씌워야 합니다.",
            "[수동 재분석]: AI가 너무 이상하게 분석했거나 failed 떴을 때 누르는 재분석 버튼은 `{api:owner_design:reanalyze}`를 호출합니다."
        ],
        "ui_events": [
            ["[버튼] 새 디자인 등록", "POST /owner/designs", "등록 성공 토스트와 함께 목록 맨 위로 올려주고, 상태 뱃지는 무조건 'AI 분석 중'으로 달아줍니다.", "가장 흔한 에러인 필수값 누락이나 이미지 0장 업로드 시도는 API를 쏘기 전에 프론트에서 막고 폼 에러를 띄워주세요."],
            ["[버튼] 사진 추가/수정", "POST /owner/designs/{design_id}/images", "새 이미지가 렌더링되면서 동시에 디자인 전체의 뱃지를 '분석 중'으로 강제 전환시켜야 합니다.", "6장째 이미지를 올리려고 하면 파일 브라우저 창을 띄우지 말고 '최대 5장까지만 가능해요' 툴팁을 보여줍니다."],
            ["[버튼] AI 결과 수동 재분석", "POST /owner/designs/{design_id}/reanalyze", "버튼 클릭 즉시 화면 전체 또는 해당 카드를 로딩 스피너/분석 중 배지로 바꿔서 '작업이 들어갔다'는 피드백을 확실히 줍니다.", "수동 재분석이 허용되지 않는 상태(이미 분석 중 등)일 때 프론트에서 버튼을 흐리게(Disabled) 처리했는지 확인하세요."],
            ["[토글] 고객 노출 상태 변경", "PATCH /owner/designs/{design_id}/visibility", "성공하면 스위치가 초록색(ON)으로 바뀌고 리스트 뱃지도 active 갱신됩니다.", "아직 AI 분석이 덜 끝났거나(pending), 사장님 사업자 승인이 안 났다면 토글이 켜지지 않게 프론트에서 막아주세요."]
        ],
        "states": [
            "`pending/in_progress`: 방금 사진을 올려서 서버 뒤에서 AI(LLM)가 열심히 깎고 태그를 다는 중인 상태입니다. 고객 앱에선 검색되지 않습니다.",
            "`done + active`: AI 분석도 무사히 끝나고, 사장님도 '공개' 토글을 켠 완벽한 영업 상태입니다. 고객이 볼 수 있습니다.",
            "`failed`: 사진 화질구지 등의 이유로 AI 분석이 실패해 멈춰버린 붉은색 상태입니다. 사장님께 '사진을 교체하거나 재분석 버튼을 눌러주세요'라는 가이드를 띄워야 합니다.",
            "`hidden`: 사장님이 자발적으로 공개를 끈 상태입니다. 포트폴리오 관리용으로 본인 눈에만 보입니다."
        ],
        "qa": [
            "디자인 등록 폼에서 사진을 아예 안 올리거나, 6장을 꽉 채워 올리려 할 때 백엔드 에러 전에 프론트엔드가 자체적으로 에러 메시지와 함께 막는지 테스트해주세요.",
            "새로 디자인을 등록하자마자 리스트로 돌아왔을 때, '공개' 토글이 아직 켜지지 않도록 잘 막아뒀는지 눈으로 확인해주세요 (분석이 안 끝났으므로).",
            "일부러 이상한 사진을 올려 AI 분석이 `failed` 상태가 되었을 때, 화면에 빨간 경고창과 함께 [재분석하기] 버튼이 나타나는지 확인해주세요."
        ]
    },
    "5": {
        "api_sequence": [
            "[예약 목록 진입]: 예약 캘린더나 리스트에 들어올 때 `GET /owner/reservations?from=날짜&to=날짜&status=상태` 쿼리를 잘 조합해서 호출해 화면을 그립니다.",
            "[최신화 조회]: 특정 예약 카드를 눌러 팝업/모달 상세를 띄울 때는 방금 전 상태가 바뀌었을지 모르니 `{api:owner_reservation:reservations}` 단건 조회를 한 번 더 날려 최신화합니다.",
            "[사장님의 응답]: 새 요청(pending)에 대해 [수락] 버튼은 `{api:owner_reservation:accept}`, [거절] 버튼은 `{api:owner_reservation:reject}`를 쏩니다.",
            "[계좌이체 확인]: 계좌이체 정책인 샵에서, 사장님이 유저의 입금 내역을 통장에서 직접 보고 누르는 [입금 확인 완료] 버튼은 `{api:owner_reservation:payment-confirmed}`입니다.",
            "[시술 종료 후]: 유저가 시술을 받고 가면 `complete`, 안 나타나면 `no-show`, 예약이 취소되면 `cancel` API를 각각 날린 후 캘린더를 새로고침(refetch) 합니다."
        ],
        "ui_events": [
            ["[버튼] 예약 수락", "POST /owner/reservations/{id}/accept", "현장결제 샵이면 확정(confirmed) 녹색 뱃지로, 계좌이체 샵이면 입금대기(payment_pending) 주황색 뱃지로 변신시킵니다.", "그 사이 다른 고객이 낚아채서 CONFLICT가 나면 '앗, 이미 선점된 시간입니다' 모달을 띄워 상황을 알려줍니다."],
            ["[버튼] 입금 내역 확인 완료", "POST /owner/reservations/{id}/payment-confirmed", "입금 대기 딱지를 떼고 확정(confirmed) 뱃지로 바꾸며, 캘린더 해당 슬롯에 확정 디자인을 예쁘게 박아줍니다.", "혹시 그 사이 유저가 취소해서 409 에러가 나면 '취소된 예약입니다' 하고 화면을 새로고침시킵니다."],
            ["[버튼] 예약 거절", "POST /owner/reservations/{id}/reject", "목록에서 거절됨(rejected) 상태로 색상을 죽이거나, 필터 설정에 따라 아예 리스트에서 부드럽게 사라지게(애니메이션) 처리합니다.", "거절 사유 입력이 필수인데 사장님이 빈칸으로 냈다면, 텍스트 상자 주변을 붉게 흔들어주세요(Shake effect)."],
            ["[버튼] 노쇼(No-show) 처리", "POST /owner/reservations/{id}/no-show", "해당 예약을 붉은색 노쇼 배지로 덮고 더 이상 변경할 수 없게 만듭니다.", "정책상 예약 시작 시간 30분 전까지는 노쇼 버튼이 프론트엔드에서 회색(Disabled)으로 굳게 잠겨 있어야 합니다."],
            ["[버튼] 시술 완료 처리", "POST /owner/reservations/{id}/complete", "확정(confirmed) 예약의 시술이 끝나면 이 버튼을 눌러 상태를 completed로 변경합니다. 완료 후에는 유저가 리뷰를 작성할 수 있게 됩니다.", "이미 completed/cancelled/no_show 상태인 예약에서 이 버튼을 누르면 409 에러가 뜹니다. 프론트에서 confirmed 상태일 때만 버튼을 노출해주세요."],
            ["[버튼] 샵 사정 예약 취소", "POST /owner/reservations/{id}/cancel", "사장님 측 사정으로 예약을 취소합니다. 취소 사유(reason)는 필수 텍스트 입력이며, 유저에게 알림과 함께 사유가 전달됩니다.", "취소 사유 입력칸이 비어있으면 버튼을 비활성화하거나 '취소 사유를 입력해주세요' 인라인 에러를 표시해주세요. 이미 종료된 예약(completed/no_show)에서는 409 에러가 반환됩니다."]
        ],
        "states": [
            "`pending`: 사장님의 수락/거절을 목빠지게 기다리는 신규 요청. 미처리 요청은 무조건 `created_at` 오름차순(먼저 온 사람 먼저)으로 보여주세요.",
            "`payment_pending`: 사장님은 수락했는데, 유저의 입금을 기다리는 상태. 또는 유저가 '입금했어요' 버튼을 눌러서 사장님이 통장을 뜯어봐야 하는 상태입니다.",
            "`confirmed`: 입금까지 다 끝나고 완벽히 캘린더 슬롯을 점유한 예약 확정 상태입니다. 시술 날짜가 다가오길 기다립니다.",
            "`completed` / `no_show` / `rejected`: 이미 끝난 옛날 예약들입니다. 아무 버튼도 누를 수 없는 완전한 읽기 전용 뷰로 그려주세요.",
            "`cancelled_by_user` / `cancelled_by_shop`: 누가 취소했는지 명확히 보여주는 취소 상태. 샵이 취소했다면 사장님이 썼던 취소 사유(cancel_reason)를 꼭 화면 어딘가에 보여주세요."
        ],
        "qa": [
            "예약 관리 대시보드의 '신규 요청' 목록이 예약이 들어온 순서(생성된 시간순)대로 최상단부터 차곡차곡 쌓여서 잘 보이는지 확인해주세요.",
            "계좌이체 샵 예약에서 유저가 앱에서 [입금 완료]를 눌렀더라도, 사장님 화면에 아직 [입금 내역 확인 완료] 버튼이 떡하니 살아있고 확정 상태가 아닌지 교차 검증해주세요.",
            "동일한 시간에 겹치는 2개의 pending 예약 중 하나를 수락했을 때, 나머지 하나를 수락하려 하면 에러 팝업(CONFLICT)이 제대로 뜨며 막히는지 테스트하세요.",
            "확정된(confirmed) 예약 상세 화면에서, 시술 시간이 아직 30분도 안 지났는데 실수로 [노쇼 처리] 버튼을 누르지 못하도록 프론트에서 버튼을 비활성화해두었는지 확인해주세요."
        ]
    },
    "6": {
        "api_sequence": [
            "[리뷰 목록 진입]: 리뷰 화면에 처음 들어오면 `{api:review:reviews}`에 sort, unanswered, cursor 등의 필터 쿼리 파라미터를 말아서 호출합니다.",
            "[미답변 필터 연동]: 대시보드에서 '미답변 리뷰 3건' 카드를 콕 찍어서 넘어온 경우엔 프론트 라우터가 똑똑하게 `unanswered=true` 쿼리를 물고 들어오게 렌더링해야 합니다.",
            "[답변 달기]: 사장님이 정성껏 쓴 답변을 저장할 때는 `{api:review:reply}`, 오타를 고칠 때는 `{api:review:reply}`, 지울 때는 `{api:review:reply}`를 호출합니다.",
            "[상태 갱신]: 답변 관련 API(POST/PATCH/DELETE)를 쏘고 나면 해당 리뷰 카드 하나만 로컬 상태를 바꾸거나, 리스트 전체를 가볍게 refetch 해서 화면 싱크를 맞춥니다."
        ],
        "ui_events": [
            ["[버튼] 리뷰 답변 남기기", "POST /reviews/{id}/reply", "저장에 성공하면 입력창이 텍스트로 굳어지고, 리뷰 카드에 붙어있던 '미답변' 주황색 뱃지가 깔끔하게 사라집니다.", "혹시 네트워크 문제 등으로 중복 클릭되어 이미 답변이 존재하면(409), 자동으로 [수정] 모드 창으로 화면을 탈바꿈시켜줍니다."],
            ["[버튼] 답변 수정하기", "PATCH /reviews/{id}/reply", "수정 폼이 닫히면서 방금 고친 새 텍스트가 부드럽게 화면에 교체되어 렌더링됩니다.", "403 권한 에러가 뜬다면 '사장님 샵의 리뷰가 아닙니다'라는 다소 무서운 토스트를 띄웁니다."],
            ["[버튼] 답변 삭제하기", "DELETE /reviews/{id}/reply", "텍스트가 날아가고, 다시 입력 폼과 '미답변' 뱃지가 살포시 돌아오는 상태로 뷰를 되돌립니다.", "진짜 지울 건지 묻는 자그마한 확인 모달 팝업을 꼭 제공해주세요. (실수 방지)"],
            ["[필터] 정렬 기준 변경", "GET /owner/reviews", "별점순/최신순 탭을 누르면 기존 리스트 데이터를 비우고 스피너를 돈 다음 새 리스트를 착 뿌려줍니다.", "검색 결과가 0건이라면 허전하지 않게 '아직 이 조건에 맞는 리뷰가 없어요' 류의 일러스트 빈 화면을 보여줍니다."]
        ],
        "states": [
            "`unanswered`: 사장님의 댓글을 기다리는 미답변 리뷰. 가장 눈에 띄게 주황색 배지 같은 걸 붙여주고 큼직한 [답변 작성] 버튼을 노출합니다.",
            "`answered`: 사장님이 이미 답글(`shop_reply`)을 달아준 리뷰. 답글 내용 밑에 작게 회색 글씨로 [수정] / [삭제] 텍스트 버튼만 붙여줍니다.",
            "`empty`: 리뷰가 한 개도 없거나, '미답변' 탭을 눌렀는데 다 답변해서 텅 빈 경우. 사장님께 뿌듯함을 주는 빈 상태(Empty State) 화면을 보여주세요."
        ],
        "qa": [
            "사장님이 한 리뷰에 답글을 두 번 달려고 광클했을 때 프론트가 버튼을 잠그거나, 서버가 튕겨냈을 때 알아서 에러 처리가 잘 되는지 확인해주세요.",
            "[미답변 리뷰 모아보기] 탭에서 특정 리뷰에 답변을 쾅 달면, 그 즉시 그 리뷰 카드가 스르륵 리스트에서 사라지는 애니메이션(또는 렌더링 제외)이 잘 작동하는지 확인하세요.",
            "별점순 등 정렬 탭을 눌러 API를 다시 호출할 때 무한 스크롤용 `cursor` 변수를 깔끔하게 초기화(reset)해서 1페이지부터 다시 잘 불러오는지 체크해주세요."
        ]
    },
    "7": {
        "api_sequence": [
            "[목록 진입]: 스네일 탭(커뮤니티)을 누르면 `GET /owner/snaps?cursor=` 무한 스크롤 API를 불러 우리 샵이 태그된 사진들만 구경합니다.",
            "[상세 조회]: 썸네일을 눌러 팝업/페이지로 들어가면 `{api:snap:snaps}`로 본문과 최신 좋아요 수 등을 가져옵니다.",
            "[댓글 로딩]: 상세 화면 하단에서 `{api:comment_like_follow:comments}`를 불러와 유저들의 반응을 주욱 나열해줍니다.",
            "[샵 댓글 처리]: 사장님이 샵 이름으로 댓글을 달거나 고치거나 지울 때는 기존 유저용 댓글 API(POST/PATCH/DELETE comments)를 그대로 재사용해 날리면 됩니다."
        ],
        "ui_events": [
            ["[행동] 스네일 상세 팝업 열기", "GET /snaps/{id}", "이미지 캐러셀, 본문 캡션, 샵/디자이너 태그 칩스, 그리고 댓글 영역을 한 화면에 예쁘게 펼쳐줍니다.", "혹시 그 사이 작성자가 글을 날려버려서 404가 뜬다면 팝업을 닫고 목록에서도 그 사진을 스윽 빼줍니다."],
            ["[버튼] 샵 공식 댓글 작성", "POST /snaps/{id}/comments", "댓글이 등록되면 리스트 최하단(혹은 상단 정렬에 맞춰)에 방금 쓴 댓글을 끼워넣어 줍니다. 이때 이름 옆에 예쁜 '샵 공식' 뱃지를 박아줍니다.", "빈 텍스트나 띄어쓰기만 입력하고 전송 버튼을 누르려 하면 버튼을 무시하거나 Disabled 처리해서 텅 빈 댓글을 막아주세요."],
            ["[버튼] 댓글 수정", "PATCH /comments/{id}", "수정 모드 입력창이 닫히며 고친 텍스트로 바로 업데이트합니다.", "사장님이 쓰지 않은 남의 댓글에는 애초에 이 수정/삭제 톱니바퀴 버튼이 렌더링되지 않도록 뷰를 잘 숨겨주세요."],
            ["[버튼] 댓글 삭제", "DELETE /comments/{id}", "해당 댓글 박스를 돔(DOM)에서 날려버리고 전체 댓글 카운트 숫자도 1 빼줍니다.", "실수로 지우지 않게 '정말 삭제할까요?'라는 네이티브 `confirm()`이나 커스텀 모달을 띄워줍니다."]
        ],
        "states": [
            "`tagged_snap`: 리스트에 뜨는 모든 게시물은 내 샵(shop_id)이 태그(tagged_shop_id)된 고마운 홍보물입니다. 디자인 시 사진을 큼직하게 살려주세요.",
            "`shop_comment`: 일반 유저 댓글과 사장님이 단 댓글(`author_type=shop`)을 시각적으로 확 구분 지어 줘야 합니다. 사장님 프로필 테두리 색상을 다르게 하거나 특별한 왕관 뱃지를 달아주세요.",
            "`empty`: 아직 우리 샵을 태그해준 유저가 없어서 텅 빈 상태. 사장님이 우울해하지 않게 귀여운 안내 문구와 이미지를 넣어주세요."
        ],
        "qa": [
            "사장님 스네일 탭에 진입했을 때, 정말로 우리 샵이 태그된 게시물들만 정확하게 필터링되어 리스트에 올라오는지 테스트 데이터로 확인해주세요.",
            "사장님 계정으로 남긴 댓글을 렌더링할 때, 일반 유저들이 쓴 댓글들과 UI적으로 명확히 구분되는 '샵 공식 마크'가 잘 그려지는지 확인해주세요.",
            "남이 쓴 일반 댓글 영역을 호버(Hover)하거나 클릭했을 때, 실수로라도 수정/삭제 액션 버튼 뭉치가 보이지 않게 프론트 코드로 단단히 숨겼는지 체크해주세요."
        ]
    },
    "8": {
        "api_sequence": [
            "[대시보드 진입]: 홈 화면(대시보드)에 뜨면 복잡하게 여러 API 부를 것 없이 쿨하게 `{api:owner_dashboard:summary}` 단일 API 하나만 쏴서 숫자 4개를 다 받아옵니다.",
            "[카드 라우팅]: 사장님이 4개의 지표 카드 중 하나를 누르면, 프론트엔드 라우터(Router)가 해당 페이지 경로로 이동시키면서 필수적인 필터 조건(Query params)을 뒤에 꼬리표처럼 달아줍니다.",
            "[예시]: '새 예약 요청 3건' 카드를 눌렀다면 라우터는 `/reservations?status=pending` 경로로 푸시하고, '미답변 리뷰' 카드는 `/reviews?unanswered=true`로 쏴줍니다."
        ],
        "ui_events": [
            ["[카드 클릭] 오늘 예약 O건", "화면 라우팅 이동", "예약 관리 달력 화면으로 넘어가면서, 달력이 오늘 날짜로 포커싱되고 오늘 스케줄 리스트가 쫙 펼쳐집니다.", "오늘 건이 0건이면 예약 화면 자체에서 빈 상태 UI를 잘 보여주면 됩니다."],
            ["[카드 클릭] 신규 예약 요청 O건", "화면 라우팅 이동", "예약 화면으로 넘어가면서 상단 필터가 '수락 대기(pending)' 상태로 탁 눌려있게 세팅합니다.", "브라우저 뒤로 가기나 새로고침을 해도 URL에 `status=pending`이 남아있어서 필터가 안 풀리는지 유심히 체크하세요."],
            ["[카드 클릭] 미답변 리뷰 O건", "화면 라우팅 이동", "리뷰 관리 화면으로 넘어가면서 탭이 '미답변'으로 맞춰져 있도록 렌더링합니다.", "거기서 답변을 달고 다시 대시보드로 돌아왔을 때, 숫자 카운트가 즉시 깎여서 갱신되어 있는지 캐시 무효화를 신경 써주세요."],
            ["[카드 클릭] 최근 스네일 태그", "화면 라우팅 이동", "내 샵이 태그된 스네일 탭으로 쓱 넘겨줍니다.", "목록에 진짜 태그가 0개면 스네일 탭 안에서 빈 화면 안내를 보여줍니다."]
        ],
        "states": [
            "`loading`: 대시보드 API를 쏴서 숫자 4개를 기다리는 찰나의 순간. 뼈대만 있는 스켈레톤(Skeleton) UI나 펄스(Pulse) 애니메이션으로 카드를 예쁘게 흔들어주세요.",
            "`loaded`: API가 도착해서 카운트 숫자가 딱 박힌 듬직한 화면. 카드가 클릭 가능해집니다.",
            "`empty_zero`: 0이라는 숫자도 비정상이 아니라 당당한 데이터입니다. 에러처럼 보이지 않게 깔끔하게 '0건'이라고 그려주세요."
        ],
        "qa": [
            "네트워크 탭을 열어서, 대시보드 화면 렌더링을 위해 정말로 `/owner/dashboard/summary` API 단 하나만 아주 가볍게 호출하고 끝나는지 확인해주세요.",
            "카드별로 클릭해서 넘어간 다음 화면(예약, 리뷰 등)에 진입했을 때, 사장님이 기대했던 대로 필터(수락 대기, 미답변 등)가 자동으로 착 켜져 있는지 직접 눌러가며 테스트하세요.",
            "카드 클릭해서 넘어갔다가 브라우저 F5(새로고침) 버튼을 빡 눌렀을 때, 필터 상태가 멍청하게 리셋되지 않고 URL 상태를 읽어서 끈질기게 필터를 유지하는지 꼼꼼히 점검해주세요.",
            "인터넷이 끊겼거나 백엔드 서버가 잠시 죽어서 API가 실패했을 때, 대시보드가 하얗게 터지지 않고 카드 안에 얌전하게 '데이터를 불러오지 못했습니다' 아이콘이 그려지는지 방어 코드(Error Boundary)를 체크하세요."
        ]
    },
    "9": {
        "api_sequence": [
            "[알림 팝오버 열기]: 우측 상단 종모양을 눌러 알림함을 열 때 무한 스크롤용 `GET /owner/notifications?cursor=` API를 호출해서 리스트를 깔아줍니다.",
            "[빨간 뱃지 갱신]: 화면 상단 종 아이콘 위 붉은 숫자 뱃지는 주기적으로 `{api:owner_notification:unread-count}`를 찔러서 안 읽은 갯수만 가볍게 그려냅니다.",
            "[알림 클릭 이벤트]: 개별 알림을 톡 누르면 제일 먼저 `{api:owner_notification:read}`를 눈썹 휘날리게 쏴서 읽음 처리를 시킨 후, 알림 객체에 담겨있던 `deeplink_target` URL 주소로 사장님을 텔레포트 시켜줍니다.",
            "[모두 읽음 빗자루질]: '모두 읽음' 텍스트 버튼을 누르면 `{api:owner_notification:read-all}` API를 쏘고, 성공하자마자 뱃지 숫자를 0으로 확 날려버립니다."
        ],
        "ui_events": [
            ["[리스트 클릭] 알림 항목 선택", "PATCH /owner/notifications/{id}/read API 직후 라우팅", "알림 백그라운드 색이 '안 읽음(푸르스름)'에서 '읽음(흰색)'으로 슥 바뀌고, 해당 예약/리뷰 상세 페이지로 바로 넘어갑니다.", "만약 deeplink_target이 빈 값이거나 갈 곳이 애매한 알림이라면 어디 안 넘어가고 그냥 읽음 처리 색깔만 바꿔주세요."],
            ["[버튼] 모두 읽음", "POST /owner/notifications/read-all", "리스트에 있는 모든 알림의 배경색을 읽음(흰색)으로 싹 바꾸고, 종 아이콘 위 숫자 뱃지를 떼버립니다.", "통신이 실패하면 '앗, 다 못 읽었어요' 류의 재시도 토스트를 띄우고 숫자 뱃지를 원복시켜줍니다."],
            ["[스크롤 하단] 더 보기", "GET /owner/notifications", "스크롤이 바닥에 닿으면 다음 페이지 분량의 알림들을 리스트 맨 아래에 자연스럽게 이어 붙여줍니다(append).", "백엔드가 `has_next=false`를 주면 스피너를 없애고 더이상 API 헛발질을 하지 못하게 꽉 막아주세요."]
        ],
        "states": [
            "`unread`: 사장님이 아직 안 읽은 신선한 알림. 배경색을 옅은 파란색이나 회색으로 칠해주고, 종 모양에는 뱃지 카운트를 달아 유혹합니다.",
            "`read`: 이미 읽어서 볼일 끝난 알림. 배경은 평범한 흰색으로 두고 글자 색상도 살짝 죽여줍니다(Dimmed).",
            "`empty`: 알림이 태초부터 한 개도 없거나 필터를 잘못 먹인 상태. '아직 도착한 알림이 없어요' 일러스트를 귀엽게 박아줍니다."
        ],
        "qa": [
            "시퍼런 '안 읽은 알림'을 하나 클릭했을 때, 상세 화면으로 넘어감과 동시에 우측 상단 뱃지 숫자가 -1 줄어드는지 실시간 동기화를 유심히 관찰해주세요.",
            "예약 취소 알림을 눌렀을 땐 '예약 상세 모달'로, 리뷰 알림을 눌렀을 땐 '해당 리뷰 카드'로 `deeplink_target`을 타고 쏙쏙 정확히 랜딩(텔레포트) 하는지 여러 케이스를 찔러보세요.",
            "[모두 읽음]을 누르고 나서 F5(새로고침)를 빡 때려도, 여전히 종 아이콘 위에 빨간 뱃지가 안 생기고 얌전히 0인 상태를 유지하는지 끈질기게 테스트해주세요."
        ]
    },
    "10": {
        "api_sequence": [
            "[사전 합의 확인]: 프론트 코딩을 빡세게 시작하기 전에, 명세서 하단의 `spec_text/14_decisions.md`(의사결정)와 `15_checklist.md`(남은 할일)를 쓱 훑어봅니다.",
            "[기획 핑퐁]: 미정 항목(예: 예약 취소 패널티 금액 등)이 프론트 UI 로직에 지대한 영향을 미칠 것 같으면, 내 맘대로 if문 짜지 말고 기획자나 백엔드 담당자 슬랙으로 핑을 쳐서 결정을 독촉하세요.",
            "[문서 재생성]: 핑퐁이 끝나서 백엔드가 정책을 확정하고 파이썬 스크립트를 한 바퀴 돌리면(`build_all_collaboration_outputs.py`), 여러분이 보고 계신 이 HTML 문서와 AI 프롬프트용 텍스트가 마법처럼 촤라락 최신본으로 업데이트됩니다."
        ],
        "ui_events": [
            ["[액션] 미정 정책 발견", "API 호출 금지", "이 부분은 일단 TODO 주석으로 비워두거나 더미 컴포넌트로 대충 자리만 잡아둡니다.", "자체적으로 하드코딩해서 '3번 지각하면 강퇴' 같은 상상 로직을 박아두지 마세요. 나중에 치우기 힘듭니다."],
            ["[액션] 결정 사항 UI 반영", "최신 API 명세 적용", "새로 뽑힌 HTML이나 AI 요약본(`ai.txt`)을 커서(Cursor)나 코파일럿에 통째로 먹여서 짜달라고 합니다.", "백엔드가 노션(Notion)에 올려둔 공유 링크의 문서 버전이 최신 날짜로 바뀌었는지 꼭 확인하고 작업에 들어가세요."]
        ],
        "states": [
            "`open`: 기획팀도 백엔드도 아직 머리 싸매고 고민 중인 상태. 프론트는 이 부분 건드리지 말고 딴 거 먼저 만드세요.",
            "`decided`: 드디어 결판이 나서 수치가 문서에 박힌 상태. 이제 프론트 구현 페달을 밟아도 좋습니다.",
            "`changed`: 엎어진 정책. 기존에 이미 프론트 UI로 짜둔 게 있다면 그 컴포넌트 뜯어고쳐야 하니 영향도를 먼저 파악하세요."
        ],
        "qa": [
            "우리 프론트엔드 소스코드 전역 검색을 돌렸을 때, 미정이었던 정책 수치(예: 7일 전 100% 환불 등)가 하드코딩 상수(const)로 억지로 박혀있는 곳이 없는지 매의 눈으로 확인해주세요.",
            "기획자가 정책을 슥 바꿨다고 했을 때, 냅다 코드부터 치지 말고 관련된 팝업 문구, 확인 버튼 상태, API Payload 모양새까지 패키지로 잘 바뀌었는지 흐름 전체를 챙겨주세요.",
            "우리가 보고 있는 이 HTML 문서와 AI 요약본 파일의 생성 시각(우측 상단 메타데이터)이 최신 날짜로 잘 찍혀있는지 한 번만 확인하고 코딩을 시작합시다."
        ]
    }
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
            # common_api_rules.image_upload.api 특수 처리
            upload_api = block.get("common_api_rules", {}).get("image_upload", {}).get("api")
            if upload_api:
                data["apis"].setdefault("uploads", {"items": {}, "source_file": rel})
                for row in upload_api:
                    if len(row) < 2:
                        continue
                    endpoint = row[0]
                    purpose = row[1] if len(row) > 1 else ""
                    params = row[2] if len(row) > 2 else ""
                    data["apis"]["uploads"]["items"][endpoint] = {
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


def resolve_mapping(mapping, backend, front_sections, annotations=None):
    annotations = annotations or {}
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
        entity_notes = annotations.get(entity, {})
        for field in fields:
            field_data = entity_data["fields"].get(field)
            if not field_data:
                missing_refs.append(f"field:{entity}.{field}")
                continue
            field_refs.append({
                **field_data,
                "entity": entity,
                "href": link_for_source(field_data["source_file"], field_data["line"]),
                "team_note": entity_notes.get(field, ""),
            })

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

    # 템플릿 참조 해석: {api:group:keyword} 등을 실제 값으로 치환
    raw_guides = IMPLEMENTATION_GUIDES.get(mapping["id"], [])
    raw_playbook = SCREEN_PLAYBOOKS.get(mapping["id"], {})

    from spec_ref import resolve_refs_in_playbooks, resolve_refs_in_guides, resolve_all_refs
    resolved_guides = resolve_refs_in_guides({mapping["id"]: raw_guides}, backend)[mapping["id"]]
    resolved_playbook_map = resolve_refs_in_playbooks({mapping["id"]: raw_playbook}, backend)
    resolved_playbook = resolved_playbook_map[mapping["id"]]

    # checkpoints 등 mapping 내 텍스트 필드도 해석
    resolved_checkpoints = []
    for cp in mapping.get("checkpoints", []):
        resolved_checkpoints.append(resolve_all_refs(cp, backend))

    result = {
        **mapping,
        "checkpoints": resolved_checkpoints,
        "implementation_guides": resolved_guides,
        "playbook": resolved_playbook,
        "front_refs": resolved_sections,
        "field_refs": field_refs,
        "api_refs": api_refs,
        "missing_front_sections": missing_front_sections,
        "missing_refs": missing_refs,
        "coverage": round(coverage, 3),
        "status": "needs_attention" if missing_refs or missing_front_sections or coverage < 1 else "connected",
    }
    return result


def clip_text(value, limit=160):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _build_preamble_lines():
    """공통 원칙 + 에러 처리 패턴 + 상태 매핑 (섹션별 복사 시에도 항상 포함)."""
    return [
        "# AI 작업용 요약: 사장님 웹앱 ↔ 백엔드",
        "",
        "이 텍스트는 HTML 전체를 AI 코딩 도구에 붙여넣는 대신 사용할 압축 컨텍스트입니다.",
        "목표: 사장님 웹앱 프론트 구현자가 백엔드 API/필드/상태 규칙을 빠르게 이해하고, 없는 API나 임의 필드를 만들지 않게 합니다.",
        "",
        "공통 원칙:",
        "- 백엔드 원본은 spec_text/*.md이고, 이 요약은 그 원본을 화면 구현 관점으로 압축한 것입니다.",
        "- API endpoint와 필드명은 아래 목록을 우선 사용합니다. 목록에 없는 값이 필요하면 백엔드 담당자에게 확인합니다.",
        "- 에러 처리는 아래 '공통 에러 처리 패턴'을 참고합니다.",
        "- 사장님 사업자 인증 전에는 초안 작성은 허용하지만 공개 전환과 예약 운영 처리는 막습니다.",
        "- 날짜/시간은 서버 UTC 저장, 화면은 샵 로컬 시간대로 표시합니다.",
        "- 리스트는 cursor 기반 페이지네이션(limit 20 기본, 50 최대)을 기본으로 가정합니다.",
        "",
        "공통 에러 처리 패턴 (모든 API 호출 후 response.ok가 아니면 아래 순서로 처리):",
        "- 401 UNAUTHORIZED → 토큰 만료. refresh token으로 재발급 시도 → 실패 시 로그인 화면으로 이동.",
        "- 403 FORBIDDEN → \"이 작업에 대한 권한이 없습니다\" 토스트 표시.",
        "- 403 VERIFICATION_REQUIRED → \"사업자 인증을 먼저 완료해주세요\" 모달 + 인증 화면 이동 버튼. FORBIDDEN과 반드시 구분 처리.",
        "- 404 NOT_FOUND → \"요청한 정보를 찾을 수 없습니다\" 표시 + 목록으로 이동.",
        "- 409 CONFLICT → \"다른 사용자가 이미 처리했습니다. 새로고침해주세요\" 안내 + 자동 재조회.",
        "- 422 VALIDATION_ERROR → error.field_errors를 순회하며 해당 입력칸 아래에 에러 메시지 인라인 표시.",
        "- 429 RATE_LIMITED → \"잠시 후 다시 시도해주세요\" 토스트 + 버튼 비활성화 3초.",
        "- 500 INTERNAL_ERROR → \"일시적인 오류입니다. 잠시 후 다시 시도해주세요\" 토스트.",
        "",
        "핵심 상태 규칙:",
        "- MVP는 1사장님=1샵 단수 구조입니다. 사장님 웹에서는 /owner/shop, /owner/designs, /owner/designers 계열을 우선 사용합니다.",
        "- pending 예약은 슬롯을 완전히 잠그는 상태가 아닙니다. 사장님 수락 시점에 충돌을 다시 확인합니다.",
        "- 계좌이체 예약은 pending -> payment_pending -> confirmed 흐름입니다. 유저의 [입금 완료]만으로 확정되지 않고 사장님 [입금 확인됨]이 필요합니다.",
        "- 디자인 이미지는 1~5장입니다. 이미지 변경 시 AI 분석을 다시 시작합니다.",
        "- 사용자 노출 조건은 owner 승인 + shop active + design active + ai_analysis_status=done 조합입니다.",
        "",
        "예약 상태별 사장님 웹 버튼 매핑:",
        "- pending → 수락(accept), 거절(reject). 유저도 취소 가능.",
        "- payment_pending → 입금 확인(payment-confirmed), 샵 취소(cancel). 유저도 입금 완료 알림 가능.",
        "- confirmed → 완료(complete), 노쇼(no-show, 시작 30분 후부터), 샵 취소(cancel). 유저도 취소 가능.",
        "- rejected, cancelled_by_user, cancelled_by_shop, no_show, completed → 액션 없음 (읽기 전용).",
        "",
        "디자인 분석 상태별 사장님 웹 표시:",
        "- pending/in_progress → \"분석 중\" 표시. 사장님 액션 없음. 고객 미노출.",
        "- done → \"분석 완료\". 노출/숨김 가능. 고객 노출 가능.",
        "- failed → \"분석 실패\" + 재분석 버튼(POST /owner/designs/{id}/reanalyze). 고객 미노출.",
    ]


def _build_section_lines(item):
    """단일 기능 섹션의 AI 요약 텍스트를 생성한다."""
    section_lines = [
        f"## {item['id']}. {item['title']}",
        f"요약: {item['summary']}",
    ]
    if item.get("implementation_guides"):
        section_lines.append("구현 가이드:")
        section_lines.extend(f"- {guide}" for guide in item["implementation_guides"])
    if item.get("checkpoints"):
        section_lines.append("체크포인트:")
        section_lines.extend(f"- {checkpoint}" for checkpoint in item["checkpoints"])
    playbook = item.get("playbook") or {}
    if playbook.get("api_sequence"):
        section_lines.append("API 호출 순서:")
        section_lines.extend(f"- {row}" for row in playbook["api_sequence"])
    if playbook.get("ui_events"):
        section_lines.append("버튼/이벤트 처리:")
        section_lines.extend(
            f"- {trigger} -> {api} -> 성공: {success} / 실패: {failure}"
            for trigger, api, success, failure in playbook["ui_events"]
        )
    if playbook.get("states"):
        section_lines.append("화면 상태:")
        section_lines.extend(f"- {row}" for row in playbook["states"])
    if playbook.get("qa"):
        section_lines.append("QA 체크리스트:")
        section_lines.extend(f"- [ ] {row}" for row in playbook["qa"])
    if item.get("field_refs"):
        field_names = ", ".join(f"{ref['entity']}.{ref['name']}" for ref in item["field_refs"])
        section_lines.append(f"관련 필드: {field_names}")
    if item.get("api_refs"):
        section_lines.append("관련 API:")
        section_lines.extend(
            f"- {ref['endpoint']} : {clip_text(ref.get('purpose'), 120)}"
            for ref in item["api_refs"]
        )
    return section_lines


_FOOTER_LINES = [
    "",
    "프론트 구현 요청 방식:",
    "- 화면 진입 시 호출 API, 버튼 클릭 시 호출 API, 성공 후 화면 변화, 실패 시 문구를 먼저 정리한 뒤 구현합니다.",
    "- 프론트에서 복잡한 상태 조합을 새로 만들지 말고 백엔드 상태값과 available action 규칙을 확인합니다.",
    "- 이미지 업로드, 예약 상태 변경, 결제 확인, AI 분석 상태는 특히 임의 구현을 피합니다.",
]


def build_ai_brief(index):
    preamble_lines = _build_preamble_lines()
    preamble = "\n".join(preamble_lines).strip()

    sections = []
    all_section_lines = []
    for item in index["mappings"]:
        section_lines = _build_section_lines(item)
        sections.append({
            "id": item["id"],
            "title": item["title"],
            "text": "\n".join(section_lines).strip(),
        })
        all_section_lines.append("")
        all_section_lines.extend(section_lines)

    full_lines = preamble_lines + ["\n기능별 구현 컨텍스트:"] + all_section_lines + _FOOTER_LINES
    full_text = "\n".join(full_lines).strip() + "\n"

    return {
        "full": full_text,
        "preamble": preamble,
        "sections": sections,
    }


def build_index():
    if not FRONT_SPEC_PATH.exists():
        raise FileNotFoundError(f"프론트 명세서를 찾을 수 없습니다: {FRONT_SPEC_PATH}")
    frontend_sections = extract_front_sections(FRONT_SPEC_PATH)
    backend = load_backend_data()
    annotations = {}
    if CANONICAL_PATH.exists():
        with CANONICAL_PATH.open(encoding="utf-8") as f:
            canonical = json.load(f)
        annotations = canonical.get("collaborator_annotations", {}).get("entities", {})
    mappings = [resolve_mapping(item, backend, frontend_sections, annotations) for item in OWNER_SECTION_MAP]

    all_fields = []
    for entity, entity_data in sorted(backend["entities"].items()):
        entity_notes = annotations.get(entity, {})
        for field in entity_data["fields"].values():
            all_fields.append({
                **field,
                "entity": entity,
                "href": link_for_source(field["source_file"], field["line"]),
                "team_note": entity_notes.get(field["name"], ""),
            })

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
    ai_result = build_ai_brief(index)
    index["ai_brief"] = ai_result["full"]
    index["ai_preamble"] = ai_result["preamble"]
    index["ai_sections"] = ai_result["sections"]
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
    .content { padding: 24px 32px 48px; overflow: auto; }
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
      gap: 16px;
    }
    .panel {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 16px;
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
      padding: 12px 14px;
      text-align: left;
      vertical-align: top;
      line-height: 1.6;
    }
    th {
      background: #f8fafc;
      color: #2d3a4a;
      font-size: 13px;
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
    ul, ol { margin: 0; padding-left: 20px; line-height: 1.6; }
    li { margin: 8px 0; }
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
    .copy-dropdown { position: relative; display: inline-block; }
    .copy-menu {
      display: none; position: absolute; right: 0; top: 100%;
      background: #fff; border: 1px solid var(--line); border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,.12); z-index: 100;
      min-width: 280px; padding: 4px 0; margin-top: 4px;
    }
    .copy-menu-item {
      display: block; width: 100%; padding: 8px 16px; border: none;
      background: none; text-align: left; cursor: pointer;
      font-size: 13px; color: var(--fg); white-space: nowrap;
    }
    .copy-menu-item:hover { background: var(--bg-alt, #f5f7fa); }
    .copy-menu-divider { border-top: 1px solid var(--line); margin: 4px 0; }
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
        <div class="copy-dropdown">
          <button class="copy-btn" id="copyAiBriefBtn" type="button">AI 요약 복사 ▾</button>
          <div class="copy-menu" id="copyMenu">
            <button class="copy-menu-item" data-copy="full" type="button">📋 전체 복사</button>
            <div class="copy-menu-divider"></div>
          </div>
        </div>
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
          <td class="team-note">${escapeHtml(ref.team_note || "")}</td>
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
          <div class="panel full"><h3>관련 필드</h3><table><thead><tr><th>필드</th><th>쉽게 말하면</th><th>원문 메모</th><th>팀 메모</th><th>출처</th></tr></thead><tbody>${fieldRows || "<tr><td colspan='5'>관련 필드 없음</td></tr>"}</tbody></table></div>
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

    async function copyToClipboard(text) {
      const status = document.getElementById("copyAiBriefStatus");
      try {
        await navigator.clipboard.writeText(text);
        status.textContent = "복사됨";
      } catch (error) {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        status.textContent = "복사됨";
      }
      document.getElementById("copyMenu").style.display = "none";
      window.setTimeout(function() { status.textContent = ""; }, 1800);
    }

    function buildCopyMenu() {
      const menu = document.getElementById("copyMenu");
      (data.ai_sections || []).forEach(function(sec) {
        const btn = document.createElement("button");
        btn.className = "copy-menu-item";
        btn.setAttribute("data-copy", "section-" + sec.id);
        btn.type = "button";
        btn.textContent = sec.id + ". " + sec.title;
        menu.appendChild(btn);
      });
    }

    document.getElementById("copyAiBriefBtn").addEventListener("click", function(e) {
      const menu = document.getElementById("copyMenu");
      menu.style.display = menu.style.display === "none" ? "block" : "none";
      e.stopPropagation();
    });
    document.addEventListener("click", function() {
      document.getElementById("copyMenu").style.display = "none";
    });
    document.getElementById("copyMenu").addEventListener("click", function(e) {
      const btn = e.target.closest(".copy-menu-item");
      if (!btn) return;
      const key = btn.getAttribute("data-copy");
      let text = "";
      if (key === "full") {
        text = data.ai_brief || "";
      } else if (key.startsWith("section-")) {
        const id = key.replace("section-", "");
        const sec = (data.ai_sections || []).find(function(s) { return s.id === id; });
        text = (data.ai_preamble || "") + "\\n\\n기능별 구현 컨텍스트:\\n\\n" + (sec ? sec.text : "");
        text += "\\n\\n프론트 구현 요청 방식:\\n- 화면 진입 시 호출 API, 버튼 클릭 시 호출 API, 성공 후 화면 변화, 실패 시 문구를 먼저 정리한 뒤 구현합니다.\\n- 프론트에서 복잡한 상태 조합을 새로 만들지 말고 백엔드 상태값과 available action 규칙을 확인합니다.\\n- 이미지 업로드, 예약 상태 변경, 결제 확인, AI 분석 상태는 특히 임의 구현을 피합니다.";
      }
      copyToClipboard(text);
    });

    document.getElementById("filterInput").addEventListener("input", renderList);
    document.getElementById("statusFilter").addEventListener("change", renderList);
    document.getElementById("globalSearch").addEventListener("input", renderGlobalResults);
    buildCopyMenu();
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
