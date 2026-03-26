import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

# --- 1. CẤU HÌNH & BẢO MẬT (LOGIN) ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

# Khởi tạo trạng thái đăng nhập
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_screen():
    st.sidebar.title("🔐 Hệ thống Bảo Minh MBA")
    user = st.sidebar.text_input("Tài khoản (Tên bạn viết liền):")
    pwd = st.sidebar.text_input("Mật khẩu:", type="password")
    if st.sidebar.button("Đăng nhập"):
        # Tài khoản: baominh | Mật khẩu: mba2026
        if user == "baominh" and pwd == "mba2026":
            st.session_state.logged_in = True
            st.sidebar.success("Đăng nhập thành công!")
            st.rerun()
        else:
            st.sidebar.error("Sai tài khoản hoặc mật khẩu!")

if not st.session_state.logged_in:
    st.title("📈 Hệ thống Phân tích Chứng khoán Chuyên sâu")
    st.info("Vui lòng đăng nhập tại thanh Sidebar bên trái để bắt đầu.")
    # Hiệu ứng chữ chạy thay cho Lottie để tránh lỗi 404
    st.write("---")
    st.subheader("Dành cho quản lý danh mục và ra quyết định đầu tư.")
    st.stop()

# --- 2. HIỆU ỨNG MỞ APP (KHI ĐÃ ĐĂNG NHẬP) ---
if "first_load" not in st.session_state:
    with st.empty():
        for i in range(101):
            st.write(f"🚀 Đang quét dữ liệu thị trường... {i}%")
            time.sleep(0.01)
        st.write("✅ Hệ thống đã sẵn sàng!")
    st.session_state.first_load = True
    time.sleep(1)
    st.rerun()

# --- 3. DANH MỤC MÃ NIÊM YẾT ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen", "DGC": "Đức Giang"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank", "STB": "Sacombank"}
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name} ({group})")

# --- 4. SIDEBAR ĐIỀU KHIỂN ---
st.sidebar.success(f"Chào Bảo Minh MBA!")
if st.sidebar.button("Đăng xuất"):
    st.session_state.logged_in = False
    st.session_state.first_load = False
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

# --- 5. HÀM XỬ LÝ DỮ LIỆU ---
def get_clean_data(ticker):
    symbol = ticker + ".VN" if "-" not in ticker and "." not in ticker else ticker
    df = yf.download(symbol, period="1y", progress=False)
    if df is not None and not df.empty:
        # Xử lý lỗi Multi-index của yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.copy()
        # Chỉ số kỹ thuật
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['STD'] = df['Close'].rolling(window=20).std()
        df['Upper'] = df['MA20'] + (df['STD'] * 2)
        df['Lower'] = df['MA20'] - (df['STD'] * 2)
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain/loss)))
        return df
    return None

# --- 6. HIỂN THỊ KẾT QUẢ ---
if btn_analyze or "main_df" in st.session_state:
    if btn_analyze:
        with st.spinner('Đang tải dữ liệu...'):
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

        # --- 3 THẺ CHỈ SỐ NHANH ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", delta=f"{df['Close'].diff().iloc[-1]:,.0f}")
        c2.metric("Chỉ số RSI (14)", f"{rsi_ht:.2f}")
        c3.metric("Vị thế so với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

        # --- BIỂU ĐỒ NẾN ---
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='Nến Nhật', increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        )])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=450, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # --- CHÚ THÍCH RSI ---
        with st.expander("❓ RSI là gì? (Kiến thức MBA)"):
            st.write("""
            **Relative Strength Index (RSI)** là chỉ số đo lường quán tính thay đổi giá:
            - **Dưới 30 (Quá bán):** Giá đang ở vùng chiết khấu sâu, cơ hội MUA.
            - **Trên 70 (Quá mua):** Giá đã tăng quá nóng, rủi ro điều chỉnh cao, nên BÁN.
            - **Mức 50:** Vùng trung tính của thị trường.
            """)

        # --- LỜI ĐỀ NGHỊ ---
        st.markdown("### 💡 Khuyến nghị hành động")
        if rsi_ht < 35: st.success(f"💎 **MUA:** RSI {rsi_ht:.2f} (Quá bán) - Vùng gom hàng an toàn.")
        elif rsi_ht > 70: st.error(f"🔥 **BÁN:** RSI {rsi_ht:.2f} (Quá mua) - Nên chốt lời bảo vệ thành quả.")
        else: st.info(f"📈 **THEO DÕI:** RSI {rsi_ht:.2f} (Cân bằng) - Tiếp tục nắm giữ.")

        # --- SO SÁNH (%) ---
        if st.session_state.get('compare_df') is not None:
            st.markdown("---")
            df_ss = st.session_state.compare_df
            combined = pd.concat([df['Close'], df_ss['Close']], axis=1).dropna()
            combined.columns = ['Chinh', 'SS']
            perf = pd.DataFrame({
                st.session_state.name_chinh: (combined['Chinh'] / combined['Chinh'].iloc[0] - 1) * 100,
                st.session_state.name_ss: (combined['SS'] / combined['SS'].iloc[0] - 1) * 100
            }, index=combined.index)
            st.subheader(f"⚔️ So sánh hiệu suất: {st.session_state.name_chinh} vs {st.session_state.name_ss}")
            st.line_chart(perf)

        # --- LỊCH SỬ & CHIẾN LƯỢC ---
        st.markdown("---")
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("📋 Lịch sử & Công thức")
            st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)
            st.latex(r"RSI = 100 - \frac{100}{1 + RS}")
        with col_r:
            st.subheader("🎯 Chiến lược Giao dịch")
            lw_ht = float(df['Lower'].iloc[-1])
            st.table(pd.DataFrame({
                "Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
                "Giá tham chiếu": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]
            }))

st.sidebar.markdown("---")
st.sidebar.write("💻 **Bảo Minh MBA System**")
