import os
import requests
from bs4 import BeautifulSoup
from langchain.tools import tool

@tool
def read_webpage(url: str) -> str:
    """Read the content of a webpage from a given URL and return the text (truncated if too long)."""
    try:
        headers = {
            "User-Agent": os.getenv("SEC_USER_AGENT", "YourName YourEmail@example.com"),
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Loại bỏ các thẻ không cần thiết
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.extract()
            
        body_text = soup.get_text(separator="\n", strip=True)

        # Trả về một phần đủ lớn để phân tích
        return body_text[:8000] + "\n...\n[Truncated]" if len(body_text) > 8000 else body_text

    except Exception as e:
        return f"[Error reading page {url}: {e}]"