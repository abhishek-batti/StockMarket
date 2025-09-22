import yfinance as yf
import requests
from langchain_core.tools import tool

@tool
def fetch_stock_price(symbol: str = "^NSEI") -> str:
    """Fetch stock price history for the past month."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        if hist.empty:
            return f"No data found for symbol: {symbol}"
        
        hist_csv = hist.to_csv(index = False)
        return hist_csv.to_string()
    
    except Exception as e:
        return f"Error fetching data for {symbol}: {e}"

@tool
def get_ticker_by_name(name: str) -> str:
    """Fetch ticker symbol from Yahoo Finance search API."""
    query = "+".join(name.lower().split())
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()
    except Exception as e:
        return f"Error fetching ticker: {e}"

    if "quotes" in data and len(data["quotes"]) > 0:
        return data["quotes"][0]["symbol"]
    return f"No ticker found for {name}."

@tool 