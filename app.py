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

# CSS Fix Zoom & Giao diện
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
        st.markdown("---")
        with st.form("login_form"):
            user = st.text_input("👤 Tài khoản (baominh):")
            pwd = st.text_input("🔑 Mật khẩu (mba2026):", type="password")
            if st.form_submit_button("🚀 ĐĂNG NHẬP HỆ THỐNG", use_container_width=True):
                if user == "baominh" and pwd == "mba2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Thông tin đăng nhập không chính xác!")
    st.stop()

# --- 2. BỘ TỪ ĐIỂN MÔ TẢ TIẾNG VIỆT ---
VI_DESCRIPTIONS = {
    "VIC": "Tập đoàn Vingroup: Hệ sinh thái đa ngành hàng đầu VN (BĐS, VinFast, Công nghệ).",
    "VHM": "Vinhomes: Nhà phát triển bất động sản thương mại lớn nhất Việt Nam.",
    "VRE": "Vincom Retail: Đơn vị sở hữu hệ thống TTTM lớn nhất VN.",
    "MWG": "Thế Giới Di Động: Nhà bán lẻ số 1 VN vận hành TGDĐ, ĐMX, BHX.",
    "MSN": "Masan Group: Tập đoàn hàng tiêu dùng và bán lẻ hàng đầu.",
    "HPG": "Hòa Phát: Vua thép Việt Nam với thị phần số 1.",
    "GAS": "PV GAS: Tổng công ty Khí Việt Nam.",
    "OIL": "PV OIL: Đơn vị bán lẻ xăng dầu lớn thứ 2 VN.",
    "BSR": "Lọc hóa dầu Bình Sơn (Dung Quất).",
    "PLX": "Petrolimex: Tập đoàn xăng dầu lớn nhất VN.",
    "FPT": "FPT: Tập đoàn công nghệ hàng đầu Việt Nam."
}

# --- 3. HÀM LẤY DỮ LIỆU (CƠ CHẾ VƯỢT RÀO YAHOO) ---
@st.cache_data(ttl=600)
def get_clean_data(ticker):
    if not ticker: return None, None
    symbol = ticker + ".VN" if "." not in ticker else ticker
    
    # Giả lập trình duyệt để tránh bị chặn IP
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        stock = yf.Ticker(symbol, session=session)
        df = stock.history(period="1y", interval="1d", timeout=10)
        if df is not None and not df.empty:
            # Tính toán chỉ số kỹ thuật
            df['MA20'] = df['Close'].rolling(20).mean()
            df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
            df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
            d = df['Close'].diff(); g = (d.where(d > 0, 0)).rolling(14).mean(); l = (-d.where(d < 0, 0)).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (g/l)))
            return df, stock
    except: return None, None
    return None, None

def get_news(ticker):
    try:
        url = f"https://news.google.com/rss/search?q={ticker}+chứng+khoán&hl=vi&gl=VN&ceid=VN:vi"
        feed = feedparser.parse(url)
        return [{"title": e.title, "link": e.link} for e in feed.entries[:3]]
    except: return []

# --- 4. DANH MỤC MÃ ---
stock_dict = {
    "HỌ NHÀ VIN": {"VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail"},
    "DẦU KHÍ": {"GAS": "PV GAS", "OIL": "PV OIL", "BSR": "Lọc dầu Bình Sơn", "PLX": "Petrolimex", "PVD": "PV Drilling", "PVS": "PTSC"},
    "BÁN LẺ & BANK": {"MWG": "Thế Giới Di Động", "MSN": "Masan Group", "VNM": "Vinamilk", "VCB": "Vietcombank", "TCB": "Techcombank", "FPT": "FPT Corp"}
}
all_options = [f"{t} - {n} ({g})" for g, s in stock_dict.items() for t, n in s.items()]

# --- 5. SIDEBAR ---
st.sidebar.title("Chào Bảo Minh MBA!")
ma_chinh_choice = st.sidebar.selectbox("Chọn mã phân tích:", options=all_options)
ma_chinh = ma_chinh_choice.split(" - ")[0]

enable_compare = st.sidebar.checkbox("⚖️ So sánh đối thủ")
ma_ss = st.sidebar.selectbox("Chọn đối thủ:", options=[x for x in all_options if x != ma_chinh_choice]).split(" - ")[0] if enable_compare else ""

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.rerun()

# --- 6. DASHBOARD CHÍNH ---
df, stock_obj = get_clean_data(ma_chinh)

