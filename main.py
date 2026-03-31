import json
import ollama
from file_tools import read_file, write_file, append_file, fetch_webpage, search_namuwiki

def main():
    model_name = "qwen2.5-coder:7b"
    
    system_prompt = """당신은 파일 시스템 호출과 외부 웹사이트 검색에 능통한 스마트한 AI 프로그래밍 에이전트입니다.
사용자를 돕기 위해 파일을 읽거나, 새로 만들거나, 기존 파일에 내용을 추가(수정)할 수 있으며, 필요하다면 나무위키 등에서 정보를 검색하여 작업을 수행합니다.
파일시스템 경로는 항상 './' 와 같은 형태의 상대 경로로 접근하세요.

[필수 규칙]
1. 텍스트로 자신의 계획을 설명하지 말고 오직 JSON 도구 호출만 하세요.
2. 도구 실행 결과(Successfully wrote...)를 다시 파일에 쓰지 마세요.
3. 파일을 성공적으로 생성(write_file)했다면 추가적인 확인 작업(read_file 등)을 하지 말고 사용자에게 보고하며 작업을 종료하세요.
4. 만약 검색(search_namuwiki) 결과가 없거나 오류가 발생했다면, 그 오류 메시지를 파일로 만들지 말고 사용자에게 즉시 보고하세요.
5. 모든 도구의 인자에는 실제 데이터만 넣으세요. 자리표시자 사용 금지.
"""

    print(f"🤖 Ollama 기반 Native Tool Calling 에이전트 (모델: {model_name})")
    print("시스템 프롬프트 기반의 도구(파일 제어, 나무위키 검색) 기능이 활성화되었습니다.")
    print("종료하려면 'exit' 또는 'quit'를 입력하세요.\n")
    print("-" * 50)
    
    # ollama.chat에 전달할 사용 가능한 함수들 (Python Native Tools)
    available_tools = [read_file, write_file, append_file, fetch_webpage, search_namuwiki]
    # 함수 이름으로 실제 함수 객체에 접근하기 위한 Dictionary 준비
    available_functions = {
        'read_file': read_file,
        'write_file': write_file,
        'append_file': append_file,
        'fetch_webpage': fetch_webpage,
        'search_namuwiki': search_namuwiki,
    }

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
            
            # 도구 사용 요청이 있을 경우 AI가 여러 번 연속해서 동작할 수 있도록 연속 호출(Chaining) 루프 처리
            while True:
                response = ollama.chat(
                    model=model_name,
                    messages=messages,
                    tools=available_tools
                )
                
                # 어시스턴트의 현재 응답을 메시지에 기록
                messages.append(response.message)
                
                # 파싱된 도구 호출 리스트
                parsed_tool_calls = []
                
                # 1. Native tool_calls 확인
                if response.message.tool_calls:
                    for tc in response.message.tool_calls:
                        parsed_tool_calls.append({
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                            "id": getattr(tc, 'id', None) # ID가 있으면 저장
                        })
                
                # 2. 본문(content)에서 JSON 추출 (Qwen 모델 대응)
                if not parsed_tool_calls and response.message.content:
                    content_str = response.message.content.strip()
                    potential_jsons = []
                    
                    # 중괄호 균형을 맞춘 추출 시도 (Stack-기반)
                    depth = 0
                    start = -1
                    for i, char in enumerate(content_str):
                        if char == '{':
                            if depth == 0: start = i
                            depth += 1
                        elif char == '}':
                            depth -= 1
                            if depth == 0 and start != -1:
                                potential_jsons.append(content_str[start:i+1])
                                start = -1
                    
                    for block in potential_jsons:
                        try:
                            # 개행 문자 제거 및 JSON 파싱
                            clean_block = block.replace('\n', ' ').replace('\r', ' ')
                            data = json.loads(clean_block)
                            if isinstance(data, dict) and "name" in data and "arguments" in data:
                                parsed_tool_calls.append(data)
                        except json.JSONDecodeError:
                            continue
                
                # 실행할 도구가 없으면 루프 종료 및 최종 답변 출력
                if not parsed_tool_calls:
                    if response.message.content:
                        # 이미 모델이 답을 냈다면 출력
                        print(f"🤖 에이전트: {response.message.content}")
                    break
                    
                # ✅ Sequential Chaining: 첫 번째 도구만 실행하고 결과 환류
                tool_call = parsed_tool_calls[0]
                function_name = tool_call["name"]
                arguments = tool_call["arguments"]
                tool_id = tool_call.get("id")
                
                print(f"\n[🛠️ 시스템 도구가 실행됩니다: {function_name}]")
                # 인자 출력 시 가독성 위해 요약
                arg_str = str(arguments)
                display_arg = arg_str[:100] if len(arg_str) > 100 else arg_str
                print(f"   인자: {display_arg}...")
                
                if function_name in available_functions:
                    function_to_call = available_functions[function_name]
                    try:
                        if isinstance(arguments, dict):
                            # [HACK] Placeholder Auto-Substitution
                            # 모델이 {{result}}, <content>, [data] 등을 쓰면 이전 도구 결과를 자동으로 주입
                            import re
                            for key, value in arguments.items():
                                if isinstance(value, str):
                                    # {{ }}, < >, [[ ]], [ ] 형식의 자리표시자 감지 (공백 무시)
                                    if re.search(r'\{\{.*?\}\}|<.*?>|\[\[.*?\]\]', value) or value.strip().lower() in ["{{result}}", "{{content}}", "{{text}}", "result", "content"]:
                                        # 가장 최근의 'tool' 역할 메시지나 이전 결과를 찾음
                                        prev_result = ""
                                        for msg in reversed(messages):
                                            # 메시지가 Message 객체이거나 dict일 수 있으므로 두 가지 경우 모두 체크
                                            role = getattr(msg, 'role', None) or (msg.get('role') if isinstance(msg, dict) else None)
                                            if role == "tool":
                                                prev_result = getattr(msg, 'content', "") or (msg.get('content', "") if isinstance(msg, dict) else "")
                                                break
                                        if prev_result:
                                            print(f"   (시스템: 자리표시자 '{value}'를 실제 데이터로 자동 대체했습니다)")
                                            arguments[key] = prev_result
                            
                            result = function_to_call(**arguments)
                        else:
                            result = f"Error: arguments must be a dictionary, got {type(arguments)}"
                    except TypeError as e:
                        result = f"Error: Invalid function arguments - {e}"
                    except Exception as e:
                        result = f"Error during tool execution: {e}"
                else:
                    result = f"Unknown tool: {function_name}"
                    
                # 도구 실행 결과 정제 (JSON 파싱 방해 요소 제거)
                # 단, 줄바꿈(\n)은 가독성을 위해 유지합니다.
                safe_result = (str(result)
                               .replace('\\', '\\\\')   # 역슬래시 이스케이프
                               .replace('"', "'")       # 큰따옴표
                               .replace('\r', '')       # 캐리지 리턴 제거
                               .replace('\t', ' '))     # 탭은 공백으로
                
                # 결과 메시지 생성
                tool_response: dict[str, str] = {
                    "role": "tool",
                    "content": safe_result,
                }
                # 가급적 name이나 tool_call_id 포함 (모델/버전에 따라 다를 수 있음)
                if tool_id and isinstance(tool_id, str):
                    tool_response["tool_call_id"] = tool_id
                else:
                    tool_response["name"] = str(function_name)
                    
                messages.append(tool_response)
                
                # 결과 출력 (사용자 피드백)
                display_result = safe_result[:100] if len(safe_result) > 100 else safe_result
                print(f"   결과: {display_result}...")


                    
                # tool 결과가 추가된 새로운 messages 히스토리를 가지고 다시 ollama.chat 을 호출하기 위해 루프 처음(while True)으로 되돌아감.

        except KeyboardInterrupt:
            print("\n\n👋 에이전트를 종료합니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            break

if __name__ == "__main__":
    main()
