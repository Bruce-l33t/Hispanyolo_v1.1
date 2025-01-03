'''
this bot is used to get the top traders from birdeye api
it makes a calculation to rank them based on pnl, volume, win rate and trade count
    - this calc gives a better rank to traders with high efficiency, win rate and pnl
then it saves the results in two csv files, human and bot traders (determined by trade count)

11/15- went through the top 100 of these and found some bangers. 
'''


import dontshare as d
import requests
import pandas as pd
from datetime import datetime
import time
import os

# 🌙 CONFIG - Customizable by the amazing Moon Dev
CHAIN = "solana"  # Network filter (all, solana, ethereum, etc)
SORT_BY = "PnL"  # Must be: PnL, volume, trade_count (case sensitive!)
SORT_TYPE = "desc"  # asc or desc
TIME_WINDOW = "1W"  # Must be: 1D, 1W, 1M (uppercase!)
DESIRED_RESULTS = 200  # Total number of traders you want in EACH category
BOT_TRADE_THRESHOLD = 500  # If trades > this number, considered a bot
MIN_TRADE_COUNT = 10  # Minimum trades to be considered
MIN_VOLUME_USD = 1000  # Minimum volume in USD
OUTPUT_FOLDER = "data"  # 🚀 Where to save the results
HUMAN_FILE = f"{OUTPUT_FOLDER}/moon_dev_human_traders.csv"
BOT_FILE = f"{OUTPUT_FOLDER}/moon_dev_bot_traders.csv"

# API setup (using Moon Dev's secure method 🔒)
KEY = d.birdeye_api_key


def get_top_traders():
    """Moon Dev's magical trader tracking function ✨"""
    print(f"🌙 Moon Dev's Top Trader Tracker Initiating...")
    
    human_traders = []
    bot_traders = []
    offset = 0
    
    while (len(human_traders) < DESIRED_RESULTS or 
           len(bot_traders) < DESIRED_RESULTS):
        
        print(f"🔄 Fetching batch (offset: {offset})")
        print(f"Current counts - Humans: {len(human_traders)}, Bots: {len(bot_traders)}")
        
        url = f"https://public-api.birdeye.so/trader/gainers-losers"
        headers = {
            "accept": "application/json",
            "x-chain": CHAIN,
            "X-API-KEY": KEY
        }
        
        params = {
            "type": TIME_WINDOW,
            "sort_by": SORT_BY,
            "sort_type": SORT_TYPE,
            "offset": offset,
            "limit": 10  # API limit
        }
        
        print(f"🔍 Requesting with params: {params}")
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text}")
            break
        
        data = response.json()
        if not data.get("success"):
            print("❌ API request failed!")
            break
        
        batch_traders = data.get("data", {}).get("items", [])
        if not batch_traders:
            print("🏁 No more traders found!")
            break
            
        for trader in batch_traders:
            if (trader.get("trade_count", 0) >= MIN_TRADE_COUNT and 
                float(trader.get("volume", 0)) >= MIN_VOLUME_USD):
                
                pnl = float(trader.get("pnl", 0))
                volume = float(trader.get("volume", 0))
                trade_count = trader.get("trade_count", 1)
                win_rate = (trader.get("win_count", 0) / trade_count) * 100

                # Moon Dev Score calculation 🌙
                moon_dev_score = (
                    (pnl / volume) * 10000 +  # Efficiency (return on volume)
                    (win_rate / 100) * 50 +    # Win rate contribution
                    min(pnl / 100000, 100)     # Raw PNL contribution (capped)
                )
                
                trader_data = {
                    "address": trader.get("address"),
                    "network": trader.get("network"),
                    "pnl": pnl,
                    "trade_count": trade_count,
                    "volume": volume,
                    "win_rate": win_rate,
                    "moon_dev_score": moon_dev_score
                }
                
                # Sort into human or bot based on trade count
                if trade_count > BOT_TRADE_THRESHOLD and len(bot_traders) < DESIRED_RESULTS:
                    bot_traders.append(trader_data)
                    print(f"🤖 Found bot trader with {trade_count} trades and PNL: ${pnl:,.2f}")
                elif trade_count <= BOT_TRADE_THRESHOLD and len(human_traders) < DESIRED_RESULTS:
                    human_traders.append(trader_data)
                    print(f"👤 Found human trader with {trade_count} trades and PNL: ${pnl:,.2f}")
        
        offset += 10
        if offset > 10000:  # Safety limit
            print("🛑 Reached maximum offset limit!")
            break
            
        # Be nice to the API 🤝
        time.sleep(0.5)
    
    print(f"🎯 Total traders found - Humans: {len(human_traders)}, Bots: {len(bot_traders)}")
    return human_traders, bot_traders

def save_traders(human_traders, bot_traders):
    """Saving Moon Dev's categorized traders 🚀"""
    # Create data folder if it doesn't exist
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Save human traders
    df_humans = pd.DataFrame(human_traders)
    df_humans.to_csv(HUMAN_FILE, index=False)
    print(f"👤 Human traders saved to {HUMAN_FILE}")
    
    # Save bot traders
    df_bots = pd.DataFrame(bot_traders)
    df_bots.to_csv(BOT_FILE, index=False)
    print(f"🤖 Bot traders saved to {BOT_FILE}")

def main():
    print("🌙 Moon Dev's Top Trader Tracker v1.0")
    print(f"Time Window: {TIME_WINDOW} | Sort By: {SORT_BY} | Chain: {CHAIN}")
    print(f"Bot threshold: {BOT_TRADE_THRESHOLD} trades")
    
    human_traders, bot_traders = get_top_traders()
    if human_traders or bot_traders:
        save_traders(human_traders, bot_traders)
        
        print("\n🔥 Top 3 Human Traders by Moon Dev Score:")
        sorted_humans = sorted(human_traders, key=lambda x: x["moon_dev_score"], reverse=True)[:3]
        for i, trader in enumerate(sorted_humans, 1):
            print(f"{i}. Address: {trader['address'][:8]}...")
            print(f"   PNL: ${trader['pnl']:,.2f} | Volume: ${trader['volume']:,.2f}")
            print(f"   Win Rate: {trader['win_rate']:.1f}% | Trades: {trader['trade_count']}")
            print(f"   Moon Dev Score: {trader['moon_dev_score']:,.2f} 🌟")
    
    print("\n👨‍🚀 Thanks for using Moon Dev's Top Trader Tracker!")

if __name__ == "__main__":
    main()
