"""
Autonomous SEM AI Agent powered by Gemini
Monitors campaigns, detects issues, takes actions, chats with user
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import httpx

AGENT_LOG_FILE = os.path.join(os.path.dirname(__file__), ".agent_log.json")
AGENT_STATE_FILE = os.path.join(os.path.dirname(__file__), ".agent_state.json")


# ─── State Management ─────────────────────────────────────────────────────────

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


# ─── Gemini Integration ───────────────────────────────────────────────────────

def call_gemini(prompt: str, system: str = "") -> str:
    """Call Gemini API for analysis."""
    from google import genai as genai_client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API key not configured."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = model.generate_content(full_prompt)
        return response.text
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
        return {"raw": result}


# ─── Campaign Analysis ────────────────────────────────────────────────────────

def analyze_campaigns_with_gemini(campaigns: list, budget_limits: dict = {}) -> dict:
    """Use Gemini to analyze campaign performance and generate insights."""
    if not campaigns:
        return {
            "status": "no_campaigns",
            "summary": "No campaigns found to analyze.",
            "alerts": [],
            "recommendations": [],
            "actions": [],
        }

    campaign_data = json.dumps(campaigns, indent=2)
    
    system = """You are an expert Google Ads SEM agent. Analyze campaign performance data and provide:
1. A brief summary of overall performance
2. Specific alerts for any issues (low CTR, high spend, low impressions, budget warnings)
3. Concrete recommendations to improve performance  
4. Specific actions to take (pause/enable campaigns, adjust bids, etc.)

Respond ONLY in JSON format with this exact structure:
{
  "status": "healthy|warning|critical",
  "summary": "2-3 sentence overview",
  "alerts": [{"level": "info|warning|critical", "campaign": "name", "message": "specific issue"}],
  "recommendations": [{"campaign": "name", "action": "what to do", "reason": "why"}],
  "actions": [{"type": "pause|enable|adjust_bid", "campaign_resource": "resource_name", "reason": "why"}]
}"""

    prompt = f"""Analyze these Google Ads campaigns:

{campaign_data}

Budget limits configured: {json.dumps(budget_limits)}

Key metrics to check:
- CTR below 1% = poor (warning if <1%, critical if <0.5%)  
- Impressions below 100/day = low visibility (warning)
- Spend at 80%+ of daily budget = budget warning
- Zero clicks with high impressions = ad copy issue
- Zero impressions = campaign not serving (critical)"""

    return call_gemini_json(prompt, system)


def generate_weekly_report(snapshots: list) -> str:
    """Generate a weekly performance report using Gemini."""
    if not snapshots:
        return "No campaign data available for weekly report."

    system = """You are an expert SEM analyst. Generate a professional weekly performance report.
Be specific, data-driven, and actionable. Format in clear sections with markdown."""

    prompt = f"""Generate a weekly Google Ads performance report from this data:

{json.dumps(snapshots[-50:], indent=2)}

Include:
1. Executive summary (2-3 sentences)
2. Top performing campaigns
3. Underperforming campaigns with specific issues
4. Week-over-week trends
5. Action plan for next week
6. Budget efficiency analysis"""

    return call_gemini(prompt, system)


# ─── Chat with Agent ──────────────────────────────────────────────────────────

def chat_with_agent(user_message: str, campaigns: list, session_id: str) -> str:
    """Chat with the AI SEM agent about campaign performance."""
    state = _agent_state
    
    # Build context
    campaign_context = json.dumps(campaigns[:10], indent=2) if campaigns else "No campaign data available."
    recent_alerts = json.dumps(state.get("alerts", [])[-5:], indent=2)
    recent_actions = json.dumps(state.get("actions_taken", [])[-5:], indent=2)
    
    # Build conversation history
    history = state.get("chat_history", [])[-10:]
    history_text = ""
    for msg in history:
        role = "User" if msg["role"] == "user" else "Agent"
        history_text += f"{role}: {msg['content']}\n"
    
    system = """You are an expert autonomous Google Ads SEM agent named SEMA (SEM AI).
You monitor campaigns, detect issues, and take actions autonomously.
You have access to real campaign data and recent alerts.
Be concise, specific, and actionable. Use numbers from the data.
When asked about performance, reference specific campaigns and metrics.
When suggesting actions, be specific about what to change and why."""

    prompt = f"""Campaign data:
{campaign_context}

Recent alerts:
{recent_alerts}

Recent actions taken:
{recent_actions}

Conversation history:
{history_text}

User: {user_message}

Respond as SEMA, the SEM AI Agent:"""

    response = call_gemini(prompt, system)
    
    # Save to history
    state["chat_history"].append({"role": "user", "content": user_message, "timestamp": datetime.now().isoformat()})
    state["chat_history"].append({"role": "agent", "content": response, "timestamp": datetime.now().isoformat()})
    
    # Keep last 50 messages
    state["chat_history"] = state["chat_history"][-50:]
    save_agent_state(state)
    
    return response


# ─── Monitoring Loop ──────────────────────────────────────────────────────────

async def run_monitoring_cycle(campaigns: list, session_id: str, customer_id: str):
    """Run one monitoring cycle - analyze campaigns and take actions."""
    state = _agent_state
    
    print(f"[SEMA] Running monitoring cycle at {datetime.now().isoformat()}")
    
    # Get budget limits from state
    budget_limits = state.get("budget_limits", {})
    
    # Analyze with Gemini
    analysis = analyze_campaigns_with_gemini(campaigns, budget_limits)
    
    # Store snapshot
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "campaigns": campaigns,
        "analysis": analysis,
    }
    state["campaign_snapshots"].append(snapshot)
    state["campaign_snapshots"] = state["campaign_snapshots"][-100:]
    
    # Store alerts
    new_alerts = []
    for alert in analysis.get("alerts", []):
        alert["timestamp"] = datetime.now().isoformat()
        new_alerts.append(alert)
    
    state["alerts"] = (state.get("alerts", []) + new_alerts)[-50:]
    state["last_check"] = datetime.now().isoformat()
    
    # Log actions
    actions = analysis.get("actions", [])
    for action in actions:
        action["timestamp"] = datetime.now().isoformat()
        action["status"] = "recommended"
        state["actions_taken"].append(action)
    
    state["actions_taken"] = state.get("actions_taken", [])[-50:]
    
    save_agent_state(state)
    print(f"[SEMA] Cycle complete. Status: {analysis.get('status')}. Alerts: {len(new_alerts)}")
    
    return analysis


def get_agent_status() -> dict:
    """Get current agent status and recent activity."""
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
    """Clear chat history."""
    _agent_state["chat_history"] = []
    save_agent_state(_agent_state)


def set_agent_active(active: bool):
    """Enable or disable the agent."""
    _agent_state["active"] = active
    save_agent_state(_agent_state)
