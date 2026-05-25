"""api_path → {api:group:keyword} 템플릿 참조로 자동 변환하는 1회성 스크립트.

실행: python tools/_convert_to_template_refs.py
결과: build_owner_webapp_index.py의 SCREEN_PLAYBOOKS 및 IMPLEMENTATION_GUIDES 영역에서
      백틱으로 감싼 API endpoint를 {api:...} 참조로 변환합니다.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_owner_webapp_index import load_backend_data

# API endpoint → {api:GROUP:KEYWORD} 매핑 생성
def build_api_ref_map(backend):
    """모든 API endpoint에 대해 최적의 {api:group:keyword} 참조를 생성."""
    ref_map = {}  # "METHOD /path" → "{api:group:keyword}"
    
    for group, group_data in backend["apis"].items():
        for endpoint in group_data["items"]:
            # endpoint: "POST /owner/auth/register"
            parts = endpoint.split()
            if len(parts) < 2:
                continue
            path = parts[1]
            # path의 마지막 세그먼트를 keyword로 사용
            segments = [s for s in path.split("/") if s and not s.startswith("{")]
            if not segments:
                continue
            keyword = segments[-1]
            
            # keyword가 고유한지 확인
            ref = f"{{api:{group}:{keyword}}}"
            ref_map[endpoint] = ref
    
    return ref_map


def convert_text(text, ref_map):
    """텍스트에서 `METHOD /path` 패턴을 {api:...}로 변환."""
    # 패턴: 백틱 안의 API endpoint
    def replacer(m):
        full = m.group(0)
        inner = m.group(1)
        # inner: "GET /owner/me" 등
        # 정확한 매칭 시도
        if inner in ref_map:
            return f"`{ref_map[inner]}`"
        # 파라미터 차이: {id} vs {designer_id} 등
        for ep, ref in ref_map.items():
            # 정규화하여 비교
            normalized_inner = re.sub(r"\{[^}]+\}", "{id}", inner)
            normalized_ep = re.sub(r"\{[^}]+\}", "{id}", ep)
            if normalized_inner == normalized_ep:
                return f"`{ref}`"
        return full  # 변환 불가 시 원본 유지
    
    result = re.sub(r"`((?:GET|POST|PATCH|PUT|DELETE)\s+/[^`]+)`", replacer, text)
    return result


def main():
    backend = load_backend_data()
    ref_map = build_api_ref_map(backend)
    
    print("=== API 참조 매핑 ===")
    for ep, ref in sorted(ref_map.items()):
        print(f"  {ep:55s} → {ref}")
    
    # build_owner_webapp_index.py 읽기
    target = ROOT / "tools" / "build_owner_webapp_index.py"
    content = target.read_text(encoding="utf-8")
    
    # SCREEN_PLAYBOOKS와 IMPLEMENTATION_GUIDES 영역만 변환
    # 전체 파일에서 변환 (OWNER_SECTION_MAP의 API 목록은 백틱이 아니므로 안 걸림)
    new_content = convert_text(content, ref_map)
    
    # 변경 사항 미리보기
    old_lines = content.splitlines()
    new_lines = new_content.splitlines()
    changes = 0
    for i, (old, new) in enumerate(zip(old_lines, new_lines)):
        if old != new:
            changes += 1
            print(f"\nL{i+1}:")
            print(f"  - {old.strip()[:120]}")
            print(f"  + {new.strip()[:120]}")
    
    print(f"\n총 {changes}개 라인 변경 예정")
    
    if changes > 0:
        target.write_text(new_content, encoding="utf-8")
        print(f"\n{target} 저장 완료!")
    else:
        print("\n변경 사항 없음.")


if __name__ == "__main__":
    main()
