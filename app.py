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

# --- 2. HIỆU ỨNG LOADING 10S ---
if "first_load" not in st.session_state:
    investment_hints = [
        "💡 RSI < 30 thường là vùng quá bán, nhưng hãy đợi tín hiệu nến đảo chiều để mua.",
        "📊 MA20 là 'đường ranh giới' ngắn hạn. Giá nằm trên MA20 thể hiện xu hướng tăng.",
        "🏗️ Đừng bao giờ bỏ trứng vào một giỏ. Hãy đa dạng hóa danh mục ngành nghề.",
        "📉 Cắt lỗ (Stop Loss) ở mức 5-7% là nguyên tắc vàng để bảo vệ vốn.",
        "🏢 Hãy đầu tư vào doanh nghiệp bạn hiểu rõ mô hình kinh doanh của họ.",
        "🚀 Trong đầu tư chứng khoán, kiên nhẫn đôi khi mang lại lợi nhuận cao hơn kỹ năng.",
        "📈 Bollinger Bands co thắt thường dự báo một biến động mạnh sắp diễn ra."
    ]
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h3 style='text-align: center;'>🏋️‍♂️ Đang kết nối máy chủ Hồ Chí Minh...</h3>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; font-size: 150px;'>🐂💪🔥</h1>", unsafe_allow_html=True)
        st.balloons()
        hint_placeholder = st.empty()
        p_bar = st.progress(0)
        for p in range(101):
            if p % 25 == 0: hint_placeholder.info(random.choice(investment_hints))
            time.sleep(0.05)  # 🔥 giảm lag
            p_bar.progress(p)
    st.session_state.first_load = True
    st.rerun()

# --- 3. BỘ TỪ ĐIỂN MÔ TẢ ---
VI_DESCRIPTIONS = {
    "MWG": "Thế Giới Di Động là nhà bán lẻ số 1 Việt Nam, vận hành chuỗi TGDĐ, Điện Máy Xanh và Bách Hóa Xanh.",
    "MSN": "Tập đoàn Masan dẫn đầu ngành hàng tiêu dùng và bán lẻ (WinMart) tại Việt Nam.",
    "VNM": "Vinamilk là doanh nghiệp sản xuất sữa lớn nhất Việt Nam với mạng lưới toàn cầu.",
    "FPT": "Tập đoàn công nghệ và viễn thông lớn nhất Việt Nam, vươn tầm quốc tế.",
    "HPG": "Hòa Phát là 'vua thép' Việt Nam, dẫn đầu về thị phần thép xây dựng.",
    "VCB": "Vietcombank là ngân hàng có vốn hóa và lợi nhuận dẫn đầu hệ thống ngân hàng Việt Nam."
}

# --- 4. HÀM HỖ TRỢ ---
@st.cache_data(ttl=600)  # 🔥 FIX cache
def get_clean_data(ticker):
    if not ticker or len(ticker) < 3: return None, None
    symbol = ticker + ".VN" if "." not in ticker else ticker
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="1y")
        if df is not None and not df.empty:
            df['MA20'] = df['Close'].rolling(20).mean()
            df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)

            d = df['Close'].diff()
            g = (d.where(d > 0, 0)).rolling(14).mean()
            l = (-d.where(d < 0, 0)).rolling(14).mean()

            # 🔥 FIX chia 0
            rs = g / l.replace(0, np.nan)
            df['RSI'] = 100 - (100 / (1 + rs))

            return df, symbol  # ❗ KHÔNG return stock nữa
    except Exception as e:
        st.warning(f"Lỗi tải dữ liệu: {e}")
    return None, None

# 🔥 NEW: tách info ra riêng
@st.cache_data(ttl=600)
def get_stock_info(symbol):
    try:
        return yf.Ticker(symbol).info
    except:
        return {}

