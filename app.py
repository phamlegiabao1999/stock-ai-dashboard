import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import json
import requests
from streamlit_lottie import st_lottie
from datetime import datetime
import pytz
import feedparser # Thư viện lấy tin tức chuyên nghiệp

# --- 1. CẤU HÌNH & ĐĂNG NHẬP (Giữ nguyên phần đầu của bạn) ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Hệ thống Phân tích Bảo Minh MBA")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        user = st.text_input("👤 Tài khoản (baominh):")
        pwd = st.text_input("🔑 Mật khẩu (mba2026):", type="password")
        if st.button("🚀 ĐĂNG NHẬP HỆ THỐNG"):
            if user == "baominh" and pwd == "mba2026":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Thông tin không chính xác!")
    st.stop()

# --- 2. HÀM LẤY TIN TỨC (Dùng RSS cho ổn định) ---
def get_stock_news_rss(ticker):
    try:
        # Sử dụng Google News RSS feed
        url = f"https://news.google.com/rss/search?q={ticker}+chứng+khoán&hl=vi&gl=VN&ceid=VN:vi"
        feed = feedparser.parse(url)
        news_items = []
        for entry in feed.entries[:3]: # Lấy 3 tin đầu
            news_items.append({"title": entry.title, "link": entry.link})
        return news_items
    except:
        return []

# --- 3. HEADER (FIX GIỜ VIỆT NAM & TIN TỨC) ---
# Ép múi giờ sang Asia/Ho_Chi_Minh
tz_VN = pytz.timezone('Asia/Ho_Chi_Minh')
now_vn = datetime.now(tz_VN).strftime("%d/%m/%Y - %H:%M:%S")

head_col1, head_col2 = st.columns([1, 2])
with head_col1:
    st.markdown(f"📅 **Giờ VN:** `{now_vn}`")

# --- 4. SIDEBAR & DANH MỤC ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank"}
}
flat_list = [f"{t} - {n}" for g, s in stock_dict.items() for t, n in s.items()]

st.sidebar.title(f"Chào Bảo Minh MBA!")
main_choice = st.sidebar.selectbox("Mã phân tích chính:", options=flat_list)
ma_chinh = main_choice.split(" - ")[0]

if st.sidebar.button("🚀 Thực hiện phân tích ngay"):
    st.session_state.force_analyze = True

# --- 5. HÀM DỮ LIỆU ---
def get_clean_data(ticker):
    symbol = ticker + ".VN" if "-" not in ticker and "." not in ticker else ticker
    df = yf.download(symbol, period="1y", progress=False)
    if df is not None and not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.copy()
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD'] = df['Close'].rolling(20).std()
        df['Upper'] = df['MA20'] + (df['STD'] * 2); df['Lower'] = df['MA20'] - (df['STD'] * 2)
        d = df['Close'].diff(); g = (d.where(d > 0, 0)).rolling(14).mean(); l = (-d.where(d < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (g/l)))
        return df
    return None

# --- 6. HIỂN THỊ ---
if "main_df" in st.session_state or st.session_state.get('force_analyze', False):
    if st.session_state.get('force_analyze', False) or "main_df" not in st.session_state:
        st.session_state.main_df = get_clean_data(ma_chinh)
        st.session_state.force_analyze = False

    df = st.session_state.main_df
    if df is not None:
        # HIỂN THỊ TIN TỨC (Ô ĐỎ 2)
        with head_col2:
            news = get_stock_news_rss(ma_chinh)
            if news:
                # Tạo chuỗi tin tức có link bấm được
                news_html = " | ".join([f"<a href='{n['link']}' target='_blank' style='color: #4CAF50; text-decoration: none;'>{n['title'][:50]}...</a>" for n in news])
                st.markdown(f"📰 **Tin {ma_chinh}:** {news_html}", unsafe_allow_html=True)
            else:
                st.markdown(f"📰 **Tin {ma_chinh}:** Chưa tìm thấy tin tức mới nhất.")

        # --- PHẦN DASHBOARD (Giữ nguyên các bảng biểu của bạn) ---
        g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1])
        st.title(f"📊 Dashboard Phân Tích: {ma_chinh}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", delta=f"{df['Close'].diff().iloc[-1]:,.0f} VNĐ")
        c2.metric("Chỉ số RSI (14)", f"{rsi_ht:.2f}")
        c3.metric("So với MA20", f"{((g_ht/df['MA20'].iloc[-1])-1)*100:+.2f}%")

        st.markdown("---")
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Nến', increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=450)
        st.plotly_chart(fig, use_container_width=True)
        
        # (Các phần Lời đề nghị, Lịch sử... giữ nguyên bên dưới)
        st.markdown("---")
        st.subheader("🎯 Chiến lược Giao dịch MBA")
        lw_ht = float(df['Lower'].iloc[-1])
        st.table(pd.DataFrame({"Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"], "Giá tham chiếu": [f"Quanh {lw_ht:,.0f}", f"Trên MA20", f"Dưới {lw_ht*0.97:,.0f}"]}))

st.sidebar.markdown("---")
st.sidebar.write("💻 **Bảo Minh MBA System**")
