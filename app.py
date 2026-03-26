import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

# Khởi tạo trạng thái đăng nhập
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- GIAO DIỆN ĐĂNG NHẬP CHÍNH DIỆN ---
if not st.session_state.logged_in:
    st.title("🔐 Hệ thống Phân tích Bảo Minh MBA")
    st.write("Vui lòng xác thực quyền truy cập để tiếp tục.")
    
    # Tạo khung đăng nhập ở giữa màn hình
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        user = st.text_input("👤 Tài khoản (Viết liền không dấu):")
        pwd = st.text_input("🔑 Mật khẩu:", type="password")
        if st.button("🚀 ĐĂNG NHẬP NGAY"):
            if user == "baominh" and pwd == "mba2026":
                st.session_state.logged_in = True
                st.success("Xác thực thành công! Đang mở hệ thống...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Sai thông tin đăng nhập. Vui lòng thử lại!")
        st.markdown("---")
    st.stop()

# --- 2. HIỆU ỨNG LOADING ---
if "first_load" not in st.session_state:
    progress_bar = st.progress(0)
    for i in range(101):
        progress_bar.progress(i)
        time.sleep(0.01)
    st.session_state.first_load = True
    st.rerun()

# --- 3. DANH MỤC & DỮ LIỆU ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank"}
}
flat_list = [f"{t} - {n}" for g, s in stock_dict.items() for t, n in s.items()]

# --- 4. GIAO DIỆN SAU ĐĂNG NHẬP ---
st.sidebar.title(f"Xin chào Bảo Minh!")
main_choice = st.sidebar.selectbox("Chọn mã chính:", options=flat_list)
ma_chinh = main_choice.split(" - ")[0]

enable_compare = st.sidebar.checkbox("⚖️ So sánh đối thủ")
ma_ss = ""
if enable_compare:
    compare_choice = st.sidebar.selectbox("Chọn đối thủ:", options=[x for x in flat_list if x != main_choice])
    ma_ss = compare_choice.split(" - ")[0]

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False
    st.session_state.first_load = False
    st.rerun()

# --- 5. HÀM XỬ LÝ (GIỮ NGUYÊN PHẦN CHUẨN) ---
def get_clean_data(ticker):
    symbol = ticker + ".VN" if "-" not in ticker and "." not in ticker else ticker
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

# Thực hiện phân tích
df_main = get_clean_data(ma_chinh)
if df_main is not None:
    g_ht = float(df_main['Close'].iloc[-1])
    rsi_ht = float(df_main['RSI'].iloc[-1])
    
    st.title(f"📊 Phân tích: {ma_chinh}")
    
    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Giá", f"{g_ht:,.0f} VNĐ", delta=f"{df_main['Close'].diff().iloc[-1]:,.0f}")
    c2.metric("RSI", f"{rsi_ht:.2f}")
    c3.metric("MA20", f"{df_main['MA20'].iloc[-1]:,.0f}")

    # Nến
    fig = go.Figure(data=[go.Candlestick(x=df_main.index, open=df_main['Open'], high=df_main['High'], low=df_main['Low'], close=df_main['Close'], name='Nến', increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
    fig.add_trace(go.Scatter(x=df_main.index, y=df_main['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
    fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=450)
    st.plotly_chart(fig, use_container_width=True)

    # Khuyến nghị
    st.markdown("### 💡 Lời đề nghị")
    if rsi_ht < 35: st.success(f"💎 **MUA:** RSI {rsi_ht:.2f} (Quá bán)")
    elif rsi_ht > 70: st.error(f"🔥 **BÁN:** RSI {rsi_ht:.2f} (Quá mua)")
    else: st.info(f"📈 **THEO DÕI:** RSI {rsi_ht:.2f} (Cân bằng)")

    # So sánh
    if enable_compare:
        df_ss = get_clean_data(ma_ss)
        if df_ss is not None:
            st.markdown("---")
            comb = pd.concat([df_main['Close'], df_ss['Close']], axis=1).dropna()
            perf = pd.DataFrame({ma_chinh: (comb.iloc[:,0]/comb.iloc[0,0]-1)*100, ma_ss: (comb.iloc[:,1]/comb.iloc[0,1]-1)*100}, index=comb.index)
            st.subheader(f"⚔️ So sánh % tăng trưởng: {ma_chinh} vs {ma_ss}")
            st.line_chart(perf)

st.sidebar.markdown("---")
st.sidebar.write("💻 **Hệ thống Bảo Minh MBA**")
