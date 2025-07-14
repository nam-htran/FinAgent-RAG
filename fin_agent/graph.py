import operator
import os
from typing import TypedDict, Annotated, Sequence, Optional
from dotenv import load_dotenv
import datetime
import json

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from .tools.stock_tools import get_stock_data, calculate_technical_indicators
from .tools.web_tools import read_webpage
from .tools.sec_tools import get_company_info, get_latest_sec_filings

load_dotenv()

# --- AGENTSTATE NÂNG CẤP ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # Thêm các trường để lưu dữ liệu lớn, tránh làm đầy context window
    company_info: Optional[dict]
    stock_csv_data: Optional[str]
    filing_content: Optional[str]


# --- SYSTEM PROMPT ĐÃ ĐƯỢC TỐI ƯU HÓA ---
system_prompt = """You are a `Sequential Tool-Calling Bot`. You MUST follow the steps below in order, ONE AT A TIME.
Your response MUST ALWAYS be a single tool call, until the final step.

**Workflow Protocol: Execute ONE step at a time.**

**Step 1: Get Company Info**
- Action: Call `get_company_info`.

**Step 2: Get SEC Filings**
- Prerequisite: Step 1 complete.
- Action: Call `get_latest_sec_filings` using the `cik` from Step 1.

**Step 3: Get Stock Data**
- Prerequisite: Step 1 complete.
- Action: Call `get_stock_data` using the `ticker` from Step 1 for the last 365 days.

**Step 4: Calculate Technical Indicators**
- Prerequisite: Step 3 complete.
- Action: Call `calculate_technical_indicators`. **Input for this tool is handled automatically.**

**Step 5: Read Filing Content**
- Prerequisite: Step 2 complete.
- Action: Call `read_webpage` using the `url` from Step 2.

**Step 6: FINAL REPORT**
- Prerequisite: ALL previous steps complete.
- Action: Synthesize all information into a final report. This is the ONLY time you generate text.

**Error Handling:**
- If a tool returns an error, STOP and report the error to the user.
"""

# --- Định nghĩa Tools và LLM ---
all_tools = [
    get_stock_data, calculate_technical_indicators,
    get_company_info, get_latest_sec_filings, read_webpage
]
tool_map = {tool.name: tool for tool in all_tools}

llm = ChatOpenAI(
    model="deepseek/deepseek-chat-v3-0324:free",
    temperature=0,
    max_tokens=2048,
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
).bind_tools(all_tools)

# --- Các Node của Graph ---
def call_model(state: AgentState):
    response = llm.invoke(state['messages'])
    return {"messages": [response]}

def call_tool_node(state: AgentState):
    tool_calls = state['messages'][-1].tool_calls
    tool_messages = []
    
    # Tạo một dict để cập nhật state sau khi chạy tools
    state_updates = {}

    for tool_call in tool_calls:
        tool_name = tool_call['name']
        tool_input = tool_call['args']
        tool = tool_map.get(tool_name)
        
        if tool is None:
            output = f"Error: Tool '{tool_name}' not found."
            tool_messages.append(ToolMessage(content=str(output), tool_call_id=tool_call['id']))
            continue

        # --- LOGIC MỚI: XỬ LÝ DỮ LIỆU LỚN ---
        # Nếu là tool tính toán, lấy dữ liệu từ state thay vì từ input
        if tool_name == 'calculate_technical_indicators':
            tool_input['csv_data'] = state['stock_csv_data']
        
        output = tool.invoke(tool_input)

        # Lưu kết quả của các tool quan trọng vào state thay vì messages
        if tool_name == 'get_company_info':
            state_updates['company_info'] = json.loads(output)
            tool_messages.append(ToolMessage(content="Successfully retrieved company info.", tool_call_id=tool_call['id']))
        elif tool_name == 'get_stock_data':
            state_updates['stock_csv_data'] = output
            tool_messages.append(ToolMessage(content="Successfully retrieved stock data. Ready to calculate indicators.", tool_call_id=tool_call['id']))
        elif tool_name == 'read_webpage':
            state_updates['filing_content'] = output
            tool_messages.append(ToolMessage(content="Successfully read filing content.", tool_call_id=tool_call['id']))
        else:
            # Các tool khác trả về kết quả bình thường
            tool_messages.append(ToolMessage(content=str(output), tool_call_id=tool_call['id']))

    state_updates["messages"] = tool_messages
    return state_updates

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
    langchain_history = []
    initial_messages = []
    for msg in history:
        if msg["role"] == "user":
            initial_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            initial_messages.append(AIMessage(content=msg["content"]))
            
    initial_messages.extend([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ])
    
    # Khởi tạo state với các trường rỗng
    initial_state = {
        "messages": initial_messages,
        "company_info": None,
        "stock_csv_data": None,
        "filing_content": None,
    }
    
    return app_graph.invoke(initial_state)