import requests
import json
import sys

def main():
    model_name = "qwen2.5-coder:7b"
    url = "http://localhost:11434/api/chat"
    
    print(f"🤖 Ollama 터미널 채팅에 오신 것을 환영합니다! (모델: {model_name})")
    print("종료하려면 'exit' 또는 'quit'를 입력하세요.\n")
    print("-" * 50)
    
    messages = []
    
    while True:
        try:
            user_input = input("\n👤 사용자: ")
            if user_input.lower() in ['exit', 'quit']:
                print("👋 채팅을 종료합니다.")
                break
            if not user_input.strip():
                continue
                
            messages.append({"role": "user", "content": user_input})
            
            payload = {
                "model": model_name,
                "messages": messages,
                "stream": True
            }
            
            print("🤖 시스템: ", end='', flush=True)
            
            try:
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
                
            except requests.exceptions.RequestException as e:
                print(f"\n❌ 서버 연결 오류: {e}")
                print("Ollama가 실행 중인지 확인해주세요.")
                if messages and messages[-1]['role'] == 'user':
                    messages.pop()
                    
        except KeyboardInterrupt:
            print("\n\n👋 채팅을 종료합니다.")
            break
        except Exception as e:
            print(f"\n❌ 알 수 없는 오류 발생: {e}")
            if messages and messages[-1]['role'] == 'user':
                messages.pop()

if __name__ == "__main__":
    main()
