import re

# Fix main_with_ads.py
with open('main_with_ads.py', 'r') as f:
    content = f.read()
content = re.sub(
    r'from fastapi import [^\n]+',
    'from fastapi import FastAPI, HTTPException, Query, Request, BackgroundTasks',
    content, count=1
)
with open('main_with_ads.py', 'w') as f:
    f.write(content)
print("main_with_ads.py: OK")

# Fix Dashboard.jsx
import os
dash = '../frontend/src/components/Dashboard.jsx'
if os.path.exists(dash):
    with open(dash, 'r') as f:
        content = f.read()
    # Fix Share2
    if 'Share2' not in content.split('lucide-react')[0]:
        content = content.replace(
            "  Zap, Search, BarChart3\n} from 'lucide-react'",
            "  Zap, Search, BarChart3, Share2\n} from 'lucide-react'"
        )
        print("Dashboard.jsx: Fixed Share2")
    # Fix budget .min
    content = content.replace(
        'seo.sem_recommendations.suggested_monthly_budget_usd.min.toLocaleString()',
        '(seo?.sem_recommendations?.monthly_budget_inr || 0).toLocaleString()'
    )
    content = content.replace(
        'seo.sem_recommendations.suggested_monthly_budget_usd.max.toLocaleString()',
        '(seo?.sem_recommendations?.monthly_budget_inr || 0).toLocaleString()'
    )
    content = content.replace(
        'seo.sem_recommendations.estimated_monthly_clicks.min.toLocaleString()',
        '(seo?.sem_recommendations?.estimated_monthly_clicks?.min || 0).toLocaleString()'
    )
    content = content.replace(
        'seo.sem_recommendations.estimated_monthly_clicks.max.toLocaleString()',
        '(seo?.sem_recommendations?.estimated_monthly_clicks?.max || 0).toLocaleString()'
    )
    content = content.replace(
        'seo.sem_recommendations.bidding_strategy.split',
        "(seo?.sem_recommendations?.bidding_strategy || '').split"
    )
    with open(dash, 'w') as f:
        f.write(content)
    print("Dashboard.jsx: OK")
