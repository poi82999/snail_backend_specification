import json
from datetime import datetime
from pathlib import Path

from build_owner_webapp_index import (
    ROOT,
    SPEC_TEXT_DIR,
    extract_front_sections,
    extract_spec_data_blocks,
    find_line,
    link_for_source,
    load_backend_data,
)


LLM_GUIDE_PATH = ROOT / "references" / "snail_llm_pipeline_integration_guide.md"
OUTPUT_DIR = ROOT / "outputs"
DOCS_DIR = ROOT / "docs"
INDEX_JSON_PATH = OUTPUT_DIR / "llm_pipeline_backend_index.json"
INDEX_HTML_PATH = OUTPUT_DIR / "llm_pipeline_backend_index.html"
SHARED_HTML_PATH = DOCS_DIR / "llm_pipeline_backend_index.html"
AI_TEXT_PATH = OUTPUT_DIR / "llm_pipeline_backend_index.ai.txt"
SHARED_AI_TEXT_PATH = DOCS_DIR / "llm_pipeline_backend_index.ai.txt"


EASY_FIELD_EXPLANATIONS = {
    "visibility": "이 디자인이나 샵을 고객에게 보여줄지 정하는 공개 상태입니다. draft는 임시저장, active는 공개, hidden은 숨김입니다.",
    "ai_analysis_status": "AI 분석이 어디까지 진행됐는지 보여주는 전체 상태입니다. 사장님 화면의 '분석 중/완료/실패' 표시 기준이 됩니다.",
    "ai_analysis_started_at": "AI 분석이 시작된 시각입니다. 분석이 오래 걸릴 때 몇 분째 처리 중인지 보여주는 데 씁니다.",
    "ai_analysis_completed_at": "AI 분석이 끝난 시각입니다. 성공뿐 아니라 최종 실패 시각을 남길 때도 씁니다.",
    "image_id": "이미지 한 장을 구분하는 고유 번호입니다. LLM 결과가 어느 이미지의 결과인지 맞추는 열쇠입니다.",
    "original_url": "사장님이 처음 올린 원본 사진의 저장 위치입니다. 나중에 재분석할 수 있도록 보관합니다.",
    "cropped_url": "LLM이 원본에서 손톱 부분만 잘라 만든 이미지의 저장 위치입니다. Classify 단계와 썸네일에 사용됩니다.",
    "ai_transform_status": "원본 사진에서 손톱 영역을 잘라내는 1단계가 성공했는지 실패했는지 나타냅니다.",
    "ai_classify_status": "잘라낸 이미지를 보고 태그와 색상을 뽑는 2단계가 성공했는지 실패했는지 나타냅니다.",
    "ai_tags": "LLM이 표준 태그 사전에서 골라준 디자인 태그입니다. 고객 검색과 필터에 직접 영향을 줍니다.",
    "ai_color_palette": "LLM이 판단한 대표 색상 목록입니다. 색상 필터와 추천에 사용됩니다.",
    "ai_style_category": "LLM이 판단한 디자인의 큰 스타일 분류입니다. 예: simple, glamour, trendy.",
    "owner_tags": "사장님이 직접 입력한 자유 태그입니다. LLM 태그와 별도로 보관해서 사장님 의도를 검색에 반영합니다.",
}


EASY_CONTRACT_FIELD_EXPLANATIONS = {
    "image_id": "백엔드와 LLM이 같은 이미지를 가리키기 위해 쓰는 고유 번호입니다.",
    "image_url": "LLM이 내려받아 분석할 이미지 파일 주소입니다.",
    "callback_url": "LLM 작업이 끝났을 때 결과를 되돌려줄 백엔드 주소입니다.",
    "options.output_size": "잘라낸 이미지의 목표 크기입니다. 예: 1080x1080.",
    "options.background": "잘라낸 이미지의 배경 처리 방식입니다. 예: 투명 배경.",
    "status": "작업 성공 여부입니다. success면 성공, failed면 실패입니다.",
    "cropped_image_url": "Transform 결과로 만들어진 손톱 영역 이미지 주소입니다.",
    "cropped_image_size": "Transform 결과 이미지의 실제 크기입니다.",
    "confidence": "Transform 결과를 모델이 얼마나 확신하는지 나타내는 점수입니다.",
    "nail_count_detected": "사진에서 감지한 손톱 개수입니다.",
    "processing_time_ms": "LLM 작업에 걸린 시간입니다. 밀리초 단위입니다.",
    "error_code": "실패했을 때 실패 이유를 기계가 읽을 수 있게 정한 코드입니다.",
    "error_message": "실패했을 때 사람이 읽을 수 있는 상세 설명입니다.",
    "locale": "결과 언어와 지역 기준입니다. 한국 서비스는 ko_KR을 사용합니다.",
    "options.max_tags": "LLM이 최대 몇 개의 태그를 돌려줄지 정합니다.",
    "options.include_color_palette": "대표 색상도 함께 받을지 정합니다.",
    "options.include_style_category": "큰 스타일 분류도 함께 받을지 정합니다.",
    "tags": "검색에 사용할 디자인 태그 목록입니다. 반드시 표준 태그 사전 안의 값이어야 합니다.",
    "color_palette": "디자인의 대표 색상 목록입니다.",
    "style_category": "디자인의 큰 스타일 분류입니다.",
    "nail_shape": "손톱 모양입니다. 현재 백엔드 저장 필드 추가 여부는 별도 결정이 필요합니다.",
    "confidence_overall": "Classify 결과 전체를 모델이 얼마나 확신하는지 나타내는 점수입니다.",
}


