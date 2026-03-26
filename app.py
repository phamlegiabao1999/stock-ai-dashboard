import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import os
import feedparser

# --- CONFIG ---
st.set_page_config(page_title="Stock Analytics Pro", layout="wide")

USER = os.getenv("APP_USER", "baominh")
PWD = os.getenv("APP_PWD", "mba2026")

# --- CACHE ---
@st.cache_data(ttl=600)
def get_clean_data(ticker):
    try:
        symbol = ticker + ".VN" if "." not in ticker else ticker
        stock = yf.Ticker(symbol)
        df = stock.history(period="1y")

        if df.empty:
            return None, None

        df['MA20'] = df['Close'].rolling(20).mean()
        std = df['Close'].rolling(20).std()
        df['Lower'] = df['MA20'] - (std * 2)

        # RSI SAFE
        delta = df['Close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()

        rs = gain / loss.replace(0, np.nan)
        df['RSI'] = 100 - (100 / (1 + rs))

        return df, stock

    except Exception as e:
        st.error(f"Lỗi dữ liệu: {e}")
        return None, None


@st.cache_data(ttl=300)
def get_news(ticker):
    try:
        url = f"https://news.google.com/rss/search?q={ticker}+chứng+khoán&hl=vi&gl=VN&ceid=VN:vi"
        feed = feedparser.parse(url)
        return [{"title": e.title, "link": e.link} for e in feed.entries[:3]]
    except Exception:
        return []


# --- LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    user = st.text_input("User")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == USER and pwd == PWD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Sai tài khoản")

    st.stop()


# --- MAIN ---
ticker = st.text_input("Nhập mã cổ phiếu", "MWG")

df, stock = get_clean_data(ticker)

if df is not None:
    info = stock.info

    st.write("Giá hiện tại:", df['Close'].iloc[-1])
    st.write("RSI:", df['RSI'].iloc[-1])
    st.write("P/E:", info.get("trailingPE", "N/A"))
