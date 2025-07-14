import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
# DÒNG IMPORT ĐÃ ĐƯỢC SỬA LỖI:
from fin_agent.graph import run_agent_chain 
import traceback

# --- Cấu hình trang và tiêu đề ---
st.set_page_config(page_title="FinAgent Pro", layout="wide")
st.title("FinAgent Pro")
st.caption("An AI Agent for financial analysis of U.S. companies (Powered by LangGraph & Streamlit)")

# --- Khởi tạo lịch sử chat ---
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "How can I assist you? Ask about a specific company (e.g., Apple, Tesla)."
    }]

# --- Hiển thị các tin nhắn cũ ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Xử lý input mới từ người dùng ---
if prompt := st.chat_input("e.g., Summarize Apple's latest annual report and technical analysis?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Chạy Agent và hiển thị kết quả (Sử dụng INVOKE) ---
    with st.chat_message("assistant"):
        # Spinner cho người dùng biết agent đang làm việc trong nền
        with st.spinner("Agent is running the full analysis... This may take a moment."):
            try:
                # Lấy lịch sử tin nhắn (trừ tin nhắn cuối cùng của user)
                history = st.session_state.messages[:-1]
                
                # Chạy toàn bộ chuỗi agent và chờ kết quả cuối cùng
                final_result = run_agent_chain(prompt, history)
                
                # Lấy nội dung từ tin nhắn cuối cùng của agent
                if final_result and final_result.get('messages'):
                    final_response = final_result['messages'][-1].content
                else:
                    final_response = "Sorry, I encountered an issue and couldn't get a final response."

                st.markdown(final_response)
                st.session_state.messages.append({"role": "assistant", "content": final_response})

            except Exception as e:
                # Xử lý lỗi một cách chi tiết
                traceback.print_exc() # In lỗi đầy đủ ra terminal để gỡ lỗi
                error_message = f"An unexpected error occurred: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})