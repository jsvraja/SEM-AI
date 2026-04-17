"""SEO Trend Tracker - stores historical SEO scores per URL"""
import json
import os
from datetime import datetime

TRENDS_FILE = os.path.join(os.path.dirname(__file__), ".seo_trends.json")

def load_trends():
    try:
        if os.path.exists(TRENDS_FILE):
            with open(TRENDS_FILE) as f:
                return json.load(f)
    except:
        pass
    return {}

def save_trends(data):
    try:
        with open(TRENDS_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass

def record_score(url: str, seo_score: int, content_score: int = 0):
    trends = load_trends()
    key = url.rstrip('/').lower()
    if key not in trends:
        trends[key] = []
    today = datetime.now().strftime('%d %b')
    entries = trends[key]
    if not entries or entries[-1]['date'] != today:
        entries.append({
            'date': today,
            'score': seo_score,
            'content': content_score,
            'timestamp': datetime.now().isoformat()
        })
        trends[key] = entries[-30:]
        save_trends(trends)
    return trends[key]

def get_trend(url: str):
    trends = load_trends()
    key = url.rstrip('/').lower()
    return trends.get(key, [])