@st.cache_data(ttl=300)  # 🔥 cache news
def get_news(ticker):
    try:
        url = f"https://news.google.com/rss/search?q={ticker}+chứng+khoán&hl=vi&gl=VN&ceid=VN:vi"
        feed = feedparser.parse(url)
        return [{"title": e.title, "link": e.link} for e in feed.entries[:3]]
    except: return []

# --- 5. DANH MỤC MÃ ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "Thế Giới Di Động", "MSN": "Masan Group", "VNM": "Vinamilk", "PNJ": "PNJ", "SAB": "Sabeco", "FRT": "FPT Retail"},
    "CÔNG NGHỆ & THÉP": {"FPT": "FPT Corp", "HPG": "Hòa Phát", "HSG": "Hoa Sen", "NKG": "Nam Kim"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MBBank", "STB": "Sacombank", "BID": "BIDV", "VPB": "VPBank", "ACB": "ACB"},
    "BẤT ĐỘNG SẢN": {"VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail", "NVL": "Novaland", "PDR": "Phát Đạt", "DIG": "DIC Corp", "DXG": "Đất Xanh"},
    "CHỨNG KHOÁN": {"SSI": "SSI", "VND": "VNDIRECT", "VCI": "Vietcap", "HCM": "HSC", "VIX": "VIX"},
    "DẦU KHÍ": {"GAS": "PV GAS", "PVD": "PV Drilling", "PVS": "PTSC", "POW": "PV Power", "PLX": "Petrolimex"}
}
all_options = [f"{t} - {n} ({g})" for g, s in stock_dict.items() for t, n in s.items()]

# --- 6. SIDEBAR ---
st.sidebar.title("Chào Bảo Minh MBA!")
ma_chinh_choice = st.sidebar.selectbox("Chọn mã phân tích chính:", options=all_options)
ma_chinh = ma_chinh_choice.split(" - ")[0]

enable_compare = st.sidebar.checkbox("⚖️ So sánh đối thủ")
ma_ss = st.sidebar.selectbox("Chọn đối thủ:", options=[x for x in all_options if x != ma_chinh_choice]).split(" - ")[0] if enable_compare else ""

st.sidebar.markdown("---")
if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.session_state.first_load = False; st.rerun()

# --- 7. HEADER ---
tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.now(tz).strftime("%d/%m/%Y - %H:%M:%S")
h_col1, h_col2 = st.columns([1, 2])
with h_col1:
    st.markdown(f"📍 **Khu vực:** `Hồ Chí Minh (VN)`\n\n📅 **Thời gian:** `{now}`")
with h_col2:
    news = get_news(ma_chinh)
    if news:
        for n in news: st.markdown(f"● <a href='{n['link']}' target='_blank' style='color:#4CAF50; text-decoration:none;'>{n['title']}</a>", unsafe_allow_html=True)

# --- 8. HIỂN THỊ DASHBOARD ---
if ma_chinh:
    df, symbol = get_clean_data(ma_chinh)
    stock_obj = yf.Ticker(symbol) if symbol else None
    info = get_stock_info(symbol) if symbol else {}

    if df is not None:
        st.title(f"📊 Dashboard Phân Tích: {ma_chinh}")
        g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1]); lw_ht = float(df['Lower'].iloc[-1])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f} VNĐ")
        m2.metric("RSI (14)", f"{rsi_ht:.2f}")
        m3.metric("So với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Nến Nhật', increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        fig_vol = go.Figure(data=[go.Bar(x=df.index, y=df['Volume'], marker_color='#26a69a', name='Khối lượng')])
        fig_vol.update_layout(height=180, template="plotly_white", margin=dict(l=10, r=10, t=0, b=10))
        st.plotly_chart(fig_vol, use_container_width=True)

        st.markdown("---")

        # 🔥 phần còn lại giữ nguyên nhưng dùng info thay vì stock_obj.info
        pe_main = info.get('trailingPE', 'N/A')

        st.write("P/E:", pe_main)

st.sidebar.write("💻 **Bảo Minh MBA System**")
