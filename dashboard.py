import json
import os
import threading
import time
import random
import requests
from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS

# -------------------------------
# Flask app setup
# -------------------------------
app = Flask(__name__, template_folder="templates")
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# -------------------------------
# Config helpers
# -------------------------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# -------------------------------
# Load initial config
# -------------------------------
config = load_config()
RPC_URL = config.get("RPC_URL")
print("CONFIG FILE PATH:", CONFIG_FILE)
print("CONFIG CONTENT LOADED:", config)
print("RPC_URL LOADED:", RPC_URL)

# -------------------------------
# State
# -------------------------------
bot_status = {"demo": config.get("DEMO_MODE", True), "running": False}
sniper_status = {"enabled": False}  # NEW for Sniper Mode
risk_settings = {"take_profit": config.get("TAKE_PROFIT", 50), "stop_loss": config.get("STOP_LOSS", 20)}
filters = {"marketcap": 0, "liquidity": 0}
trades = []
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
# Rug check with holder/mcap/liquidity
# -------------------------------
def passes_rug_check(token: str) -> bool:
    largest_holder_percent = random.randint(1, 100)
    fake_marketcap = random.randint(10000, 200000)
    fake_liquidity = random.randint(1000, 50000)

    logs.append(f"[{time.strftime('%H:%M:%S')}] 🧪 Holder check {token}: top holder = {largest_holder_percent}%")
    if len(logs) > 50: logs.pop(0)
    if largest_holder_percent > 40:
        logs.append(f"[{time.strftime('%H:%M:%S')}] 🚨 Rug check failed: top holder owns too much")
        if len(logs) > 50: logs.pop(0)
        return False

    logs.append(f"[{time.strftime('%H:%M:%S')}] 🧪 Marketcap check {token}: mc = ${fake_marketcap}")
    if len(logs) > 50: logs.pop(0)
    if fake_marketcap < filters.get("marketcap", 0):
        logs.append(f"[{time.strftime('%H:%M:%S')}] 🚨 Rug check failed: marketcap too low (min {filters.get('marketcap',0)})")
        if len(logs) > 50: logs.pop(0)
        return False

    logs.append(f"[{time.strftime('%H:%M:%S')}] 🧪 Liquidity check {token}: liq = ${fake_liquidity}")
    if len(logs) > 50: logs.pop(0)
    if fake_liquidity < filters.get("liquidity", 0):
        logs.append(f"[{time.strftime('%H:%M:%S')}] 🚨 Rug check failed: liquidity too low (min {filters.get('liquidity',0)})")
        if len(logs) > 50: logs.pop(0)
        return False

    logs.append(f"[{time.strftime('%H:%M:%S')}] ✅ Rug check passed for {token}")
    if len(logs) > 50: logs.pop(0)
    return True

# -------------------------------
# RPC helper
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
# Bot loop
# -------------------------------
def run_bot():
    while bot_status["running"]:
        token_list = config.get("TOKENS", [])
        token = random.choice(token_list) if token_list else "DEMO"

        if not passes_rug_check(token):
            time.sleep(random.uniform(3, 6))
            continue

        action = random.choice(["Buy", "Sell"])
        usd_amount = round(random.uniform(50, 500), 2)
        pl_value = round(random.uniform(-5, 5), 2)
        pl_str = f"{'+' if pl_value >= 0 else ''}{pl_value}%"
        trade_time = time.strftime("%H:%M:%S")

        trade_entry = {
            "time": f"{trade_time}",
            "token": token,
            "type": action,
            "usd": usd_amount,
            "pl": pl_str
        }
        trades.append(trade_entry)
        if len(trades) > 50:
            trades.pop(0)

        logs.append(f"[{trade_time}] ✅ Demo trade: {action} {token} for ${usd_amount} ({pl_str})")
        if len(logs) > 50:
            logs.pop(0)

        time.sleep(random.uniform(3, 6))

# -------------------------------
# Sniper loop
# -------------------------------
def run_sniper():
    while sniper_status["enabled"]:
        token_list = config.get("TOKENS", [])
        token = random.choice(token_list) if token_list else "NEWDEMO"

        if not passes_rug_check(token):
            time.sleep(random.uniform(5, 8))
            continue

        action = "Buy"
        usd_amount = round(random.uniform(100, 800), 2)
        pl_value = round(random.uniform(-3, 8), 2)
        pl_str = f"{'+' if pl_value >= 0 else ''}{pl_value}%"
        trade_time = time.strftime("%H:%M:%S")

        trade_entry = {
            "time": f"{trade_time}",
            "token": token,
            "type": action,
            "usd": usd_amount,
            "pl": pl_str
        }
        trades.append(trade_entry)
        if len(trades) > 50:
            trades.pop(0)

        logs.append(f"[{trade_time}] 🎯 [SNIPER] Auto-{action} {token} for ${usd_amount} ({pl_str})")
        if len(logs) > 50:
            logs.pop(0)

        time.sleep(random.uniform(5, 10))

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

@app.route("/toggle_sniper", methods=["POST"])
def toggle_sniper():
    sniper_status["enabled"] = not sniper_status["enabled"]
    if sniper_status["enabled"]:
        threading.Thread(target=run_sniper, daemon=True).start()
        logs.append(f"[{time.strftime('%H:%M:%S')}] 🎯 Sniper mode ENABLED")
    else:
        logs.append(f"[{time.strftime('%H:%M:%S')}] 🎯 Sniper mode DISABLED")
    return jsonify(sniper_status)

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
# Run server
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)