if df is not None:
    g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1]); lw_ht = float(df['Lower'].iloc[-1]); atr_ht = float(df['ATR'].iloc[-1])

    # Header Status
    if rsi_ht > 70: bg, txt, lb = "#feeceb", "#ef5350", "QUÁ MUA - RỦI RO"
    elif rsi_ht < 35: bg, txt, lb = "#e8f5e9", "#2e7d32", "VÙNG MUA AN TOÀN"
    else: bg, txt, lb = "#f0f2f6", "#31333f", "TRẠNG THÁI CÂN BẰNG"

    st.markdown(f'<div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid {txt}; color:{txt}; text-align:center;"><h2>📊 {ma_chinh}: {lb}</h2></div>', unsafe_allow_html=True)
    
    # 6.1 Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Giá", f"{g_ht:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f}")
    m2.metric("RSI (14)", f"{rsi_ht:.2f}")
    m3.metric("Vs MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")
    m4.metric("Biến động ATR", f"{atr_ht:,.0f}")

    # 6.2 Biểu đồ nến & Khối lượng
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Nến Nhật')])
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
    fig.update_layout(template="plotly_white", height=450, xaxis_rangeslider_visible=False, dragmode='zoom', margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    fig_vol = go.Figure(data=[go.Bar(x=df.index, y=df['Volume'], marker_color='#26a69a', name='Khối lượng')])
    fig_vol.update_layout(height=150, template="plotly_white", margin=dict(l=10, r=10, t=0, b=10))
    st.plotly_chart(fig_vol, use_container_width=True)

    # 6.3 So sánh đối thủ
    st.markdown("---")
    if enable_compare:
        st.subheader(f"⚔️ So sánh: {ma_chinh} vs {ma_ss}")
        df_s, _ = get_clean_data(ma_ss)
        if df_s is not None:
            comb = pd.concat([df['Close'], df_s['Close']], axis=1).dropna()
            st.line_chart(pd.DataFrame({ma_chinh: (comb.iloc[:,0]/comb.iloc[0,0]-1)*100, ma_ss: (comb.iloc[:,1]/comb.iloc[0,1]-1)*100}, index=comb.index))

    # 6.4 Nhận định & Tin tức
    col_rep, col_news = st.columns([1, 1])
    with col_rep:
        st.subheader("📝 Báo cáo Sales Exec")
        st.success(f"Nhận định {ma_chinh}: Giá đang {'trên' if g_ht > ma_ht else 'dưới'} MA20. Điểm hỗ trợ cứng MBA: {lw_ht:,.0f} VNĐ.")
        st.text_area("Copy gửi Zalo:", value=f"Bản tin {ma_chinh} ({datetime.now().strftime('%H:%M')}): Giá {g_ht:,.0f}, RSI {rsi_ht:.2f}, Chiến lược: Mua quanh {lw_ht:,.0f}.", height=80)
    with col_news:
        st.subheader("📰 Tin tức mới nhất")
        news_list = get_news(ma_chinh)
        if news_list:
            for n in news_list: st.markdown(f"● <a href='{n['link']}' target='_blank' style='color:#4CAF50;'>{n['title']}</a>", unsafe_allow_html=True)

    # 6.5 Doanh thu & Thông tin (ĐÃ KHÔI PHỤC)
    st.markdown("---")
    c_info, c_rev = st.columns(2)
    with c_info:
        st.subheader("🏢 Thông tin doanh nghiệp")
        try:
            st.write(f"**Tên:** {stock_obj.info.get('longName', ma_chinh)}")
            with st.expander("📖 Xem mô tả tiếng Việt"):
                st.write(VI_DESCRIPTIONS.get(ma_chinh, "Đang cập nhật dữ liệu chuyên sâu..."))
        except: st.info("Dữ liệu đang được đồng bộ...")
    with c_rev:
        st.subheader("💰 Doanh thu 4 năm gần nhất")
        try:
            financials = stock_obj.financials
            if not financials.empty and 'Total Revenue' in financials.index:
                rev = financials.loc['Total Revenue'].head(4)
                rev_df = pd.DataFrame({'Năm': rev.index.year, 'Doanh thu (Tỷ)': rev.values / 1e9})
                st.bar_chart(data=rev_df, x='Năm', y='Doanh thu (Tỷ)', color="#26a69a")
            else: st.info("Chưa có dữ liệu tài chính.")
        except: st.info("Biểu đồ doanh thu đang được xử lý...")

else:
    st.error("🚫 Yahoo Finance hiện đang bận. Bảo Minh hãy nhấn **Rerun** hoặc đợi 1 phút rồi thử lại nhé!")
    st.markdown("<h1 style='text-align: center; font-size: 150px;'>🐂💪🔥</h1>", unsafe_allow_html=True)

st.sidebar.write("💻 **Bảo Minh MBA System v2.7**")
