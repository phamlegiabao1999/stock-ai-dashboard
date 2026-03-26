import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="AI Stock - Bảo Minh", layout="wide")

# 1. DATABASE DANH MỤC
stock_dict = {
    "NHÓM FMCG & BÁN LẺ": {
        "MSN": "Masan Group (Tiêu dùng)",
        "VNM": "Vinamilk (Sữa)",
        "SAB": "Sabeco (Bia rượu)",
        "MWG": "Thế giới di động (Bách Hóa Xanh)",
        "MCH": "Masan Consumer",
        "KDC": "Kido (Dầu ăn, bánh kẹo)"
    },
    "NHÓM CÔNG NGHỆ & SẢN XUẤT": {
        "FPT": "FPT (Công nghệ)",
        "HPG": "Hòa Phát (Thép)",
        "HSG": "Hoa Sen (Thép)",
        "DGC": "Đức Giang (Hóa chất)"
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

# 2. GIAO DIỆN TÌM KIẾM
st.sidebar.header("🔍 Bộ lọc mã chứng khoán")
search_choice = st.sidebar.selectbox("Gõ tên công ty hoặc ngành:", options=["Tự nhập mã khác..."] + flat_list)

if search_choice == "Tự nhập mã khác...":
    ma_final = st.sidebar.text_input("Nhập mã 3 chữ cái:", "").upper()
else:
    ma_final = search_choice.split(" - ")[0]

if ma_final:
    ticker_symbol = ma_final + ".VN" if "-" not in ma_final and "." not in ma_final else ma_final
    
    if st.sidebar.button("🚀 Bắt đầu phân tích"):
        with st.spinner(f'Đang phân tích dữ liệu {ma_final}...'):
            data = yf.download(ticker_symbol, period="1y", progress=False)
            
            if not data.empty:
                # TÍNH TOÁN KỸ THUẬT
                data['MA20'] = data['Close'].rolling(window=20).mean()
                data['STD'] = data['Close'].rolling(window=20).std()
                data['Lower'] = data['MA20'] - (data['STD'] * 2)
                
                # Tính RSI (Sức mạnh tương đối)
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))

                gia_ht = float(data['Close'].iloc[-1].item())
                ma20_ht = float(data['MA20'].iloc[-1].item())
                rsi_ht = float(data['RSI'].iloc[-1].item())
                lower_band = float(data['Lower'].iloc[-1].item())

                # --- HIỂN THỊ CHỈ SỐ ---
                st.subheader(f"Kết quả phân tích mã: {ma_final}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Giá hiện tại", f"{gia_ht:,.0f} VNĐ")
                c2.metric("Chỉ số RSI", f"{rsi_ht:.2f}")
                c3.metric("Biến động", f"{((gia_ht/ma20_ht)-1)*100:.2f}%")

                # --- PHẦN QUAN TRỌNG: NHẬN ĐỊNH MUA/BÁN ---
                st.markdown("### 🤖 Nhận định chiến lược từ AI")
                
                if gia_ht <= lower_band * 1.02 and rsi_ht < 35:
                    st.success(f"💎 **TÍN HIỆU MUA MẠNH:** Giá {ma_final} đang ở vùng quá bán (RSI thấp) và chạm dải dưới. Cơ hội bắt đáy cao!")
                    st.balloons()
                elif rsi_ht > 70:
                    st.error(f"⚠️ **CẢNH BÁO BÁN:** RSI ({rsi_ht:.2f}) cho thấy thị trường đang quá mua. Nguy cơ đảo chiều giảm giá rất cao.")
                elif gia_ht > ma20_ht:
                    st.info(f"📈 **XU HƯỚNG TĂNG:** Cổ phiếu đang vận động trên đường MA20. Phù hợp để tiếp tục nắm giữ.")
                else:
                    st.warning(f"📉 **THẬN TRỌNG:** Giá đang nằm dưới đường trung bình MA20. Xu hướng ngắn hạn yếu, nên đứng ngoài quan sát.")

                # Biểu đồ
                st.subheader("📊 Biểu đồ kỹ thuật")
                fig, ax = plt.subplots(figsize=(12, 5))
                ax.plot(data['Close'], label='Giá', color='#1f77b4', linewidth=2)
                ax.plot(data['MA20'], label='MA20', color='orange', linestyle='--')
                ax.fill_between(data.index, data['MA20'] - (data['STD'] * 2), data['MA20'] + (data['STD'] * 2), color='gray', alpha=0.1)
                ax.legend()
                st.pyplot(fig)
            else:
                st.error("Không tìm thấy dữ liệu!")

st.sidebar.markdown("---")
st.sidebar.write("💻 Hệ thống hỗ trợ quyết định - Bảo Minh MBA")
