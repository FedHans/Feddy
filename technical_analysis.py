import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# ============================================================
# CONFIGURATION
# ============================================================
TRACKED_COINS = [
    {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin"},
    {"id": "ethereum", "symbol": "ETH", "name": "Ethereum"},
    {"id": "solana", "symbol": "SOL", "name": "Solana"},
    {"id": "hyperliquid", "symbol": "HYPE", "name": "HYPE"},
]

# ============================================================
# SINGLE API CALL WITH RETRY
# ============================================================
def fetch_data(coin_id, days=30, max_retries=3):
    """Single API call with retry for both historical and current data"""
    for attempt in range(max_retries):
        try:
            # Fetch historical data
            hist_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            hist_params = {"vs_currency": "usd", "days": days, "interval": "daily"}
            
            hist_response = requests.get(hist_url, params=hist_params, timeout=15)
            
            if hist_response.status_code == 429:
                wait_time = (attempt + 1) * 3
                print(f"⏳ Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            elif hist_response.status_code != 200:
                print(f"❌ API error: {hist_response.status_code}")
                time.sleep(2)
                continue
            
            hist_data = hist_response.json()
            prices = [p[1] for p in hist_data.get("prices", [])]
            
            if not prices or len(prices) < 20:
                print(f"❌ Not enough data for {coin_id}")
                return None
            
            # Get current price with 24h change
            price_url = "https://api.coingecko.com/api/v3/simple/price"
            price_params = {"ids": coin_id, "vs_currencies": "usd", "include_24hr_change": "true"}
            price_response = requests.get(price_url, params=price_params, timeout=10)
            
            if price_response.status_code == 200:
                price_data = price_response.json()
                if coin_id in price_data:
                    current_price = price_data[coin_id].get("usd", prices[-1])
                    change_24h = price_data[coin_id].get("usd_24h_change", 0)
                else:
                    current_price = prices[-1]
                    change_24h = 0
            else:
                current_price = prices[-1]
                change_24h = 0
            
            return {
                "prices": prices,
                "current_price": current_price,
                "change_24h": change_24h
            }
            
        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    
    print(f"❌ All attempts failed for {coin_id}")
    return None

# ============================================================
# TECHNICAL INDICATORS
# ============================================================
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    if down == 0:
        return 100
    rs = up / down
    return 100 - (100 / (1 + rs))

def calculate_sma(prices, period):
    if len(prices) < period:
        return prices[-1] if len(prices) > 0 else 0
    return np.mean(prices[-period:])

def calculate_macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow + signal:
        return 0, 0, 0
    
    def ema(data, span):
        if len(data) < span:
            return data[-1] if len(data) > 0 else 0
        return pd.Series(data).ewm(span=span, adjust=False).mean().iloc[-1]
    
    macd_line = ema(prices, fast) - ema(prices, slow)
    
    macd_history = []
    for i in range(signal, len(prices)):
        fast_ema = ema(prices[:i+1], fast)
        slow_ema = ema(prices[:i+1], slow)
        macd_history.append(fast_ema - slow_ema)
    
    if len(macd_history) >= signal:
        signal_line = np.mean(macd_history[-signal:])
    else:
        signal_line = macd_line
    
    return macd_line, signal_line, macd_line - signal_line

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    if len(prices) < period:
        return prices[-1], prices[-1], prices[-1]
    sma = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    return sma + (std * std_dev), sma, sma - (std * std_dev)

def calculate_vwap(prices):
    if not prices or len(prices) < 2:
        return prices[-1] if prices else 0
    return np.mean(prices[-20:]) if len(prices) >= 20 else np.mean(prices)

# ============================================================
# ANALYZE COIN
# ============================================================
def analyze_coin(coin_id, coin_symbol, coin_name, data):
    """Analyze a single coin"""
    if not data:
        return None
    
    prices = data["prices"]
    current_price = data["current_price"]
    change_24h = data["change_24h"]
    
    if len(prices) < 20:
        return None
    
    # Calculate indicators
    rsi = calculate_rsi(prices, 14)
    sma_20 = calculate_sma(prices, 20)
    sma_50 = calculate_sma(prices, 50)
    macd, macd_signal, macd_hist = calculate_macd(prices)
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices, 20, 2)
    vwap = calculate_vwap(prices)
    
    # Generate signals
    signals = []
    signal_count = 0
    
    if rsi < 30:
        signals.append(f"🟢 BUY: RSI Oversold ({rsi:.1f})")
        signal_count += 1
    elif rsi > 70:
        signals.append(f"🔴 SELL: RSI Overbought ({rsi:.1f})")
        signal_count -= 1
    else:
        signals.append(f"⚪ RSI: {rsi:.1f}")
    
    if current_price > sma_20 and sma_20 > sma_50:
        signals.append("🟢 BULLISH: Golden Cross")
        signal_count += 1
    elif current_price < sma_20 and sma_20 < sma_50:
        signals.append("🔴 BEARISH: Death Cross")
        signal_count -= 1
    else:
        signals.append("⚪ SMA: No crossover")
    
    if macd > macd_signal:
        signals.append("🟢 BULLISH: MACD > Signal")
        signal_count += 1
    elif macd < macd_signal:
        signals.append("🔴 BEARISH: MACD < Signal")
        signal_count -= 1
    else:
        signals.append("⚪ MACD: Neutral")
    
    if current_price <= bb_lower:
        signals.append("🟢 BUY: Near Lower Band")
        signal_count += 1
    elif current_price >= bb_upper:
        signals.append("🔴 SELL: Near Upper Band")
        signal_count -= 1
    else:
        signals.append("⚪ BB: Mid-band")
    
    if current_price > vwap:
        signals.append(f"🟢 BULLISH: Price > VWAP (${vwap:,.0f})")
        signal_count += 0.5
    else:
        signals.append(f"🔴 BEARISH: Price < VWAP (${vwap:,.0f})")
        signal_count -= 0.5
    
    if signal_count >= 2.5:
        overall, action = "🟢 STRONG BUY", "Consider accumulating"
    elif signal_count >= 1.5:
        overall, action = "🟢 BUY", "Monitor for entry"
    elif signal_count >= 0.5:
        overall, action = "🟡 BULLISH", "Hold position"
    elif signal_count <= -2.5:
        overall, action = "🔴 STRONG SELL", "Consider reducing"
    elif signal_count <= -1.5:
        overall, action = "🔴 SELL", "Monitor for exit"
    elif signal_count <= -0.5:
        overall, action = "🟡 BEARISH", "Watch closely"
    else:
        overall, action = "⚪ NEUTRAL", "Hold position"
    
    return {
        "name": coin_name,
        "symbol": coin_symbol,
        "price": current_price,
        "change_24h": change_24h,
        "rsi": rsi,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "macd": macd,
        "macd_signal": macd_signal,
        "bb_upper": bb_upper,
        "bb_middle": bb_middle,
        "bb_lower": bb_lower,
        "vwap": vwap,
        "overall": overall,
        "action": action,
        "signals": signals,
        "signal_count": signal_count,
    }

# ============================================================
# BITCOIN SPECIAL ANALYSIS
# ============================================================
def get_bitcoin_prediction(data):
    """Generate Bitcoin-specific analysis"""
    if not data:
        return "❌ Bitcoin data unavailable"
    
    prices = data["prices"]
    current_price = data["current_price"]
    
    if len(prices) < 30:
        return "❌ Insufficient Bitcoin data"
    
    rsi = calculate_rsi(prices, 14)
    sma_20 = calculate_sma(prices, 20)
    sma_50 = calculate_sma(prices, 50)
    macd, macd_signal, _ = calculate_macd(prices)
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices, 20, 2)
    
    bottom_warning = "✅ No bottom signal detected"
    top_warning = "✅ No top signal detected"
    
    if rsi < 30:
        bottom_warning = "⚠️ RSI Oversold - Potential bottom forming!"
    elif current_price <= bb_lower:
        bottom_warning = "⚠️ Price at Lower Band - Oversold!"
    
    if rsi > 70:
        top_warning = "⚠️ RSI Overbought - Potential top forming!"
    elif current_price >= bb_upper:
        top_warning = "⚠️ Price at Upper Band - Overbought!"
    
    if rsi < 30 and macd > macd_signal:
        prediction, move, target = "🟢 BULLISH", "Upward reversal", current_price * 1.05
    elif rsi > 70 and macd < macd_signal:
        prediction, move, target = "🔴 BEARISH", "Downward correction", current_price * 0.95
    elif macd > macd_signal and current_price > sma_50:
        prediction, move, target = "🟢 BULLISH", "Continuing upward", current_price * 1.03
    elif macd < macd_signal and current_price < sma_50:
        prediction, move, target = "🔴 BEARISH", "Continuing downward", current_price * 0.97
    else:
        prediction, move, target = "🟡 NEUTRAL", "Sideways", current_price
    
    return f"""
🔵 **BITCOIN SPECIAL REPORT**

📊 **Current Status**
  Price: ${current_price:,.2f}
  RSI: {rsi:.1f}
  SMA 20: ${sma_20:,.2f}
  SMA 50: ${sma_50:,.2f}
  MACD: {macd:.4f}

📈 **Bollinger Bands**
  Upper: ${bb_upper:,.2f}
  Middle: ${bb_middle:,.2f}
  Lower: ${bb_lower:,.2f}

⚠️ **Signals**
  Bottom: {bottom_warning}
  Top: {top_warning}

🔮 **Prediction**
  Outlook: {prediction}
  Expected: {move}
  Target: ${target:,.2f}

💡 **Recommendation:** {
    "🟢 Accumulate at current levels" if bottom_warning.startswith("⚠️") else
    "🔴 Consider taking profits" if top_warning.startswith("⚠️") else
    "🟢 Hold position for upward momentum" if prediction == "🟢 BULLISH" else
    "🔴 Reduce position, wait for clarity" if prediction == "🔴 BEARISH" else
    "⚪ Wait for clearer direction"
}
"""

