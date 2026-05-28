import json
from datetime import datetime
from pathlib import Path

from build_owner_webapp_index import (
    ROOT,
    SPEC_TEXT_DIR,
    CANONICAL_PATH,
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
    "visibility": "사장님이 고객에게 샵/디자인을 보여줄지 숨길지 직접 토글하는 스위치 상태입니다. (임시저장 draft, 노출 active, 숨김 hidden)",
    "ai_analysis_status": "현재 AI가 어디까지 분석했는지 나타내는 가장 중요한 필드입니다. 화면에 '분석 중 / 분석 완료 / 실패' 배지를 띄우는 기준이 됩니다.",
    "ai_analysis_started_at": "분석이 시작된 시간입니다. 빙글빙글 도는 로딩 화면에서 'n분째 분석 중입니다'라고 친절하게 알려줄 때 씁니다.",
    "ai_analysis_completed_at": "분석이 끝난(성공이든 실패든) 시간입니다. 얼마나 걸렸는지 기록하거나 에러 발생 시점을 파악할 때 유용합니다.",
    "image_id": "디자인에 올라간 여러 장의 사진 중 딱 1장을 콕 집어내는 고유 번호입니다. 백엔드와 LLM이 서로 '이 사진 말이야'라고 소통할 때 씁니다.",
    "original_url": "사장님이 처음 업로드한 쌩원본 사진의 링크입니다. 나중에 AI가 잘못 분석해서 다시 처음부터 재분석해야 할 때 꺼내 씁니다.",
    "cropped_url": "AI(Transform)가 원본에서 손톱 영역만 예쁘게 오려낸 썸네일 이미지 링크입니다. 고객 검색 화면이나 2차 AI 분석(Classify)에 들어갑니다.",
    "ai_transform_status": "1단계 AI(손톱 오려내기) 작업의 성공/실패 여부입니다.",
    "ai_classify_status": "2단계 AI(태그/색상 추출) 작업의 성공/실패 여부입니다.",
    "ai_tags": "AI가 우리 서비스의 '표준 태그 사전'에서만 쏙쏙 골라낸 검색용 태그들입니다. 프론트 필터 칩스와 100% 일치해야 합니다.",
    "ai_color_palette": "AI가 뽑아낸 대표 컬러들입니다. '핑크톤 모아보기' 같은 색상 필터 검색의 핵심 무기입니다.",
    "ai_style_category": "전체적인 무드(러블리, 힙한, 심플 등)를 분류해둔 큰 카테고리입니다.",
    "owner_tags": "AI 분석과 무관하게, 사장님이 굳이 덧붙이고 싶어 하는 자유 키워드(해시태그) 배열입니다."
}


EASY_CONTRACT_FIELD_EXPLANATIONS = {
    "image_id": "어떤 이미지를 처리할지 백엔드와 AI가 맞추는 주민번호 같은 고유 키입니다.",
    "image_url": "AI 모듈이 다운로드 받아서 분석을 시작할 원본 사진의 주소입니다.",
    "callback_url": "비동기로 작업하는 AI가 '분석 다 끝났어요!'라고 백엔드에게 결과를 던져줄 도착지 주소입니다.",
    "options.output_size": "잘라낼 손톱 썸네일을 가로세로 몇 픽셀로 맞출지 지정합니다. (예: 1080x1080)",
    "options.background": "잘라낸 손톱 이미지 뒷배경을 투명하게 날릴지, 단색으로 채울지 정하는 옵션입니다.",
    "status": "AI 작업의 최종 명운. `success`(성공) 아니면 `failed`(실패) 둘 중 하나만 내려옵니다.",
    "cropped_image_url": "1단계(Transform)를 무사히 마치고 저장소에 업로드된 예쁜 손톱 썸네일 주소입니다.",
    "cropped_image_size": "실제로 오려진 썸네일 이미지의 최종 해상도입니다.",
    "confidence": "AI가 자기 분석 결과에 얼마나 자신 있는지 나타내는 확신도 점수(0~1)입니다. 너무 낮으면 차라리 실패 처리합니다.",
    "nail_count_detected": "사진에서 감지된 손톱의 개수입니다. (예: 0개면 손톱이 없는 사진이라 에러 뱉음)",
    "processing_time_ms": "AI가 끙끙대며 분석한 시간입니다. 1000이 1초입니다.",
    "error_code": "실패 시 기계가 쉽게 읽고 프론트 분기 처리를 할 수 있는 텍스트 코드입니다. (예: NO_NAIL)",
    "error_message": "실패 시 사람이 읽을 수 있는 친절한 설명입니다.",
    "locale": "결과물을 무슨 언어로 줄지 묻는 옵션. 한국 서비스니까 무조건 `ko_KR`을 씁니다.",
    "options.max_tags": "AI한테 '태그 너무 많이 주지 말고 딱 N개만 뽑아줘'라고 제한을 거는 설정입니다.",
    "options.include_color_palette": "결과물에 대표 색상도 같이 내려줄지 물어보는 옵션입니다.",
    "options.include_style_category": "큰 스타일 분류 값도 같이 내려줄지 물어보는 옵션입니다.",
    "tags": "프론트 필터링에 쓰일 귀중한 태그 리스트입니다. 무조건 우리가 약속한 단어(사전)만 와야 합니다.",
    "color_palette": "디자인의 대표 색상 헥스코드나 색상명 배열입니다.",
    "style_category": "디자인의 큼직한 분위기(심플, 화려함 등)를 뜻합니다.",
    "nail_shape": "라운드, 스퀘어 등 손톱의 생김새입니다.",
    "confidence_overall": "2단계(Classify) 전체 결과에 대한 AI 스스로의 종합 자신감 점수입니다."
}


