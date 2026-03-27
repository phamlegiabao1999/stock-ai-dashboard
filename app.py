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

# CSS HỖ TRỢ ZOOM ĐA NỀN TẢNG
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
            submit = st.form_submit_button("🚀 ĐĂNG NHẬP HỆ THỐNG", use_container_width=True)
            if submit:
                if user == "baominh" and pwd == "mba2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Thông tin đăng nhập không chính xác!")
    st.stop()

# --- 2. HIỆU ỨNG LOADING ---
if "first_load" not in st.session_state:
    investment_hints = ["💡 RSI < 30 là vùng quá bán.", "📊 MA20 là đường xu hướng ngắn hạn.", "🏢 Đầu tư vào DN bạn hiểu rõ."]
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h3 style='text-align: center;'>🏋️‍♂️ Đang kết nối máy chủ Hồ Chí Minh...</h3>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; font-size: 150px;'>🐂💪🔥</h1>", unsafe_allow_html=True)
        st.balloons()
        p_bar = st.progress(0)
        for p in range(101):
            time.sleep(0.04) 
            p_bar.progress(p)
    st.session_state.first_load = True
    st.rerun()

# --- 3. BỘ TỪ ĐIỂN MÔ TẢ TIẾNG VIỆT ---
VI_DESCRIPTIONS = {
    "VIC": "Tập đoàn Vingroup: Hệ sinh thái đa ngành hàng đầu VN (BĐS, Xe điện VinFast, Công nghệ).",
    "VHM": "Vinhomes: Nhà phát triển bất động sản thương mại lớn nhất Việt Nam.",
    "VRE": "Vincom Retail: Đơn vị vận hành hệ thống trung tâm thương mại lớn nhất VN.",
    "MWG": "Thế Giới Di Động: Nhà bán lẻ số 1 VN vận hành TGDĐ, ĐMX, BHX.",
    "MSN": "Masan Group: Tập đoàn hàng tiêu dùng và bán lẻ thực phẩm hàng đầu.",
    "HPG": "Hòa Phát: Vua thép Việt Nam với quy trình sản xuất khép kín hiện đại.",
    "OIL": "PV OIL: Tổng Công ty Dầu Việt Nam, đơn vị bán lẻ xăng dầu lớn thứ 2 VN.",
    "BSR": "Lọc hóa dầu Bình Sơn: Quản lý nhà máy lọc dầu Dung Quất.",
    "GAS": "PV GAS: Tổng công ty Khí Việt Nam, đơn vị dẫn dắt ngành khí.",
    "PLX": "Petrolimex: Tập đoàn xăng dầu có mạng lưới phân phối lớn nhất cả nước.",
    "FPT": "FPT: Tập đoàn công nghệ hàng đầu, tiên phong trong chuyển đổi số."
}

# --- 4. HÀM HỖ TRỢ ---
@st.cache_data(ttl=600)
def get_clean_data(ticker):
    if not ticker: return None, None
    symbol = ticker + ".VN" if "." not in ticker else ticker
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    try:
        stock = yf.Ticker(symbol, session=session)
        df = stock.history(period="1y", interval="1d")
        if df is not None and not df.empty:
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