# ============================================================
# SECTOR PERFORMANCE (Using CoinGecko Categories)
# ============================================================
def get_sector_performance():
    """Get sector performance from CoinGecko categories"""
    sector_performance = {}
    
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/global",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            market_cap_change = data.get("data", {}).get("market_cap_change_percentage_24h_usd", 0)
            sector_performance["Overall Market"] = market_cap_change
        else:
            sector_performance["Overall Market"] = 0
    except:
        sector_performance["Overall Market"] = 0
    
    # Add tracked coins performance
    for coin in TRACKED_COINS:
        try:
            price_url = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": coin["id"], "vs_currencies": "usd", "include_24hr_change": "true"}
            response = requests.get(price_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if coin["id"] in data:
                    sector_performance[coin["symbol"]] = data[coin["id"]].get("usd_24h_change", 0)
            time.sleep(0.5)
        except:
            continue
    
    return sector_performance

# ============================================================
# GENERATE REPORT
# ============================================================
def generate_portfolio_report():
    """Generate complete portfolio analysis report"""
    print("\n📊 Fetching all coin data...")
    
    # Fetch data for all tracked coins (one call each)
    coin_data = {}
    for coin in TRACKED_COINS:
        print(f"  📊 Fetching {coin['name']}...")
        data = fetch_data(coin["id"], days=30)
        if data:
            coin_data[coin["id"]] = data
        time.sleep(1.5)  # Reduced wait time
    
    report = f"""
============================================================
📊 **PORTFOLIO ANALYSIS REPORT**
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================================================

📈 **MARKET PERFORMANCE**
"""
    
    # Sector performance
    sectors = get_sector_performance()
    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
    
    best_sector = sorted_sectors[0][0] if sorted_sectors else "Unknown"
    best_performance = sorted_sectors[0][1] if sorted_sectors else 0
    
    for sector, change in sorted_sectors:
        emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        report += f"  {emoji} {sector}: {change:+.2f}%\n"
    
    report += f"\n🏆 **Trending: {best_sector}** ({best_performance:+.2f}%)\n"
    
    report += "\n" + "=" * 60 + "\n"
    report += "📊 **TRACKED COINS ANALYSIS**\n\n"
    
    # Analyze each tracked coin
    for coin in TRACKED_COINS:
        data = coin_data.get(coin["id"])
        if not data:
            report += f"❌ {coin['name']}: Data unavailable\n\n"
            continue
        
        result = analyze_coin(coin["id"], coin["symbol"], coin["name"], data)
        if not result:
            report += f"❌ {coin['name']}: Analysis failed\n\n"
            continue
        
        report += f"""
📊 **{result['name']} ({result['symbol']})**
  Price: ${result['price']:,.2f} ({result['change_24h']:+.2f}%)
  RSI: {result['rsi']:.1f}
  SMA 20: ${result['sma_20']:,.2f}
  SMA 50: ${result['sma_50']:,.2f}
  VWAP: ${result['vwap']:,.2f}
  
  Signal: {result['overall']}
  Action: {result['action']}
  Indicators:
"""
        for s in result["signals"]:
            report += f"    {s}\n"
        report += "\n"
    
    # Bitcoin Special Report
    btc_data = coin_data.get("bitcoin")
    report += "\n" + "=" * 60 + "\n"
    report += get_bitcoin_prediction(btc_data) if btc_data else "❌ Bitcoin data unavailable"
    report += "\n" + "=" * 60 + "\n"
    report += "⚠️ Always do your own research (DYOR)\n"
    report += f"Data refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += "=" * 60
    
    return report

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📊 PORTFOLIO ANALYSIS TOOL")
    print("=" * 60)
    report = generate_portfolio_report()
    print(report)