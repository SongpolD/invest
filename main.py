# main.py

# ─────────────────────────────────────────────
# 📦 Import libraries
import streamlit as st                    # สำหรับสร้าง dashboard UI
import requests                           # สำหรับเรียก API ดึงข่าว
from textblob import TextBlob            # สำหรับวิเคราะห์ sentiment
from dataclasses import dataclass, field # สำหรับสร้าง class data แบบอัตโนมัติ
from typing import List, Literal          # สำหรับกำหนดประเภทข้อมูล

from transformers import pipeline         # HuggingFace summarizer
from googletrans import Translator        # ใช้แปลภาษา (ฟรี)

# ─────────────────────────────────────────────
# 📌 Define custom data types

# ค่าที่สามารถเป็นได้ของแต่ละประเภท
Sentiment = Literal["positive", "negative", "neutral"]
Impact = Literal["high", "medium", "low"]
Category = Literal["portfolio", "watchlist"]

# ข้อมูลข่าว 1 ชิ้น
@dataclass
class NewsItem:
    title: str
    content: str
    sentiment: Sentiment
    impact: Impact
    url: str
    published_at: str
    summary_en: str = ""
    summary_th: str = ""

# ข้อมูลหุ้น 1 ตัว
@dataclass
class Stock:
    ticker: str
    name: str
    category: Category
    news: List[NewsItem] = field(default_factory=list)

# ─────────────────────────────────────────────
# 🧠 Load AI models

# ใช้โมเดล HuggingFace สำหรับสรุปข่าว (ภาษาอังกฤษ)
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# ใช้ Google Translate (ฟรี) สำหรับแปลอังกฤษ → ไทย
translator = Translator()

# ─────────────────────────────────────────────
# 💬 วิเคราะห์อารมณ์ข่าว (sentiment)

def analyze_sentiment(text: str) -> Sentiment:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.2:
        return "positive"
    elif polarity < -0.2:
        return "negative"
    else:
        return "neutral"

# ─────────────────────────────────────────────
# ✂️ สรุปข่าวเป็นข้อความสั้น

def summarize_text(text: str) -> str:
    try:
        summary = summarizer(text, max_length=60, min_length=25, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        return "⚠️ สรุปไม่ได้: " + str(e)

# ─────────────────────────────────────────────
# 🌐 แปลสรุปข่าวเป็นภาษาไทย

def translate_to_thai(text: str) -> str:
    try:
        result = translator.translate(text, dest='th')
        return result.text
    except Exception as e:
        return "⚠️ แปลไม่ได้: " + str(e)

# ─────────────────────────────────────────────
# 📰 ดึงข่าวจาก NewsAPI

def fetch_news(ticker: str) -> List[NewsItem]:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": ticker,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": "1947c97709734759b81277ccb7ee8152",  # 👈 ใช้ API Key ของคุณ
        "pageSize": 3,
    }

    response = requests.get(url, params=params)
    articles = response.json().get("articles", [])

    news_items = []
    for article in articles:
        content = article.get("description") or ""
        sentiment = analyze_sentiment(content)
        summary_en = summarize_text(content)
        summary_th = translate_to_thai(summary_en)

        news_items.append(NewsItem(
            title=article["title"],
            content=content,
            sentiment=sentiment,
            impact="medium",  # คุณสามารถปรับ logic การวัด impact เพิ่มภายหลังได้
            url=article["url"],
            published_at=article["publishedAt"],
            summary_en=summary_en,
            summary_th=summary_th
        ))
    return news_items

# ─────────────────────────────────────────────
# 📊 รายชื่อหุ้นของคุณ

stocks: List[Stock] = [
    Stock(ticker="AAPL", name="Apple Inc.", category="portfolio"),
    Stock(ticker="TSLA", name="Tesla Inc.", category="watchlist"),
    Stock(ticker="NVDA", name="NVIDIA Corporation", category="watchlist"),
    Stock(ticker="MSFT", name="Microsoft Corp.", category="portfolio"),
]

# ─────────────────────────────────────────────
# 🖥️ สร้างหน้า UI ด้วย Streamlit

st.set_page_config(page_title="📈 Vibe Stock Dashboard", layout="wide")
st.title("📈 Vibe Stock Tracker Dashboard")

# ให้ผู้ใช้เลือกหมวดหมู่หุ้น (watchlist / portfolio)
category_filter = st.radio("เลือกกลุ่มหุ้น", ["portfolio", "watchlist"])

filtered_stocks = [s for s in stocks if s.category == category_filter]

# แสดงผลข่าวของหุ้นแต่ละตัว
for stock in filtered_stocks:
    with st.expander(f"{stock.name} ({stock.ticker})"):
        if not stock.news:
            stock.news = fetch_news(stock.ticker)

        # แบ่ง layout ซ้าย = ข่าวดี / ขวา = ข่าวร้าย
        col1, col2 = st.columns(2)

        for news in stock.news:
            block = col1 if news.sentiment == "positive" else col2
            with block:
                st.markdown(f"**📰 {news.title}**")
                st.caption(f"*{news.published_at}*")
                st.write(news.summary_th)  # แสดงข่าวที่แปลไทยแล้ว
                st.markdown(f"[🔗 อ่านต่อ]({news.url})")
                st.markdown("---")
