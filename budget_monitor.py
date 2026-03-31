"""
Budget Monitor — runs as a background scheduler.
Checks all active campaigns every 30 minutes and pauses/resumes based on budget rules.
"""

import asyncio
import json
import os
from datetime import datetime


# In-memory store for MVP (replace with PostgreSQL in production)
# Format: { "campaign_resource_name": { "monthly_budget": 500, "monthly_spend": 120.5, "status": "ENABLED" } }
_campaign_budgets: dict = {}


def register_campaign(
    campaign_resource_name: str,
    monthly_budget_usd: float,
    customer_id: str,
    refresh_token: str,
):
    """Register a campaign for budget monitoring."""
    _campaign_budgets[campaign_resource_name] = {
        "monthly_budget_usd": monthly_budget_usd,
        "monthly_spend_usd": 0.0,
        "status": "ENABLED",
        "customer_id": customer_id,
        "refresh_token": refresh_token,
        "registered_at": datetime.now().isoformat(),
        "last_checked": None,
        "actions_log": [],
    }


def update_spend(campaign_resource_name: str, spend_usd: float, status: str):
    """Update the recorded spend for a campaign."""
    if campaign_resource_name in _campaign_budgets:
        _campaign_budgets[campaign_resource_name]["monthly_spend_usd"] = spend_usd
        _campaign_budgets[campaign_resource_name]["status"] = status
        _campaign_budgets[campaign_resource_name]["last_checked"] = datetime.now().isoformat()


def get_all_monitored() -> dict:
    """Return all monitored campaigns with their budget status."""
    result = {}
    for name, data in _campaign_budgets.items():
        budget = data["monthly_budget_usd"]
        spend = data["monthly_spend_usd"]
        pct = round((spend / budget * 100), 1) if budget > 0 else 0
        result[name] = {
            **data,
            "spend_percentage": pct,
            "budget_remaining_usd": round(budget - spend, 2),
            "alert": "CRITICAL" if pct >= 100 else "WARNING" if pct >= 90 else "OK",
        }
    return result


async def run_budget_check():
    """
    Main monitoring loop — runs every 30 minutes.
    Fetches real spend from Google Ads API and enforces budget rules.
    """
    from ads_manager import get_campaign_spend, pause_campaign, enable_campaign

    while True:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Running budget check for {len(_campaign_budgets)} campaigns...")

        for resource_name, data in list(_campaign_budgets.items()):
            try:
                customer_id = data["customer_id"]
                refresh_token = data["refresh_token"]
                monthly_budget = data["monthly_budget_usd"]

                # Fetch today's spend from Google Ads
                spend_data = get_campaign_spend(customer_id, refresh_token, resource_name)

                if not spend_data.get("success"):
                    print(f"  ⚠ Could not fetch spend for {resource_name}")
                    continue

                current_spend = spend_data["spend_today_usd"]
                current_status = spend_data["status"]

                # Update our records
                update_spend(resource_name, current_spend, current_status)

                spend_pct = (current_spend / monthly_budget * 100) if monthly_budget > 0 else 0

                print(f"  Campaign: {spend_data['campaign_name']} | Spend: ${current_spend} / ${monthly_budget} ({spend_pct:.1f}%) | Status: {current_status}")

                # Enforce budget rules
                if spend_pct >= 100 and current_status == "ENABLED":
                    print(f"  🛑 Budget exhausted — pausing campaign")
                    result = pause_campaign(customer_id, refresh_token, resource_name)
                    _campaign_budgets[resource_name]["actions_log"].append({
                        "time": datetime.now().isoformat(),
                        "action": "PAUSED",
                        "reason": f"Budget 100% spent (${current_spend}/${monthly_budget})",
                    })

                elif spend_pct >= 90 and current_status == "ENABLED":
                    print(f"  ⚠ 90% budget threshold reached — sending alert")
                    _campaign_budgets[resource_name]["actions_log"].append({
                        "time": datetime.now().isoformat(),
                        "action": "ALERT_90PCT",
                        "reason": f"90% budget reached (${current_spend}/${monthly_budget})",
                    })

                elif spend_pct < 5 and current_status == "PAUSED":
                    # New month / budget reset detected
                    print(f"  ✅ Budget reset detected — resuming campaign")
                    result = enable_campaign(customer_id, refresh_token, resource_name)
                    _campaign_budgets[resource_name]["actions_log"].append({
                        "time": datetime.now().isoformat(),
                        "action": "RESUMED",
                        "reason": "Budget reset — spend near zero",
                    })

            except Exception as e:
                print(f"  ❌ Error checking {resource_name}: {e}")

        # Wait 30 minutes before next check
        await asyncio.sleep(30 * 60)


def start_monitor_background(loop=None):
    """Start the budget monitor as a background task."""
    if loop:
        loop.create_task(run_budget_check())
    else:
        asyncio.create_task(run_budget_check())
