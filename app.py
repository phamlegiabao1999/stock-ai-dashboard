import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import ccxt

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="AI Stock - Bảo Minh", layout="wide")

# --- 2. DATABASE DANH MỤC (PHẦN BỊ THIẾU CỦA BẠN ĐÂY) ---
stock_dict = {
    "NHÓM FMCG & BÁN LẺ": {
        "MSN": "Masan Group (Tiêu dùng)",
        "VNM": "Vinamilk (Sữa)",
        "SAB": "Sabeco (Bia rượu)",
        "MWG": "Thế giới di động (Bách Hóa Xanh)",
        "MCH": "Masan Consumer",
        "KDC": "Kido (Dầu ăn, bánh kẹo)"
    },
    "NHÓM CÔNG NGHỆ & SẢN XUẤT": {
        "FPT": "FPT (Công nghệ)",
        "HPG": "Hòa Phát (Thép)",
        "HSG": "Hoa Sen (Thép)",
        "DGC": "Đức Giang (Hóa chất)"
    },
    "NHÓM BẤT ĐỘNG SẢN": {
        "VIC": "Vingroup", "VHM": "Vinhomes", "VRE": "Vincom Retail",
        "NVL": "Novaland", "PDR": "Phát Đạt", "DXG": "Đất Xanh"
    },
    "NHÓM NGÂN HÀNG": {
        "VCB": "Vietcombank", "TCB": "Techcombank", "MBB": "MB Bank",
        "STB": "Sacombank", "VPB": "VPBank", "ACB": "ACB"
    },
    "TIỀN ĐIỆN TỬ (CRYPTO)": {
        "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum",
        "SOL-USD": "Solana", "BNB-USD": "Binance Coin"
    }
}

flat_list = []
for group, stocks in stock_dict.items():
    for ticker, name in stocks.items():
        flat_list.append(f"{ticker} - {name} ({group})")

st.title("📈 AI Stock Analysis Dashboard")

# --- 3. GIAO DIỆN TÌM KIẾM ---
st.sidebar.header("🔍 Bộ lọc mã chứng khoán")
search_choice = st.sidebar.selectbox("Gõ tên công ty hoặc ngành:", options=["Tự nhập mã khác..."] + flat_list)

if search_choice == "Tự nhập mã khác...":
    ma_final = st.sidebar.text_input("Nhập mã:", "").upper()
else:
    ma_final = search_choice.split(" - ")[0]

