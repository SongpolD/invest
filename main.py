import streamlit as st
import requests
import datetime
import pandas as pd
import openai
from newsapi import NewsApiClient
import time
import yfinance as yf

# ========== Configs ==========
openai.api_key = st.secrets["OPENAI_API_KEY"]
newsapi = NewsApiClient(api_key=st.secrets["NEWS_API_KEY"])

PORT_STOCKS = ["AAPL", "TSLA", "NVDA"]  # Example port
WATCHLIST = ["GOOGL", "MSFT"]
ALL_TICKERS = list(set(PORT_STOCKS + WATCHLIST))

# ========== Utility Functions ==========
@st.cache_data(ttl=300)  # Cache 5 นาที
def get_stock_price_and_indicators(ticker):
    """ดึงราคาหุ้นจริงผ่าน Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="30d")  # ข้อมูล 30 วัน
        
        if hist.empty:
            raise Exception(f"ไม่พบข้อมูลสำหรับ {ticker}")
            
        current_price = hist['Close'].iloc[-1]
        
        # คำนวณ RSI
        closes = hist['Close']
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # คำนวณ EMA 20 วัน
        ema = closes.ewm(span=20).mean().iloc[-1]
        
        return {
            "price": round(current_price, 2),
            "rsi": round(rsi, 2),
            "ema": round(ema, 2),
            "change": round(((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100, 2)
        }
    except Exception as e:
        st.error(f"❌ ไม่สามารถดึงข้อมูลราคาหุ้น {ticker}: {str(e)}")
        # ใช้ข้อมูล Mock เป็น fallback
        return {
            "price": round(100 + hash(ticker) % 100, 2),
            "rsi": 30 + hash(ticker + "rsi") % 40,
            "ema": round(95 + hash(ticker + "ema") % 10, 2),
            "change": round(-5 + hash(ticker + "change") % 10, 2)
        }

def get_news_for_ticker(ticker):
    """ดึงข่าวพร้อม Rate Limiting Protection"""
    
    # ✅ Mapping ชื่อหุ้นให้เข้าใจง่ายขึ้น
    query_map = {
        "AAPL": "Apple Inc stock",
        "TSLA": "Tesla Motors stock",
        "NVDA": "Nvidia Corporation stock", 
        "GOOGL": "Google Alphabet stock",
        "MSFT": "Microsoft Corporation stock"
    }
    query_term = query_map.get(ticker, f"{ticker} stock")

    # ✅ ใช้ session_state cache เพื่อลดการเรียกซ้ำ
    cache_key = f"news_cache_{ticker}_{datetime.datetime.now().strftime('%Y%m%d_%H')}"  # Cache ต่อชั่วโมง
    
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    # ✅ Rate Limiting Protection
    last_request_key = "last_news_request"
    if last_request_key in st.session_state:
        time_since_last = time.time() - st.session_state[last_request_key]
        if time_since_last < 10:  # รอ 10 วินาทีระหว่างการเรียก
            st.warning(f"⏳ รอ {10-int(time_since_last)} วินาที เพื่อป้องกัน Rate Limit")
            time.sleep(10 - time_since_last)

    try:
        # เรียก API จริง
        st.session_state[last_request_key] = time.time()
        
        articles = newsapi.get_everything(
            q=query_term,
            language="en",
            sort_by="publishedAt",
            page_size=8,
            from_param=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')  # ข่าว 7 วันย้อนหลัง
        )
        
        if articles["status"] == "ok":
            filtered_articles = [art for art in articles["articles"] if art["title"] and art["description"]]
            st.session_state[cache_key] = filtered_articles[:6]  # แคชไว้ใน session
            return st.session_state[cache_key]
        else:
            raise Exception(f"API Error: {articles.get('message', 'Unknown error')}")
            
    except Exception as e:
        st.error(f"❌ ดึงข่าวไม่สำเร็จ: {str(e)}")
        
        # ✅ Fallback ข่าวตัวอย่าง
        fallback_news = [
            {
                "title": f"📈 {ticker} อัปเดตล่าสุด: การเคลื่อนไหวในตลาด",
                "description": f"ข้อมูลการเคลื่อนไหวของหุ้น {ticker} และแนวโน้มในระยะสั้น",
                "url": f"https://finance.yahoo.com/quote/{ticker}",
                "publishedAt": datetime.datetime.now().isoformat()
            },
            {
                "title": f"💼 {ticker} รายงานผลประกอบการ",
                "description": f"การวิเคราะห์ผลงานล่าสุดของ {ticker} และผลกระทบต่อราคาหุ้น",
                "url": f"https://finance.yahoo.com/quote/{ticker}",
                "publishedAt": datetime.datetime.now().isoformat()
            }
        ]
        return fallback_news

@st.cache_data(ttl=3600)  # Cache 1 ชั่วโมง
def analyze_sentiment_and_summarize(article):
    """วิเคราะห์ความรู้สึกและสรุปข่าว"""
    try:
        prompt = f"""
        วิเคราะห์บทความข่าวหุ้นนี้:
        หัวข้อ: "{article['title']}"
        เนื้อหา: {article['description']}

        กรุณาตอบเป็นภาษาไทยในรูปแบบ:
        
        **สรุป:** [สรุปประเด็นสำคัญใน 1-2 ประโยค]
        
        **ผลกระทบ:** [บวก/ลบ/เป็นกลาง] - [เหตุผลสั้นๆ]
        
        **คำแนะนำ:** [ข้อเสนอแนะสำหรับนักลงทุน]
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # ใช้ gpt-3.5-turbo ประหยัดกว่า
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        # Fallback analysis
        return f"""
        **สรุป:** ข่าวเกี่ยวกับการเคลื่อนไหวของหุ้น
        
        **ผลกระทบ:** เป็นกลาง - ต้องติดตามความคืบหน้าต่อไป
        
        **คำแนะนำ:** ศึกษาข้อมูลเพิ่มเติมก่อนตัดสินใจลงทุน
        """

