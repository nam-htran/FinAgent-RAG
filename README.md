# FinAgent Pro: AI Financial Analysis Agent

[![Python Version](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Framework: Streamlit](https://img.shields.io/badge/Framework-Streamlit-ff4b4b)](https://streamlit.io)
[![Orchestration: LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-brightgreen)](https://langchain.com/langgraph)

FinAgent Pro is a sophisticated AI-powered agent designed to perform financial analysis of U.S. companies. By leveraging a multi-step, tool-based workflow orchestrated by LangGraph, this agent can retrieve SEC filings, calculate technical stock indicators, and synthesize the information into a concise report. The interactive user interface is built with Streamlit.

*(This is a representative image of the UI)*

---

## Features

- **Automated SEC Filing Retrieval**: Automatically finds a company's CIK and fetches the latest annual (10-K) or quarterly (10-Q) reports directly from the SEC EDGAR database.
- **Technical Indicator Calculation**: Gathers historical stock data using `yfinance` and calculates key technical indicators like RSI, MACD, and SMA using `pandas-ta`.
- **Web Content Parsing**: Intelligently reads the content of SEC filings from the web for analysis.
- **Stateful, Multi-Step Workflow**: Utilizes LangGraph to create a robust, sequential chain of actions, ensuring a reliable analysis process.
- **Conversational Interface**: A simple and intuitive chat interface powered by Streamlit allows users to make requests in natural language.
- **Error Handling**: The agent is designed to identify and report tool execution errors, providing clear feedback to the user.

---

## How It Works: The Agent's Architecture

FinAgent Pro operates as a stateful agent graph. When a user provides a company name, the agent initiates a sequential workflow managed by LangGraph:

1. **Get Company Info**  
   Calls `get_company_info` to find the company's CIK and ticker from SEC data.

2. **Fetch Filings & Stock Data**  
   - Calls `get_latest_sec_filings` to retrieve the most recent 10-K filing (in `.txt` format).  
   - Calls `get_stock_data` to fetch the last 365 days of price history.

3. **Process Data**  
   - Sends stock data to `calculate_technical_indicators`.  
   - Sends filing URL to `read_webpage` to extract text.

4. **Synthesize Final Report**  
   The LLM generates a final summary based on the gathered data.

This process includes robust error handling to inform the user about any failed steps.

---

## Technology Stack

- **Frontend**: Streamlit  
- **AI Orchestration**: LangChain, LangGraph  
- **LLM Provider**: OpenRouter (e.g., DeepSeek, GPT-4o, etc.)  
- **Data Sources**:  
  - SEC EDGAR API  
  - Yahoo Finance (`yfinance`)  
- **Libraries**: `langchain-openai`, `pandas`, `pandas-ta`, `requests`, `beautifulsoup4`

---

## Setup and Installation

### 1. Prerequisites

- Python 3.11+
- `pip` and `venv`

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/FinAgent-RAG.git
cd FinAgent-RAG
```

### 3. Set Up a Virtual Environment

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.env\Scriptsctivate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Copy the example file and update your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
# .env

# Get your key from https://openrouter.ai/keys
OPENROUTER_API_KEY="sk-or-..."

# Required for SEC API access
SEC_USER_AGENT="YourFullName YourEmail@example.com"
```

> ⚠️ The SEC requires a valid `User-Agent`. Generic agents like `python-requests` will be blocked.

### 6. Run the Application

```bash
streamlit run app.py
```

Your browser should now open the app interface.

---

## Usage

Once the app is running, type a query in the chat such as:

- `Analyze the latest annual report for Microsoft`
- `Give me a financial and technical summary for Tesla`
- `Apple 2024 financial report analysis`

The agent will retrieve data, analyze it, and return a summarized report.

---

## Roadmap & Future Improvements

- **Data Visualization**: Add charts with matplotlib or plotly.
- **Streaming Responses**: Show real-time steps of agent reasoning.
- **News Analysis Tool**: Include company news with sentiment scoring.
- **Advanced Caching**: Speed up repeated queries with caching.
- **Model Comparison UI**: Let users test and compare LLM outputs.

---

## Contributing

We welcome contributions!

```bash
# Steps to contribute
1. Fork the repo
2. git checkout -b feature/your-feature-name
3. Make your changes
4. git commit -m "Add your feature"
5. git push origin feature/your-feature-name
6. Open a Pull Request
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
