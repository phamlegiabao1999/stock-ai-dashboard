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

# CSS Fix Zoom
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
        with st.form("login_form"):
            user = st.text_input("👤 Tài khoản (baominh):")
            pwd = st.text_input("🔑 Mật khẩu (mba2026):", type="password")
            if st.form_submit_button("🚀 ĐĂNG NHẬP"):
                if user == "baominh" and pwd == "mba2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Thông tin đăng nhập không chính xác!")
    st.stop()

# --- 2. HÀM LẤY DỮ LIỆU (HOTFIX: AUTO-RETRY) ---
@st.cache_data(ttl=600)
def get_clean_data(ticker):
    if not ticker: return None, None
    symbol = ticker + ".VN" if "." not in ticker else ticker
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    # Thử lấy dữ liệu tối đa 3 lần nếu Yahoo bận
    for _ in range(3):
        try:
            stock = yf.Ticker(symbol, session=session)
            df = stock.history(period="1y", interval="1d", timeout=10)
            if df is not None and not df.empty:
                df['MA20'] = df['Close'].rolling(20).mean()
                df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
                df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
                d = df['Close'].diff(); g = (d.where(d > 0, 0)).rolling(14).mean(); l = (-d.where(d < 0, 0)).rolling(14).mean()
                df['RSI'] = 100 - (100 / (1 + (g/l)))
                return df, stock
        except:
            time.sleep(1)
            continue
    return None, None

def get_news(ticker):
    try:
        url = f"https://news.google.com/rss/search?q={ticker}+chứng+khoán&hl=vi&gl=VN&ceid=VN:vi"
        feed = feedparser.parse(url)
        return [{"title": e.title, "link": e.link} for e in feed.entries[:3]]
    except: return []

# --- 3. DANH MỤC MÃ (HỌ VIN & DẦU KHÍ) ---
stock_dict = {
    "HỌ NHÀ VIN": {"VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail"},
    "DẦU KHÍ": {"GAS": "PV GAS", "OIL": "PV OIL", "BSR": "Lọc dầu Bình Sơn", "PLX": "Petrolimex", "PVD": "PV Drilling"},
    "BÁN LẺ & BANK": {"MWG": "Thế Giới Di Động", "MSN": "Masan Group", "FPT": "FPT Corp", "VCB": "Vietcombank", "TCB": "Techcombank"}
}
all_options = [f"{t} - {n}" for g, s in stock_dict.items() for t, n in s.items()]

# --- 4. SIDEBAR ---
st.sidebar.title("Bảo Minh MBA v2.5.1")
choice = st.sidebar.selectbox("Chọn mã phân tích chính:", options=all_options)
ma_chinh = choice.split(" - ")[0]

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.rerun()

# --- 5. HIỂN THỊ DASHBOARD ---
df, stock_obj = get_clean_data(ma_chinh)

if df is not None:
    g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1])
    
    # Status Bar
    if rsi_ht > 70: bg, txt, lb = "#feeceb", "#ef5350", "QUÁ MUA - RỦI RO"
    elif rsi_ht < 35: bg, txt, lb = "#e8f5e9", "#2e7d32", "VÙNG MUA AN TOÀN"
    else: bg, txt, lb = "#f0f2f6", "#31333f", "TRẠNG THÁI CÂN BẰNG"

    st.markdown(f'<div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid {txt}; color:{txt};"><h2>📊 {ma_chinh}: {lb}</h2></div>', unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Giá", f"{g_ht:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f}")
    m2.metric("RSI (14)", f"{rsi_ht:.2f}")
    m3.metric("Vs MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.update_layout(template="plotly_white", height=500, xaxis_rangeslider_visible=False, dragmode='zoom')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    st.markdown("---")
    st.subheader("📝 Báo cáo & Tin tức")
    news = get_news(ma_chinh)
    if news:
        for n in news: st.markdown(f"● <a href='{n['link']}' target='_blank'>{n['title']}</a>", unsafe_allow_html=True)
else:
    st.error("🚫 Yahoo Finance đang bận. Bảo Minh hãy nhấn **Rerun** (trong menu 3 chấm góc phải) hoặc thử lại sau 30 giây nhé!")

st.sidebar.write("💻 **Bảo Minh MBA System**")
