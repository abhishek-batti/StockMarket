import yfinance as yf
import requests
# from langchain_core.tools import tool
# from langchain_google_genai import ChatGoogleGenerativeAI



def fetch_stock_price(symbol: str = "^NSEI") -> str:
    """Fetch stock price history for the past month and return as a CSV string"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="60d", interval = "5m")
        if hist.empty:
            return f"No data found for symbol: {symbol}"
        print(hist.head())
        hist_csv = hist.to_csv()
        return hist_csv
    
    except Exception as e:
        return f"Error fetching data for {symbol}: {e}"

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
    return None

def get_company_data(company_name: str):
    ticker = get_ticker_by_name(company_name)
    if ticker is None:
        return None
    stock_data = fetch_stock_price(ticker) 
    return stock_data

