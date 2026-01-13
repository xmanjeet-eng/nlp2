import yfinance as yf
import pandas as pd
import pandas_ta as ta
import nltk
import requests

class FinanceEngine:
    @staticmethod
    def get_session():
        """Creates a session with a browser-like User-Agent to avoid blocking"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        return session

    @staticmethod
    def get_sentiment(ticker_symbol):
        try:
            # 1. Lazy-load NLTK inside the function to prevent Gunicorn boot errors
            try:
                nltk.data.find('sentiment/vader_lexicon.zip')
            except LookupError:
                nltk.download('vader_lexicon', quiet=True)
            
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            sia = SentimentIntensityAnalyzer()

            # 2. Use a browser session for the request
            custom_session = FinanceEngine.get_session()
            
            # Use RELIANCE as proxy if Nifty index news is empty
            target = "RELIANCE.NS" if ticker_symbol == "^NSEI" else ticker_symbol
            ticker = yf.Ticker(target, session=custom_session)
            news = ticker.news
            
            if not news:
                return {"avg": 0, "label": "NO NEWS FOUND", "list": []}

            scores = []
            headlines = []
            for n in news[:5]:
                title = n.get('title', '')
                score = sia.polarity_scores(title)['compound']
                scores.append(score)
                headlines.append({"title": title, "score": score})

            avg_score = sum(scores) / len(scores) if scores else 0
            label = "BULLISH" if avg_score > 0.05 else "BEARISH" if avg_score < -0.05 else "NEUTRAL"
            return {"avg": round(avg_score, 2), "label": label, "list": headlines}
            
        except Exception as e:
            print(f"Sentiment Logic Error: {e}")
            return {"avg": 0, "label": "ERROR", "list": []}

    @staticmethod
    def get_technical_analysis(symbol):
        try:
            custom_session = FinanceEngine.get_session()
            df = yf.download(symbol, period='5d', interval='5m', progress=False, session=custom_session)
            
            if df.empty: return None
            
            df.ta.rsi(append=True)
            last = df.iloc[-1]
            rsi_val = float(last.filter(like='RSI').iloc[0])
            
            return {
                "price": round(float(last['Close']), 2),
                "rsi": round(rsi_val, 2),
                "signal": "BUY" if rsi_val < 35 else "SELL" if rsi_val > 65 else "HOLD"
            }
        except Exception as e:
            print(f"Technical Error: {e}")
            return None