EASY_API_EXPLANATIONS = {
    "POST /owner/designs": "[디자인 등록하기 버튼] 사장님이 폼을 채워 저장을 누를 때 호출합니다. 쏘자마자 프론트는 성공 화면으로 넘어가지만, 뒤에선 AI가 땀 뻘뻘 흘리며 분석을 시작합니다.",
    "GET /owner/designs": "[디자인 목록 보기] 사장님이 자기 포트폴리오를 볼 때 씁니다. 상태별(분석중, 완료, 실패) 탭이나 필터를 구현할 때 쿼리를 적극 활용하세요.",
    "GET /owner/designs/{design_id}": "[디자인 상세 뷰] 디자인 하나를 눌렀을 때, 혹은 AI가 분석을 끝냈는지 실시간으로 새로고침(폴링)해서 뱃지를 갈아끼울 때 호출합니다.",
    "PATCH /owner/designs/{design_id}": "[디자인 텍스트 수정] 사진은 놔두고 제목이나 가격, 태그만 슥 고칠 때 가볍게 호출하는 API입니다.",
    "POST /owner/designs/{design_id}/images": "[새 사진 끼워넣기] 사진을 새로 올리면 원본이 바뀌므로, 얌전히 '분석 중' 뱃지로 원복하고 AI에게 다시 일감을 던집니다.",
    "DELETE /owner/designs/{design_id}/images/{image_id}": "[사진 삭제하기] 사진을 지워도 전체 디자인의 분위기가 바뀔 수 있어 AI 분석이 다시 돌아갈 수 있습니다.",
    "POST /owner/designs/{design_id}/reanalyze": "[수동 재분석 버튼] AI가 사진을 엄한 걸로 인식해서 실패(failed) 떴을 때, 억울한 사장님이 다시 분석해달라고 찌르는 버튼입니다."
}


STEP_PLAIN_LANGUAGE = {
    "flow": [
        "사장님이 디자인 사진을 올리고 [등록]을 쾅 누르면, 백엔드는 일단 '알겠어요!' 하고 바로 화면을 응답해줍니다.",
        "그러고 나서 백엔드가 몰래 AI(LLM)에게 사진 분석을 맡기는데, AI가 곰곰이 생각해서 정답을 돌려주면 그제야 디자인에 예쁜 태그가 붙고 유저들에게 보일 준비가 끝납니다.",
        "즉, 등록 버튼을 누른 찰나에 모든 분석이 끝나는 게 아니니, 프론트엔드는 반드시 사장님께 '현재 ⏳AI 분석 중입니다'라는 뱃지를 친절하게 띄워주며 기다리게 해야 합니다."
    ],
    "transform": [
        "Transform 단계는 한마디로 '원룸 배경, 사장님 손가락 등을 싹 다 날리고 오직 예쁜 손톱만 네모 반듯하게 오려내는(Crop) 단계'입니다.",
        "이 1단계 오려내기가 완벽해야 다음 2단계에서 색상이나 스타일을 안 틀리고 잘 잡을 수 있습니다.",
        "만약 이 단계부터 '이건 손톱이 아닌데?(NO_NAIL)' 하고 실패해버리면 2단계로 넘어가지 말고, 프론트에서 재빨리 사장님께 '사진에 손톱이 안 보여요 ㅠㅠ 교체해주세요'라고 안내해야 합니다."
    ],
    "classify": [
        "Classify 단계는 1단계에서 예쁘게 오려낸 손톱만 보고 '이건 핑크톤에 글리터가 들어갔군' 하며 검색용 태그와 색상을 찰떡같이 붙여주는 단계입니다.",
        "이때 AI가 신나서 아무 단어나 창조하면 안 되고, 반드시 우리가 미리 짜둔 '표준 태그 사전' 안에서만 단어를 골라야 고객 앱 필터링 칩스와 아귀가 딱 맞습니다.",
        "프론트엔드는 여기서 내려온 `ai_tags`를 고객 앱의 검색 필터 버튼으로 100% 매핑해서 뿌려주면 됩니다."
    ],
    "errors": [
        "AI 분석 실패는 단순히 서버가 죽은 게 아니라, 사장님이 실수로 발가락이나 풍경 사진을 올려서 못 알아보는 경우도 많습니다.",
        "백엔드가 친절하게 내려주는 `error_code`를 프론트에서 찰떡같이 캐치해서, '사진이 너무 흐려요(LOW_QUALITY)'인지 '손톱이 없어요(NO_NAIL)'인지 팝업 텍스트를 다르게 띄워주세요.",
        "같은 실패라도 원인에 따라 사장님한테 [재분석하기] 버튼을 줄지, [사진 아예 바꾸기] 버튼을 줄지 다르게 렌더링하는 게 핵심입니다."
    ],
    "dictionary": [
        "표준 태그 사전은 AI가 사용할 수 있는 '허락된 단어장'입니다.",
        "만약 AI가 사전 밖의 단어를 뱉으면, 백엔드가 컷오프하거나 프론트 검색 칩스에 안 나타나게 되니 양쪽 모두 철저하게 이 사전을 기준으로 로직을 짭니다.",
        "나중에 기획자가 '이제 시럽 네일 태그도 추가할까요?' 하면 백엔드/AI/프론트 셋 다 동시에 이 단어장을 업데이트해야 화면이 꼬이지 않습니다."
    ],
    "open-questions": [
        "여기 있는 질문들은 코딩 들어가기 전에 '어떻게 할까요?' 하고 기획/백엔드와 결판을 내야 하는 항목들입니다.",
        "예를 들어 AI 분석이 오래 걸리는데 화면을 새로고침할 건지(동기), 아니면 나중에 팝업 띄울 건지(비동기 Webhook) 등에 따라 프론트 짜는 방식이 180도 바뀝니다.",
        "따라서 헷갈리면 절대 마음대로 더미코드 짜지 마시고 핑을 쳐서 결정을 받아낸 뒤 UI에 반영해주세요."
    ]
}


