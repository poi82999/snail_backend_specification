from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OPENAPI_PATH = DOCS / "openapi.json"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.openapi_examples import (  # noqa: E402
    DESIGN_ID,
    DESIGNER_ID,
    OPERATION_EXAMPLES,
    OPTION_ID,
    RESERVATION_ID,
    SHOP_ID,
)
from tools.build_contract_reference import collect_enums, collect_errors  # noqa: E402


@dataclass(frozen=True, slots=True)
class Operation:
    method: str
    path: str
    tag: str
    summary: str
    operation_id: str


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _status_label(status: int) -> str:
    try:
        return f"{status} {HTTPStatus(status).name}"
    except ValueError:
        return str(status)


def _load_openapi() -> dict[str, Any]:
    return json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))


def _iter_operations(schema: dict[str, Any]) -> list[Operation]:
    operations: list[Operation] = []
    paths = schema.get("paths", {})
    if not isinstance(paths, dict):
        return operations

    for path, path_item in paths.items():
        if not isinstance(path, str) or not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if not isinstance(method, str) or not isinstance(operation, dict):
                continue
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            tags = operation.get("tags")
            tag = tags[0] if isinstance(tags, list) and tags and isinstance(tags[0], str) else "-"
            summary = operation.get("summary")
            operation_id = operation.get("operationId")
            operations.append(
                Operation(
                    method=method.upper(),
                    path=path,
                    tag=tag,
                    summary=summary if isinstance(summary, str) else "",
                    operation_id=operation_id if isinstance(operation_id, str) else "",
                )
            )
    return sorted(operations, key=lambda op: (op.tag, op.path, op.method))


def _format_operations(operations: list[Operation]) -> str:
    grouped: dict[str, list[Operation]] = defaultdict(list)
    for operation in operations:
        grouped[operation.tag].append(operation)

    lines: list[str] = []
    for tag in sorted(grouped):
        lines.append(f"## {tag}")
        for operation in grouped[tag]:
            lines.append(
                f"- {operation.method:6} {operation.path} | {operation.summary} "
                f"| operationId={operation.operation_id}"
            )
        lines.append("")
    return "\n".join(lines).rstrip()


def _frontend_filter(operation: Operation) -> bool:
    if operation.tag == "auth":
        return operation.path in {"/api/v1/auth/apple", "/api/v1/auth/refresh"}
    if operation.tag in {"users", "favorites", "follows", "snails", "search", "reports"}:
        return True
    if operation.tag == "designs":
        return not operation.path.startswith("/api/v1/shops/me")
    if operation.tag == "reservations":
        return not operation.path.startswith("/api/v1/shops/me")
    if operation.tag == "reviews":
        return operation.path != "/api/v1/reviews/{review_id}/replies"
    if operation.tag == "shops":
        return not operation.path.startswith("/api/v1/shops/me")
    if operation.tag == "designers":
        return operation.path.startswith("/api/v1/shops/{shop_id}/designers")
    return False


def _owner_filter(operation: Operation) -> bool:
    if operation.tag == "auth":
        return operation.path.startswith("/api/v1/auth/owner") or operation.path in {
            "/api/v1/auth/refresh",
            "/api/v1/auth/password-reset",
            "/api/v1/auth/password-reset/confirm",
        }
    if operation.tag in {"owners", "notifications"}:
        return True
    if operation.tag in {"shops", "designers", "designs", "reservations"}:
        return operation.path.startswith("/api/v1/shops/me")
    if operation.tag == "reviews":
        return operation.path in {
            "/api/v1/shops/{shop_id}/reviews",
            "/api/v1/reviews/{review_id}/replies",
        }
    return False


def _llm_filter(operation: Operation) -> bool:
    return operation.path.startswith("/api/v1/shops/me/designs") or operation.path in {
        "/api/v1/designs",
        "/api/v1/designs/{design_id}",
    }


