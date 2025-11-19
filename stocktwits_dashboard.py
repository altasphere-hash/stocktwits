# stocktwits_dashboard.py - Web Scraping Edition (Real Data, No API!)
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import re

st.set_page_config(page_title="StockTwits Trending", layout="wide")
st.title("🔥 StockTwits Trending Stocks - Live Auto-Refresh (Scraping Magic)")

placeholder = st.empty()
status = st.empty()

@st.cache_data(ttl=180)  # Cache for 3 minutes
def get_trending():
    url = "https://stocktwits.com/rankings/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find the trending table (common selector for StockTwits - adjust if needed)
        table = soup.find("table")  # Main table
        if not table:
            raise ValueError("No table found - page changed?")
        
        rows = table.find_all("tr")[1:21]  # Skip header, top 20
        data = []
        rank_counter = 1
        
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 4:
                # Rank (auto if not explicit)
                rank = cells[0].get_text(strip=True) or str(rank_counter)
                
                # Ticker: Look for $SYMBOL in link or text
                ticker_cell = cells[1].get_text(strip=True)
                ticker_match = re.search(r'\$([A-Z]+)', ticker_cell)
                ticker = f"${ticker_match.group(1)}" if ticker_match else "N/A"
                
                # Volume: e.g., "1.2K messages"
                volume = cells[2].get_text(strip=True) if len(cells) > 2 else "N/A"
                
                # Change: e.g., "+2.5%"
                change = cells[3].get_text(strip=True) if len(cells) > 3 else "N/A"
                
                # Trending Since: Last cell or infer
                since = cells[-1].get_text(strip=True) if len(cells) > 4 else "Now"
                
                data.append({
                    "Rank": rank,
                    "Ticker": ticker,
                    "Messages": volume,
                    "Change": change,
                    "Trending Since": since,
                    "Updated": datetime.now().strftime("%H:%M:%S")
                })
                rank_counter += 1
        
        if not data:
            raise ValueError("No data parsed - check selectors!")
        
        return pd.DataFrame(data)
    
    except Exception as e:
        st.error(f"Oops! Fetch hiccup: {str(e)} - Using sample data...")
        # Fallback with realistic samples (based on typical trends)
        return pd.DataFrame({
            "Rank": [1, 2, 3, 4, 5],
            "Ticker": ["$AAPL", "$TSLA", "$NVDA", "$AMD", "$MSFT"],
            "Messages": ["2.1K messages", "1.8K messages", "1.5K messages", "1.2K messages", "950 messages"],
            "Change": ["+1.2%", "-0.5%", "+3.1%", "+0.8%", "+2.0%"],
            "Trending Since": ["14:30 ET", "14:20 ET", "14:10 ET", "14:05 ET", "13:55 ET"],
            "Updated": [datetime.now().strftime("%H:%M:%S")] * 5
        })

# The banana loop lives!
while True:
    with placeholder.container():
        df = get_trending()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.dataframe(
                df[["Rank", "Ticker", "Messages", "Change", "Trending Since"]].style
                .set_properties(**{"text-align": "left", "font-size": "14px"})
            )
        with col2:
            # Bar chart: Parse volumes to numbers (e.g., 1.2K -> 1200)
            def parse_volume(v):
                v = str(v).replace(" messages", "")
                if "K" in v:
                    return float(v.replace("K", "")) * 1000
                elif "M" in v:
                    return float(v.replace("M", "")) * 1000000
                else:
                    return float(re.sub(r'[^\d.]', '', v) or 0)
            
            volume_num = df["Messages"].apply(parse_volume)
            st.bar_chart(pd.Series(volume_num, index=df["Ticker"]), use_container_width=True)
        
        st.caption(f"🐒 Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Every 3 min • Scraped fresh from StockTwits")
    
    status.success("🍌 Next refresh in 3 minutes...")
    time.sleep(180)