EASY_API_EXPLANATIONS = {
    "POST /owner/designs": "사장님이 새 디자인을 등록하는 버튼과 연결됩니다. 화면은 바로 등록 완료로 넘어가고, AI 분석은 뒤에서 따로 진행됩니다.",
    "GET /owner/designs": "사장님이 내 디자인 목록을 볼 때 사용합니다. 분석 중, 분석 실패, 숨김 같은 탭을 만들 때 필요합니다.",
    "GET /owner/designs/{design_id}": "디자인 하나의 상세 정보와 AI 분석 상태를 확인할 때 사용합니다.",
    "PATCH /owner/designs/{design_id}": "디자인 제목, 가격, 소요 시간, 태그 같은 정보를 수정할 때 사용합니다.",
    "POST /owner/designs/{design_id}/images": "기존 디자인에 사진을 추가할 때 사용합니다. 사진이 바뀌면 AI 분석도 다시 시작됩니다.",
    "DELETE /owner/designs/{design_id}/images/{image_id}": "디자인 사진을 삭제할 때 사용합니다. 사진이 바뀌므로 AI 분석이 다시 필요할 수 있습니다.",
    "POST /owner/designs/{design_id}/reanalyze": "분석이 실패했거나 다시 분석하고 싶을 때 누르는 '재분석' 버튼과 연결됩니다.",
}


STEP_PLAIN_LANGUAGE = {
    "flow": [
        "사장님이 디자인 사진을 올리면 백엔드는 먼저 저장만 하고 화면에 빠르게 응답합니다.",
        "그 뒤 백엔드가 LLM에게 사진 분석을 맡기고, LLM 결과가 돌아오면 디자인의 검색 태그와 노출 가능 상태를 업데이트합니다.",
        "즉, 사장님이 등록 버튼을 누르는 일과 AI 분석이 끝나는 일은 같은 순간에 일어나지 않습니다.",
    ],
    "transform": [
        "Transform은 원본 사진에서 손톱 부분만 보기 좋게 잘라내는 단계입니다.",
        "이 단계가 성공해야 다음 Classify 단계에서 색상과 스타일을 안정적으로 판단할 수 있습니다.",
        "실패하면 태그 분석으로 넘어가지 않고, 사장님에게 사진을 다시 올리거나 재분석하라는 동선을 보여줘야 합니다.",
    ],
    "classify": [
        "Classify는 잘라낸 손톱 이미지를 보고 검색에 필요한 태그와 색상을 붙이는 단계입니다.",
        "LLM이 아무 단어나 만들면 검색 필터와 맞지 않으므로, 정해진 표준 태그 사전 안에서만 골라야 합니다.",
        "이 결과가 고객이 '핑크', '프렌치', '봄' 같은 조건으로 검색할 때 사용됩니다.",
    ],
    "errors": [
        "LLM 실패는 단순 서버 오류뿐 아니라 사진 품질 문제일 수도 있습니다.",
        "백엔드는 실패 코드를 보고 사장님에게 '다시 촬영', '재분석', '잠시 후 재시도' 중 어떤 안내를 보여줄지 결정합니다.",
        "같은 failed라도 원인별로 다음 행동이 달라야 화면이 친절해집니다.",
    ],
    "dictionary": [
        "표준 태그 사전은 LLM이 사용할 수 있는 단어 목록입니다.",
        "이 목록 밖의 단어가 들어오면 고객 검색과 필터에서 빠질 수 있습니다.",
        "태그를 추가하거나 이름을 바꾸면 LLM, 백엔드 검색, 프론트 필터를 함께 업데이트해야 합니다.",
    ],
    "open-questions": [
        "이 항목들은 코드를 짜기 전에 팀끼리 먼저 정해야 하는 운영 규칙입니다.",
        "예를 들어 LLM 결과를 바로 받을지, 나중에 callback으로 받을지에 따라 백엔드 구조가 달라집니다.",
        "이미지 저장 주체와 신뢰도 기준도 나중에 바꾸기 어려우므로 초기에 합의해야 합니다.",
    ],
}


