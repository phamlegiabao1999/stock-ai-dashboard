import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import google.generativeai as genai

# --- 1. CẤU HÌNH API GEMINI ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.warning("⚠️ Hãy cấu hình GEMINI_API_KEY trong phần Secrets của Streamlit để dùng Chat AI.")

# --- 2. CẤU HÌNH TRANG ---
st.set_page_config(page_title="AI Stock - Bảo Minh", layout="wide")

# --- 3. DATABASE DANH MỤC ---
stock_dict = {
    "NHÓM FMCG & BÁN LẺ": {
        "MSN": "Masan Group", "VNM": "Vinamilk", "SAB": "Sabeco",
        "MWG": "Thế giới di động", "MCH": "Masan Consumer", "KDC": "Kido"
    },
    "NHÓM CÔNG NGHỆ & SẢN XUẤT": {
        "FPT": "FPT", "HPG": "Hòa Phát", "HSG": "Hoa Sen", "DGC": "Đức Giang"
    },
    "NHÓM BẤT ĐỘNG SẢN": {
        "VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail",
        "NVL": "Novaland", "PDR": "Phát Đạt", "DXG": "Đất Xanh"
    },
    "NHÓM NGÂN HÀNG": {
        "VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank",
        "STB": "Sacombank", "VPB": "VPBank", "ACB": "ACB"
    },
    "TIỀN ĐIỆN TỬ (CRYPTO)": {
        "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum",
        "SOL-USD": "Solana", "BNB-USD": "Binance Coin"
    }
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name} ({group})")

st.title("📈 AI Stock Analysis Dashboard")

# --- 4. KHỞI TẠO BỘ NHỚ (SESSION STATE) ---
if "data" not in st.session_state:
    st.session_state.data = None
if "ma_current" not in st.session_state:
    st.session_state.ma_current = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. GIAO DIỆN TÌM KIẾM ---
st.sidebar.header("🔍 Bộ lọc mã chứng khoán")
search_choice = st.sidebar.selectbox("Gõ tên công ty hoặc ngành:", options=["Tự nhập mã khác..."] + flat_list)

if search_choice == "Tự nhập mã khác...":
    ma_input = st.sidebar.text_input("Nhập mã (VD: HPG hoặc BTC-USD):", "").upper()
else:
    ma_input = search_choice.split(" - ")[0]

# Nút bấm chính
btn_analyze = st.sidebar.button("🚀 Bắt đầu phân tích")

# Kiểm tra nếu người dùng đổi mã khác thì xóa dữ liệu cũ
if ma_input != st.session_state.ma_current:
    st.session_state.data = None
    st.session_state.messages = [] # Xóa chat cũ khi đổi mã

# LUỒNG XỬ LÝ CHÍNH
if btn_analyze or st.session_state.data is not None:
    if btn_analyze or st.session_state.data is None:
        with st.spinner(f'Đang tải dữ liệu {ma_input}...'):
            ticker_symbol = ma_input + ".VN" if "-" not in ma_input and "." not in ma_input else ma_input
            try:
                df_raw = yf.download(ticker_symbol, period="1y", progress=False)
                if not df_raw.empty:
                    # Tính toán kỹ thuật
                    df_raw['MA20'] = df_raw['Close'].rolling(window=20).mean()
                    df_raw['STD'] = df_raw['Close'].rolling(window=20).std()
                    df_raw['Upper'] = df_raw['MA20'] + (df_raw['STD'] * 2)
                    df_raw['Lower'] = df_raw['MA20'] - (df_raw['STD'] * 2)
                    
                    delta = df_raw['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    df_raw['RSI'] = 100 - (100 / (1 + rs))
                    
                    st.session_state.data = df_raw
                    st.session_state.ma_current = ma_input
                else:
                    st.error("Không tìm thấy dữ liệu!")
            except Exception as e:
                st.error(f"Lỗi tải dữ liệu: {e}")

    # Nếu đã có dữ liệu trong bộ nhớ, hiển thị ra
    if st.session_state.data is not None:
        data = st.session_state.data
        gia_ht = float(data['Close'].iloc[-1])
        rsi_ht = float(data['RSI'].iloc[-1])
        ma20_ht = float(data['MA20'].iloc[-1])
        lower_ht = float(data['Lower'].iloc[-1])
        ngay_ht = data.index[-1]

        # Hiển thị Metric
        st.subheader(f"Kết quả cho mã: {st.session_state.ma_current}")
        c1, c2, c3 = st.columns(3)
        dv = "VNĐ" if "-" not in st.session_state.ma_current else "USD"
        c1.metric("Giá hiện tại", f"{gia_ht:,.0f} {dv}")
        c2.metric("Chỉ số RSI", f"{rsi_ht:.2f}")
        c3.metric("So với MA20", f"{((gia_ht/ma20_ht)-1)*100:+.2f}%")

        # Biểu đồ
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(data.index, data['Close'], label='Giá', color='#1f77b4', linewidth=2)
        ax.plot(data.index, data['MA20'], label='MA20', color='orange', linestyle='--')
        ax.fill_between(data.index, data['Lower'], data['Upper'], color='gray', alpha=0.1)
        ax.scatter(ngay_ht, gia_ht, color='red', s=70, zorder=5)
        ax.annotate(f"{gia_ht:,.0f}", (ngay_ht, gia_ht), xytext=(15, 5), textcoords='offset points', 
                    color='white', weight='bold', bbox=dict(boxstyle='round,pad=0.3', fc='red', ec='none'))
        ax.legend()
        st.pyplot(fig)

        # Nhận định & Khuyến nghị
        st.markdown("---")
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("💡 Nhận định từ AI")
            if rsi_ht < 35: st.success("💎 **Vùng quá bán:** Cơ hội tích lũy đáy.")
            elif rsi_ht > 70: st.error("🔥 **Vùng quá mua:** Rủi ro điều chỉnh cao.")
            else: st.info("📈 **Trạng thái:** Cổ phiếu đang tích lũy cân bằng.")
        
        with col_r:
            st.subheader("🎯 Chiến lược tham khảo")
            st.table(pd.DataFrame({
                "Kịch bản": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
                "Mức giá": [f"Quanh {lower_ht:,.0f}", f"Trên {ma20_ht:,.0f}", f"Dưới {lower_ht*0.97:,.0f}"]
            }))

        # --- PHẦN CHAT AI ---
        st.markdown("---")
        st.subheader(f"💬 Hỏi đáp AI về mã {st.session_state.ma_current}")
        
        # Hiển thị tin nhắn cũ
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Ô nhập chat
        if prompt := st.chat_input("Hỏi AI về mã này..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("AI đang trả lời..."):
                    try:
                        model = genai.GenerativeModel(model_name="models/gemini-pro")
                        ctx = f"Mã {st.session_state.ma_current}, Giá {gia_ht}, RSI {rsi_ht}, MA20 {ma20_ht}. Trả lời ngắn."
                        resp = model.generate_content([ctx, prompt])
                        st.markdown(resp.text)
                        st.session_state.messages.append({"role": "assistant", "content": resp.text})
                    except Exception as e:
                        st.error(f"Lỗi AI: {e}")

st.sidebar.markdown("---")
st.sidebar.write("💻 Hệ thống hỗ trợ quyết định - Bảo Minh MBA")
