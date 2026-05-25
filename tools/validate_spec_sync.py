"""validate_spec_sync.py – 백엔드 명세 ↔ HTML 가이드 동기화 검증 CLI.

실행:
  python tools/validate_spec_sync.py           # WARNING 허용
  python tools/validate_spec_sync.py --strict   # WARNING도 에러 취급
"""

import sys
from pathlib import Path

# 모듈 경로
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_owner_webapp_index import (
    IMPLEMENTATION_GUIDES,
    SCREEN_PLAYBOOKS,
    load_backend_data,
)
from spec_ref import run_validation


def main():
    strict = "--strict" in sys.argv
    backend = load_backend_data()

    print("백엔드 명세 로드 완료:")
    print(f"  엔티티: {len(backend['entities'])}개")
    print(f"  API 그룹: {len(backend['apis'])}개")
    total_apis = sum(len(g["items"]) for g in backend["apis"].values())
    print(f"  API 엔드포인트: {total_apis}개")

    exit_code = run_validation(backend, SCREEN_PLAYBOOKS, IMPLEMENTATION_GUIDES, strict=strict)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
