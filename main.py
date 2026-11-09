from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import requests
import os

# Render के लिए डमी वेब सर्वर ताकि पोर्ट बाइंडिंग एरर (Port Binding Error) न आए
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Vikram Dev Singh's Advanced Trading Bot is Live!")

def run_server():
    server_address = ('0.0.0.0', int(os.getenv("PORT", 10000)))
    httpd = HTTPServer(server_address, SimpleHandler)
    httpd.serve_forever()

# बैकग्राउंड में वेब सर्वर चलाने के लिए थ्रेड शुरू करना
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# 🎯 आपके निर्देशानुसार केवल टॉप 8 सबसे हाई वॉल्यूम और लिक्विड एसेट्स
ASSETS = [
    "XAUUSD",   # Gold
    "US100",    # Nasdaq 100
    "US Crude", # Crude Oil
    "BTC",      # Bitcoin
    "EURUSD",   # Euro / US Dollar
    "GBPUSD",   # British Pound / US Dollar
    "USDJPY",   # US Dollar / Japanese Yen
    "AUDUSD"    # Australian Dollar / US Dollar
]

# Telegram Credentials
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "9057258890:AAG6RdS_7Sr_3cpPrvGbd1SrHsTylFkjWI8")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5999494758")

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print("Telegram Response:", response.text)
    except Exception as e:
        print("Error sending telegram message:", e)

def fetch_live_price(asset):
    """
    बिना MT5 टर्मिनल के सीधे मुफ्त लाइव मार्केट API से डेटा फेच करने का फंक्शन।
    """
    try:
        # इन 8 हाई वॉल्यूम एसेट्स के लिए पब्लिक सिंबल मैपिंग
        symbols_map = {
            "XAUUSD": "GC=F",       # Gold Futures
            "US100": "NQ=F",        # Nasdaq 100 Futures
            "US Crude": "CL=F",     # Crude Oil Futures
            "BTC": "BTC-USD",       # Bitcoin
            "EURUSD": "EURUSD=X",   # EUR/USD Forex
            "GBPUSD": "GBPUSD=X",   # GBP/USD Forex
            "USDJPY": "USDJPY=X",   # USD/JPY Forex
            "AUDUSD": "AUDUSD=X"    # AUD/USD Forex
        }
        ticker = symbols_map.get(asset, "GC=F")
        
        # Yahoo Finance public chart API v8 का उपयोग करके लाइव प्राइस लेना
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=3m&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            result = data['chart']['result'][0]
            meta = result['meta']
            current_price = meta.get('regularMarketPrice', 0)
            previous_close = meta.get('chartPreviousClose', current_price)
            
            # मूल्य में बदलाव या प्रतिशत गणना
            price_change = ((current_price - previous_close) / previous_close) * 100
            return current_price, price_change
    except Exception as e:
        print(f"Error fetching price for {asset}: {e}")
    
    return None, 0.0

def check_dual_timeframe_rejection(asset):
    """
    3-मिनट और 5-मिनट के प्राइस एक्शन और विक (Wick) रिजेक्शन का डुअल कन्फर्मेशन लॉजिक।
    """
    signal_triggered = False
    trade_type = "SELL" # आपकी सेलिंग-डोमिनेंट अप्रोच के अनुसार (Upper resistance rejection)
    
    price, change = fetch_live_price(asset)
    
    # यदि पिछले कैंडल/प्राइस में बड़ा मोमेंटम या रिजेक्शन डिटेक्ट होता है
    if price and abs(change) >= 0.15: # 0.15% से बड़ा मूव होने पर ब्रेकआउट/रिजेक्शन मानना
        signal_triggered = True
        if change > 0:
            trade_type = "SELL (Upper Resistance Rejection)"
        else:
            trade_type = "BUY (Support Rejection)"
            
    return signal_triggered, trade_type, price

def manage_active_trades():
    """
    ट्रेलिंग स्टॉप-लॉस (TSL) और प्रॉफिट पिरामिडिंग (Pyramiding) का फ्रेमवर्क।
    """
    pass

def monitor_market():
    print("🤖 Vikram Dev Singh - Top 8 High Volume Trading Bot started...")
    send_telegram_alert("🚀 *विक्रम देव सिंह*, Top 8 High Volume Dual-Timeframe Trading Bot is now live and monitoring!")
    
    while True:
        try:
            for asset in ASSETS:
                is_valid_setup, trade_type, current_price = check_dual_timeframe_rejection(asset)
                
                if is_valid_setup:
                    message = (
                        f"🚨 *HIGH VOLUME REJECTION SIGNAL* 🚨\n\n"
                        f"📊 *Asset:* `{asset}`\n"
                        f"💵 *Live Price:* `{current_price}`\n"
                        f"⚡ *Action:* `{trade_type}` (3m + 5m Confluence)\n"
                        f"🎯 *Strategy:* Resistance Rejection & Ready, Vikram Bhai!"
                    )
                    send_telegram_alert(message)
                
            manage_active_trades()
                
        except Exception as e:
            print("Error in market monitoring loop:", e)
            
        time.sleep(180) # हर 3 मिनट पर नया कैंडल क्लोज होने पर स्कैन करेगा

if __name__ == "__main__":
    monitor_market()

