# 🤖 Ollama 기반 나무위키 검색 & 파일 제어 에이전트

이 프로젝트는 **Ollama (qwen2.5-coder:7b)** 모델을 활용하여 사용자의 복합적인 명령(검색 및 파일 저장)을 수행하는 지능형 AI 에이전트입니다.

## 🚀 주요 특징 (Key Features)

- **Sequential Tool Chaining (연환 호출)**: 한 번의 질문으로 "나무위키 검색 -> 내용 요약 -> 파일 저장" 등의 다단계 작업을 스스로 판단하여 수행합니다.
- **Robust Web Scraping**: `requests`와 `BeautifulSoup`을 사용하여 나무위키의 구성을 분석하고, 봇 차단을 방지하는 헤더 설정을 통해 안정적으로 데이터를 수집합니다.
- **데이터 무결성 보장 (Auto-Substitution)**: AI가 긴 텍스트 대신 `{{result}}`와 같은 자리표시자(Placeholder)를 사용할 경우, 시스템이 이를 자동으로 감지하여 실제 데이터로 치환합니다.
- **Brace-Balancing JSON Parsing**: AI의 응답 속에 섞인 복잡하거나 중첩된 JSON 도구 호출 명령을 정확하게 추출해내는 강력한 파싱 로직을 갖추고 있습니다.
- **가독성 중심 저장**: 나무위키의 단락 구조를 보존하여 줄바꿈이 살아있는 텍스트/마크다운 파일을 생성합니다.

## 🛠 Tech Stack

- **Language**: Python 3.12+
- **Manager**: [uv](https://github.com/astral-sh/uv)
- **LLM**: Ollama (`qwen2.5-coder:7b`)
- **Libraries**: `ollama`, `requests`, `beautifulsoup4`

## 📦 설치 및 실행 방법 (Setup & Run)

1. **의존성 설치**:
   ```bash
   uv sync
   ```

2. **에이전트 실행**:
   ```bash
   uv run main.py
   ```

## 💡 사용 예시 (Usage Example)

에이전트 실행 후 터미널에 다음과 같이 입력해 보세요:

> **"자작나무에 대해 검색해서 자작나무_정보.md 파일로 요약해서 저장해줘. 단락별로 줄바꿈도 꼭 해줘!"**

에이전트는 스스로 다음과 같은 단계를 밟습니다:
1. `search_namuwiki(keyword="자작나무")` 호출
2. 검색된 대량의 데이터를 수신 및 컨텍스트에 유지
3. `write_file(file_path="./자작나무_정보.md", content="...")` 호출
4. 작업 완료 보고

## 🔧 주요 해결 과제 (Technical Challenges Fixed)

- **무한 루프 차단**: 파일 작성 후 무의미하게 다시 읽거나 중복 저장하는 루프 현상을 시스템 프롬프트 규칙을 통해 해결했습니다.
- **JSON 파싱 오류**: 마크다운 블록이나 줄바꿈이 섞인 JSON 응답에서도 도구 호출 명령을 정확히 뽑아내도록 정규표현식 이상의 괄호 매칭 로직을 적용했습니다.
- **공백 및 줄바꿈**: 크롤링 시 단락 구분이 사라지던 문제를 `separator='\n'` 설정을 통해 해결하여 문서의 구조를 보존했습니다.