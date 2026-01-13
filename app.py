from flask import Flask, render_template
from engine import FinanceEngine
from datetime import datetime
import pytz

app = Flask(__name__)

@app.route('/')
def home():
    # Fetch Data
    nifty_tech = FinanceEngine.get_technical_analysis('^NSEI')
    news_data = FinanceEngine.get_sentiment('^NSEI')
    
    # Simple Timestamp
    tz = pytz.timezone('Asia/Kolkata')
    ts = datetime.now(tz).strftime('%H:%M:%S')
    
    return render_template('index.html', 
                           nifty=nifty_tech, 
                           news=news_data, 
                           ts=ts)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
