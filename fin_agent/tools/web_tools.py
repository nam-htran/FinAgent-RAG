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
        
        # Chỉ cần trả về text thô, không cần phân tích HTML phức tạp với tệp .txt
        body_text = response.text

        # Giảm độ dài để không làm tràn bộ nhớ
        return body_text[:4000] + "\n...\n[Truncated]" if len(body_text) > 4000 else body_text

    except Exception as e:
        return f"[Error reading page {url}: {e}]"