LLM_STEP_PLAYBOOKS = {
    "flow": {
        "call_order": [
            "[최초 등록]: 사장님이 폼을 제출하면 백엔드는 쌩 원본 이미지를 스토리지에 올리고 상태를 `ai_analysis_status = pending(대기중)`으로 만듭니다.",
            "[1단계 큐잉]: 백엔드 워커가 눈치껏 이미지 한 장 한 장마다 Transform(오려내기) 요청을 비동기 큐에 밀어 넣습니다.",
            "[1단계 성공 시]: Transform 결과(크롭된 이미지)가 도착하면 그걸 저장하고, 바로 이어서 2단계 Classify(태그 추출) 요청을 큐에 던집니다.",
            "[최종 성공 시]: Classify까지 정답이 오면 태그/컬러를 다 저장한 뒤 디자인의 최종 상태를 `ai_analysis_status = done(완료)`으로 쾅 찍어줍니다.",
            "[에러 발생 시]: 1단계든 2단계든 어디서라도 엎어지면 그 즉시 분석을 중단하고 `failed(실패)` 상태와 에러 사유를 남깁니다."
        ],
        "events": [
            ["[시스템] 디자인 새로 등록됨", "Transform 큐 작업 시작", "프론트에서는 사장님께 'AI가 꼼꼼히 분석을 시작했어요 ⏳' 배지를 예쁘게 보여주며 달래줍니다.", "URL이 깨졌거나 용량이 0바이트면 애초에 큐에 안 넣고 즉각 failed 처리합니다."],
            ["[시스템] 1단계 Transform 무사 통과", "Classify 큐 작업 바통 터치", "화면상엔 아직 '분석 중'으로 계속 유지됩니다 (사장님은 뒤에서 무슨 단계인지 모릅니다).", "손톱이 안 보여서 NO_NAIL 에러가 터졌다면, 2단계로 안 넘어가고 즉시 사장님 화면에 실패 딱지와 함께 [사진 교체] 안내를 띄웁니다."],
            ["[시스템] 2단계 Classify 최종 합격", "Design.ai_* 데이터 꽉꽉 채움", "프론트 뱃지를 '분석 완료 ✅'로 갈아끼우고, 이제 드디어 사장님이 [고객에게 공개하기] 토글을 켤 수 있게 스위치 잠금을 풀어줍니다.", "만약 AI가 사전 밖의 단어를 마구 내뱉었다면 백엔드가 검증에서 컷하고 에러(failed)로 간주할 수 있습니다."]
        ],
        "qa": [
            "사장님이 [디자인 등록] 버튼을 눌렀을 때, AI 분석이 끝날 때까지 10초 넘게 멍때리며 로딩만 돌고 있지 않고 바로 화면이 넘어가 비동기로 처리되는지 확인하세요.",
            "고의로 풍경 사진을 올려 1단계에서 NO_NAIL 실패가 떴을 때, 쓸데없이 2단계 태그 추출까지 안 돌아가고 재빨리 에러 팝업을 띄우는지 테스트하세요.",
            "분석 중(pending)일 때는 고객용 앱에서 검색해도 절대 해당 디자인이 나오지 않다가, 완료(done)로 상태가 바뀌는 순간 검색 결과에 짠 하고 나타나는지 교차 검증해주세요.",
            "같은 이미지를 연속해서 중복으로 등록 버튼을 광클했을 때 DB에 분석 결과나 크롭 이미지가 두 번씩 오염되어 쌓이지 않게 방어 로직이 튼튼한지 확인하세요."
        ]
    },
    "transform": {
        "call_order": [
            "[AI 호출 시작]: 백엔드가 AI 모듈의 `/v1/transform` 엔드포인트를 찌르며 '이 원본 주소(image_url) 다운받아서 잘라줘, 다 되면 이 주소(callback_url)로 알려줘'라고 주문합니다.",
            "[AI의 작업]: AI는 원본 사진을 쓱 훑어보고 손톱 위치를 기가 막히게 감지한 뒤, 1080x1080 등 약속된 예쁜 크기로 잘라내고(Crop) 기울기도 잡아줍니다.",
            "[결과 저장]: 잘라낸 사진을 어딘가(S3 등)에 예쁘게 저장하고 최종 `cropped_image_url`을 뽑아냅니다.",
            "[콜백 응답]: 백엔드에게 '나 다했어!'라며 성공 데이터나 명확한 에러 코드를 콜백으로 날려줍니다."
        ],
        "events": [
            ["[AI] 백엔드 요청 받음", "이미지 다운로드 시작", "정상 다운로드되면 룰루랄라 손톱을 찾기 시작합니다.", "서버가 잠시 죽었거나 URL이 404면 INTERNAL_ERROR 류의 에러 코드를 뱉고 바로 퇴근합니다."],
            ["[AI] 손톱 기가막히게 감지함", "크롭 이미지 생성 및 저장", "기분 좋게 success 응답과 함께 확신도(confidence) 점수를 백엔드에 제출합니다.", "어렴풋이 보이긴 하는데 자신감(confidence)이 너무 낮으면 정책에 따라 매정하게 실패로 돌릴 수 있습니다."],
            ["[AI] 사진에 손톱이 아예 없음", "failed 응답과 에러 뱉음", "얄짤없이 `NO_NAIL`, `LOW_QUALITY` 같은 명확한 코드와 함께 분석을 거부합니다.", "실패했는데 error_code가 빈 값으로 내려오는 대참사가 일어나면 안 됩니다."]
        ],
        "qa": [
            "백엔드가 준 `image_id`를 AI가 콜백 응답에 잃어버리지 않고 고스란히 돌려주는지(매칭용) 꼭 확인하세요.",
            "인터넷에서 다운받은 강아지 사진을 올렸을 때 정확하게 `status=failed`, `error_code=NO_NAIL`이 반환되고 프론트에 '손톱이 없어요' 문구가 뜨는지 테스트하세요.",
            "성공했을 땐 크롭된 이미지 URL, 사이즈 정보, 확신도 점수 3종 세트가 모두 빠짐없이 내려오는지 콘솔을 찍어보세요.",
            "사진이 너무 고화질이라 분석에 10초 넘게 걸려도 비동기 콜백 방식이 끊기거나 타임아웃 나지 않고 무사히 돌아오는지 긴장하며 확인하세요."
        ]
    },
    "classify": {
        "call_order": [
            "[AI 호출 시작]: 1단계를 통과한 예쁜 크롭 이미지(cropped_url)를 가지고, 백엔드가 이번엔 `/v1/classify`에 들이밀며 '태그 좀 달아줘'라고 요청합니다.",
            "[특징 추출]: LLM(비전 모델)이 이미지를 째려보며 '음, 이건 핑크베이스에 큐빅이 박혔고 분위기는 러블리하군' 하며 태그 후보들을 마구 떠올립니다.",
            "[사전 필터링]: LLM 스스로 방금 떠올린 단어들을 우리가 정해둔 '표준 태그 사전'과 대조해서 똑같은 단어들만 살아남게 매핑합니다.",
            "[비표준 컷오프]: 사전에 없는 기상천외한 단어는 가차 없이 버리거나, 제일 비슷한 표준 단어로 억지로 끼워 맞춥니다.",
            "[최종 저장]: 정제된 태그, 컬러, 스타일 결과가 백엔드로 넘어오면 프론트가 읽기 좋게 `Design` 테이블에 쏙쏙 박아넣습니다."
        ],
        "events": [
            ["[AI] 분류 성공 및 매핑 완료", "success 콜백 전송", "결과에 표준 단어들만 예쁘게 배열로 담겨 백엔드에 도착합니다.", "만약 이 배열에 우리가 모르는 사투리(?) 태그가 들어있으면 백엔드가 500 에러를 뱉고 화를 냅니다."],
            ["[AI] 뭔지 잘 모르겠음 (확신도 낮음)", "confidence 임계치 적용", "확신이 안 서는 태그는 덜어내거나 통째로 failed 처리합니다.", "어디서 컷할지 기준(예: 0.7 이하면 버린다)이 미정이면 프론트는 일단 로직을 비워두고 기획을 쪼세요."],
            ["[시스템] 여러 사진에서 태그 나옴", "태그 병합(Merge) 로직", "사진이 3장이면 각 사진의 태그들을 모아서 중복을 제거하고 디자인 하나의 통합 태그로 만듭니다.", "병합 규칙 없이 아무거나 덮어쓰면 안 되니 로직을 꼭 확인하세요."]
        ],
        "qa": [
            "`tags`, `color_palette`, `style_category` 배열 안에 들어온 값들이 100% 빠짐없이 우리의 '표준 태그 사전'에 등재된 녀석들인지 깐깐하게 대조해보세요.",
            "`nail_shape`(손톱 모양) 값도 같이 내려오긴 하는데, 이걸 화면에 그릴 건지 DB에 짱박을 건지 정책 문서(decisions)랑 로직이 찰떡같이 맞는지 확인하세요.",
            "백엔드가 `max_tags=5`로 5개만 달라고 제한을 걸었는데 눈치 없는 AI가 6개를 뱉어내진 않는지 제한(Limit) 테스트를 돌려보세요.",
            "이미지 URL이 중간에 깨졌거나 404일 때, AI가 무한정 뻗어있지 않고 명확한 failed 콜백을 신속하게 쏴주는지 확인하세요."
        ]
    },
    "errors": {
        "call_order": [
            "[AI 실패 발생]: 어떤 이유로든 실패하면 AI는 `status=failed`, `error_code`, `error_message` 3형제를 무조건 챙겨서 콜백을 줍니다.",
            "[메시지 번역]: 백엔드는 영어로 된 딱딱한 error_code를 받아서, 프론트엔드가 사장님께 보여주기 좋은 부드러운 안내 문구로 번역해 넘겨줍니다.",
            "[에러 분기 1]: '사진이 흐려요', '손톱이 없어요' 류는 시스템 잘못이 아니니 사장님께 [사진 다시 올리기]를 강권합니다.",
            "[에러 분기 2]: 'AI 서버 접속 끊김' 류는 억울하니까 백엔드가 몰래 재시도(Retry)를 몇 번 돌려보고, 그래도 안 되면 최종 failed 처리와 함께 [재분석] 버튼을 띄웁니다."
        ],
        "events": [
            ["[에러] NO_NAIL / LOW_QUALITY", "사용자 조치 필요 모드 전환", "사장님 화면에 '사진을 너무 멀리서 찍었거나 손톱이 안 보여요. 다른 사진을 올려주세요'라고 친절히 띄웁니다.", "이 상황에선 자동 재시도해봤자 똑같으니 백엔드 리소스 낭비하지 마세요."],
            ["[에러] INTERNAL_ERROR", "백엔드 몰래 자동 재시도", "일단 사장님한텐 계속 '분석 중 ⏳'으로 뻥을 치면서 뒤에선 다시 AI를 찔러봅니다.", "3번 찔러도 안 되면 그제야 뱃지를 '분석 실패 🚨'로 바꾸고 눈물을 머금고 수동 재분석 버튼을 띄웁니다."],
            ["[에러] INAPPROPRIATE", "유해 콘텐츠 차단 모드", "욕설, 야한 사진 등이 걸러졌으므로 단호하게 '등록할 수 없는 사진입니다'라고 안내합니다.", "이건 절대 자동 재시도하면 안 됩니다."]
        ],
        "qa": [
            "성공이든 실패든 AI가 뱉어내는 모든 실패 콜백에 빈칸 없이 `error_code`가 확실히 들어있는지 포스트맨으로 찍어보세요.",
            "프론트엔드 코드에 하드코딩된 에러 팝업 문구가 백엔드 error_policy 명세서랑 토씨 하나 안 틀리고 싱크가 잘 맞는지 확인하세요.",
            "백엔드 자동 재시도로 기적적으로 성공했을 때, 찰나의 실패(failed) 상태가 화면에 깜빡이며 잔상으로 남지 않는지 눈 크게 뜨고 확인하세요.",
            "최종 찐 실패 상태가 떨어졌을 때, [수동 재분석] 텍스트 버튼이 제대로 렌더링되고 누르면 큐에 잘 들어가는지 테스트하세요."
        ]
    },
    "dictionary": {
        "call_order": [
            "[AI 맘대로 떠올리기]: 2단계 Classify 모델이 일단 뇌피셜로 온갖 태그 후보를 마구 뽑아냅니다.",
            "[사전 매핑 컷오프]: 뽑아낸 단어들을 style, color, mood, shape 등의 '공식 허가 사전(Dictionary)' 필터망에 부어버립니다.",
            "[백엔드 철통 방어]: 혹시라도 매핑망을 뚫고 이상한 사투리 단어가 백엔드로 넘어오면, 백엔드가 문지기처럼 거부(에러)하거나 조용히 지워버린 채로 DB에 저장합니다.",
            "[사전 업데이트 동기화]: '가을웜톤'이라는 새 태그가 사전에 추가되면, AI-백엔드-프론트(검색 필터) 3곳의 코드에 동시에 추가하고 배포해야 합니다."
        ],
        "events": [
            ["[상황] 기획팀이 새 태그 추가해달라 함", "사전 수정 및 3자 동기화", "프론트 검색 드롭다운에 추가, 백엔드 validation 통과 처리, AI 모델 프롬프트 인지까지 삼위일체로 챙깁니다.", "AI 모델 혼자만 똑똑해져서 새 단어를 뱉게 놔두면 백엔드에서 500 에러 폭탄이 터집니다."],
            ["[상황] AI가 사전에 없는 단어 뱉음", "백엔드 무결성 검증 발동", "프론트엔드로는 절대 그 이상한 단어가 내려가지 않도록 DB 저장 전에 백엔드가 조용히 암살(제거)합니다.", "검색 필터에 '블링블링(X)' 같은 오타가 쌓이는 걸 막기 위한 최후 방어선입니다."]
        ],
        "qa": [
            "AI한테 고의로 '울트라캡짱화려함' 같은 요상한 태그를 강제로 뱉게 테스트 모드를 켰을 때, 백엔드가 DB에 저장 안 하고 철벽 방어하는지 꼭 테스트하세요.",
            "디자인 상세 조회 시 내려오는 `color_palette` 값들이 검색 필터 드롭다운에 있는 옵션 값(value)들과 철자 하나 안 틀리고 일치하는지 비교하세요.",
            "enum(목록)으로 관리되는 `style_category` 값들에 대소문자나 오타가 껴있어서 프론트 렌더링이 깨지지 않는지 확인하세요.",
            "사전 단어를 기획자가 바꿨다고 했을 때, 냅다 코드만 고치지 말고 스크립트(`build_all_collaboration_outputs.py`)를 돌려서 HTML 문서를 최신화했는지 챙겨주세요."
        ]
    },
    "open-questions": {
        "call_order": [
            "[결정 시작]: 기획, 디자인, 백엔드, 프론트가 모여 앉아 미정인 부분(동기/비동기, 타임아웃 룰 등)을 결판냅니다.",
            "[보안/인증]: 비동기 콜백을 쓰기로 했다면, 외부 해커가 콜백 URL로 가짜 완료 메시지를 쏠 수 없도록 인증(Secret Token 등) 규칙과 중복 방지 룰을 세웁니다.",
            "[저장과 만료]: 1단계에서 자른 손톱 이미지 썸네일을 우리 S3에 평생 안고 갈 건지, 한 달 뒤에 날릴 건지 등 돈(인프라 비용)이 걸린 문제를 결정합니다.",
            "[확신도 및 재시도]: AI가 '나 50% 정도 확신해'라고 할 때 이걸 성공으로 쳐줄지(Threshold), 네트워크 에러 시 최대 몇 번까지 다시 찌를지 정책을 확정합니다.",
            "[문서 박제]: 결정이 떨어지면 구두로 끄덕이지 말고 즉시 `spec_text/14_decisions.md`에 박제한 뒤 HTML을 재생성합니다."
        ],
        "events": [
            ["[상황] 정책이 아직 미정일 때", "개발 보류 또는 가짜 뼈대만 짜기", "회의록(결정 기록)이 업데이트될 때까지 로직은 비워두거나 피처 토글(Feature Flag)로 숨겨둡니다.", "프론트 개발자 마음대로 '콜백 오겠지 뭐~' 하고 뇌피셜로 짜지 마세요."],
            ["[상황] 정책이 갑자기 바뀔 때", "문서 재생성 및 영향도 파악", "HTML을 다시 뽑고, 백엔드/LLM/프론트 중 어디 어디를 고쳐야 하는지 빠르게 리스트업합니다.", "Notion에 걸려있는 문서 공유 링크가 최신 버전을 가리키는지 확인해서 서로 다른 문서 보고 싸우지 않게 합니다."]
        ],
        "qa": [
            "백엔드 콜백 URL이 인증 토큰 쪼가리도 없이 완전 무방비 열린 문(Open Door) 상태라 아무나 POST 쏘면 디자인 상태가 휙휙 바뀌진 않는지 보안 점검하세요.",
            "AI가 주는 신뢰도 점수(confidence) 커트라인이 실제 코드 if문에 잘 반영되어 0.3점짜리 쓰레기 태그가 안 남는지 테스트하세요.",
            "임시로 AWS에 올려둔 썸네일 URL이 프론트엔드가 화면에 그리기도 전에 만료되어 엑스박스(403)가 뜨지 않는지 타이밍 계산을 확실히 해두세요.",
            "새로 결정된 뜨끈뜨끈한 항목들이 백엔드 파일(`spec_text/14_decisions.md`)에 잘 새겨졌는지 한 번쯤 크로스 체크해주세요."
        ]
    }
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
        "title": '표준 태그 사전',
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


def resolve_field_refs(mapping, backend, annotations=None):
    annotations = annotations or {}
    refs = []
    missing = []
    for entity, fields in mapping.get("entities", {}).items():
        entity_data = backend["entities"].get(entity)
        if not entity_data:
            missing.append(f"entity:{entity}")
            continue
        entity_notes = annotations.get(entity, {})
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
                    "team_note": entity_notes.get(field, ""),
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


def resolve_step(mapping, backend, llm_spec, source_sections, annotations=None):
    field_refs, missing_fields = resolve_field_refs(mapping, backend, annotations)
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
        "playbook": LLM_STEP_PLAYBOOKS.get(mapping["id"], {}),
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

    preamble_lines = [
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
        "LLM 에러 코드별 처리 규칙:",
    ]
    for code, meaning, owner_message in llm_spec.get("error_codes", []):
        preamble_lines.append(f"- {code}: {meaning} → 사장님 안내: {owner_message}")

    preamble_lines.extend([
        "",
        "디자인 분석 상태별 처리:",
        "- pending/in_progress → \"분석 중\". 사장님 화면에서 하나로 묶어 표시. 고객 미노출.",
        "- done → \"분석 완료\". 고객 노출 가능 (owner 승인 + shop active + design active 조건도 충족 필요).",
        "- failed → \"분석 실패\". 재분석 버튼(POST /owner/designs/{id}/reanalyze) 또는 사진 교체 동선 표시.",
    ])
    preamble = "\n".join(preamble_lines).strip()

    sections = []
    all_section_lines = []
    for step in index["steps"]:
        section_lines = [f"## {step['title']}", f"요약: {step['summary']}"]
        if step.get("plain_language"):
            section_lines.append("쉽게 말하면:")
            section_lines.extend(f"- {row}" for row in step["plain_language"])
        if step.get("guide"):
            section_lines.append("구현 가이드:")
            section_lines.extend(f"- {row}" for row in step["guide"])
        if step.get("checkpoints"):
            section_lines.append("체크포인트:")
            section_lines.extend(f"- {row}" for row in step["checkpoints"])
        playbook = step.get("playbook") or {}
        if playbook.get("call_order"):
            section_lines.append("처리/API 순서:")
            section_lines.extend(f"- {row}" for row in playbook["call_order"])
        if playbook.get("events"):
            section_lines.append("이벤트별 처리:")
            section_lines.extend(
                f"- {trigger} -> {process} -> 성공: {success} / 실패: {failure}"
                for trigger, process, success, failure in playbook["events"]
            )
        if playbook.get("qa"):
            section_lines.append("QA/계약 테스트:")
            section_lines.extend(f"- [ ] {row}" for row in playbook["qa"])
        if step.get("contract"):
            contract = step["contract"]
            section_lines.append(f"Endpoint: {contract['endpoint']}")
            section_lines.append("Request fields:")
            section_lines.extend(f"- {field['name']}: {field.get('meaning') or '-'}" for field in contract["request_fields"])
            section_lines.append("Response fields:")
            section_lines.extend(f"- {field['name']}: {field.get('meaning') or '-'}" for field in contract["response_fields"])
        if step.get("field_refs"):
            field_names = ", ".join(f"{ref['entity']}.{ref['name']}" for ref in step["field_refs"])
            section_lines.append(f"관련 백엔드 필드: {field_names}")
        if step.get("api_refs"):
            section_lines.append("관련 백엔드 API:")
            section_lines.extend(
                f"- {ref['endpoint']}: {clip_text(ref.get('easy_purpose') or ref.get('purpose'), 120)}"
                for ref in step["api_refs"]
            )

        sections.append({
            "id": step["id"],
            "title": step["title"],
            "text": "\n".join(section_lines).strip(),
        })
        all_section_lines.append("")
        all_section_lines.extend(section_lines)

    footer_lines = [
        "",
        "표준 태그 사전:",
    ]
    for key, values in llm_spec.get("standard_tags", {}).items():
        footer_lines.append(f"- {key}: {', '.join(values)}")
    footer_lines.extend(["", "논의 필요 질문:"])
    footer_lines.extend(f"- {row}" for row in llm_spec.get("worker_questions", []))

    full_lines = preamble_lines + ["\n단계별 구현 컨텍스트:"] + all_section_lines + footer_lines
    full_text = "\n".join(full_lines).strip() + "\n"

    return {
        "full": full_text,
        "preamble": preamble,
        "sections": sections,
    }


def build_index():
    if not LLM_GUIDE_PATH.exists():
        raise FileNotFoundError(f"LLM 연동 가이드를 찾을 수 없습니다: {LLM_GUIDE_PATH}")
    source_sections = extract_front_sections(LLM_GUIDE_PATH)
    backend = load_backend_data()
    llm_spec = load_llm_spec()
    annotations = {}
    if CANONICAL_PATH.exists():
        with CANONICAL_PATH.open(encoding="utf-8") as f:
            canonical = json.load(f)
        annotations = canonical.get("collaborator_annotations", {}).get("entities", {})
    steps = [resolve_step(item, backend, llm_spec, source_sections, annotations) for item in PIPELINE_MAP]
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
    ai_result = build_ai_brief(index)
    index["ai_brief"] = ai_result["full"]
    index["ai_preamble"] = ai_result["preamble"]
    index["ai_sections"] = ai_result["sections"]
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
    .content { padding: 24px 32px 48px; overflow: auto; }
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
      gap: 16px;
    }
    .panel {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 16px;
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
      padding: 12px 14px;
      text-align: left;
      vertical-align: top;
      line-height: 1.6;
    }
    th {
      background: #f8fafc;
      color: #2d3a4a;
      font-size: 13px;
      font-weight: 700;
    }
    tr:last-child td { border-bottom: 0; }
    ul, ol { margin: 0; padding-left: 20px; line-height: 1.6; }
    li { margin: 8px 0; }
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
    .copy-dropdown { position: relative; display: inline-block; }
    .copy-menu {
      display: none; position: absolute; right: 0; top: 100%;
      background: #fff; border: 1px solid var(--line); border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,.12); z-index: 100;
      min-width: 280px; padding: 4px 0; margin-top: 4px;
    }
    .copy-menu-item {
      display: block; width: 100%; padding: 8px 16px; border: none;
      background: none; text-align: left; cursor: pointer;
      font-size: 13px; color: var(--text); white-space: nowrap;
    }
    .copy-menu-item:hover { background: #f5f7fa; }
    .copy-menu-divider { border-top: 1px solid var(--line); margin: 4px 0; }
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
        <div class="copy-dropdown">
          <button class="copy-btn" id="copyAiBriefBtn" type="button">AI 요약 복사 ▾</button>
          <div class="copy-menu" id="copyMenu">
            <button class="copy-menu-item" data-copy="full" type="button">📋 전체 복사</button>
            <div class="copy-menu-divider"></div>
          </div>
        </div>
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
        ...(step.playbook?.call_order || []),
        ...(step.playbook?.qa || []),
        ...(step.playbook?.events || []).flat(),
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
      const playbook = step.playbook || {};
      const callOrder = playbook.call_order?.length
        ? `<ol>${playbook.call_order.map((row) => `<li>${escapeHtml(row)}</li>`).join("")}</ol>`
        : `<div class="meta">등록된 처리 순서 없음</div>`;
      const qaRows = playbook.qa?.length
        ? `<ul>${playbook.qa.map((row) => `<li><label><input type="checkbox"> ${escapeHtml(row)}</label></li>`).join("")}</ul>`
        : `<div class="meta">등록된 QA/계약 테스트 없음</div>`;
      const eventRows = (playbook.events || []).map((row) => `
        <tr>
          <td>${escapeHtml(row[0])}</td>
          <td>${escapeHtml(row[1])}</td>
          <td>${escapeHtml(row[2])}</td>
          <td>${escapeHtml(row[3])}</td>
        </tr>
      `).join("");
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
          <td class="team-note">${escapeHtml(ref.team_note || "")}</td>
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
          <div class="panel full"><h3>처리/API 순서</h3>${callOrder}</div>
          <div class="panel full"><h3>이벤트별 구현 지시서</h3><table><thead><tr><th>이벤트</th><th>처리</th><th>성공 시</th><th>실패 시</th></tr></thead><tbody>${eventRows || "<tr><td colspan='4'>등록된 이벤트 없음</td></tr>"}</tbody></table></div>
          <div class="panel full"><h3>QA / 계약 테스트</h3>${qaRows}</div>
          <div class="panel full"><h3>LLM 작업자 구현 가이드</h3>${guide}</div>
          <div class="panel full"><h3>Input / Output 계약</h3>${renderContract(step.contract)}</div>
          <div class="panel"><h3>체크포인트</h3>${checkpoints}</div>
          <div class="panel"><h3>원문/백엔드 출처</h3>
            <table><thead><tr><th>LLM 가이드 섹션</th><th>라인</th></tr></thead><tbody>${sourceRows || "<tr><td colspan='2'>연결된 원문 섹션 없음</td></tr>"}</tbody></table>
            <h3>백엔드 파일</h3>
            <table><tbody>${fileRows || "<tr><td>연결된 파일 없음</td></tr>"}</tbody></table>
          </div>
          ${missing}
          <div class="panel full"><h3>관련 백엔드 필드</h3><table><thead><tr><th>필드</th><th>쉽게 말하면</th><th>원문 메모</th><th>팀 메모</th><th>출처</th></tr></thead><tbody>${fieldRows || "<tr><td colspan='5'>관련 필드 없음</td></tr>"}</tbody></table></div>
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

    async function copyToClipboard(text) {
      const status = document.getElementById("copyAiBriefStatus");
      try {
        await navigator.clipboard.writeText(text);
        status.textContent = "복사됨";
      } catch (error) {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        status.textContent = "복사됨";
      }
      document.getElementById("copyMenu").style.display = "none";
      window.setTimeout(function() { status.textContent = ""; }, 1800);
    }

    function buildCopyMenu() {
      const menu = document.getElementById("copyMenu");
      (data.ai_sections || []).forEach(function(sec) {
        const btn = document.createElement("button");
        btn.className = "copy-menu-item";
        btn.setAttribute("data-copy", "section-" + sec.id);
        btn.type = "button";
        btn.textContent = sec.title;
        menu.appendChild(btn);
      });
    }

    document.getElementById("copyAiBriefBtn").addEventListener("click", function(e) {
      const menu = document.getElementById("copyMenu");
      menu.style.display = menu.style.display === "none" ? "block" : "none";
      e.stopPropagation();
    });
    document.addEventListener("click", function() {
      document.getElementById("copyMenu").style.display = "none";
    });
    document.getElementById("copyMenu").addEventListener("click", function(e) {
      const btn = e.target.closest(".copy-menu-item");
      if (!btn) return;
      const key = btn.getAttribute("data-copy");
      let text = "";
      if (key === "full") {
        text = data.ai_brief || "";
      } else if (key.startsWith("section-")) {
        const id = key.replace("section-", "");
        const sec = (data.ai_sections || []).find(function(s) { return s.id === id; });
        text = (data.ai_preamble || "") + "\\n\\n단계별 구현 컨텍스트:\\n\\n" + (sec ? sec.text : "");
      }
      copyToClipboard(text);
    });

    document.getElementById("filterInput").addEventListener("input", renderList);
    document.getElementById("globalSearch").addEventListener("input", renderGlobalResults);
    buildCopyMenu();
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
