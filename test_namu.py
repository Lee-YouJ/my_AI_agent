import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_namuwiki(keyword: str) -> str:
    url = f"https://namu.wiki/w/{urllib.parse.quote(keyword)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    print(f"Fetching {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
            
        article = soup.find('article')
        if article:
            text = article.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)
            
        return text[:500]
    except Exception as e:
        return f"Error: {e}"

print(search_namuwiki('젤다'))
