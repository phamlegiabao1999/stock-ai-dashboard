import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt

# Cấu hình trang
st.set_page_config(page_title="AI Stock - Bảo Minh", layout="wide")
st.title("📈 AI Stock Analysis Dashboard")

# Thanh công cụ bên trái
st.sidebar.header("🔍 Tìm kiếm mã")
ma_nhap = st.sidebar.text_input("Nhập mã (VD: VIC, FPT, HPG, BTC-USD)", "FPT").upper()
ticker = ma_nhap + ".VN" if "." not in ma_nhap and "-" not in ma_nhap else ma_nhap

if st.sidebar.button("Phân tích"):
    # Tải dữ liệu từ Yahoo Finance
    data = yf.download(ticker, period="1y", progress=False)
    
    if not data.empty:
        # TÍNH TOÁN CÔNG THỨC THUẦN (Không dùng thư viện ngoài)
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['STD'] = data['Close'].rolling(window=20).std()
        data['Upper'] = data['MA20'] + (data['STD'] * 2)
        data['Lower'] = data['MA20'] - (data['STD'] * 2)

        gia_ht = float(data['Close'].iloc[-1].item())
        ma20_ht = float(data['MA20'].iloc[-1].item())

        # Hiển thị các chỉ số chính
        col1, col2 = st.columns(2)
        col1.metric("Giá Hiện Tại", f"{gia_ht:,.0f} VNĐ")
        col2.metric("Trung bình MA20", f"{ma20_ht:,.0f} VNĐ")

        # Đưa ra lời khuyên AI
        st.subheader("🤖 Nhận định từ AI")
        if gia_ht > ma20_ht:
            st.success(f"✅ XU HƯỚNG TĂNG: Giá {ma_nhap} đang nằm trên đường trung bình 20 phiên.")
        else:
            st.warning(f"📉 XU HƯỚNG GIẢM: Giá {ma_nhap} đang chịu áp lực điều chỉnh.")

        # Vẽ biểu đồ kỹ thuật
        st.subheader("📊 Biểu đồ biến động 1 năm")
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(data['Close'], label='Giá thị trường', color='#1f77b4', linewidth=2)
        ax.plot(data['MA20'], label='Đường xu hướng MA20', color='#ff7f0e', linestyle='--')
        ax.fill_between(data.index, data['Lower'], data['Upper'], color='gray', alpha=0.1, label='Vùng Bollinger Bands')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        
        # Hiển thị bảng dữ liệu cuối
        with st.expander("Xem bảng giá 5 phiên gần nhất"):
            st.write(data[['Open', 'High', 'Low', 'Close', 'Volume']].tail(5))
    else:
        st.error(f"Không tìm thấy dữ liệu cho mã {ticker}. Bảo kiểm tra lại mã nhé!")

# Ghi chú chân trang
st.sidebar.markdown("---")
st.sidebar.write("💻 Phát triển bởi: Phạm Lê Gia Bảo")
