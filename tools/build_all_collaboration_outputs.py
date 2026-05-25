import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


STEPS = [
    (
        "workbook",
        [sys.executable, str(ROOT / "tools" / "build_workbook.py")],
        "spec_text/*.md에서 백엔드 협업 엑셀을 재생성합니다.",
    ),
    (
        "owner_webapp_index",
        [sys.executable, str(ROOT / "tools" / "build_owner_webapp_index.py")],
        "사장님 웹앱 기능명세와 백엔드 필드/API 바인딩 HTML을 재생성합니다.",
    ),
    (
        "llm_pipeline_index",
        [sys.executable, str(ROOT / "tools" / "build_llm_pipeline_index.py")],
        "LLM 파이프라인 연동 가이드와 백엔드 필드/API 바인딩 HTML을 재생성합니다.",
    ),
    (
        "validate_spec_sync",
        [sys.executable, str(ROOT / "tools" / "validate_spec_sync.py")],
        "Playbook 텍스트의 API 참조가 spec JSON과 일치하는지 교차 검증합니다.",
    ),
]


def run_step(name, command, description):
    print(f"\n== {name} ==")
    print(description)
    result = subprocess.run(command, cwd=ROOT, text=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    print("Collaboration outputs build")
    print(f"root: {ROOT}")
    for name, command, description in STEPS:
        run_step(name, command, description)

    print("\nDone.")
    print("outputs/네일예약_백엔드_협업명세서_v3.xlsx")
    print("outputs/owner_webapp_backend_index.html")
    print("outputs/owner_webapp_backend_index.ai.txt")
    print("outputs/llm_pipeline_backend_index.html")
    print("outputs/llm_pipeline_backend_index.ai.txt")
    print("docs/owner_webapp_backend_index.html")
    print("docs/owner_webapp_backend_index.ai.txt")
    print("docs/llm_pipeline_backend_index.html")
    print("docs/llm_pipeline_backend_index.ai.txt")
    print("\n새 역할용 HTML 자동화 절차:")
    print("1. references/ 아래에 역할별 기능명세서 md를 둡니다.")
    print("2. 기존 HTML 빌더 중 구조가 가까운 파일을 복사해 역할별 MAP과 출력 파일명만 바꿉니다.")
    print("3. 이 파일의 STEPS에 새 빌더를 추가하면 전체 산출물이 한 번에 재생성됩니다.")


if __name__ == "__main__":
    main()