def _format_errors() -> str:
    lines: list[str] = []
    for entry in collect_errors():
        statuses = ", ".join(_status_label(status) for status in sorted(entry.statuses))
        message = entry.representative_message or "(메시지 동적 생성; 발생 위치 기준 확인)"
        lines.append(f"- {entry.code} | {statuses} | {message}")
    return "\n".join(lines)


def _format_enums() -> str:
    lines = [
        "주의: API/OpenAPI에는 아래 소문자 value가 노출된다. DB native_enum=False 컬럼은 대문자 NAME을 저장할 수 있다.",
        "",
    ]
    for name, values in collect_enums().items():
        lines.append(f"- {name}: {', '.join(values)}")
    return "\n".join(lines)


def _request(operation_id: str) -> str:
    return _json(OPERATION_EXAMPLES[operation_id]["request"])


def _response(operation_id: str, status: str = "200") -> str:
    return _json(OPERATION_EXAMPLES[operation_id]["responses"][status])


def _common_contract() -> str:
    return f"""# 공통 계약

- Base URL: `http://localhost:8000/api/v1`
- 인증: `Authorization: Bearer <access_token>`
- 변이 요청: `POST`, `PUT`, `PATCH`, `DELETE`에는 `Idempotency-Key: <unique-key>`를 붙인다.
- request id: 모든 응답 헤더에 `X-Request-Id`, 에러 응답 body에 `request_id`.
- 에러 envelope:

```json
{_json({"error": {"code": "VALIDATION_ERROR", "message": "입력값을 확인해주세요.", "field_errors": {"email": "올바른 이메일 형식이 아닙니다."}}, "request_id": "req_01HYZ000000000000000000000"})}
```

## 에러 코드 카탈로그

{_format_errors()}

## Enum 값

{_format_enums()}
"""


def _frontend_bundle(operations: list[Operation], generated_at: str) -> str:
    return f"""# frontend_app.ai.txt — Snail 유저 앱 AI 번들

Generated at: {generated_at}
Source: docs/openapi.json + backend/app AppError/StrEnum scan

목표: iOS 유저 앱 또는 모바일 프론트 AI가 이 파일 하나로 인증, 탐색, 예약, 커뮤니티 호출 코드를 만들 수 있게 한다.

{_common_contract()}

# 핵심 시나리오 선택

유저앱의 golden path는 `애플 로그인 → 디자인 검색 → 디자인 상세 → 예약 가능 시간 조회 → 예약 생성 → 내 예약 확인 → 완료 후 리뷰 작성`이다. 지도/스네일/팔로우는 보조 시나리오로 붙인다.

# 인증 흐름

1. `POST /auth/apple`로 Apple id_token을 교환한다. 로컬 mock Apple endpoint는 없다.
2. 응답의 `tokens.access_token`을 저장하고 모든 사용자 보호 API에 Bearer로 보낸다.
3. 만료 시 `POST /auth/refresh`로 access/refresh token pair를 갱신한다.
4. 선호 이미지 모드는 `PATCH /me`의 `image_view_mode`로 바꾼다. 값은 `model` 또는 `wear`.

## 애플 로그인 요청

```http
POST /api/v1/auth/apple
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json
```

```json
{_request("auth_apple_sign_in")}
```

## 애플 로그인 응답

```json
{_response("auth_apple_sign_in")}
```

# 레시피: 디자인 검색해서 예약하기

## 1. 디자인 검색

```http
GET /api/v1/designs?q=프렌치&region=강남&colors=핑크&moods=러블리&sort=popular&limit=20
Authorization: Bearer <optional_access_token>
```

```json
{_response("designs_search_designs")}
```

## 2. 디자인 상세

```http
GET /api/v1/designs/{DESIGN_ID}
Authorization: Bearer <optional_access_token>
```

```json
{_response("designs_get_public_design")}
```

## 3. 예약 가능 시간 조회

옵션을 선택했다면 같은 option id를 `option_ids` query로 넘긴다. 선택 옵션의 추가 소요 시간이 availability에 반영된다.

```http
GET /api/v1/designs/{DESIGN_ID}/availability?date=2026-06-01&option_ids={OPTION_ID}
```

```json
{_response("reservations_get_design_availability")}
```

## 4. 예약 생성

```http
POST /api/v1/reservations
Authorization: Bearer <access_token>
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440001
Content-Type: application/json
```

```json
{_request("reservations_create_reservation")}
```

```json
{_response("reservations_create_reservation", "201")}
```

## 5. 내 예약 확인

```http
GET /api/v1/me/reservations/{RESERVATION_ID}
Authorization: Bearer <access_token>
```

예약 목록은 `GET /api/v1/me/reservations?status=confirmed&limit=20`로 조회하고, 응답의 `page.next_cursor`가 있으면 다음 요청에 `cursor`로 그대로 전달한다.

## 6. 완료 후 리뷰 작성

작성 가능 기간이 지나면 `REVIEW_EDIT_WINDOW_CLOSED`가 올 수 있다.

```http
POST /api/v1/reservations/{RESERVATION_ID}/reviews
Authorization: Bearer <access_token>
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440002
Content-Type: application/json
```

```json
{_request("reviews_create_review")}
```

```json
{_response("reviews_create_review", "201")}
```

# 보조 시나리오

- 지도 탐색: `GET /shops?bbox=minLng,minLat,maxLng,maxLat&location_tag=강남` → `GET /shops/{{shop_id}}` → `GET /shops/{{shop_id}}/designers`.
- 스네일 피드: `GET /snails?feed_type=latest&limit=20` → `POST /snails/{{snap_id}}/like` / `POST /snails/{{snap_id}}/save` / `POST /snails/{{snap_id}}/comments`.
- 디자인 즐겨찾기: `POST /designs/{{design_id}}/favorite`.
- 팔로우: `POST /users/{{user_id}}/follow`, 목록은 followers/following API.
- 신고: `POST /reports`.

# 유저 앱 엔드포인트 카탈로그

{_format_operations([operation for operation in operations if _frontend_filter(operation)])}
"""


