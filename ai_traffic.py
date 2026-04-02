"""
AI Traffic Tracker - Live data only, no demo data
"""

import json
import os
from datetime import datetime, date, timedelta
from collections import defaultdict
from typing import Optional

AI_PLATFORMS = {
    "chatgpt": {"name": "ChatGPT", "domains": ["chat.openai.com", "openai.com", "chatgpt.com"], "color": "#10a37f"},
    "perplexity": {"name": "Perplexity", "domains": ["perplexity.ai", "www.perplexity.ai"], "color": "#20b2aa"},
    "claude": {"name": "Claude", "domains": ["claude.ai", "anthropic.com", "www.claude.ai"], "color": "#cc785c"},
    "gemini": {"name": "Gemini", "domains": ["gemini.google.com", "bard.google.com", "ai.google.com"], "color": "#4285f4"},
    "copilot": {"name": "Microsoft Copilot", "domains": ["copilot.microsoft.com", "bing.com", "www.bing.com"], "color": "#0078d4"},
    "grok": {"name": "Grok", "domains": ["grok.x.ai", "x.ai", "grok.com"], "color": "#1da1f2"},
    "meta_ai": {"name": "Meta AI", "domains": ["meta.ai", "www.meta.ai"], "color": "#0866ff"},
    "you": {"name": "You.com", "domains": ["you.com", "www.you.com"], "color": "#7c3aed"},
}

TRAFFIC_FILE = os.path.join(os.path.dirname(__file__), ".ai_traffic.json")

def load_traffic():
    try:
        if os.path.exists(TRAFFIC_FILE):
            with open(TRAFFIC_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {"visits": [], "total": 0}

def save_traffic(data):
    try:
        with open(TRAFFIC_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Warning: could not save traffic data: {e}")

_traffic_data = load_traffic()


def detect_ai_platform(referrer: str) -> Optional[dict]:
    if not referrer:
        return None
    referrer_lower = referrer.lower()
    for platform_id, platform in AI_PLATFORMS.items():
        for domain in platform["domains"]:
            if domain in referrer_lower:
                return {"id": platform_id, **platform}
    return None


UTM_PLATFORM_MAP = {
    "chatgpt": "chatgpt",
    "chat.openai": "chatgpt",
    "perplexity": "perplexity",
    "claude": "claude",
    "gemini": "gemini",
    "copilot": "copilot",
    "grok": "grok",
    "meta_ai": "meta_ai",
    "you": "you",
}

def detect_utm_platform(utm_source: str) -> Optional[dict]:
    if not utm_source:
        return None
    utm_lower = utm_source.lower()
    for key, platform_id in UTM_PLATFORM_MAP.items():
        if key in utm_lower:
            platform = AI_PLATFORMS.get(platform_id)
            if platform:
                return {"id": platform_id, **platform}
    return None

def log_visit(referrer: str, page: str, user_agent: str = "", ip: str = "", converted: bool = False, conversion_value: float = 0.0, utm_source: str = ""):
    platform = detect_ai_platform(referrer)
    if not platform:
        platform = detect_utm_platform(utm_source)
    if not platform:
        return None

    visit = {
        "id": len(_traffic_data["visits"]) + 1,
        "timestamp": datetime.now().isoformat(),
        "date": date.today().isoformat(),
        "platform_id": platform["id"],
        "platform_name": platform["name"],
        "platform_color": platform["color"],
        "referrer": referrer,
        "page": page,
        "user_agent": user_agent[:200] if user_agent else "",
        "converted": converted,
        "conversion_value": conversion_value,
    }

    _traffic_data["visits"].append(visit)
    _traffic_data["total"] = len(_traffic_data["visits"])

    if len(_traffic_data["visits"]) > 10000:
        _traffic_data["visits"] = _traffic_data["visits"][-10000:]

    save_traffic(_traffic_data)
    return visit


def get_traffic_stats(days: int = 30) -> dict:
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    recent = [v for v in _traffic_data["visits"] if v["date"] >= cutoff]

    platform_counts = defaultdict(lambda: {"visits": 0, "conversions": 0, "conversion_value": 0.0, "pages": set()})
    for v in recent:
        pid = v["platform_id"]
        platform_counts[pid]["visits"] += 1
        platform_counts[pid]["pages"].add(v["page"])
        if v.get("converted"):
            platform_counts[pid]["conversions"] += 1
            platform_counts[pid]["conversion_value"] += v.get("conversion_value", 0)

    platforms = []
    for pid, stats in platform_counts.items():
        platform_info = AI_PLATFORMS.get(pid, {"name": pid, "color": "#888"})
        platforms.append({
            "id": pid,
            "name": platform_info["name"],
            "color": platform_info["color"],
            "visits": stats["visits"],
            "conversions": stats["conversions"],
            "conversion_rate": round(stats["conversions"] / stats["visits"] * 100, 1) if stats["visits"] > 0 else 0,
            "conversion_value": round(stats["conversion_value"], 2),
            "unique_pages": len(stats["pages"]),
        })
    platforms.sort(key=lambda x: x["visits"], reverse=True)

    page_counts = defaultdict(lambda: {"visits": 0, "platforms": set()})
    for v in recent:
        page_counts[v["page"]]["visits"] += 1
        page_counts[v["page"]]["platforms"].add(v["platform_name"])

    top_pages = sorted([
        {"page": page, "visits": stats["visits"], "platforms": list(stats["platforms"])}
        for page, stats in page_counts.items()
    ], key=lambda x: x["visits"], reverse=True)[:10]

    daily = defaultdict(lambda: defaultdict(int))
    for v in recent:
        if v["date"] >= (date.today() - timedelta(days=14)).isoformat():
            daily[v["date"]][v["platform_id"]] += 1

    trend = []
    for i in range(14):
        d = (date.today() - timedelta(days=13-i)).isoformat()
        day_data = {"date": d, "total": 0}
        for pid in AI_PLATFORMS:
            day_data[pid] = daily[d].get(pid, 0)
            day_data["total"] += day_data[pid]
        trend.append(day_data)

    recent_visits = sorted(recent, key=lambda x: x["timestamp"], reverse=True)[:20]
    total_conversions = sum(1 for v in recent if v.get("converted"))
    total_value = sum(v.get("conversion_value", 0) for v in recent if v.get("converted"))

    return {
        "period_days": days,
        "total_visits": len(recent),
        "total_conversions": total_conversions,
        "total_conversion_value": round(total_value, 2),
        "overall_conversion_rate": round(total_conversions / len(recent) * 100, 1) if recent else 0,
        "platforms": platforms,
        "top_pages": top_pages,
        "daily_trend": trend,
        "recent_visits": recent_visits,
    }
