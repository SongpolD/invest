# main.py

import streamlit as st
import openai
import requests
from typing import List, Literal
from dataclasses import dataclass, field

# ✅ ตั้งค่า API KEY
openai.api_key = st.secrets["OPENAI_API_KEY"]
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]  # ใช้ NewsAPI (https://newsapi.org)

# ✅ ประเภทข้อมูล
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

# ✅ ใช้ OpenAI วิเคราะห์อารมณ์ + แปลไทย
def analyze_and_translate(content: str) -> tuple[str, Sentiment]:
    if not content.strip():
        return "❌ ไม่มีเนื้อหาข่าวให้แปล", "neutral"
    
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
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            timeout=30
        )
        result = response.choices[0].message.content
        translated = result.split("แปลไทย:")[1].split("อารมณ์:")[0].strip()
        sentiment = result.split("อารมณ์:")[1].strip().lower()
        return translated, sentiment
    except Exception:
        return "❌ แปลไม่สำเร็จ", "neutral"

# ✅ ดึงข่าวจาก NewsAPI พร้อม fallback ถ้าไม่มี description
def fetch_news(ticker: str) -> List[NewsItem]:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": ticker,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY,
        "pageSize": 5,  # ดึงแค่ 5 ข่าว
    }
    response = requests.get(url, params=params)
    articles = response.json().get("articles", [])
    news_items = []
    for article in articles:
        # 🔁 ใช้ description → content → title
        content = article.get("description") or article.get("content") or article.get("title") or ""
        if not content.strip():
            continue  # ข้ามถ้าไม่มีเนื้อหาจริงๆ

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
    Stock(ticker="HIMS", name="Hims & Hers Health, Inc.", category="watchlist"),
    Stock(ticker="ABBV", name="AbbVie Inc.", category="watchlist"),
    Stock(ticker="NVO", name="Novo Nordisk A/S", category="watchlist"),
]

# ✅ Streamlit UI
st.set_page_config(page_title="📈 Vibe Stock Dashboard", layout="wide")
st.title("📈 Vibe Stock Tracker (OpenAI Powered)")

category_filter = st.radio("เลือกหมวดหมู่", ["portfolio", "watchlist"])
filtered_stocks = [s for s in stocks if s.category == category_filter]

for stock in filtered_stocks:
    with st.expander(f"{stock.name} ({stock.ticker})"):
        if not stock.news:
            st.write("🔄 กำลังดึงข่าว...")
            stock.news = fetch_news(stock.ticker)

        # ✅ แบ่งข่าวตาม sentiment
        good_news = [n for n in stock.news if n.sentiment == "positive"]
        bad_news = [n for n in stock.news if n.sentiment == "negative"]
        neutral_news = [n for n in stock.news if n.sentiment == "neutral"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### ✅ ข่าวเชิงบวก")
            for news in good_news:
                st.markdown(f"**🟢 {news.title}**")
                st.caption(news.published_at)
                st.write(news.translated)
                st.markdown(f"[🔗 อ่านต่อ]({news.url})")
                st.markdown("---")

        with col2:
            st.markdown("### ⚠️ ข่าวเป็นกลาง")
            for news in neutral_news:
                st.markdown(f"**🟡 {news.title}**")
                st.caption(news.published_at)
                st.write(news.translated)
                st.markdown(f"[🔗 อ่านต่อ]({news.url})")
                st.markdown("---")

        with col3:
            st.markdown("### ❌ ข่าวลบ")
            for news in bad_news:
                st.markdown(f"**🔴 {news.title}**")
                st.caption(news.published_at)
                st.write(news.translated)
                st.markdown(f"[🔗 อ่านต่อ]({news.url})")
                st.markdown("---")
