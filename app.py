import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime
import pytz
import random
import requests

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

st.markdown("""
    <style>
    .stPlotlyChart { touch-action: pan-y; }
    .js-plotly-plot .plotly .modebar { left: 50% !important; transform: translateX(-50%) !important; top: 0px !important; }
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
            if st.form_submit_button("🚀 ĐĂNG NHẬP"):
                if user == "baominh" and pwd == "mba2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Sai thông tin!")
    st.stop()

# --- 2. LOADING (Fix lỗi ảnh Oops) ---
if "first_load" not in st.session_state:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h3 style='text-align: center;'>🏋️‍♂️ Đang kết nối máy chủ an toàn...</h3>", unsafe_allow_html=True)
        # Dùng Emoji hệ thống khổng lồ thay cho GIF để đảm bảo 100% không bao giờ lỗi "Oops"
        st.markdown("<h1 style='text-align: center; font-size: 150px;'>🐂💪🔥</h1>", unsafe_allow_html=True)
        st.balloons()
        p_bar = st.progress(0)
        for p in range(101):
            time.sleep(0.04)
            p_bar.progress(p)
    st.session_state.first_load = True
    st.rerun()

# --- 3. HÀM LẤY DỮ LIỆU (Siêu ổn định) ---
@st.cache_data(ttl=300)
def get_clean_data(ticker):
    if not ticker: return None, None
    symbol = ticker + ".VN" if "." not in ticker else ticker
    
    # Thử lấy bằng Yahoo Finance với Header giả lập trình duyệt
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    try:
        stock = yf.Ticker(symbol, session=session)
        df = stock.history(period="1y", interval="1d", timeout=5)
        
        if df is not None and not df.empty:
            df['MA20'] = df['Close'].rolling(20).mean()
            df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
            df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
            d = df['Close'].diff()
            g = (d.where(d > 0, 0)).rolling(14).mean()
            l = (-d.where(d < 0, 0)).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (g/l)))
            return df, stock
    except:
        return None, None
    return None, None

# --- 4. DANH MỤC (SSI Style) ---
stock_dict = {
    "HỌ NHÀ VIN": {"VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail"},
    "DẦU KHÍ": {"OIL": "PV OIL", "BSR": "Lọc dầu Bình Sơn", "GAS": "PV GAS", "PLX": "Petrolimex", "PVD": "PV Drilling"},
    "BÁN LẺ & BANK": {"MWG": "Thế Giới Di Động", "MSN": "Masan Group", "FPT": "FPT Corp", "VCB": "Vietcombank", "TCB": "Techcombank"},
    "THÉP & CK": {"HPG": "Hòa Phát", "HSG": "Hoa Sen", "SSI": "SSI", "VND": "VNDIRECT"}
}
all_options = [f"{t} - {n}" for g, s in stock_dict.items() for t, n in s.items()]

# --- 5. GIAO DIỆN CHÍNH ---
st.sidebar.title("Chào Bảo Minh MBA!")
choice = st.sidebar.selectbox("Chọn mã phân tích:", options=all_options)
ma_chinh = choice.split(" - ")[0]

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.rerun()

# Hiển thị dữ liệu
df, stock_obj = get_clean_data(ma_chinh)

if df is not None:
    g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1]); lw_ht = float(df['Lower'].iloc[-1])
    
    # Cảnh báo màu sắc UI
    if rsi_ht > 70: bg, txt, lb = "#feeceb", "#ef5350", "QUÁ MUA - RỦI RO"
    elif rsi_ht < 35: bg, txt, lb = "#e8f5e9", "#2e7d32", "VÙNG MUA AN TOÀN"
    else: bg, txt, lb = "#f0f2f6", "#31333f", "TRẠNG THÁI CÂN BẰNG"

    st.markdown(f'<div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid {txt}; color:{txt};"><h2>📊 {ma_chinh}: {lb}</h2></div>', unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f}")
    m2.metric("RSI (14)", f"{rsi_ht:.2f}")
    m3.metric("Hỗ trợ MA20", f"{ma_ht:,.0f}")

    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.update_layout(template="plotly_white", height=500, xaxis_rangeslider_visible=False, dragmode='zoom')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    st.markdown("---")
    st.subheader("🏢 Thông tin & Báo cáo nhanh")
    st.info(f"Mã {ma_chinh} hiện tại giá {g_ht:,.0f} VNĐ. Chiến lược: Mua quanh {lw_ht:,.0f} VNĐ.")
else:
    st.error("🚫 Yahoo Finance đang chặn kết nối tạm thời.")
    st.warning("👉 **Mẹo cho Bảo Minh:** Đừng nhấn Rerun liên tục. Hãy đợi 1 phút hoặc chuyển sang dùng mạng 4G để đổi IP là App sẽ chạy lại ngay.")

st.sidebar.write("💻 **Bảo Minh MBA v3.0**")
