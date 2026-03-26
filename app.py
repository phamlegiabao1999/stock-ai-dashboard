import ccxt
import pandas as pd
import pandas_ta as ta  # Thư viện phân tích kỹ thuật
import time
from datetime import datetime
import tabulate
from decimal import Decimal
import os

class CoinAnalyzer:
    def __init__(self, exchange_id='binance'):
        try:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'enableRateLimit': True,
                # 'apiKey': 'YOUR_API_KEY', # Cần cho đặt lệnh thực, nhưng không cần để lấy dữ liệu
                # 'secret': 'YOUR_SECRET_KEY',
            })
            print(f"✅ Đã kết nối với sàn: {exchange_id.upper()}")
        except AttributeError:
            print(f"❌ Sàn {exchange_id} không được hỗ trợ bởi ccxt.")
            exit()
        except Exception as e:
            print(f"❌ Lỗi kết nối sàn: {e}")
            exit()

    def fetch_data(self, symbol='BTC/USDT', timeframe='1h', limit=50):
        try:
            print(f"⏳ Đang lấy dữ liệu cho {symbol}...")
            # 1. Lấy dữ liệu nến (OHLCV) để phân tích
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            # 2. Lấy dữ liệu Bảng giá chi tiết (Orderbook)
            orderbook = self.exchange.fetch_orderbook(symbol, limit=10)

            # 3. Lấy dữ liệu Lịch sử giao dịch gần đây (Recent Trades)
            trades = self.exchange.fetch_trades(symbol, limit=10)

            return df, orderbook, trades
        except Exception as e:
            print(f"❌ Lỗi khi lấy dữ liệu: {e}")
            return None, None, None

    def display_market_overview(self, df):
        if df is None or df.empty:
            print("⚠️ Không có dữ liệu nến để hiển thị.")
            return

        last_close = df['close'].iloc[-1]
        previous_close = df['close'].iloc[-2]
        change_pct = ((last_close - previous_close) / previous_close) * 100
        
        print(f"\n" + "="*50)
        print(f"📊 TỔNG QUAN THỊ TRƯỜNG ({datetime.now().strftime('%H:%M:%S')})")
        print(f"Đồng: {symbol} | Giá hiện tại: {last_close:,.2f} USDT")
        print(f"Thay đổi (nến cuối): {change_pct:.2f}%")
        print("="*50)

    def display_orderbook_details(self, orderbook):
        if orderbook is None:
            print("⚠️ Không thể lấy dữ liệu Orderbook.")
            return

        print(f"\n📋 BIỂU ĐỒ GIÁ CHI TIẾT (ORDERBOOK) - LỆNH GẦN KHỚP NHẤT")
        bids = orderbook['bids'] # Lệnh MUA đang chờ
        asks = orderbook['asks'] # Lệnh BÁN đang chờ

        # Tạo DataFrame để hiển thị đẹp hơn
        bids_df = pd.DataFrame(bids, columns=['Price', 'Quantity'])
        asks_df = pd.DataFrame(asks, columns=['Price', 'Quantity'])

        # Tính tổng khối lượng (để dễ so sánh phe mua/bán)
        total_bid_vol = bids_df['Quantity'].sum()
        total_ask_vol = asks_df['Quantity'].sum()

        # Hiển thị
        print(f"--- PHE BÁN (ASKS) --- | Tổng KL bán: {total_ask_vol:,.2f}")
        # Phe bán hiển thị từ giá cao xuống thấp (nhưng gần khớp nhất là giá thấp nhất)
        print(tabulate.tabulate(asks_df.sort_values(by='Price', ascending=False), headers='keys', tablefmt='psql', floatfmt=",.4f"))
        
        print("\n" + "^" * 30 + " KHOẢNG GIÁ HIỆN TẠI " + "^" * 30)
        
        print(f"\n--- PHE MUA (BIDS) --- | Tổng KL mua: {total_bid_vol:,.2f}")
        print(tabulate.tabulate(bids_df, headers='keys', tablefmt='psql', floatfmt=",.4f"))
        print("="*50)

    def display_recent_history(self, trades):
        if trades is None:
            print("⚠️ Không thể lấy lịch sử giao dịch.")
            return

        print(f"\n🕒 LỊCH SỬ GIAO DỊCH GẦN ĐÂY (RECENT TRADES)")
        
        trades_data = []
        for trade in trades:
            time_str = datetime.fromtimestamp(trade['timestamp']/1000).strftime('%H:%M:%S')
            trades_data.append([
                time_str,
                "BUY 🟢" if trade['side'] == 'buy' else "SELL 🔴",
                f"{trade['price']:.2f}",
                f"{trade['amount']:.4f}"
            ])
            
        headers = ['Thời gian', 'Loại', 'Giá (USDT)', 'Số lượng']
        print(tabulate.tabulate(trades_data, headers=headers, tablefmt='psql'))
        print("="*50)

    def analyze_and_suggest_entry(self, df):
        if df is None or len(df) < 30: # Cần đủ dữ liệu để tính chỉ số
            print("\n⚠️ Nhận xét và Phân tích: Không đủ dữ liệu.")
            return

        print(f"\n🤖 NHẬN XÉT VÀ VÙNG GIÁ MUA THAM KHẢO")
        print("(Lưu ý: Đây là phân tích kỹ thuật tự động, CHỈ DÙNG ĐỂ THAM KHẢO, không phải lời khuyên đầu tư.)")
        
        # 1. Tính toán các chỉ số kỹ thuật đơn giản bằng pandas-ta
        # - Moving Average (Đường trung bình) - Xác định xu hướng
        df.ta.sma(length=20, append=True) # SMA 20
        df.ta.ema(length=50, append=True) # EMA 50

        # - Relative Strength Index (Chỉ số sức mạnh tương đối) - Quá mua/Quá bán
        df.ta.rsi(length=14, append=True)

        # 2. Lấy các giá trị cuối cùng
        last_row = df.iloc[-1]
        last_price = last_row['close']
        rsi = last_row['RSI_14']
        sma20 = last_row['SMA_20']
        ema50 = last_row['EMA_50']

        # 3. Phân tích xu hướng (Đơn giản: Giá so với SMA 20)
        trend = "TĂNG ⬆️" if last_price > sma20 else "GIẢM ⬇️"
        
        # 4. Phân tích vùng mua (Logic tham khảo: RSI thấp, gần hỗ trợ)
        comments = []
        buy_zone = None

        if trend == "TĂNG ⬆️":
            comments.append(f"• Xu hướng ngắn hạn ({df.attrs['timeframe']}): {trend}. Giá hiện tại ({last_price:,.2f}) nằm trên SMA_20.")
            if rsi < 40:
                comments.append(f"• Chỉ số RSI hiện tại là {rsi:.2f}, đang ở vùng THẤP (gần quá bán), đây có thể là cơ hội.")
                buy_zone = (last_price * 0.99, last_price * 1.00) # Gần giá hiện tại
            elif rsi > 70:
                comments.append(f"• Chỉ số RSI hiện tại là {rsi:.2f}, đang ở vùng QUÁ MUA. Nên thận trọng.")
                buy_zone = (sma20 * 0.99, sma20 * 1.01) # Chờ hồi về SMA20
            else:
                comments.append(f"• Chỉ số RSI ({rsi:.2f}) ở mức trung bình.")
                # Tìm hỗ trợ gần: Giá trị thấp nhất của n nến gần đây
                support_near = df['low'].tail(10).min()
                buy_zone = (support_near, max(support_near * 1.01, ema50)) # Chờ hồi về hỗ trợ/ema50

        else: # Xu hướng Giảm
            comments.append(f"• Xu hướng ngắn hạn ({df.attrs['timeframe']}): {trend}. Giá hiện tại nằm dưới SMA_20.")
            if rsi < 30:
                comments.append(f"• Chỉ số RSI rất thấp ({rsi:.2f}), dấu hiệu QUÁ BÁN, có thể có sóng hồi.")
                buy_zone = (last_price * 0.985, last_price * 1.00) # Mua "bắt đáy" mạo hiểm
            else:
                comments.append(f"• Xu hướng chính là giảm. Nên thận trọng, không nên mua vội.")
                # Vùng mua ở hỗ trợ thấp hơn
                buy_zone = (df['low'].tail(30).min(), sma20 * 0.95)

        # 5. Hiển thị nhận xét
        for comment in comments:
            print(comment)

        # 6. Hiển thị vùng mua
        if buy_zone:
            print(f"👉 Vùng mua tham khảo (Entry Zone): {buy_zone[0]:,.2f} - {buy_zone[1]:,.2f} USDT")
        else:
            print("👉 Không xác định được vùng mua phù hợp lúc này.")
        print("="*50)

