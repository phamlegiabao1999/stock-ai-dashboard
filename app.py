import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen", "DGC": "Đức Giang"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank", "STB": "Sacombank"}
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name}")

# --- 2. SIDEBAR ---
st.sidebar.header("🔍 Phân tích & So sánh")
main_stock = st.sidebar.selectbox("Chọn mã chính:", options=flat_list)
ma_chinh = main_stock.split(" - ")[0]

# Tính năng so sánh
enable_compare = st.sidebar.checkbox("Thêm mã so sánh")
ma_so_sanh = ""
if enable_compare:
    compare_stock = st.sidebar.selectbox("Chọn mã đối thủ:", options=[x for x in flat_list if x != main_stock])
    ma_so_sanh = compare_stock.split(" - ")[0]

btn_analyze = st.sidebar.button("🚀 Thực hiện phân tích")

# --- 3. HÀM LẤY DỮ LIỆU ---
def get_data(ticker):
    symbol = ticker + ".VN" if "-" not in ticker and "." not in ticker else ticker
    df = yf.download(symbol, period="1y", progress=False)
    if not df.empty:
        # Tính MA20 và Bollinger Bands
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['STD'] = df['Close'].rolling(window=20).std()
        df['Upper'] = df['MA20'] + (df['STD'] * 2)
        df['Lower'] = df['MA20'] - (df['STD'] * 2)
        # Tính RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain/loss)))
    return df

# --- 4. XỬ LÝ CHÍNH ---
if btn_analyze or "main_df" in st.session_state:
    if btn_analyze:
        st.session_state.main_df = get_data(ma_chinh)
        st.session_state.ma_chinh_name = ma_chinh
        if enable_compare:
            st.session_state.compare_df = get_data(ma_so_sanh)
            st.session_state.ma_ss_name = ma_so_sanh
        else:
            st.session_state.compare_df = None

    df = st.session_state.main_df
    
    if not df.empty:
        st.title(f"📊 Phân tích kỹ thuật: {st.session_state.ma_chinh_name}")

        # --- BIỂU ĐỒ NẾN (PLONLY) ---
        fig = go.Figure()

        # Nến Nhật
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name='Nến Nhật'
        ))

        # Đường MA20
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='MA20'))

        # Bollinger Bands
        fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], line=dict(color='rgba(173, 216, 230, 0.4)'), name='Boll Upper'))
        fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], line=dict(color='rgba(173, 216, 230, 0.4)'), fill='tonexty', name='Boll Lower'))

        fig.update_layout(title=f'Biểu đồ nến {st.session_state.ma_chinh_name}', yaxis_title='Giá (VNĐ)', xaxis_rangeslider_visible=False, height=600)
        st.plotly_chart(fig, use_container_width=True)

        # --- PHẦN SO SÁNH ---
        if st.session_state.compare_df is not None:
            st.header(f"⚔️ So sánh hiệu suất: {st.session_state.ma_chinh_name} vs {st.session_state.ma_ss_name}")
            df_ss = st.session_state.compare_df
            
            # Tính % thay đổi để so sánh trên cùng hệ quy chiếu
            df_comp = pd.DataFrame({
                st.session_state.ma_chinh_name: (df['Close'] / df['Close'].iloc[0] - 1) * 100,
                st.session_state.ma_ss_name: (df_ss['Close'] / df_ss['Close'].iloc[0] - 1) * 100
            })
            
            st.line_chart(df_comp)
            st.caption("Biểu đồ thể hiện mức tăng trưởng (%) tính từ đầu năm.")

        # --- CHỈ SỐ VÀ CHIẾN LƯỢC ---
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        rsi_ht = df['RSI'].iloc[-1]
        g_ht = df['Close'].iloc[-1]
        
        with col1:
            st.subheader("💡 Nhận định hành động")
            if rsi_ht < 30: st.success(f"💎 **VÙNG MUA:** RSI {rsi_ht:.2f} (Quá bán)")
            elif rsi_ht > 70: st.error(f"🔥 **VÙNG BÁN:** RSI {rsi_ht:.2f} (Quá mua)")
            else: st.info(f"📉 **THEO DÕI:** RSI {rsi_ht:.2f} (Cân bằng)")
            
            st.write("**Lịch sử giá gần đây:**")
            st.dataframe(df[['Close', 'RSI']].tail(5))

        with col2:
            st.subheader("📋 Bảng kế hoạch MBA")
            lw_ht = df['Lower'].iloc[-1]
            ma_ht = df['MA20'].iloc[-1]
            
            plan = pd.DataFrame({
                "Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
                "Giá mục tiêu": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Thủng {lw_ht*0.97:,.0f}"]
            })
            st.table(plan)

st.sidebar.markdown("---")
st.sidebar.write("💻 **Bảo Minh MBA System**")
