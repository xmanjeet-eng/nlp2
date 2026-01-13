import nltk
import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# FIX: Force download before anything else runs
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

# Initialize after download
sia = SentimentIntensityAnalyzer()

class FinanceEngine:
    @staticmethod
    def get_sentiment(ticker_symbol):
        try:
            # Fallback logic: Indices don't always have news, use RELIANCE for Nifty context
            target = "RELIANCE.NS" if ticker_symbol == "^NSEI" else ticker_symbol
            ticker = yf.Ticker(target)
            news = ticker.news
            
            if not news:
                return {"avg": 0, "label": "NEUTRAL", "list": []}

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
            print(f"Sentiment Error: {e}")
            return {"avg": 0, "label": "NEUTRAL", "list": []}

    @staticmethod
    def get_technical_analysis(symbol):
        try:
            # Fetch data with enough history for indicators
            df = yf.download(symbol, period='5d', interval='5m', progress=False)
            if df.empty: return None
            
            df.ta.rsi(append=True)
            df.ta.ema(length=20, append=True)
            
            last = df.iloc[-1]
            rsi_val = float(last.filter(like='RSI').iloc[0])
            
            return {
                "price": round(float(last['Close']), 2),
                "rsi": round(rsi_val, 2),
                "signal": "OVERSOLD (BUY)" if rsi_val < 35 else "OVERBOUGHT (SELL)" if rsi_val > 65 else "NEUTRAL"
            }
        except Exception as e:
            print(f"Technical Error: {e}")
            return None
