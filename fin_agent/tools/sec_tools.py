# ./fin_agent/tools/sec_tools.py
import requests
import json
import os
from langchain.tools import tool

USER_AGENT = os.getenv("SEC_USER_AGENT", "YourName YourEmail@example.com")

@tool
def get_company_info(company_name_or_ticker: str) -> str:
    """Gets the CIK for a U.S. company from the SEC. Essential for other SEC tools."""
    headers = {'User-Agent': USER_AGENT}
    search_term = company_name_or_ticker.lower()
    try:
        response = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
        response.raise_for_status()
        companies = response.json()
        
        for key, value in companies.items():
            if value['ticker'].lower() == search_term:
                cik_str = str(value['cik_str']).zfill(10)
                return json.dumps({"ticker": value['ticker'], "company_name": value['title'], "cik": cik_str})

        for key, value in companies.items():
            if search_term in value['title'].lower():
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
                
                # --- THAY ĐỔI QUAN TRỌNG BẮT ĐẦU TỪ ĐÂY ---
                accession_number = recent_filings['accessionNumber'][i]
                accession_number_no_dashes = accession_number.replace('-', '')
                
                # Tạo URL trực tiếp đến tệp .txt gốc để đọc dễ dàng hơn
                txt_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession_number_no_dashes}/{accession_number}.txt"
                
                filings_by_type.append({
                    "accession_number": accession_number,
                    "filing_date": recent_filings['filingDate'][i],
                    "report_date": recent_filings['reportDate'][i],
                    "url": txt_url  # Trả về URL của tệp .txt
                })
                # --- THAY ĐỔI QUAN TRỌNG KẾT THÚC TẠI ĐÂY ---

        if not filings_by_type: return f"No {form_type} filings found for CIK {cik}."
        return json.dumps(filings_by_type[:5])
    except Exception as e:
        return f"Error getting filings: {e}"