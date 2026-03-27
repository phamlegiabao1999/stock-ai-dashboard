import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime
import pytz
import feedparser
import random

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Stock Analytics Pro - Bảo Minh MBA", layout="wide")

st.markdown("""
    <style>
    .stPlotlyChart { touch-action: pan-y; }
    .js-plotly-plot .plotly .modebar { left: 50% !important; transform: translateX(-50%) !important; top: 0px !important; }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- MÀN HÌNH ĐĂNG NHẬP ---
if not st.session_state.logged_in:
    st.title("🔐 Hệ thống Phân tích Bảo Minh MBA")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        with st.form("login_form"):
            user = st.text_input("👤 Tài khoản:")
            pwd = st.text_input("🔑 Mật khẩu:", type="password")
            submit = st.form_submit_button("🚀 ĐĂNG NHẬP")
            if submit:
                if user == "baominh" and pwd == "mba2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Sai thông tin!")
    st.stop()

# --- 2. HÀM HỖ TRỢ (Cơ chế tránh bị chặn) ---
@st.cache_data(ttl=600) # Lưu dữ liệu trong 10 phút để tránh gọi Yahoo quá nhiều
def get_clean_data(ticker):
    if not ticker: return None, None
    symbol = ticker + ".VN" if "." not in ticker else ticker
    try:
        stock = yf.Ticker(symbol)
        # Lấy dữ liệu 6 tháng thay vì 1 năm để giảm tải request
        df = stock.history(period="6m", interval="1d", timeout=10)
        
        if df is not None and not df.empty:
            df['MA20'] = df['Close'].rolling(20).mean()
            df['Lower'] = df['MA20'] - (df['Close'].rolling(20).std() * 2)
            df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
            d = df['Close'].diff(); g = (d.where(d > 0, 0)).rolling(14).mean(); l = (-d.where(d < 0, 0)).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (g/l)))
            return df, stock
    except Exception:
        return None, None
    return None, None

# --- 3. DANH MỤC MÃ (Giữ nguyên các nhóm ngành Bảo Minh thích) ---
stock_dict = {
    "HỌ NHÀ VIN": {"VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail"},
    "DẦU KHÍ": {"GAS": "PV GAS", "PLX": "Petrolimex", "BSR": "Lọc dầu Bình Sơn", "OIL": "PV OIL", "PVD": "PV Drilling"},
    "BÁN LẺ & BANK": {"MWG": "Thế Giới Di Động", "MSN": "Masan Group", "FPT": "FPT Corp", "VCB": "Vietcombank", "TCB": "Techcombank"},
    "THÉP & CK": {"HPG": "Hòa Phát", "HSG": "Hoa Sen", "SSI": "SSI", "VND": "VNDIRECT"}
}
all_options = [f"{t} - {n}" for g, s in stock_dict.items() for t, n in s.items()]

# --- 4. SIDEBAR ---
st.sidebar.title("Chào Bảo Minh MBA!")
ma_chinh_choice = st.sidebar.selectbox("Chọn mã phân tích:", options=all_options)
ma_chinh = ma_chinh_choice.split(" - ")[0]

if st.sidebar.button("🔴 Đăng xuất"):
    st.session_state.logged_in = False; st.rerun()

# --- 5. HIỂN THỊ ---
df, stock_obj = get_clean_data(ma_chinh)

if df is not None:
    # --- Mọi tính năng cũ: Giá, RSI, ATR, Biểu đồ nến, Báo cáo nhanh... giữ nguyên ---
    g_ht = float(df['Close'].iloc[-1]); rsi_ht = float(df['RSI'].iloc[-1]); ma_ht = float(df['MA20'].iloc[-1]); lw_ht = float(df['Lower'].iloc[-1])
    
    st.title(f"📊 Dashboard: {ma_chinh}")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ")
    m2.metric("RSI (14)", f"{rsi_ht:.2f}")
    m3.metric("Mục tiêu hỗ trợ", f"{lw_ht:,.0f} VNĐ")

    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.update_layout(template="plotly_white", height=450, xaxis_rangeslider_visible=False, dragmode='zoom')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    st.markdown("---")
    st.subheader("📝 Báo cáo nhanh")
    st.info(f"Mã {ma_chinh} hiện tại giá {g_ht:,.0f} VNĐ. RSI ở mức {rsi_ht:.2f}. {'Cơ hội mua' if rsi_ht < 35 else 'Cần thận trọng' if rsi_ht > 70 else 'Trạng thái cân bằng'}.")

else:
    # HIỂN THỊ KHI BỊ YAHOO CHẶN
    st.error("🚫 Yahoo Finance đang tạm ngắt kết nối với máy chủ của bạn.")
    st.warning("👉 **Cách xử lý cho Bảo Minh:**\n1. Đợi khoảng 1-2 phút rồi nhấn 'Rerun' ở góc phải.\n2. Hạn chế chuyển mã quá nhanh trong thời gian ngắn.\n3. Nếu vẫn không được, hãy thử mở bằng mạng 4G thay vì Wifi.")

st.sidebar.write("💻 **Bảo Minh MBA v2.2**")
