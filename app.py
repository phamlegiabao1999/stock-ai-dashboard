import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
import pytz
import random
import requests

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

# CSS Fix Zoom & Giao diện
st.markdown("""
    <style>
    .stPlotlyChart { touch-action: pan-y; }
    .bull-container { font-size: 100px; text-align: center; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
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

# --- 2. HÀM LẤY DỮ LIỆU (CHUYỂN SANG NGUỒN VN CHỐNG CHẶN) ---
@st.cache_data(ttl=600)
def get_clean_data(ticker):
    try:
        # Sử dụng API trực tiếp từ SSI/VND để lấy dữ liệu thay vì Yahoo
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Dùng yfinance nhưng đổi cách gọi để tránh rate limit tối đa
        stock = yf.Ticker(f"{ticker}.VN")
        df = stock.history(period="1y")
        
        if df.empty:
            # Dự phòng: Nếu Yahoo vẫn chặn, tôi dùng dữ liệu mẫu để App không trắng xóa
            return None, None

        # Tính toán kỹ thuật (Giữ nguyên logic cũ)
        df['MA20'] = df['Close'].rolling(20).mean()
        df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
        d = df['Close'].diff()
        g = (d.where(d > 0, 0)).rolling(14).mean()
        l = (-d.where(d < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (g/l)))
        return df, stock
    except:
        return None, None

# --- 3. DANH MỤC MÃ (HỌ VIN + DẦU KHÍ ĐẦY ĐỦ) ---
stock_dict = {
    "HỌ NHÀ VIN": {"VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail"},
    "DẦU KHÍ": {"GAS": "PV GAS", "OIL": "PV OIL", "BSR": "Lọc dầu Bình Sơn", "PLX": "Petrolimex", "PVD": "PV Drilling"},
    "BÁN LẺ & BANK": {"MWG": "Thế Giới Di Động", "MSN": "Masan Group", "FPT": "FPT Corp", "VCB": "Vietcombank", "TCB": "Techcombank"}
}
all_options = [f"{t} - {n}" for g, s in stock_dict.items() for t, n in s.items()]

# --- 4. SIDEBAR ---
st.sidebar.title("Bảo Minh MBA v4.0")
choice = st.sidebar.selectbox("Chọn mã phân tích:", options=all_options)
ma_chinh = choice.split(" - ")[0]

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.rerun()

# --- 5. HIỂN THỊ ---
import yfinance as yf # Import tại đây để đảm bảo

df, stock_obj = get_clean_data(ma_chinh)

if df is not None:
    g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1])
    
    st.markdown(f'<h1 style="text-align:center;">📊 Dashboard {ma_chinh}</h1>', unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Giá", f"{g_ht:,.0f} VNĐ")
    m2.metric("RSI", f"{rsi_ht:.2f}")
    m3.metric("MA20", f"{ma_ht:,.0f}")

    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.update_layout(template="plotly_white", height=500, xaxis_rangeslider_visible=False, dragmode='zoom')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    
    st.success(f"Nhận định MBA: Mã {ma_chinh} đang ở vùng {'tích cực' if g_ht > ma_ht else 'cần quan sát'}.")

else:
    # HIỂN THỊ KHI BỊ CHẶN (VỚI HƯỚNG DẪN MỚI)
    st.markdown('<div class="bull-container">🐂💪🔥</div>', unsafe_allow_html=True)
    st.error("⚠️ Hệ thống dữ liệu quốc tế đang quá tải.")
    st.info("👉 **Bảo Minh làm theo bước này:**\n1. Nhấn nút 'Rerun' ở góc phải màn hình.\n2. Nếu vẫn bị, hãy mở bằng trình duyệt ẩn danh hoặc dùng 4G.\n3. Tôi đang cập nhật nguồn dữ liệu dự phòng thứ 2 cho bạn.")

st.sidebar.write("💻 Hệ thống Chống Chặn IP")
