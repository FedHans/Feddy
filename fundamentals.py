import requests
from datetime import datetime

def get_coin_fundamentals(coin_name):
    """
    Fetch fundamental data for a cryptocurrency from CoinGecko
    """
    try:
        # Search for the coin ID first
        search_response = requests.get(
            f"https://api.coingecko.com/api/v3/search",
            params={"query": coin_name}
        )
        search_data = search_response.json()
        
        if not search_data.get("coins"):
            return {"error": f"Coin '{coin_name}' not found. Please check the name."}
        
        # Get the first result's ID
        coin_id = search_data["coins"][0]["id"]
        
        # Fetch detailed coin data
        response = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "true",
                "developer_data": "false",
                "sparkline": "false"
            }
        )
        data = response.json()
        
        # Extract market data
        market_data = data.get("market_data", {})
        
        # Get price change percentages for trend analysis
        price_change_24h = market_data.get("price_change_percentage_24h", 0)
        price_change_7d = market_data.get("price_change_percentage_7d", 0)
        price_change_30d = market_data.get("price_change_percentage_30d", 0)
        
        # Determine trend
        if price_change_24h > 5 and price_change_7d > 5:
            trend = "🟢 Strongly Bullish"
        elif price_change_24h > 2 and price_change_7d > 2:
            trend = "🟢 Bullish"
        elif price_change_24h < -5 and price_change_7d < -5:
            trend = "🔴 Strongly Bearish"
        elif price_change_24h < -2 and price_change_7d < -2:
            trend = "🔴 Bearish"
        elif price_change_24h > 0:
            trend = "🟡 Slightly Bullish"
        elif price_change_24h < 0:
            trend = "🟡 Slightly Bearish"
        else:
            trend = "⚪ Neutral"
        
        # Calculate dilution risk
        market_cap = market_data.get("market_cap", {}).get("usd", 0)
        fdv = market_data.get("fully_diluted_valuation", {}).get("usd", 0)
        
        dilution_risk = "Low"
        dilution_ratio = 0
        if market_cap > 0 and fdv > 0:
            dilution_ratio = fdv / market_cap
            if dilution_ratio > 3:
                dilution_risk = "🔴 High (FDV > 3x Market Cap)"
            elif dilution_ratio > 1.5:
                dilution_risk = "🟡 Medium (FDV 1.5-3x Market Cap)"
            else:
                dilution_risk = "🟢 Low (FDV < 1.5x Market Cap)"
        
        # Build the report
        report = f"""
============================================================
📊 **FUNDAMENTAL ANALYSIS: {data['name'].upper()} ({data['symbol'].upper()})**
============================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 **PRICE & MARKET DATA**
  Current Price: ${market_data.get('current_price', {}).get('usd', 'N/A'):,.2f}
  Market Cap: ${market_data.get('market_cap', {}).get('usd', 0):,.0f}
  Fully Diluted Valuation (FDV): ${market_data.get('fully_diluted_valuation', {}).get('usd', 0):,.0f}
  Rank: #{data.get('market_cap_rank', 'N/A')}

📊 **SUPPLY & TOKENOMICS**
  Circulating Supply: {market_data.get('circulating_supply', 0):,.0f} {data['symbol'].upper()}
  Total Supply: {market_data.get('total_supply', 'Unlimited'):,.0f} {data['symbol'].upper()}
  Max Supply: {market_data.get('max_supply', 'Unlimited'):,.0f} {data['symbol'].upper()}

🔄 **DILUTION ANALYSIS**
  FDV / Market Cap Ratio: {dilution_ratio:.2f}x
  Dilution Risk: {dilution_risk}

📉 **PRICE TREND**
  24h Change: {price_change_24h:+.2f}%
  7d Change: {price_change_7d:+.2f}%
  30d Change: {price_change_30d:+.2f}%
  Overall Trend: {trend}

📅 **ALL-TIME STATS**
  All-Time High: ${market_data.get('ath', {}).get('usd', 'N/A'):,.2f}
  All-Time Low: ${market_data.get('atl', {}).get('usd', 'N/A'):,.2f}

💡 **QUICK SUMMARY**
  {data['name']} is currently trading at ${market_data.get('current_price', {}).get('usd', 'N/A'):,.2f} with a market cap of ${market_data.get('market_cap', {}).get('usd', 0):,.0f}.
  The project has {market_data.get('circulating_supply', 0):,.0f} tokens in circulation out of {market_data.get('total_supply', 'unlimited')} total supply.
  The FDV of ${market_data.get('fully_diluted_valuation', {}).get('usd', 0):,.0f} is {dilution_ratio:.2f}x the current market cap, indicating {dilution_risk.lower()} dilution risk.
  The price has {price_change_24h:+.2f}% in the last 24 hours, showing a {trend.split()[1].lower()} trend.

============================================================
  Data sourced from CoinGecko
  ⚠️ Always do your own research (DYOR)
============================================================
"""
        return report
        
    except Exception as e:
        return f"❌ Error fetching data: {str(e)}"

# For testing directly
if __name__ == "__main__":
    coin = input("Enter coin name (e.g., bitcoin, ethereum, solana): ")
    result = get_coin_fundamentals(coin)
    print(result)