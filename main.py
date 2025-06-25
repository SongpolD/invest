# main.py

from dataclasses import dataclass, field
from typing import List, Literal
import datetime

# Type definitions
Sentiment = Literal["positive", "negative", "neutral"]
Impact = Literal["high", "medium", "low"]
Category = Literal["portfolio", "watchlist"]

# Data classes
@dataclass
class NewsItem:
    title: str
    content: str
    sentiment: Sentiment
    impact: Impact
    url: str
    published_at: str

@dataclass
class Stock:
    ticker: str
    name: str
    category: Category
    news: List[NewsItem] = field(default_factory=list)
    prediction: str = ""

# Mock function to simulate news fetching
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

# Portfolio and Watchlist
stocks: List[Stock] = [
    Stock(ticker="AAPL", name="Apple Inc.", category="portfolio"),
    Stock(ticker="TSLA", name="Tesla Inc.", category="watchlist"),
]

# Fetch news and update stocks
for stock in stocks:
    stock.news = fetch_mock_news(stock.ticker)

# Output summary
def display_summary(stock: Stock):
    print(f"\n[{stock.category.upper()}] {stock.name} ({stock.ticker})")
    for news in stock.news:
        print(f"- {news.title} [{news.sentiment}, {news.impact}]")
        print(f"  {news.url}")

for stock in stocks:
    display_summary(stock)
