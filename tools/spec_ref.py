"""spec_ref.py – 템플릿 참조 해석 + Drift Detection 엔진.

사용법:
  1) 빌드 시: resolve_all_refs(text, backend) 로 {api:...} 등을 실제 값으로 치환
  2) 검증 시: validate_playbook_refs(playbooks, guides, backend) 로 하드코딩 참조 점검

템플릿 문법:
  {api:GROUP:KEYWORD}        → spec JSON의 apis[GROUP]에서 KEYWORD를 포함하는 endpoint
  {field:ENTITY:FIELD_NAME}  → spec JSON의 entities[ENTITY].fields[FIELD_NAME].type
  {enum:ENTITY:FIELD_NAME}   → spec JSON의 entities[ENTITY].fields[FIELD_NAME].note (enum 값)
  {error:CODE}               → error codes에서 CODE 존재 확인 후 그대로 반환
"""

import re
import sys
from difflib import get_close_matches


# ---------------------------------------------------------------------------
# 1) 에러 코드 목록 (16_common_api_auth.md 에서 추출하여 캐싱)
# ---------------------------------------------------------------------------

_KNOWN_ERROR_CODES = {
    "UNAUTHORIZED", "FORBIDDEN", "VERIFICATION_REQUIRED",
    "NOT_FOUND", "VALIDATION_ERROR", "CONFLICT",
    "RATE_LIMITED", "INTERNAL_ERROR",
}


def _load_error_codes(backend):
    """backend_data 로부터 에러 코드 목록을 추출한다."""
    codes = set(_KNOWN_ERROR_CODES)
    # 만약 backend_data에 추가 에러코드가 있으면 병합
    for group_data in backend.get("apis", {}).values():
        for item in group_data.get("items", {}).values():
            note = item.get("purpose", "")
            for match in re.findall(r"\b([A-Z_]{4,})\b", note):
                if match in _KNOWN_ERROR_CODES:
                    codes.add(match)
    return codes


# ---------------------------------------------------------------------------
# 2) 템플릿 참조 해석
# ---------------------------------------------------------------------------

_REF_PATTERN = re.compile(r"\{(api|field|enum|error):([^}]+)\}")


class RefResolutionError(Exception):
    """템플릿 참조 해석 실패 시 발생."""
    pass


def _find_api(backend, group, keyword):
    """apis[group]에서 keyword를 포함하는 endpoint를 찾는다."""
    group_data = backend.get("apis", {}).get(group)
    if not group_data:
        available_groups = list(backend.get("apis", {}).keys())
        raise RefResolutionError(
            f"API 그룹 '{group}' 없음. 사용 가능: {available_groups}"
        )
    items = group_data.get("items", {})
    # keyword가 endpoint 문자열에 포함되는 것을 찾기
    candidates = [ep for ep in items if keyword in ep]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        # 더 정확한 매칭: endpoint가 keyword로 끝나는 것 우선
        exact = [ep for ep in candidates if ep.endswith("/" + keyword) or ep.endswith(keyword)]
        if len(exact) == 1:
            return exact[0]
        return candidates[0]  # 첫 번째 반환
    # 없으면 가까운 후보 제안
    all_endpoints = list(items.keys())
    close = get_close_matches(keyword, [ep.split("/")[-1] for ep in all_endpoints], n=3, cutoff=0.4)
    raise RefResolutionError(
        f"API '{group}'에서 '{keyword}' 키워드 포함 endpoint 없음. "
        f"가까운 후보: {close}, 전체: {all_endpoints}"
    )


def _find_field(backend, entity, field_name):
    """entities[entity].fields[field_name]을 찾는다."""
    entity_data = backend.get("entities", {}).get(entity)
    if not entity_data:
        available = list(backend.get("entities", {}).keys())
        raise RefResolutionError(f"엔티티 '{entity}' 없음. 사용 가능: {available}")
    field_data = entity_data.get("fields", {}).get(field_name)
    if not field_data:
        available = list(entity_data.get("fields", {}).keys())
        close = get_close_matches(field_name, available, n=3, cutoff=0.4)
        raise RefResolutionError(
            f"필드 '{entity}.{field_name}' 없음. 가까운 후보: {close}"
        )
    return field_data