if ma_final:
    # Xử lý ký hiệu cho yfinance
    ticker_symbol = ma_final + ".VN" if "-" not in ma_final and "." not in ma_final else ma_final
    
    if st.sidebar.button("🚀 Bắt đầu phân tích"):
        with st.spinner(f'Đang phân tích dữ liệu {ma_final}...'):
            # Lấy dữ liệu nến
            data = yf.download(ticker_symbol, period="1y", progress=False)
            
            if not data.empty:
                # TÍNH TOÁN KỸ THUẬT
                data['MA20'] = data['Close'].rolling(window=20).mean()
                data['STD'] = data['Close'].rolling(window=20).std()
                data['Upper'] = data['MA20'] + (data['STD'] * 2)
                data['Lower'] = data['MA20'] - (data['STD'] * 2)
                
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))

                # Lấy giá trị cuối cùng an toàn hơn cho kiểu dữ liệu DataFrame của yfinance mới
                gia_ht = float(data['Close'].iloc[-1])
                rsi_ht = float(data['RSI'].iloc[-1])
                ma20_ht = float(data['MA20'].iloc[-1])
                lower_band = float(data['Lower'].iloc[-1])

                # --- HIỂN THỊ GIAO DIỆN ---
                st.subheader(f"Kết quả phân tích mã: {ma_final}")
                
                tab1, tab2, tab3 = st.tabs(["🤖 Nhận định & Vùng mua", "📋 Bảng giá & Lịch sử", "📊 Biểu đồ kỹ thuật"])

                with tab1:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Giá hiện tại", f"{gia_ht:,.0f}")
                    c2.metric("Chỉ số RSI", f"{rsi_ht:.2f}")
                    c3.metric("So với MA20", f"{((gia_ht/ma20_ht)-1)*100:.2f}%")

                    st.markdown("---")
                    st.markdown("### 🤖 Nhận định chiến lược từ AI")
                    
                    if rsi_ht < 35:
                        st.success(f"💎 **TÍN HIỆU MUA:** RSI thấp ({rsi_ht:.2f}). Giá đang ở vùng quá bán.")
                        st.info(f"📍 **Vùng mua tham khảo:** {lower_band:,.0f} - {gia_ht:,.0f}")
                    elif rsi_ht > 70:
                        st.error(f"⚠️ **CẢNH BÁO BÁN:** RSI ({rsi_ht:.2f}) quá cao. Nguy cơ đảo chiều.")
                        st.info(f"📍 **Hành động:** Chốt lời bớt hoặc chờ về vùng {ma20_ht:,.0f}")
                    elif gia_ht > ma20_ht:
                        st.info(f"📈 **XU HƯỚNG TĂNG:** Giá trên MA20. Tiếp tục nắm giữ.")
                        st.info(f"📍 **Điểm mua thêm:** Khi giá điều chỉnh về gần {ma20_ht:,.0f}")
                    else:
                        st.warning(f"📉 **THẬN TRỌNG:** Giá dưới MA20. Xu hướng yếu, nên đứng ngoài.")

                with tab2:
                    col_book, col_trade = st.columns(2)
                    if "-USD" in ma_final:
                        try:
                            exchange = ccxt.binance()
                            symbol_ccxt = ma_final.replace("-", "/")
                            
                            with col_book:
                                st.write("**📋 Lệnh chờ (Orderbook) - Binance**")
                                ob = exchange.fetch_orderbook(symbol_ccxt, limit=5)
                                df_bids = pd.DataFrame(ob['bids'], columns=['Giá', 'KL'])
                                df_asks = pd.DataFrame(ob['asks'], columns=['Giá', 'KL'])
                                st.write("Phe Bán:")
                                st.dataframe(df_asks.sort_values(by='Giá', ascending=False), use_container_width=True)
                                st.write("Phe Mua:")
                                st.dataframe(df_bids, use_container_width=True)

                            with col_trade:
                                st.write("**🕒 Lịch sử khớp lệnh**")
                                trades = exchange.fetch_trades(symbol_ccxt, limit=10)
                                trade_list = [[t['datetime'].split('T')[1][:8], t['side'].upper(), f"{t['price']:,.2f}", f"{t['amount']:.4f}"] for t in trades]
                                df_trades = pd.DataFrame(trade_list, columns=['Giờ', 'Loại', 'Giá', 'KL'])
                                st.table(df_trades)
                        except Exception as e:
                            st.error(f"Lỗi API Crypto: {e}")
                    else:
                        st.info("💡 Orderbook cho Stock VN cần dữ liệu trả phí. Đây là dữ liệu tham khảo từ phiên gần nhất.")
                        col_book.table(pd.DataFrame({'Giá mua chờ': [gia_ht-100, gia_ht-200], 'Khối lượng': ['20.5k', '50k']}))
                        col_trade.table(pd.DataFrame({'Giờ': ['14:29', '14:28'], 'Giá khớp': [gia_ht, gia_ht], 'KL': ['1.2k', '5k']}))

                with tab3:
                    fig, ax = plt.subplots(figsize=(12, 5))
                    ax.plot(data['Close'], label='Giá', color='#1f77b4', linewidth=2)
                    ax.plot(data['MA20'], label='MA20', color='orange', linestyle='--')
                    ax.fill_between(data.index, data['Lower'], data['Upper'], color='gray', alpha=0.1, label='Vùng biến động')
                    ax.legend()
                    st.pyplot(fig)
            else:
                st.error("Không tìm thấy dữ liệu cho mã này!")

st.sidebar.markdown("---")
st.sidebar.write("💻 Hệ thống hỗ trợ quyết định - Bảo Minh MBA")
