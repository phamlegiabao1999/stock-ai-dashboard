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
main_stock_choice = st.sidebar.selectbox("Mã phân tích chính:", options=flat_list)
ma_chinh = main_stock_choice.split(" - ")[0]

st.sidebar.markdown("---")
enable_compare = st.sidebar.checkbox("⚖️ Kích hoạt So sánh đối thủ")
ma_ss = ""
if enable_compare:
    compare_choice = st.sidebar.selectbox("Chọn mã đối chiếu:", options=[x for x in flat_list if x != main_stock_choice])
    ma_ss = compare_choice.split(" - ")[0]

btn_analyze = st.sidebar.button("🚀 Thực hiện phân tích")

# --- 3. HÀM LẤY DỮ LIỆU ---
def get_stock_data(ticker):
    symbol = ticker + ".VN" if "-" not in ticker and "." not in ticker else ticker
    df = yf.download(symbol, period="1y", progress=False)
    
    if df is not None and not df.empty:
        # Xử lý Multi-index của yfinance mới
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.copy()
        # Tính toán kỹ thuật
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

# --- 4. XỬ LÝ CHÍNH ---
if btn_analyze or "main_df" in st.session_state:
    if btn_analyze:
        st.session_state.main_df = get_stock_data(ma_chinh)
        st.session_state.name_chinh = ma_chinh
        if enable_compare and ma_ss:
            st.session_state.compare_df = get_stock_data(ma_ss)
            st.session_state.name_ss = ma_ss
        else:
            st.session_state.compare_df = None

    df = st.session_state.main_df
    
    if df is not None:
        st.title(f"📊 Dashboard: {st.session_state.name_chinh}")

        # BIỂU ĐỒ NẾN
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name='Giá nến',
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        )])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=450)
        st.plotly_chart(fig, use_container_width=True)

        # PHẦN SO SÁNH (FIX LỖI VALUEERROR TRIỆT ĐỂ)
        if st.session_state.get('compare_df') is not None:
            df_ss = st.session_state.compare_df
            if not df_ss.empty:
                st.markdown("---")
                st.subheader(f"⚔️ So sánh tăng trưởng (%): {st.session_state.name_chinh} vs {st.session_state.name_ss}")
                
                # Gộp dữ liệu theo trục ngang (axis=1) để đảm bảo đồng bộ ngày
                combined = pd.concat([df['Close'], df_ss['Close']], axis=1).dropna()
                combined.columns = ['Chinh', 'SS']
                
                if not combined.empty:
                    perf_chinh = (combined['Chinh'] / combined['Chinh'].iloc[0] - 1) * 100
                    perf_ss = (combined['SS'] / combined['SS'].iloc[0] - 1) * 100
                    
                    comparison_df = pd.DataFrame({
                        st.session_state.name_chinh: perf_chinh,
                        st.session_state.name_ss: perf_ss
                    }, index=combined.index)
                    
                    st.line_chart(comparison_df)
                else:
                    st.warning("⚠️ Dữ liệu thời gian của hai mã không khớp nhau để so sánh.")

        # CHIẾN LƯỢC
        st.markdown("---")
        c1, c2 = st.columns(2)
        rsi_ht = float(df['RSI'].iloc[-1])
        with c1:
            st.subheader("📚 Chỉ số kỹ thuật")
            st.metric("RSI (14 phiên)", f"{rsi_ht:.2f}")
            if rsi_ht < 35: st.success("💎 VÙNG MUA")
            elif rsi_ht > 70: st.error("🔥 VÙNG BÁN")
            else: st.info("📈 CÂN BẰNG")
            
        with c2:
            st.subheader("🎯 Kế hoạch MBA")
            lw_ht = float(df['Lower'].iloc[-1])
            plan = pd.DataFrame({
                "Vị thế": ["Mua mới", "Nắm giữ"],
                "Giá tham khảo": [f"Quanh {lw_ht:,.0f}", f"Trên hỗ trợ"]
            })
            st.table(plan)

st.sidebar.markdown("---")
st.sidebar.write("💻 **Bảo Minh MBA System**")
