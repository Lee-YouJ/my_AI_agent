import json
import re
import os
import requests

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {file_path}: {e}"

def write_file(file_path, content):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file {file_path}: {e}"

def append_file(file_path, content):
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully appended to {file_path}"
    except Exception as e:
        return f"Error appending file {file_path}: {e}"

def fetch_webpage(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # HTML 태그 제거용
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if len(text) > 4000:
            text = text[:4000] + "\n\n...[내용이 너무 길어 4000자로 생략되었습니다]..."
            
        return text
    except Exception as e:
        return f"Error fetching {url}: {e}"

def process_tool_calls(response_text):
    results = []
    has_tools = False
    
    # 1. <tool_call> 태그 추출 시도
    pattern_tag = r"<tool_call>\s*(.*?)\s*</tool_call>"
    matches_tag = list(re.finditer(pattern_tag, response_text, re.DOTALL))
    
    json_strings = []
    if matches_tag:
        for match in matches_tag:
            json_strings.append(match.group(1).strip())
    else:
        # 2. 마크다운 json 블록 시도 (```json ... ```)
        pattern_md = r"```json\s*(.*?)\s*```"
        matches_md = list(re.finditer(pattern_md, response_text, re.DOTALL))
        if matches_md:
            for match in matches_md:
                text = match.group(1).strip()
                if '"name"' in text:
                    json_strings.append(text)
        else:
            # 3. 전체 응답이 단일 JSON 형태일 경우 시도
            text = response_text.strip()
            if text.startswith("{") and text.endswith("}") and '"name"' in text:
                json_strings.append(text)
            
    for json_str in json_strings:
        try:
            tool_data = json.loads(json_str)
            if "name" in tool_data and "arguments" in tool_data:
                has_tools = True
                name = tool_data.get("name")
                args = tool_data.get("arguments", {})
                
                print(f"\n[🛠️ 시스템 도구가 실행됩니다: {name}({args})]")
                
                if name == "read_file":
                    res = read_file(args.get("file_path"))
                elif name == "write_file":
                    res = write_file(args.get("file_path"), args.get("content"))
                elif name == "append_file":
                    res = append_file(args.get("file_path"), args.get("content"))
                elif name == "fetch_webpage":
                    res = fetch_webpage(args.get("url"))
                else:
                    res = f"알 수 없는 도구: {name}"
                    
                results.append(f"도구 실행결과 ({name}):\n{res}")
        except json.JSONDecodeError as e:
            # 파싱에 실패하면 무시하거나 시스템에 알림
            pass
        except Exception as e:
            results.append(f"도구 실행 중 치명적 오류: {e}")
            
    return has_tools, results
