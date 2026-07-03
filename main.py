import time
import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials

# 1. Parse Google Service Account from Environment Variables
# (We set this up on the cloud dashboard so your keys stay safe)
info = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
creds = Credentials.from_service_account_info(info, scopes=[
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
])
client = gspread.authorize(creds)

# Open your sheet (Change to your exact Google Sheet name)
sheet = client.open("Untitled spreadsheet").sheet1  

url = "https://www.nseindia.com/api/option-chain/indices?symbol=NIFTY"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br"
}

def fetch_and_push():
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
    
    print("Cloud script started successfully...")
    while True:
        try:
            response = session.get(url, headers=headers, timeout=10)
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
            
        except Exception as e:
            print(f"Error: {e}. Resetting session...")
            session = requests.Session()
            session.get("https://www.nseindia.com", headers=headers, timeout=10)
            
        time.sleep(30)

if __name__ == "__main__":
    fetch_and_push()