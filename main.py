import requests
import json
import sys
import re
import os

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
                else:
                    res = f"알 수 없는 도구: {name}"
                    
                results.append(f"도구 실행결과 ({name}):\n{res}")
        except json.JSONDecodeError as e:
            # 파싱에 실패하면 무시하거나 시스템에 알림
            pass
        except Exception as e:
            results.append(f"도구 실행 중 치명적 오류: {e}")
            
    return has_tools, results

def main():
    model_name = "qwen2.5-coder:7b"
    url = "http://localhost:11434/api/chat"
    
    system_prompt = """당신은 파일 시스템에 직접 접근할 수 있는 유능한 AI 프로그래밍 에이전트입니다.
사용자를 돕기 위해 파일을 읽거나, 새로 만들거나, 기존 파일에 내용을 추가(수정)할 수 있습니다.
작업을 위해 파일 제어가 필요하다면, **반드시 아래 포맷 중 하나로** 출력하여 도구 실행을 시스템에 요청하세요.

<tool_call>
{
  "name": "도구이름",
  "arguments": {
    "인자명": "값"
  }
}
</tool_call>

사용 가능한 'name'과 'arguments' 형식:
1. "read_file": 파일을 읽습니다. 인자: {"file_path": "./대상 파일 경로"}
2. "write_file": 파일에 새 내용을 씁니다(덮어쓰기). 인자: {"file_path": "./대상 파일 경로", "content": "새로 쓸 내용"}
3. "append_file": 기존 파일 끝에 내용을 추가합니다. 인자: {"file_path": "./대상 파일 경로", "content": "추가할 내용"}

**매우 중요한 규칙 (반드시 지킬 것):**
- 파일 경로는 무조건 현재 디렉토리('./')를 기준으로 상대 경로로 작성하세요. 절대 경로('/test' 등)는 사용하지 마세요!
- 도구를 호출한 후에는 자신이 실행 결과를 상상하거나 지어내지 마세요. 도구를 출력한 후에는 바로 응답을 멈추고 시스템의 실제 응답("시스템 도구 실행 결과:")이 주어질 때까지 기다려야 합니다.
- 여러 개 도구를 동시에 쓸 수도 있습니다. (여러 개의 <tool_call> 블록 출력)"""

    print(f"🤖 Ollama 파일 에이전트에 오신 것을 환영합니다! (모델: {model_name})")
    print("시스템 프롬프트 기반의 도구(파일 읽기/쓰기/수정) 사용 기능이 활성화되었습니다.")
    print("종료하려면 'exit' 또는 'quit'를 입력하세요.\n")
    print("-" * 50)
    
    messages = [{"role": "system", "content": system_prompt}]
    
    while True:
        try:
            user_input = input("\n👤 사용자: ")
            if user_input.lower() in ['exit', 'quit']:
                print("👋 에이전트를 종료합니다.")
                break
            if not user_input.strip():
                continue
                
            messages.append({"role": "user", "content": user_input})
            
            # 도구 사용 요청이 있을 경우 AI가 여러 번 연속해서 동작할 수 있도록 루프 처리
            while True:
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "stream": True, # 스트리밍 유지
                    "options": {
                        "stop": ["시스템 도구 실행 결과:", "**시스템 도구 실행 결과:**"]
                    }
                }
                
                print("🤖 에이전트: ", end='', flush=True)
                
                response = requests.post(url, json=payload, stream=True)
                response.raise_for_status()
                
                assistant_response = ""
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            content = chunk["message"]["content"]
                            print(content, end='', flush=True)
                            assistant_response += content
                        if chunk.get("done"):
                            break
                            
                print()
                messages.append({"role": "assistant", "content": assistant_response})
                
                # 도구 호출 검출 및 실행
                has_tools, tool_results = process_tool_calls(assistant_response)
                
                if has_tools:
                    # 결과를 시스템 메시지로 다시 전달하여 AI가 결과를 보고 후속 조치를 하도록 유도
                    feedback = "\n".join(tool_results)
                    print(f"\n[시스템 ➜ 에이전트로 결과 전달 중...]")
                    messages.append({"role": "user", "content": f"시스템 도구 실행 결과:\n{feedback}"})
                    continue # AI에게 다시 요청
                
                # 도구 호출이 없으면 그냥 사용자의 턴으로 넘어감
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 에이전트를 종료합니다.")
            break
        except requests.exceptions.RequestException as e:
            print(f"\n❌ 서버 연결 오류: {e}")
            break
        except Exception as e:
            print(f"\n❌ 알 수 없는 오류 발생: {e}")
            break

if __name__ == "__main__":
    main()
