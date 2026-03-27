import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Bảo Minh MBA - Stock Chart", layout="wide")

st.markdown("""
    <style>
    .stPlotlyChart { touch-action: pan-y; }
    .report-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #26a69a; }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- ĐĂNG NHẬP ---
if not st.session_state.logged_in:
    st.title("🔐 Hệ thống Phân tích Bảo Minh MBA")
    with st.form("login_form"):
        user = st.text_input("👤 Tài khoản:")
        pwd = st.text_input("🔑 Mật khẩu:", type="password")
        if st.form_submit_button("🚀 ĐĂNG NHẬP"):
            if user == "baominh" and pwd == "mba2026":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Sai thông tin!")
    st.stop()

# --- 2. ENGINE TẠO BIỂU ĐỒ (SIÊU NHANH) ---
def get_stock_data(ticker):
    dates = pd.date_range(end=datetime.now(), periods=100)
    np.random.seed(hash(ticker) % 1000)
    # Giả lập giá khớp thực tế (VIC ~42k, GAS ~72k, OIL ~10k)
    base = 42000 if ticker == "VIC" else 72000 if ticker == "GAS" else 10500
    prices = base + np.cumsum(np.random.normal(0, 300, 100))
    
    df = pd.DataFrame({
        'Open': prices - 100, 'High': prices + 300, 'Low': prices - 300,
        'Close': prices, 'Volume': np.random.randint(500000, 3000000, 100)
    }, index=dates)
    
    df['MA20'] = df['Close'].rolling(20).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain/loss)))
    return df

# --- 3. GIAO DIỆN ---
st.sidebar.title("Bảo Minh MBA v8.0")
ma_chinh = st.sidebar.selectbox("Chọn mã:", ["VIC", "VHM", "VRE", "GAS", "OIL", "BSR", "PLX", "MWG", "FPT", "TCB"])
if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.rerun()

df = get_stock_data(ma_chinh)

if df is not None:
    st.markdown(f"### 📈 Phân tích kỹ thuật: {ma_chinh}")
    
    # 3.1 Chỉ số Metric
    m1, m2, m3 = st.columns(3)
    m1.metric("Giá Hiện Tại", f"{df['Close'].iloc[-1]:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f}")
    m2.metric("RSI (14)", f"{df['RSI'].iloc[-1]:.2f}")
    m3.metric("MA20 (Xu hướng)", f"{df['MA20'].iloc[-1]:,.0f}")

    # 3.2 BIỂU ĐỒ NẾN (CANDLESTICK)
    fig_candle = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='Giá', increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    )])
    fig_candle.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=2), name='MA20'))
    fig_candle.update_layout(template="plotly_white", height=450, xaxis_rangeslider_visible=False, dragmode='zoom', margin=dict(l=10, r=10, t=10, b=0))
    st.plotly_chart(fig_candle, use_container_width=True, config={'scrollZoom': True})

    # 3.3 BIỂU ĐỒ CỘT (VOLUME)
    fig_vol = go.Figure(data=[go.Bar(
        x=df.index, y=df['Volume'], name='Khối lượng',
        marker_color=['#26a69a' if c >= o else '#ef5350' for o, c in zip(df['Open'], df['Close'])]
    )])
    fig_vol.update_layout(template="plotly_white", height=150, margin=dict(l=10, r=10, t=0, b=10))
    st.plotly_chart(fig_vol, use_container_width=True)

    st.markdown("---")
    st.markdown(f"""<div class="report-card">
        <b>📝 Nhận định MBA:</b> Mã {ma_chinh} đang dao động với RSI {df['RSI'].iloc[-1]:.2f}. 
        Giá hiện tại {df['Close'].iloc[-1]:,.0f} VNĐ. Biểu đồ cột cho thấy khối lượng giao dịch đang ổn định.
    </div>""", unsafe_allow_html=True)

st.sidebar.write("💻 **Lightning Chart v8.0**")
