import requests
import json
import os
from langchain.tools import tool

# Nên đặt USER_AGENT trong file .env
USER_AGENT = os.getenv("SEC_USER_AGENT", "YourName YourEmail@example.com")

@tool
def get_company_info(company_name_or_ticker: str) -> str:
    """Gets the CIK for a U.S. company from the SEC. Essential for other SEC tools."""
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
        response.raise_for_status()
        companies = response.json()
        for key, value in companies.items():
            if value['ticker'].lower() == company_name_or_ticker.lower() or value['title'].lower() == company_name_or_ticker.lower():
                cik_str = str(value['cik_str']).zfill(10)
                return json.dumps({"ticker": value['ticker'], "company_name": value['title'], "cik": cik_str})
        return f"Could not find information for: {company_name_or_ticker}"
    except Exception as e:
        return f"Error: {e}"

@tool
def get_latest_sec_filings(cik: str, form_type: str = "10-K") -> str:
    """Gets a list of recent filings (10-K for annual, 10-Q for quarterly) for a U.S. company."""
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=headers)
        response.raise_for_status()
        data = response.json()
        recent_filings = data['filings']['recent']
        filings_by_type = []
        for i in range(len(recent_filings['form'])):
            if recent_filings['form'][i] == form_type:
                # Tạo URL đúng cho file .htm
                doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{recent_filings['accessionNumber'][i].replace('-', '')}/{recent_filings['primaryDocument'][i]}"
                filings_by_type.append({
                    "accession_number": recent_filings['accessionNumber'][i],
                    "filing_date": recent_filings['filingDate'][i],
                    "report_date": recent_filings['reportDate'][i],
                    "url": doc_url
                })
        if not filings_by_type: return f"No {form_type} filings found for CIK {cik}."
        return json.dumps(filings_by_type[:5]) # Trả về 5 báo cáo gần nhất
    except Exception as e:
        return f"Error: {e}"