def build_seo_prompt(s: dict) -> str:
    return f"""You are a senior SEO and SEM specialist. Analyze this website data and return a detailed, actionable report.

WEBSITE DATA:
URL: {s['url']}
Title: {s['title']}
Meta Description: {s['meta_description']}
H1 Tags: {s['h1_tags']}
H2 Tags: {s['h2_tags']}
Internal Links: {s['internal_links_count']}
External Links: {s['external_links_count']}
Images: {s['images_count']} total, {s['images_without_alt_count']} missing alt text
Has Schema Markup: {s['has_schema_markup']}
Has Viewport Meta: {s['has_viewport']}
HTML Size: {s['html_size_kb']} KB
Body Text Sample: {s['body_text_sample'][:1500]}

Return ONLY valid JSON with no markdown, no code fences, no explanation. Start your response with {{ and end with }}:
{{
  "overall_seo_score": <integer 0-100>,
  "summary": "<2-3 sentence overall assessment>",
  "strengths": [{{"point": "<strength>", "impact": "high"}}],
  "weaknesses": [{{"point": "<weakness>", "impact": "high", "fix": "<specific fix>"}}],
  "technical_issues": [{{"issue": "<name>", "severity": "critical", "description": "<detail>", "recommendation": "<action>"}}],
  "content_analysis": {{
    "quality_score": <integer 0-100>,
    "readability": "<assessment>",
    "keyword_density": "<assessment>",
    "content_gaps": ["<gap1>", "<gap2>"]
  }},
  "keyword_suggestions": [{{"keyword": "<keyword>", "intent": "transactional", "difficulty": "medium", "priority": "primary"}}],
  "sem_recommendations": {{
    "monthly_budget_inr": <integer in Indian Rupees e.g. 50000>,
    "suggested_monthly_budget_usd": {{"min": <int>, "max": <int>}},
    "budget_calculation": {{
      "target_daily_clicks": <int>,
      "avg_cpc_inr": <int>,
      "daily_budget_inr": <int>,
      "buffer_pct": 20,
      "reasoning": "<brief reasoning>"
    }},
    "bidding_strategy": "<strategy>",
    "target_countries": ["<country1>"],
    "country_budgets": [
      {{"country": "<name>", "budget_inr": <int>, "budget_pct": <int>, "avg_cpc_inr": <int>}}
    ],
    "audience_segments": [{{"segment": "<name>", "age_range": "<range>", "interests": ["<interest>"]}}],
    "estimated_monthly_clicks": {{"min": <int>, "max": <int>}},
    "monthly_budget_inr": <int>,
    "estimated_cpc_usd": {{"min": <float>, "max": <float>}},
    "estimated_cpc_inr": <integer in Indian Rupees e.g. 30>,
    "monthly_budget_inr": <integer in Indian Rupees e.g. 50000>
  }},
  "competitor_insights": {{
    "likely_competitors": ["<domain1>", "<domain2>"],
    "positioning_suggestion": "<suggestion>"
  }},
  "priority_actions": [{{"action": "<action>", "effort": "low", "impact": "high"}}]
}}"""


def build_ad_prompt(s: dict, desc: str, kws: list) -> str:
    return f"""You are a Google Ads copywriting expert. Generate high-converting, policy-compliant Google Ads content.

BUSINESS INFO:
URL: {s['url']}
Page Title: {s['title']}
Meta Description: {s['meta_description']}
Business Description: {desc}
Target Keywords: {kws}
Content Sample: {s['body_text_sample'][:800]}

STRICT RULES:
- Headlines: MAXIMUM 30 characters each
- Descriptions: MAXIMUM 90 characters each
- No exclamation marks more than once per ad
- Be specific and benefit-focused

Return ONLY valid JSON, no markdown, no code fences. Start with {{ and end with }}:
{{
  "ad_variants": [
    {{
      "variant_name": "Value-Led",
      "angle": "<angle>",
      "headlines": [{{"text": "<max 30 chars>", "char_count": <int>}},
                    {{"text": "<max 30 chars>", "char_count": <int>}},
                    {{"text": "<max 30 chars>", "char_count": <int>}},
                    {{"text": "<max 30 chars>", "char_count": <int>}},
                    {{"text": "<max 30 chars>", "char_count": <int>}}],
      "descriptions": [{{"text": "<max 90 chars>", "char_count": <int>}},
                       {{"text": "<max 90 chars>", "char_count": <int>}},
                       {{"text": "<max 90 chars>", "char_count": <int>}}],
      "display_url_path": "/free-trial"
    }},
    {{
      "variant_name": "Feature-Led",
      "angle": "<angle>",
      "headlines": [{{"text": "<max 30 chars>", "char_count": <int>}},
                    {{"text": "<max 30 chars>", "char_count": <int>}},
                    {{"text": "<max 30 chars>", "char_count": <int>}},
                    {{"text": "<max 30 chars>", "char_count": <int>}},
                    {{"text": "<max 30 chars>", "char_count": <int>}}],
      "descriptions": [{{"text": "<max 90 chars>", "char_count": <int>}},
                       {{"text": "<max 90 chars>", "char_count": <int>}},
                       {{"text": "<max 90 chars>", "char_count": <int>}}],
      "display_url_path": "/features"
    }},
    {{
      "variant_name": "Social Proof",
      "angle": "<angle>",
      "headlines": [{{"text": "<max 30 chars>", "char_count": <int>}},
                    {{"text": "<max 30 chars>", "char_count": <int>}},
                    {{"text": "<max 30 chars>", "char_count": <int>}},
                    {{"text": "<max 30 chars>", "char_count": <int>}},
                    {{"text": "<max 30 chars>", "char_count": <int>}}],
      "descriptions": [{{"text": "<max 90 chars>", "char_count": <int>}},
                       {{"text": "<max 90 chars>", "char_count": <int>}},
                       {{"text": "<max 90 chars>", "char_count": <int>}}],
      "display_url_path": "/reviews"
    }}
  ],
  "recommended_extensions": {{
    "sitelinks": ["<sitelink1>", "<sitelink2>", "<sitelink3>", "<sitelink4>"],
    "callouts": ["<callout1>", "<callout2>", "<callout3>"],
    "structured_snippets": ["<snippet1>", "<snippet2>"]
  }},
  "campaign_settings": {{
    "campaign_type": "Search",
    "ad_rotation": "Optimize: Prefer best performing ads",
    "keyword_match_types": ["Phrase match", "Exact match"],
    "negative_keywords": ["<neg1>", "<neg2>", "<neg3>"],
    "landing_page_recommendation": "<recommendation>"
  }}
}}"""
