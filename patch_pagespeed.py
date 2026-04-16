import os

# 1. Patch backend - add PageSpeed endpoint
backend_path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(backend_path) as f:
    content = f.read()

pagespeed_endpoint = '''
@app.post("/api/pagespeed")
async def get_pagespeed(request: Request):
    """Fetch real PageSpeed Insights scores from Google API."""
    try:
        body = await request.json()
        url = body.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="URL required")
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        api_key = os.environ.get("PAGESPEED_API_KEY", "")
        if not api_key:
            return {"error": "PageSpeed API key not configured"}

        results = {}
        async with httpx.AsyncClient(timeout=30) as client:
            for strategy in ["mobile", "desktop"]:
                psi_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy={strategy}&key={api_key}&category=performance&category=accessibility&category=best-practices&category=seo"
                resp = await client.get(psi_url)
                data = resp.json()

                if "error" in data:
                    results[strategy] = {"error": data["error"].get("message", "API error")}
                    continue

                cats = data.get("lighthouseResult", {}).get("categories", {})
                audits = data.get("lighthouseResult", {}).get("audits", {})

                results[strategy] = {
                    "performance": round((cats.get("performance", {}).get("score", 0) or 0) * 100),
                    "accessibility": round((cats.get("accessibility", {}).get("score", 0) or 0) * 100),
                    "best_practices": round((cats.get("best-practices", {}).get("score", 0) or 0) * 100),
                    "seo": round((cats.get("seo", {}).get("score", 0) or 0) * 100),
                    "fcp": audits.get("first-contentful-paint", {}).get("displayValue", "N/A"),
                    "lcp": audits.get("largest-contentful-paint", {}).get("displayValue", "N/A"),
                    "cls": audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
                    "tbt": audits.get("total-blocking-time", {}).get("displayValue", "N/A"),
                    "speed_index": audits.get("speed-index", {}).get("displayValue", "N/A"),
                }

        return {"url": url, "results": results}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

'''

# Insert before agent routes
marker = '@app.get("/api/agent/status")'
if marker in content:
    content = content.replace(marker, pagespeed_endpoint + marker)
    print("Backend endpoint added!")
else:
    print("ERROR: marker not found")