def rsi_recommendation(rsi):
    if rsi < 30:
        return "🟢 RSI ต่ำเกินไป → สัญญาณซื้อแข็งแกร่ง"
    elif rsi > 70:
        return "🔴 RSI สูงเกินไป → สัญญาณขายแข็งแกร่ง"
    elif rsi < 40:
        return "🟡 RSI ค่อนข้างต่ำ → อาจพิจารณาซื้อ"
    elif rsi > 60:
        return "🟡 RSI ค่อนข้างสูง → ระวังการปรับตัวลง"
    else:
        return "⚪ RSI ปกติ → ถือหรือรอจังหวะ"

def ema_recommendation(price, ema):
    diff_percent = ((price - ema) / ema * 100)
    if diff_percent > 2:
        return f"🟢 ราคาสูงกว่า EMA {diff_percent:.1f}% → เทรนด์ขาขึ้นแข็งแกร่ง"
    elif diff_percent < -2:
        return f"🔴 ราคาต่ำกว่า EMA {abs(diff_percent):.1f}% → เทรนด์ขาลงแข็งแกร่ง"
    elif diff_percent > 0:
        return f"🟡 ราคาสูงกว่า EMA {diff_percent:.1f}% → เทรนด์ขาขึ้นอ่อน"
    elif diff_percent < 0:
        return f"🟡 ราคาต่ำกว่า EMA {abs(diff_percent):.1f}% → เทรนด์ขาลงอ่อน"
    else:
        return "⚪ ราคาใกล้เคียง EMA → อาจรอแนวโน้ม"

