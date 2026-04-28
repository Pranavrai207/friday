import yfinance as yf
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests
import re
from gnews import GNews

# Load environment variables
load_dotenv()

STOCKS = ["AAPL", "MSFT", "NVDA", "TSLA", "SPY"]
GROQ_API_KEY = os.getenv("GroqAPIKey")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

def fetch_market_data():
    print("Fetching real-time data from Finnhub & yfinance...")
    data = {}
    try:
        for ticker in STOCKS:
            # 1. Get History from yfinance (for charts)
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            # 2. Get Live Quote from Finnhub (for absolute accuracy)
            quote_resp = requests.get(f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_KEY}")
            quote = quote_resp.json()
            
            data[ticker] = {
                "history": hist['Close'].tolist(),
                "latest_price": quote.get('c', hist['Close'].iloc[-1]),
                "change_pct": quote.get('dp', ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100)
            }
        
        # Calculate Market Trend based on SPY
        spy_change = data["SPY"]["change_pct"]
        market_trend = "BULLISH" if spy_change > 0.1 else "BEARISH" if spy_change < -0.1 else "NEUTRAL"
        
        return data, market_trend
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return None, None

def fetch_latest_news():
    print("Fetching high-impact macro drivers (Geopolitics & AI)...")
    news_headlines = []
    try:
        gn = GNews(language="en", max_results=5)
        # Focus on top drivers
        combined = gn.get_news("US stock market drivers geopolitics AI")
        
        for item in combined:
            title = item.get("title", "").rsplit(" - ", 1)[0].strip()
            news_headlines.append({
                "ticker": "MACRO",
                "title": title,
                "link": item.get("url"),
                "publisher": item.get("publisher", {}).get("title") or "GNEWS"
            })
        return news_headlines
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

def get_live_pulses(market_data, news, trend):
    """Generates factual pulse points based on raw data, NO LLM used."""
    pulses = []
    spy_chg = market_data['SPY']['change_pct']
    dir_str = "GAIN" if spy_chg > 0 else "LOSS"
    pulses.append(f"MARKET PULSE: S&P 500 exhibiting {trend} momentum with a {abs(spy_chg):.2f}% {dir_str}.")
    
    nvda_chg = market_data['NVDA']['change_pct']
    pulses.append(f"TECH ALERT: NVDA at ${market_data['NVDA']['latest_price']:.2f} ({nvda_chg:+.2f}%).")
    
    if news:
        for i, h in enumerate(news[:2]):
            pulses.append(f"INTEL {i+1}: {h['title'].upper()}")
    return pulses

def get_multiple_video_ids():
    queries = ["Bloomberg Live News", "CNBC Live News", "Yahoo Finance Live", "Market Intel News"]
    video_ids = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for q in queries:
        try:
            url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
            resp = requests.get(url, headers=headers, timeout=5)
            ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", resp.text)
            if ids: video_ids.append(ids[0])
        except: pass
    return video_ids

def main():
    market_data, trend = fetch_market_data()
    news = fetch_latest_news()
    if market_data:
        pulses = get_live_pulses(market_data, news, trend)
        video_ids = get_multiple_video_ids()
        final_data = {
            "timestamp": datetime.now().isoformat(),
            "market_trend": trend,
            "pulses": pulses,
            "stocks": market_data,
            "news": news,
            "video_ids": video_ids,
            "finnhub_key": FINNHUB_KEY
        }
        output_path = os.path.join("Frontend", "market_data.json")
        with open(output_path, "w") as f:
            json.dump(final_data, f, indent=4)
        print(f"Successfully saved market data to {output_path}")

if __name__ == "__main__":
    main()