def resolve_ref(match_obj, backend):
    """정규식 match 객체를 받아 치환할 문자열을 반환."""
    ref_type = match_obj.group(1)
    ref_args = match_obj.group(2)

    if ref_type == "api":
        parts = ref_args.split(":", 1)
        if len(parts) != 2:
            raise RefResolutionError(f"api 참조 형식 오류: {{api:{ref_args}}} → {{api:GROUP:KEYWORD}} 형식 필요")
        group, keyword = parts
        return _find_api(backend, group, keyword)

    elif ref_type == "field":
        parts = ref_args.split(":", 1)
        if len(parts) != 2:
            raise RefResolutionError(f"field 참조 형식 오류: {{field:{ref_args}}}")
        entity, field_name = parts
        field_data = _find_field(backend, entity, field_name)
        return field_data["type"]

    elif ref_type == "enum":
        parts = ref_args.split(":", 1)
        if len(parts) != 2:
            raise RefResolutionError(f"enum 참조 형식 오류: {{enum:{ref_args}}}")
        entity, field_name = parts
        field_data = _find_field(backend, entity, field_name)
        return field_data.get("note", field_data["type"])

    elif ref_type == "error":
        code = ref_args.strip()
        codes = _load_error_codes(backend)
        if code not in codes:
            close = get_close_matches(code, list(codes), n=3, cutoff=0.4)
            raise RefResolutionError(f"에러코드 '{code}' 없음. 가까운 후보: {close}")
        return code

    raise RefResolutionError(f"알 수 없는 참조 타입: {ref_type}")


def resolve_all_refs(text, backend):
    """텍스트 내의 모든 {api:...}, {field:...} 등을 치환한다.
    치환 실패 시 RefResolutionError를 발생시킨다."""
    errors = []

    def _replacer(m):
        try:
            return resolve_ref(m, backend)
        except RefResolutionError as e:
            errors.append(str(e))
            return m.group(0)  # 원본 유지

    result = _REF_PATTERN.sub(_replacer, text)
    if errors:
        raise RefResolutionError(
            f"템플릿 참조 해석 실패 {len(errors)}건:\n" + "\n".join(f"  - {e}" for e in errors)
        )
    return result


def resolve_refs_in_playbooks(playbooks, backend):
    """SCREEN_PLAYBOOKS 딕셔너리의 모든 텍스트에서 참조를 치환한다."""
    resolved = {}
    all_errors = []
    for section_id, playbook in playbooks.items():
        resolved[section_id] = {}
        for key, value in playbook.items():
            if isinstance(value, str):
                try:
                    resolved[section_id][key] = resolve_all_refs(value, backend)
                except RefResolutionError as e:
                    all_errors.append(f"섹션 {section_id}.{key}: {e}")
                    resolved[section_id][key] = value
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, str):
                        try:
                            new_list.append(resolve_all_refs(item, backend))
                        except RefResolutionError as e:
                            all_errors.append(f"섹션 {section_id}.{key}: {e}")
                            new_list.append(item)
                    elif isinstance(item, list):
                        new_sublist = []
                        for sub in item:
                            if isinstance(sub, str):
                                try:
                                    new_sublist.append(resolve_all_refs(sub, backend))
                                except RefResolutionError as e:
                                    all_errors.append(f"섹션 {section_id}.{key}: {e}")
                                    new_sublist.append(sub)
                            else:
                                new_sublist.append(sub)
                        new_list.append(new_sublist)
                    else:
                        new_list.append(item)
                resolved[section_id][key] = new_list
            else:
                resolved[section_id][key] = value
    if all_errors:
        raise RefResolutionError(
            f"Playbook 참조 해석 실패 {len(all_errors)}건:\n" + "\n".join(f"  - {e}" for e in all_errors)
        )
    return resolved


def resolve_refs_in_guides(guides, backend):
    """IMPLEMENTATION_GUIDES 딕셔너리의 모든 텍스트에서 참조를 치환한다."""
    resolved = {}
    all_errors = []
    for section_id, items in guides.items():
        new_items = []
        for item in items:
            try:
                new_items.append(resolve_all_refs(item, backend))
            except RefResolutionError as e:
                all_errors.append(f"가이드 섹션 {section_id}: {e}")
                new_items.append(item)
        resolved[section_id] = new_items
    if all_errors:
        raise RefResolutionError(
            f"가이드 참조 해석 실패 {len(all_errors)}건:\n" + "\n".join(f"  - {e}" for e in all_errors)
        )
    return resolved


# ---------------------------------------------------------------------------
# 3) Drift Detection: 하드코딩된 API 경로/에러코드 참조를 spec과 대조
# ---------------------------------------------------------------------------

_API_PATTERN = re.compile(r"`(GET|POST|PATCH|PUT|DELETE)\s+(/[a-zA-Z0-9_/{}\-\.]+)`")
_ERROR_CODE_PATTERN = re.compile(r"`?([A-Z][A-Z_]{3,})`?")
_BACKTICK_STATE_PATTERN = re.compile(r"`([a-z_]+)`")


