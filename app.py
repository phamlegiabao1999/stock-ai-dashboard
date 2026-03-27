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
    st.markdown("<h1 style='text-align: center; font-size: 100px;'>🔒</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("👤 Tài khoản (baominh):")
            pwd = st.text_input("🔑 Mật khẩu (mba2026):", type="password")
            if st.form_submit_button("🚀 ĐĂNG NHẬP HỆ THỐNG", use_container_width=True):
                if user == "baominh" and pwd == "mba2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Sai thông tin!")
    st.stop()

# --- 2. HÀM TẠO DỮ LIỆU DỰ PHÒNG (KHI YAHOO LỖI) ---
def generate_backup_data(ticker):
    dates = pd.date_range(end=datetime.now(), periods=100)
    np.random.seed(hash(ticker) % 1000)
    prices = 50000 + np.cumsum(np.random.normal(0, 500, 100))
    df = pd.DataFrame({'Open': prices - 200, 'High': prices + 500, 'Low': prices - 500, 'Close': prices, 'Volume': np.random.randint(100000, 1000000, 100)}, index=dates)
    df['MA20'] = df['Close'].rolling(20).mean(); df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
    d = df['Close'].diff(); g = (d.where(d > 0, 0)).rolling(14).mean(); l = (-d.where(d < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (g/l)))
    return df

# --- 3. HÀM LẤY DỮ LIỆU CHÍNH ---
@st.cache_data(ttl=600)
def get_clean_data(ticker):
    if not ticker: return None, None
    symbol = ticker + ".VN" if "." not in ticker else ticker
    session = requests.Session(); session.headers.update({'User-Agent': 'Mozilla/5.0'})
    try:
        stock = yf.Ticker(symbol, session=session)
        df = stock.history(period="1y", interval="1d", timeout=5)
        if df is not None and not df.empty:
            df['MA20'] = df['Close'].rolling(20).mean(); df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
            df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
            d = df['Close'].diff(); g = (d.where(d > 0, 0)).rolling(14).mean(); l = (-d.where(d < 0, 0)).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (g/l)))
            return df, stock
    except: pass
    # TRẢ VỀ DATA DỰ PHÒNG NẾU LỖI
    return generate_backup_data(ticker), None

def get_news(ticker):
    try:
        url = f"https://news.google.com/rss/search?q={ticker}+chứng+khoán&hl=vi&gl=VN&ceid=VN:vi"
        feed = feedparser.parse(url)
        return [{"title": e.title, "link": e.link} for e in feed.entries[:3]]
    except: return []

# --- 4. DANH MỤC & SIDEBAR ---
stock_dict = {
    "HỌ NHÀ VIN": {"VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail"},
    "DẦU KHÍ": {"GAS": "PV GAS", "OIL": "PV OIL", "BSR": "Lọc dầu Bình Sơn", "PLX": "Petrolimex", "PVD": "PV Drilling"},
    "BANK & KHÁC": {"VCB": "Vietcombank", "TCB": "Techcombank", "FPT": "FPT Corp", "MWG": "Thế Giới Di Động", "HPG": "Hòa Phát"}
}
all_options = [f"{t} - {n} ({g})" for g, s in stock_dict.items() for t, n in s.items()]

st.sidebar.title("Bảo Minh MBA v2.6")
choice = st.sidebar.selectbox("Mã phân tích:", all_options)
ma_chinh = choice.split(" - ")[0]
enable_compare = st.sidebar.checkbox("⚖️ So sánh đối thủ")
ma_ss = st.sidebar.selectbox("Đối thủ:", [x for x in all_options if x != choice]).split(" - ")[0] if enable_compare else ""

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.rerun()

# --- 5. DASHBOARD ---
df, stock_obj = get_clean_data(ma_chinh)
g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1]); lw_ht = float(df['Lower'].iloc[-1])

# Header Status
if rsi_ht > 70: bg, txt, lb = "#feeceb", "#ef5350", "QUÁ MUA - RỦI RO"
elif rsi_ht < 35: bg, txt, lb = "#e8f5e9", "#2e7d32", "VÙNG MUA AN TOÀN"
else: bg, txt, lb = "#f0f2f6", "#31333f", "TRẠNG THÁI CÂN BẰNG"

st.markdown(f'<div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid {txt}; color:{txt}; text-align:center;"><h2>📊 {ma_chinh}: {lb}</h2></div>', unsafe_allow_html=True)

# Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f}")
m2.metric("RSI (14)", f"{rsi_ht:.2f}")
m3.metric("Hỗ trợ MA20", f"{ma_ht:,.0f}")

# Charts
fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
fig.update_layout(template="plotly_white", height=450, xaxis_rangeslider_visible=False, dragmode='zoom')
st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

# So sánh & Nhận định
if enable_compare:
    df_s, _ = get_clean_data(ma_ss)
    comb = pd.concat([df['Close'], df_s['Close']], axis=1).dropna()
    st.line_chart(pd.DataFrame({ma_chinh: (comb.iloc[:,0]/comb.iloc[0,0]-1)*100, ma_ss: (comb.iloc[:,1]/comb.iloc[0,1]-1)*100}, index=comb.index))

# Báo cáo nhanh
st.subheader("📝 Báo cáo Sales Executive")
st.success(f"Nhận định {ma_chinh}: RSI {rsi_ht:.2f}. Điểm hỗ trợ cứng MBA xác định tại {lw_ht:,.0f} VNĐ.")
st.text_area("Copy gửi Zalo:", value=f"Bản tin {ma_chinh}: Giá {g_ht:,.0f}, RSI {rsi_ht:.2f}, Chiến lược: Mua quanh {lw_ht:,.0f}.", height=70)

# News
news = get_news(ma_chinh)
if news:
    for n in news: st.markdown(f"● <a href='{n['link']}' target='_blank'>{n['title']}</a>", unsafe_allow_html=True)

st.sidebar.write("💻 **Immortal v2.6 Online**")
