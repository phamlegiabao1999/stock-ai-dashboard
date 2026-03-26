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
    "FMCG & BÁN LẺ": {"MSN": "Masan", "VNM": "Vinamilk", "MWG": "MWG", "PNJ": "PNJ", "KDC": "Kido"},
    "CÔNG NGHỆ & THÉP": {"FPT": "FPT", "HPG": "Hòa Phát", "HSG": "Hoa Sen", "DGC": "Đức Giang"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank", "ACB": "ACB", "STB": "Sacombank"},
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
    ticker_symbol = ma_input + ".VN" if "-" not in ma_input and "." not in ma_input else ma_input
    with st.spinner(f'Đang tải dữ liệu {ma_input}...'):
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
        else:
            st.error(f"Không tìm thấy dữ liệu!")

# --- 6. HIỂN THỊ KẾT QUẢ ---
if st.session_state.data is not None:
    df = st.session_state.data
    g_ht = float(df['Close'].iloc[-1])
    rsi_ht = float(df['RSI'].iloc[-1])
    ma_ht = float(df['MA20'].iloc[-1])
    lw_ht = float(df['Lower'].iloc[-1])
    up_ht = float(df['Upper'].iloc[-1])
    
    st.title(f"📈 Phân tích mã: {st.session_state.ma_current}")
    
    # Metrics chính
    c1, c2, c3 = st.columns(3)
    c1.metric("Giá hiện tại", f"{g_ht:,.0f}")
    c2.metric("Chỉ số RSI", f"{rsi_ht:.2f}")
    c3.metric("So với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

    # Biểu đồ
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df['Close'], label='Giá', color='#1f77b4', linewidth=2)
    ax.plot(df.index, df['MA20'], label='MA20', color='orange', linestyle='--')
    ax.fill_between(df.index, df['Lower'], df['Upper'], color='gray', alpha=0.1, label='Vùng biến động')
    ax.scatter(df.index[-1], g_ht, color='red', s=70, zorder=5)
    ax.annotate(f"Giá: {g_ht:,.0f}", (df.index[-1], g_ht), xytext=(10, 10), textcoords='offset points', 
                color='white', weight='bold', bbox=dict(boxstyle='round,pad=0.3', fc='red', ec='none'))
    ax.legend()
    st.pyplot(fig)

    st.markdown("---")
    
    # KHU VỰC THÔNG TIN CHI TIẾT
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.subheader("📚 Giải thích & Nhận định AI")
        with st.expander("Xem chi tiết các công thức tính"):
            st.markdown(r"""
            * **MA20:** Trung bình 20 phiên. $$MA = \frac{\sum P_i}{20}$$
            * **RSI:** Sức mạnh giá (14 phiên). 
            * **Bollinger Bands:** Đo độ biến động thị trường.
            """)
        
        if rsi_ht < 35: st.success("💎 **CƠ HỘI:** RSI vùng quá bán. Tiềm năng tạo đáy cao.")
        elif rsi_ht > 70: st.error("🔥 **RỦI RO:** RSI vùng quá mua. Thận trọng điều chỉnh.")
        else: st.info("📈 **TRẠNG THÁI:** Thị trường cân bằng, đang tích lũy.")

    with col_r:
        st.subheader("🎯 Chiến lược & Quản trị")
        rec_df = pd.DataFrame({
            "Kịch bản": ["Mua mới", "Đang giữ", "Cắt lỗ"],
            "Hành động": [
                f"Chờ mua quanh {lw_ht:,.0f}",
                f"Giữ nếu giá trên {ma_ht:,.0f}",
                f"Bán nếu thủng {lw_ht*0.97:,.0f}"
            ]
        })
        st.table(rec_df)

    # --- 7. CHAT AI ---
    st.markdown("---")
    st.subheader(f"💬 Hỏi đáp AI về mã {st.session_state.ma_current}")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Hỏi AI chuyên sâu..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # CÁCH GỌI MODEL MỚI NHẤT ĐỂ TRÁNH LỖI 404
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                ctx = f"Bạn là chuyên gia chứng khoán VN. Mã {st.session_state.ma_current}, Giá {g_ht:,.0f}, RSI {rsi_ht:.2f}, MA20 {ma_ht:,.0f}. Trả lời tiếng Việt ngắn gọn."
                response = model.generate_content([ctx, prompt])
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Lỗi kết nối AI: {e}. Thử lại sau 1 phút.")

st.sidebar.markdown("---")
st.sidebar.write("💻 Bảo Minh MBA")
