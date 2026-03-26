import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="AI Stock - Bảo Minh", layout="wide")

# 1. DATABASE DANH MỤC MÃ CHỨNG KHOÁN MỞ RỘNG
stock_dict = {
    "NHÓM FMCG & BÁN LẺ": {
        "MSN": "Masan Group (Tiêu dùng)",
        "VNM": "Vinamilk (Sữa)",
        "SAB": "Sabeco (Bia rượu)",
        "MWG": "Thế giới di động (Bách Hóa Xanh)",
        "MCH": "Masan Consumer",
        "BHX": "Bách Hóa Xanh (Dữ liệu qua MWG)",
        "KDC": "Kido (Dầu ăn, bánh kẹo)"
    },
    "NHÓM CÔNG NGHỆ & SẢN XUẤT": {
        "FPT": "FPT (Công nghệ)",
        "HPG": "Hòa Phát (Thép)",
        "HSG": "Hoa Sen (Thép)",
        "DGC": "Đức Giang (Hóa chất)"
    },
    "NHÓM BẤT ĐỘNG SẢN": {
        "VIC": "Vingroup",
        "VHM": "Vinhomes",
        "VRE": "Vincom Retail",
        "NVL": "Novaland",
        "PDR": "Phát Đạt",
        "DXG": "Đất Xanh"
    },
    "NHÓM NGÂN HÀNG": {
        "VCB": "Vietcombank",
        "TCB": "Techcombank",
        "MBB": "MB Bank",
        "STB": "Sacombank",
        "VPB": "VPBank",
        "ACB": "ACB"
    },
    "TIỀN ĐIỆN TỬ (CRYPTO)": {
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
        "SOL-USD": "Solana",
        "BNB-USD": "Binance Coin"
    }
}

# Chuyển đổi Database sang danh sách phẳng để dễ tìm kiếm
flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name} ({group})")

st.title("📈 AI Stock Analysis Dashboard")

# 2. GIAO DIỆN CHỌN MÃ THÔNG MINH
st.sidebar.header("🔍 Bộ lọc mã chứng khoán")

search_choice = st.sidebar.selectbox(
    "Gõ tên công ty hoặc ngành để tìm:",
    options=["Tự nhập mã khác..."] + flat_list
)

if search_choice == "Tự nhập mã khác...":
    ma_final = st.sidebar.text_input("Nhập mã 3 chữ cái (VD: VCB):", "").upper()
else:
    ma_final = search_choice.split(" - ")[0]

# Tự động xử lý đuôi mã
if ma_final:
    ticker_symbol = ma_final + ".VN" if "-" not in ma_final and "." not in ma_final else ma_final
    
    if st.sidebar.button("🚀 Bắt đầu phân tích"):
        with st.spinner(f'Đang tải dữ liệu cho {ma_final}...'):
            data = yf.download(ticker_symbol, period="1y", progress=False)
            
            if not data.empty:
                # Tính toán kỹ thuật
                data['MA20'] = data['Close'].rolling(window=20).mean()
                data['STD'] = data['Close'].rolling(window=20).std()
                data['Upper'] = data['MA20'] + (data['STD'] * 2)
                data['Lower'] = data['MA20'] - (data['STD'] * 2)

                gia_ht = float(data['Close'].iloc[-1].item())
                ma20_ht = float(data['MA20'].iloc[-1].item())

                # Hiển thị kết quả
                st.subheader(f"Phân tích mã: {ma_final}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Giá hiện tại", f"{gia_ht:,.0f}")
                c2.metric("MA20", f"{ma20_ht:,.0f}")
                c3.metric("Biến động", f"{((gia_ht/ma20_ht)-1)*100:.2f}%")

                # Biểu đồ
                fig, ax = plt.subplots(figsize=(12, 5))
                ax.plot(data['Close'], label='Giá', color='#1f77b4')
                ax.plot(data['MA20'], label='MA20', color='orange', linestyle='--')
                ax.fill_between(data.index, data['Lower'], data['Upper'], color='gray', alpha=0.1)
                ax.legend()
                st.pyplot(fig)
            else:
                st.error("Không có dữ liệu cho mã này!")
else:
    st.info("👈 Hãy chọn một mã từ danh sách hoặc nhập mã mới ở thanh bên.")

st.sidebar.markdown("---")
st.sidebar.write("💻 Hệ thống hỗ trợ quyết định - Bảo Minh MBA")
