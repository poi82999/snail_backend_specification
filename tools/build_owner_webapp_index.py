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
        "front_refs": resolved_sections,
        "field_refs": field_refs,
        "api_refs": api_refs,
        "missing_front_sections": missing_front_sections,
        "missing_refs": missing_refs,
        "coverage": round(coverage, 3),
        "status": "needs_attention" if missing_refs or missing_front_sections or coverage < 1 else "connected",
    }


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

    return {
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
    <div class="stats" id="stats"></div>
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

    document.getElementById("filterInput").addEventListener("input", renderList);
    document.getElementById("statusFilter").addEventListener("change", renderList);
    document.getElementById("globalSearch").addEventListener("input", renderGlobalResults);
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
    print(f"sections: {index['stats']['mapping_sections']}")
    print(f"fields: {index['stats']['backend_fields']}")
    print(f"apis: {index['stats']['apis']}")
    print(f"attention_sections: {index['stats']['attention_sections']}")


if __name__ == "__main__":
    main()
