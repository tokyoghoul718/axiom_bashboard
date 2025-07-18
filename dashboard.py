import random

# Keep track of positions we "bought"
active_positions = {}  # token -> {"entry_price": float}

def fake_price_for_token(token):
    """
    Demo price generator. Replace with a real price API later.
    """
    # Use token name to seed for stability
    base = random.uniform(0.5, 1.5)
    # Simulate some volatility
    spike = random.uniform(-0.05, 0.05)
    return round(base + spike, 4)

def passes_rug_check(token):
    """
    Basic rug check demo. You can expand with real logic later.
    """
    # Use filters from config
    if filters["marketcap"] > 0:
        # Placeholder: always pass for now
        pass
    if filters["liquidity"] > 0:
        # Placeholder: always pass for now
        pass
    # In demo mode, always safe
    return True

def monitor_wallets_for_snipes():
    """
    Placeholder for future wallet copy-trading.
    When you add wallet addresses in config["COPY_WALLETS"],
    this is where you'd fetch their trades from an API and react.
    """
    for wallet in config.get("COPY_WALLETS", []):
        # Demo log for now
        logs.append(f"[{time.strftime('%H:%M:%S')}] 👀 Watching wallet {wallet} for snipes...")

def run_bot():
    """
    Main bot loop. Scans tokens, applies TP/SL, rug-check, and logs signals.
    """
    while bot_status["running"]:
        try:
            # Step 1: Monitor wallets for sniping (future)
            if config.get("COPY_WALLETS"):
                monitor_wallets_for_snipes()

            # Step 2: Scan tokens
            for token in config.get("TOKENS", []):
                price = fake_price_for_token(token)

                # If not in active_positions, consider buying
                if token not in active_positions:
                    # Example entry rule: random chance of spike
                    if random.random() < 0.1:  # 10% chance per loop
                        if passes_rug_check(token):
                            active_positions[token] = {"entry_price": price}
                            logs.append(f"[{time.strftime('%H:%M:%S')}] 🚀 BUY signal for {token} at ${price}")
                        else:
                            logs.append(f"[{time.strftime('%H:%M:%S')}] ❌ Rug-check failed for {token}")
                else:
                    # Already holding, check TP/SL
                    entry = active_positions[token]["entry_price"]
                    change_pct = ((price - entry) / entry) * 100

                    if change_pct >= risk_settings["take_profit"]:
                        logs.append(f"[{time.strftime('%H:%M:%S')}] ✅ TAKE PROFIT on {token}: +{round(change_pct,2)}%")
                        del active_positions[token]
                    elif change_pct <= -risk_settings["stop_loss"]:
                        logs.append(f"[{time.strftime('%H:%M:%S')}] 🔻 STOP LOSS on {token}: {round(change_pct,2)}%")
                        del active_positions[token]

            # Keep logs trimmed
            if len(logs) > 100:
                del logs[0]

            time.sleep(5)

        except Exception as e:
            logs.append(f"[{time.strftime('%H:%M:%S')}] ⚠️ Bot error: {e}")
            time.sleep(5)
