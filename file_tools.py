import os
import requests
from bs4 import BeautifulSoup
import urllib.parse

def read_file(file_path: str) -> str:
    """
    지정된 경로의 파일 내용을 읽어옵니다. 경로는 반드시 현재 디렉토리('./') 기준 상대 경로를 사용하세요.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {file_path}: {e}"

def write_file(file_path: str, content: str) -> str:
    """
    지정된 경로의 파일에 새로운 내용을 씁니다(덮어쓰기). 경로는 반드시 상대 경로('./')를 사용하세요.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file {file_path}: {e}"

def append_file(file_path: str, content: str) -> str:
    """
    지정된 경로의 기존 파일 끝에 내용을 추가합니다. 경로는 반드시 상대 경로('./')를 사용하세요.
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully appended to {file_path}"
    except Exception as e:
        return f"Error appending file {file_path}: {e}"

def fetch_webpage(url: str) -> str:
    """
    인터넷 웹페이지에 접속하여 텍스트 내용을 읽어옵니다.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if len(text) > 1500:
            text = text[:1500] + "\n\n...[내용이 너무 길어 1500자로 생략되었습니다]..."
            
        return text
    except Exception as e:
        return f"Error fetching {url}: {e}"

def search_namuwiki(keyword: str) -> str:
    """
    사용자가 입력한 키워드를 나무위키(namu.wiki)에서 검색하여 해당 항목의 본문 내용을 가져옵니다.
    """
    if not keyword:
        return "Keyword is required for search."
        
    url = f"https://namu.wiki/w/{urllib.parse.quote(keyword)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        # 403 Forbidden 등으로 요청이 거부될 경우 처리
        if response.status_code == 403:
            return f"Error: 나무위키에서 '{keyword}'를 검색 중 접근 거부(403) 발생. 나중에 다시 시도해 주세요."
        
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 가비지 태그 제거 (스크립트, 스타일, 네비게이션, 푸터 등)
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        # 1. 아티클 태그 검색 우선
        article = soup.find('article')
        if article:
            # 아티클 내에서 위키 보충 정보(분류, 틀 등) 제외 시도
            content_div = article.find('div', class_='wiki-inner-content')
            if content_div:
                text = content_div.get_text(separator='\n', strip=True)
            else:
                text = article.get_text(separator='\n', strip=True)
        else:
            # 2. 아티클 태그가 없는 경우 다른 유력한 콘텐츠 태그 검색
            content = soup.find('div', {'id': 'app'}) or soup.find('div', {'class': 'content'})
            if content:
                text = content.get_text(separator='\n', strip=True)
            else:
                # 3. 최후의 수단으로 전체 텍스트
                text = soup.get_text(separator='\n', strip=True)
            
        # 결과가 너무 길면 LLM 컨텍스트 한계를 고려해 자름 (1500자)
        if len(text) > 1500:
             text = text[:1500] + "\n\n...[내용이 너무 길어 1500자로 생략되었습니다]..."
             
        return text if text.strip() else f"'{keyword}'에 대한 내용을 나무위키에서 찾을 수 없습니다."
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"Error: '{keyword}' 항목이 나무위키에 존재하지 않습니다."
        return f"HTTP error during search: {e}"
    except Exception as e:
        return f"나무위키 검색 중 예기치 못한 오류 발생 ({keyword}): {str(e)}"
