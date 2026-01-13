import yfinance as yf
import pandas as pd
import pandas_ta as ta
import nltk
import requests
import time

class FinanceEngine:
    @staticmethod
    def get_session():
        """Creates a browser-mimicking session"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        return session

    @staticmethod
    def get_sentiment(ticker_symbol):
        # 1. Setup NLTK (Lazy Load)
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon', quiet=True)
        
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        sia = SentimentIntensityAnalyzer()
        
        # 2. Retry Logic List: Try Index, then Reliance, then HDFC Bank
        fallbacks = [ticker_symbol, "RELIANCE.NS", "HDFCBANK.NS"]
        news = []
        session = FinanceEngine.get_session()

        for ticker_name in fallbacks:
            try:
                t = yf.Ticker(ticker_name, session=session)
                news = t.news
                if news and len(news) > 0:
                    print(f"Successfully fetched news from: {ticker_name}")
                    break # Stop retrying if we found news
                time.sleep(1) # Small delay between retries
            except Exception as e:
                print(f"Attempt failed for {ticker_name}: {e}")
                continue

        if not news:
            return {"avg": 0, "label": "NEUTRAL", "list": [{"title": "No recent headlines available", "score": 0}]}

        # 3. Process the results
        scores = []
        headlines = []
        for n in news[:8]:
            title = n.get('title', '')
            if title:
                score = sia.polarity_scores(title)['compound']
                scores.append(score)
                headlines.append({"title": title, "score": score})

        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Bullish/Bearish Thresholds
        if avg_score >= 0.05: label = "BULLISH"
        elif avg_score <= -0.05: label = "BEARISH"
        else: label = "NEUTRAL"

        return {"avg": round(avg_score, 2), "label": label, "list": headlines[:5]}

    @staticmethod
    def get_technical_analysis(symbol):
        """Technical analysis with session support"""
        try:
            session = FinanceEngine.get_session()
            # Fetching 5 days of 5-minute data
            df = yf.download(symbol, period='5d', interval='5m', progress=False, session=session)
            
            if df.empty: return None
            
            df.ta.rsi(append=True)
            last = df.iloc[-1]
            rsi_val = float(last.filter(like='RSI').iloc[0])
            
            return {
                "price": round(float(last['Close']), 2),
                "rsi": round(rsi_val, 2),
                "signal": "BUY" if rsi_val < 30 else "SELL" if rsi_val > 70 else "NEUTRAL"
            }
        except Exception as e:
            print(f"Technical Error: {e}")
            return None
