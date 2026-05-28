"""MVP 위치 태그 — 서울 주요 지역 시스템 큐레이션 사전 (결정 #11).

도로명 주소 자동 파싱·지역구 자동화는 P1. MVP는 이 사전 내 키워드만 허용.
"""

from http import HTTPStatus

from app.api.errors import AppError

SEOUL_LOCATION_TAGS: tuple[str, ...] = (
    "홍대",
    "성수",
    "강남",
    "명동",
    "이태원",
    "가로수길",
    "압구정",
    "신사",
    "연남",
    "한남",
)

_ALLOWED = set(SEOUL_LOCATION_TAGS)
MAX_LOCATION_TAGS = 3


def validate_location_tags(tags: list[str]) -> list[str]:
    """큐레이션 사전 내 태그만 허용, 중복 제거(입력 순서 유지), 최대 개수 제한."""
    seen: list[str] = []
    for tag in tags:
        if tag not in _ALLOWED:
            raise AppError(
                "INVALID_LOCATION_TAG",
                f"지원하지 않는 위치 태그입니다: {tag}",
                HTTPStatus.BAD_REQUEST,
            )
        if tag not in seen:
            seen.append(tag)
    if len(seen) > MAX_LOCATION_TAGS:
        raise AppError(
            "TOO_MANY_LOCATION_TAGS",
            f"위치 태그는 최대 {MAX_LOCATION_TAGS}개까지 선택할 수 있습니다.",
            HTTPStatus.BAD_REQUEST,
        )
    return seen
