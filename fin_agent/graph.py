import operator
import os
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from .tools.stock_tools import get_stock_data, calculate_technical_indicators
from .tools.web_tools import read_webpage
from .tools.sec_tools import get_company_info, get_latest_sec_filings

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# System prompt đã được tối ưu để agent tuân thủ quy trình chặt chẽ
system_prompt = """You are an expert financial analyst AI for U.S. companies. You must follow a strict workflow and chain your tool calls together. Do not explain your steps, just execute them.

**Workflow:**

1.  **Get Company Info:** Start by calling the `get_company_info` tool with the company's name or ticker.

2.  **Extract CIK and Get Filings:** From the JSON output of `get_company_info`, you MUST extract the `cik` value. Immediately use this `cik` to call the `get_latest_sec_filings` tool to find the most recent '10-K' report.

3.  **Get Stock Data:** Use the company's ticker symbol to call `get_stock_data`. Fetch data for the last 365 days.

4.  **Calculate Indicators:** Take the CSV data from the output of `get_stock_data` and pass it directly to the `calculate_technical_indicators` tool.

5.  **Read Filing and Summarize:** After you have the URL for the 10-K report, use the `read_webpage` tool to read its content.

6.  **Final Report:** Only after all previous steps are complete, synthesize all the information gathered (10-K summary, and technical indicators) into a single, concise final report in English. Do not present results individually.
"""

# --- Định nghĩa Tools và LLM ---
all_tools = [
    get_stock_data, calculate_technical_indicators,
    get_company_info, get_latest_sec_filings, read_webpage
]
tool_map = {tool.name: tool for tool in all_tools}

# Model được đề xuất để có kết quả tốt nhất (yêu cầu tài khoản trả phí trên OpenRouter)
# Bạn có thể thử các model khác, nhưng chúng có thể không tuân thủ quy trình tốt bằng.
llm = ChatOpenAI(
    model="deepseek/deepseek-chat",
    temperature=0,
    max_tokens=1024,
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
).bind_tools(all_tools)

# --- Các Node của Graph ---
def call_tool_node(state: AgentState):
    tool_calls = state['messages'][-1].tool_calls
    tool_messages = []
    for tool_call in tool_calls:
        tool_name = tool_call['name']
        tool_input = tool_call['args']
        tool = tool_map.get(tool_name)
        if tool is None:
            output = f"Error: Tool '{tool_name}' not found."
        else:
            output = tool.invoke(tool_input)
        tool_messages.append(ToolMessage(content=str(output), tool_call_id=tool_call['id']))
    return {"messages": tool_messages}

def call_model(state: AgentState):
    response = llm.invoke(state['messages'])
    return {"messages": [response]}

# --- Xây dựng Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    lambda s: "end" if not s['messages'][-1].tool_calls else "continue",
    {"continue": "action", "end": END}
)
workflow.add_edge("action", "agent")
app_graph = workflow.compile()


# --- Hàm chạy chính sử dụng invoke ---
def run_agent_chain(user_input: str, history: list):
    """
    Runs the entire agent chain from start to finish using invoke().
    """
    langchain_history = []
    for msg in history:
        if msg["role"] == "user":
            langchain_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_history.append(AIMessage(content=msg["content"]))

    messages = [
        SystemMessage(content=system_prompt),
        *langchain_history,
        HumanMessage(content=user_input)
    ]
    
    # Sử dụng invoke để chạy toàn bộ chuỗi và chờ kết quả
    return app_graph.invoke({"messages": messages})