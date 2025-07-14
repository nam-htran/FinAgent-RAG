import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
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
        with st.spinner("Agent is running the full analysis... This may take a moment."):
            try:
                history = st.session_state.messages[:-1]
                
                # Chạy toàn bộ chuỗi agent và chờ kết quả cuối cùng
                final_result = run_agent_chain(prompt, history)
                
                print("--- FINAL AGENT RESULT ---")
                print(final_result)
                print("--------------------------")
                
                # --- LOGIC MỚI: TÌM CÂU TRẢ LỜI ĐÚNG ---
                final_response = ""
                if final_result and final_result.get('messages'):
                    # Lặp ngược từ cuối để tìm tin nhắn cuối cùng CÓ NỘI DUNG của assistant
                    for msg in reversed(final_result['messages']):
                        if isinstance(msg, AIMessage) and msg.content.strip():
                            final_response = msg.content
                            break # Dừng lại khi tìm thấy
                
                if not final_response:
                    final_response = "Sorry, I ran into an issue and couldn't generate a final report. Please check the logs."

                st.markdown(final_response)
                st.session_state.messages.append({"role": "assistant", "content": final_response})

            except Exception as e:
                traceback.print_exc()
                error_message = f"An unexpected error occurred: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})