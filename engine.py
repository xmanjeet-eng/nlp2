import yfinance as yf
import pandas as pd
import pandas_ta as ta
import nltk

class FinanceEngine:
    @staticmethod
    def get_sentiment(ticker_symbol):
        try:
            # 1. Ensure NLTK is ready locally inside the function
            try:
                nltk.data.find('sentiment/vader_lexicon.zip')
            except LookupError:
                nltk.download('vader_lexicon', quiet=True)
            
            # 2. Import locally to prevent Gunicorn boot crashes
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            sia = SentimentIntensityAnalyzer()

            # 3. Fetch News (Using RELIANCE as a proxy for NIFTY context)
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
            print(f"Sentiment Logic Error: {e}")
            return {"avg": 0, "label": "NEUTRAL", "list": []}

    @staticmethod
    def get_technical_analysis(symbol):
        try:
            # period='5d' ensures we have enough data for RSI calculation
            df = yf.download(symbol, period='5d', interval='5m', progress=False)
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
            print(f"Technical Analysis Error: {e}")
            return None
