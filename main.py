# main.py

import requests
from dataclasses import dataclass, field
from typing import List, Literal
from textblob import TextBlob
import datetime

# 🔐 ใส่ API KEY ของคุณจาก NewsAPI.org
NEWS_API_KEY = "1947c97709734759b81277ccb7ee8152"

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

def analyze_sentiment(text: str) -> Sentiment:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # ค่าระหว่าง -1.0 ถึง +1.0
    if polarity > 0.2:
        return "positive"
    elif polarity < -0.2:
        return "negative"
    else:
        return "neutral"

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
        content = article.get("description") or ""
        sentiment = analyze_sentiment(content)
        news_items.append(NewsItem(
            title=article["title"],
            content=content,
            sentiment=sentiment,
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
        print(f"- {news.title} [{news.sentiment}]")
        print(f"  {news.url}")

for stock in stocks:
    display_summary(stock)
