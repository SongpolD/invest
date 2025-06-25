# main.py

import streamlit as st
import openai
import requests
from typing import List, Literal
from dataclasses import dataclass, field

# ✅ โหลด API Key จาก secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🧠 ประเภทข้อมูล
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

# ✅ วิเคราะห์ sentiment และแปลข่าว ด้วย OpenAI
def analyze_and_translate(content: str) -> tuple[str, Sentiment]:
    prompt = f"""
ข่าว: {content}

1. แปลข่าวด้านบนเป็นภาษาไทยโดยสรุปให้สั้น ชัดเจน
2. วิเคราะห์ว่าเนื้อหามีอารมณ์แบบใด: positive, negative หรือ neutral

รูปแบบผลลัพธ์ที่ต้องการ:
แปลไทย: <แปลข่าว>
อารมณ์: <positive/negative/neutral>
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # หรือ "gpt-4" ถ้ามีสิทธิ์ใช้งาน
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        result = response.choices[0].message.content
        translated = result.split("แปลไทย:")[1].split("อารมณ์:")[0].strip()
        sentiment = result.split("อารมณ์:")[1].strip().lower()
        return translated, sentiment
    except Exception as e:
        return "❌ แปลไม่สำเร็จ", "neutral"

# ✅ ดึงข่าวจาก NewsAPI
NEWS_API_KEY = "1947c97709734759b81277ccb7ee8152"  # ← ใช้ key ของคุณ
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
        translated, sentiment = analyze_and_translate(content)
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

# ✅ รายชื่อหุ้น
stocks: List[Stock] = [
    Stock(ticker="AAPL", name="Apple Inc.", category="portfolio"),
    Stock(ticker="TSLA", name="Tesla Inc.", category="watchlist"),
    Stock(ticker="NVDA", name="NVIDIA Corporation", category="watchlist"),
    Stock(ticker="MSFT", name="Microsoft Corp.", category="portfolio"),
]

# ✅ UI ด้วย Streamlit
st.set_page_config(page_title="📈 Vibe Stock Dashboard", layout="wide")
st.title("📈 Vibe Stock Tracker (OpenAI-Powered)")

category_filter = st.radio("เลือกหมวดหมู่", ["portfolio", "watchlist"])
filtered_stocks = [s for s in stocks if s.category == category_filter]

for stock in filtered_stocks:
    with st.expander(f"{stock.name} ({stock.ticker})"):
        if not stock.news:
            stock.news = fetch_news(stock.ticker)

        # 🎯 แสดงข่าวแยกบวก-ลบ
        good_news = [n for n in stock.news if n.sentiment == "positive"]
        bad_news = [n for n in stock.news if n.sentiment == "negative"]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### ✅ ข่าวบวก")
            for news in good_news:
                st.markdown(f"**🟢 {news.title}**")
                st.caption(news.published_at)
                st.write(news.translated)
                st.markdown(f"[🔗 อ่านต่อ]({news.url})")
                st.markdown("---")

        with col2:
            st.markdown("### ⚠️ ข่าวลบ")
            for news in bad_news:
                st.markdown(f"**🔴 {news.title}**")
                st.caption(news.published_at)
                st.write(news.translated)
                st.markdown(f"[🔗 อ่านต่อ]({news.url})")
                st.markdown("---")
