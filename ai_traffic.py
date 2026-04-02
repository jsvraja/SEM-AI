"""
AI Traffic Tracker - PostgreSQL backed for persistent storage
"""

import json
import os
from datetime import datetime, date, timedelta
from collections import defaultdict
from typing import Optional
from urllib.parse import urlparse, parse_qs

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

UTM_PLATFORM_MAP = {
    "chatgpt": "chatgpt", "chat.openai": "chatgpt",
    "perplexity": "perplexity", "claude": "claude",
    "gemini": "gemini", "copilot": "copilot",
    "grok": "grok", "meta_ai": "meta_ai", "you": "you",
}

# ─── Database Setup ───────────────────────────────────────────────────────────

def get_db_conn():
    """Get PostgreSQL connection."""
    import psycopg2
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise Exception("DATABASE_URL not set")
    return psycopg2.connect(database_url)


def init_db():
    """Create tables if they don't exist."""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ai_visits (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                visit_date DATE DEFAULT CURRENT_DATE,
                platform_id VARCHAR(50),
                platform_name VARCHAR(100),
                platform_color VARCHAR(20),
                referrer TEXT,
                page VARCHAR(500),
                keyword VARCHAR(500),
                user_agent TEXT,
                converted BOOLEAN DEFAULT FALSE,
                conversion_value DECIMAL(10,2) DEFAULT 0
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("[AI Traffic] Database initialized")
    except Exception as e:
        print(f"[AI Traffic] DB init error: {e}")


# Initialize on import
init_db()


# ─── Platform Detection ───────────────────────────────────────────────────────

def detect_ai_platform(referrer: str) -> Optional[dict]:
    if not referrer:
        return None
    referrer_lower = referrer.lower()
    for platform_id, platform in AI_PLATFORMS.items():
        for domain in platform["domains"]:
            if domain in referrer_lower:
                return {"id": platform_id, **platform}
    return None


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


def extract_search_keyword(referrer: str, utm_term: str = "") -> str:
    if utm_term:
        return utm_term.strip()
    if not referrer:
        return ""
    try:
        parsed = urlparse(referrer)
        params = parse_qs(parsed.query)
        for param in ['q', 'query', 'search', 'text', 'message', 's']:
            if param in params:
                return params[param][0].strip()
    except:
        pass
    return ""


# ─── Logging ──────────────────────────────────────────────────────────────────

def log_visit(referrer: str, page: str, user_agent: str = "", ip: str = "",
              converted: bool = False, conversion_value: float = 0.0,
              utm_source: str = "", utm_term: str = ""):
    platform = detect_ai_platform(referrer)
    if not platform:
        platform = detect_utm_platform(utm_source)
    if not platform:
        return None

    keyword = extract_search_keyword(referrer, utm_term)

    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO ai_visits
                (platform_id, platform_name, platform_color, referrer, page, keyword, user_agent, converted, conversion_value)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            platform["id"], platform["name"], platform["color"],
            referrer[:500], page[:500], keyword[:500],
            user_agent[:200] if user_agent else "",
            converted, conversion_value
        ))
        visit_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return {
            "id": visit_id,
            "platform_id": platform["id"],
            "platform_name": platform["name"],
            "page": page,
            "keyword": keyword,
        }
    except Exception as e:
        print(f"[AI Traffic] log_visit error: {e}")
        return None


# ─── Stats ────────────────────────────────────────────────────────────────────

