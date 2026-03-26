import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import google.generativeai as genai

# --- 1. CẤU HÌNH API GEMINI (LẤY TỪ STREAMLIT SECRETS) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.warning("⚠️ Chưa cấu hình GEMINI_API_KEY trong phần Secrets của Streamlit.")

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

# --- 4. GIAO DIỆN TÌM KIẾM ---
st.sidebar.header("🔍 Bộ lọc mã chứng khoán")
search_choice = st.sidebar.selectbox("Gõ tên công ty hoặc ngành:", options=["Tự nhập mã khác..."] + flat_list)

if search_choice == "Tự nhập mã khác...":
    ma_final = st.sidebar.text_input("Nhập mã (VD: HPG hoặc BTC-USD):", "").upper()
else:
    ma_final = search_choice.split(" - ")[0]

if ma_final:
    ticker_symbol = ma_final + ".VN" if "-" not in ma_final and "." not in ma_final else ma_final
    
    if st.sidebar.button("🚀 Bắt đầu phân tích"):
        with st.spinner(f'Đang tải dữ liệu {ma_final}...'):
            data = yf.download(ticker_symbol, period="1y", progress=False)
            
            if not data.empty:
                # TÍNH TOÁN KỸ THUẬT
                data['MA20'] = data['Close'].rolling(window=20).mean()
                data['STD'] = data['Close'].rolling(window=20).std()
                data['Upper'] = data['MA20'] + (data['STD'] * 2)
                data['Lower'] = data['MA20'] - (data['STD'] * 2)
                
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))

                # Thông số hiện tại
                gia_ht = float(data['Close'].iloc[-1])
                rsi_ht = float(data['RSI'].iloc[-1])
                ma20_ht = float(data['MA20'].iloc[-1])
                lower_ht = float(data['Lower'].iloc[-1])
                upper_ht = float(data['Upper'].iloc[-1])
                ngay_ht = data.index[-1]

                # HIỂN THỊ CHỈ SỐ
                st.subheader(f"Kết quả cho mã: {ma_final}")
                c1, c2, c3 = st.columns(3)
                don_vi = "VNĐ" if "-" not in ma_final else "USD"
                c1.metric("Giá hiện tại", f"{gia_ht:,.0f} {don_vi}")
                c2.metric("Chỉ số RSI", f"{rsi_ht:.2f}")
                c3.metric("So với MA20", f"{((gia_ht/ma20_ht)-1)*100:+.2f}%")

                # BIỂU ĐỒ
                fig, ax = plt.subplots(figsize=(14, 6))
                ax.plot(data.index, data['Close'], label='Giá', color='#1f77b4', linewidth=2)
                ax.plot(data.index, data['MA20'], label='MA20', color='orange', linestyle='--')
                ax.fill_between(data.index, data['Lower'], data['Upper'], color='gray', alpha=0.1)
                
                # Nhãn giá hiện tại
                ax.scatter(ngay_ht, gia_ht, color='red', s=70, zorder=5)
                ax.annotate(f"{gia_ht:,.0f}", (ngay_ht, gia_ht), xytext=(15, 5), textcoords='offset points', 
                            color='white', weight='bold', bbox=dict(boxstyle='round,pad=0.3', fc='red', ec='none'))
                ax.legend()
                st.pyplot(fig)

                # NHẬN ĐỊNH & KHUYẾN NGHỊ
                st.markdown("---")
                col_left, col_right = st.columns(2)
                with col_left:
                    st.subheader("📚 Công thức & Chỉ số")
                    with st.expander("Nhấn để xem chi tiết"):
                        st.write(f"- **MA20:** {ma20_ht:,.0f} (Ngưỡng xu hướng)")
                        st.write(f"- **Bollinger Lower:** {lower_ht:,.0f} (Vùng hỗ trợ mạnh)")
                        st.write(f"- **RSI:** {rsi_ht:.2f} (Sức mạnh thị trường)")
                    
                    if rsi_ht < 35: st.success("💎 **AI NHẬN ĐỊNH:** Vùng quá bán - Cơ hội tích lũy.")
                    elif rsi_ht > 70: st.error("🔥 **AI NHẬN ĐỊNH:** Vùng quá mua - Rủi ro điều chỉnh.")
                    else: st.info("📈 **AI NHẬN ĐỊNH:** Thị trường đang trong trạng thái cân bằng.")

                with col_right:
                    st.subheader("🎯 Chiến lược tham khảo")
                    st.table(pd.DataFrame({
                        "Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
                        "Mức giá": [f"Quanh {lower_ht:,.0f}", f"Trên {ma20_ht:,.0f}", f"Dưới {lower_ht*0.97:,.0f}"]
                    }))

                # --- 5. CHAT AI CÙNG GEMINI ---
                st.markdown("---")
                st.subheader(f"💬 Hỏi đáp cùng Trợ lý AI về {ma_final}")
                
                if "messages" not in st.session_state:
                    st.session_state.messages = []

                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                if prompt := st.chat_input("Hỏi tôi về mã này..."):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    with st.chat_message("assistant"):
                        with st.spinner("AI đang phân tích..."):
                            try:
                                model = genai.GenerativeModel("gemini-1.5-flash")
                                context = f"Bạn là chuyên gia tài chính. Mã {ma_final} có Giá={gia_ht}, RSI={rsi_ht}, MA20={ma20_ht}. Trả lời ngắn gọn."
                                response = model.generate_content([context, prompt])
                                st.markdown(response.text)
                                st.session_state.messages.append({"role": "assistant", "content": response.text})
                            except:
                                st.error("Hãy kiểm tra lại API Key trong phần Secrets!")

            else:
                st.error("Không tìm thấy dữ liệu!")

st.sidebar.markdown("---")
st.sidebar.write("💻 Hệ thống hỗ trợ quyết định - Bảo Minh MBA")
