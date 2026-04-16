path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(path) as f:
    content = f.read()

# Find the SEM recommendations section in the prompt and enhance it
old_sem_whole = '''  "sem_recommendations": {{
    "monthly_budget_inr": 40000,
    "monthly_clicks_estimate": "1,000-5,000",
    "estimated_cpc_inr": 25,
    "campaign_type": "Search + Display",
    "bidding_strategy": "Target CPA — focus on conversion-ready audiences",
    "country_budgets": [
      {{"country": "India", "code": "IN", "budget_pct": 50, "budget_inr": 20000, "avg_cpc_inr": 15, "monthly_clicks": "800-1500", "competition": "medium", "notes": "High volume, lower CPC market"}},
      {{"country": "United States", "code": "US", "budget_pct": 30, "budget_inr": 12000, "avg_cpc_inr": 80, "monthly_clicks": "100-200", "competition": "high", "notes": "Premium market, high intent leads"}},
      {{"country": "United Kingdom", "code": "UK", "budget_pct": 20, "budget_inr": 8000, "avg_cpc_inr": 65, "monthly_clicks": "80-150", "competition": "high", "notes": "Strong enterprise market"}}
    ],
    "audience_segments": [
      {{"segment": "IT Professionals", "age_range": "25-45", "interests": ["Technology", "Enterprise Software"]}}
    ]
  }}'''

new_sem_whole = '''  "sem_recommendations": {{
    "industry": "SaaS/Software",
    "monthly_budget_inr": 45000,
    "monthly_clicks_estimate": "1,200-2,500",
    "estimated_cpc_inr": 35,
    "campaign_type": "Search + Display",
    "bidding_strategy": "Target CPA — focus on conversion-ready audiences",
    "budget_calculation": {{
      "target_daily_clicks": 60,
      "avg_cpc_inr": 35,
      "daily_budget_inr": 2100,
      "monthly_budget_inr": 63000,
      "buffer_pct": 10,
      "final_monthly_inr": 45000,
      "reasoning": "Based on SaaS industry benchmarks: India avg CPC ₹18-35, US avg CPC ₹600-900. Target 60 clicks/day across markets. 10% buffer added for bid fluctuations."
    }},
    "country_budgets": [
      {{"country": "India", "code": "IN", "budget_pct": 50, "budget_inr": 22500, "avg_cpc_inr": 18, "monthly_clicks": "800-1500", "competition": "medium", "notes": "High volume, cost-effective leads"}},
      {{"country": "United States", "code": "US", "budget_pct": 30, "budget_inr": 13500, "avg_cpc_inr": 750, "monthly_clicks": "100-200", "competition": "high", "notes": "Premium leads, high conversion value"}},
      {{"country": "United Kingdom", "code": "UK", "budget_pct": 20, "budget_inr": 9000, "avg_cpc_inr": 620, "monthly_clicks": "80-150", "competition": "high", "notes": "Strong enterprise demand"}}
    ],
    "audience_segments": [
      {{"segment": "IT Decision Makers", "age_range": "28-50", "interests": ["Enterprise Software", "Cloud Computing", "IT Management"]}}
    ]
  }}

IMPORTANT BUDGET RULES:
- Detect industry from the website content (SaaS, E-commerce, Finance, Healthcare, Education, IT Services, Legal, Real Estate)
- Use realistic India CPC: SaaS ₹18-45, E-commerce ₹8-25, Finance ₹40-120, Healthcare ₹30-80, Education ₹10-30, IT Services ₹20-60
- Use realistic US CPC (multiply India CPC by 15-20x)
- Calculate: monthly_budget = (target_daily_clicks × weighted_avg_cpc × 30) + 10% buffer
- monthly_clicks_estimate = monthly_budget / avg_cpc (show as range ±20%)
- Always explain the reasoning in budget_calculation.reasoning'''

content = content.replace(old_sem_whole, new_sem_whole)

# Also fix single page prompt
old_sem_single = '''  "sem_recommendations": {{
    "monthly_budget_inr": 15000,
    "monthly_clicks_estimate": "500-1,500",
    "estimated_cpc_inr": 20,
    "campaign_type": "Search",
    "bidding_strategy": "Target CPA — focus on high-intent keywords",
    "country_budgets": [
      {{"country": "India", "code": "IN", "budget_pct": 60, "budget_inr": 9000, "avg_cpc_inr": 15, "monthly_clicks": "400-700", "competition": "medium", "notes": "Primary market focus"}},
      {{"country": "United States", "code": "US", "budget_pct": 40, "budget_inr": 6000, "avg_cpc_inr": 75, "monthly_clicks": "50-100", "competition": "high", "notes": "High value leads"}}
    ],
    "audience_segments": [
      {{"segment": "Decision Makers", "age_range": "28-50", "interests": ["Business Software", "Productivity"]}}
    ]
  }}'''

