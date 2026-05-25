with open('tools/build_owner_webapp_index.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"AI 분석 중이라 아직 노출되지 않습니다"', "'AI 분석 중이라 아직 노출되지 않습니다'")

with open('tools/build_owner_webapp_index.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("fixed")