PIPELINE_MAP = [
    {
        "id": "flow",
        "title": "전체 처리 흐름",
        "summary": "사장님 디자인 이미지 업로드부터 LLM 분석 완료 후 유저 노출까지의 비동기 연결 흐름.",
        "source_needles": ["전체 흐름 요약"],
        "backend_files": ["spec_text/06_owner_design.md", "spec_text/12_llm.md", "spec_text/16_common_api_auth.md"],
        "entities": {
            "Design": [
                "visibility",
                "ai_analysis_status",
                "ai_analysis_started_at",
                "ai_analysis_completed_at",
            ],
            "DesignImage": [
                "original_url",
                "cropped_url",
                "ai_transform_status",
                "ai_classify_status",
            ],
        },
        "apis": {
            "owner_design": [
                "POST /owner/designs",
                "GET /owner/designs/{design_id}",
                "POST /owner/designs/{design_id}/images",
                "POST /owner/designs/{design_id}/reanalyze",
            ]
        },
        "guide": [
            "백엔드는 사장님 등록 요청에 즉시 응답하고, LLM 작업은 별도 큐에서 처리한다.",
            "사용자 노출은 `owner approved + shop active + design active + ai_analysis_status=done`이 모두 충족된 뒤 가능하다.",
            "이미지 변경 또는 재분석 요청은 `ai_analysis_status=pending`으로 되돌리고 Transform부터 다시 태운다.",
        ],
        "checkpoints": [
            "LLM 처리 시간이 10초 이상이면 동기 응답 대신 callback/webhook 구조로 고정한다.",
            "사장님 화면의 분석 중 상태는 pending/in_progress를 하나로 묶어 보여준다.",
            "원본 이미지는 재처리와 감사 추적을 위해 보관한다.",
        ],
    },
    {
        "id": "transform",
        "title": "1단계 Transform 계약",
        "summary": "원본 이미지에서 네일 영역을 추출하고 규격화된 cropped 이미지를 반환하는 계약.",
        "source_needles": ["1단계: Transform"],
        "contract_key": "transform",
        "backend_files": ["spec_text/06_owner_design.md", "spec_text/12_llm.md"],
        "entities": {
            "Design": ["ai_analysis_status"],
            "DesignImage": ["image_id", "original_url", "cropped_url", "ai_transform_status"],
        },
        "apis": {
            "owner_design": [
                "POST /owner/designs",
                "POST /owner/designs/{design_id}/images",
                "POST /owner/designs/{design_id}/reanalyze",
            ]
        },
        "guide": [
            "`image_id`는 백엔드의 `DesignImage.image_id`와 1:1로 맞춘다.",
            "`image_url`은 백엔드가 보관한 원본 이미지 URL이며, LLM은 이 URL에서 원본을 내려받아 처리한다.",
            "성공 시 `cropped_image_url`을 `DesignImage.cropped_url`에 저장하고 `ai_transform_status=done`으로 변경한다.",
        ],
        "checkpoints": [
            "`cropped_image_url`의 저장 주체와 URL 만료 정책을 먼저 확정해야 한다.",
            "Transform 실패는 Classify로 넘기지 않고 해당 이미지 또는 디자인 분석 상태를 failed로 종료한다.",
            "confidence 기준값이 낮으면 재촬영 요구 또는 수동 검수로 보내는 정책이 필요하다.",
        ],
    },
    {
        "id": "classify",
        "title": "2단계 Classify 계약",
        "summary": "cropped 이미지를 분석해 검색/필터에 쓰는 태그, 색상, 스타일, 손톱 모양을 반환하는 계약.",
        "source_needles": ["2단계: Classify"],
        "contract_key": "classify",
        "backend_files": ["spec_text/06_owner_design.md", "spec_text/12_llm.md"],
        "entities": {
            "Design": ["ai_tags", "ai_color_palette", "ai_style_category", "ai_analysis_status"],
            "DesignImage": ["image_id", "cropped_url", "ai_classify_status"],
        },
        "apis": {
            "owner_design": [
                "GET /owner/designs/{design_id}",
                "POST /owner/designs/{design_id}/reanalyze",
            ]
        },
        "guide": [
            "LLM이 반환하는 `tags`는 백엔드의 `Design.ai_tags`로 저장한다.",
            "`color_palette`는 `Design.ai_color_palette`, `style_category`는 `Design.ai_style_category`로 저장한다.",
            "Classify 결과는 표준 태그 사전 값만 사용해야 검색 누락을 피할 수 있다.",
        ],
        "checkpoints": [
            "디자인 이미지가 여러 장일 때 이미지별 결과를 어떻게 병합할지 정책이 필요하다.",
            "`confidence_overall` 기준 미만일 때 failed 처리할지, 낮은 신뢰도 태그만 제외할지 정해야 한다.",
            "모델 버전이 바뀌면 기존 디자인 재분석 필요 여부를 결정해야 한다.",
        ],
    },
    {
        "id": "errors",
        "title": "에러 처리와 사장님 안내",
        "summary": "LLM 실패 응답을 백엔드 상태와 사장님 화면 안내 문구로 연결하는 규칙.",
        "source_needles": ["에러 처리 가이드"],
        "backend_files": ["spec_text/06_owner_design.md", "spec_text/12_llm.md", "spec_text/13_notifications.md"],
        "entities": {
            "Design": ["ai_analysis_status", "ai_analysis_completed_at"],
            "DesignImage": ["ai_transform_status", "ai_classify_status"],
        },
        "apis": {
            "owner_design": [
                "GET /owner/designs",
                "GET /owner/designs/{design_id}",
                "POST /owner/designs/{design_id}/reanalyze",
            ]
        },
        "guide": [
            "`status=failed`와 `error_code`를 기준으로 DB 상태와 사장님 화면 문구를 분기한다.",
            "최종 실패 후에는 사장님 화면에서 재분석 버튼 또는 사진 교체 동선을 제공한다.",
            "재시도 가능한 내부 오류와 재촬영이 필요한 품질 오류는 분리해서 다룬다.",
        ],
        "checkpoints": [
            "`INTERNAL_ERROR`는 자동 재시도 대상이 될 수 있지만 `NO_NAIL`, `INAPPROPRIATE`는 재시도보다 사용자 조치가 우선이다.",
            "실패 알림을 보낼지, 사장님 디자인 목록에서만 표시할지 제품 정책을 확정한다.",
        ],
    },
    {
        "id": "dictionary",
        "title": "표준 태그 사전",
        "summary": "Classify 결과가 반드시 따라야 하는 enum/태그 사전과 백엔드 저장 필드.",
        "source_needles": ["부록 A: 표준 태그 사전"],
        "backend_files": ["spec_text/06_owner_design.md", "spec_text/12_llm.md", "spec_text/14_decisions.md"],
        "entities": {
            "Design": ["owner_tags", "ai_tags", "ai_color_palette", "ai_style_category"],
        },
        "apis": {
            "owner_design": [
                "POST /owner/designs",
                "PATCH /owner/designs/{design_id}",
            ]
        },
        "guide": [
            "`owner_tags`는 사장님 자유 입력, `ai_tags`는 LLM 표준 사전 기반 자동 태그로 분리한다.",
            "LLM이 사전에 없는 단어를 보내면 DB 검색/필터에서 누락될 수 있으므로 백엔드 검증이 필요하다.",
            "태그 사전 변경은 프론트 필터, 검색 인덱스, 모델 프롬프트를 같이 업데이트한다.",
        ],
        "checkpoints": [
            "`nail_shape`는 현재 `Design` 저장 필드에 명시되어 있지 않다. 저장이 필요하면 필드를 추가하거나 표시 제외 정책을 정해야 한다.",
            "Classify output의 `tags`는 style/technique/mood/occasion을 하나의 배열로 합치는 구조다.",
        ],
    },
    {
        "id": "open-questions",
        "title": "결정 필요 항목",
        "summary": "LLM 작업 시작 전에 백엔드와 맞춰야 하는 운영 계약.",
        "source_needles": ["백엔드 팀의 질문"],
        "backend_files": ["spec_text/12_llm.md", "spec_text/14_decisions.md", "spec_text/16_common_api_auth.md"],
        "entities": {
            "Design": ["ai_analysis_status"],
            "DesignImage": ["original_url", "cropped_url"],
        },
        "apis": {},
        "guide": [
            "동기/비동기, callback 인증, 이미지 저장 주체, confidence 기준값은 API 구현 전에 확정한다.",
            "LLM callback을 시스템 actor로 볼 경우 인증 방식과 재시도 중복 처리 idempotency가 필요하다.",
            "운영 중 모델이 업데이트될 때 `model_version`을 응답에 포함하면 재분석 판단이 쉬워진다.",
        ],
        "checkpoints": [
            "callback을 쓴다면 동일 `image_id` 결과가 중복 도착해도 DB가 깨지지 않아야 한다.",
            "LLM이 제공한 임시 URL 만료 전에 백엔드가 이미지를 소유 스토리지로 옮기는지 결정한다.",
        ],
    },
]


