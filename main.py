import streamlit as st
import requests
import datetime
import pandas as pd
import openai
from newsapi import NewsApiClient

# ========== Configs ==========
openai.api_key = st.secrets["OPENAI_API_KEY"]
newsapi = NewsApiClient(api_key=st.secrets["NEWS_API_KEY"])

PORT_STOCKS = ["AAPL", "TSLA", "NVDA"]  # Example port
WATCHLIST = ["GOOGL", "MSFT"]
ALL_TICKERS = list(set(PORT_STOCKS + WATCHLIST))

# ========== Utility Functions ==========
def get_stock_price_and_indicators(ticker):
    # --- MOCKUP API --- Replace this with actual finance API call
    return {
        "price": round(100 + hash(ticker) % 100, 2),
        "rsi": 30 + hash(ticker + "rsi") % 40,  # 30-70
        "ema": round(95 + hash(ticker + "ema") % 10, 2),
    }

def get_news_for_ticker(ticker):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    articles = newsapi.get_everything(
        q=ticker,
        from_param=today,
        to=today,
        language="en",
        sort_by="relevancy",
        page=1,
    )
    return articles["articles"][:8]  # return top 8 for filtering later

def analyze_sentiment_and_summarize(article):
    prompt = f"""
    บทความนี้เกี่ยวกับหุ้น: "{article['title']}"
    เนื้อหาคือ:
    {article['description'] or article['content']}

    1. สรุปประเด็นสำคัญ (เป็น Bullet)
    2. วิเคราะห์ว่าเป็นข่าวเชิงบวกหรือลบต่อราคาหุ้น และเพราะอะไร
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()

def rsi_recommendation(rsi):
    if rsi < 30:
        return "RSI ต่ำเกินไป → อาจถึงจุดซื้อ"
    elif rsi > 70:
        return "RSI สูงเกินไป → อาจถึงจุดขาย"
    else:
        return "RSI ปกติ → ถือหรือรอจังหวะ"

def ema_recommendation(price, ema):
    if price > ema:
        return "ราคาสูงกว่า EMA → เทรนด์ขาขึ้น"
    elif price < ema:
        return "ราคาต่ำกว่า EMA → เทรนด์ขาลง"
    else:
        return "ราคาใกล้เคียง EMA → อาจรอแนวโน้ม"

# ========== Streamlit Layout ==========
st.set_page_config(page_title="📊 Stock News Dashboard", layout="wide")
st.title("📈 Dashboard ข่าวหุ้น + ตัวชี้วัดแบบ Realtime")

ticker = st.selectbox("เลือกหุ้นในพอร์ตหรือ Watchlist:", ALL_TICKERS)

with st.spinner("📡 กำลังดึงข้อมูลหุ้นและข่าว..."):
    stock_data = get_stock_price_and_indicators(ticker)
    raw_news = get_news_for_ticker(ticker)

    summaries = []
    for article in raw_news:
        try:
            summary = analyze_sentiment_and_summarize(article)
            summaries.append({
                "title": article["title"],
                "summary": summary,
                "url": article["url"]
            })
        except Exception as e:
            continue

# ========== Display Section ==========

st.subheader(f"📉 ราคาปัจจุบัน: ${stock_data['price']}")
col1, col2 = st.columns(2)

with col1:
    st.metric("📌 RSI", stock_data['rsi'], help="ดัชนีความแข็งแรงของราคา")
    st.write(rsi_recommendation(stock_data['rsi']))

with col2:
    st.metric("📌 EMA", stock_data['ema'], help="ค่าเฉลี่ยเคลื่อนที่แบบเอ็กซ์โปเนนเชียล")
    st.write(ema_recommendation(stock_data['price'], stock_data['ema']))

# ข่าวแยกสองประเภท
st.subheader("📰 ข่าวรายวัน (แปลไทย + วิเคราะห์)")

positive_news = [n for n in summaries if "บวก" in n["summary"]][:2]
negative_news = [n for n in summaries if "ลบ" in n["summary"]][:2]

st.markdown("#### ✅ ข่าวดีที่อาจส่งผลบวก")
for n in positive_news:
    st.markdown(f"- [{n['title']}]({n['url']})\n\n{n['summary']}")

st.markdown("#### ⚠️ ข่าวร้ายหรือความเสี่ยง")
for n in negative_news:
    st.markdown(f"- [{n['title']}]({n['url']})\n\n{n['summary']}")
