"""
Autonomous SEM AI Agent powered by Gemini
Monitors campaigns, detects issues, takes actions, chats with user
"""

import os
import json
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional

AGENT_STATE_FILE = os.path.join(os.path.dirname(__file__), ".agent_state.json")


def load_agent_state():
    try:
        if os.path.exists(AGENT_STATE_FILE):
            with open(AGENT_STATE_FILE) as f:
                return json.load(f)
    except:
        pass
    return {
        "active": True,
        "last_check": None,
        "alerts": [],
        "actions_taken": [],
        "chat_history": [],
        "campaign_snapshots": [],
    }

def save_agent_state(state):
    try:
        with open(AGENT_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2, default=str)
    except Exception as e:
        print(f"Warning: could not save agent state: {e}")

_agent_state = load_agent_state()


def call_gemini(prompt: str, system: str = "") -> str:
    """Call Gemini API via direct REST — no library needed."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API key not configured."
    try:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        resp = httpx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent",
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": full_prompt}]}]},
            timeout=45,
        )
        if resp.status_code != 200:
            return f"Gemini API error {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Gemini error: {str(e)}"


def call_gemini_json(prompt: str, system: str = "") -> dict:
    """Call Gemini and parse JSON response."""
    result = call_gemini(prompt, system)
    try:
        import re
        cleaned = re.sub(r'^```(?:json)?\s*', '', result.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r'\s*```\s*$', '', cleaned, flags=re.MULTILINE)
        return json.loads(cleaned.strip())
    except:
        return {"raw": result, "status": "healthy", "summary": result[:200], "alerts": [], "recommendations": [], "actions": []}


def analyze_campaigns_with_gemini(campaigns: list, budget_limits: dict = {}) -> dict:
    """Use Gemini to analyze campaign performance and generate insights."""
    if not campaigns:
        return {
            "status": "no_campaigns",
            "summary": "No campaigns found. Publish your first campaign from the Google Ads tab.",
            "alerts": [],
            "recommendations": [],
            "actions": [],
        }

    campaign_data = json.dumps(campaigns, indent=2)

    system = """You are an expert Google Ads SEM agent. Analyze campaign performance data and provide actionable insights.
Respond ONLY in JSON format with this exact structure:
{
  "status": "healthy|warning|critical",
  "summary": "2-3 sentence overview of performance",
  "alerts": [{"level": "info|warning|critical", "campaign": "campaign name", "message": "specific issue description"}],
  "recommendations": [{"campaign": "name", "action": "what to do", "reason": "why"}],
  "actions": [{"type": "pause|enable|adjust_bid", "campaign_resource": "resource_name", "reason": "why"}]
}"""

    prompt = f"""Analyze these Google Ads campaigns and provide insights:

{campaign_data}

Check for:
- CTR below 1% = warning, below 0.5% = critical
- Zero impressions = critical (campaign not serving)
- Zero clicks with impressions = ad copy issue
- High spend relative to conversions = efficiency issue
- PAUSED status campaigns that could be enabled"""

    return call_gemini_json(prompt, system)


def generate_weekly_report(snapshots: list) -> str:
    """Generate a weekly performance report using Gemini."""
    if not snapshots:
        return "No campaign data available yet. Run an analysis first by clicking 'Analyze campaigns' in the SEMA panel."

    system = "You are an expert SEM analyst. Generate a concise weekly Google Ads performance report with clear sections and actionable recommendations."

    prompt = f"""Generate a weekly Google Ads performance report from this data:

{json.dumps(snapshots[-20:], indent=2)}

Include:
1. Executive summary
2. Top performing campaigns
3. Issues and underperformers
4. Action plan for next week
5. Budget efficiency"""

    return call_gemini(prompt, system)


def chat_with_agent(user_message: str, campaigns: list, session_id: str) -> str:
    """Chat with the AI SEM agent about campaign performance."""
    state = _agent_state

    campaign_context = json.dumps(campaigns[:10], indent=2) if campaigns else "No campaign data available yet."
    recent_alerts = json.dumps(state.get("alerts", [])[-5:], indent=2)

    history = state.get("chat_history", [])[-8:]
    history_text = ""
    for msg in history:
        role = "User" if msg["role"] == "user" else "SEMA"
        history_text += f"{role}: {msg['content']}\n"

    system = """You are SEMA (SEM AI), an expert autonomous Google Ads agent.
You monitor campaigns, detect issues, and provide specific actionable advice.
Be concise, data-driven, and reference specific campaign names and metrics when available.
When no campaign data is available, guide the user to publish their first campaign."""

    prompt = f"""Campaign data:
{campaign_context}

Recent alerts:
{recent_alerts}

Conversation:
{history_text}
User: {user_message}

SEMA:"""

    response = call_gemini(prompt, system)

    state["chat_history"].append({"role": "user", "content": user_message, "timestamp": datetime.now().isoformat()})
    state["chat_history"].append({"role": "agent", "content": response, "timestamp": datetime.now().isoformat()})
    state["chat_history"] = state["chat_history"][-50:]
    save_agent_state(state)

    return response


async def run_monitoring_cycle(campaigns: list, session_id: str, customer_id: str):
    """Run one monitoring cycle."""
    state = _agent_state
    print(f"[SEMA] Running monitoring cycle at {datetime.now().isoformat()}")

    budget_limits = state.get("budget_limits", {})
    analysis = analyze_campaigns_with_gemini(campaigns, budget_limits)

    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "campaigns": campaigns,
        "analysis": analysis,
    }
    state["campaign_snapshots"].append(snapshot)
    state["campaign_snapshots"] = state["campaign_snapshots"][-100:]

    new_alerts = []
    for alert in analysis.get("alerts", []):
        alert["timestamp"] = datetime.now().isoformat()
        new_alerts.append(alert)

    state["alerts"] = (state.get("alerts", []) + new_alerts)[-50:]
    state["last_check"] = datetime.now().isoformat()

    for action in analysis.get("actions", []):
        action["timestamp"] = datetime.now().isoformat()
        action["status"] = "recommended"
        state.setdefault("actions_taken", []).append(action)

    state["actions_taken"] = state.get("actions_taken", [])[-50:]
    save_agent_state(state)

    print(f"[SEMA] Cycle complete. Status: {analysis.get('status')}. Alerts: {len(new_alerts)}")
    return analysis


def get_agent_status() -> dict:
    state = _agent_state
    return {
        "active": state.get("active", True),
        "last_check": state.get("last_check"),
        "total_alerts": len(state.get("alerts", [])),
        "recent_alerts": state.get("alerts", [])[-5:],
        "recent_actions": state.get("actions_taken", [])[-5:],
        "chat_history": state.get("chat_history", [])[-20:],
        "total_snapshots": len(state.get("campaign_snapshots", [])),
    }


def clear_agent_chat():
    _agent_state["chat_history"] = []
    save_agent_state(_agent_state)


def set_agent_active(active: bool):
    _agent_state["active"] = active
    save_agent_state(_agent_state)
