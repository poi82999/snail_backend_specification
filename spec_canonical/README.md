# Backend Collaboration Spec v3 Canonical Notes

이 폴더는 네일 예약 + 커뮤니티 플랫폼 백엔드 협업 명세서의 중간 매개체입니다.

## 사용 원칙

1. 백엔드 협업명세서 관련 탐색, 분석, 수정 논의는 엑셀 파일이 아니라 텍스트 원본을 먼저 봅니다.
2. 팀원이 직접 수정할 원본은 `../spec_text/*.md`입니다.
3. 엑셀은 산출물입니다. 필요할 때 `tools/build_workbook.py`로 다시 생성합니다.
4. 사람이 빠르게 전체 방향을 읽어야 할 때는 `backend_spec_v3.summary.md`를 사용합니다.

## 파일 역할

- `../spec_text/*.md`: git에서 관리할 페이지별 텍스트 원본입니다. 각 파일의 `json spec-data` 블록이 엑셀 생성에 반영됩니다.
- `backend_spec_v3.canonical.json`: fallback 및 전체 스냅샷입니다. 새 협업 구조에서는 직접 수정 우선순위가 낮습니다.
- `backend_spec_v3.summary.md`: 대화와 리뷰에서 우선 참조할 요약 문서입니다.
- `../tools/build_workbook.py`: 텍스트 원본을 읽어 `outputs/네일예약_백엔드_협업명세서_v3.xlsx`를 생성합니다.
- `../tools/export_spec_text.py`: canonical JSON에서 `spec_text/*.md`를 다시 뽑는 초기화/복구용 도구입니다.

## 수정 워크플로우

```powershell
python tools/build_workbook.py
```

수정 요청이 들어오면 먼저 `spec_text/*.md`를 갱신하고, 최종 반영 시점에 위 명령으로 엑셀을 재빌드합니다.
