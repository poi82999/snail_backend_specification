from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import sentry_sdk
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.api.errors import install_error_handlers
from app.api.middleware import request_id_middleware
from app.api.v1 import api_v1_router
from app.core.config import get_settings
from app.core.database import close_engine, init_engine
from app.core.logging import setup_logging
from app.core.redis import close_arq_pool, close_redis, init_arq_pool, init_redis
from app.openapi_examples import OPERATION_EXAMPLES, PARAMETER_EXAMPLES
from app.schemas.common import ErrorResponse

logger = structlog.get_logger()

_ERROR_RESPONSE_REF = "#/components/schemas/ErrorResponse"
_IDEMPOTENT_METHODS = {"post", "put", "patch", "delete"}
_OPENAPI_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
_COMMON_ERROR_RESPONSES = {
    "401": "UNAUTHORIZED",
    "403": "FORBIDDEN",
    "404": "NOT_FOUND",
    "409": "CONFLICT",
    "422": "VALIDATION_ERROR",
}


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL, json_output=settings.is_prod)

    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            environment=settings.ENV,
            integrations=[FastApiIntegration()],
        )

    init_engine()
    await init_redis()
    await init_arq_pool()
    logger.info("app.start", env=settings.ENV, version=settings.APP_VERSION)
    try:
        yield
    finally:
        await close_arq_pool()
        await close_redis()
        await close_engine()
        logger.info("app.stop")


def _generate_operation_id(route: APIRoute) -> str:
    if route.tags:
        return f"{route.tags[0]}_{route.name}"
    return route.name


def _error_response(description: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": {"$ref": _ERROR_RESPONSE_REF},
            },
        },
    }


def _request_id_header() -> dict[str, Any]:
    return {
        "description": "Request correlation id.",
        "schema": {"type": "string"},
    }


def _idempotency_key_parameter() -> dict[str, Any]:
    return {
        "name": "Idempotency-Key",
        "in": "header",
        "required": True,
        "schema": {"type": "string"},
        "description": "Required for mutating requests.",
    }


def _ensure_components(schema: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    components = schema.setdefault("components", {})
    if not isinstance(components, dict):
        components = {}
        schema["components"] = components
    schemas = components.setdefault("schemas", {})
    if not isinstance(schemas, dict):
        schemas = {}
        components["schemas"] = schemas
    return components, schemas


def _register_error_schemas(schemas: dict[str, Any]) -> None:
    error_schema = ErrorResponse.model_json_schema(ref_template="#/components/schemas/{model}")
    definitions = error_schema.pop("$defs", {})
    if isinstance(definitions, dict):
        schemas.update(definitions)
    schemas["ErrorResponse"] = error_schema


def _remove_fastapi_validation_schemas(schemas: dict[str, Any]) -> None:
    schemas.pop("HTTPValidationError", None)
    schemas.pop("ValidationError", None)


def _register_security(schema: dict[str, Any], components: dict[str, Any]) -> None:
    security_schemes = components.setdefault("securitySchemes", {})
    if not isinstance(security_schemes, dict):
        security_schemes = {}
        components["securitySchemes"] = security_schemes
    security_schemes["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    schema["security"] = [{"bearerAuth": []}, {}]


def _ensure_request_id_header(response: Any) -> None:
    if not isinstance(response, dict):
        return
    headers = response.setdefault("headers", {})
    if not isinstance(headers, dict):
        headers = {}
        response["headers"] = headers
    headers.setdefault("X-Request-Id", _request_id_header())


def _ensure_idempotency_key(operation: dict[str, Any]) -> None:
    parameters = operation.setdefault("parameters", [])
    if not isinstance(parameters, list):
        parameters = []
        operation["parameters"] = parameters

    for parameter in parameters:
        if (
            isinstance(parameter, dict)
            and parameter.get("in") == "header"
            and parameter.get("name") == "Idempotency-Key"
        ):
            parameter["required"] = True
            parameter["schema"] = {"type": "string"}
            parameter.setdefault("description", "Required for mutating requests.")
            return

    parameters.append(_idempotency_key_parameter())


def _ensure_operation_responses(operation: dict[str, Any]) -> None:
    responses = operation.setdefault("responses", {})
    if not isinstance(responses, dict):
        responses = {}
        operation["responses"] = responses

    for status_code, description in _COMMON_ERROR_RESPONSES.items():
        if status_code == "422" or status_code not in responses:
            responses[status_code] = _error_response(description)

    for response in responses.values():
        _ensure_request_id_header(response)


def _ensure_json_example(container: Any, value: Any) -> None:
    if not isinstance(container, dict):
        return
    content = container.get("content")
    if not isinstance(content, dict):
        return
    media = content.get("application/json")
    if not isinstance(media, dict):
        return
    examples = media.setdefault("examples", {})
    if not isinstance(examples, dict):
        examples = {}
        media["examples"] = examples
    examples.setdefault("default", {"summary": "Example", "value": value})


def _apply_parameter_examples(operation: dict[str, Any], operation_id: str) -> None:
    parameter_examples = PARAMETER_EXAMPLES.get(operation_id)
    if parameter_examples is None:
        return
    parameters = operation.get("parameters")
    if not isinstance(parameters, list):
        return
    for parameter in parameters:
        if not isinstance(parameter, dict):
            continue
        name = parameter.get("name")
        if isinstance(name, str) and name in parameter_examples:
            parameter.setdefault("example", parameter_examples[name])


def _apply_operation_examples(operation: dict[str, Any]) -> None:
    operation_id = operation.get("operationId")
    if not isinstance(operation_id, str):
        return
    examples = OPERATION_EXAMPLES.get(operation_id)
    if examples is None:
        _apply_parameter_examples(operation, operation_id)
        return

    request_example = examples.get("request")
    if request_example is not None:
        _ensure_json_example(operation.get("requestBody"), request_example)

    response_examples = examples.get("responses")
    responses = operation.get("responses")
    if isinstance(response_examples, dict) and isinstance(responses, dict):
        for status_code, response_example in response_examples.items():
            if isinstance(status_code, str):
                _ensure_json_example(responses.get(status_code), response_example)

    _apply_parameter_examples(operation, operation_id)


def _iter_operations(schema: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    paths = schema.get("paths", {})
    if not isinstance(paths, dict):
        return []

    operations: list[tuple[str, dict[str, Any]]] = []
    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            method_name = method.lower() if isinstance(method, str) else ""
            if method_name in _OPENAPI_METHODS and isinstance(operation, dict):
                operations.append((method_name, operation))
    return operations


def custom_openapi(app: FastAPI) -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    components, schemas = _ensure_components(schema)
    _register_error_schemas(schemas)
    _register_security(schema, components)

    for method, operation in _iter_operations(schema):
        _ensure_operation_responses(operation)
        if method in _IDEMPOTENT_METHODS:
            _ensure_idempotency_key(operation)
        _apply_operation_examples(operation)
    _remove_fastapi_validation_schemas(schemas)

    app.openapi_schema = schema
    return app.openapi_schema


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        generate_unique_id_function=_generate_operation_id,
        docs_url=None if settings.is_prod else "/docs",
        redoc_url=None if settings.is_prod else "/redoc",
        openapi_url=None if settings.is_prod else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(request_id_middleware)
    install_error_handlers(app)

    app.include_router(api_v1_router, prefix="/api/v1")
    app.openapi = lambda: custom_openapi(app)  # type: ignore[method-assign]
    return app


app = create_app()