def get_traffic_stats(days: int = 30) -> dict:
    try:
        conn = get_db_conn()
        cur = conn.cursor()

        cutoff = (date.today() - timedelta(days=days)).isoformat()

        # Total stats
        cur.execute("""
            SELECT COUNT(*), 
                   SUM(CASE WHEN converted THEN 1 ELSE 0 END),
                   SUM(CASE WHEN converted THEN conversion_value ELSE 0 END)
            FROM ai_visits WHERE visit_date >= %s
        """, (cutoff,))
        row = cur.fetchone()
        total_visits = row[0] or 0
        total_conversions = row[1] or 0
        total_value = float(row[2] or 0)

        # Platform breakdown
        cur.execute("""
            SELECT platform_id, platform_name, platform_color,
                   COUNT(*) as visits,
                   SUM(CASE WHEN converted THEN 1 ELSE 0 END) as conversions,
                   SUM(CASE WHEN converted THEN conversion_value ELSE 0 END) as conv_value,
                   COUNT(DISTINCT page) as unique_pages
            FROM ai_visits WHERE visit_date >= %s
            GROUP BY platform_id, platform_name, platform_color
            ORDER BY visits DESC
        """, (cutoff,))
        platforms = []
        for r in cur.fetchall():
            visits = r[3] or 0
            convs = r[4] or 0
            platforms.append({
                "id": r[0], "name": r[1], "color": r[2],
                "visits": visits, "conversions": convs,
                "conversion_rate": round(convs / visits * 100, 1) if visits > 0 else 0,
                "conversion_value": float(r[5] or 0),
                "unique_pages": r[6] or 0,
            })

        # Top pages
        cur.execute("""
            SELECT page, COUNT(*) as visits,
                   array_agg(DISTINCT platform_name) as platforms
            FROM ai_visits WHERE visit_date >= %s
            GROUP BY page ORDER BY visits DESC LIMIT 10
        """, (cutoff,))
        top_pages = [{"page": r[0], "visits": r[1], "platforms": list(r[2])} for r in cur.fetchall()]

        # Top keywords
        cur.execute("""
            SELECT keyword, COUNT(*) as visits,
                   array_agg(DISTINCT platform_name) as platforms,
                   SUM(CASE WHEN converted THEN 1 ELSE 0 END) as conversions
            FROM ai_visits 
            WHERE visit_date >= %s AND keyword != '' AND keyword IS NOT NULL
            GROUP BY keyword ORDER BY visits DESC LIMIT 20
        """, (cutoff,))
        top_keywords = []
        for r in cur.fetchall():
            visits = r[1] or 0
            convs = r[3] or 0
            top_keywords.append({
                "keyword": r[0], "visits": visits,
                "platforms": list(r[2]),
                "conversions": convs,
                "conversion_rate": round(convs / visits * 100, 1) if visits > 0 else 0,
            })

        # Daily trend (last 14 days)
        cur.execute("""
            SELECT visit_date, platform_id, COUNT(*) as visits
            FROM ai_visits 
            WHERE visit_date >= %s
            GROUP BY visit_date, platform_id
        """, ((date.today() - timedelta(days=14)).isoformat(),))
        daily_map = defaultdict(lambda: defaultdict(int))
        for r in cur.fetchall():
            daily_map[str(r[0])][r[1]] += r[2]

        trend = []
        for i in range(14):
            d = (date.today() - timedelta(days=13-i)).isoformat()
            day_data = {"date": d, "total": 0}
            for pid in AI_PLATFORMS:
                day_data[pid] = daily_map[d].get(pid, 0)
                day_data["total"] += day_data[pid]
            trend.append(day_data)

        # Recent visits
        cur.execute("""
            SELECT id, timestamp, platform_id, platform_name, platform_color,
                   page, keyword, converted, conversion_value
            FROM ai_visits WHERE visit_date >= %s
            ORDER BY timestamp DESC LIMIT 20
        """, (cutoff,))
        recent_visits = []
        for r in cur.fetchall():
            recent_visits.append({
                "id": r[0],
                "timestamp": r[1].isoformat() if r[1] else "",
                "platform_id": r[2], "platform_name": r[3], "platform_color": r[4],
                "page": r[5], "keyword": r[6] or "",
                "converted": r[7], "conversion_value": float(r[8] or 0),
            })

        cur.close()
        conn.close()

        impressions_by_platform = {p["id"]: p["visits"] for p in platforms}

        return {
            "period_days": days,
            "total_visits": total_visits,
            "total_conversions": total_conversions,
            "total_conversion_value": round(total_value, 2),
            "overall_conversion_rate": round(total_conversions / total_visits * 100, 1) if total_visits > 0 else 0,
            "platforms": platforms,
            "top_pages": top_pages,
            "top_keywords": top_keywords,
            "impressions_by_platform": impressions_by_platform,
            "daily_trend": trend,
            "recent_visits": recent_visits,
        }

    except Exception as e:
        print(f"[AI Traffic] get_traffic_stats error: {e}")
        return {
            "period_days": days, "total_visits": 0, "total_conversions": 0,
            "total_conversion_value": 0, "overall_conversion_rate": 0,
            "platforms": [], "top_pages": [], "top_keywords": [],
            "impressions_by_platform": {}, "daily_trend": [], "recent_visits": [],
            "error": str(e)
        }


def reset_traffic():
    """Clear all traffic data."""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM ai_visits")
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[AI Traffic] reset error: {e}")
        return False
