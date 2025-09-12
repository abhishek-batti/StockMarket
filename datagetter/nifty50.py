import requests

def get_ticker_by_name(name):
    """
    Fetches the stock ticker symbol for a given company name using Yahoo Finance's search API.
    Args:
        name (str): The name of the company.
    Returns:
        str: The stock ticker symbol if found, else None.
    """
    query = "+".join(name.lower().split())
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()
    except Exception as e:
        print("Error fetching data:", e)
        return None

    if "quotes" in data and len(data["quotes"]) > 0:
        return data["quotes"][0]["symbol"]
    return None


