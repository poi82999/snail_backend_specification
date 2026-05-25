import re

with open('tools/build_owner_webapp_index.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix nested double quotes
content = content.replace('"입금 완료했어요!"', "'입금 완료했어요!'")
content = content.replace('"AI 분석 중이라 아직 노출되지 않습니다"', "'AI 분석 중이라 아직 노출되지 않습니다'")
content = content.replace('"이 사진 말이야"', "'이 사진 말이야'")
content = content.replace('"분석 중 / 분석 완료 / 실패"', "'분석 중 / 분석 완료 / 실패'")
content = content.replace('"n분째 분석 중입니다"', "'n분째 분석 중입니다'")
content = content.replace('"핑크톤 모아보기"', "'핑크톤 모아보기'")
content = content.replace('"분석 다 끝났어요!"', "'분석 다 끝났어요!'")
content = content.replace('"태그 너무 많이 주지 말고 딱 N개만 뽑아줘"', "'태그 너무 많이 주지 말고 딱 N개만 뽑아줘'")
content = content.replace('"알겠어요!"', "'알겠어요!'")
content = content.replace('"현재 ⏳AI 분석 중입니다"', "'현재 ⏳AI 분석 중입니다'")
content = content.replace('"원룸 배경, 사장님 손가락 등을 싹 다 날리고 오직 예쁜 손톱만 네모 반듯하게 오려내는(Crop) 단계"', "'원룸 배경, 사장님 손가락 등을 싹 다 날리고 오직 예쁜 손톱만 네모 반듯하게 오려내는(Crop) 단계'")
content = content.replace('"이건 손톱이 아닌데?(NO_NAIL)"', "'이건 손톱이 아닌데?(NO_NAIL)'")
content = content.replace('"사진에 손톱이 안 보여요 ㅠㅠ 교체해주세요"', "'사진에 손톱이 안 보여요 ㅠㅠ 교체해주세요'")
content = content.replace('"이건 핑크베이스에 큐빅이 박혔고 분위기는 러블리하군"', "'이건 핑크베이스에 큐빅이 박혔고 분위기는 러블리하군'")
content = content.replace('"표준 태그 사전"', "'표준 태그 사전'")
content = content.replace('"사진이 너무 흐려요(LOW_QUALITY)"', "'사진이 너무 흐려요(LOW_QUALITY)'")
content = content.replace('"손톱이 없어요(NO_NAIL)"', "'손톱이 없어요(NO_NAIL)'")
content = content.replace('"허락된 단어장"', "'허락된 단어장'")
content = content.replace('"이제 시럽 네일 태그도 추가할까요?"', "'이제 시럽 네일 태그도 추가할까요?'")
content = content.replace('"어떻게 할까요?"', "'어떻게 할까요?'")

with open('tools/build_owner_webapp_index.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('tools/build_llm_pipeline_index.py', 'r', encoding='utf-8') as f:
    content2 = f.read()

# Apply same fixes to llm pipeline index
content2 = content2.replace('"분석 중 / 분석 완료 / 실패"', "'분석 중 / 분석 완료 / 실패'")
content2 = content2.replace('"n분째 분석 중입니다"', "'n분째 분석 중입니다'")
content2 = content2.replace('"이 사진 말이야"', "'이 사진 말이야'")
content2 = content2.replace('"핑크톤 모아보기"', "'핑크톤 모아보기'")
content2 = content2.replace('"분석 다 끝났어요!"', "'분석 다 끝났어요!'")
content2 = content2.replace('"태그 너무 많이 주지 말고 딱 N개만 뽑아줘"', "'태그 너무 많이 주지 말고 딱 N개만 뽑아줘'")
content2 = content2.replace('"알겠어요!"', "'알겠어요!'")
content2 = content2.replace('"현재 ⏳AI 분석 중입니다"', "'현재 ⏳AI 분석 중입니다'")
content2 = content2.replace('"원룸 배경, 사장님 손가락 등을 싹 다 날리고 오직 예쁜 손톱만 네모 반듯하게 오려내는(Crop) 단계"', "'원룸 배경, 사장님 손가락 등을 싹 다 날리고 오직 예쁜 손톱만 네모 반듯하게 오려내는(Crop) 단계'")
content2 = content2.replace('"이건 손톱이 아닌데?(NO_NAIL)"', "'이건 손톱이 아닌데?(NO_NAIL)'")
content2 = content2.replace('"사진에 손톱이 안 보여요 ㅠㅠ 교체해주세요"', "'사진에 손톱이 안 보여요 ㅠㅠ 교체해주세요'")
content2 = content2.replace('"이건 핑크베이스에 큐빅이 박혔고 분위기는 러블리하군"', "'이건 핑크베이스에 큐빅이 박혔고 분위기는 러블리하군'")
content2 = content2.replace('"표준 태그 사전"', "'표준 태그 사전'")
content2 = content2.replace('"사진이 너무 흐려요(LOW_QUALITY)"', "'사진이 너무 흐려요(LOW_QUALITY)'")
content2 = content2.replace('"손톱이 없어요(NO_NAIL)"', "'손톱이 없어요(NO_NAIL)'")
content2 = content2.replace('"허락된 단어장"', "'허락된 단어장'")
content2 = content2.replace('"이제 시럽 네일 태그도 추가할까요?"', "'이제 시럽 네일 태그도 추가할까요?'")
content2 = content2.replace('"어떻게 할까요?"', "'어떻게 할까요?'")
content2 = content2.replace('"콜백 오겠지 뭐~"', "'콜백 오겠지 뭐~'")
content2 = content2.replace('"나 50% 정도 확신해"', "'나 50% 정도 확신해'")
content2 = content2.replace('"울트라캡짱화려함"', "'울트라캡짱화려함'")
content2 = content2.replace('"블링블링(X)"', "'블링블링(X)'")
content2 = content2.replace('"가을웜톤"', "'가을웜톤'")
content2 = content2.replace('"등록할 수 없는 사진입니다"', "'등록할 수 없는 사진입니다'")
content2 = content2.replace('"사진을 너무 멀리서 찍었거나 손톱이 안 보여요. 다른 사진을 올려주세요"', "'사진을 너무 멀리서 찍었거나 손톱이 안 보여요. 다른 사진을 올려주세요'")
content2 = content2.replace('"이 원본 주소(image_url) 다운받아서 잘라줘, 다 되면 이 주소(callback_url)로 알려줘"', "'이 원본 주소(image_url) 다운받아서 잘라줘, 다 되면 이 주소(callback_url)로 알려줘'")
content2 = content2.replace('"나 다했어!"', "'나 다했어!'")
content2 = content2.replace('"태그 좀 달아줘"', "'태그 좀 달아줘'")

with open('tools/build_llm_pipeline_index.py', 'w', encoding='utf-8') as f:
    f.write(content2)

print("fixed both")