if __name__ == "__main__":
    # Khởi tạo Analyzer
    analyzer = CoinAnalyzer(exchange_id='binance')
    symbol = 'BTC/USDT'  # Có thể đổi thành 'ETH/USDT', etc.
    timeframe = '1h'    # Khung giờ để phân tích

    while True:
        os.system('cls' if os.name == 'nt' else 'clear') # Xóa màn hình cho dễ nhìn

        # Lấy dữ liệu
        df, orderbook, trades = analyzer.fetch_data(symbol, timeframe)
        
        # Gắn thông tin timeframe vào df để phân tích
        if df is not None: df.attrs['timeframe'] = timeframe

        # 1. Hiển thị tổng quan
        analyzer.display_market_overview(df)

        # 2. Yêu cầu 1: Biểu đồ giá chi tiết (Orderbook)
        analyzer.display_orderbook_details(orderbook)

        # 3. Yêu cầu 2: Lịch sử gần đây
        analyzer.display_recent_history(trades)

        # 4. Yêu cầu 3: Nhận xét và Vùng mua
        analyzer.analyze_and_suggest_entry(df)

        # Dừng 30 giây trước khi cập nhật tiếp
        print("⏳ Sẽ cập nhật sau 30 giây... Bấm Ctrl+C để dừng.")
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n👋 Đã dừng chương trình.")
            break
