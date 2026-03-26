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

# --- 2. SIDEBAR (BỐ CỤC SO SÁNH) ---
st.sidebar.header("🔍 Phân tích & Đối chiếu")
main_stock_choice = st.sidebar.selectbox("Mã phân tích chính:", options=flat_list)
ma_chinh = main_stock_choice.split(" - ")[0]

# Mục so sánh
st.sidebar.markdown("---")
enable_compare = st.sidebar.checkbox("⚖️ Kích hoạt So sánh đối thủ")
ma_ss = ""
if enable_compare:
    compare_choice = st.sidebar.selectbox("Chọn mã đối chiếu:", options=[x for x in flat_list if x != main_stock_choice])
    ma_ss = compare_choice.split(" - ")[0]

btn_analyze = st.sidebar.button("🚀 Thực hiện phân tích ngay")

# --- 3. HÀM LẤY DỮ LIỆU ---
def get_stock_data(ticker):
    symbol = ticker + ".VN" if "-" not in ticker and "." not in ticker else ticker
    df = yf.download(symbol, period="1y", progress=False)
    if not df.empty:
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['STD'] = df['Close'].rolling(window=20).std()
        df['Upper'] = df['MA20'] + (df['STD'] * 2)
        df['Lower'] = df['MA20'] - (df['STD'] * 2)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain/loss)))
    return df

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
    
    if not df.empty:
        st.title(f"📊 Dashboard Phân Tích: {st.session_state.name_chinh}")

        # --- PHẦN 1: BIỂU ĐỒ NẾN NHẬT ---
        st.subheader("🕯️ Biểu đồ nến Nhật & Bollinger Bands")
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name='Giá nến',
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        )])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
        fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], line=dict(color='rgba(173, 216, 230, 0.3)', width=0.5), name='Boll Upper'))
        fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], line=dict(color='rgba(173, 216, 230, 0.3)', width=0.5), fill='tonexty', name='Boll Lower'))

        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=500, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # --- PHẦN 2: BIỂU ĐỒ SO SÁNH (CÁI BẠN CẦN ĐÂY!) ---
        if st.session_state.compare_df is not None:
            st.markdown("---")
            st.subheader(f"⚔️ So sánh hiệu suất tăng trưởng: {st.session_state.name_chinh} vs {st.session_state.name_ss}")
            df_ss = st.session_state.compare_df
            
            # Đưa về cùng gốc 0% để so sánh sức mạnh tương đối
            comp_data = pd.DataFrame({
                st.session_state.name_chinh: (df['Close'] / df['Close'].iloc[0] - 1) * 100,
                st.session_state.name_ss: (df_ss['Close'] / df_ss['Close'].iloc[0] - 1) * 100
            })
            
            st.line_chart(comp_data)
            st.info(f"💡 Giải thích: Biểu đồ thể hiện mức % lợi nhuận nếu bạn đầu tư vào 2 mã này từ 1 năm trước.")

        # --- PHẦN 3: CHIẾN LƯỢC ---
        st.markdown("---")
        col_info, col_plan = st.columns(2)
        rsi_ht = df['RSI'].iloc[-1]
        
        with col_info:
            st.subheader("📚 Chỉ số kỹ thuật")
            st.metric("RSI hiện tại", f"{rsi_ht:.2f}")
            if rsi_ht < 35: st.success("💎 VÙNG MUA (Quá bán)")
            elif rsi_ht > 70: st.error("🔥 VÙNG BÁN (Quá mua)")
            else: st.info("📉 TRẠNG THÁI CÂN BẰNG")
            st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)

        with col_plan:
            st.subheader("🎯 Kế hoạch giao dịch MBA")
            lw_ht = df['Lower'].iloc[-1]
            ma_ht = df['MA20'].iloc[-1]
            plan = pd.DataFrame({
                "Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
                "Giá tham khảo": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]
            })
            st.table(plan)

st.sidebar.markdown("---")
st.sidebar.write("💻 **Bảo Minh MBA System v2.0**")
