import json
import sys
import re

def main():
    input_file = r"d:\Code\merx-horizon-ipc-camera-connector\api\C1.3_API_doc_en_45305f72\book\searchindex.json"
    output_file = r"d:\Code\merx-horizon-ipc-camera-connector\API_Documentation.md"

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    doc_urls = data.get("doc_urls", [])
    index = data.get("index", {})
    document_store = index.get("documentStore", {})
    docs = document_store.get("docs", {})
    
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("# MERX Horizon IPC Camera API Documentation\n\n")
        
        for i, url in enumerate(doc_urls):
            doc_id = str(i)
            doc_info = docs.get(doc_id)
            if doc_info:
                title = doc_info.get("title", "")
                body = doc_info.get("body", "")
                
                # Clean up formatting a bit
                body = re.sub(r'\n+', '\n\n', body)
                
                out.write(f"## {title}\n\n")
                out.write(f"**URL:** `{url}`\n\n")
                out.write(f"{body}\n\n")
                out.write("---\n\n")

if __name__ == "__main__":
    main()
