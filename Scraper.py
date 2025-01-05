import requests
import pandas as pd
from bs4 import BeautifulSoup
import yfinance as yf
import ta
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockScraper:
    """
    Scrapes stock-related data from web sources.
    """

    def __init__(self, company, exchange="NSE"):
        """
        Initialize the scraper with a company symbol and exchange.
        """
        self.stock = company.upper()
        self.exchange = exchange.upper()

    def table_to_json(self, table):
        """
        Convert an HTML table to a JSON format using pandas.

        :param table: BeautifulSoup table element.
        :return: JSON string.
        """
        headers = [th.text.strip() for th in table.find_all('th')]
        rows = table.find_all('tr')[1:]

        data = [
            {headers[i + 1]: td.text.strip() for i, td in enumerate(row.find_all('td')[1:])}
            for row in rows
        ]
        index = [row.find('td').text.strip() for row in rows]
        df = pd.DataFrame(data, index=index)
        return df.to_json(orient='index')

    def technical_analysis(self):
        """
        Perform technical analysis for a 3-month holding period.
        """
        tick = f"{self.stock}.NS"
        df = yf.download(tick, period="1y", interval="1d")

        if df.empty:
            logger.error("Data fetch failed for ticker: %s", tick)
            return "Data fetch failed. Check the stock symbol."

        signals = []

        # Simple Moving Averages
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_100'] = df['Close'].rolling(window=100).mean()
        signals.append(1 if df['SMA_50'].iloc[-1] > df['SMA_100'].iloc[-1] else -1)

        # Relative Strength Index
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        if df['RSI'].iloc[-1] > 70:
            signals.append(-1)
        elif df['RSI'].iloc[-1] < 30:
            signals.append(1)
        else:
            signals.append(0)

        # MACD
        macd = ta.trend.MACD(df['Close'])
        df['MACD_line'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        signals.append(1 if df['MACD_line'].iloc[-1] > df['MACD_signal'].iloc[-1] else -1)

        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_upper'] = bb.bollinger_hband()
        df['BB_lower'] = bb.bollinger_lband()
        if df['Close'].iloc[-1] < df['BB_lower'].iloc[-1]:
            signals.append(1)
        elif df['Close'].iloc[-1] > df['BB_upper'].iloc[-1]:
            signals.append(-1)
        else:
            signals.append(0)

        # Exponential Moving Averages
        df['EMA_20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
        df['EMA_50'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
        signals.append(1 if df['EMA_20'].iloc[-1] > df['EMA_50'].iloc[-1] else -1)

        # Weighted Voting
        weights = [0.3, 0.2, 0.2, 0.2, 0.1]
        weighted_signals = sum(s * w for s, w in zip(signals, weights))

        if weighted_signals > 0.5:
            return "Buy"
        elif weighted_signals < -0.5:
            return "Sell"
        return "Hold"

    def get_stock_news(self):
        """
        Fetch latest news from Google Finance.

        :return: Dictionary of news with timestamps or error message.
        """
        url = f"https://www.google.com/finance/quote/{self.stock}:{self.exchange}?hl=en"
        logger.info("Fetching news from %s", url)

        try:
            response = requests.get(url)
            response.raise_for_status()
            logger.info("News fetched successfully.")
        except requests.RequestException as e:
            logger.error("Error fetching news: %s", e)
            return {"error": str(e)}

        page = BeautifulSoup(response.content, "html.parser")
        news_items = page.find_all("div", class_="Yfwt5")
        times = page.find_all("div", class_="Adak")

        news = {
            times[i].text if i < len(times) else "Unknown Time": [item.text.strip()]
            for i, item in enumerate(news_items)
        }

        return news

    def get_stock_properties(self):
        """
        Scrape stock properties from Screener.in.

        :return: Dictionary of stock data or error message.
        """
        url = f'https://www.screener.in/company/{self.stock}'
        logger.info("Fetching stock properties from %s", url)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error fetching stock properties: %s", e)
            return {"error": str(e)}

        page = BeautifulSoup(response.content, 'html.parser')

        try:
            stock_name = page.find('h1', class_='h2 shrink-text').text.strip()
        except AttributeError:
            logger.error("Stock name not found.")
            return {"error": "Stock name not found."}

        stock_info = page.find('div', class_='flex flex-align-center')
        stock_price, stock_change = ("", "")
        if stock_info and stock_info.find_all('span'):
            spans = stock_info.find_all('span')
            stock_price, stock_change = spans[0].text.strip(), spans[1].text.strip()

        about = page.find('div', class_='sub show-more-box about')
        key = page.find('div', class_='sub commentary always-show-more-box')
        about_text = about.text.strip() if about else ""
        key_text = key.text.strip() if key else ""

        props = {
            pt.find('span', class_='name').text.strip(): pt.find('span', class_='nowrap value').text.strip().replace('\n        ', '')
            for pt in page.find_all('li', class_='flex flex-space-between')
            if pt.find('span', class_='name') and pt.find('span', class_='nowrap value')
        }

        pros = page.find('div', class_='pros')
        cons = page.find('div', class_='cons')
        sector = page.find('div', class_='sub')

        pros_text = pros.text.strip() if pros else ""
        cons_text = cons.text.strip() if cons else ""
        sector_text = sector.text.strip() if sector else ""

        tables = page.find_all('table', class_='data-table responsive-text-nowrap')
        financial_data = {
            "quarterly_results": self.table_to_json(tables[0]) if len(tables) > 0 else "",
            "profit_and_loss": self.table_to_json(tables[1]) if len(tables) > 1 else "",
            "balance_sheet": self.table_to_json(tables[2]) if len(tables) > 2 else "",
            "cash_flow": self.table_to_json(tables[3]) if len(tables) > 3 else "",
            "debtors_ratio": self.table_to_json(tables[4]) if len(tables) > 4 else "",
        }

        shareholding_table = page.find('table', class_='data-table')
        shareholding = self.table_to_json(shareholding_table) if shareholding_table else ""

        data = {
            "stock_name": stock_name,
            "stock_price": stock_price,
            "stock_change": stock_change,
            "news": self.get_stock_news(),
            "about": about_text,
            "key": key_text,
            "properties": props,
            "pros": pros_text,
            "cons": cons_text,
            "sector": sector_text,
            **financial_data,
            "shareholding_pattern": shareholding,
            "technical_analysis": self.technical_analysis()
        }

        return data

# Example usage
# scraper = StockScraper("HDFCBANK")
# print(scraper.get_stock_news())
# print(scraper.technical_analysis())
# print(scraper.get_stock_properties())