def load_llm_spec():
    path = SPEC_TEXT_DIR / "12_llm.md"
    for block in extract_spec_data_blocks(path):
        if "llm" in block:
            return block["llm"]
    raise RuntimeError("spec_text/12_llm.md에서 llm spec-data를 찾을 수 없습니다.")


def source_refs_for(sections, needles):
    refs = []
    used = set()
    for needle in needles:
        for section in sections:
            key = (section["title"], section["line"])
            if key in used:
                continue
            if needle in section["title"]:
                rel = LLM_GUIDE_PATH.relative_to(ROOT).as_posix()
                refs.append({**section, "href": link_for_source(rel, section["line"])})
                used.add(key)
    return refs


def file_refs_for(paths):
    refs = []
    for rel in paths:
        path = ROOT / rel
        refs.append(
            {
                "source_file": rel,
                "title": rel,
                "line": 1,
                "href": link_for_source(rel, 1) if path.exists() else "",
            }
        )
    return refs


def resolve_field_refs(mapping, backend):
    refs = []
    missing = []
    for entity, fields in mapping.get("entities", {}).items():
        entity_data = backend["entities"].get(entity)
        if not entity_data:
            missing.append(f"entity:{entity}")
            continue
        for field in fields:
            field_data = entity_data["fields"].get(field)
            if not field_data:
                missing.append(f"field:{entity}.{field}")
                continue
            refs.append(
                {
                    **field_data,
                    "entity": entity,
                    "href": link_for_source(field_data["source_file"], field_data["line"]),
                    "easy_note": EASY_FIELD_EXPLANATIONS.get(field, field_data["note"]),
                }
            )
    return refs, missing


def resolve_api_refs(mapping, backend):
    refs = []
    missing = []
    for group, endpoints in mapping.get("apis", {}).items():
        group_data = backend["apis"].get(group)
        if not group_data:
            missing.append(f"api_group:{group}")
            continue
        for endpoint in endpoints:
            api_data = group_data["items"].get(endpoint)
            if not api_data:
                missing.append(f"api:{group}:{endpoint}")
                continue
            refs.append(
                {
                    **api_data,
                    "group": group,
                    "href": link_for_source(api_data["source_file"], api_data["line"]),
                    "easy_purpose": EASY_API_EXPLANATIONS.get(endpoint, api_data["purpose"]),
                }
            )
    return refs, missing


def contract_from_llm_spec(llm_spec, key):
    if not key:
        return None
    contract = llm_spec.get(key, {})
    source_file = "spec_text/12_llm.md"
    return {
        "purpose": contract.get("purpose", ""),
        "endpoint": contract.get("suggested_endpoint", ""),
        "request_fields": [
            {
                "name": field,
                "href": link_for_source(source_file, find_line(ROOT / source_file, f'"{field}"')),
                "meaning": EASY_CONTRACT_FIELD_EXPLANATIONS.get(field, ""),
            }
            for field in contract.get("request_fields", [])
        ],
        "response_fields": [
            {
                "name": field,
                "href": link_for_source(source_file, find_line(ROOT / source_file, f'"{field}"')),
                "meaning": EASY_CONTRACT_FIELD_EXPLANATIONS.get(field, ""),
            }
            for field in contract.get("response_fields", [])
        ],
        "recommendation": contract.get("recommendation", ""),
        "source_file": source_file,
        "href": link_for_source(source_file, find_line(ROOT / source_file, f'"{key}"')),
    }


