# stocktwits_dashboard.py - API Version (No Selenium!)
import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import re

st.set_page_config(page_title="StockTwits Trending", layout="wide")
st.title("🔥 StockTwits Trending Stocks - Live Auto-Refresh (API Edition)")

placeholder = st.empty()
status = st.empty()

@st.cache_data(ttl=180)  # Cache for 3 minutes
def get_trending():
    # Real StockTwits API endpoint for trending (public, no key needed)
    url = "https://api.stocktwits.com/api/2/streams/symbol/rankings/trending.json"
    params = {"limit": 20}  # Top 20
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; StockTwitsDashboard/1.0)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        symbols = data.get("symbols", [])
        trending_data = []
        
        for sym in symbols:
            # Parse the data - API structure is clean!
            symbol_obj = sym.get("symbol", {})
            ticker = symbol_obj.get("symbol", "N/A")
            rank = sym.get("rank", "N/A")
            volume = f"{sym.get('messages_today', 0):,} messages"  # e.g., 1,234 messages
            change = f"{sym.get('change', 0):.2f}%"  # % change
            # "Trending since" from updated_at timestamp
            updated_at = sym.get("updated_at", "")
            if updated_at:
                # Parse ISO to readable time (e.g., "14:30 ET")
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                since = dt.strftime("%H:%M ET")
            else:
                since = "Just now"
            
            trending_data.append({
                "Rank": rank,
                "Ticker": f"${ticker}",
                "Messages": volume,
                "Change": change,
                "Trending Since": since,
                "Updated": datetime.now().strftime("%H:%M:%S")
            })
        
        return pd.DataFrame(trending_data)
    
    except Exception as e:
        st.error(f"Oops! API hiccup: {str(e)} - Retrying soon...")
        # Fallback dummy data to keep dashboard alive
        return pd.DataFrame({
            "Rank": [1, 2, 3],
            "Ticker": ["$AAPL", "$TSLA", "$NVDA"],
            "Messages": ["1,234 messages", "987 messages", "765 messages"],
            "Change": ["+2.5%", "-1.2%", "+3.1%"],
            "Trending Since": ["14:30 ET", "14:15 ET", "14:00 ET"],
            "Updated": [datetime.now().strftime("%H:%M:%S")] * 3
        })

# Endless refresh loop
while True:
    with placeholder.container():
        df = get_trending()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.dataframe(
                df[["Rank", "Ticker", "Messages", "Change", "Trending Since"]].style
                .set_properties(**{"text-align": "left"})
                .format({"Change": lambda x: x})  # Keep % sign
            )
        with col2:
            # Bar chart: Messages volume (strip commas for numbers)
            volume_num = df["Messages"].str.replace(",", "").str.replace(" messages", "").astype(int)
            st.bar_chart(pd.Series(volume_num, index=df["Ticker"]))
        
        st.caption(f"🐒 Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Refreshes every 3 min • Powered by StockTwits API")
    
    status.success("🍌 Next refresh in 3 minutes...")
    time.sleep(180)  # 3-min nap
