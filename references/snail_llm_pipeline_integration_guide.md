# 스네일(Snail) 프로젝트 - LLM 파이프라인 연동 가이드

안녕하세요! 이 문서는 네일 예약 플랫폼 **스네일(Snail)** 의 백엔드와 LLM 서버 간의 원활한 연동을 위해 작성되었습니다.

LLM 파이프라인은 크게 **1단계(Transform)** 와 **2단계(Classify)** 로 나뉘어 순차적으로 실행됩니다. 백엔드가 어떤 데이터를 보내고(Input), 모델이 어떤 작업을 해야 하며(Processing), 백엔드로 어떤 결과를 돌려주셔야 하는지(Output) 상세히 정리했습니다.

---

## 전체 흐름 요약

1. 사장님이 네일 디자인 원본 사진을 앱에 업로드합니다.
2. 백엔드는 LLM 서버로 원본 사진을 보내며 **1단계(Transform)** 를 요청합니다.
3. LLM은 손톱 영역을 추출하여 크롭된 이미지를 만들고 백엔드로 결과를 반환합니다.
4. 백엔드는 다시 크롭된 이미지를 보내며 **2단계(Classify)** 를 요청합니다.
5. LLM은 색상, 스타일, 태그 등을 분석하여 백엔드로 반환합니다.
6. 디자인 등록이 완료되고 유저들에게 노출됩니다.

---

## 1단계: Transform (네일 영역 추출 및 규격화)

사장님이 올린 다양한 구도의 원본 사진에서 **네일(손톱) 영역만 추출하여 규격화된 썸네일 이미지**를 생성하는 단계입니다.

### 1. INPUT (백엔드 -> LLM)

백엔드에서 LLM 서버의 `/v1/transform` 엔드포인트로 아래와 같은 JSON을 보냅니다.

```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "image_url": "https://snail-bucket.s3.ap-northeast-2.amazonaws.com/original/nail1.jpg",
  "callback_url": "https://api.snail.com/webhooks/llm/transform",
  "options": {
    "output_size": "1080x1080",
    "background": "transparent"
  }
}
```

### 2. PROCESSING (LLM 처리 작업)

1. `image_url`의 원본 이미지를 다운로드합니다.
2. 비전 모델을 사용하여 **손톱 영역(Nail area)을 감지(Detect)** 합니다.
3. 배경을 제거하거나 손톱 영역을 중심으로 이미지를 크롭/규격화합니다.
4. 처리된 이미지를 LLM 측 스토리지(S3 등)에 업로드하여 URL을 생성합니다.

백엔드가 직접 저장하길 원한다면 Base64 바이너리로 리턴하는 방식을 백엔드와 협의합니다.

### 3. OUTPUT (LLM -> 백엔드)

분석 완료 후 백엔드의 `callback_url` 또는 동기 응답으로 아래 데이터를 반환합니다.

```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "cropped_image_url": "https://llm-bucket.s3.../cropped/nail1.png",
  "cropped_image_size": "1080x1080",
  "confidence": 0.95,
  "nail_count_detected": 10,
  "processing_time_ms": 1250,
  "error_code": null,
  "error_message": null
}
```

---

## 2단계: Classify (디자인 태그 및 속성 분류)

1단계에서 잘라낸 규격화된 이미지를 보고, **어떤 스타일과 색상인지 분류**하는 단계입니다. 검색 필터의 핵심이 됩니다.

### 1. INPUT (백엔드 -> LLM)

백엔드에서 LLM 서버의 `/v1/classify` 엔드포인트로 아래와 같은 JSON을 보냅니다.

```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "image_url": "https://llm-bucket.s3.../cropped/nail1.png",
  "locale": "ko_KR",
  "options": {
    "max_tags": 5,
    "include_color_palette": true,
    "include_style_category": true
  }
}
```

### 2. PROCESSING (LLM 처리 작업)

1. 이미지를 분석하여 디자인의 주요 색상, 스타일, 분위기, 기법, 손톱 모양을 추출합니다.
2. 추출한 태그들을 반드시 **부록 A: 표준 태그 사전** 에 있는 단어들로만 매핑합니다. 사전에 없는 자유 단어는 DB 검색에서 누락됩니다.

### 3. OUTPUT (LLM -> 백엔드)

분석 완료 후 아래의 결과 포맷으로 백엔드에 반환하면, 백엔드가 DB(`designs`)에 업데이트합니다.

```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "tags": ["프렌치", "봄", "러블리"],
  "color_palette": ["핑크", "화이트"],
  "style_category": "simple",
  "nail_shape": "라운드",
  "confidence_overall": 0.88,
  "processing_time_ms": 1500
}
```

---

## 에러 처리 가이드 (공통)

만약 1단계나 2단계 처리 중 문제가 발생하면, `status`를 `failed`로 하고 약속된 `error_code`를 보내주세요. 백엔드에서 사장님 앱 화면에 알맞은 안내 문구를 띄웁니다.

- `NO_NAIL`: 사진에서 네일이 감지되지 않음 (안내: "손이 잘 보이는 사진으로 다시 올려주세요.")
- `LOW_QUALITY`: 해상도 낮음, 블러, 조명 부족
- `MULTIPLE_HANDS`: 여러 명의 손이 섞임
- `OBSTRUCTED`: 네일이 가려짐
- `INAPPROPRIATE`: 부적절 콘텐츠 감지
- `INTERNAL_ERROR`: LLM 내부 에러

실패 시 Output 예시:

```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "error_code": "NO_NAIL",
  "error_message": "Could not detect nail area in the image"
}
```

---

## 부록 A: 표준 태그 사전 (Dictionary)

2단계 Classify Output을 만들 때, 아래 배열에 존재하는 텍스트만 출력해야 합니다.

- **[style_category] 대분류 (Enum)**:
  - `simple`, `glamour`, `classic`, `trendy`, `chic`
- **[nail_shape] 손톱 모양 (Enum)**:
  - `스퀘어`, `라운드`, `오벌`, `아몬드`, `스틸레토`, `발레리나`
- **[tags] 스타일/기법**:
  - `프렌치`, `옴브레`, `그라데이션`, `마그넷`, `글리터`, `큐빅`, `라인아트`, `캐릭터`, `무광`, `유광`, `젤`, `매니큐어`, `페디큐어`, `연장`, `케어`, `제거`
- **[tags] 분위기/상황**:
  - `봄`, `여름`, `가을`, `겨울`, `시크`, `러블리`, `심플`, `글래머`, `내추럴`, `키치`, `모던`, `웨딩`, `데일리`, `파티`, `오피스`, `데이트`
- **[color_palette] 색상**:
  - `핑크`, `레드`, `누드`, `블랙`, `화이트`, `베이지`, `블루`, `그린`, `옐로우`, `퍼플`, `브라운`, `골드`, `실버`

---

## 백엔드 팀의 질문 (논의 필요 사항)

개발을 시작하기 전, 아래 항목에 대해 백엔드 팀과 룰을 맞춥니다.

1. **동기 vs 비동기**: 처리에 시간이 얼마나 걸리나요? 10초 이상 걸린다면 API 응답을 끊고 Webhook Callback으로 결과를 받는 비동기 구조가 안전합니다.
2. **이미지 저장 주체**: 1단계에서 잘라낸 `cropped_image_url`은 LLM 측 S3에 저장하나요? 아니면 백엔드가 업로드하도록 설계할까요?
3. **신뢰도 기준**: 모델의 `confidence`가 몇 점 이하일 때 백엔드가 실패(`failed`) 처리하는 것이 좋을까요? 예: 0.5 미만이면 재촬영 요구.
