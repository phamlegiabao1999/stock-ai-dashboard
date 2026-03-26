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
            # Tải dữ liệu 1 năm
            data = yf.download(ticker_symbol, period="1y", progress=False)
            
            if not data.empty:
                # --- 4. TÍNH TOÁN KỸ THUẬT (CODE THUẦN PANDAS) ---
                # Tính MA20 và Bollinger Bands
                data['MA20'] = data['Close'].rolling(window=20).mean()
                data['STD'] = data['Close'].rolling(window=20).std()
                data['Upper'] = data['MA20'] + (data['STD'] * 2)
                data['Lower'] = data['MA20'] - (data['STD'] * 2)
                
                # Tính RSI (14)
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))

                # Lấy các thông số cuối cùng
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
                c3.metric("Xu hướng (MA20)", f"{((gia_ht/ma20_ht)-1)*100:+.2f}%")

                # --- 6. NHẬN ĐỊNH AI & VÙNG MUA ---
                st.markdown("### 🤖 Nhận định chiến lược & Vùng mua")
                
                col_info, col_zone = st.columns([2, 1])
                
                with col_info:
                    if rsi_ht < 35:
                        st.success(f"✅ **TÍN HIỆU MUA:** RSI thấp ({rsi_ht:.2f}). Giá đang ở vùng quá bán, tiềm năng hồi phục cao.")
                    elif rsi_ht > 70:
                        st.error(f"❌ **CẢNH BÁO:** RSI quá cao ({rsi_ht:.2f}). Thị trường đang hưng phấn quá mức, nguy cơ chỉnh.")
                    elif gia_ht > ma20_ht:
                        st.info(f"📈 **XU HƯỚNG TĂNG:** Giá nằm trên MA20. Ưu tiên nắm giữ.")
                    else:
                        st.warning(f"📉 **THẬN TRỌNG:** Giá nằm dưới MA20. Cần quan sát thêm điểm cân bằng.")

                with col_zone:
                    # Đề xuất vùng mua dựa trên Lower Band và MA20
                    st.info(f"📍 **Vùng mua tham khảo:**\n\n **{lower_ht:,.0f} - {ma20_ht:,.0f}**")

                # --- 7. BIỂU ĐỒ KỸ THUẬT (HIỂN THỊ GIÁ TRÊN ĐỒ THỊ) ---
                st.subheader("📊 Biểu đồ kỹ thuật chi tiết")
                fig, ax = plt.subplots(figsize=(14, 7))
                
                # Vẽ các đường chính
                ax.plot(data.index, data['Close'], label='Giá đóng cửa', color='#1f77b4', linewidth=2, alpha=0.9)
                ax.plot(data.index, data['MA20'], label='Đường MA20', color='orange', linestyle='--', linewidth=1.5)
                
                # Vẽ vùng Bollinger Bands
                ax.fill_between(data.index, data['Lower'], data['Upper'], color='gray', alpha=0.1, label='Vùng biến động')

                # HIỂN THỊ GIÁ HIỆN TẠI LÊN BIỂU ĐỒ
                ax.scatter(ngay_ht, gia_ht, color='red', s=60, zorder=5) # Chấm đỏ tại điểm cuối
                ax.annotate(f"Hiện tại: {gia_ht:,.0f}", 
                            xy=(ngay_ht, gia_ht),
                            xytext=(15, 0), 
                            textcoords='offset points',
                            va='center',
                            color='white',
                            weight='bold',
                            bbox=dict(boxstyle='round,pad=0.3', fc='red', ec='none', alpha=0.8))

                ax.set_title(f"Diễn biến giá {ma_final}", fontsize=16)
                ax.grid(True, alpha=0.3)
                ax.legend(loc='upper left')
                
                # Làm đẹp trục X (ngày tháng)
                plt.xticks(rotation=0)
                
                st.pyplot(fig)
                
            else:
                st.error("Không tìm thấy dữ liệu! Hãy kiểm tra lại mã chứng khoán.")

st.sidebar.markdown("---")
st.sidebar.write("💻 Hệ thống hỗ trợ quyết định - Bảo Minh MBA")