def _owner_bundle(operations: list[Operation], generated_at: str) -> str:
    return f"""# owner_web.ai.txt — Snail 사장님 웹 AI 번들

Generated at: {generated_at}
Source: docs/openapi.json + backend/app AppError/StrEnum scan

목표: 사장님 웹 프론트 AI가 이 파일 하나로 계정, 샵, 디자이너, 디자인/옵션, 예약 운영 화면을 구현하게 한다.

{_common_contract()}

# 핵심 시나리오 선택

사장님 웹의 golden path는 `회원가입/로그인 → 사업자 인증 → 샵 생성/영업시간 → 디자이너 등록 → 디자인 등록 → 디자인 옵션 → AI 완료 후 공개 → 예약 승인/결제확인/완료`이다.

# 인증과 계정

## 회원가입

```http
POST /api/v1/auth/owner/signup
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440010
Content-Type: application/json
```

```json
{_request("auth_owner_signup")}
```

```json
{_response("auth_owner_signup", "201")}
```

## 로그인

```http
POST /api/v1/auth/owner/login
Content-Type: application/json
```

```json
{_request("auth_owner_login")}
```

```json
{_response("auth_owner_login")}
```

로그인 후 첫 화면은 `GET /owners/me`로 `verification_status`를 확인한다. `pending`/`rejected`에서는 공개 전환과 예약 운영 액션을 막고 인증 화면으로 유도한다.

# 레시피: 사장님 온보딩부터 디자인 공개까지

## 1. 사업자 인증 제출

현재 OpenAPI에는 presigned upload endpoint가 없다. `document_object_key`에는 이미 업로드된 사업자등록증 object key를 넣는 전제로 구현한다.

```http
POST /api/v1/owners/me/business-verification
Authorization: Bearer <owner_access_token>
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440011
Content-Type: application/json
```

```json
{_request("owners_submit_business_verification")}
```

```json
{_response("owners_submit_business_verification", "201")}
```

## 2. 샵 생성

```http
POST /api/v1/shops/me
Authorization: Bearer <owner_access_token>
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440012
Content-Type: application/json
```

```json
{_request("shops_create_my_shop")}
```

```json
{_response("shops_create_my_shop", "201")}
```

## 3. 영업시간 설정

```http
PUT /api/v1/shops/me/business-hours
Authorization: Bearer <owner_access_token>
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440013
Content-Type: application/json
```

```json
{_request("shops_set_my_shop_business_hours")}
```

## 4. 디자이너 등록

```http
POST /api/v1/shops/me/designers
Authorization: Bearer <owner_access_token>
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440014
Content-Type: application/json
```

```json
{_request("designers_create_designer")}
```

```json
{_response("designers_create_designer", "201")}
```

## 5. 디자인 등록

현재 OpenAPI에는 presigned upload endpoint가 없다. `image_upload_keys`에는 이미 업로드된 object key를 넣는 전제로 구현하고, 실제 업로드 계약은 백엔드와 별도 확인한다.

```http
POST /api/v1/shops/me/designs
Authorization: Bearer <owner_access_token>
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440015
Content-Type: application/json
```

```json
{_request("designs_create_design")}
```

```json
{_response("designs_create_design", "201")}
```

등록 직후 `ai_analysis_status=pending`이면 고객 앱에 노출하지 않는다. 상세 화면은 `GET /shops/me/designs/{DESIGN_ID}`를 폴링하거나 수동 새로고침한다.

## 6. 디자인 옵션 등록

```http
POST /api/v1/shops/me/designs/{DESIGN_ID}/options
Authorization: Bearer <owner_access_token>
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440016
Content-Type: application/json
```

```json
{_request("designs_create_design_option")}
```

```json
{_response("designs_create_design_option", "201")}
```

## 7. 공개 전환

공개 노출 조건은 `owner.verification_status=approved`, `shop.visibility=active`, `design.visibility=active`, `design.ai_analysis_status=done`이다.

```http
POST /api/v1/shops/me/designs/{DESIGN_ID}/visibility
Authorization: Bearer <owner_access_token>
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440017
Content-Type: application/json
```

```json
{_request("designs_change_visibility")}
```

# 레시피: 예약 운영

```http
GET /api/v1/shops/me/reservations?status=pending&from=2026-06-01&to=2026-06-30&limit=20
Authorization: Bearer <owner_access_token>
```

```json
{_response("reservations_list_shop_reservations")}
```

예약 상태 버튼:
- `pending` → `POST /shops/me/reservations/{{reservation_id}}/accept` 또는 `/reject`.
- `payment_pending` → `POST /shops/me/reservations/{{reservation_id}}/confirm-payment`.
- `confirmed` → `POST /shops/me/reservations/{{reservation_id}}/complete`, `/no-show`, `/cancel`.
- terminal 상태 `rejected`, `cancelled_by_user`, `cancelled_by_shop`, `no_show`, `completed`는 읽기 전용.

# 사장님 웹 엔드포인트 카탈로그

{_format_operations([operation for operation in operations if _owner_filter(operation)])}
"""


