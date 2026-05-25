import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = ROOT / "spec_canonical" / "backend_spec_v3.canonical.json"
SPEC_TEXT_DIR = ROOT / "spec_text"


SHEET_SPECS = [
    {
        "file": "00_workflow.md",
        "title": "텍스트 원본 관리 방식",
        "description": "팀원이 어떤 파일을 고치고 어떻게 엑셀을 생성하는지 설명합니다. 이 파일은 안내용입니다.",
        "keys": [],
    },
    {
        "file": "01_readme.md",
        "title": "1.README",
        "description": "문서 목적, 협업자 책임, 전체 변경사항, 시스템 주체를 관리합니다.",
        "keys": ["document", "collaboration_goal", "changes", "actors"],
        "page_guides": ["1.README"],
    },
    {
        "file": "02_flow.md",
        "title": "2.전체플로우",
        "description": "전체 데이터 흐름 페이지의 안내 문구를 관리합니다. 상세 플로우 행은 현재 빌더에서 생성합니다.",
        "keys": [],
        "page_guides": ["2.전체플로우"],
    },
    {
        "file": "03_user_member.md",
        "title": "3.유저(앱)_회원",
        "description": "유저 회원가입, 로그인, 프로필 필드 정의를 관리합니다.",
        "entities": ["User"],
        "page_guides": ["3.유저(앱)_회원"],
    },
    {
        "file": "04_user_discovery_reservation.md",
        "title": "4.유저(앱)_탐색예약",
        "description": "검색/피드/예약 API, 예약 엔티티, 상태 전이, 가용 슬롯 규칙을 관리합니다.",
        "entities": ["Reservation", "IdempotencyKey"],
        "apis": ["search", "reservation"],
        "keys": ["reservation_statuses", "reservation_state_transitions", "availability_rules"],
        "page_guides": ["4.유저(앱)_탐색예약"],
    },
    {
        "file": "05_owner_shop.md",
        "title": "5.사장님(웹)_샵관리",
        "description": "사장님 계정, 샵, 디자이너 필드와 사장님 웹 CRUD API를 관리합니다.",
        "entities": ["Owner", "Shop", "Designer"],
        "apis": ["owner_auth", "owner_shop", "owner_designer"],
        "page_guides": ["5.사장님(웹)_샵관리"],
    },
    {
        "file": "06_owner_design.md",
        "title": "6.사장님(웹)_디자인",
        "description": "디자인/이미지 필드와 디자인 관리 API를 관리합니다.",
        "entities": ["Design", "DesignImage"],
        "apis": ["owner_design"],
        "page_guides": ["6.사장님(웹)_디자인"],
    },
    {
        "file": "07_owner_reservation.md",
        "title": "7.사장님(웹)_예약",
        "description": "사장님 웹 예약 관리 API를 관리합니다.",
        "apis": ["owner_reservation"],
        "page_guides": ["7.사장님(웹)_예약"],
    },
    {
        "file": "08_snail.md",
        "title": "8.커뮤니티_스네일",
        "description": "스네일(Snap) 필드와 스네일 API를 관리합니다. 엔드포인트명은 /snaps를 유지합니다.",
        "entities": ["Snap"],
        "apis": ["snap"],
        "page_guides": ["8.커뮤니티_스네일"],
    },
    {
        "file": "09_comments_likes_follows.md",
        "title": "9.커뮤니티_댓글",
        "description": "댓글, 좋아요, 팔로우 필드/API를 관리합니다.",
        "entities": ["Comment"],
        "apis": ["comment_like_follow"],
        "page_guides": ["9.커뮤니티_댓글"],
    },
    {
        "file": "10_reviews.md",
        "title": "10.커뮤니티_리뷰",
        "description": "리뷰 필드와 리뷰 API를 관리합니다.",
        "entities": ["Review"],
        "apis": ["review"],
        "page_guides": ["10.커뮤니티_리뷰"],
    },
    {
        "file": "11_reports.md",
        "title": "11.커뮤니티_신고",
        "description": "신고/모더레이션 필드를 관리합니다.",
        "entities": ["Report"],
        "page_guides": ["11.커뮤니티_신고"],
    },
    {
        "file": "12_llm.md",
        "title": "12.LLM명세",
        "description": "LLM Transform/Classify, 태그 사전, 에러 코드, 작업자 질문을 관리합니다.",
        "keys": ["llm"],
        "page_guides": ["12.LLM명세"],
    },
    {
        "file": "13_notifications.md",
        "title": "13.알림",
        "description": "APNs, 카카오 알림톡 등 알림 종류를 관리합니다.",
        "keys": ["notifications"],
        "page_guides": ["13.알림"],
    },
    {
        "file": "14_decisions.md",
        "title": "14.의사결정기록",
        "description": "확정 의사결정과 팀 내부 결정 필요 사항을 관리합니다.",
        "keys": ["decisions", "internal_decisions_needed", "policies"],
        "page_guides": ["14.의사결정기록"],
    },
    {
        "file": "15_checklist.md",
        "title": "15.체크리스트",
        "description": "담당자별 회신 전 체크리스트를 관리합니다.",
        "keys": ["checklist"],
        "page_guides": ["15.체크리스트"],
    },
    {
        "file": "16_common_api_auth.md",
        "title": "16.공통_API권한",
        "description": "공통 응답/에러/페이지네이션/rate limit/권한 모델을 관리합니다.",
        "keys": ["auth_permission_model", "common_api_rules"],
        "page_guides": ["16.공통_API권한"],
    },
]


def pick(data, spec):
    picked = {}
    for key in spec.get("keys", []):
        picked[key] = data[key]
    if spec.get("entities"):
        picked["entities"] = {key: data["entities"][key] for key in spec["entities"]}
    if spec.get("apis"):
        picked["apis"] = {key: data["apis"][key] for key in spec["apis"]}
    if spec.get("page_guides"):
        picked["page_guides"] = {key: data["page_guides"][key] for key in spec["page_guides"]}
    return picked


def md_for_spec(spec, data):
    lines = [
        f"# {spec['title']}",
        "",
        spec["description"],
        "",
        "## 수정 방법",
        "",
        "- 아래 `json spec-data` 코드블록이 엑셀 생성에 쓰이는 원본입니다.",
        "- 팀원은 이 파일을 수정하고 git에 커밋/푸시하면 됩니다.",
        "- JSON 문법이 깨지면 엑셀 빌드가 실패하므로 큰따옴표, 쉼표, 대괄호를 유지해주세요.",
        "- 엑셀 파일은 산출물입니다. 원본 수정은 이 텍스트 파일에서 합니다.",
        "",
    ]
    payload = pick(data, spec)
    if payload:
        lines.extend([
            "```json spec-data",
            json.dumps(payload, ensure_ascii=False, indent=2),
            "```",
            "",
        ])
    else:
        lines.extend([
            "이 파일은 안내용입니다. 엑셀에 들어가는 실제 데이터는 다른 `*.md` 파일의 `json spec-data` 블록에서 관리합니다.",
            "",
            "빌드 명령:",
            "",
            "```powershell",
            "python tools\\build_workbook.py",
            "```",
            "",
        ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="기존 spec_text/*.md 파일을 덮어씁니다.")
    args = parser.parse_args()

    data = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
    SPEC_TEXT_DIR.mkdir(parents=True, exist_ok=True)

    for spec in SHEET_SPECS:
        path = SPEC_TEXT_DIR / spec["file"]
        if path.exists() and not args.force:
            print(f"skip existing: {path}")
            continue
        path.write_text(md_for_spec(spec, data), encoding="utf-8")
        print(f"wrote: {path}")


if __name__ == "__main__":
    main()
