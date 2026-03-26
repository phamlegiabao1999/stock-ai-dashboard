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
            time.sleep(0.1) 
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
def get_clean_data(ticker):
    if not ticker or len(ticker) < 3: return None, None
    symbol = ticker + ".VN" if "." not in ticker else ticker
    stock = yf.Ticker(symbol)
    df = stock.history(period="1y")
    if df is not None and not df.empty:
        df['MA20'] = df['Close'].rolling(20).mean()
        df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
        d = df['Close'].diff(); g = (d.where(d > 0, 0)).rolling(14).mean(); l = (-d.where(d < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (g/l)))
        return df, stock
    return None, None

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
    df, stock_obj = get_clean_data(ma_chinh)
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

        # --- PHẦN REVIEW ĐỐI ĐẦU (NẾU CÓ SO SÁNH) ---
        if enable_compare and ma_ss:
            st.markdown("---")
            st.subheader(f"⚔️ Review Đối Đầu: {ma_chinh} vs {ma_ss}")
            df_s, stock_s_obj = get_clean_data(ma_ss)
            
            if df_s is not None:
                # 1. So sánh hiệu suất
                comb = pd.concat([df['Close'], df_s['Close']], axis=1).dropna()
                perf = pd.DataFrame({ma_chinh: (comb.iloc[:,0]/comb.iloc[0,0]-1)*100, ma_ss: (comb.iloc[:,1]/comb.iloc[0,1]-1)*100}, index=comb.index)
                st.line_chart(perf)
                
                # 2. Bảng nhận định chi tiết
                c_rev1, c_rev2 = st.columns(2)
                i_main = stock_obj.info
                i_ss = stock_s_obj.info
                
                with c_rev1:
                    st.info(f"🔎 **Góc nhìn kỹ thuật:**\n- {ma_chinh} đang có RSI là {rsi_ht:.2f}, trong khi {ma_ss} đạt {float(df_s['RSI'].iloc[-1]):.2f}.\n- {'Sức mạnh giá của ' + ma_chinh + ' tốt hơn' if rsi_ht > float(df_s['RSI'].iloc[-1]) else 'Cơ hội tích lũy nằm ở ' + ma_chinh if rsi_ht < 40 else ma_ss + ' đang hút tiền mạnh hơn'}.")
                
                with c_rev2:
                    pe_main = i_main.get('trailingPE', 'N/A')
                    pe_ss = i_ss.get('trailingPE', 'N/A')
                    st.success(f"💎 **Định giá MBA:**\n- P/E {ma_chinh}: {pe_main} | P/E {ma_ss}: {pe_ss}.\n- {'Về mặt định giá, ' + ma_chinh + ' đang rẻ hơn đối thủ.' if isinstance(pe_main, (int, float)) and isinstance(pe_ss, (int, float)) and pe_main < pe_ss else 'Thị trường đang trả giá cao hơn cho kỳ vọng của ' + ma_chinh if pe_main != 'N/A' else 'Dữ liệu định giá đang cập nhật.'}")

                st.warning(f"💡 **Kết luận Sales Executive:** Nếu ưu tiên sự an toàn, hãy nhìn vào MA20. Nếu ưu tiên đột phá, hãy theo dõi tin tức ngành của cả hai mã tại header.")

        # --- THÔNG TIN CÔNG TY & DOANH THU ---
        st.markdown("---")
        col_info, col_rev = st.columns([1, 1])
        with col_info:
            st.subheader("🏢 Thông tin doanh nghiệp")
            try:
                info = stock_obj.info
                st.write(f"**Tên:** {info.get('longName', ma_chinh)}")
                st.write(f"**Ngành:** {info.get('industry', 'Đa ngành')}")
                with st.expander("📖 Xem tóm tắt bằng tiếng Việt"):
                    st.write(VI_DESCRIPTIONS.get(ma_chinh, "Mô tả chi tiết đang được cập nhật bằng tiếng Việt cho mã này."))
            except: st.info("Đang đồng bộ dữ liệu...")

        with col_rev:
            st.subheader("💰 Doanh thu 4 năm gần nhất")
            try:
                financials = stock_obj.financials
                if not financials.empty:
                    rev = financials.loc['Total Revenue'].head(4)
                    rev_df = pd.DataFrame({'Năm': rev.index.year, 'Doanh thu (Tỷ)': rev.values / 1e9})
                    st.bar_chart(data=rev_df, x='Năm', y='Doanh thu (Tỷ)', color="#26a69a")
                else: st.info("Chưa có dữ liệu tài chính.")
            except: st.info("Không thể tải biểu đồ doanh thu.")

        # --- CHIẾN LƯỢC & CÔNG THỨC ---
        st.markdown("---")
        col_h, col_s = st.columns(2)
        with col_h:
            st.subheader("📋 Lịch sử 5 phiên")
            st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)
        with col_s:
            st.subheader("🎯 Chiến lược Giao dịch MBA")
            strategy_data = {"Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"], "Giá tham chiếu": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]}
            st.table(pd.DataFrame(strategy_data))

        st.latex(r"RSI = 100 - \frac{100}{1 + RS}")

st.sidebar.write("💻 **Bảo Minh MBA System**")