def _llm_bundle(operations: list[Operation], generated_at: str) -> str:
    return f"""# llm_module.ai.txt — Snail LLM 모듈 AI 번들

Generated at: {generated_at}
Source: backend/app/workers/llm_pipeline.py + backend/app/services/llm + docs/openapi.json

목표: Transform/Classify/Embed 작업자가 백엔드 저장 필드, 상태 전이, GCS 인터페이스, 표준 태그 사전을 한 파일에서 이해하게 한다.

{_common_contract()}

# 핵심 시나리오 선택

LLM 모듈의 golden path는 `Design 생성 이벤트 → Transform/vision describe → processed image 저장 → Classify → Embed → Design.ai_* 저장 → ai_analysis_status=done`이다. 실패 시 `failed`와 error_code/error_message를 남긴다.

# 현재 백엔드 파이프라인

- 워커 entrypoint: `backend/app/workers/llm_pipeline.py::analyze_design(ctx, design_id)`.
- 상태 전이: `pending → in_progress → done` 또는 `failed`.
- 작업 row: `LlmJob(job_type=transform|classify|embed|reanalyze, status=running|succeeded|failed, request_payload, response_payload, error_code)`.
- 대상 이미지: `Design.thumbnail_url` 우선, 없으면 `DesignImage`의 thumbnail/sort 순서. `processed_url`이 있으면 그것을 쓰고 없으면 `original_url`.
- 이미지가 없으면 `NO_IMAGE` AppError로 실패한다.
- 현재 코드에는 masking bytes를 받아 `upload_and_attach_processed_image()`를 호출하는 TODO가 남아 있다. LLM 작업자는 이 인터페이스에 맞춰 Transform 결과를 연결한다.

# Transform 계약

입력:
```json
{_json({"image_id": "99999999-9999-4999-8999-999999999999", "image_url": "https://cdn.example.com/designs/original.jpg", "callback_url": "https://api.example.com/internal/llm/transform-callback", "options": {"output_size": "1080x1080", "background": "transparent"}})}
```

성공 출력:
```json
{_json({"image_id": "99999999-9999-4999-8999-999999999999", "status": "success", "cropped_image_url": "https://cdn.example.com/designs/processed.png", "cropped_image_size": {"width": 1080, "height": 1080}, "confidence": 0.94, "nail_count_detected": 10, "processing_time_ms": 1820})}
```

실패 출력:
```json
{_json({"image_id": "99999999-9999-4999-8999-999999999999", "status": "failed", "error_code": "NO_NAIL", "error_message": "Could not detect nail area in the image"})}
```

# GCS processed image 연결

백엔드 함수:

```python
await upload_and_attach_processed_image(
    session,
    gcs_client,
    design_image_id,
    image_bytes,
    content_type="image/png",
)
```

계약:
- bucket: `settings.GCS_BUCKET_DESIGNS`.
- object key: `designs/processed/{{design_image_id}}.png`.
- public URL: `GCS_PUBLIC_BASE_URL`이 있으면 그 prefix, 없으면 `https://storage.googleapis.com/{{bucket}}/{{object_key}}`.
- 성공하면 `DesignImage.processed_url`에 public URL을 저장하고 flush한다.
- 실패 코드: `GCS_BUCKET_NOT_CONFIGURED`, `DESIGN_IMAGE_NOT_FOUND`.

# Classify 계약

입력:
```json
{_json({"image_url": "https://cdn.example.com/designs/processed.png", "image_id": "99999999-9999-4999-8999-999999999999", "locale": "ko_KR", "options": {"max_tags": 5, "include_color_palette": True, "include_style_category": True}})}
```

출력:
```json
{_json({"image_id": "99999999-9999-4999-8999-999999999999", "status": "success", "ai_tags": ["프렌치", "봄", "러블리"], "color_palette": ["핑크", "화이트"], "style_category": "trendy", "nail_shape": "라운드", "confidence": 0.932, "processing_time_ms": 1460})}
```

백엔드 저장:
- `Design.ai_tags`
- `Design.color_palette`
- `Design.style_category`
- `Design.nail_shape`
- `Design.ai_confidence`
- `Design.ai_model_version`
- `Design.search_indexed_at`

# 표준 태그 사전

- style_category: `simple`, `glamour`, `classic`, `trendy`, `chic`
- nail_shape: `스퀘어`, `라운드`, `오벌`, `아몬드`, `스틸레토`, `발레리나`
- tags/style-technique: `프렌치`, `옴브레`, `그라데이션`, `마그넷`, `글리터`, `큐빅`, `라인아트`, `캐릭터`, `무광`, `유광`, `젤`, `매니큐어`, `페디큐어`, `연장`, `케어`, `제거`
- tags/mood-occasion: `봄`, `여름`, `가을`, `겨울`, `시크`, `러블리`, `심플`, `글래머`, `내추럴`, `키치`, `모던`, `웨딩`, `데일리`, `파티`, `오피스`, `데이트`
- color_palette: `핑크`, `레드`, `누드`, `블랙`, `화이트`, `베이지`, `블루`, `그린`, `옐로우`, `퍼플`, `브라운`, `골드`, `실버`

# 재분석과 공개 노출

- 사장님 수동 재분석: `POST /api/v1/shops/me/designs/{DESIGN_ID}/reanalyze`.
- 디자인 상세 polling: `GET /api/v1/shops/me/designs/{DESIGN_ID}`.
- 고객 앱 노출 조건: `owner approved + shop active + design active + ai_analysis_status=done`.

# 관련 REST 엔드포인트

{_format_operations([operation for operation in operations if _llm_filter(operation)])}
"""


