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
from bs4 import BeautifulSoup

# --- 1. CẤU HÌNH HỆ THỐNG ---
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
        user = st.text_input("👤 Tài khoản (baominh):")
        pwd = st.text_input("🔑 Mật khẩu (mba2026):", type="password")
        if st.button("🚀 ĐĂNG NHẬP HỆ THỐNG"):
            if user == "baominh" and pwd == "mba2026":
                st.session_state.logged_in = True
                st.success("Xác thực thành công!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Thông tin đăng nhập không chính xác!")
    st.stop()

# --- 2. HIỆU ỨNG LOADING (CON TRÂU CẦM TẠ) ---
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
    bull_gym_data = json.loads(bull_gym_json_raw)
    st.markdown("<h3 style='text-align: center;'>🏋️‍♂️ Đang khởi tạo môi trường phân tích...</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2: st_lottie(bull_gym_data, height=300, key="bull_loading")
    progress_bar = st.progress(0)
    for p in range(100):
        time.sleep(0.02)
        progress_bar.progress(p + 1)
    st.session_state.first_load = True
    st.rerun()

# --- 3. HÀM LẤY TIN TỨC ---
def get_stock_news(ticker):
    try:
        query = f"{ticker} chứng khoán"
        url = f"https://www.google.com/search?q={query}&tbm=nws"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        news_list = []
        for g in soup.find_all("div", class_="SoEbef")[:3]: # Lấy 3 tin mới nhất
            title = g.find("div", class_="n0u1rf").get_text()
            link = g.find("a")["href"]
            news_list.append({"title": title, "link": link})
        return news_list
    except:
        return []

# --- 4. HEADER (THỜI GIAN & TIN TỨC - Ô ĐỎ) ---
now = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")

# TẠO 2 CỘT Ở TRÊN CÙNG (Vị trí ô đỏ bạn đánh dấu)
head_col1, head_col2 = st.columns([1, 2])
with head_col1:
    st.markdown(f"📅 **Thời gian:** `{now}`")

# --- 5. DANH MỤC & SIDEBAR ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank"}
}
flat_list = [f"{t} - {n}" for g, s in stock_dict.items() for t, n in s.items()]

st.sidebar.title(f"Chào Bảo Minh MBA!")
main_choice = st.sidebar.selectbox("Mã phân tích chính:", options=flat_list)
ma_chinh = main_choice.split(" - ")[0]
enable_compare = st.sidebar.checkbox("⚖️ So sánh đối thủ")
ma_ss = ""
if enable_compare:
    compare_choice = st.sidebar.selectbox("Chọn mã đối chiếu:", options=[x for x in flat_list if x != main_choice])
    ma_ss = compare_choice.split(" - ")[0]

if st.sidebar.button("🚀 Thực hiện phân tích ngay"):
    if 'main_df' in st.session_state: del st.session_state.main_df
    st.session_state.force_analyze = True

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.session_state.first_load = False; st.rerun()

# --- 6. HÀM DỮ LIỆU ---
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

# --- 7. HIỂN THỊ KẾT QUẢ ---
if "main_df" in st.session_state or st.session_state.get('force_analyze', False):
    if st.session_state.get('force_analyze', False) or "main_df" not in st.session_state:
        st.session_state.main_df = get_clean_data(ma_chinh)
        st.session_state.force_analyze = False

    df = st.session_state.main_df
    if df is not None:
        # TIN TỨC MỚI NHẤT (Vị trí ô đỏ 2)
        with head_col2:
            news = get_stock_news(ma_chinh)
            if news:
                news_text = " | ".join([f"[{n['title'][:40]}...]({n['link']})" for n in news])
                st.markdown(f"📰 **Tin mới {ma_chinh}:** {news_text}", unsafe_allow_html=True)
            else:
                st.markdown(f"📰 **Tin mới {ma_chinh}:** Đang cập nhật tin tức từ Google News...")

        # PHẦN CÒN LẠI CỦA DASHBOARD
        g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1]); lw_ht = float(df['Lower'].iloc[-1])
        st.title(f"📊 Dashboard Phân Tích: {ma_chinh}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", delta=f"{df['Close'].diff().iloc[-1]:,.0f} VNĐ")
        c2.metric("Chỉ số RSI (14)", f"{rsi_ht:.2f}")
        c3.metric("So với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

        st.markdown("---")
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Nến', increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=450, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # Lời đề nghị, So sánh, Lịch sử... (Giữ nguyên như bản cũ)
        st.markdown("### 💡 Lời đề nghị hành động")
        if rsi_ht < 35: st.success(f"💎 **MUA:** RSI {rsi_ht:.2f} (Quá bán)")
        elif rsi_ht > 70: st.error(f"🔥 **BÁN:** RSI {rsi_ht:.2f} (Quá mua)")
        else: st.info(f"📈 **THEO DÕI:** RSI {rsi_ht:.2f} (Cân bằng)")

        if enable_compare:
            df_ss = get_clean_data(ma_ss)
            if df_ss is not None:
                st.markdown("---")
                comb = pd.concat([df['Close'], df_ss['Close']], axis=1).dropna()
                perf = pd.DataFrame({ma_chinh: (comb.iloc[:,0]/comb.iloc[0,0]-1)*100, ma_ss: (comb.iloc[:,1]/comb.iloc[0,1]-1)*100}, index=comb.index)
                st.subheader(f"⚔️ So sánh % tăng trưởng: {ma_chinh} vs {ma_ss}")
                st.line_chart(perf)

        st.markdown("---")
        col_h, col_m = st.columns(2)
        with col_h:
            st.subheader("📋 Lịch sử 5 phiên gần nhất")
            st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)
        with col_m:
            st.subheader("🎯 Chiến lược Giao dịch MBA")
            st.table(pd.DataFrame({"Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"], "Giá tham chiếu": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]}))

st.sidebar.markdown("---")
st.sidebar.write("💻 **Bảo Minh MBA System**")
