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
        user = st.text_input("👤 Tài khoản (baominh):")
        pwd = st.text_input("🔑 Mật khẩu (mba2026):", type="password")
        if st.button("🚀 ĐĂNG NHẬP HỆ THỐNG"):
            if user == "baominh" and pwd == "mba2026":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Sai thông tin đăng nhập!")
    st.stop()

# --- 2. HIỆU ỨNG LOADING (CHỈ HIỆN LẦN ĐẦU) ---
if "first_load" not in st.session_state:
    bull_gym_json_raw = """
    {
      "v": "5.7.1", "fr": 30, "ip": 0, "op": 60, "w": 500, "h": 500, "nm": "Gym Bull", "ddd": 0,
      "assets": [],
      "layers": [
        { "ddd": 0, "ind": 1, "ty": 4, "nm": "Dumbbell", "ks": { "r": { "k": [{ "t": 0, "s": [0] }, { "t": 30, "s": [-40] }, { "t": 60, "s": [0] }] }, "p": { "k": [250, 200] } }, "shapes": [{ "ty": "gr", "it": [{ "ty": "st", "c": { "k": [0.2, 0.2, 0.2] }, "w": { "k": 20 } }, { "ty": "sh", "ks": { "k": { "v": [[-100, 0], [100, 0]] } } }] }] },
        { "ddd": 0, "ind": 2, "ty": 4, "nm": "Bull", "ks": { "p": { "k": [250, 350] } }, "shapes": [{ "ty": "gr", "it": [{ "ty": "fl", "c": { "k": [0.6, 0.4, 0.2] } }, { "ty": "sh", "ks": { "k": { "v": [[0, -80], [60, 0], [0, 80], [-60, 0]], "c": true } } }] }] }
      ]
    }
    """
    bull_data = json.loads(bull_gym_json_raw)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h3 style='text-align: center;'>🏋️‍♂️ Đang quét dữ liệu...</h3>", unsafe_allow_html=True)
        st_lottie(bull_data, height=250)
        p_bar = st.progress(0)
        for p in range(100):
            time.sleep(0.02)
            p_bar.progress(p + 1)
    st.session_state.first_load = True
    st.rerun()

# --- 3. HÀM HỖ TRỢ ---
def get_clean_data(ticker):
    symbol = ticker + ".VN" if "." not in ticker else ticker
    df = yf.download(symbol, period="1y", progress=False)
    if df is not None and not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.copy()
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD'] = df['Close'].rolling(20).std()
        df['Upper'] = df['MA20'] + (df['STD'] * 2)
        df['Lower'] = df['MA20'] - (df['STD'] * 2)
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

# --- 4. SIDEBAR ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank"}
}
flat_list = [f"{t} - {n}" for g, s in stock_dict.items() for t, n in s.items()]

st.sidebar.title("Chào Bảo Minh MBA!")
main_choice = st.sidebar.selectbox("Mã phân tích chính:", options=flat_list)
ma_chinh = main_choice.split(" - ")[0]
enable_compare = st.sidebar.checkbox("⚖️ So sánh đối thủ")
ma_ss = st.sidebar.selectbox("Đối thủ:", options=[x for x in flat_list if x != main_choice]).split(" - ")[0] if enable_compare else ""

if st.sidebar.button("🚀 Phân tích ngay"):
    st.session_state.main_df = get_clean_data(ma_chinh)
    if enable_compare: st.session_state.comp_df = get_clean_data(ma_ss)
    st.sidebar.success("Đã cập nhật dữ liệu!")

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.session_state.first_load = False; st.rerun()

# --- 5. HEADER & TIN TỨC ---
tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.now(tz).strftime("%d/%m/%Y - %H:%M:%S")

h_col1, h_col2 = st.columns([1, 3])
with h_col1:
    st.markdown(f"📅 **Giờ VN:** `{now}`")
with h_col2:
    news = get_news(ma_chinh)
    if news:
        news_links = " | ".join([f"<a href='{n['link']}' target='_blank' style='color:#4CAF50;text-decoration:none;'>{n['title'][:45]}...</a>" for n in news])
        st.markdown(f"📰 **Tin {ma_chinh}:** {news_links}", unsafe_allow_html=True)

# --- 6. NỘI DUNG CHÍNH ---
if "main_df" in st.session_state:
    df = st.session_state.main_df
    g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1]); lw_ht = float(df['Lower'].iloc[-1])
    
    st.title(f"📊 Dashboard: {ma_chinh}")
    
    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f}")
    m2.metric("RSI (14)", f"{rsi_ht:.2f}")
    m3.metric("So với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

    # Chart
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Nến', increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
    fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=450, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # Khuyến nghị
    st.markdown(f"### 💡 Lời đề nghị cho {ma_chinh}")
    if rsi_ht < 35: st.success(f"💎 **MUA:** RSI {rsi_ht:.2f} (Quá bán).")
    elif rsi_ht > 70: st.error(f"🔥 **BÁN:** RSI {rsi_ht:.2f} (Quá mua).")
    else: st.info(f"📈 **THEO DÕI:** RSI {rsi_ht:.2f} (Cân bằng).")

    # So sánh
    if enable_compare and "comp_df" in st.session_state:
        df_ss = st.session_state.comp_df
        st.markdown("---")
        st.subheader(f"⚔️ So sánh % tăng trưởng: {ma_chinh} vs {ma_ss}")
        comb = pd.concat([df['Close'], df_ss['Close']], axis=1).dropna()
        perf = pd.DataFrame({ma_chinh: (comb.iloc[:,0]/comb.iloc[0,0]-1)*100, ma_ss: (comb.iloc[:,1]/comb.iloc[0,1]-1)*100}, index=comb.index)
        st.line_chart(perf)

    # Lịch sử & Công thức
    st.markdown("---")
    c_h, c_m = st.columns(2)
    with c_h:
        st.subheader("📋 Lịch sử 5 phiên")
        st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)
    with c_m:
        st.subheader("📐 Công thức")
        st.latex(r"RSI = 100 - \frac{100}{1 + RS}")

    # Chiến lược
    st.markdown("---")
    st.subheader("🎯 Chiến lược Giao dịch MBA")
    st.table(pd.DataFrame({"Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"], "Giá tham chiếu": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]}))

st.sidebar.markdown("---")
st.sidebar.write("💻 **Bảo Minh MBA System**")
