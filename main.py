# main.py

from dataclasses import dataclass, field
from typing import List, Literal
import datetime

# ประเภทข้อมูลที่ใช้
Sentiment = Literal["positive", "negative", "neutral"]
Impact = Literal["high", "medium", "low"]
Category = Literal["portfolio", "watchlist"]

# โครงสร้างข่าว
@dataclass
class NewsItem:
    title: str
    content: str
    sentiment: Sentiment
    impact: Impact
    url: str
    published_at: str

# โครงสร้างหุ้น
@dataclass
class Stock:
    ticker: str
    name: str
    category: Category
    news: List[NewsItem] = field(default_factory=list)
    prediction: str = ""

# จำลองการดึงข่าว (mock)
def fetch_mock_news(ticker: str) -> List[NewsItem]:
    return [
        NewsItem(
            title=f"Positive outlook for {ticker}",
            content="Analysts are bullish on the stock.",
            sentiment="positive",
            impact="medium",
            url="https://example.com/news1",
            published_at=str(datetime.datetime.now())
        ),
        NewsItem(
            title=f"Concerns about {ticker}'s supply chain",
            content="There are reports of delays.",
            sentiment="negative",
            impact="high",
            url="https://example.com/news2",
            published_at=str(datetime.datetime.now())
        )
    ]

# หุ้นใน watchlist และ portfolio
stocks: List[Stock] = [
    Stock(ticker="AAPL", name="Apple Inc.", category="portfolio"),
    Stock(ticker="TSLA", name="Tesla Inc.", category="watchlist"),
]

# ดึงข่าวใส่แต่ละหุ้น
for stock in stocks:
    stock.news = fetch_mock_news(stock.ticker)

# แสดงผลสรุป
def display_summary(stock: Stock):
    print(f"\n[{stock.category.upper()}] {stock.name} ({stock.ticker})")
    for news in stock.news:
        print(f"- {news.title} [{news.sentiment}, {news.impact}]")
        print(f"  {news.url}")

for stock in stocks:
    display_summary(stock)
