import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Hệ thống Bảo Minh MBA", layout="wide")

stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank"}
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name} ({group})")

# --- 2. SESSION STATE ---
if "data" not in st.session_state: st.session_state.data = None
if "ma_current" not in st.session_state: st.session_state.ma_current = ""

# --- 3. SIDEBAR ---
st.sidebar.header("🔍 Bộ lọc chuyên sâu")
search_choice = st.sidebar.selectbox("Chọn mã niêm yết:", options=["Tự nhập mã khác..."] + flat_list)
ma_input = st.sidebar.text_input("Mã:", "").upper().strip() if search_choice == "Tự nhập mã khác..." else search_choice.split(" - ")[0].strip()
btn_analyze = st.sidebar.button("🚀 Bắt đầu phân tích")

# --- 4. XỬ LÝ DỮ LIỆU ---
if (btn_analyze or st.session_state.data is not None) and ma_input:
    if btn_analyze or st.session_state.ma_current != ma_input:
        symbol = ma_input + ".VN" if "-" not in ma_input and "." not in ma_input else ma_input
        with st.spinner(f'Đang tải {ma_input}...'):
            df = yf.download(symbol, period="1y", progress=False)
            if not df.empty:
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['STD'] = df['Close'].rolling(window=20).std()
                df['Lower'] = df['MA20'] - (df['STD'] * 2)
                df['Upper'] = df['MA20'] + (df['STD'] * 2)
                d = df['Close'].diff()
                g = (d.where(d > 0, 0)).rolling(window=14).mean()
                l = (-d.where(d < 0, 0)).rolling(window=14).mean()
                df['RSI'] = 100 - (100 / (1 + (g/l)))
                st.session_state.data = df
                st.session_state.ma_current = ma_input
            else:
                st.error("Không lấy được dữ liệu. Kiểm tra lại mã!")

    if st.session_state.data is not None:
        df = st.session_state.data
        g_ht = float(df['Close'].iloc[-1])
        rsi_ht = float(df['RSI'].iloc[-1])
        ma_ht = float(df['MA20'].iloc[-1])
        lw_ht = float(df['Lower'].iloc[-1])
        up_ht = float(df['Upper'].iloc[-1])
        
        st.title(f"📈 Phân tích mã {st.session_state.ma_current}")
        
        # --- KHU VỰC BIỂU ĐỒ NẾN (PLONLY) ---
        st.subheader("📊 Biểu đồ nến Nhật chuyên sâu")
        
        # Tạo biểu đồ nến Nhật
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            name='Nến Nhật',
            # Định nghĩa màu nến
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        )])

        # Thêm đường MA20
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))

        # Thêm dải Bollinger Bands
        fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], line=dict(color='rgba(173, 216, 230, 0.4)', width=0.5), name='Boll Upper'))
        fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], line=dict(color='rgba(173, 216, 230, 0.4)', width=0.5), fill='tonexty', name='Boll Lower'))

        # --- CẤU HÌNH GIAO DIỆN BIỂU ĐỒ SÁNG SỦA ---
        fig.update_layout(
            template="plotly_white", # Ép sang nền trắng
            yaxis_title='Giá (VNĐ)',
            xaxis_rangeslider_visible=False,
            height=600,
            # Cấu hình màu chữ và đường lưới
            xaxis=dict(gridcolor='#e0e0e0', tickfont=dict(color='black')),
            yaxis=dict(gridcolor='#e0e0e0', tickfont=dict(color='black'), autorange=True), # Tự động cân bằng y-axis
            legend=dict(font=dict(color='black'))
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- CHỈ SỐ VÀ CHIẾN LƯỢC ---
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", delta=f"RSI: {rsi_ht:.2f}")
        c2.metric("Chỉ số MA20", f"{ma_ht:,.0f} VNĐ", delta=f"vs MA20: {((g_ht/ma_ht)-1)*100:+.2f}%")
        c3.metric("Bollinger bands", f"{lw_ht:,.0f} - {up_ht:,.0f} VNĐ")

        st.markdown("---")
        col_rec, col_strat = st.columns(2)
        
        with col_rec:
            st.subheader("💡 Nhận định hành động")
            if rsi_ht < 35:
                st.success(f"💎 **VÙNG MUA:** RSI ({rsi_ht:.2f}) Quá bán")
            elif rsi_ht > 70:
                st.error(f"🔥 **VÙNG BÁN:** RSI ({rsi_ht:.2f}) Quá mua")
            else:
                st.info(f"📉 **THEO DÕI:** RSI ({rsi_ht:.2f}) Cân bằng")
            
            st.write("**Lịch sử giá gần đây:**")
            st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)

        with col_strat:
            st.subheader("📋 Bảng chiến lược MBA")
            lw_ht = df['Lower'].iloc[-1]
            ma_ht = df['MA20'].iloc[-1]
            
            plan = pd.DataFrame({
                "Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
                "Giá tham khảo": [f"Quanh {lw_ht:,.0f}", f"Trên {ma_ht:,.0f}", f"Dưới {lw_ht*0.97:,.0f}"]
            })
            st.table(plan)

st.sidebar.markdown("---")
st.sidebar.write("💻 **Bảo Minh MBA System**")
