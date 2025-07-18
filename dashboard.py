from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import json
import os
import threading
import time
import random
import requests

# -------------------------------
# Flask app
# -------------------------------
app = Flask(__name__, template_folder="templates")
CORS(app)

# -------------------------------
# Config
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


config = load_config()
RPC_URL = config.get("RPC_URL")
print("CONFIG FILE PATH:", CONFIG_FILE)
print("CONFIG CONTENT LOADED:", config)
print("RPC_URL LOADED:", RPC_URL)

# -------------------------------
# Global state
# -------------------------------
bot_status = {
    "demo": config.get("DEMO_MODE", True),
    "running": False
}

risk_settings = {
    "take_profit": config.get("TAKE_PROFIT", 50),
    "stop_loss": config.get("STOP_LOSS", 20)
}

filters = {
    "marketcap": 0,
    "liquidity": 0
}

copy_wallets = config.get("COPY_WALLETS", [])
tokens = config.get("TOKENS", [])

# -------------------------------
# Demo data
# -------------------------------
trades = [
    {"time": "17s ago", "token": "BONKA", "type": "Buy", "usd": 124.58, "pl": "+3.1%"},
    {"time": "34s ago", "token": "BONKA", "type": "Sell", "usd": 397.54, "pl": "-2.5%"}
]

wallets = [
    {"address": "Wallet1...abc", "trades": 45, "profit": 230, "pl": "+10%"},
    {"address": "Wallet2...xyz", "trades": 32, "profit": -50, "pl": "-3%"}
]

logs = [
    "[10:20:05] ✅ Bot started",
    "[10:22:10] 🎯 Sniper triggered",
    "[10:24:30] ⚙️ Settings updated",
    "[10:25:50] ✅ Trade executed"
]

