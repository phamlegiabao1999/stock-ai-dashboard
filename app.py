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

# --- 3. HÀM LẤY DỮ LIỆU (ĐÃ FIX MULTI-INDEX) ---
def get_stock_data(ticker):
    symbol = ticker + ".VN" if "-" not in ticker and "." not in ticker else ticker
    df = yf.download(symbol, period="1y", progress=False)
    
    if not df.empty:
        # FIX LỖI KEYERROR: Loại bỏ Multi-index nếu có
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Đảm bảo các cột là số (float)
        for col in ['Open', 'High', 'Low', 'Close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

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
        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=450, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # PHẦN SO SÁNH (ĐÃ FIX LỖI MERGE)
        if st.session_state.compare_df is not None:
            st.markdown("---")
            st.subheader(f"⚔️ So sánh tăng trưởng (%): {st.session_state.name_chinh} vs {st.session_state.name_ss}")
            df_ss = st.session_state.compare_df
            
            # Đồng bộ dữ liệu đóng cửa
            combined = pd.DataFrame({
                'Chinh': df['Close'],
                'SS': df_ss['Close']
            }).dropna() # Bỏ các ngày bị lệch dữ liệu
            
            # Tính %
            perf_chinh = (combined['Chinh'] / combined['Chinh'].iloc[0] - 1) * 100
            perf_ss = (combined['SS'] / combined['SS'].iloc[0] - 1) * 100
            
            comparison_df = pd.DataFrame({
                st.session_state.name_chinh: perf_chinh,
                st.session_state.name_ss: perf_ss
            })
            
            st.line_chart(comparison_df)

        # CHIẾN LƯỢC
        st.markdown("---")
        c1, c2 = st.columns(2)
        rsi_ht = float(df['RSI'].iloc[-1])
        with c1:
            st.subheader("📚 Chỉ số kỹ thuật")
            st.metric("RSI (14 phiên)", f"{rsi_ht:.2f}")
            if rsi_ht < 35: st.success("💎 VÙNG MUA")
            elif rsi_ht > 70: st.error("🔥 VÙNG BÁN")
            else: st.info("📉 CÂN BẰNG")
            
        with c2:
            st.subheader("🎯 Kế hoạch MBA")
            lw_ht = float(df['Lower'].iloc[-1])
            plan = pd.DataFrame({
                "Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
                "Giá tham khảo": [f"Quanh {lw_ht:,.0f}", f"Trên hỗ trợ", f"Dưới {lw_ht*0.97:,.0f}"]
            })
            st.table(plan)

st.sidebar.markdown("---")
st.sidebar.write("💻 **Bảo Minh MBA System**")
