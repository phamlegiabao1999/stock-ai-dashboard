import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import time
from google import genai

# --- 1. CẤU HÌNH AI ---
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Thiếu API Key trong Secrets!")

st.set_page_config(page_title="Hệ thống Bảo Minh MBA", layout="wide")

# (Database danh mục giữ nguyên)
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank"}
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name} ({group})")

if "data" not in st.session_state: st.session_state.data = None
if "ma_current" not in st.session_state: st.session_state.ma_current = ""
if "messages" not in st.session_state: st.session_state.messages = []

# --- 2. GIAO DIỆN ---
st.sidebar.header("🔍 Bộ lọc mã")
search_choice = st.sidebar.selectbox("Chọn mã:", options=["Tự nhập mã khác..."] + flat_list)
ma_input = st.sidebar.text_input("Mã:", "").upper().strip() if search_choice == "Tự nhập mã khác..." else search_choice.split(" - ")[0].strip()

btn_analyze = st.sidebar.button("🚀 Bắt đầu phân tích")

# --- 3. XỬ LÝ DỮ LIỆU (FIX LỖI TOO MANY REQUESTS) ---
if (btn_analyze or st.session_state.data is not None) and ma_input:
    if btn_analyze or st.session_state.ma_current != ma_input:
        ts = ma_input + ".VN" if "-" not in ma_input and "." not in ma_input else ma_input
        with st.spinner(f'Đang nạp {ma_input}...'):
            time.sleep(1) # Nghỉ 1 giây để tránh bị Yahoo chặn
            df = yf.download(ts, period="1y", progress=False)
            
            if not df.empty:
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['RSI'] = 50 # Tạm thời fix cứng nếu tính RSI bị lỗi
                st.session_state.data = df
                st.session_state.ma_current = ma_input
                st.session_state.messages = []
            else:
                st.error("⚠️ Yahoo Finance đang chặn kết nối. Hãy đợi 2-3 phút rồi thử lại.")

    if st.session_state.data is not None:
        df = st.session_state.data
        g_ht = float(df['Close'].iloc[-1].item())
        
        st.title(f"📈 Phân tích: {st.session_state.ma_current}")
        st.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ")

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df['Close'], color='#1f77b4', label='Giá')
        st.pyplot(fig)

        # --- 4. CHAT AI (BẢN FIX 404) ---
        st.markdown("---")
        st.subheader(f"💬 Chat AI về {st.session_state.ma_current}")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Hỏi AI..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    # GỌI MODEL THẲNG TÊN gemini-1.5-flash
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=f"Mã {st.session_state.ma_current}, Giá {g_ht:,.0f}. Trả lời ngắn gọn: {prompt}"
                    )
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"AI đang bận hoặc lỗi: {e}")

st.sidebar.write("💻 Hệ thống Bảo Minh MBA")
