from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import Any, TypedDict, cast

import openai
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.api.errors import AppError
from app.core.config import get_settings

EMBEDDING_DIMENSIONS = 1536
_semaphore = asyncio.Semaphore(get_settings().OPENAI_MAX_CONCURRENT)


class VisionResult(TypedDict):
    description: str
    model: str


class ClassifyResult(TypedDict):
    ai_tags: list[str]
    color_palette: list[str]
    style_category: str | None
    nail_shape: str | None
    confidence: float
    model: str


def _client() -> Any:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        raise AppError(
            "OPENAI_NOT_CONFIGURED",
            "OpenAI API 키가 설정되지 않았습니다.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )
    return openai.AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=settings.OPENAI_REQUEST_TIMEOUT_SEC,
    )


def _response_model(response: Any, fallback: str) -> str:
    model = getattr(response, "model", fallback)
    return model if isinstance(model, str) else fallback


def _raise_non_retryable_openai_error(exc: openai.APIStatusError) -> None:
    if exc.status_code == HTTPStatus.TOO_MANY_REQUESTS:
        return
    if HTTPStatus.BAD_REQUEST <= exc.status_code < HTTPStatus.INTERNAL_SERVER_ERROR:
        if exc.status_code in {
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.FORBIDDEN,
        }:
            raise AppError(
                "OPENAI_AUTH_FAILED",
                "OpenAI 인증에 실패했습니다.",
                HTTPStatus.SERVICE_UNAVAILABLE,
            ) from exc
        raise AppError(
            "OPENAI_REQUEST_REJECTED",
            "OpenAI 요청이 거부되었습니다.",
            HTTPStatus.BAD_GATEWAY,
        ) from exc


def _message_text(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if not isinstance(choices, list) or not choices:
        raise AppError("LLM_EMPTY_RESPONSE", "LLM 응답이 비어 있습니다.", HTTPStatus.BAD_GATEWAY)

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None)
    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
                continue
            item_text = getattr(item, "text", None)
            if isinstance(item_text, str):
                parts.append(item_text)
        text = "\n".join(parts).strip()
    else:
        text = ""

    if not text:
        raise AppError("LLM_EMPTY_RESPONSE", "LLM 응답이 비어 있습니다.", HTTPStatus.BAD_GATEWAY)
    return text


def _string_list(value: object, *, max_items: int = 12) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        normalized = item.strip()
        if normalized and normalized not in result:
            result.append(normalized[:40])
        if len(result) >= max_items:
            break
    return result


def _optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized[:40] if normalized else None


def _confidence(value: object) -> float:
    if isinstance(value, int | float | str):
        try:
            parsed = float(value)
        except ValueError:
            return 0.0
        return max(0.0, min(1.0, parsed))
    return 0.0


@retry(
    retry=retry_if_exception_type((openai.RateLimitError, openai.APIError)),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def vision_describe(image_url: str, *, prompt: str) -> VisionResult:
    settings = get_settings()
    model = settings.OPENAI_VISION_MODEL
    async with _semaphore:
        try:
            response = await _client().chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
            )
        except openai.APIStatusError as exc:
            _raise_non_retryable_openai_error(exc)
            raise
    return {"description": _message_text(response), "model": _response_model(response, model)}


@retry(
    retry=retry_if_exception_type((openai.RateLimitError, openai.APIError)),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def classify_from_description(description: str) -> ClassifyResult:
    settings = get_settings()
    model = settings.OPENAI_VISION_MODEL
    async with _semaphore:
        try:
            response = await _client().chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "네일 디자인 설명을 JSON으로 분류하세요. "
                            "키는 ai_tags, color_palette, style_category, nail_shape, confidence만 "
                            "사용하세요."
                        ),
                    },
                    {"role": "user", "content": description},
                ],
                response_format={"type": "json_object"},
            )
        except openai.APIStatusError as exc:
            _raise_non_retryable_openai_error(exc)
            raise
    content = _message_text(response)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AppError(
            "LLM_PARSE_FAILED",
            "LLM JSON 응답을 해석할 수 없습니다.",
            HTTPStatus.BAD_GATEWAY,
        ) from exc
    if not isinstance(parsed, dict):
        raise AppError(
            "LLM_PARSE_FAILED",
            "LLM JSON 응답 형식이 올바르지 않습니다.",
            HTTPStatus.BAD_GATEWAY,
        )

    payload = cast(dict[str, object], parsed)
    colors = payload.get("color_palette", payload.get("colors"))
    return {
        "ai_tags": _string_list(payload.get("ai_tags")),
        "color_palette": _string_list(colors),
        "style_category": _optional_string(payload.get("style_category")),
        "nail_shape": _optional_string(payload.get("nail_shape")),
        "confidence": _confidence(payload.get("confidence")),
        "model": _response_model(response, model),
    }


@retry(
    retry=retry_if_exception_type((openai.RateLimitError, openai.APIError)),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def embed_text(text: str) -> list[float]:
    settings = get_settings()
    model = settings.OPENAI_EMBED_MODEL
    async with _semaphore:
        try:
            response = await _client().embeddings.create(
                model=model,
                input=text,
                dimensions=EMBEDDING_DIMENSIONS,
            )
        except openai.APIStatusError as exc:
            _raise_non_retryable_openai_error(exc)
            raise
    data = getattr(response, "data", None)
    if not isinstance(data, list) or not data:
        raise AppError("LLM_EMPTY_RESPONSE", "임베딩 응답이 비어 있습니다.", HTTPStatus.BAD_GATEWAY)

    raw_embedding = getattr(data[0], "embedding", None)
    if not isinstance(raw_embedding, list):
        raise AppError(
            "LLM_PARSE_FAILED",
            "임베딩 응답 형식이 올바르지 않습니다.",
            HTTPStatus.BAD_GATEWAY,
        )
    embedding = [float(value) for value in raw_embedding]
    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise AppError(
            "LLM_PARSE_FAILED",
            "임베딩 차원이 올바르지 않습니다.",
            HTTPStatus.BAD_GATEWAY,
        )
    return embedding
