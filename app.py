import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank"}
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name}")

# --- 2. SIDEBAR ---
st.sidebar.header("🔍 Phân tích & Đối chiếu")
main_choice = st.sidebar.selectbox("Mã phân tích chính:", options=flat_list)
ma_chinh = main_choice.split(" - ")[0]

enable_compare = st.sidebar.checkbox("⚖️ Kích hoạt So sánh đối thủ")
ma_ss = ""
if enable_compare:
    compare_choice = st.sidebar.selectbox("Chọn mã đối chiếu:", options=[x for x in flat_list if x != main_choice])
    ma_ss = compare_choice.split(" - ")[0]

btn_analyze = st.sidebar.button("🚀 Thực hiện phân tích")

# --- 3. HÀM LẤY DỮ LIỆU ---
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

# --- 4. XỬ LÝ HIỂN THỊ ---
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
        # LẤY GIÁ TRỊ HIỆN TẠI
        g_ht = float(df['Close'].iloc[-1])
        rsi_ht = float(df['RSI'].iloc[-1])
        ma_ht = float(df['MA20'].iloc[-1])
        
        st.title(f"📊 Dashboard Phân Tích: {st.session_state.name_chinh}")

        # --- KHU VỰC GIÁ HIỆN TẠI (CARD CHỈ SỐ) ---
        c_price, c_rsi, c_ma = st.columns(3)
        c_price.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", delta=f"{df['Close'].diff().iloc[-1]:,.0f} VNĐ")
        c_rsi.metric("Chỉ số RSI (14)", f"{rsi_ht:.2f}")
        c_ma.metric("So với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

        # --- BIỂU ĐỒ NẾN ---
        st.markdown("---")
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name='Giá nến',
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        )])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=450, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # --- LỜI ĐỀ NGHỊ HÀNH ĐỘNG ---
        st.markdown("### 💡 Lời đề nghị hành động")
        if rsi_ht < 35:
            st.success(f"💎 **MUA:** RSI ({rsi_ht:.2f}) Quá bán. Cơ hội tích lũy.")
        elif rsi_ht > 70:
            st.error(f"🔥 **BÁN:** RSI ({rsi_ht:.2f}) Quá mua. Cần thận trọng.")
        else:
            st.info(f"📈 **THEO DÕI:** RSI ({rsi_ht:.2f}) Cân bằng. Ưu tiên nắm giữ.")

        # --- SO SÁNH (%) ---
        if st.session_state.get('compare_df') is not None:
            st.markdown("---")
            st.subheader(f"⚔️ So sánh hiệu suất: {st.session_state.name_chinh} vs {st.session_state.name_ss}")
            df_ss = st.session_state.compare_df
            combined = pd.concat([df['Close'], df_ss['Close']], axis=1).dropna()
            combined.columns = ['Chinh', 'SS']
            if not combined.empty:
                perf = pd.DataFrame({
                    st.session_state.name_chinh: (combined['Chinh'] / combined['Chinh'].iloc[0] - 1) * 100,
                    st.session_state.name_ss: (combined['SS'] / combined['SS'].iloc[0] - 1) * 100
                }, index=combined.index)
                st.line_chart(perf)

        # --- LỊCH SỬ & CÔNG THỨC ---
        st.markdown("---")
        col_hist, col_math = st.columns(2)
        with col_hist:
            st.subheader("📋 Lịch sử 5 phiên gần nhất")
            st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)
        with col_math:
            st.subheader("📐 Công thức & Lý thuyết")
            st.latex(r"RSI = 100 - \frac{100}{1 + RS}")

        # --- CHIẾN LƯỢC CHI TIẾT ---
        st.markdown("---")
        st.subheader("🎯 Chiến lược Giao dịch MBA")
        lw_ht = float(df['Lower'].iloc[-1])
        plan = pd.DataFrame({
            "Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
            "Giá tham chiếu": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]
        })
        st.table(plan)

st.sidebar.markdown("---")
st.sidebar.write("💻 **Bảo Minh MBA System**")
