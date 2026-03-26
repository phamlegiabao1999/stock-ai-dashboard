import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from google import genai

# --- 1. CẤU HÌNH AI GEMINI ---
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Lỗi: Chưa tìm thấy GEMINI_API_KEY trong phần Secrets của Streamlit!")

st.set_page_config(page_title="AI Stock - Bảo Minh", layout="wide")

# --- 2. DANH MỤC MÃ CHỨNG KHOÁN ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "Thế giới di động", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "Vàng bạc PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen", "DGC": "Đức Giang"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank", "STB": "Sacombank"},
    "CRYPTO": {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana"}
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name} ({group})")

# --- 3. KHỞI TẠO BỘ NHỚ (SESSION STATE) ---
if "data" not in st.session_state: st.session_state.data = None
if "ma_current" not in st.session_state: st.session_state.ma_current = ""
if "messages" not in st.session_state: st.session_state.messages = []

# --- 4. GIAO DIỆN SIDEBAR ---
st.sidebar.header("🔍 Bộ lọc mã")
search_choice = st.sidebar.selectbox("Chọn mã:", options=["Tự nhập mã khác..."] + flat_list)

if search_choice == "Tự nhập mã khác...":
    ma_input = st.sidebar.text_input("Nhập mã (VD: HPG):", "").upper().strip()
else:
    ma_input = search_choice.split(" - ")[0].strip()

btn_analyze = st.sidebar.button("🚀 Bắt đầu phân tích")

# --- 5. XỬ LÝ DỮ LIỆU ---
if (btn_analyze or st.session_state.data is not None) and ma_input:
    # Nếu nhấn nút mới hoặc chưa có dữ liệu cho mã hiện tại
    if btn_analyze or st.session_state.ma_current != ma_input:
        ticker_symbol = ma_input + ".VN" if "-" not in ma_input and "." not in ma_input else ma_input
        with st.spinner(f'Đang nạp dữ liệu {ma_input}...'):
            df = yf.download(ticker_symbol, period="1y", progress=False)
            if not df.empty:
                # Tính toán kỹ thuật cơ bản
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
                st.error("Không lấy được dữ liệu. Kiểm tra lại mã!")

    # HIỂN THỊ KẾT QUẢ
    if st.session_state.data is not None:
        df = st.session_state.data
        g_ht = float(df['Close'].iloc[-1])
        rsi_ht = float(df['RSI'].iloc[-1])
        ma_ht = float(df['MA20'].iloc[-1])
        lw_ht = float(df['Lower'].iloc[-1])
        
        st.title(f"📈 Phân tích: {st.session_state.ma_current}")
        
        # Chỉ số nhanh
        c1, c2, c3 = st.columns(3)
        c1.metric("Giá hiện tại", f"{g_ht:,.0f}")
        c2.metric("Chỉ số RSI", f"{rsi_ht:.2f}")
        c3.metric("So với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

        # Biểu đồ kỹ thuật
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df.index, df['Close'], color='#1f77b4', label='Giá')
        ax.plot(df.index, df['MA20'], color='orange', linestyle='--', label='MA20')
        ax.fill_between(df.index, df['Lower'], df['Upper'], color='gray', alpha=0.1)
        ax.legend()
        st.pyplot(fig)

        st.markdown("---")
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("📚 Nhận định")
            if rsi_ht < 35: st.success("💎 Vùng quá bán. Cơ hội tích lũy.")
            elif rsi_ht > 70: st.error("🔥 Vùng quá mua. Rủi ro điều chỉnh.")
            else: st.info("Thị trường đang ở trạng thái cân bằng.")

        with col_r:
            st.subheader("🎯 Chiến lược")
            st.table(pd.DataFrame({
                "Kịch bản": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
                "Giá tham khảo": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]
            }))

        # --- 6. CHAT AI (FIX LỖI 404 BẰNG CÁCH GỌI TRỰC TIẾP) ---
        st.markdown("---")
        st.subheader(f"💬 Hỏi đáp AI về mã {st.session_state.ma_current}")
        
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Hỏi AI về mã này..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    # Gửi yêu cầu tới Gemini 1.5 Flash (Bỏ models/ phía trước)
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=f"Dữ liệu mã {st.session_state.ma_current}: Giá {g_ht:,.0f}, RSI {rsi_ht:.2f}. Trả lời câu hỏi: {prompt}. Hãy trả lời ngắn gọn, chuyên nghiệp."
                    )
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Lỗi AI: {e}")

st.sidebar.markdown("---")
st.sidebar.write("💻 Bảo Minh MBA")