with open(backend_path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(backend_path, doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print("Syntax ERROR:", e)

# 2. Patch Dashboard - add PageSpeed section in Overview
dash_path = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(dash_path) as f:
    dcontent = f.read()

# Add pagespeed state after recommendedPages state
old_state = "  const [recommendedPages, setRecommendedPages] = useState([])"
new_state = """  const [recommendedPages, setRecommendedPages] = useState([])
  const [pageSpeed, setPageSpeed] = useState(null)
  const [loadingSpeed, setLoadingSpeed] = useState(false)"""
dcontent = dcontent.replace(old_state, new_state)

# Add PageSpeed card after AI Summary in overview
old_summary = """            {seo.overall_summary && (
              <Card>
                <SectionTitle icon={Zap}>AI Summary</SectionTitle>
                <p style={{ fontSize: '14px', color: 'var(--text2)', lineHeight: 1.7 }}>{seo.overall_summary}</p>
              </Card>
            )}"""

new_summary = """            {seo.overall_summary && (
              <Card>
                <SectionTitle icon={Zap}>AI Summary</SectionTitle>
                <p style={{ fontSize: '14px', color: 'var(--text2)', lineHeight: 1.7 }}>{seo.overall_summary}</p>
              </Card>
            )}

            {/* PageSpeed Insights Card */}
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <SectionTitle icon={BarChart3}>PageSpeed Insights (Google)</SectionTitle>
                {!pageSpeed && !loadingSpeed && (
                  <button onClick={async () => {
                    setLoadingSpeed(true)
                    try {
                      const res = await fetch(`${BASE}/api/pagespeed`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url }),
                      })
                      const data = await res.json()
                      setPageSpeed(data)
                    } catch(e) { console.error(e) }
                    setLoadingSpeed(false)
                  }} style={{ padding: '6px 14px', borderRadius: '7px', background: 'var(--accent)', border: 'none', color: 'white', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>
                    {loadingSpeed ? 'Loading...' : '🚀 Run PageSpeed Test'}
                  </button>
                )}
                {pageSpeed && (
                  <button onClick={() => setPageSpeed(null)} style={{ padding: '4px 10px', borderRadius: '6px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text3)', fontSize: '11px', cursor: 'pointer' }}>↺ Re-run</button>
                )}
              </div>
              {!pageSpeed && !loadingSpeed && (
                <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text3)', fontSize: '13px' }}>
                  Click "Run PageSpeed Test" to get real Performance, SEO, Accessibility scores from Google
                </div>
              )}
              {loadingSpeed && (
                <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text3)', fontSize: '13px' }}>
                  ⏳ Running PageSpeed analysis... (takes 20-30 seconds)
                </div>
              )}
              {pageSpeed && pageSpeed.error && (
                <div style={{ color: 'var(--red)', fontSize: '13px' }}>⚠ {pageSpeed.error}</div>
              )}
              {pageSpeed && pageSpeed.results && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {['mobile', 'desktop'].map(strategy => {
                    const r = pageSpeed.results[strategy]
                    if (!r || r.error) return null
                    return (
                      <div key={strategy}>
                        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                          {strategy === 'mobile' ? '📱 Mobile' : '🖥️ Desktop'}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '8px' }}>
                          {[
                            { label: 'Performance', score: r.performance },
                            { label: 'SEO', score: r.seo },
                            { label: 'Accessibility', score: r.accessibility },
                            { label: 'Best Practices', score: r.best_practices },
                          ].map(({ label, score }) => {
                            const c = score >= 90 ? 'var(--green)' : score >= 50 ? 'var(--yellow)' : 'var(--red)'
                            return (
                              <div key={label} style={{ textAlign: 'center', padding: '10px 6px', background: 'var(--bg3)', borderRadius: '10px', border: `2px solid ${c}` }}>
                                <div style={{ fontSize: '22px', fontWeight: 700, color: c }}>{score}</div>
                                <div style={{ fontSize: '10px', color: 'var(--text3)', textTransform: 'uppercase' }}>{label}</div>
                              </div>
                            )
                          })}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
                          {[
                            { label: 'FCP', val: r.fcp },
                            { label: 'LCP', val: r.lcp },
                            { label: 'CLS', val: r.cls },
                          ].map(({ label, val }) => (
                            <div key={label} style={{ padding: '6px', background: 'var(--bg3)', borderRadius: '6px', textAlign: 'center' }}>
                              <div style={{ fontSize: '13px', fontWeight: 600 }}>{val}</div>
                              <div style={{ fontSize: '10px', color: 'var(--text3)' }}>{label}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                  <div style={{ fontSize: '11px', color: 'var(--text3)', padding: '6px 8px', background: 'var(--bg3)', borderRadius: '6px' }}>
                    🟢 90-100 Good &nbsp;|&nbsp; 🟡 50-89 Needs Improvement &nbsp;|&nbsp; 🔴 0-49 Poor &nbsp;|&nbsp; Powered by Google PageSpeed Insights
                  </div>
                </div>
              )}
            </Card>"""

dcontent = dcontent.replace(old_summary, new_summary)

# Add BASE import
if "import { BASE }" not in dcontent and "from '../api_config'" not in dcontent:
    dcontent = dcontent.replace(
        "import { useState",
        "import { BASE } from '../api_config'\nimport { useState"
    )

with open(dash_path, 'w') as f:
    f.write(dcontent)

# Also update backend copy
dash_path2 = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(dash_path2, 'w') as f:
    f.write(dcontent)

print("Dashboard patched!")
print("Has pageSpeed state:", "pageSpeed" in dcontent)
print("Has pagespeed card:", "PageSpeed Insights" in dcontent)
