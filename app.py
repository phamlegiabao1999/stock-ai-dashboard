import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import ccxt # Đảm bảo đã thêm vào requirements.txt

# --- CẤU HÌNH BAN ĐẦU ---
st.set_page_config(page_title="AI Stock - Bảo Minh", layout="wide")

# (Phần stock_dict và flat_list giữ nguyên như code cũ của bạn)
# ... [Đoạn code danh mục của bạn] ...

st.title("📈 AI Stock Analysis Dashboard")

# --- GIAO DIỆN TÌM KIẾM ---
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
                # 1. TÍNH TOÁN KỸ THUẬT (Giữ nguyên logic của bạn và thêm Bollinger Bands)
                data['MA20'] = data['Close'].rolling(window=20).mean()
                data['STD'] = data['Close'].rolling(window=20).std()
                data['Upper'] = data['MA20'] + (data['STD'] * 2)
                data['Lower'] = data['MA20'] - (data['STD'] * 2)
                
                # Tính RSI
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))

                # Giá trị hiện tại
                gia_ht = float(data['Close'].iloc[-1].iloc[0] if isinstance(data['Close'].iloc[-1], pd.Series) else data['Close'].iloc[-1])
                rsi_ht = float(data['RSI'].iloc[-1])
                ma20_ht = float(data['MA20'].iloc[-1])
                lower_band = float(data['Lower'].iloc[-1])

                # --- HIỂN THỊ GIAO DIỆN ---
                st.subheader(f"Kết quả phân tích mã: {ma_final}")
                
                # Chia Tabs để hiển thị chi tiết
                tab1, tab2, tab3 = st.tabs(["🤖 Nhận định & Vùng mua", "📋 Bảng giá & Lịch sử", "📊 Biểu đồ kỹ thuật"])

                with tab1:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Giá hiện tại", f"{gia_ht:,.0f} ")
                    c2.metric("Chỉ số RSI", f"{rsi_ht:.2f}")
                    c3.metric("So với MA20", f"{((gia_ht/ma20_ht)-1)*100:.2f}%")

                    st.markdown("---")
                    st.markdown("### 🤖 Nhận định chiến lược từ AI")
                    
                    # Logic Nhận xét & Vùng mua
                    if rsi_ht < 35:
                        st.success(f"💎 **TÍN HIỆU MUA:** RSI thấp ({rsi_ht:.2f}). Giá đang ở vùng quá bán.")
                        st.info(f"📍 **Vùng mua tham khảo:** {lower_band:,.0f} - {gia_ht:,.0f}")
                    elif rsi_ht > 70:
                        st.error(f"⚠️ **CẢNH BÁO BÁN:** RSI cao. Nguy cơ đảo chiều.")
                        st.info(f"📍 **Hành động:** Chốt lời bớt hoặc chờ về vùng {ma20_ht:,.0f}")
                    elif gia_ht > ma20_ht:
                        st.info(f"📈 **XU HƯỚNG TĂNG:** Giá trên MA20. Tiếp tục nắm giữ.")
                        st.info(f"📍 **Điểm mua thêm:** Khi giá điều chỉnh về gần {ma20_ht:,.0f}")
                    else:
                        st.warning(f"📉 **THẬN TRỌNG:** Xu hướng yếu. Đứng ngoài quan sát.")

                with tab2:
                    col_book, col_trade = st.columns(2)
                    
                    # Nếu là Crypto thì lấy data từ Binance qua CCXT
                    if "-USD" in ma_final:
                        try:
                            exchange = ccxt.binance()
                            symbol_ccxt = ma_final.replace("-", "/")
                            
                            with col_book:
                                st.write("**📋 Lệnh chờ (Orderbook)**")
                                ob = exchange.fetch_orderbook(symbol_ccxt, limit=5)
                                df_bids = pd.DataFrame(ob['bids'], columns=['Giá Mua', 'Số lượng'])
                                df_asks = pd.DataFrame(ob['asks'], columns=['Giá Bán', 'Số lượng'])
                                st.dataframe(df_asks.sort_values(by='Giá Bán', ascending=False), use_container_width=True)
                                st.write("---")
                                st.dataframe(df_bids, use_container_width=True)

                            with col_trade:
                                st.write("**🕒 Khớp lệnh gần đây**")
                                trades = exchange.fetch_trades(symbol_ccxt, limit=10)
                                trade_list = [[t['datetime'].split('T')[1][:8], t['side'].upper(), t['price'], t['amount']] for t in trades]
                                df_trades = pd.DataFrame(trade_list, columns=['Giờ', 'Mua/Bán', 'Giá', 'KL'])
                                st.table(df_trades)
                        except:
                            st.write("Không kết nối được API sàn Crypto.")
                    else:
                        st.info("💡 Tính năng Bảng giá chi tiết (L2) cho Chứng khoán VN yêu cầu dữ liệu Premium. Hiện tại hiển thị dữ liệu mô phỏng.")
                        col_book.write("**Bảng giá khớp lệnh dự kiến**")
                        col_book.table(pd.DataFrame({'Giá': [gia_ht, gia_ht-50, gia_ht-100], 'Khối lượng': ['10k', '25k', '15k']}))

                with tab3:
                    fig, ax = plt.subplots(figsize=(12, 5))
                    ax.plot(data['Close'], label='Giá', color='#1f77b4', linewidth=2)
                    ax.plot(data['MA20'], label='MA20', color='orange', linestyle='--')
                    ax.fill_between(data.index, data['Lower'], data['Upper'], color='gray', alpha=0.1, label='Bollinger Bands')
                    ax.legend()
                    st.pyplot(fig)

            else:
                st.error("Không tìm thấy dữ liệu!")

st.sidebar.markdown("---")
st.sidebar.write("💻 Hệ thống hỗ trợ quyết định - Bảo Minh MBA")
