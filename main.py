import time
import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# 1. Fake Web Server for Render Health Check
def run_fake_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Fake server running on port {port}...")
    server.serve_forever()

threading.Thread(target=run_fake_server, daemon=True).start()

# 2. Parse Google Service Account
info = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
creds = Credentials.from_service_account_info(info, scopes=[
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
])
client = gspread.authorize(creds)
sheet = client.open("Option chain").sheet1

base_url = "https://www.nseindia.com"
data_url = "https://www.nseindia.com/api/option-chain/indices?symbol=NIFTY"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

def fetch_and_push():
    while True:
        try:
            session = requests.Session()
            # First hit the home page to get valid NSE cookies
            init_res = session.get(base_url, headers=headers, timeout=15)
            
            # Use the captured cookies to pull the actual JSON data
            response = session.get(data_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                raw_records = data['records']['data']
                
                output_rows = [["Strike Price", "CE OI", "CE Change in OI", "CE LTP", "PE LTP", "PE Change in OI", "PE OI"]]
                
                for record in raw_records:
                    strike = record.get('strikePrice')
                    ce = record.get('CE', {})
                    pe = record.get('PE', {})
                    
                    if ce or pe:
                        output_rows.append([
                            strike,
                            ce.get('openInterest', 0),
                            ce.get('changeinOpenInterest', 0),
                            ce.get('lastPrice', 0),
                            pe.get('lastPrice', 0),
                            pe.get('changeinOpenInterest', 0),
                            pe.get('openInterest', 0)
                        ])
                
                sheet.clear()
                sheet.update('A1', output_rows)
                print("Spreadsheet updated cleanly from cloud!")
            else:
                print(f"NSE returned status code: {response.status_code}. Retrying...")
                
        except Exception as e:
            print(f"Data fetch error: {e}. Retrying script loop...")
            
        time.sleep(30)

if __name__ == "__main__":
    fetch_and_push()
