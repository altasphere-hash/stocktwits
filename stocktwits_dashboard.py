# stocktwits_dashboard.py - Pure Python HTML Parsing (No bs4 Needed!)
import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import re

st.set_page_config(page_title="StockTwits Trending", layout="wide")
st.title("🔥 StockTwits Trending Stocks - Live Auto-Refresh (Pure Python Edition)")

placeholder = st.empty()
status = st.empty()

@st.cache_data(ttl=180)  # Cache 3 min
def get_trending():
    url = "https://stocktwits.com/rankings/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
        
        # Pure Python parsing: Find the table HTML
        table_match = re.search(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        if not table_match:
            raise ValueError("No table found - page structure changed?")
        
        table_html = table_match.group(1)
        
        # Split into rows using <tr> tags
        rows = re.split(r'<tr[^>]*>', table_html)
        data_rows = [row for row in rows if '<td' in row or '<th' in row][:21]  # Header + top 20
        
        data = []
        rank_counter = 1
        
        for row in data_rows[1:]:  # Skip header
            # Extract cells from <td> or <th>
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
            clean_cells = [re.sub(r'<[^>]*>', '', cell).strip() for cell in cells]
            
            if len(clean_cells) >= 4:
                # Rank
                rank = clean_cells[0] if clean_cells[0].isdigit() else str(rank_counter)
                
                # Ticker: Extract $SYMBOL from text or href
                ticker_text = ' '.join(clean_cells[1:2])
                ticker_match = re.search(r'\$([A-Z]{1,5})', ticker_text)
                ticker = f"${ticker_match.group(1)}" if ticker_match else "N/A"
                
                # Messages volume
                volume_match = re.search(r'([\d.]+[KMB]?)\s*messages?', ' '.join(clean_cells[2:3]))
                volume = volume_match.group(1) + " messages" if volume_match else "N/A"
                
                # Change: e.g., +2.5%
                change_match = re.search(r'([+-]?\d+\.?\d*)%', ' '.join(clean_cells[3:4]))
                change = change_match.group(1) + "%" if change_match else "N/A"
                
                # Trending Since: Last cell or "Now"
                since = clean_cells[-1] if len(clean_cells) > 4 else "Now"
                
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
            raise ValueError("No data extracted - selectors need tweak?")
        
        return pd.DataFrame(data)
    
    except Exception as e:
        st.error(f"Fetch oops: {str(e)} - Sample mode activated...")
        # Sample data for unbreakable dashboard
        return pd.DataFrame({
            "Rank": range(1, 11),
            "Ticker": ["$AAPL", "$TSLA", "$NVDA", "$AMD", "$MSFT", "$GOOGL", "$META", "$AMZN", "$NFLX", "$CRM"],
            "Messages": ["2.5K messages", "2.1K messages", "1.9K messages", "1.6K messages", "1.4K messages",
                         "1.2K messages", "1.1K messages", "1.0K messages", "950 messages", "850 messages"],
            "Change": ["+1.8%", "+0.5%", "+2.2%", "-0.3%", "+1.1%", "+0.9%", "-1.5%", "+3.0%", "+0.7%", "-0.2%"],
            "Trending Since": ["15:10 ET", "15:05 ET", "15:00 ET", "14:55 ET", "14:50 ET",
                               "14:45 ET", "14:40 ET", "14:35 ET", "14:30 ET", "14:25 ET"],
            "Updated": [datetime.now().strftime("%H:%M:%S")] * 10
        })

# Loop de banana
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
            # Parse volume for chart (1.2K -> 1200)
            def parse_vol(v):
                v = re.sub(r'\s*messages', '', str(v))
                mult = 1
                if 'K' in v: mult, v = 1000, re.sub(r'K', '', v)
                elif 'M' in v: mult, v = 1000000, re.sub(r'M', '', v)
                return float(re.sub(r'[^\d.]', '', v)) * mult
            
            vol_num = df["Messages"].apply(parse_vol)
            st.bar_chart(pd.Series(vol_num, index=df["Ticker"]), use_container_width=True)
        
        st.caption(f"🐒 Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Every 3 min • Pure Python Power!")
    
    status.success("🍌 Chill—next update in 3 min...")
    time.sleep(180)
