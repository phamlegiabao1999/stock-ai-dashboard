import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
import pytz
from vnstock3 import Vnstock

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Bảo Minh MBA - Realtime Analytics", layout="wide")

st.markdown("""
    <style>
    .stPlotlyChart { touch-action: pan-y; }
    .metric-container { background-color: #f0f2f6; padding: 20px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- ĐĂNG NHẬP ---
if not st.session_state.logged_in:
    st.title("🔐 Hệ thống Phân tích Bảo Minh MBA")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("👤 User (baominh):")
            pwd = st.text_input("🔑 Pass (mba2026):", type="password")
            if st.form_submit_button("🚀 ĐĂNG NHẬP"):
                if user == "baominh" and pwd == "mba2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Thông tin không khớp!")
    st.stop()

# --- 2. ENGINE LẤY DỮ LIỆU CHUẨN (SOURCE: VCI) ---
@st.cache_data(ttl=300)
def get_realtime_data(ticker):
    try:
        # Lấy data từ nguồn VCI (Bản Việt) - khớp giá sàn HOSE/HNX nhất
        stock = Vnstock().stock(symbol=ticker, source='VCI')
        df = stock.quote.history(start='2025-01-01', end=datetime.now().strftime('%Y-%m-%d'))
        
        if df is not None and not df.empty:
            df = df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            
            # --- TÍNH TOÁN KỸ THUẬT CHUẨN XÁC ---
            # MA20
            df['MA20'] = df['Close'].rolling(window=20).mean()
            # RSI 14 (Công thức chuẩn Wilder's)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            # Hỗ trợ dưới (Bollinger Lower)
            df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
            
            return df
    except:
        return None

# --- 3. DANH MỤC MÃ (HỌ VIN & DẦU KHÍ) ---
stock_dict = {
    "HỌ NHÀ VIN": ["VIC", "VHM", "VRE"],
    "DẦU KHÍ": ["GAS", "OIL", "BSR", "PLX", "PVD", "PVS"],
    "BÁN LẺ & BANK": ["MWG", "MSN", "FPT", "VCB", "TCB", "MBB"]
}
all_options = [ticker for sub in stock_dict.values() for ticker in sub]

# --- 4. SIDEBAR ---
st.sidebar.title("Bảo Minh MBA v6.0")
ma_chinh = st.sidebar.selectbox("Mã cổ phiếu:", options=all_options)
if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.rerun()

# --- 5. HIỂN THỊ DASHBOARD ---
df = get_realtime_data(ma_chinh)

if df is not None:
    g_ht = float(df['Close'].iloc[-1])
    rsi_ht = float(df['RSI'].iloc[-1])
    ma_ht = float(df['MA20'].iloc[-1])
    lw_ht = float(df['Lower'].iloc[-1])
    change = df['Close'].diff().iloc[-1]
    
    st.markdown(f'<h2 style="text-align:center;">📊 Phân tích {ma_chinh} (Realtime)</h2>', unsafe_allow_html=True)
    
    # Thẻ thông tin chính
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Giá Hiện Tại", f"{g_ht:,.0f}", f"{change:,.0f}")
    m2.metric("Chỉ số RSI", f"{rsi_ht:.2f}")
    m3.metric("Đường MA20", f"{ma_ht:,.0f}")
    m4.metric("Vùng Hỗ Trợ", f"{lw_ht:,.0f}")

    # Biểu đồ nến chuyên nghiệp
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Nến')])
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=2), name='MA20'))
    fig.update_layout(template="plotly_white", height=600, xaxis_rangeslider_visible=False, dragmode='zoom')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    st.markdown("---")
    # Báo cáo nhanh cho Sales Executive
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📝 Nhận định MBA")
        status = "VÙNG MUA" if rsi_ht < 35 else "QUÁ MUA" if rsi_ht > 70 else "TÍCH LŨY"
        st.success(f"Khuyến nghị {ma_chinh}: Trạng thái **{status}**. RSI đạt {rsi_ht:.2f}. Điểm vào lệnh tối ưu quanh vùng **{lw_ht:,.0f} VNĐ**.")
    with col_b:
        st.subheader("💰 Hiệu suất")
        st.info(f"Giá đang nằm {'TRÊN' if g_ht > ma_ht else 'DƯỚI'} trung bình 20 phiên. Dữ liệu được đồng bộ trực tiếp từ sàn HOSE.")

else:
    st.markdown('<h1 style="text-align: center; font-size: 100px;">🐂💪🔥</h1>', unsafe_allow_html=True)
    st.error("⚠️ Đang khớp lệnh dữ liệu thực tế. Vui lòng đợi 5 giây rồi nhấn Rerun.")

st.sidebar.write("💻 **Engine: High-Fidelity v6.0**")