def _cookbook(generated_at: str) -> str:
    return f"""# api_cookbook.ai.txt — 작업지향 레시피

Generated at: {generated_at}

이 파일은 비개발자와 AI에게 "무엇을 어떤 순서로 호출해야 하는지"를 복붙 가능한 흐름으로 준다. 상세 스키마는 `docs/openapi.json`, 에러/enum 전체 계약은 `docs/api_contract_reference.html`도 함께 본다.

# Recipe A — 유저앱: 디자인 검색해서 예약하는 화면

1. `POST /api/v1/auth/apple`로 토큰 획득.
2. `GET /api/v1/designs?q=프렌치&region=강남&colors=핑크&moods=러블리&sort=popular&limit=20`.
3. 사용자가 디자인 카드 선택 → `GET /api/v1/designs/{DESIGN_ID}`.
4. 옵션 선택 후 `GET /api/v1/designs/{DESIGN_ID}/availability?date=2026-06-01&option_ids={OPTION_ID}`.
5. 슬롯 선택 후 `POST /api/v1/reservations` with Idempotency-Key.
6. 예약 완료 화면은 `ReservationMe.status`, `payment_method_snapshot`, `deposit_amount_snapshot`, `bank_snapshot`으로 분기.

예약 생성 body:
```json
{_request("reservations_create_reservation")}
```

예약 생성 response:
```json
{_response("reservations_create_reservation", "201")}
```

# Recipe B — 사장님 웹: 디자인 등록하고 공개하는 화면

1. `POST /api/v1/auth/owner/login`.
2. `GET /api/v1/owners/me`로 인증 상태 확인.
3. `POST /api/v1/owners/me/business-verification`로 사업자 인증 제출.
4. `POST /api/v1/shops/me` 또는 `GET/PATCH /api/v1/shops/me`.
5. `POST /api/v1/shops/me/designers`로 담당 디자이너를 만든다.
6. 업로드된 object key로 `POST /api/v1/shops/me/designs`.
7. `GET /api/v1/shops/me/designs/{DESIGN_ID}`를 새로고침해 `ai_analysis_status=done`을 확인.
8. `POST /api/v1/shops/me/designs/{DESIGN_ID}/options`.
9. `POST /api/v1/shops/me/designs/{DESIGN_ID}/visibility`로 active 전환.

사업자 인증 body:
```json
{_request("owners_submit_business_verification")}
```

디자인 생성 body:
```json
{_request("designs_create_design")}
```

옵션 생성 body:
```json
{_request("designs_create_design_option")}
```

# Recipe C — 사장님 웹: 예약 처리 보드

1. `GET /api/v1/shops/me/reservations?status=pending&from=2026-06-01&to=2026-06-30&limit=20`.
2. pending 예약은 `POST /api/v1/shops/me/reservations/{{reservation_id}}/accept` 또는 `/reject`.
3. 계좌이체 예약이 `payment_pending`이면 `POST /confirm-payment`.
4. 방문 완료 후 `POST /complete`, 미방문은 정책에 맞춰 `POST /no-show`.

예약 목록 response:
```json
{_response("reservations_list_shop_reservations")}
```

# Recipe D — LLM 모듈: 디자인 분석 파이프라인

1. 워커가 `analyze_design(ctx, design_id)` 시작.
2. `Design.ai_analysis_status=in_progress`.
3. 대상 이미지 URL 선택: `processed_url or original_url`.
4. Transform/vision describe 성공 → `LlmJob(transform).status=succeeded`.
5. 필요 시 `upload_and_attach_processed_image()`로 processed_url 저장.
6. Classify 성공 → `Design.ai_tags`, `color_palette`, `style_category`, `nail_shape`, `ai_confidence` 저장.
7. Embed 성공 → `Design.embedding` 저장.
8. `Design.ai_analysis_status=done`, `search_indexed_at=now`.
9. 예외가 max retry 이후에도 계속되면 `ai_analysis_status=failed`, `ai_error_code`, `ai_error_message` 저장.

# AI 검증 프롬프트

AI 도구에 `docs/frontend_app.ai.txt`와 이 cookbook만 주고 다음을 요청한다:

> React Native로 "디자인 검색해서 예약하는 화면"을 구현해줘. 검색 필터, 디자인 카드, 옵션 선택, 날짜별 availability, 예약 생성, 에러 처리까지 포함해줘.

올바른 답변은 최소한 다음 호출을 사용해야 한다:
- `POST /api/v1/auth/apple`
- `GET /api/v1/designs`
- `GET /api/v1/designs/{{design_id}}`
- `GET /api/v1/designs/{{design_id}}/availability`
- `POST /api/v1/reservations`
- `Authorization: Bearer <token>`
- `Idempotency-Key` on mutation
- `ErrorResponse.error.code` 분기
"""