def _collect_all_spec_endpoints(backend):
    """spec에 정의된 모든 API endpoint 집합."""
    endpoints = set()
    for group_data in backend.get("apis", {}).values():
        for ep in group_data.get("items", {}).keys():
            endpoints.add(ep)
    return endpoints


def _collect_all_spec_fields(backend):
    """spec에 정의된 모든 entity.field 집합."""
    fields = set()
    for entity, entity_data in backend.get("entities", {}).items():
        for field_name in entity_data.get("fields", {}).keys():
            fields.add(f"{entity}.{field_name}")
    return fields


def _normalize_endpoint(text):
    """endpoint 텍스트에서 {param} 패턴을 유지한 채 정규화."""
    # 파라미터 이름 통일: {id} → {id}, {designer_id} → {designer_id}
    return text.strip()


def validate_hardcoded_refs(playbooks, guides, backend, strict=False):
    """Playbook/Guide 텍스트에 하드코딩된 API 경로, 에러코드를 spec과 대조.
    
    Returns: (errors: list, warnings: list)
    """
    all_endpoints = _collect_all_spec_endpoints(backend)
    error_codes = _load_error_codes(backend)
    errors = []
    warnings = []

    def _check_text(text, location):
        # API 경로 검사
        for m in _API_PATTERN.finditer(text):
            method = m.group(1)
            path = m.group(2)
            full_ep = f"{method} {path}"
            # {param} 패턴 정규화
            normalized = full_ep
            if normalized not in all_endpoints:
                # 파라미터명 차이 허용: {id} vs {designer_id} 등
                matched = False
                pattern = re.sub(r"\{[^}]+\}", r"{[^}]+}", re.escape(normalized))
                pattern = pattern.replace(r"\{\[\^\\}\]\+\}", "{[^}]+}")
                for ep in all_endpoints:
                    if re.fullmatch(pattern, ep):
                        matched = True
                        break
                if not matched:
                    close = get_close_matches(normalized, list(all_endpoints), n=2, cutoff=0.5)
                    errors.append(f"[{location}] API `{normalized}` → spec에 없음. 가까운 후보: {close}")

        # 에러코드 검사 (백틱 안에 있는 대문자 코드만)
        for m in re.finditer(r"`([A-Z][A-Z_]{3,})`", text):
            code = m.group(1)
            # 일반적인 프로그래밍 키워드 제외
            if code in {"NULL", "UNIQUE", "JSON", "TRUE", "FALSE", "HTTP", "UUID", "TODO",
                        "CSV", "PUT", "GET", "POST", "PATCH", "DELETE", "AND", "CRUD",
                        "OK", "TTL", "URL", "API", "APNs", "PG", "IS", "DB", "ES",
                        "LLM", "MVP", "UI", "UX", "WEBP", "JPEG", "PDF", "HEIC"}:
                continue
            if code not in error_codes:
                close = get_close_matches(code, list(error_codes), n=2, cutoff=0.5)
                if close:
                    warnings.append(f"[{location}] 에러코드 `{code}` → spec 에러코드에 없음. 가까운 후보: {close}")

    # Playbook 검사
    for section_id, playbook in playbooks.items():
        for key, value in playbook.items():
            location = f"Playbook 섹션{section_id}.{key}"
            if isinstance(value, str):
                _check_text(value, location)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        _check_text(item, location)
                    elif isinstance(item, list):
                        for sub in item:
                            if isinstance(sub, str):
                                _check_text(sub, location)

    # Guide 검사
    for section_id, items in guides.items():
        for item in items:
            _check_text(item, f"Guide 섹션{section_id}")

    return errors, warnings


# ---------------------------------------------------------------------------
# 4) CLI용 메인
# ---------------------------------------------------------------------------

def run_validation(backend, playbooks, guides, strict=False):
    """전체 검증을 실행하고 결과를 출력한다. 에러가 있으면 exit code 1."""
    errors, warnings = validate_hardcoded_refs(playbooks, guides, backend, strict)

    print(f"\n{'='*60}")
    print(f"  Spec ↔ Playbook 동기화 검증 결과")
    print(f"{'='*60}")

    if not errors and not warnings:
        print("[OK] 모든 참조가 spec과 일치합니다!")
        return 0

    for w in warnings:
        print(f"[WARNING] {w}")
    for e in errors:
        print(f"[ERROR] {e}")

    print(f"\n요약: ERROR {len(errors)}건, WARNING {len(warnings)}건")

    if errors or (strict and warnings):
        return 1
    return 0
