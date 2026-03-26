import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import requests
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

# --- 2. HIỆU ỨNG LOADING (10 GIÂY VỚI GIF SIÊU BỀN) ---
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
        
        # THAY ĐỔI TẠI ĐÂY: Dùng link GIF dự phòng siêu bền
        gif_url = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHpueG5kbXpnd3Z3Ym1icm90ZjF6bm5pM3R6eWxtZ3R4ZnN0bjRjdyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw,L0H7L6pW8X8o8k8U8S/giphy.gif"
        try:
            st.image(gif_url, use_container_width=True)
        except:
            st.markdown("<h1 style='text-align: center;'>🐂🏋️‍♂️</h1>", unsafe_allow_html=True)
        
        hint_placeholder = st.empty()
        p_bar = st.progress(0)
        
        for p in range(101):
            if p % 25 == 0:
                hint_placeholder.info(random.choice(investment_hints))
            time.sleep(0.1) 
            p_bar.progress(p)
            
    st.session_state.first_load = True
    st.rerun()

# --- 3. HÀM HỖ TRỢ ---
def get_clean_data(ticker):
    if not ticker or len(ticker) < 3: return None
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

# --- 4. DANH MỤC MÃ ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "Thế Giới Di Động", "MSN": "Masan Group", "VNM": "Vinamilk", "PNJ": "PNJ", "SAB": "Sabeco", "FRT": "FPT Retail"},
    "CÔNG NGHỆ & THÉP": {"FPT": "FPT Corp", "HPG": "Hòa Phát", "HSG": "Hoa Sen", "NKG": "Nam Kim"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MBBank", "STB": "Sacombank", "BID": "BIDV", "VPB": "VPBank", "ACB": "ACB"},
    "BẤT ĐỘNG SẢN": {"VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail", "NVL": "Novaland", "PDR": "Phát Đạt", "DIG": "DIC Corp", "DXG": "Đất Xanh"},
    "CHỨNG KHOÁN": {"SSI": "SSI", "VND": "VNDIRECT", "VCI": "Vietcap", "HCM": "HSC", "VIX": "VIX"},
    "DẦU KHÍ": {"GAS": "PV GAS", "PVD": "PV Drilling", "PVS": "PTSC", "POW": "PV Power", "PLX": "Petrolimex"}
}
all_options = [f"{t} - {n} ({g})" for g, s in stock_dict.items() for t, n in s.items()]

# --- 5. SIDEBAR ---
st.sidebar.title("Chào Bảo Minh MBA!")
ma_chinh_choice = st.sidebar.selectbox("Chọn mã phân tích:", options=all_options)
ma_chinh = ma_chinh_choice.split(" - ")[0]

enable_compare = st.sidebar.checkbox("⚖️ So sánh đối thủ")
ma_ss = ""
if enable_compare:
    comp_choice = st.sidebar.selectbox("Chọn đối thủ:", options=[x for x in all_options if x != ma_chinh_choice])
    ma_ss = comp_choice.split(" - ")[0]

st.sidebar.markdown("---")
if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.session_state.first_load = False; st.rerun()

# --- 6. HEADER (GIỜ VN & TIN TỨC) ---
tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.now(tz).strftime("%d/%m/%Y - %H:%M:%S")
h_col1, h_col2 = st.columns([1, 2])
with h_col1:
    st.markdown(f"📍 **Khu vực:** `Hồ Chí Minh (VN)`")
    st.markdown(f"📅 **Thời gian:** `{now}`")

with h_col2:
    st.markdown(f"📰 **Tin tức mới nhất ({ma_chinh}):**")
    news = get_news(ma_chinh)
    if news:
        for n in news:
            st.markdown(f"● <a href='{n['link']}' target='_blank' style='color:#4CAF50; text-decoration:none;'>{n['title']}</a>", unsafe_allow_html=True)

# --- 7. HIỂN THỊ DASHBOARD ---
if ma_chinh:
    df = get_clean_data(ma_chinh)
    if df is not None:
        st.title(f"📊 Dashboard Phân Tích: {ma_chinh}")
        g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1]); lw_ht = float(df['Lower'].iloc[-1])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f} VNĐ")
        m2.metric("RSI (14)", f"{rsi_ht:.2f}")
        m3.metric("So với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Nến Nhật', increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=450, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"### 💡 Lời đề nghị cho {ma_chinh}")
        if rsi_ht < 35: st.success(f"💎 **MUA:** RSI {rsi_ht:.2f} (Quá bán).")
        elif rsi_ht > 70: st.error(f"🔥 **BÁN:** RSI {rsi_ht:.2f} (Quá mua).")
        else: st.info(f"📈 **THEO DÕI:** RSI {rsi_ht:.2f} (Cân bằng).")

        if enable_compare and ma_ss:
            df_s = get_clean_data(ma_ss)
            if df_s is not None:
                st.markdown("---")
                comb = pd.concat([df['Close'], df_s['Close']], axis=1).dropna()
                perf = pd.DataFrame({ma_chinh: (comb.iloc[:,0]/comb.iloc[0,0]-1)*100, ma_ss: (comb.iloc[:,1]/comb.iloc[0,1]-1)*100}, index=comb.index)
                st.subheader(f"⚔️ So sánh % tăng trưởng: {ma_chinh} vs {ma_ss}")
                st.line_chart(perf)

        st.markdown("---")
        col_h, col_m = st.columns(2)
        with col_h:
            st.subheader("📋 Lịch sử 5 phiên")
            st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)
        with col_m:
            st.subheader("🎯 Chiến lược MBA")
            st.table(pd.DataFrame({"Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"], "Giá tham chiếu": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]}))
        
        st.markdown("---")
        st.subheader("📐 Công thức & Lý thuyết")
        st.latex(r"RSI = 100 - \frac{100}{1 + RS}")

st.sidebar.write("💻 **Bảo Minh MBA System**")
