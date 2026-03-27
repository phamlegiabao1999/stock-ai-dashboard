import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime
import pytz
import feedparser
import random
import requests

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

# CSS để App mượt trên Safari và tạo hiệu ứng cho con trâu
st.markdown("""
    <style>
    .stPlotlyChart { touch-action: pan-y; }
    .bull-container { font-size: 150px; text-align: center; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- MÀN HÌNH ĐĂNG NHẬP ---
if not st.session_state.logged_in:
    st.title("🔐 Hệ thống Phân tích Bảo Minh MBA")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        with st.form("login_form"):
            user = st.text_input("👤 Tài khoản:")
            pwd = st.text_input("🔑 Mật khẩu:", type="password")
            if st.form_submit_button("🚀 ĐĂNG NHẬP", use_container_width=True):
                if user == "baominh" and pwd == "mba2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Sai thông tin!")
    st.stop()

# --- 2. HIỆU ỨNG LOADING (KHÔNG DÙNG GIF - CHỐNG LỖI 100%) ---
if "first_load" not in st.session_state:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h3 style='text-align: center;'>🏋️‍♂️ Đang kết nối máy chủ an toàn...</h3>", unsafe_allow_html=True)
        # Dùng cụm Emoji có hiệu ứng CSS Pulse ở trên
        st.markdown('<div class="bull-container">🐂💪🔥</div>', unsafe_allow_html=True)
        st.balloons()
        p_bar = st.progress(0)
        for p in range(101):
            time.sleep(0.04)
            p_bar.progress(p)
    st.session_state.first_load = True
    st.rerun()

# --- 3. HÀM LẤY DỮ LIỆU (TỐI ƯU CHỐNG CHẶN) ---
@st.cache_data(ttl=600) # Cache 10 phút để Yahoo không nghi ngờ
def get_clean_data(ticker):
    if not ticker: return None, None
    symbol = ticker + ".VN" if "." not in ticker else ticker
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    try:
        stock = yf.Ticker(symbol, session=session)
        df = stock.history(period="1y", interval="1d", timeout=10)
        if df is not None and not df.empty:
            df['MA20'] = df['Close'].rolling(20).mean()
            df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
            d = df['Close'].diff(); g = (d.where(d > 0, 0)).rolling(14).mean(); l = (-d.where(d < 0, 0)).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (g/l)))
            return df, stock
    except: return None, None
    return None, None

# --- 4. DANH MỤC MÃ (HỌ VIN + DẦU KHÍ ĐẦY ĐỦ) ---
stock_dict = {
    "HỌ NHÀ VIN": {"VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail"},
    "DẦU KHÍ": {"GAS": "PV GAS", "OIL": "PV OIL", "BSR": "Lọc dầu Bình Sơn", "PLX": "Petrolimex", "PVD": "PV Drilling"},
    "BÁN LẺ & BANK": {"MWG": "Thế Giới Di Động", "MSN": "Masan Group", "FPT": "FPT Corp", "VCB": "Vietcombank", "TCB": "Techcombank"}
}
all_options = [f"{t} - {n}" for g, s in stock_dict.items() for t, n in s.items()]

# --- 5. GIAO DIỆN ---
st.sidebar.title("Bảo Minh MBA")
choice = st.sidebar.selectbox("Chọn mã:", options=all_options)
ma_chinh = choice.split(" - ")[0]

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.session_state.first_load = False; st.rerun()

df, stock_obj = get_clean_data(ma_chinh)

if df is not None:
    g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1]); lw_ht = float(df['Lower'].iloc[-1])
    
    # UI Thông minh
    color = "#ef5350" if rsi_ht > 70 else "#2e7d32" if rsi_ht < 35 else "#31333f"
    st.markdown(f'<h1 style="color:{color}; text-align:center;">📊 {ma_chinh} Dashboard</h1>', unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Giá", f"{g_ht:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f}")
    m2.metric("RSI", f"{rsi_ht:.2f}")
    m3.metric("Hỗ trợ MBA", f"{lw_ht:,.0f}")

    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.update_layout(template="plotly_white", height=500, xaxis_rangeslider_visible=False, dragmode='zoom')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    st.markdown("---")
    st.subheader("📝 Báo cáo nhanh")
    st.success(f"Nhận định {ma_chinh}: Giá đang {'trên' if g_ht > ma_ht else 'dưới'} MA20. RSI {rsi_ht:.2f} cho thấy vùng {'rủi ro' if rsi_ht > 70 else 'hấp dẫn' if rsi_ht < 35 else 'tích lũy'}.")

else:
    st.error("🚫 Yahoo Finance đang chặn máy chủ tạm thời.")
    st.info("👉 **Bảo Minh lưu ý:** Hãy dùng mạng **4G** trên điện thoại để mở lại App. Mạng 4G sẽ đổi địa chỉ IP và giúp bạn vượt rào ngay lập tức!")

st.sidebar.write("💻 **Bảo Minh MBA v3.0**")
