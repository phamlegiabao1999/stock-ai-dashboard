import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
from vnstock3 import Vnstock

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Bảo Minh MBA - Realtime Analytics", layout="wide")

st.markdown("""
    <style>
    .stPlotlyChart { touch-action: pan-y; }
    .bull-container { font-size: 80px; text-align: center; margin: 20px 0; }
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
            user = st.text_input("👤 Tài khoản:")
            pwd = st.text_input("🔑 Mật khẩu:", type="password")
            if st.form_submit_button("🚀 ĐĂNG NHẬP"):
                if user == "baominh" and pwd == "mba2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Sai thông tin!")
    st.stop()

# --- 2. ENGINE LẤY DỮ LIỆU SIÊU ỔN ĐỊNH (AUTO-RETRY) ---
@st.cache_data(ttl=300)
def get_realtime_data(ticker):
    # Thử kết nối 3 lần để tránh lỗi "Hệ thống đang cài đặt"
    for i in range(3):
        try:
            stock = Vnstock().stock(symbol=ticker, source='TCBS')
            df = stock.quote.history(start='2025-01-01', end=datetime.now().strftime('%Y-%m-%d'))
            if df is not None and not df.empty:
                df = df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
                
                # Chỉ số kỹ thuật chuẩn MBA
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                df['RSI'] = 100 - (100 / (1 + (gain/loss)))
                return df
        except:
            time.sleep(2) # Đợi 2 giây rồi thử lại
    return None

# --- 3. DANH MỤC MÃ ---
stock_dict = {
    "HỌ NHÀ VIN": ["VIC", "VHM", "VRE"],
    "DẦU KHÍ": ["GAS", "OIL", "BSR", "PLX", "PVD", "PVS"],
    "BÁN LẺ & BANK": ["MWG", "MSN", "FPT", "VCB", "TCB", "MBB"]
}
all_options = [ticker for sub in stock_dict.values() for ticker in sub]

# --- 4. SIDEBAR ---
st.sidebar.title("Bảo Minh MBA v6.2")
ma_chinh = st.sidebar.selectbox("Mã phân tích:", options=all_options)
if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.rerun()

# --- 5. HIỂN THỊ ---
df = get_realtime_data(ma_chinh)

if df is not None:
    g_ht = float(df['Close'].iloc[-1])
    rsi_ht = float(df['RSI'].iloc[-1])
    ma_ht = float(df['MA20'].iloc[-1])
    lw_ht = float(df['Lower'].iloc[-1])
    
    st.markdown(f'<h2 style="text-align:center;">📊 Phân tích Realtime: {ma_chinh}</h2>', unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Giá Hiện Tại", f"{g_ht:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f}")
    m2.metric("RSI (Xung lực)", f"{rsi_ht:.2f}")
    m3.metric("Hỗ trợ MA20", f"{ma_ht:,.0f}")

    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Nến')])
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=2), name='MA20'))
    fig.update_layout(template="plotly_white", height=550, xaxis_rangeslider_visible=False, dragmode='zoom')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    st.markdown("---")
    st.success(f"📝 **Nhận định:** Mã {ma_chinh} có RSI {rsi_ht:.2f}. Điểm gom tối ưu quanh **{lw_ht:,.0f} VNĐ**. Dữ liệu lấy trực tiếp từ sàn nội địa.")

else:
    st.markdown('<div class="bull-container">🐂💪🔥</div>', unsafe_allow_html=True)
    st.warning("🚀 Đang đồng bộ dữ liệu Realtime... Bảo Minh hãy đợi vài giây, App sẽ tự động tải lại.")
    time.sleep(5)
    st.rerun() # Tự động Rerun cho bạn luôn!

st.sidebar.write("💻 **Engine: Vnstock3 Ultra Stable**")
