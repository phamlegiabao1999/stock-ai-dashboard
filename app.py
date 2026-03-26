import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Stock Analytics - Bảo Minh MBA", layout="wide")

# --- 2. DANH MỤC MÃ CHỨNG KHOÁN ---
stock_dict = {
    "BÁN LẺ & FMCG": {"MWG": "MWG", "MSN": "Masan", "VNM": "Vinamilk", "PNJ": "PNJ"},
    "THÉP & CÔNG NGHỆ": {"HPG": "Hòa Phát", "FPT": "FPT", "HSG": "Hoa Sen", "DGC": "Đức Giang"},
    "NGÂN HÀNG": {"VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank", "STB": "Sacombank"}
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name} ({group})")

# --- 3. KHỞI TẠO BỘ NHỚ ---
if "data" not in st.session_state: st.session_state.data = None
if "ma_current" not in st.session_state: st.session_state.ma_current = ""

# --- 4. SIDEBAR (THANH CÔNG CỤ) ---
st.sidebar.header("🔍 Bộ lọc chuyên sâu")
search_choice = st.sidebar.selectbox("Chọn mã niêm yết:", options=["Tự nhập mã khác..."] + flat_list)

if search_choice == "Tự nhập mã khác...":
    ma_input = st.sidebar.text_input("Nhập mã (VD: HPG):", "").upper().strip()
else:
    ma_input = search_choice.split(" - ")[0].strip()

btn_analyze = st.sidebar.button("🚀 Bắt đầu phân tích")

# --- 5. XỬ LÝ DỮ LIỆU ---
if (btn_analyze or st.session_state.data is not None) and ma_input:
    # Chỉ tải lại khi người dùng nhấn nút hoặc đổi mã mới
    if btn_analyze or st.session_state.ma_current != ma_input:
        ticker_symbol = ma_input + ".VN" if "-" not in ma_input and "." not in ma_input else ma_input
        with st.spinner(f'Đang trích xuất dữ liệu {ma_input}...'):
            try:
                df = yf.download(ticker_symbol, period="1y", progress=False)
                if not df.empty:
                    # Tính toán các chỉ số kỹ thuật
                    df['MA20'] = df['Close'].rolling(window=20).mean()
                    df['STD'] = df['Close'].rolling(window=20).std()
                    df['Lower'] = df['MA20'] - (df['STD'] * 2)
                    df['Upper'] = df['MA20'] + (df['STD'] * 2)
                    
                    # Tính toán RSI
                    delta = df['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    df['RSI'] = 100 - (100 / (1 + (gain/loss)))
                    
                    st.session_state.data = df
                    st.session_state.ma_current = ma_input
                else:
                    st.error("⚠️ Không tìm thấy dữ liệu cho mã này trên Yahoo Finance.")
            except Exception as e:
                st.error(f"❌ Lỗi kết nối dữ liệu: {e}")

    # HIỂN THỊ KẾT QUẢ PHÂN TÍCH
    if st.session_state.data is not None:
        df = st.session_state.data
        g_ht = float(df['Close'].iloc[-1].item())
        rsi_ht = float(df['RSI'].iloc[-1].item())
        ma_ht = float(df['MA20'].iloc[-1].item())
        lw_ht = float(df['Lower'].iloc[-1].item())
        
        st.title(f"📊 Dashboard Phân Tích: {st.session_state.ma_current}")
        
        # --- CỘT CHỈ SỐ NHANH ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Giá hiện tại", f"{g_ht:,.0f} VNĐ")
        c2.metric("Chỉ số RSI (14)", f"{rsi_ht:.2f}")
        c3.metric("So với MA20", f"{((g_ht/ma_ht)-1)*100:+.2f}%")

        # --- BIỂU ĐỒ & LỊCH SỬ ---
        col_chart, col_hist = st.columns([2, 1])
        
        with col_chart:
            st.subheader("📈 Biểu đồ kỹ thuật (1 Năm)")
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df.index, df['Close'], color='#1f77b4', label='Giá đóng cửa')
            ax.plot(df.index, df['MA20'], color='orange', linestyle='--', label='Đường MA20')
            ax.fill_between(df.index, df['Lower'], df['Upper'], color='gray', alpha=0.1, label='Bollinger Bands')
            ax.set_ylabel("Giá (VNĐ)")
            ax.legend()
            st.pyplot(fig)
            
        with col_hist:
            st.subheader("📋 Lịch sử 5 phiên cuối")
            st.dataframe(df[['Close', 'RSI']].tail(5), use_container_width=True)
            
            # CÔNG THỨC TOÁN HỌC
            st.subheader("📐 Công thức")
            st.latex(r"RSI = 100 - \frac{100}{1 + RS}")
            st.caption("Trong đó RS = Trung bình tăng / Trung bình giảm")

        st.markdown("---")
        
        # --- KHUYẾN NGHỊ & CHIẾN LƯỢC ---
        st.header("🎯 Khuyến nghị hành động (MBA Insight)")
        col_rec, col_strat = st.columns(2)
        
        with col_rec:
            st.subheader("💡 Nhận định thị trường")
            if rsi_ht < 35:
                st.success(f"💎 **VÙNG MUA:** RSI ({rsi_ht:.2f}) cho thấy cổ phiếu đang bị bán quá mức. Cơ hội tích lũy cao.")
            elif rsi_ht > 70:
                st.error(f"🔥 **VÙNG BÁN:** RSI ({rsi_ht:.2f}) quá cao. Áp lực chốt lời đang gia tăng rõ rệt.")
            else:
                st.info("📉 **THEO DÕI:** Giá đang vận động trong vùng an toàn, chưa có tín hiệu đột phá mạnh.")

        with col_strat:
            st.subheader("📋 Kế hoạch giao dịch")
            plan_data = {
                "Vị thế": ["Mua mới", "Nắm giữ", "Cắt lỗ"],
                "Mức giá tham chiếu": [
                    f"Quanh hỗ trợ {lw_ht:,.0f}",
                    f"Trên ngưỡng MA20 {ma_ht:,.0f}",
                    f"Thủng mức {lw_ht*0.97:,.0f} (-3%)"
                ]
            }
            st.table(pd.DataFrame(plan_data))

st.sidebar.markdown("---")
st.sidebar.write("💻 **Hệ thống Bảo Minh MBA**")
st.sidebar.caption("Phiên bản ổn định 1.0 (No-AI)")
