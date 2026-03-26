import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from google import genai

# --- 1. CẤU HÌNH AI ---
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("⚠️ Chưa cấu hình GEMINI_API_KEY trong Secrets.")

st.set_page_config(page_title="AI Stock - Bảo Minh", layout="wide")

# (Giữ nguyên database danh mục)
stock_dict = {
    "FMCG & BÁN LẺ": {"MSN": "Masan", "VNM": "Vinamilk", "MWG": "MWG", "PNJ": "PNJ"},
    "CÔNG NGHỆ & THÉP": {"FPT": "FPT", "HPG": "Hòa Phát", "HSG": "Hoa Sen"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank"},
    "CRYPTO": {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana"}
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name} ({group})")

# --- 2. KHỞI TẠO BỘ NHỚ ---
if "data" not in st.session_state: st.session_state.data = None
if "ma_current" not in st.session_state: st.session_state.ma_current = ""
if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. SIDEBAR ---
st.sidebar.header("🔍 Bộ lọc mã")
search_choice = st.sidebar.selectbox("Chọn mã:", options=["Tự nhập mã khác..."] + flat_list)
if search_choice == "Tự nhập mã khác...":
    ma_input = st.sidebar.text_input("Mã:", "").upper().strip()
else:
    ma_input = search_choice.split(" - ")[0].strip()

btn_analyze = st.sidebar.button("🚀 Bắt đầu phân tích")

# --- 4. XỬ LÝ DỮ LIỆU ---
if (btn_analyze or st.session_state.data is not None) and ma_input:
    if btn_analyze or st.session_state.ma_current != ma_input:
        ticker_symbol = ma_input + ".VN" if "-" not in ma_input and "." not in ma_input else ma_input
        with st.spinner(f'Đang tải {ma_input}...'):
            df = yf.download(ticker_symbol, period="1y", progress=False)
            if not df.empty:
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
                st.session_state.messages = []

    if st.session_state.data is not None:
        df = st.session_state.data
        g_ht = float(df['Close'].iloc[-1].item())
        rsi_ht = float(df['RSI'].iloc[-1].item())
        ma_ht = float(df['MA20'].iloc[-1].item())
        lw_ht = float(df['Lower'].iloc[-1].item())
        
        st.title(f"📈 {st.session_state.ma_current}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Giá", f"{g_ht:,.0f}")
        c2.metric("RSI", f"{rsi_ht:.2f}")
        c3.metric("vs MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df['Close'], color='#1f77b4', label='Giá')
        ax.plot(df['MA20'], color='orange', linestyle='--', label='MA20')
        ax.fill_between(df.index, df['Lower'], df['Upper'], color='gray', alpha=0.1)
        ax.legend()
        st.pyplot(fig)

        st.markdown("---")
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("📚 Nhận định")
            with st.expander("Công thức"):
                st.latex(r"RSI = 100 - \frac{100}{1 + \frac{Gain}{Loss}}")
            if rsi_ht < 35: st.success("💎 Quá bán.")
            elif rsi_ht > 70: st.error("🔥 Quá mua.")
            else: st.info("Cân bằng.")

        with col_r:
            st.subheader("🎯 Chiến lược")
            st.table(pd.DataFrame({
                "Kịch bản": ["Mua mới", "Giữ", "Cắt lỗ"],
                "Giá": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]
            }))

        # --- 5. CHAT AI (SỬA LỖI 404 TRIỆT ĐỂ) ---
        st.markdown("---")
        st.subheader(f"💬 Chat AI về {st.session_state.ma_current}")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Hỏi AI..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    # Gọi model flash (không có tiền tố models/)
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=f"Mã chứng khoán {st.session_state.ma_current}, Giá {g_ht:,.0f}, RSI {rsi_ht:.2f}. {prompt}"
                    )
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    # PHƯƠNG ÁN DỰ PHÒNG: Thử dùng model gemini-1.5-pro nếu flash lỗi
                    try:
                        response = client.models.generate_content(
                            model="gemini-1.5-pro",
                            contents=f"Dữ liệu mã {st.session_state.ma_current}: {prompt}"
                        )
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e2:
                        st.error(f"Lỗi AI: {e2}")

st.sidebar.write("💻 Bảo Minh MBA")