# ========== Streamlit Layout ==========
st.set_page_config(page_title="📊 Stock News Dashboard", layout="wide")

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #1f77b4;
}
.positive { color: #28a745; }
.negative { color: #dc3545; }
.neutral { color: #6c757d; }
</style>
""", unsafe_allow_html=True)

st.title("📈 Dashboard ข่าวหุ้น + ตัวชี้วัดแบบ Realtime")
st.markdown("*อัปเดตข้อมูลจาก Yahoo Finance และ News API*")

ticker = st.selectbox("🎯 เลือกหุ้นในพอร์ตหรือ Watchlist:", ALL_TICKERS, index=0)

# Refresh button
if st.button("🔄 รีเฟรชข้อมูล"):
    st.cache_data.clear()
    st.rerun()

with st.spinner("📡 กำลังดึงข้อมูลหุ้นและข่าว..."):
    stock_data = get_stock_price_and_indicators(ticker)
    raw_news = get_news_for_ticker(ticker)

# ========== Display Section ==========

# Price Section
change_color = "positive" if stock_data['change'] >= 0 else "negative"
change_symbol = "+" if stock_data['change'] >= 0 else ""

st.markdown(f"""
<div class="metric-card">
<h2>💰 {ticker} - ราคาปัจจุบัน: ${stock_data['price']}</h2>
<p class="{change_color}">การเปลี่ยนแปลง: {change_symbol}{stock_data['change']}%</p>
</div>
""", unsafe_allow_html=True)

# Technical Indicators
col1, col2 = st.columns(2)

with col1:
    st.metric("📊 RSI (14 วัน)", f"{stock_data['rsi']:.1f}", help="Relative Strength Index - ดัชนีความแข็งแรงของราคา")
    st.info(rsi_recommendation(stock_data['rsi']))

with col2:
    st.metric("📈 EMA (20 วัน)", f"${stock_data['ema']:.2f}", help="Exponential Moving Average - ค่าเฉลี่ยเคลื่อนที่แบบเอ็กซ์โปเนนเชียล")
    st.info(ema_recommendation(stock_data['price'], stock_data['ema']))

# News Analysis Section
st.subheader("📰 ข่าวและการวิเคราะห์")

if raw_news:
    with st.expander(f"📄 พบข่าวทั้งหมด {len(raw_news)} ข่าว", expanded=True):
        for i, article in enumerate(raw_news[:4], 1):  # แสดง 4 ข่าวแรก
            with st.container():
                col_title, col_date = st.columns([3, 1])
                
                with col_title:
                    st.markdown(f"**{i}. [{article['title']}]({article['url']})**")
                
                with col_date:
                    try:
                        pub_date = datetime.datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                        st.caption(f"📅 {pub_date.strftime('%d/%m/%Y %H:%M')}")
                    except:
                        st.caption("📅 วันที่ไม่ระบุ")
                
                if article.get('description'):
                    st.write(f"📝 {article['description'][:200]}...")
                
                # AI Analysis
                with st.spinner(f"🤖 กำลังวิเคราะห์ข่าวที่ {i}..."):
                    analysis = analyze_sentiment_and_summarize(article)
                    st.markdown(f"**🎯 การวิเคราะห์:**\n{analysis}")
                
                st.divider()
else:
    st.warning("⚠️ ไม่พบข่าวสำหรับหุ้นนี้ในขณะนี้")

# Summary Section
st.subheader("📋 สรุปภาพรวม")
col_summary1, col_summary2 = st.columns(2)

with col_summary1:
    st.markdown("### 📊 สถานะทางเทคนิค")
    rsi_status = "เป็นกลาง"
    if stock_data['rsi'] < 30: rsi_status = "ซื้อแรง"
    elif stock_data['rsi'] > 70: rsi_status = "ขายแรง"
    
    ema_status = "เป็นกลาง" 
    if stock_data['price'] > stock_data['ema']: ema_status = "เทรนด์บวก"
    elif stock_data['price'] < stock_data['ema']: ema_status = "เทรนด์ลบ"
    
    st.write(f"- RSI: {rsi_status}")
    st.write(f"- EMA: {ema_status}")

with col_summary2:
    st.markdown("### 📈 คำแนะนำการลงทุน")
    if stock_data['rsi'] < 30 and stock_data['price'] > stock_data['ema']:
        st.success("✅ สัญญาณซื้อ - RSI ต่ำและเทรนด์บวก")
    elif stock_data['rsi'] > 70 and stock_data['price'] < stock_data['ema']:
        st.error("❌ สัญญาณขาย - RSI สูงและเทรนด์ลบ")
    else:
        st.info("⏳ สัญญาณไม่ชัดเจน - ติดตามต่อไป")

st.markdown("---")
st.caption("⚠️ ข้อมูลนี้เป็นเพียงการศึกษาเท่านั้น ไม่ใช่คำแนะนำการลงทุน กรุณาศึกษาข้อมูลเพิ่มเติมก่อนตัดสินใจลงทุน")
