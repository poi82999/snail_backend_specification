# Backend Specification Workbook

이 저장소는 네일 예약 + 커뮤니티 플랫폼 백엔드 협업 명세서를 텍스트 원본으로 관리하고, 필요할 때 엑셀 파일로 생성하기 위한 작업 공간입니다.

## 핵심 원칙

- 원본은 `spec_text/*.md`입니다.
- 엑셀 파일은 산출물입니다. 직접 수정해도 다음 빌드 때 덮어써질 수 있습니다.
- 팀원은 담당 페이지의 `json spec-data` 블록을 수정하고 git에 커밋/푸시합니다.
- 누가 어느 항목을 바꿨는지는 git diff로 확인합니다.

## 자주 쓰는 명령

처음 한 번만 의존성을 설치합니다.

```powershell
pip install -r requirements.txt
```

```powershell
python tools\build_workbook.py
```

위 명령은 `spec_text/*.md`를 읽어 `outputs/네일예약_백엔드_협업명세서_v3.xlsx`를 생성합니다.
기존 엑셀 파일이 열려 있어 덮어쓸 수 없으면 `_updated` 또는 타임스탬프가 붙은 새 파일명으로 저장합니다.

```powershell
python tools\build_owner_webapp_index.py
```

위 명령은 `references/snail_owner_webapp_spec_v1.md`와 `spec_text/*.md`를 연결해 `outputs/owner_webapp_backend_index.html` 비주얼라이저와 `outputs/owner_webapp_backend_index.json` 색인 데이터를 생성합니다.
사장님 웹앱 프론트 작업자는 HTML 파일을 열어 기능별 관련 백엔드 필드/API를 빠르게 찾을 수 있습니다.
AI 코딩 도구에 넣을 압축 컨텍스트는 HTML 상단의 `AI 요약 복사` 버튼 또는 `outputs/owner_webapp_backend_index.ai.txt`를 사용합니다.

```powershell
python tools\build_llm_pipeline_index.py
```

위 명령은 `references/snail_llm_pipeline_integration_guide.md`와 `spec_text/*.md`를 연결해 `outputs/llm_pipeline_backend_index.html` 비주얼라이저와 `outputs/llm_pipeline_backend_index.json` 색인 데이터를 생성합니다.
LLM 작업자는 Transform/Classify 계약, 에러 코드, 표준 태그 사전, 백엔드 저장 필드/API를 한 화면에서 확인할 수 있습니다.
AI 코딩 도구에 넣을 압축 컨텍스트는 HTML 상단의 `AI 요약 복사` 버튼 또는 `outputs/llm_pipeline_backend_index.ai.txt`를 사용합니다.

```powershell
python tools\build_all_collaboration_outputs.py
```

위 명령은 엑셀과 현재 등록된 협업 비주얼라이저를 한 번에 재생성합니다.
앞으로 LLM 작업자나 다른 프론트엔드용 HTML을 추가할 때는 역할별 빌더를 만든 뒤 `build_all_collaboration_outputs.py`의 `STEPS`에 추가하면 됩니다.

## Notion 공유용 링크

각 HTML 빌더는 로컬 확인용 `outputs/*.html`과 함께 GitHub Pages 공유용 `docs/*.html`도 생성합니다.

GitHub 저장소 Settings → Pages에서 source를 `Deploy from a branch`, branch를 `main`, folder를 `/docs`로 설정하면 아래 URL을 Notion에 붙여 공유할 수 있습니다.

```text
https://poi82999.github.io/snail_backend_specification/
https://poi82999.github.io/snail_backend_specification/owner_webapp_backend_index.html
https://poi82999.github.io/snail_backend_specification/llm_pipeline_backend_index.html
```

```powershell
python tools\export_spec_text.py
```

위 명령은 `spec_canonical/backend_spec_v3.canonical.json`에서 `spec_text/*.md`를 생성합니다. 이미 파일이 있으면 덮어쓰지 않습니다.

```powershell
python tools\export_spec_text.py --force
```

기존 `spec_text/*.md`를 canonical JSON 기준으로 덮어씁니다. 팀원이 수정한 내용이 사라질 수 있으므로 복구 목적일 때만 사용합니다.

## 협업 방식

1. 담당자는 `spec_text`에서 자기 담당 파일을 엽니다.
2. 설명을 읽고 `json spec-data` 블록 안의 필요한 값만 수정합니다.
3. `python tools\build_workbook.py`로 엑셀 생성이 되는지 확인합니다.
4. 변경된 텍스트 파일을 git에 커밋/푸시합니다.

엑셀 파일은 `outputs/` 아래에 생성되며 git 추적 대상에서 제외합니다.
