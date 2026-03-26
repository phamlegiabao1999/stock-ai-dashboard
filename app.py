import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="AI Stock - Bảo Minh", layout="wide")

# 1. TẠO DANH SÁCH GỢI Ý (Database nhỏ)
# Bảo có thể thêm các mã đối tác FMCG khác vào đây nhé
stock_db = {
    "VIC": "Tập đoàn Vingroup - Đa ngành",
    "VHM": "Vinhomes - Bất động sản",
    "FPT": "FPT - Công nghệ viễn thông",
    "HPG": "Hòa Phát - Thép",
    "VNM": "Vinamilk - Sữa, Thực phẩm FMCG",
    "MSN": "Masan Group - Hàng tiêu dùng FMCG",
    "SAB": "Sabeco - Bia rượu, Nước giải khát",
    "MWG": "Thế giới di động - Bán lẻ (Bách Hóa Xanh)",
    "PNJ": "Vàng bạc đá quý Phú Nhuận",
    "VCB": "Vietcombank - Ngân hàng",
    "BTC-USD": "Bitcoin - Tiền điện tử",
    "SOL-USD": "Solana - Tiền điện tử"
}

st.title("📈 AI Stock Analysis Dashboard")

# 2. GIAO DIỆN TÌM KIẾM THÔNG MINH
st.sidebar.header("🔍 Tìm kiếm thông minh")

# Tạo danh sách hiển thị cho người dùng chọn
options = [f"{k} ({v})" for k, v in stock_db.items()]
choice = st.sidebar.selectbox(
    "Chọn hoặc gõ tên công ty/ngành:",
    options=["Tự nhập mã mới..."] + options
)

# Xử lý lấy mã từ lựa chọn
if choice == "Tự nhập mã mới...":
    ma_nhap = st.sidebar.text_input("Nhập mã thủ công (VD: HPG):", "FPT").upper()
else:
    ma_nhap = choice.split(" ")[0] # Lấy 3 chữ cái đầu tiên

ticker = ma_nhap + ".VN" if "." not in ma_nhap and "-" not in ma_nhap else ma_nhap

# --- PHẦN PHÂN TÍCH ---
if st.sidebar.button("Phân tích ngay"):
    data = yf.download(ticker, period="1y", progress=False)
    
    if not data.empty:
        # Tính MA20 và Bollinger
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['STD'] = data['Close'].rolling(window=20).std()
        data['Upper'] = data['MA20'] + (data['STD'] * 2)
        data['Lower'] = data['MA20'] - (data['STD'] * 2)

        gia_ht = float(data['Close'].iloc[-1].item())
        ma20_ht = float(data['MA20'].iloc[-1].item())

        st.info(f"Đang phân tích: {stock_db.get(ma_nhap, ma_nhap)}")

        col1, col2 = st.columns(2)
        col1.metric("Giá Hiện Tại", f"{gia_ht:,.0f} VNĐ")
        col2.metric("Trung bình MA20", f"{ma20_ht:,.0f} VNĐ")

        # Biểu đồ
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(data['Close'], label='Giá', color='#1f77b4', linewidth=2)
        ax.plot(data['MA20'], label='MA20', color='orange', linestyle='--')
        ax.fill_between(data.index, data['Lower'], data['Upper'], color='gray', alpha=0.1)
        ax.legend()
        st.pyplot(fig)
    else:
        st.error("Không tìm thấy dữ liệu. Hãy chắc chắn mã đúng.")

st.sidebar.markdown("---")
st.sidebar.write("💻 Phát triển bởi: Phạm Lê Gia Bảo")
