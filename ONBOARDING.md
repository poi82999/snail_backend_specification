# 🐌 스네일 백엔드 명세서 — 팀원 온보딩 가이드

> 이 문서는 처음 이 저장소를 받은 팀원이 **10분 안에 작업을 시작**할 수 있도록 만든 안내서입니다.

---

## 내가 해야 할 일 요약

1. 이 저장소를 내 컴퓨터에 받는다
2. 내 담당 파일을 연다
3. 노란색 칸에 해당하는 JSON 값을 수정한다
4. 저장하고 git에 올린다

**끝입니다.** DB 설계, 서버 코드 작성, 엑셀 편집은 하지 않습니다.

---

## 1단계: 저장소 받기

### Git이 처음이라면

먼저 아래 두 가지를 설치합니다.

- [Git 다운로드](https://git-scm.com/downloads) — 설치 시 기본 옵션 그대로 Next 클릭
- [VS Code 다운로드](https://code.visualstudio.com/) — 코드 편집기

설치 후 아무 폴더에서 마우스 우클릭 → **"Git Bash Here"** 또는 **터미널**을 열고:

```bash
git clone https://github.com/poi82999/snail_backend_specification.git
cd snail_backend_specification
```

### Git을 이미 쓰고 있다면

```bash
git clone https://github.com/poi82999/snail_backend_specification.git
```

---

## 2단계: 내 담당 파일 찾기

`spec_text/` 폴더 안에 페이지별 파일이 있습니다. 아래에서 자기 역할에 해당하는 파일을 엽니다.

### 앱 프론트엔드 담당자

| 파일 | 내용 |
|------|------|
| `03_user_member.md` | 회원가입, 로그인, 프로필 |
| `04_user_discovery_reservation.md` | 검색, 피드, 예약 ← **가장 중요** |
| `08_snail.md` | 스네일(커뮤니티) |
| `09_comments_likes_follows.md` | 댓글, 좋아요, 팔로우 |
| `10_reviews.md` | 리뷰 |
| `13_notifications.md` | 푸시 알림 |

### UI 디자이너

| 파일 | 내용 |
|------|------|
| `04_user_discovery_reservation.md` | 예약 상태별 화면/문구 |
| `08_snail.md` | 스네일 작성/상세 화면 |
| `10_reviews.md` | 리뷰 작성 화면 |
| `11_reports.md` | 신고 사유/화면 |

### 사장님 웹 담당자

| 파일 | 내용 |
|------|------|
| `05_owner_shop.md` | 샵/디자이너 관리 ← **가장 중요** |
| `06_owner_design.md` | 디자인 등록/관리 |
| `07_owner_reservation.md` | 예약 관리 |

### LLM 담당자

| 파일 | 내용 |
|------|------|
| `12_llm.md` | LLM 분석 명세 ← **전부 여기** |

### 공통

| 파일 | 내용 |
|------|------|
| `15_checklist.md` | 내 체크리스트 |
| `16_common_api_auth.md` | 공통 API/에러/권한 규칙 |

---

## 3단계: 파일 수정하기

### 파일 구조 이해

각 파일은 이렇게 생겼습니다:

```markdown
# 페이지 제목

설명 텍스트...

## 수정 방법
...

```json spec-data
{
  "entities": { ... },
  "apis": { ... },
  ...
}
```                          ← 여기까지가 JSON 블록
```

**수정할 곳은 ` ```json spec-data ` 안의 JSON 값**입니다.

### 수정 예시

예를 들어 `04_user_discovery_reservation.md`에서 API 호출 화면을 확인하라는 항목이 있으면:

**수정 전:**
```json
["GET /search", "통합 검색", "q, region, cursor, limit"]
```

**수정 후 (프론트 의견 추가):**
```json
["GET /search", "통합 검색", "q, region, cursor, limit — 프론트: region은 GPS 자동 감지로 처리 가능. cursor 대신 page 번호도 지원 필요?"]
```

### ⚠️ JSON 수정 시 주의사항

| 규칙 | 예시 |
|------|------|
| 문자열은 **큰따옴표**만 사용 | ✅ `"값"` / ❌ `'값'` |
| 마지막 항목 뒤에 **쉼표 없음** | ✅ `["a", "b"]` / ❌ `["a", "b",]` |
| 줄바꿈은 `\n`으로 | ✅ `"1줄\n2줄"` / ❌ 실제 엔터 |

> **팁:** VS Code에서 파일을 열면 JSON 문법 오류가 빨간 줄로 표시됩니다.

---

## 4단계: 수정한 내용 올리기

### 방법 A: 터미널 (개발자 추천)

```bash
# 1. 최신 상태로 업데이트
git pull

# 2. 수정한 파일 확인
git status

# 3. 수정 내용 스테이징
git add spec_text/04_user_discovery_reservation.md

# 4. 커밋 (메시지에 뭘 바꿨는지 적기)
git commit -m "프론트: 검색 API region 파라미터 GPS 자동 감지 확인"

# 5. 서버에 올리기
git push
```

### 방법 B: VS Code 그래픽 (비개발자 추천)

1. VS Code 왼쪽 사이드바에서 **소스 제어** 아이콘 클릭 (가지 모양)
2. 변경된 파일 옆 **+** 버튼 클릭 (스테이징)
3. 상단 메시지 입력란에 변경 내용 작성
4. **✓ 커밋** 버튼 클릭
5. **동기화** 버튼 클릭 (올리기)

### 방법 C: GitHub 웹에서 직접 수정 (가장 쉬움)

1. https://github.com/poi82999/snail_backend_specification 접속
2. `spec_text/` 폴더 → 수정할 파일 클릭
3. 연필 아이콘 (Edit) 클릭
4. JSON 수정
5. 하단 "Commit changes" 클릭

> **비개발 팀원에게는 방법 C를 추천합니다.**

---

## 5단계: 엑셀로 확인하기 (선택)

수정한 내용이 엑셀에 제대로 반영되는지 확인하고 싶다면:

```powershell
# 처음 한 번만
pip install -r requirements.txt

# 엑셀 생성
python tools\build_workbook.py
```

`outputs/네일예약_백엔드_협업명세서_v3.xlsx`가 생성됩니다.

> 엑셀 빌드는 필수가 아닙니다. 텍스트 파일만 수정하면 됩니다.

---

## 자주 하는 실수와 해결

### "엑셀 빌드가 실패해요"

99%는 JSON 문법 오류입니다. 에러 메시지에 파일명과 줄 번호가 나옵니다.

```
ValueError: JSON 파싱 실패: spec_text/04_user_discovery_reservation.md line 12, col 5: ...
```

→ 해당 파일의 해당 줄에서 쉼표, 따옴표, 대괄호를 확인하세요.

### "git push가 안 돼요"

다른 팀원이 먼저 올린 경우입니다.

```bash
git pull --rebase
# 충돌이 있으면 VS Code에서 해결 후
git push
```

### "내가 수정할 곳을 모르겠어요"

1. `spec_canonical/backend_spec_v3.summary.md`를 먼저 읽으세요 — 전체 그림이 잡힙니다
2. 엑셀의 **노란색 칸**이 여러분이 채울 곳입니다
3. JSON에서는 빈 문자열 `""`로 되어 있는 곳이 여러분 몫입니다

---

## 전체 그림을 빠르게 잡고 싶다면

이 순서로 읽으세요:

1. **`spec_canonical/backend_spec_v3.summary.md`** — 전체 요약 (10분)
2. **`spec_canonical/user_scenarios_v3_mvp.txt`** — 유저 시나리오 (5분)
3. **내 담당 `spec_text/*.md` 파일** — 상세 명세 확인

---

## 질문이 있으면

- 명세 내용 관련: 팀 채널에 질문
- git 사용법: 이 문서의 해당 섹션 참고
- JSON 문법: VS Code가 빨간 줄로 알려줌
