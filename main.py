# main.py

import streamlit as st
import requests
from textblob import TextBlob
from dataclasses import dataclass, field
from typing import List, Literal
from transformers import pipeline

# 🔑 ใส่ NewsAPI key ของคุณ
NEWS_API_KEY = "1947c97709734759b81277ccb7ee8152"

# 🧠 โหลดโมเดลแปลภาษาจาก HuggingFace
translator = pipeline("translation", model="Helsinki-NLP/opus-mt-en-th")

# 📦 ประเภทข้อมูล
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
    translated_summary: str = ""

@dataclass
class Stock:
    ticker: str
    name: str
    category: Category
    news: List[NewsItem] = field(default_factory=list)

# 💬 วิเคราะห์ความรู้สึก
def analyze_sentiment(text: str) -> Sentiment:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.2:
        return "positive"
    elif polarity < -0.2:
        return "negative"
    else:
        return "neutral"

# 🌐 แปลข้อความเป็นภาษาไทย
def translate_to_thai(text: str) -> str:
    try:
        if not text.strip():
            return ""
        translated = translator(text, max_length=200)[0]["translation_text"]
        return translated
    except Exception as e:
        return "⚠️ แปลไม่ได้"

# 📰 ดึงข่าว
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
        summary = translate_to_thai(content)

        news_items.append(NewsItem(
            title=article["title"],
            content=content,
            sentiment=sentiment,
            impact="medium",
            url=article["url"],
            published_at=article["publishedAt"],
            translated_summary=summary
        ))
    return news_items

# 📈 รายชื่อหุ้น
stocks: List[Stock] = [
    Stock(ticker="AAPL", name="Apple Inc.", category="portfolio"),
    Stock(ticker="TSLA", name="Tesla Inc.", category="watchlist"),
    Stock(ticker="NVDA", name="NVIDIA Corporation", category="watchlist"),
    Stock(ticker="MSFT", name="Microsoft Corp.", category="portfolio"),
]

# 🖼️ Streamlit UI
st.set_page_config(page_title="📈 Vibe Stock Dashboard", layout="wide")
st.title("📊 Vibe Stock Tracker Dashboard")

category_filter = st.radio("เลือกประเภทหุ้น", ["portfolio", "watchlist"])
filtered_stocks = [s for s in stocks if s.category == category_filter]

for stock in filtered_stocks:
    with st.expander(f"{stock.name} ({stock.ticker})"):
        if not stock.news:
            stock.news = fetch_news(stock.ticker)

        # 📤 แยกซ้าย-ขวา: ข่าวดี/ร้าย
        col1, col2 = st.columns(2)

        for news in stock.news:
            block = col1 if news.sentiment == "positive" else col2
            sentiment_color = {
                "positive": "🟢",
                "negative": "🔴",
                "neutral": "🟡"
            }.get(news.sentiment, "⚪")

            with block:
                st.markdown(f"**{sentiment_color} {news.title}**")
                st.caption(f"*{news.published_at}*")
                st.markdown(f"**🗣️ แปล:** {news.translated_summary}")
                st.markdown(f"[🔗 อ่านข่าวต้นฉบับ]({news.url})")
                st.markdown("---")
