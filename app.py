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

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- MÀN HÌNH ĐĂNG NHẬP ---
if not st.session_state.logged_in:
    st.title("🔐 Hệ thống Phân tích Bảo Minh MBA")
    st.markdown("<h1 style='text-align: center; font-size: 100px;'>🔒</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        with st.form("login_form"):
            user = st.text_input("👤 Tài khoản (baominh):")
            pwd = st.text_input("🔑 Mật khẩu (mba2026):", type="password")
            submit = st.form_submit_button("🚀 ĐĂNG NHẬP HỆ THỐNG", use_container_width=True)
            if submit:
                if user == "baominh" and pwd == "mba2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Thông tin đăng nhập không chính xác!")
    st.stop()

# --- 2. HIỆU ỨNG LOADING ---
if "first_load" not in st.session_state:
    investment_hints = [
        "💡 RSI < 30 thường là vùng quá bán.",
        "📊 MA20 là ranh giới xu hướng.",
        "📉 Cắt lỗ 5-7% để bảo vệ vốn.",
        "🚀 Kiên nhẫn quan trọng hơn kỹ năng."
    ]
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        hint_placeholder = st.empty()
        p_bar = st.progress(0)
        for p in range(101):
            if p % 25 == 0:
                hint_placeholder.info(random.choice(investment_hints))
            time.sleep(0.05)
            p_bar.progress(p)
    st.session_state.first_load = True
    st.rerun()

# --- 3. MÔ TẢ ---
VI_DESCRIPTIONS = {
    "MWG": "Thế Giới Di Động...",
    "MSN": "Masan...",
    "VNM": "Vinamilk...",
    "FPT": "FPT...",
    "HPG": "Hòa Phát...",
    "VCB": "Vietcombank..."
}

# --- 4. HÀM ---
@st.cache_data(ttl=600)
def get_clean_data(ticker):
    if not ticker or len(ticker) < 3:
        return None, None
    symbol = ticker + ".VN" if "." not in ticker else ticker
    try:
        df = yf.Ticker(symbol).history(period="1y")
        if df is not None and not df.empty:
            df['MA20'] = df['Close'].rolling(20).mean()
            df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)

            d = df['Close'].diff()
            g = (d.where(d > 0, 0)).rolling(14).mean()
            l = (-d.where(d < 0, 0)).rolling(14).mean()
            rs = g / l.replace(0, np.nan)
            df['RSI'] = 100 - (100 / (1 + rs))

            return df, symbol
    except:
        return None, None

    return None, None

@st.cache_data(ttl=600)
def get_stock_info(symbol):
    try:
        return yf.Ticker(symbol).info
    except:
        return {}

# --- 5. SIDEBAR ---
ma_chinh = st.sidebar.text_input("Nhập mã:", "MWG").upper()
enable_compare = st.sidebar.checkbox("So sánh")
ma_ss = st.sidebar.text_input("Mã so sánh:", "FPT").upper() if enable_compare else ""

# --- 6. LOAD DATA ---
df, symbol = get_clean_data(ma_chinh)
info = get_stock_info(symbol) if symbol else {}

# --- 7. DASHBOARD ---
if df is not None:
    st.title(f"📊 {ma_chinh}")

    g_ht = float(df['Close'].iloc[-1])
    rsi_ht = float(df['RSI'].iloc[-1])
    ma_ht = float(df['MA20'].iloc[-1])
    lw_ht = float(df['Lower'].iloc[-1])

    col1, col2, col3 = st.columns(3)
    col1.metric("Giá", f"{g_ht:,.0f}")
    col2.metric("RSI", f"{rsi_ht:.2f}")
    col3.metric("MA20", f"{ma_ht:,.0f}")

    # --- chart ---
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20']))
    st.plotly_chart(fig, use_container_width=True)

    # --- compare ---
    if enable_compare and ma_ss:
        df_s, symbol_s = get_clean_data(ma_ss)
        info_s = get_stock_info(symbol_s) if symbol_s else {}

        if df_s is not None:
            st.subheader("So sánh")
            st.line_chart(pd.concat([df['Close'], df_s['Close']], axis=1))

            st.write("P/E chính:", info.get('trailingPE', 'N/A'))
            st.write("P/E đối thủ:", info_s.get('trailingPE', 'N/A'))

    # --- info ---
    st.markdown("---")
    st.write("P/E:", info.get('trailingPE', 'N/A'))
    st.write("Market Cap:", info.get('marketCap', 0))

    # --- financials FIX ---
    try:
        financials = yf.Ticker(symbol).financials if symbol else pd.DataFrame()
        if not financials.empty and 'Total Revenue' in financials.index:
            rev = financials.loc['Total Revenue'].head(4)
            st.bar_chart(rev)
    except:
        st.info("Không có dữ liệu doanh thu")

st.sidebar.write("💻 Bảo Minh MBA")
