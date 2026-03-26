import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from datetime import datetime
import pytz
import feedparser

# ================= CONFIG =================
st.set_page_config(page_title="Stock Analytics Pro", layout="wide")

USER = os.getenv("APP_USER", "baominh")
PWD = os.getenv("APP_PWD", "mba2026")

# ================= SESSION =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ================= LOGIN =================
if not st.session_state.logged_in:
    st.title("🔐 Stock Analytics System")

    user = st.text_input("User")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == USER and pwd == PWD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Sai tài khoản")

    st.stop()

# ================= CACHE =================
@st.cache_data(ttl=600)
def get_price_data(ticker):
    try:
        symbol = ticker + ".VN" if "." not in ticker else ticker
        df = yf.Ticker(symbol).history(period="1y")

        if df.empty:
            return None

        df['MA20'] = df['Close'].rolling(20).mean()
        std = df['Close'].rolling(20).std()
        df['Lower'] = df['MA20'] - std * 2

        # RSI SAFE
        delta = df['Close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()

        rs = gain / loss.replace(0, np.nan)
        df['RSI'] = 100 - (100 / (1 + rs))

        return df

    except Exception as e:
        st.error(f"Lỗi dữ liệu giá: {e}")
        return None


@st.cache_data(ttl=600)
def get_stock_info(ticker):
    try:
        symbol = ticker + ".VN" if "." not in ticker else ticker
        return yf.Ticker(symbol).info
    except:
        return {}


@st.cache_data(ttl=300)
def get_news(ticker):
    try:
        url = f"https://news.google.com/rss/search?q={ticker}+chứng+khoán&hl=vi&gl=VN&ceid=VN:vi"
        feed = feedparser.parse(url)
        return [{"title": e.title, "link": e.link} for e in feed.entries[:3]]
    except:
        return []


@st.cache_data(ttl=1800)
def get_financials(ticker):
    try:
        symbol = ticker + ".VN" if "." not in ticker else ticker
        return yf.Ticker(symbol).financials
    except:
        return pd.DataFrame()

# ================= UI =================
st.sidebar.title("📊 Stock Tool MBA")
ticker = st.sidebar.text_input("Nhập mã cổ phiếu", "MWG")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ================= HEADER =================
tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")

st.markdown(f"📍 HCM | ⏰ {now}")

# ================= DATA =================
df = get_price_data(ticker)
info = get_stock_info(ticker) or {}
news = get_news(ticker)

# ================= NEWS =================
if news:
    st.subheader("📰 Tin tức")
    for n in news:
        st.markdown(f"- [{n['title']}]({n['link']})")

# ================= MAIN =================
if df is not None:

    price = float(df['Close'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    ma20 = float(df['MA20'].iloc[-1])
    lower = float(df['Lower'].iloc[-1])

    # ===== METRICS =====
    col1, col2, col3 = st.columns(3)
    col1.metric("Giá", f"{price:,.0f}")
    col2.metric("RSI", f"{rsi:.2f}")
    col3.metric("So với MA20", f"{((price/ma20)-1)*100:+.2f}%")

    # ===== CHART =====
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="MA20"))

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # ===== VOLUME =====
    st.bar_chart(df['Volume'])

    # ===== ANALYSIS =====
    st.subheader("🧐 Nhận định")

    trend = "TĂNG" if price > ma20 else "GIẢM"

    if rsi > 70:
        status = "QUÁ MUA"
    elif rsi < 30:
        status = "QUÁ BÁN"
    else:
        status = "TRUNG TÍNH"

    st.info(f"""
    - Xu hướng: {trend}
    - RSI: {status} ({rsi:.2f})
    """)

    # ===== INFO =====
    st.subheader("🏢 Doanh nghiệp")

    st.write("Tên:", info.get("longName", ticker))
    st.write("Ngành:", info.get("industry", "N/A"))
    st.write("P/E:", info.get("trailingPE", "N/A"))

    market_cap = info.get("marketCap")
    if market_cap:
        st.write("Vốn hóa:", f"{market_cap/1e12:,.2f} nghìn tỷ")

    # ===== FINANCIALS =====
    st.subheader("💰 Doanh thu")

    financials = get_financials(ticker)

    try:
        if not financials.empty and "Total Revenue" in financials.index:
            rev = financials.loc["Total Revenue"].head(4)
            rev_df = pd.DataFrame({
                "Năm": rev.index.year,
                "Doanh thu": rev.values / 1e9
            })
            st.bar_chart(rev_df.set_index("Năm"))
        else:
            st.info("Không có dữ liệu doanh thu")
    except:
        st.info("Lỗi đọc financials")

    # ===== REPORT =====
    st.subheader("📝 Báo cáo nhanh")

    report = f"""
    {ticker}:
    Giá: {price:,.0f}
    RSI: {rsi:.2f}
    Xu hướng: {trend}
    Gợi ý: {'MUA gần hỗ trợ' if price < ma20 else 'GIỮ / CHỜ'}
    """

    st.text_area("Copy gửi khách:", report)

else:
    st.warning("Không có dữ liệu")
