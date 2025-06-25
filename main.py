# main.py

import streamlit as st
import requests
from textblob import TextBlob
from dataclasses import dataclass, field
from typing import List, Literal

# ----🔐 API KEYS ----
NEWS_API_KEY = "1947c97709734759b81277ccb7ee8152"
HUGGINGFACE_API_KEY = st.secrets["HUGGINGFACE_API_KEY"]

# ----📌 Type Definitions ----
Sentiment = Literal["positive", "negative", "neutral"]
Impact = Literal["high", "medium", "low"]
Category = Literal["portfolio", "watchlist"]

@dataclass
class NewsItem:
    title: str
    content: str
    translated: str
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

# ----🧠 Sentiment Analysis ----
def analyze_sentiment(text: str) -> Sentiment:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.2:
        return "positive"
    elif polarity < -0.2:
        return "negative"
    else:
        return "neutral"

# ----🌐 Translation via HuggingFace API ----
def translate_to_thai(text: str) -> str:
    if not text.strip():
        return ""
    try:
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"inputs": text}
        response = requests.post(
            "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-en-th",
            headers=headers,
            json=payload
        )
        result = response.json()
        return result[0]["translation_text"] if isinstance(result, list) else "⚠️ แปลไม่ได้"
    except Exception:
        return "⚠️ แปลไม่ได้"

# ----📰 Fetch News ----
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
        translated = translate_to_thai(content)
        news_items.append(NewsItem(
            title=article["title"],
            content=content,
            translated=translated,
            sentiment=sentiment,
            impact="medium",
            url=article["url"],
            published_at=article["publishedAt"]
        ))
    return news_items

# ----📊 Stocks to Track ----
stocks: List[Stock] = [
    Stock(ticker="AAPL", name="Apple Inc.", category="portfolio"),
    Stock(ticker="TSLA", name="Tesla Inc.", category="watchlist"),
    Stock(ticker="NVDA", name="NVIDIA Corporation", category="watchlist"),
    Stock(ticker="MSFT", name="Microsoft Corp.", category="portfolio"),
]

# ----🖥️ Streamlit UI ----
st.set_page_config(page_title="📈 Vibe Stock Dashboard", layout="wide")
st.title("📈 Vibe Stock Tracker Dashboard")

category_filter = st.radio("เลือกหมวดหมู่หุ้น", ["portfolio", "watchlist"])

filtered_stocks = [s for s in stocks if s.category == category_filter]

for stock in filtered_stocks:
    with st.expander(f"{stock.name} ({stock.ticker})"):
        if not stock.news:
            stock.news = fetch_news(stock.ticker)

        positive_news = [n for n in stock.news if n.sentiment == "positive"]
        negative_news = [n for n in stock.news if n.sentiment == "negative"]

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🟢 ข่าวเชิงบวก")
            for news in positive_news:
                st.markdown(f"**{news.title}**")
                st.caption(f"*{news.published_at}*")
                st.write(news.translated)
                st.markdown(f"[🔗 อ่านต่อ]({news.url})")
                st.markdown("---")

        with col2:
            st.subheader("🔴 ข่าวเชิงลบ")
            for news in negative_news:
                st.markdown(f"**{news.title}**")
                st.caption(f"*{news.published_at}*")
                st.write(news.translated)
                st.markdown(f"[🔗 อ่านต่อ]({news.url})")
                st.markdown("---")
