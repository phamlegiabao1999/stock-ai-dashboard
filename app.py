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
    st.warning("⚠️ Hãy kiểm tra GEMINI_API_KEY trong Secrets.")

st.set_page_config(page_title="AI Stock Analytics - Bảo Minh MBA", layout="wide")

# --- 2. DATABASE ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen", "DGC": "Đức Giang"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank", "STB": "Sacombank"}
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name} ({group})")

# --- 3. SESSION STATE ---
if "data" not in st.session_state: st.session_state.data = None
if "ma_current" not in st.session_state: st.session_state.ma_current = ""
if "messages" not in st.session_state: st.session_state.messages = []

# --- 4. SIDEBAR ---
st.sidebar.header("🔍 Bộ lọc mã chứng khoán")
search_choice = st.sidebar.selectbox("Chọn mã:", options=["Tự nhập mã khác..."] + flat_list)
ma_input = st.sidebar.text_input("Nhập mã:", "").upper().strip() if search_choice == "Tự nhập mã khác..." else search_choice.split(" - ")[0].strip()
btn_analyze = st.sidebar.button("🚀 Bắt đầu phân tích")

# --- 5. XỬ LÝ DỮ LIỆU ---
if (btn_analyze or st.session_state.data is not None) and ma_input:
    if btn_analyze or st.session_state.ma_current != ma_input:
        ts = ma_input + ".VN" if "-" not in ma_input and "." not in ma_input else ma_input
        with st.spinner(f'Đang nạp dữ liệu {ma_input}...'):
            df = yf.download(ts, period="1y", progress=False)
            if not df.empty:
                # Tính toán kỹ thuật
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['STD'] = df['Close'].rolling(window=20).std()
                df['Lower'] = df['MA20'] - (df['STD'] * 2)
                df['Upper'] = df['MA20'] + (df['STD'] * 2)
                d = df['Close'].diff()
                g = (d.where(d > 0, 0)).rolling(window=14).mean()
                l = (-d.where(d < 0, 0)).rolling(window=14).mean()
                df['RSI'] = 100 - (100 / (1 + (g/l)))
                
                st.session_state.data = df
                st.session_state.ma_current = ma_input
                st.session_state.messages = []
            else:
                st.error("Không tìm thấy dữ liệu. Hãy thử lại sau!")

    if st.session_state.data is not None:
        df = st.session_state.data
        g_ht = float(df['Close'].iloc[-1].item())
        rsi_ht = float(df['RSI'].iloc[-1].item())
        ma_ht = float(df['MA20'].iloc[-1].item())
        lw_ht = float(df['Lower'].iloc[-1].item())
        up_ht = float(df['Upper'].iloc[-1].item())
        
        st.title(f"📈 Phân tích chuyên sâu: {st.session_state.ma_current}")
        
        # Biểu đồ và Chỉ số
        col_chart, col_data = st.columns([2, 1])
        
        with col_chart:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df['Close'], color='#1f77b4', label='Giá đóng cửa')
            ax.plot(df['MA20'], color='orange', linestyle='--', label='Đường MA20')
            ax.fill_between(df.index, df['Lower'], df['Upper'], color='gray', alpha=0.1, label='Bollinger Bands')
            ax.legend()
            st.pyplot(fig)
            
        with col_data:
            st.subheader("📊 Lịch sử giá gần nhất")
            st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)
            st.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ")
            st.metric("RSI (14 phiên)", f"{rsi_ht:.2f}")

        st.markdown("---")
        
        # KHU VỰC CÔNG THỨC & CHIẾN LƯỢC
        c_left, c_right = st.columns(2)
        
        with c_left:
            st.subheader("📐 Công thức tính toán")
            with st.expander("Xem chi tiết các chỉ số kỹ thuật"):
                st.markdown(r"""
                * **Relative Strength Index (RSI):**
                    $$RSI = 100 - \frac{100}{1 + RS}$$
                * **Bollinger Bands (Dải băng):**
                    $$Upper/Lower = MA20 \pm (2 \times \sigma)$$
                """)
            
            # NHẬN ĐỊNH MUA/BÁN
            st.subheader("💡 Khuyến nghị hành động")
            if rsi_ht < 35:
                st.success(f"💎 **VÙNG MUA:** RSI ({rsi_ht:.2f}) đang ở mức quá bán. Cổ phiếu có dấu hiệu tạo đáy.")
            elif rsi_ht > 70:
                st.error(f"🔥 **VÙNG BÁN:** RSI ({rsi_ht:.2f}) quá cao. Rủi ro điều chỉnh rất lớn.")
            else:
                st.info("📈 **THEO DÕI:** Giá đang vận động ổn định trong vùng tích lũy.")

        with c_right:
            st.subheader("🎯 Chiến lược quản trị rủi ro")
            plan = pd.DataFrame({
                "Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
                "Mức giá mục tiêu": [
                    f"Quanh hỗ trợ {lw_ht:,.0f}",
                    f"Duy trì trên {ma_ht:,.0f}",
                    f"Thủng ngưỡng {lw_ht*0.97:,.0f}"
                ]
            })
            st.table(plan)

        # --- 6. CHAT AI ---
        st.markdown("---")
        st.subheader(f"💬 Chat AI chuyên gia về mã {st.session_state.ma_current}")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Hỏi AI về mã này..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with
