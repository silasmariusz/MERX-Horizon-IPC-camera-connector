import json

input_file = r"d:\Code\merx-horizon-ipc-camera-connector\api\C1.3_API_doc_en_45305f72\book\searchindex.json"
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

docs = data['index']['documentStore']['docs']

with open('api_login.txt', 'w', encoding='utf-8') as out:
    for k, v in docs.items():
        body = v.get('body', '')
        if 'API/Web/Login' in body:
            out.write(f"=== {v.get('title', '')} ===\n")
            out.write(body[:1500] + "\n\n")
