import json

input_file = r"d:\Code\merx-horizon-ipc-camera-connector\api\C1.3_API_doc_en_45305f72\book\searchindex.json"
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

docs = data['index']['documentStore']['docs']

with open('api_details.txt', 'w', encoding='utf-8') as out:
    for k, v in docs.items():
        title = v.get('title', '')
        if 'Event push' in title or 'Event check' in title or 'PTZ' in title or 'Search Record' in title:
            out.write(f"=== {title} ===\n")
            out.write(v.get('body', '')[:1000] + "\n\n")
