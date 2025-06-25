# main.py

import streamlit as st
import requests
from textblob import TextBlob
from dataclasses import dataclass, field
from typing import List, Literal

# ตั้งค่า NewsAPI Key
NEWS_API_KEY = "1947c97709734759b81277ccb7ee8152"  # ← ใส่ API key ของคุณตรงนี้

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

def analyze_sentiment(text: str) -> Sentiment:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.2:
        return "positive"
    elif polarity < -0.2:
        return "negative"
    else:
        return "neutral"

def fetch_news(ticker: str) -> List[NewsItem]:
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

# รายชื่อหุ้น
stocks: List[Stock] = [
    Stock(ticker="AAPL", name="Apple Inc.", category="portfolio"),
    Stock(ticker="TSLA", name="Tesla Inc.", category="watchlist"),
    Stock(ticker="NVDA", name="NVIDIA Corporation", category="watchlist"),
    Stock(ticker="MSFT", name="Microsoft Corp.", category="portfolio"),
]

# Streamlit UI
st.set_page_config(page_title="📈 Vibe Stock Dashboard", layout="wide")
st.title("📈 Vibe Stock Tracker Dashboard")

category_filter = st.radio("Choose stock category", ["portfolio", "watchlist"])

filtered_stocks = [s for s in stocks if s.category == category_filter]

for stock in filtered_stocks:
    with st.expander(f"{stock.name} ({stock.ticker})"):
        if not stock.news:
            stock.news = fetch_news(stock.ticker)

        for news in stock.news:
            sentiment_color = {
                "positive": "🟢",
                "negative": "🔴",
                "neutral": "🟡"
            }.get(news.sentiment, "⚪")

            st.markdown(f"**{sentiment_color} {news.title}**")
            st.caption(f"*{news.published_at}*")
            st.write(news.content)
            st.markdown(f"[🔗 Read more]({news.url})")
            st.markdown("---")
