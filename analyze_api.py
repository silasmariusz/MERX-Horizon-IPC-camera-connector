import json

input_file = r"d:\Code\merx-horizon-ipc-camera-connector\api\C1.3_API_doc_en_45305f72\book\searchindex.json"
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

docs = data['index']['documentStore']['docs']

with open('api_analysis.txt', 'w', encoding='utf-8') as out:
    out.write("==== EVENTS ====\n")
    for k, v in docs.items():
        title = v.get('title', '')
        if 'Event check' in title or 'Event push' in title or 'Alarm' in title or 'AI' in title:
            out.write(f"{title}\n")
            
    out.write("\n==== PTZ ====\n")
    for k, v in docs.items():
        title = v.get('title', '')
        if 'PTZ' in title:
            out.write(f"{title}\n")
            
    out.write("\n==== MEDIA/RECORD ====\n")
    for k, v in docs.items():
        title = v.get('title', '')
        if 'Record' in title or 'Search' in title:
            out.write(f"{title}\n")