# -------------------------------
# RPC test
# -------------------------------
def get_current_slot():
    if not RPC_URL:
        return {"error": "No RPC_URL set in config.json"}
    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getSlot"}
        r = requests.post(RPC_URL, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# -------------------------------
# Bot logic
# -------------------------------
active_positions = {}

def fake_price_for_token(token):
    base = random.uniform(0.5, 1.5)
    spike = random.uniform(-0.05, 0.05)
    return round(base + spike, 4)

def passes_rug_check(token):
    """
    Demo rug check: randomly fail tokens that don't meet filters.
    Later, replace with real API data.
    """
    # Fake marketcap and liquidity values for demo
    fake_marketcap = random.randint(0, 1_000_000)
    fake_liquidity = random.randint(0, 500_000)

    # Log what we’re checking
    logs.append(f"[{time.strftime('%H:%M:%S')}] 🧪 Rug-check {token}: mc={fake_marketcap}, liq={fake_liquidity}")

    # Apply filters
    if fake_marketcap < filters["marketcap"]:
        logs.append(f"[{time.strftime('%H:%M:%S')}] ❌ Rug-check fail: marketcap too low")
        return False
    if fake_liquidity < filters["liquidity"]:
        logs.append(f"[{time.strftime('%H:%M:%S')}] ❌ Rug-check fail: liquidity too low")
        return False

    # Random small chance of failure for demo realism
    if random.random() < 0.05:
        logs.append(f"[{time.strftime('%H:%M:%S')}] ❌ Rug-check fail: random flag")
        return False

    logs.append(f"[{time.strftime('%H:%M:%S')}] ✅ Rug-check passed for {token}")
    return True


def monitor_wallets_for_snipes():
    for wallet in config.get("COPY_WALLETS", []):
        logs.append(f"[{time.strftime('%H:%M:%S')}] 👀 Watching wallet {wallet} for snipes...")

import random
import time

def run_bot():
    """
    Main bot loop for demo mode.
    Creates random trades every few seconds while running.
    """
    while bot_status["running"]:
        # Pick a token from config or use demo name
        token_list = config.get("TOKENS", [])
        token = random.choice(token_list) if token_list else "DEMO"

        # Randomly decide buy or sell
        action = random.choice(["Buy", "Sell"])

        # Random trade amount
        usd_amount = round(random.uniform(50, 500), 2)

        # Random P/L
        pl_value = round(random.uniform(-5, 5), 2)
        pl_str = f"{'+' if pl_value >= 0 else ''}{pl_value}%"

        # Timestamp
        trade_time = time.strftime("%H:%M:%S")

        # Append to trades list
        trade_entry = {
            "time": f"{trade_time}",
            "token": token,
            "type": action,
            "usd": usd_amount,
            "pl": pl_str
        }
        trades.append(trade_entry)

        # Keep trades list trimmed (optional)
        if len(trades) > 50:
            trades.pop(0)

        # Log it
        logs.append(f"[{trade_time}] ✅ Demo trade: {action} {token} for ${usd_amount} ({pl_str})")
        if len(logs) > 50:
            logs.pop(0)

        # Wait a few seconds before next trade
        time.sleep(random.uniform(3, 6))


# -------------------------------
# Routes
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html", cfg=config)

@app.route("/toggle_demo", methods=["POST"])
def toggle_demo():
    bot_status["demo"] = not bot_status["demo"]
    config["DEMO_MODE"] = bot_status["demo"]
    save_config()
    return jsonify(bot_status)

@app.route("/start_bot", methods=["POST"])
def start_bot():
    bot_status["running"] = not bot_status["running"]
    if bot_status["running"]:
        threading.Thread(target=run_bot, daemon=True).start()
        logs.append(f"[{time.strftime('%H:%M:%S')}] ✅ Bot started")
    else:
        logs.append(f"[{time.strftime('%H:%M:%S')}] ⏹️ Bot stopped")
    return jsonify(bot_status)

@app.route("/save_risk", methods=["POST"])
def save_risk():
    data = request.json
    risk_settings["take_profit"] = int(data.get("take_profit", risk_settings["take_profit"]))
    risk_settings["stop_loss"] = int(data.get("stop_loss", risk_settings["stop_loss"]))
    config["TAKE_PROFIT"] = risk_settings["take_profit"]
    config["STOP_LOSS"] = risk_settings["stop_loss"]
    save_config()
    logs.append(f"[{time.strftime('%H:%M:%S')}] ⚙️ Risk settings updated")
    return jsonify({"message": "Risk settings saved!", "risk": risk_settings})

@app.route("/save_filters", methods=["POST"])
def save_filters():
    data = request.json
    filters["marketcap"] = int(data.get("marketcap", filters["marketcap"]))
    filters["liquidity"] = int(data.get("liquidity", filters["liquidity"]))
    logs.append(f"[{time.strftime('%H:%M:%S')}] ⚙️ Filters updated")
    return jsonify({"message": "Filters saved!", "filters": filters})

@app.route("/get_trades", methods=["GET"])
def get_trades():
    return jsonify(trades)

@app.route("/get_wallets", methods=["GET"])
def get_wallets():
    return jsonify(wallets)

@app.route("/get_logs", methods=["GET"])
def get_logs():
    return jsonify(logs)

@app.route("/update_tokens", methods=["POST"])
def update_tokens():
    token_str = request.form.get("token_addresses", "")
    token_list = [t.strip() for t in token_str.split(",") if t.strip()]
    config["TOKENS"] = token_list
    save_config()
    logs.append(f"[{time.strftime('%H:%M:%S')}] ✅ Tokens updated")
    return redirect("/")

@app.route("/tokens", methods=["GET"])
def tokens_route():
    result = []
    for t in config.get("TOKENS", []):
        result.append({
            "name": "DemoToken",
            "address": t,
            "price": round(1.23, 4),
            "volume": 12345
        })
    return jsonify(result)

@app.route("/test_rpc", methods=["GET"])
def test_rpc():
    return jsonify(get_current_slot())

# -------------------------------
# Run
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)