def _llms_txt(generated_at: str) -> str:
    return f"""# Snail Backend AI Entry Point

Generated at: {generated_at}

AI 도구(Cursor, Claude, Codex 등)에 파일/URL 하나만 줄 수 있으면 이 파일을 먼저 준다.

- `docs/openapi.json`: 전체 API의 기계용 계약. codegen 입력은 항상 이 파일이다.
- `docs/api_reference.html`: `openapi.json`을 Redoc으로 보는 사람용 API 탐색기.
- `docs/api_contract_reference.html`: 에러 코드, 인증, 페이지네이션, Idempotency-Key, enum value 계약.
- `docs/local_onboarding.md`: 로컬 실행, base URL, 개발 토큰 발급, CORS.
- `docs/frontend_app.ai.txt`: 유저 앱 AI용 self-contained 번들. 디자인 검색/예약/리뷰/스네일 구현 전용.
- `docs/owner_web.ai.txt`: 사장님 웹 AI용 self-contained 번들. 샵/디자이너/디자인/예약 운영 구현 전용.
- `docs/llm_module.ai.txt`: LLM Transform/Classify/Embed 작업자용 self-contained 번들.
- `docs/api_cookbook.ai.txt`: 복붙 가능한 작업지향 레시피. "로그인 → 검색 → 예약 생성" 같은 흐름 우선.

권장 사용:
1. 앱/웹 codegen은 `docs/openapi.json`만 사용한다.
2. AI에게 화면이나 모듈 구현을 맡길 때는 해당 audience `.ai.txt`와 `docs/api_cookbook.ai.txt`를 함께 준다.
3. 에러/enum이 헷갈리면 `docs/api_contract_reference.html`을 추가로 읽힌다.
"""


def main() -> None:
    schema = _load_openapi()
    operations = _iter_operations(schema)
    generated_at = datetime.now(UTC).isoformat()

    outputs = {
        "llms.txt": _llms_txt(generated_at),
        "frontend_app.ai.txt": _frontend_bundle(operations, generated_at),
        "owner_web.ai.txt": _owner_bundle(operations, generated_at),
        "llm_module.ai.txt": _llm_bundle(operations, generated_at),
        "api_cookbook.ai.txt": _cookbook(generated_at),
    }

    for name, content in outputs.items():
        path = DOCS / name
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
