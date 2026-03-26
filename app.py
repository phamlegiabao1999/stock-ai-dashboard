import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="AI Stock - Bảo Minh", layout="wide")

# --- 2. DATABASE DANH MỤC ---
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

# --- 3. GIAO DIỆN TÌM KIẾM ---
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
                # --- 4. TÍNH TOÁN KỸ THUẬT ---
                data['MA20'] = data['Close'].rolling(window=20).mean()
                data['STD'] = data['Close'].rolling(window=20).std()
                data['Upper'] = data['MA20'] + (data['STD'] * 2)
                data['Lower'] = data['MA20'] - (data['STD'] * 2)
                
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))

                gia_ht = float(data['Close'].iloc[-1])
                rsi_ht = float(data['RSI'].iloc[-1])
                ma20_ht = float(data['MA20'].iloc[-1])
                lower_ht = float(data['Lower'].iloc[-1])
                upper_ht = float(data['Upper'].iloc[-1])
                ngay_ht = data.index[-1]

                # --- 5. HIỂN THỊ CHỈ SỐ ---
                st.subheader(f"Kết quả cho mã: {ma_final}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Giá hiện tại", f"{gia_ht:,.0f} VNĐ" if "-" not in ma_final else f"${gia_ht:,.2f}")
                c2.metric("Chỉ số RSI", f"{rsi_ht:.2f}")
                c3.metric("So với MA20", f"{((gia_ht/ma20_ht)-1)*100:+.2f}%")

                # --- 6. BIỂU ĐỒ KỸ THUẬT ---
                fig, ax = plt.subplots(figsize=(14, 6))
                ax.plot(data.index, data['Close'], label='Giá đóng cửa', color='#1f77b4', linewidth=2)
                ax.plot(data.index, data['MA20'], label='MA20 (Xu hướng)', color='orange', linestyle='--')
                ax.fill_between(data.index, data['Lower'], data['Upper'], color='gray', alpha=0.1, label='Dải Bollinger')
                
                # Điểm giá hiện tại
                ax.scatter(ngay_ht, gia_ht, color='red', s=70, zorder=5)
                ax.annotate(f"Giá: {gia_ht:,.0f}", (ngay_ht, gia_ht), xytext=(15, 5), textcoords='offset points', 
                            color='white', weight='bold', bbox=dict(boxstyle='round,pad=0.3', fc='red', ec='none'))
                
                ax.legend()
                st.pyplot(fig)

                # --- 7. PHẦN BỔ SUNG DƯỚI BIỂU ĐỒ ---
                st.markdown("---")
                col_left, col_right = st.columns(2)

                with col_left:
                    st.subheader("📚 Giải thích Công thức & Chỉ số")
                    with st.expander("Xem chi tiết các công thức tính"):
                        st.markdown(r"""
                        * **MA20 (Moving Average):** Trung bình giá đóng cửa của 20 ngày gần nhất. 
                            $$MA = \frac{P_1 + P_2 + ... + P_{20}}{20}$$
                        * **RSI (Relative Strength Index):** Chỉ số sức mạnh tương đối, đo lường tốc độ thay đổi giá. 
                            * RSI > 70: Quá mua (Hưng phấn).
                            * RSI < 30: Quá bán (Sợ hãi).
                        * **Bollinger Bands:** Dải băng đo biến động. Khi giá chạm dải dưới (**Lower Band**), thường có xu hướng bật lại.
                        """)
                    
                    st.subheader("💡 Nhận định từ AI")
                    if rsi_ht < 35:
                        st.success("💎 **CƠ HỘI:** Thị trường đang hoảng loạn, giá đi vào vùng quá bán. Đây thường là vùng đáy ngắn hạn.")
                    elif rsi_ht > 70:
                        st.error("🔥 **RỦI RO:** Tâm lý thị trường quá hưng phấn. Tránh mua đuổi (FOMO) tại vùng này.")
                    elif gia_ht > ma20_ht:
                        st.info("📈 **XU HƯỚNG:** Cổ phiếu đang trong đà tăng trưởng mạnh mẽ (Up-trend).")
                    else:
                        st.warning("📉 **XU HƯỚNG:** Cổ phiếu đang suy yếu (Down-trend). Cần tích lũy thêm.")

                with col_right:
                    st.subheader("🎯 Khuyến nghị hành động")
                    
                    # Tạo bảng khuyến nghị
                    rec_data = {
                        "Kịch bản": ["Mua mới", "Đang nắm giữ", "Cắt lỗ"],
                        "Hành động": [
                            f"Chờ mua quanh vùng {lower_ht:,.0f} VNĐ",
                            f"Tiếp tục giữ nếu giá đóng cửa trên {ma20_ht:,.0f}",
                            f"Bán nếu thủng vùng {lower_ht*0.97:,.0f} (lỗ 3%)"
                        ]
                    }
                    st.table(pd.DataFrame(rec_data))

                    st.subheader("🛡️ Quản trị rủi ro")
                    st.write("""
                    1. **Nguyên tắc 2%:** Không để thua lỗ quá 2% tổng tài sản trên mỗi lệnh giao dịch.
                    2. **Chia vốn:** Không bao giờ mua hết 100% vốn tại một mức giá duy nhất.
                    3. **Kỷ luật:** Luôn đặt lệnh dừng lỗ ngay khi vừa khớp lệnh mua.
                    """)

            else:
                st.error("Không tìm thấy dữ liệu!")

st.sidebar.markdown("---")
st.sidebar.write("💻 Hệ thống hỗ trợ quyết định - Bảo Minh MBA")