def resolve_step(mapping, backend, llm_spec, source_sections):
    field_refs, missing_fields = resolve_field_refs(mapping, backend)
    api_refs, missing_apis = resolve_api_refs(mapping, backend)
    source_refs = source_refs_for(source_sections, mapping["source_needles"])
    source_missing = [needle for needle in mapping["source_needles"] if not any(needle in ref["title"] for ref in source_refs)]
    total_expected = (
        sum(len(fields) for fields in mapping.get("entities", {}).values())
        + sum(len(endpoints) for endpoints in mapping.get("apis", {}).values())
        + len(mapping["source_needles"])
    )
    found = len(field_refs) + len(api_refs) + len(mapping["source_needles"]) - len(source_missing)
    missing = missing_fields + missing_apis + [f"source_section:{item}" for item in source_missing]
    coverage = 1.0 if total_expected == 0 else found / total_expected
    return {
        **mapping,
        "plain_language": STEP_PLAIN_LANGUAGE.get(mapping["id"], []),
        "contract": contract_from_llm_spec(llm_spec, mapping.get("contract_key")),
        "source_refs": source_refs,
        "file_refs": file_refs_for(mapping.get("backend_files", [])),
        "field_refs": field_refs,
        "api_refs": api_refs,
        "missing_refs": missing,
        "coverage": round(coverage, 3),
        "status": "needs_attention" if missing else "connected",
    }


def flatten_backend(backend):
    fields = []
    for entity, entity_data in sorted(backend["entities"].items()):
        for field in entity_data["fields"].values():
            fields.append(
                {
                    **field,
                    "entity": entity,
                    "href": link_for_source(field["source_file"], field["line"]),
                    "easy_note": EASY_FIELD_EXPLANATIONS.get(field["name"], field["note"]),
                }
            )

    apis = []
    for group, group_data in sorted(backend["apis"].items()):
        for api in group_data["items"].values():
            apis.append(
                {
                    **api,
                    "group": group,
                    "href": link_for_source(api["source_file"], api["line"]),
                    "easy_purpose": EASY_API_EXPLANATIONS.get(api["endpoint"], api["purpose"]),
                }
            )

    return fields, apis


def clip_text(value, limit=160):
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def build_ai_brief(index):
    llm_spec = index["llm_spec"]
    lines = [
        "# AI 작업용 요약: LLM 파이프라인 ↔ 백엔드",
        "",
        "이 텍스트는 HTML 전체를 AI 코딩 도구에 붙여넣는 대신 사용할 압축 컨텍스트입니다.",
        "목표: LLM Transform/Classify 작업자와 백엔드 담당자가 같은 입출력 계약, 저장 필드, 실패 처리 규칙을 기준으로 구현하게 합니다.",
        "",
        "전체 흐름:",
        "1. 사장님이 디자인 원본 이미지를 업로드합니다.",
        "2. 백엔드는 원본 이미지를 저장하고 LLM Transform을 요청합니다.",
        "3. Transform은 손톱 영역을 잘라 cropped 이미지를 만듭니다.",
        "4. 백엔드는 cropped 이미지로 Classify를 요청합니다.",
        "5. Classify는 표준 태그/색상/스타일을 반환합니다.",
        "6. 백엔드는 결과를 Design/DesignImage 필드에 저장하고, 조건 충족 시 고객에게 노출합니다.",
        "",
        "공통 원칙:",
        "- image_id는 백엔드 DesignImage.image_id와 LLM 결과를 맞추는 키입니다.",
        "- status는 success 또는 failed를 사용합니다. failed이면 error_code를 반드시 보냅니다.",
        "- Classify의 tags/color/style은 표준 태그 사전 값만 반환합니다.",
        "- 10초 이상 걸리면 동기 응답보다 callback/webhook 구조를 권장합니다.",
        "- 이미지 저장 주체, callback 인증, confidence 실패 기준은 구현 전 합의해야 합니다.",
        "",
        "단계별 구현 컨텍스트:",
    ]

    for step in index["steps"]:
        lines.extend(["", f"## {step['title']}", f"요약: {step['summary']}"])
        if step.get("plain_language"):
            lines.append("쉽게 말하면:")
            lines.extend(f"- {row}" for row in step["plain_language"])
        if step.get("guide"):
            lines.append("구현 가이드:")
            lines.extend(f"- {row}" for row in step["guide"])
        if step.get("checkpoints"):
            lines.append("체크포인트:")
            lines.extend(f"- {row}" for row in step["checkpoints"])
        if step.get("contract"):
            contract = step["contract"]
            lines.append(f"Endpoint: {contract['endpoint']}")
            lines.append("Request fields:")
            lines.extend(f"- {field['name']}: {field.get('meaning') or '-'}" for field in contract["request_fields"])
            lines.append("Response fields:")
            lines.extend(f"- {field['name']}: {field.get('meaning') or '-'}" for field in contract["response_fields"])
        if step.get("field_refs"):
            field_names = ", ".join(f"{ref['entity']}.{ref['name']}" for ref in step["field_refs"])
            lines.append(f"관련 백엔드 필드: {field_names}")
        if step.get("api_refs"):
            lines.append("관련 백엔드 API:")
            lines.extend(
                f"- {ref['endpoint']}: {clip_text(ref.get('easy_purpose') or ref.get('purpose'), 120)}"
                for ref in step["api_refs"]
            )

    lines.extend(["", "에러 코드:"])
    for code, meaning, owner_message in llm_spec.get("error_codes", []):
        lines.append(f"- {code}: {meaning} / 사장님 안내: {owner_message}")

    lines.extend(["", "표준 태그 사전:"])
    for key, values in llm_spec.get("standard_tags", {}).items():
        lines.append(f"- {key}: {', '.join(values)}")

    lines.extend(["", "논의 필요 질문:"])
    lines.extend(f"- {row}" for row in llm_spec.get("worker_questions", []))

    return "\n".join(lines).strip() + "\n"