# --- 5. DANH MỤC MÃ ---
stock_dict = {
    "HỌ NHÀ VIN": {"VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail"},
    "DẦU KHÍ": {"GAS": "PV GAS", "PVD": "PV Drilling", "PVS": "PTSC", "PLX": "Petrolimex", "BSR": "Lọc dầu Bình Sơn", "OIL": "PV OIL", "POW": "PV Power"},
    "BÁN LẺ & FMCG": {"MWG": "Thế Giới Di Động", "MSN": "Masan Group", "VNM": "Vinamilk", "PNJ": "PNJ", "FRT": "FPT Retail"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MBBank", "STB": "Sacombank", "BID": "BIDV", "VPB": "VPBank", "ACB": "ACB"},
    "THÉP & CN": {"HPG": "Hòa Phát", "HSG": "Hoa Sen", "NKG": "Nam Kim", "GVR": "Cao su VN"},
    "CÔNG NGHỆ & CK": {"FPT": "FPT Corp", "SSI": "SSI", "VND": "VNDIRECT", "VCI": "Vietcap", "VIX": "VIX"}
}
all_options = [f"{t} - {n} ({g})" for g, s in stock_dict.items() for t, n in s.items()]

# --- 6. SIDEBAR ---
st.sidebar.title("Chào Bảo Minh MBA!")
ma_chinh_choice = st.sidebar.selectbox("Chọn mã phân tích chính:", options=all_options)
ma_chinh = ma_chinh_choice.split(" - ")[0]
enable_compare = st.sidebar.checkbox("⚖️ So sánh đối thủ")
ma_ss = st.sidebar.selectbox("Chọn đối thủ:", options=[x for x in all_options if x != ma_chinh_choice]).split(" - ")[0] if enable_compare else ""

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.session_state.first_load = False; st.rerun()

# --- 7. HEADER ---
tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.now(tz).strftime("%d/%m/%Y - %H:%M:%S")
h_col1, h_col2 = st.columns([1, 2])
with h_col1:
    st.markdown(f"📍 `Hồ Chí Minh (VN)`\n\n📅 `{now}`")
with h_col2:
    news = get_news(ma_chinh)
    if news:
        for n in news: st.markdown(f"● <a href='{n['link']}' target='_blank' style='color:#4CAF50; text-decoration:none;'>{n['title']}</a>", unsafe_allow_html=True)

# --- 8. DASHBOARD ---
if ma_chinh:
    df, stock_obj = get_clean_data(ma_chinh)
    if df is not None:
        g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1]); lw_ht = float(df['Lower'].iloc[-1]); atr_ht = float(df['ATR'].iloc[-1])

        # Status Bar
        if rsi_ht > 70: bg, txt, lb = "#feeceb", "#ef5350", "QUÁ MUA - RỦI RO"
        elif rsi_ht < 35: bg, txt, lb = "#e8f5e9", "#2e7d32", "VÙNG MUA AN TOÀN"
        else: bg, txt, lb = "#f0f2f6", "#31333f", "TRẠNG THÁI CÂN BẰNG"

        st.markdown(f"""<div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid {txt}; color:{txt};">
            <h2 style="margin:0;">📊 {ma_chinh}: {lb}</h2></div>""", unsafe_allow_html=True)
        st.write("")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f} VNĐ")
        m2.metric("RSI (14)", f"{rsi_ht:.2f}")
        m3.metric("Vs MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")
        m4.metric("Biến động ATR", f"{atr_ht:,.0f} VNĐ")

        # Biểu đồ nến
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Nến Nhật', increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=500, margin=dict(l=10, r=10, t=10, b=10), dragmode='zoom')
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        # Biểu đồ khối lượng
        fig_vol = go.Figure(data=[go.Bar(x=df.index, y=df['Volume'], marker_color='#26a69a', name='Khối lượng')])
        fig_vol.update_layout(height=180, template="plotly_white", margin=dict(l=10, r=10, t=0, b=10), dragmode='zoom')
        st.plotly_chart(fig_vol, use_container_width=True, config={'scrollZoom': True})

        # --- PHẦN SO SÁNH & NHẬN ĐỊNH ---
        st.markdown("---")
        if enable_compare and ma_ss:
            st.subheader(f"⚔️ So sánh Đối đầu: {ma_chinh} vs {ma_ss}")
            df_s, stock_s_obj = get_clean_data(ma_ss)
            if df_s is not None:
                comb = pd.concat([df['Close'], df_s['Close']], axis=1).dropna()
                st.line_chart(pd.DataFrame({ma_chinh: (comb.iloc[:,0]/comb.iloc[0,0]-1)*100, ma_ss: (comb.iloc[:,1]/comb.iloc[0,1]-1)*100}, index=comb.index))
                c_rev1, c_rev2 = st.columns(2)
                with c_rev1: st.info(f"🔎 **Kỹ thuật:** {ma_chinh} ({rsi_ht:.2f}) vs {ma_ss} ({float(df_s['RSI'].iloc[-1]):.2f}).")
                with c_rev2: 
                    pe1 = stock_obj.info.get('trailingPE', 'N/A')
                    pe2 = stock_s_obj.info.get('trailingPE', 'N/A')
                    st.success(f"💎 **Định giá P/E:** {ma_chinh}: {pe1} | {ma_ss}: {pe2}")
        else:
            st.subheader(f"🧐 Nhận định chuyên sâu: {ma_chinh}")
            c1, c2 = st.columns(2)
            with c1: st.info(f"📊 **Xu hướng:** {'TÍCH CỰC' if g_ht > ma_ht else 'CẦN QUAN SÁT'} trên MA20.")
            with c2: 
                try: 
                    target = stock_obj.info.get('targetMeanPrice', 0)
                    st.success(f"🎯 **Giá mục tiêu:** {f'{target:,.0f} VNĐ' if target else 'Đang cập nhật...'}")
                except: st.success("🎯 **Giá mục tiêu:** Theo dõi thêm báo cáo phân tích.")

        st.markdown("---")
        st.subheader("📝 Báo cáo nhanh (Copy gửi đối tác)")
        summary_text = f"NHẬN ĐỊNH {ma_chinh} ({now}):\n- Giá: {g_ht:,.0f} VNĐ\n- Trạng thái: {lb}\n- RSI: {rsi_ht:.2f}\n- Chiến lược: Gom mua quanh vùng {lw_ht:,.0f} VNĐ."
        st.text_area("Nội dung báo cáo:", value=summary_text, height=120)

        # --- THÔNG TIN DOANH NGHIỆP & DOANH THU ---
        st.markdown("---")
        col_info, col_rev = st.columns([1, 1])
        with col_info:
            st.subheader("🏢 Thông tin doanh nghiệp")
            try:
                company_name = stock_obj.info.get('longName', ma_chinh)
                st.write(f"**Tên:** {company_name}")
                st.write(f"**Ngành:** {stock_obj.info.get('industry', 'Đa ngành')}")
                with st.expander("📖 Xem mô tả tiếng Việt"):
                    st.write(VI_DESCRIPTIONS.get(ma_chinh, "Dữ liệu đang được cập nhật..."))
            except: st.info("Đang đồng bộ dữ liệu doanh nghiệp...")
        with col_rev:
            st.subheader("💰 Doanh thu 4 năm gần nhất")
            try:
                financials = stock_obj.financials
                if not financials.empty and 'Total Revenue' in financials.index:
                    rev = financials.loc['Total Revenue'].head(4)
                    rev_df = pd.DataFrame({'Năm': rev.index.year, 'Doanh thu (Tỷ)': rev.values / 1e9})
                    st.bar_chart(data=rev_df, x='Năm', y='Doanh thu (Tỷ)', color="#26a69a")
                else: st.info("Yahoo Finance chưa cập nhật dữ liệu tài chính cho mã này.")
            except: st.info("Biểu đồ doanh thu đang được xử lý...")

        st.markdown("---")
        col_h, col_s = st.columns(2)
        with col_h:
            st.subheader("📋 Lịch sử 5 phiên")
            st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)
        with col_s:
            st.subheader("🎯 Chiến lược Giao dịch MBA")
            st.table(pd.DataFrame({"Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"], "Giá tham chiếu": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]}))

st.sidebar.write("💻 **Bảo Minh MBA System v2.5**")
