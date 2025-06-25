# main.py

import requests
from dataclasses import dataclass, field
from typing import List, Literal
import datetime

# ตั้งค่า API KEY ที่นี่
NEWS_API_KEY = "1947c97709734759b81277ccb7ee8152"  # 🔐 เปลี่ยนตรงนี้เป็น API KEY ของคุณ

# ประเภทข้อมูล
Sentiment = Literal["positive", "negative", "neutral"]
Impact = Literal["high", "medium", "low"]
Category = Literal["portfolio", "watchlist"]

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

def fetch_real_news(ticker: str) -> List[NewsItem]:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": ticker,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY,
        "pageSize": 5,
    }
    response = requests.get(url, params=params)
    articles = response.json().get("articles", [])
    
    news_items = []
    for article in articles:
        news_items.append(NewsItem(
            title=article["title"],
            content=article.get("description") or "",
            sentiment="neutral",  # ยังไม่วิเคราะห์จริงในขั้นนี้
            impact="medium",
            url=article["url"],
            published_at=article["publishedAt"]
        ))
    return news_items

stocks: List[Stock] = [
    Stock(ticker="AAPL", name="Apple Inc.", category="portfolio"),
    Stock(ticker="TSLA", name="Tesla Inc.", category="watchlist"),
]

for stock in stocks:
    stock.news = fetch_real_news(stock.ticker)

def display_summary(stock: Stock):
    print(f"\n[{stock.category.upper()}] {stock.name} ({stock.ticker})")
    for news in stock.news:
        print(f"- {news.title} [{news.sentiment}, {news.impact}]")
        print(f"  {news.url}")

for stock in stocks:
    display_summary(stock)