new_sem_single = '''  "sem_recommendations": {{
    "industry": "SaaS/Software",
    "monthly_budget_inr": 18000,
    "monthly_clicks_estimate": "400-900",
    "estimated_cpc_inr": 30,
    "campaign_type": "Search",
    "bidding_strategy": "Target CPA — focus on high-intent keywords",
    "budget_calculation": {{
      "target_daily_clicks": 25,
      "avg_cpc_inr": 30,
      "daily_budget_inr": 750,
      "monthly_budget_inr": 22500,
      "buffer_pct": 10,
      "final_monthly_inr": 18000,
      "reasoning": "Single page campaign focused on one product/service. Lower volume but higher intent. India avg CPC ₹15-30, US avg CPC ₹500-800."
    }},
    "country_budgets": [
      {{"country": "India", "code": "IN", "budget_pct": 60, "budget_inr": 10800, "avg_cpc_inr": 18, "monthly_clicks": "350-650", "competition": "medium", "notes": "Primary market, cost-effective"}},
      {{"country": "United States", "code": "US", "budget_pct": 40, "budget_inr": 7200, "avg_cpc_inr": 680, "monthly_clicks": "60-120", "competition": "high", "notes": "High value leads"}}
    ],
    "audience_segments": [
      {{"segment": "Decision Makers", "age_range": "28-50", "interests": ["Business Software", "Productivity", "Automation"]}}
    ]
  }}

IMPORTANT BUDGET RULES:
- Detect industry from the website content
- Use realistic India CPC rates based on industry
- Calculate budget from target clicks × CPC + 10% buffer
- Always show reasoning'''

content = content.replace(old_sem_single, new_sem_single)

# Add budget_calculation normalization in the normalize section
old_norm = """        sem['target_countries'] = [cb['code'] for cb in sem.get('country_budgets', [])]"""
new_norm = """        sem['target_countries'] = [cb['code'] for cb in sem.get('country_budgets', [])]
        
        # Ensure budget_calculation exists
        if not sem.get('budget_calculation'):
            budget = sem.get('monthly_budget_inr', 0)
            cpc = sem.get('estimated_cpc_inr', 30)
            daily = round(budget / 30)
            clicks = round(budget / cpc) if cpc else 0
            sem['budget_calculation'] = {
                'target_daily_clicks': round(clicks / 30),
                'avg_cpc_inr': cpc,
                'daily_budget_inr': daily,
                'monthly_budget_inr': budget,
                'buffer_pct': 10,
                'final_monthly_inr': budget,
                'reasoning': f'Budget of ₹{budget:,}/mo calculated based on target CPC of ₹{cpc} and estimated {clicks:,} monthly clicks.'
            }"""

content = content.replace(old_norm, new_norm)

with open(path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print("ERROR:", e)

# Now patch Dashboard to show budget breakdown
dash_path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(dash_path) as f:
    dcontent = f.read()

old_budget = """              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Budget Range</div>
                {seo.sem_recommendations && (
                  <>
                    <div style={{ fontSize: '28px', fontWeight: 600, letterSpacing: '-0.03em', color: 'var(--text)' }}>
                      ₹{(seo?.sem_recommendations?.monthly_budget_inr || 0).toLocaleString()}
                      <span style={{ fontSize: '14px', color: 'var(--text3)', fontWeight: 400 }}>/mo</span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '4px' }}>{(seo?.sem_recommendations?.bidding_strategy || "").split('—')[0]}</div>
                  </>
                )}
              </Card>"""

new_budget = """              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '8px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Budget Range</div>
                {seo.sem_recommendations && (
                  <>
                    <div style={{ fontSize: '28px', fontWeight: 600, letterSpacing: '-0.03em', color: 'var(--text)' }}>
                      ₹{(seo?.sem_recommendations?.monthly_budget_inr || 0).toLocaleString()}
                      <span style={{ fontSize: '14px', color: 'var(--text3)', fontWeight: 400 }}>/mo</span>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>{(seo?.sem_recommendations?.bidding_strategy || "").split('—')[0]}</div>
                    {seo.sem_recommendations.budget_calculation && (
                      <div style={{ marginTop: '8px', padding: '8px', background: 'var(--bg3)', borderRadius: '8px', fontSize: '11px' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text2)', marginBottom: '4px' }}>How calculated:</div>
                        <div style={{ color: 'var(--text3)', lineHeight: 1.6 }}>
                          <div>🎯 Target: {seo.sem_recommendations.budget_calculation.target_daily_clicks} clicks/day</div>
                          <div>💰 Avg CPC: ₹{seo.sem_recommendations.budget_calculation.avg_cpc_inr}</div>
                          <div>📅 Daily: ₹{(seo.sem_recommendations.budget_calculation.daily_budget_inr || 0).toLocaleString()}</div>
                          <div>📦 Buffer: +{seo.sem_recommendations.budget_calculation.buffer_pct}%</div>
                        </div>
                        {seo.sem_recommendations.budget_calculation.reasoning && (
                          <div style={{ marginTop: '4px', padding: '4px 6px', background: 'var(--accent-bg)', borderRadius: '5px', color: 'var(--accent)', fontSize: '10px', lineHeight: 1.5 }}>
                            💡 {seo.sem_recommendations.budget_calculation.reasoning}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </Card>"""

dcontent = dcontent.replace(old_budget, new_budget)

with open(dash_path, 'w') as f:
    f.write(dcontent)

dash_path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(dash_path2, 'w') as f:
    f.write(dcontent)

print("Dashboard budget breakdown added!")
print("Has budget_calculation:", "budget_calculation" in dcontent)
