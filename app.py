import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import json
import requests
from streamlit_lottie import st_lottie

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
                st.success("Xác thực thành công!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Thông tin không chính xác!")
    st.stop()

# --- 2. HIỆU ỨNG LOADING (ĐÃ FIX ĐỂ NHÌN RÕ HƠN) ---
if "first_load" not in st.session_state:
    st.markdown("### ⚙️ Đang khởi tạo môi trường phân tích...")
    progress_text = "🔍 Đang đồng bộ dữ liệu từ Yahoo Finance..."
    my_bar = st.progress(0, text=progress_text)
    
    for percent_complete in range(100):
        # Chỉnh lại thời gian ngủ 0.03 để thanh chạy khoảng 3 giây
        time.sleep(0.03) 
        if percent_complete == 30:
            progress_text = "📊 Đang tính toán chỉ số RSI & MA20..."
        if percent_complete == 70:
            progress_text = "✅ Đã sẵn sàng dữ liệu thị trường!"
        my_bar.progress(percent_complete + 1, text=progress_text)
    
    st.session_state.first_load = True
    time.sleep(0.5) # Dừng lại nửa giây để bạn thấy 100% trước khi nhảy trang
    st.rerun()

# --- 3. DANH MỤC DỮ LIỆU ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen", "DGC": "Đức Giang"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank"}
}
flat_list = [f"{t} - {n}" for g, s in stock_dict.items() for t, n in s.items()]

# --- 4. SIDEBAR ---
st.sidebar.title(f"Chào Bảo Minh MBA!")
main_choice = st.sidebar.selectbox("Mã phân tích chính:", options=flat_list)
ma_chinh = main_choice.split(" - ")[0]

enable_compare = st.sidebar.checkbox("⚖️ So sánh đối thủ")
ma_ss = ""
if enable_compare:
    compare_choice = st.sidebar.selectbox("Chọn mã đối chiếu:", options=[x for x in flat_list if x != main_choice])
    ma_ss = compare_choice.split(" - ")[0]

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False
    st.session_state.first_load = False # Để lần sau login lại hiện hiệu ứng
    st.rerun()

# --- 5. HÀM XỬ LÝ DỮ LIỆU ---
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

# --- 6. HIỂN THỊ CHI TIẾT ---
df = get_clean_data(ma_chinh)
if df is not None:
    g_ht = float(df['Close'].iloc[-1])
    rsi_ht = float(df['RSI'].iloc[-1])
    ma_ht = float(df['MA20'].iloc[-1])
    lw_ht = float(df['Lower'].iloc[-1])
    
    st.title(f"📊 Dashboard Phân Tích: {ma_chinh}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", delta=f"{df['Close'].diff().iloc[-1]:,.0f} VNĐ")
    c2.metric("Chỉ số RSI (14)", f"{rsi_ht:.2f}")
    c3.metric("So với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

    st.markdown("---")
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Nến', increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
    fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 💡 Lời đề nghị hành động")
    if rsi_ht < 35: st.success(f"💎 **MUA:** RSI {rsi_ht:.2f} (Quá bán) - Vùng gom hàng tốt.")
    elif rsi_ht > 70: st.error(f"🔥 **BÁN:** RSI {rsi_ht:.2f} (Quá mua) - Nên chốt lời.")
    else: st.info(f"📈 **THEO DÕI:** RSI {rsi_ht:.2f} (Cân bằng) - Tiếp tục nắm giữ.")

    if enable_compare:
        df_ss = get_clean_data(ma_ss)
        if df_ss is not None:
            st.markdown("---")
            st.subheader(f"⚔️ So sánh % tăng trưởng: {ma_chinh} vs {ma_ss}")
            comb = pd.concat([df['Close'], df_ss['Close']], axis=1).dropna()
            perf = pd.DataFrame({ma_chinh: (comb.iloc[:,0]/comb.iloc[0,0]-1)*100, ma_ss: (comb.iloc[:,1]/comb.iloc[0,1]-1)*100}, index=comb.index)
            st.line_chart(perf)

    st.markdown("---")
    col_h, col_m = st.columns(2)
    with col_h:
        st.subheader("📋 Lịch sử 5 phiên gần nhất")
        st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)
    with col_m:
        st.subheader("📐 Công thức & Lý thuyết")
        st.latex(r"RSI = 100 - \frac{100}{1 + RS}")

    st.markdown("---")
    st.subheader("🎯 Chiến lược Giao dịch MBA")
    st.table(pd.DataFrame({
        "Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
        "Giá tham chiếu": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]
    }))

st.sidebar.markdown("---")
st.sidebar.write("💻 **Bảo Minh MBA System**")
