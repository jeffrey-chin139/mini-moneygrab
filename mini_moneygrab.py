import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import threading
import time
from flask import Flask, send_from_directory
import os

app = Flask(__name__)

# ---------- Scraper Function ----------
def fetch_fx_rates():
    url = "https://www.x-rates.com/table/?from=SGD&amount=1"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", class_="tablesorter ratesTable")
    rows = table.find_all("tr")

    # Currency name → ISO code mapping
    mapping = {
        "US Dollar": "USD",
        "Euro": "EUR",
        "British Pound": "GBP",
        "Indian Rupee": "INR",
        "Australian Dollar": "AUD",
        "Canadian Dollar": "CAD",
        "Swiss Franc": "CHF",
        "Malaysian Ringgit": "MYR",
        "Japanese Yen": "JPY",
        "Chinese Yuan Renminbi": "CNY",
        "Indonesian Rupiah": "IDR",
        "Thai Baht": "THB",
        "Hong Kong Dollar": "HKD",
        "New Zealand Dollar": "NZD",
        "Indonesian Rupiah": "IDR",
        "Philippine Peso": "PHP",
        "Vietnamese Dong": "VND",
        "Korean Won": "KRW",
        "Taiwan Dollar": "TWD"
        # Add more if x-rates lists extra currencies
    }

    fx_data = []
    for row in rows[1:]:  # Skip header
        cols = row.find_all("td")
        if len(cols) >= 3:
            currency_name = cols[0].text.strip()
            inverse_rate = cols[2].text.strip()  # Column 3 = 1 foreign = SGD
            try:
                mid = float(inverse_rate)
            except:
                continue

            if currency_name in mapping:
                code = mapping[currency_name]
                spread = 0.0001  # 0.01%
                bid = round(mid * (1 - spread), 6)
                ask = round(mid * (1 + spread), 6)

                fx_data.append({
                    "code": code,
                    "bid": bid,
                    "ask": ask
                })

    output = {
        "base_currency": "SGD",
        "timestamp": datetime.now().isoformat(),
        "rates": fx_data
    }

    with open("fx_rates.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)

    print(f"FX rates updated at {output['timestamp']}")

# ---------- Background Auto-Updater ----------
def auto_update(interval=60):
    while True:
        try:
            fetch_fx_rates()
        except Exception as e:
            print("Error during scraping:", e)
        time.sleep(interval)

# ---------- Self-Ping to Keep Render Awake ----------
def self_ping():
    url = "https://mini-moneygrab.onrender.com/"  # Replace with your actual Render URL
    while True:
        try:
            requests.get(url)
            print("Pinged self to stay awake.")
        except Exception as e:
            print("Ping failed:", e)
        time.sleep(600)  # Ping every 10 minutes

# ---------- Flask Routes ----------
@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")

@app.route("/fx_rates.json")
def serve_json():
    return send_from_directory(".", "fx_rates.json")

# ---------- Main Entry Point ----------
if __name__ == "__main__":
    # Start background scraper thread
    thread = threading.Thread(target=auto_update, daemon=True)
    thread.start()

    # Start self-ping thread
    ping_thread = threading.Thread(target=self_ping, daemon=True)
    ping_thread.start()

    print("Mini MoneyGrab with bid/ask is starting in the cloud...")

    # Render uses a dynamic PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