def build_index():
    if not LLM_GUIDE_PATH.exists():
        raise FileNotFoundError(f"LLM 연동 가이드를 찾을 수 없습니다: {LLM_GUIDE_PATH}")
    source_sections = extract_front_sections(LLM_GUIDE_PATH)
    backend = load_backend_data()
    llm_spec = load_llm_spec()
    steps = [resolve_step(item, backend, llm_spec, source_sections) for item in PIPELINE_MAP]
    all_fields, all_apis = flatten_backend(backend)
    dictionary = llm_spec.get("standard_tags", {})
    dictionary_terms = sum(len(values) for values in dictionary.values())
    contract_field_count = 0
    for key in ("transform", "classify"):
        contract = llm_spec.get(key, {})
        contract_field_count += len(contract.get("request_fields", [])) + len(contract.get("response_fields", []))

    index = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": {
            "llm_guide": LLM_GUIDE_PATH.relative_to(ROOT).as_posix(),
            "backend_spec_dir": SPEC_TEXT_DIR.relative_to(ROOT).as_posix(),
        },
        "stats": {
            "pipeline_sections": len(steps),
            "contract_fields": contract_field_count,
            "error_codes": len(llm_spec.get("error_codes", [])),
            "dictionary_terms": dictionary_terms,
            "related_fields": sum(len(step["field_refs"]) for step in steps),
            "related_apis": sum(len(step["api_refs"]) for step in steps),
            "attention_sections": sum(1 for step in steps if step["status"] != "connected"),
        },
        "steps": steps,
        "llm_spec": llm_spec,
        "backend": {
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
  <title>LLM 파이프라인 ↔ 백엔드 명세 인덱스</title>
  <style>
    :root {
      --bg: #f6f7f9;
      --panel: #ffffff;
      --line: #d7dde6;
      --text: #17202a;
      --muted: #667485;
      --accent: #0f766e;
      --accent-weak: #e7f4f1;
      --blue: #1d4ed8;
      --blue-weak: #edf3ff;
      --warn: #9a3412;
      --warn-weak: #fff4e8;
      --green: #166534;
      --green-weak: #ecfdf3;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, "Malgun Gothic", sans-serif;
      font-size: 14px;
    }
    header {
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      padding: 16px 22px;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
    }
    h1 { margin: 0 0 5px; font-size: 20px; letter-spacing: 0; }
    h2 { margin: 0 0 6px; font-size: 22px; letter-spacing: 0; }
    h3 { margin: 18px 0 8px; font-size: 15px; letter-spacing: 0; }
    a { color: var(--blue); text-decoration: none; }
    a:hover { text-decoration: underline; }
    code {
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      background: #f1f5f9;
      border-radius: 4px;
      padding: 1px 4px;
    }
    main {
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      min-height: calc(100vh - 84px);
    }
    aside {
      background: var(--panel);
      border-right: 1px solid var(--line);
      padding: 16px;
      overflow: auto;
    }
    .content { padding: 18px 22px 36px; overflow: auto; }
    .meta { color: var(--muted); font-size: 12px; line-height: 1.45; }
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
      min-width: 92px;
      border: 1px solid var(--line);
      background: #fafbfc;
      border-radius: 6px;
      padding: 7px 10px;
    }
    .stat b { display: block; font-size: 16px; }
    .help-box {
      border: 1px solid #bfdbfe;
      background: var(--blue-weak);
      color: #1e3a8a;
      border-radius: 6px;
      padding: 10px;
      line-height: 1.5;
      margin-bottom: 12px;
      font-size: 12px;
    }
    input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      font: inherit;
      margin-bottom: 10px;
    }
    button {
      width: 100%;
      text-align: left;
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 6px;
      padding: 10px;
      font: inherit;
      cursor: pointer;
    }
    button:hover { border-color: var(--accent); }
    button.active { border-color: var(--accent); background: var(--accent-weak); }
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
    .step-list { display: grid; gap: 8px; }
    .step-title { font-weight: 700; margin-bottom: 5px; }
    .step-summary { color: var(--muted); font-size: 12px; line-height: 1.45; }
    .chips { display: flex; gap: 5px; flex-wrap: wrap; margin-top: 8px; }
    .chip {
      display: inline-flex;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      color: var(--muted);
      min-height: 20px;
      padding: 2px 7px;
      font-size: 11px;
      line-height: 16px;
    }
    .chip.good { color: var(--green); background: var(--green-weak); border-color: #bbf7d0; }
    .chip.warn { color: var(--warn); background: var(--warn-weak); border-color: #fed7aa; }
    .detail-header {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      margin-bottom: 14px;
    }
    .summary { color: var(--muted); line-height: 1.55; max-width: 920px; }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      min-width: 0;
    }
    .panel.full { grid-column: 1 / -1; }
    table {
      width: 100%;
      border-collapse: collapse;
      background: #fff;
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
    }
    tr:last-child td { border-bottom: 0; }
    ul { margin: 0; padding-left: 18px; }
    li { margin: 4px 0; }
    .excerpt {
      white-space: pre-wrap;
      border: 1px solid var(--line);
      background: #fbfcfe;
      border-radius: 6px;
      padding: 10px;
      max-height: 280px;
      overflow: auto;
      line-height: 1.55;
      color: #2d3a4a;
    }
    .plain {
      border: 1px solid #cde7df;
      background: #f0faf7;
      border-radius: 6px;
      padding: 10px;
      line-height: 1.55;
      color: #164e45;
    }
    .plain ul { margin-top: 4px; }
    .index-results {
      display: grid;
      gap: 6px;
      margin-top: 8px;
      max-height: 260px;
      overflow: auto;
    }
    .result-row {
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 6px;
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
      .detail-header { display: block; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>LLM 파이프라인 ↔ 백엔드 명세 인덱스</h1>
      <div class="meta" id="generatedMeta"></div>
    </div>
    <div class="header-right">
      <div class="stats" id="stats"></div>
      <div class="actions">
        <button class="copy-btn" id="copyAiBriefBtn" type="button">AI 요약 복사</button>
        <a class="text-link" href="llm_pipeline_backend_index.ai.txt">AI용 TXT 열기</a>
        <span class="meta" id="copyAiBriefStatus"></span>
      </div>
    </div>
  </header>
  <main>
    <aside>
      <div class="help-box">
        <b>LLM 작업자 분석 순서</b><br>
        1. 왼쪽 단계 선택<br>
        2. Input/Output 계약 확인<br>
        3. 백엔드 저장 필드/API 출처 확인<br>
        4. 에러 코드와 표준 태그 사전 확인
      </div>
      <input id="filterInput" type="search" placeholder="단계, 필드, API 검색">
      <div class="step-list" id="stepList"></div>
      <h3>전체 백엔드 검색</h3>
      <input id="globalSearch" type="search" placeholder="예: ai_tags, cropped_url, /owner/designs">
      <div class="index-results" id="globalResults"></div>
    </aside>
    <section class="content" id="detail"></section>
  </main>
  <script id="index-data" type="application/json">__INDEX_DATA__</script>
  <script>
    const data = JSON.parse(document.getElementById("index-data").textContent);
    let currentId = data.steps[0]?.id || "";

    const escapeHtml = (value) => String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

    const link = (href, label) => href ? `<a href="${escapeHtml(href)}">${escapeHtml(label)}</a>` : escapeHtml(label);
    const statusLabel = (item) => item.status === "connected" ? "연결됨" : "확인 필요";
    const statusClass = (item) => item.status === "connected" ? "good" : "warn";
    const sourceLink = (ref) => link(ref.href, `${ref.source_file || ref.title}${ref.line ? ":" + ref.line : ""}`);

    function renderStats() {
      document.getElementById("generatedMeta").textContent =
        `${data.source.llm_guide} / ${data.source.backend_spec_dir} / ${data.generated_at}`;
      const rows = [
        ["단계", data.stats.pipeline_sections],
        ["계약 필드", data.stats.contract_fields],
        ["에러", data.stats.error_codes],
        ["태그", data.stats.dictionary_terms],
        ["확인 필요", data.stats.attention_sections],
      ];
      document.getElementById("stats").innerHTML = rows
        .map(([label, value]) => `<div class="stat"><b>${value}</b>${label}</div>`)
        .join("");
    }

    function stepSearchText(step) {
      return [
        step.id,
        step.title,
        step.summary,
        ...(step.guide || []),
        ...(step.checkpoints || []),
        ...(step.field_refs || []).map((ref) => `${ref.entity} ${ref.name} ${ref.note}`),
        ...(step.api_refs || []).map((ref) => `${ref.endpoint} ${ref.purpose} ${ref.params}`),
        step.contract?.endpoint || "",
      ].join(" ").toLowerCase();
    }

    function renderList() {
      const q = document.getElementById("filterInput").value.trim().toLowerCase();
      const items = data.steps.filter((step) => !q || stepSearchText(step).includes(q));
      document.getElementById("stepList").innerHTML = items.map((step) => `
        <button class="${step.id === currentId ? "active" : ""}" data-id="${escapeHtml(step.id)}">
          <div class="step-title">${escapeHtml(step.title)}</div>
          <div class="step-summary">${escapeHtml(step.summary)}</div>
          <div class="chips">
            <span class="chip ${statusClass(step)}">${statusLabel(step)}</span>
            <span class="chip">필드 ${step.field_refs.length}</span>
            <span class="chip">API ${step.api_refs.length}</span>
          </div>
        </button>
      `).join("");
      document.querySelectorAll("#stepList button").forEach((button) => {
        button.addEventListener("click", () => {
          currentId = button.dataset.id;
          renderList();
          renderDetail();
        });
      });
      if (!items.some((step) => step.id === currentId) && items[0]) {
        currentId = items[0].id;
        renderList();
        renderDetail();
      }
    }

    function renderContract(contract) {
      if (!contract) return `<div class="meta">이 단계는 별도 endpoint 계약 없음</div>`;
      const requestRows = contract.request_fields.map((field) => `
        <tr><td>${link(field.href, field.name)}</td><td>${escapeHtml(field.meaning || "-")}</td></tr>
      `).join("");
      const responseRows = contract.response_fields.map((field) => `
        <tr><td>${link(field.href, field.name)}</td><td>${escapeHtml(field.meaning || "-")}</td></tr>
      `).join("");
      return `
        <table>
          <tbody>
            <tr><th>Endpoint</th><td><code>${escapeHtml(contract.endpoint)}</code></td></tr>
            <tr><th>Purpose</th><td>${escapeHtml(contract.purpose)}</td></tr>
            <tr><th>Recommendation</th><td>${escapeHtml(contract.recommendation || "-")}</td></tr>
            <tr><th>Source</th><td>${link(contract.href, contract.source_file)}</td></tr>
          </tbody>
        </table>
        <h3>백엔드가 LLM에게 보내는 값</h3>
        <table><thead><tr><th>필드</th><th>쉽게 말하면</th></tr></thead><tbody>${requestRows}</tbody></table>
        <h3>LLM이 백엔드에게 돌려주는 값</h3>
        <table><thead><tr><th>필드</th><th>쉽게 말하면</th></tr></thead><tbody>${responseRows}</tbody></table>
      `;
    }

    function renderDictionary() {
      return Object.entries(data.llm_spec.standard_tags || {}).map(([key, values]) => `
        <tr>
          <td><code>${escapeHtml(key)}</code></td>
          <td><div class="chips">${values.map((value) => `<span class="chip">${escapeHtml(value)}</span>`).join("")}</div></td>
        </tr>
      `).join("");
    }

    function renderErrors() {
      return (data.llm_spec.error_codes || []).map((row) => `
        <tr><td><code>${escapeHtml(row[0])}</code></td><td>${escapeHtml(row[1])}</td><td>${escapeHtml(row[2])}</td></tr>
      `).join("");
    }

    function renderDetail() {
      const step = data.steps.find((entry) => entry.id === currentId) || data.steps[0];
      if (!step) return;
      const guide = step.guide?.length
        ? `<ul>${step.guide.map((row) => `<li>${escapeHtml(row)}</li>`).join("")}</ul>`
        : `<div class="meta">등록된 가이드 없음</div>`;
      const plain = step.plain_language?.length
        ? `<div class="plain"><b>쉽게 말하면</b><ul>${step.plain_language.map((row) => `<li>${escapeHtml(row)}</li>`).join("")}</ul></div>`
        : "";
      const checkpoints = step.checkpoints?.length
        ? `<ul>${step.checkpoints.map((row) => `<li>${escapeHtml(row)}</li>`).join("")}</ul>`
        : `<div class="meta">등록된 체크포인트 없음</div>`;
      const sourceRows = step.source_refs.map((ref) => `
        <tr><td>${link(ref.href, ref.title)}</td><td>${escapeHtml(ref.line)}</td></tr>
      `).join("");
      const fileRows = step.file_refs.map((ref) => `
        <tr><td>${sourceLink(ref)}</td></tr>
      `).join("");
      const fieldRows = step.field_refs.map((ref) => `
        <tr>
          <td><code>${escapeHtml(ref.entity)}.${escapeHtml(ref.name)}</code></td>
          <td>${escapeHtml(ref.easy_note)}</td>
          <td>${escapeHtml(ref.note)}</td>
          <td>${sourceLink(ref)}</td>
        </tr>
      `).join("");
      const apiRows = step.api_refs.map((ref) => `
        <tr>
          <td><code>${escapeHtml(ref.endpoint)}</code><div class="meta">${escapeHtml(ref.group)}</div></td>
          <td>${escapeHtml(ref.easy_purpose)}</td>
          <td>${escapeHtml(ref.purpose)}</td>
          <td>${escapeHtml(ref.params)}</td>
          <td>${sourceLink(ref)}</td>
        </tr>
      `).join("");
      const missing = step.missing_refs?.length
        ? `<div class="panel full"><h3>확인 필요</h3><ul>${step.missing_refs.map((row) => `<li><code>${escapeHtml(row)}</code></li>`).join("")}</ul></div>`
        : "";
      const excerpt = step.source_refs.map((ref) => `# ${ref.title}\\n${ref.excerpt}`).join("\\n\\n");
      const questions = (data.llm_spec.worker_questions || []).map((row) => `<li>${escapeHtml(row)}</li>`).join("");

      document.getElementById("detail").innerHTML = `
        <div class="detail-header">
          <div>
            <h2>${escapeHtml(step.title)}</h2>
            <div class="summary">${escapeHtml(step.summary)}</div>
          </div>
          <span class="chip ${statusClass(step)}">${statusLabel(step)} · ${Math.round(step.coverage * 100)}%</span>
        </div>
        <div class="grid">
          <div class="panel full"><h3>이 단계의 의미</h3>${plain}</div>
          <div class="panel full"><h3>LLM 작업자 구현 가이드</h3>${guide}</div>
          <div class="panel full"><h3>Input / Output 계약</h3>${renderContract(step.contract)}</div>
          <div class="panel"><h3>체크포인트</h3>${checkpoints}</div>
          <div class="panel"><h3>원문/백엔드 출처</h3>
            <table><thead><tr><th>LLM 가이드 섹션</th><th>라인</th></tr></thead><tbody>${sourceRows || "<tr><td colspan='2'>연결된 원문 섹션 없음</td></tr>"}</tbody></table>
            <h3>백엔드 파일</h3>
            <table><tbody>${fileRows || "<tr><td>연결된 파일 없음</td></tr>"}</tbody></table>
          </div>
          ${missing}
          <div class="panel full"><h3>관련 백엔드 필드</h3><table><thead><tr><th>필드</th><th>쉽게 말하면</th><th>원문 메모</th><th>출처</th></tr></thead><tbody>${fieldRows || "<tr><td colspan='4'>관련 필드 없음</td></tr>"}</tbody></table></div>
          <div class="panel full"><h3>관련 백엔드 API</h3><table><thead><tr><th>엔드포인트</th><th>쉽게 말하면</th><th>원문 용도</th><th>요청값</th><th>출처</th></tr></thead><tbody>${apiRows || "<tr><td colspan='5'>관련 API 없음</td></tr>"}</tbody></table></div>
          <div class="panel full"><h3>에러 코드</h3><table><thead><tr><th>코드</th><th>의미</th><th>사장님 안내</th></tr></thead><tbody>${renderErrors()}</tbody></table></div>
          <div class="panel full"><h3>표준 태그 사전</h3><table><thead><tr><th>분류</th><th>허용값</th></tr></thead><tbody>${renderDictionary()}</tbody></table></div>
          <div class="panel full"><h3>백엔드-LLM 논의 질문</h3><ul>${questions}</ul></div>
          <div class="panel full"><h3>LLM 가이드 원문 발췌</h3><div class="excerpt">${escapeHtml(excerpt || "발췌 없음")}</div></div>
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
          const easy = item.endpoint ? item.easy_purpose : item.easy_note;
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
    print(f"sections: {index['stats']['pipeline_sections']}")
    print(f"contract_fields: {index['stats']['contract_fields']}")
    print(f"error_codes: {index['stats']['error_codes']}")
    print(f"dictionary_terms: {index['stats']['dictionary_terms']}")
    print(f"attention_sections: {index['stats']['attention_sections']}")


if __name__ == "__main__":
    main()
