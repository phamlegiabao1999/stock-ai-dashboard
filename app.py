import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import google.generativeai as genai

# --- 1. CẤU HÌNH AI ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("⚠️ Hãy cấu hình GEMINI_API_KEY trong phần Secrets của Streamlit.")

st.set_page_config(page_title="AI Stock - Bảo Minh", layout="wide")

# --- 2. DATABASE DANH MỤC ---
stock_dict = {
    "FMCG & BÁN LẺ": {"MSN": "Masan", "VNM": "Vinamilk", "MWG": "MWG", "PNJ": "PNJ"},
    "CÔNG NGHỆ & THÉP": {"FPT": "FPT", "HPG": "Hòa Phát", "HSG": "Hoa Sen"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank", "ACB": "ACB"},
    "CRYPTO": {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana"}
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name} ({group})")

# --- 3. KHỞI TẠO BỘ NHỚ ---
if "data" not in st.session_state: st.session_state.data = None
if "ma_current" not in st.session_state: st.session_state.ma_current = ""
if "messages" not in st.session_state: st.session_state.messages = []

# --- 4. GIAO DIỆN SIDEBAR ---
st.sidebar.header("🔍 Bộ lọc mã")
search_choice = st.sidebar.selectbox("Chọn mã hoặc ngành:", options=["Tự nhập mã khác..."] + flat_list)

if search_choice == "Tự nhập mã khác...":
    ma_input = st.sidebar.text_input("Nhập mã (VD: HPG):", "").upper().strip()
else:
    ma_input = search_choice.split(" - ")[0].strip()

btn_analyze = st.sidebar.button("🚀 Bắt đầu phân tích")

# --- 5. XỬ LÝ DỮ LIỆU ---
if btn_analyze and ma_input:
    # Fix lỗi tải mã trống
    ticker_symbol = ma_input + ".VN" if "-" not in ma_input and "." not in ma_input else ma_input
    with st.spinner(f'Đang tải dữ liệu {ma_input}...'):
        df = yf.download(ticker_symbol, period="1y", progress=False)
        if not df.empty:
            # Tính chỉ số
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['STD'] = df['Close'].rolling(window=20).std()
            df['Lower'] = df['MA20'] - (df['STD'] * 2)
            df['Upper'] = df['MA20'] + (df['STD'] * 2)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain/loss)))
            
            st.session_state.data = df
            st.session_state.ma_current = ma_input
            st.session_state.messages = [] # Reset chat khi đổi mã
        else:
            st.error(f"Không tìm thấy dữ liệu cho mã {ma_input}!")

# --- 6. HIỂN THỊ KẾT QUẢ ---
if st.session_state.data is not None:
    df = st.session_state.data
    g_ht = float(df['Close'].iloc[-1])
    rsi_ht = float(df['RSI'].iloc[-1])
    ma_ht = float(df['MA20'].iloc[-1])
    lw_ht = float(df['Lower'].iloc[-1])
    
    st.title(f"📈 Phân tích mã: {st.session_state.ma_current}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Giá hiện tại", f"{g_ht:,.0f}")
    c2.metric("Chỉ số RSI", f"{rsi_ht:.2f}")
    c3.metric("So với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

    # Vẽ biểu đồ
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df['Close'], label='Giá', color='#1f77b4')
    ax.plot(df.index, df['MA20'], label='MA20', color='orange', linestyle='--')
    ax.fill_between(df.index, df['Lower'], df['Upper'], color='gray', alpha=0.1)
    ax.scatter(df.index[-1], g_ht, color='red', s=50)
    ax.legend()
    st.pyplot(fig)

    # Nhận định chiến lược
    st.markdown("---")
    cl1, cl2 = st.columns(2)
    with cl1:
        st.subheader("🤖 Nhận định AI")
        if rsi_ht < 35: st.success("Vùng quá bán - Tiềm năng tạo đáy.")
        elif rsi_ht > 70: st.error("Vùng quá mua - Rủi ro điều chỉnh.")
        else: st.info("Thị trường cân bằng.")
    with cl2:
        st.subheader("🎯 Chiến lược")
        st.write(f"Vùng mua hỗ trợ: **{lw_ht:,.0f}**")
        st.write(f"Ngưỡng xu hướng: **{ma_ht:,.0f}**")

    # --- 7. CHAT AI (FIX LỖI 404) ---
    st.markdown("---")
    st.subheader(f"💬 Hỏi đáp AI về mã {st.session_state.ma_current}")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Hỏi AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # Dùng model name chuẩn nhất hiện tại
                model = genai.GenerativeModel('gemini-1.5-flash')
                ctx = f"Mã {st.session_state.ma_current}, Giá {g_ht:,.0f}, RSI {rsi_ht:.2f}. Trả lời tiếng Việt ngắn gọn."
                response = model.generate_content([ctx, prompt])
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Lỗi AI: {e}")

st.sidebar.markdown("---")
st.sidebar.write("💻 Bảo Minh MBA")
