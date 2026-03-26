import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt

st.set_page_config(page_title="AI Stock - Bảo Minh", layout="wide")

st.title("📈 AI Stock Analysis Dashboard")
st.sidebar.header("🔍 Tìm kiếm mã")

# Nhập mã
ma_nhap = st.sidebar.text_input("Nhập mã (VD: VIC, FPT, HPG, BTC-USD)", "FPT").upper()
ticker = ma_nhap + ".VN" if "." not in ma_nhap and "-" not in ma_nhap else ma_nhap

if st.sidebar.button("Phân tích"):
    data = yf.download(ticker, period="1y", interval="1d", progress=False)
    
    if not data.empty:
        # Chỉ báo
        data.ta.bbands(length=20, append=True)
        data.ta.rsi(length=14, append=True)
        
        gia_ht = float(data['Close'].iloc[-1].item())
        rsi_ht = float(data['RSI_14'].iloc[-1].item())
        lower_b = float(data['BBL_20_2.0'].iloc[-1].item())

        # Hiển thị
        col1, col2, col3 = st.columns(3)
        col1.metric("Giá Hiện Tại", f"{gia_ht:,.0f}")
        col2.metric("Chỉ số RSI", f"{rsi_ht:.2f}")
        col3.metric("Hỗ trợ MA20", f"{data['BBM_20_2.0'].iloc[-1]:,.0f}")

        # Khuyến nghị
        if gia_ht <= lower_b * 1.02 and rsi_ht < 40:
            st.success("✅ GỢI Ý: NÊN MUA")
        elif rsi_ht > 70:
            st.error("❌ GỢI Ý: QUÁ ĐẮT - KHÔNG MUA")
        else:
            st.warning("🟡 GỢI Ý: THEO DÕI THÊM")

        # Biểu đồ
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(data['Close'], label='Giá', color='blue')
        ax.fill_between(data.index, data['BBL_20_2.0'], data['BBU_20_2.0'], color='gray', alpha=0.2)
        st.pyplot(fig)
    else:
        st.error("Không tìm thấy dữ liệu.")
