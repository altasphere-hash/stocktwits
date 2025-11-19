# stocktwits_dashboard.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

st.set_page_config(page_title="StockTwits Trending", layout="wide")
st.title("🔥 StockTwits Trending Stocks - Live Auto-Refresh")

placeholder = st.empty()
status = st.empty()

@st.cache_data(ttl=180)  # Cache for 3 minutes to save juice
def get_trending():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://stocktwits.com/rankings/trending")
        time.sleep(6)  # Let the page load like a sleepy sloth
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("table tr")[1:21]  # Grab top 20 bananas
        
        data = []
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 5:
                rank = cols[0].get_text(strip=True)
                ticker_link = cols[1].find("a")
                ticker = ticker_link.get_text(strip=True).replace("$", "") if ticker_link else "N/A"
                volume = cols[2].get_text(strip=True)
                change = cols[3].get_text(strip=True)
                since = cols[4].get_text(strip=True)
                
                data.append({
                    "Rank": rank,
                    "Ticker": ticker,
                    "Messages": volume,
                    "Change": change,
                    "Trending Since": since,
                    "Updated": datetime.now().strftime("%H:%M:%S")
                })
        
        return pd.DataFrame(data)
    
    finally:
        driver.quit()

# The endless banana loop
while True:
    with placeholder.container():
        df = get_trending()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.dataframe(df[["Rank", "Ticker", "Messages", "Change", "Trending Since"]].style.set_properties(**{'text-align': 'left'}))
        with col2:
            # Quick bar chart of message volume (magic numbers to make it graph-y)
            volume_numeric = pd.to_numeric(df["Messages"].str.replace(r'[KMB]', lambda m: {'K': 'e3', 'M': 'e6', 'B': 'e9'}[m.group()], regex=True), errors='coerce')
            st.bar_chart(pd.Series(volume_numeric, index=df["Ticker"]))
        
        st.caption(f"🐒 Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Refreshes every 3 minutes • Eat a banana!")
    
    status.success("🍌 Next refresh in 3 minutes...")
    time.sleep(180)  # 3-minute nap