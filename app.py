import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
import pytz
from vnstock3 import Vnstock

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

# CSS Fix giao diện & Zoom
st.markdown("""
    <style>
    .stPlotlyChart { touch-action: pan-y; }
    .bull-container { font-size: 80px; text-align: center; margin: 20px 0; }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- MÀN HÌNH ĐĂNG NHẬP ---
if not st.session_state.logged_in:
    st.title("🔐 Hệ thống Phân tích Bảo Minh MBA")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("👤 Tài khoản:")
            pwd = st.text_input("🔑 Mật khẩu:", type="password")
            if st.form_submit_button("🚀 ĐĂNG NHẬP"):
                if user == "baominh" and pwd == "mba2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Sai thông tin!")
    st.stop()

# --- 2. HÀM LẤY DỮ LIỆU (NGUỒN VNSTOCK - SIÊU ỔN ĐỊNH) ---
@st.cache_data(ttl=300)
def get_clean_data(ticker):
    try:
        # Sử dụng nguồn dữ liệu VCI hoặc SSI
        stock = Vnstock().stock(symbol=ticker, source='VCI')
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        df = stock.quote.history(start=start_date, end=end_date)
        
        if df is not None and not df.empty:
            # Chuẩn hóa tên cột cho Plotly
            df = df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            
            # Tính toán chỉ số kỹ thuật
            df['MA20'] = df['Close'].rolling(20).mean()
            df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
            
            d = df['Close'].diff()
            g = (d.where(d > 0, 0)).rolling(14).mean()
            l = (-d.where(d < 0, 0)).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (g/l)))
            return df
    except Exception as e:
        return None
    return None

# --- 3. DANH MỤC MÃ ---
stock_dict = {
    "HỌ NHÀ VIN": ["VIC", "VHM", "VRE"],
    "DẦU KHÍ": ["GAS", "OIL", "BSR", "PLX", "PVD", "PVS"],
    "BÁN LẺ & BANK": ["MWG", "MSN", "FPT", "VCB", "TCB", "MBB"],
    "THÉP & CK": ["HPG", "HSG", "SSI", "VND", "VCI"]
}
all_options = [ticker for sublist in stock_dict.values() for ticker in sublist]

# --- 4. SIDEBAR ---
st.sidebar.title("Bảo Minh MBA v4.1")
ma_chinh = st.sidebar.selectbox("Chọn mã phân tích:", options=all_options)

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.rerun()

# --- 5. HIỂN THỊ ---
df = get_clean_data(ma_chinh)

if df is not None:
    g_ht = float(df['Close'].iloc[-1])
    rsi_ht = float(df['RSI'].iloc[-1])
    ma_ht = float(df['MA20'].iloc[-1])
    lw_ht = float(df['Lower'].iloc[-1])
    
    st.markdown(f'<h2 style="text-align:center;">📊 Dashboard {ma_chinh}</h2>', unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ", f"{df['Close'].diff().iloc[-1]:,.0f}")
    m2.metric("RSI (14)", f"{rsi_ht:.2f}")
    m3.metric("Hỗ trợ MA20", f"{ma_ht:,.0f}")

    # Biểu đồ nến
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Nến Nhật')])
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ff9800', width=1.5), name='MA20'))
    fig.update_layout(template="plotly_white", height=500, xaxis_rangeslider_visible=False, dragmode='zoom', margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    st.markdown("---")
    st.subheader("📝 Báo cáo nhanh")
    st.success(f"Nhận định {ma_chinh}: Trạng thái {'TÍCH CỰC' if g_ht > ma_ht else 'CẦN QUAN SÁT'}. RSI ở mức {rsi_ht:.2f}. Điểm gom quanh {lw_ht:,.0f} VNĐ.")
    
    st.info("✅ Dữ liệu được bảo mật và cung cấp bởi hệ thống nội địa SSI/VCI.")

else:
    st.markdown('<div class="bull-container">🐂💪🔥</div>', unsafe_allow_html=True)
    st.error("⚠️ Hệ thống đang khởi tạo nguồn dữ liệu mới. Vui lòng đợi 30 giây rồi nhấn Rerun.")

st.sidebar.write("💻 **Data Engine: Vnstock3**")
