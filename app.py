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
import feedparser

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- MÀN HÌNH ĐĂNG NHẬP ---
if not st.session_state.logged_in:
    st.title("🔐 Hệ thống Phân tích Bảo Minh MBA")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        user = st.text_input("👤 Tài khoản:")
        pwd = st.text_input("🔑 Mật khẩu:", type="password")
        if st.button("🚀 ĐĂNG NHẬP HỆ THỐNG"):
            if user == "baominh" and pwd == "mba2026":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Thông tin đăng nhập không chính xác!")
    st.stop()

# --- 2. HIỆU ỨNG LOADING ---
if "first_load" not in st.session_state:
    bull_gym_json_raw = """{"v": "5.7.1", "fr": 30, "ip": 0, "op": 60, "w": 500, "h": 500, "nm": "Gym Bull", "layers": [{ "ind": 1, "ty": 4, "nm": "Dumbbell", "ks": { "r": { "k": [{ "t": 0, "s": [0] }, { "t": 30, "s": [-40] }, { "t": 60, "s": [0] }] }, "p": { "k": [250, 200] } }, "shapes": [{ "ty": "gr", "it": [{ "ty": "st", "c": { "k": [0.2, 0.2, 0.2] }, "w": { "k": 20 } }, { "ty": "sh", "ks": { "k": { "v": [[-100, 0], [100, 0]] } } }] }] }, { "ind": 2, "ty": 4, "nm": "Bull", "ks": { "p": { "k": [250, 350] } }, "shapes": [{ "ty": "gr", "it": [{ "ty": "fl", "c": { "k": [0.6, 0.4, 0.2] } }, { "ty": "sh", "ks": { "k": { "v": [[0, -80], [60, 0], [0, 80], [-60, 0]], "c": true } } }] }] }]}"""
    bull_data = json.loads(bull_gym_json_raw)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h3 style='text-align: center;'>🏋️‍♂️ Đang kết nối máy chủ Hồ Chí Minh...</h3>", unsafe_allow_html=True)
        st_lottie(bull_data, height=250)
        p_bar = st.progress(0)
        for p in range(100):
            time.sleep(0.01)
            p_bar.progress(p + 1)
    st.session_state.first_load = True
    st.rerun()

# --- 3. DANH MỤC MÃ CỔ PHIẾU CHI TIẾT ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "Thế Giới Di Động", "MSN": "Masan Group", "VNM": "Vinamilk", "PNJ": "Vàng bạc PNJ", "SAB": "Sabeco", "FRT": "FPT Retail"},
    "CÔNG NGHỆ & THÉP": {"FPT": "FPT Corp", "HPG": "Hòa Phát", "HSG": "Hoa Sen", "NKG": "Nam Kim"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MBBank", "STB": "Sacombank", "BID": "BIDV", "VPB": "VPBank", "ACB": "ACB"},
    "BẤT ĐỘNG SẢN": {"VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail", "NVL": "Novaland", "PDR": "Phát Đạt", "DIG": "DIC Corp", "DXG": "Đất Xanh"},
    "CHỨNG KHOÁN": {"SSI": "SSI", "VND": "VNDIRECT", "VCI": "Vietcap", "HCM": "HSC", "VIX": "VIX"},
    "DẦU KHÍ & NĂNG LƯỢNG": {"GAS": "PV GAS", "PVD": "PV Drilling", "PVS": "PTSC", "POW": "PV Power", "PLX": "Petrolimex"}
}

all_options = ["Tự nhập mã khác..."]
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        all_options.append(f"{ticker} - {name} ({group})")

# --- 4. SIDEBAR ---
st.sidebar.title("Chào Bảo Minh MBA!")
choice = st.sidebar.selectbox("Chọn hoặc tìm mã:", options=all_options)

if choice == "Tự nhập mã khác...":
    ma_chinh = st.sidebar.text_input("Nhập mã (VD: VJC):", "").upper().strip()
else:
    ma_chinh = choice.split(" - ")[0]

enable_compare = st.sidebar.checkbox("⚖️ So sánh đối thủ")
ma_ss = ""
if enable_compare:
    comp_choice = st.sidebar.selectbox("Đối thủ:", options=[x for x in all_options if x != choice])
    ma_ss = comp_choice.split(" - ")[0] if comp_choice != "Tự nhập mã khác..." else st.sidebar.text_input("Mã đối thủ:", "").upper().strip()

if st.sidebar.button("🚀 Phân tích ngay"):
    st.session_state.need_refresh = True

# --- 5. HÀM XỬ LÝ (Giữ nguyên logic chuẩn) ---
def get_clean_data(ticker):
    if not ticker: return None
    symbol = ticker + ".VN" if "." not in ticker else ticker
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

def get_news(ticker):
    try:
        url = f"https://news.google.com/rss/search?q={ticker}+chứng+khoán&hl=vi&gl=VN&ceid=VN:vi"
        feed = feedparser.parse(url)
        return [{"title": e.title, "link": e.link} for e in feed.entries[:3]]
    except: return []

# --- 6. HEADER ---
tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.now(tz).strftime("%d/%m/%Y - %H:%M:%S")
h_col1, h_col2 = st.columns([1, 2])
with h_col1:
    st.markdown(f"📍 **Máy chủ:** `Hồ Chí Minh` | 📅 `{now}`")

# --- 7. HIỂN THỊ ---
if ma_chinh:
    if st.session_state.get('need_refresh', False) or "main_df" not in st.session_state:
        st.session_state.main_df = get_clean_data(ma_chinh)
        if ma_ss: st.session_state.comp_df = get_clean_data(ma_ss)
        st.session_state.need_refresh = False

    df = st.session_state.main_df
    if df is not None:
        with h_col2:
            news = get_news(ma_chinh)
            if news:
                for n in news: st.markdown(f"● <a href='{n['link']}' target='_blank' style='color:#4CAF50;text-decoration:none;'>{n['title'][:60]}...</a>", unsafe_allow_html=True)
        
        st.title(f"📊 Dashboard Phân Tích: {ma_chinh}")
        g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1]); lw_ht = float(df['Lower'].iloc[-1])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f}")
        m2.metric("RSI (14)", f"{rsi_ht:.2f}")
        m3.metric("So với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Nến', increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=450)
        st.plotly_chart(fig, use_container_width=True)

        if enable_compare and "comp_df" in st.session_state:
            st.markdown("---")
            df_s = st.session_state.comp_df
            comb = pd.concat([df['Close'], df_s['Close']], axis=1).dropna()
            perf = pd.DataFrame({ma_chinh: (comb.iloc[:,0]/comb.iloc[0,0]-1)*100, ma_ss: (comb.iloc[:,1]/comb.iloc[0,1]-1)*100}, index=comb.index)
            st.subheader(f"⚔️ So sánh % tăng trưởng: {ma_chinh} vs {ma_ss}")
            st.line_chart(perf)

        st.markdown("---")
        c_h, c_m = st.columns(2)
        with c_h:
            st.subheader("📋 Lịch sử 5 phiên")
            st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)
        with c_m:
            st.subheader("🎯 Chiến lược MBA")
            st.table(pd.DataFrame({"Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"], "Giá tham chiếu": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]}))

st.sidebar.markdown("---")
if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.session_state.first_load = False; st.rerun()
