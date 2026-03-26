import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import requests
import time

# --- 1. CẤU HÌNH & BẢO MẬT ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

# Hàm load hiệu ứng Lottie
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

# Kiểm tra đăng nhập
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.sidebar.title("🔐 Đăng nhập hệ thống")
    user = st.sidebar.text_input("Tài khoản:")
    pwd = st.sidebar.text_input("Mật khẩu:", type="password")
    if st.sidebar.button("Đăng nhập"):
        # Bạn có thể đổi tài khoản/mật khẩu ở đây
        if user == "baominh" and pwd == "mba2026":
            st.session_state.logged_in = True
            st.sidebar.success("Đăng nhập thành công!")
            st.rerun()
        else:
            st.sidebar.error("Sai tài khoản hoặc mật khẩu!")

if not st.session_state.logged_in:
    login()
    st.info("Vui lòng đăng nhập ở thanh Sidebar bên trái để sử dụng hệ thống.")
    # Hiệu ứng chờ đăng nhập
    lottie_stock = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_06spybuy.json")
    st_lottie(lottie_stock, height=300)
    st.stop()

# --- HIỆU ỨNG MỞ APP KHI ĐÃ LOGGED IN ---
if "first_load" not in st.session_state:
    lottie_loading = load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_p8bfn5to.json")
    st_lottie(lottie_loading, height=200)
    st.write("🚀 Đang khởi tạo hệ thống phân tích...")
    time.sleep(2)
    st.session_state.first_load = True
    st.rerun()

# --- 2. DANH MỤC MÃ ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank"}
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name}")

# --- 3. SIDEBAR PHÂN TÍCH ---
st.sidebar.success(f"Chào Bảo Minh MBA!")
if st.sidebar.button("Đăng xuất"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.header("🔍 Phân tích & Đối chiếu")
main_choice = st.sidebar.selectbox("Mã phân tích chính:", options=flat_list)
ma_chinh = main_choice.split(" - ")[0]

enable_compare = st.sidebar.checkbox("⚖️ Kích hoạt So sánh đối thủ")
ma_ss = ""
if enable_compare:
    compare_choice = st.sidebar.selectbox("Chọn mã đối chiếu:", options=[x for x in flat_list if x != main_choice])
    ma_ss = compare_choice.split(" - ")[0]

btn_analyze = st.sidebar.button("🚀 Thực hiện phân tích")

# --- 4. HÀM DỮ LIỆU ---
def get_clean_data(ticker):
    symbol = ticker + ".VN" if "-" not in ticker and "." not in ticker else ticker
    df = yf.download(symbol, period="1y", progress=False)
    if df is not None and not df.empty:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.copy()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['STD'] = df['Close'].rolling(window=20).std()
        df['Upper'] = df['MA20'] + (df['STD'] * 2)
        df['Lower'] = df['MA20'] - (df['STD'] * 2)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain/loss)))
        return df
    return None

# --- 5. HIỂN THỊ CHÍNH ---
if btn_analyze or "main_df" in st.session_state:
    if btn_analyze:
        st.session_state.main_df = get_clean_data(ma_chinh)
        st.session_state.name_chinh = ma_chinh
        if enable_compare and ma_ss:
            st.session_state.compare_df = get_clean_data(ma_ss)
            st.session_state.name_ss = ma_ss
        else:
            st.session_state.compare_df = None

    df = st.session_state.main_df
    if df is not None:
        g_ht = float(df['Close'].iloc[-1])
        rsi_ht = float(df['RSI'].iloc[-1])
        ma_ht = float(df['MA20'].iloc[-1])
        
        st.title(f"📊 Dashboard: {st.session_state.name_chinh}")

        # --- CARDS ---
        c_price, c_rsi, c_ma = st.columns(3)
        c_price.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", delta=f"{df['Close'].diff().iloc[-1]:,.0f}")
        c_rsi.metric("Chỉ số RSI (14)", f"{rsi_ht:.2f}")
        c_ma.metric("So với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

        # --- BIỂU ĐỒ NẾN ---
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='Giá nến', increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        )])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=450)
        st.plotly_chart(fig, use_container_width=True)

        # --- CHÚ THÍCH RSI ---
        with st.expander("❓ RSI là gì? (Chú thích cho MBA)"):
            st.write("""
            **Relative Strength Index (RSI)** là chỉ số sức mạnh tương đối, dùng để đo lường tốc độ và sự thay đổi của biến động giá:
            - **RSI > 70:** Thị trường 'Quá mua' (Overbought) -> Rủi ro đảo chiều giảm giá cao.
            - **RSI < 30:** Thị trường 'Quá bán' (Oversold) -> Cơ hội cổ phiếu đang rẻ, dễ bật tăng lại.
            - **RSI quanh 50:** Trạng thái cân bằng, xu hướng không rõ ràng.
            """)

        # --- LỜI ĐỀ NGHỊ ---
        st.markdown("### 💡 Lời đề nghị hành động")
        if rsi_ht < 35: st.success(f"💎 **MUA:** RSI ({rsi_ht:.2f}) Quá bán. Vùng giá hấp dẫn.")
        elif rsi_ht > 70: st.error(f"🔥 **BÁN:** RSI ({rsi_ht:.2f}) Quá mua. Nên chốt lời.")
        else: st.info(f"📈 **THEO DÕI:** RSI ({rsi_ht:.2f}) Cân bằng.")

        # --- SO SÁNH ---
        if st.session_state.get('compare_df') is not None:
            df_ss = st.session_state.compare_df
            combined = pd.concat([df['Close'], df_ss['Close']], axis=1).dropna()
            combined.columns = ['Chinh', 'SS']
            perf = pd.DataFrame({
                st.session_state.name_chinh: (combined['Chinh'] / combined['Chinh'].iloc[0] - 1) * 100,
                st.session_state.name_ss: (combined['SS'] / combined['SS'].iloc[0] - 1) * 100
            }, index=combined.index)
            st.subheader(f"⚔️ So sánh: {st.session_state.name_chinh} vs {st.session_state.name_ss}")
            st.line_chart(perf)

        # --- LỊCH SỬ & CHIẾN LƯỢC ---
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 Lịch sử & Công thức")
            st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)
            st.latex(r"RSI = 100 - \frac{100}{1 + RS}")
        with col2:
            st.subheader("🎯 Chiến lược Giao dịch")
            lw_ht = float(df['Lower'].iloc[-1])
            st.table(pd.DataFrame({
                "Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
                "Giá tham chiếu": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]
            }))

st.sidebar.markdown("---")
st.sidebar.write("💻 **Bảo Minh MBA System**")
