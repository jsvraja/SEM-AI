import { useState, useEffect } from "react"
import { Search, TrendingUp, MousePointer, Eye, ExternalLink, CheckCircle } from "lucide-react"

const BASE = "https://sem-ai-production.up.railway.app"

export default function SearchConsole({ sessionId: propSessionId, url }) {
  const sessionId = propSessionId || localStorage.getItem("sem_session_id") || localStorage.getItem("gsc_session_id") || (() => {
    const newId = "gsc_" + Math.random().toString(36).slice(2)
    localStorage.setItem("gsc_session_id", newId)
    return newId
  })()
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [activeTab, setActiveTab] = useState("opportunities")
  const [insights, setInsights] = useState(null)
  const [loadingInsights, setLoadingInsights] = useState(false)

  useEffect(() => {
    // Check if returning from OAuth redirect
    const params = new URLSearchParams(window.location.search)
    if (params.get("gsc_connected") === "1") {
      // Clean URL
      window.history.replaceState({}, "", window.location.pathname)
    }
    checkStatus()
  }, [])

  const checkStatus = async () => {
    setLoading(true)
    try {
      const gscToken = localStorage.getItem("gsc_token")
      if (gscToken) {
        setConnected(true)
        fetchData()
      } else {
        setConnected(false)
        setLoading(false)
      }
    } catch { setLoading(false) }
  }

  const connect = async () => {
    try {
      const res = await fetch(BASE + "/api/search-console/auth?session_id=" + sessionId)
      const d = await res.json()
      if (d.auth_url) {
        localStorage.setItem("gsc_session_id", sessionId)
        localStorage.setItem("gsc_return_tab", "search-console")
        window.location.href = d.auth_url
      } else {
        alert("Google Search Console integration coming soon! Please check back later.")
      }
    } catch(e) { 
      alert("Google Search Console integration coming soon! Please check back later.")
    }
  }

  // Auto-fetch if already connected
  useEffect(() => {
    const gscToken = localStorage.getItem("gsc_token")
    if (gscToken && url) fetchData()
  }, [url])

  const fetchData = async () => {
    setLoading(true)
    try {
      let gscToken = localStorage.getItem("gsc_token") || ""
      
      // Try to refresh token if we have refresh token
      const refreshToken = localStorage.getItem("gsc_refresh_token") || ""
      if (refreshToken) {
        try {
          const refreshRes = await fetch(BASE + "/api/search-console/refresh-token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken })
          })
          const refreshData = await refreshRes.json()
          if (refreshData.access_token) {
            gscToken = refreshData.access_token
            localStorage.setItem("gsc_token", gscToken)
          }
        } catch(e) { console.error("Token refresh failed:", e) }
      }

      const token = localStorage.getItem("sem_token") || ""
      const res = await fetch(BASE + "/api/search-console/data", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify({ session_id: sessionId, url, days: 28, gsc_token: gscToken })
      })
      const d = await res.json()
      if (d && (d.keywords !== undefined || d.pages !== undefined)) {
        setData(d)
        setConnected(true)
        generateInsights(d)
      }
    } catch(e) { console.error(e) }
    setLoading(false)
  }

  const generateInsights = async (gscData) => {
    setLoadingInsights(true)
    try {
      const token = localStorage.getItem("sem_token") || ""
      const res = await fetch(BASE + "/api/search-console/insights", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify({ session_id: sessionId, url, data: gscData })
      })
      const d = await res.json()
      setInsights(d)
    } catch(e) { console.error(e) }
    setLoadingInsights(false)
  }

  const [aiInsights, setAiInsights] = useState(null)
  const [loadingInsights2, setLoadingInsights2] = useState(false)

  const generateAIInsights = async () => {
    if (!data) return
    setLoadingInsights2(true)
    try {
      const res = await fetch(BASE + "/api/search-console/ai-insights", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          keywords: data.keywords || [],
          pages: data.pages || [],
          summary: data.summary || {},
          url: url
        })
      })
      const d = await res.json()
      setAiInsights(d)
    } catch(e) { console.error(e) }
    setLoadingInsights2(false)
  }

  const fmt = (n) => n >= 1000 ? (n/1000).toFixed(1) + "k" : String(n)
  const pct = (n) => (n * 100).toFixed(1) + "%"
  const pos = (n) => Number(n).toFixed(1)

  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "300px", color: "var(--text3)" }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: "32px", marginBottom: "12px" }}>loading</div>
        <p>Loading Search Console data...</p>
      </div>
    </div>
  )

  if (!connected) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "400px" }}>
      <div style={{ textAlign: "center", maxWidth: "420px" }}>
        <div style={{ width: "72px", height: "72px", borderRadius: "50%", background: "var(--accent-bg)", border: "2px solid var(--accent-border)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px", fontSize: "32px" }}>search</div>
        <h2 style={{ fontSize: "22px", fontWeight: 700, marginBottom: "10px" }}>Connect Google Search Console</h2>
        <p style={{ fontSize: "14px", color: "var(--text3)", marginBottom: "28px", lineHeight: 1.6 }}>
          Real keyword data, clicks & impressions — find AI-powered SEO opportunities
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "28px", textAlign: "left" }}>
          {["Keyword Opportunities", "CTR Optimizer", "Content Gaps", "SEM + SEO Connect"].map(f => (
            <div key={f} style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 14px", fontSize: "13px", display: "flex", alignItems: "center", gap: "8px" }}>
              <CheckCircle size={14} color="var(--accent)" /> {f}
            </div>
          ))}
        </div>
        <button onClick={connect} style={{ padding: "12px 32px", background: "var(--accent)", border: "none", borderRadius: "10px", color: "white", fontSize: "15px", fontWeight: 600, cursor: "pointer" }}>
          Connect Search Console
        </button>
      </div>
    </div>
  )

  const keywords = data?.keywords || []
  const pages = data?.pages || []
  const summary = data?.summary || {}

  const opportunities = keywords.filter(k => k.position >= 4 && k.position <= 20 && k.impressions > 10).sort((a,b) => b.impressions - a.impressions).slice(0,15)
  const lowCTR = keywords.filter(k => k.ctr < 0.03 && k.impressions > 50).sort((a,b) => b.impressions - a.impressions).slice(0,15)
  const contentGaps = keywords.filter(k => k.impressions > 100 && k.clicks < 5).sort((a,b) => b.impressions - a.impressions).slice(0,15)
  const semOpp = keywords.filter(k => k.position > 10 && k.impressions > 30).sort((a,b) => b.impressions - a.impressions).slice(0,10)

  const subTabs = [
    { id: "opportunities", label: "Opportunities", count: opportunities.length },
    { id: "ctr", label: "CTR Optimizer", count: lowCTR.length },
    { id: "gaps", label: "Content Gaps", count: contentGaps.length },
    { id: "sem", label: "SEM Connect", count: semOpp.length },
    { id: "pages", label: "Top Pages", count: pages.length },
  ]

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "1rem" }}>
        {[
          { label: "Total Clicks", value: fmt(summary.total_clicks || summary.clicks || 0), color: "var(--accent)" },
          { label: "Impressions", value: fmt(summary.total_impressions || summary.impressions || 0), color: "var(--blue, #3b82f6)" },
          { label: "Avg CTR", value: pct(summary.avg_ctr || summary.ctr || 0), color: "var(--green)" },
          { label: "Avg Position", value: pos(summary.avg_position || summary.position || 0), color: "var(--yellow)" },
        ].map(c => (
          <div key={c.label} style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: "12px", padding: "16px" }}>
            <div style={{ fontSize: "11px", color: "var(--text3)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>{c.label}</div>
            <div style={{ fontSize: "24px", fontWeight: 700, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: "11px", color: "var(--text3)", marginTop: "4px" }}>Last 28 days</div>
          </div>
        ))}
      </div>

      {loadingInsights && (
        <div style={{ background: "var(--accent-bg)", border: "1px solid var(--accent-border)", borderRadius: "12px", padding: "16px", fontSize: "13px", color: "var(--accent)" }}>
          AI இந்த data analyze pannudhu... insights ready aagum
        </div>
      )}
      {insights?.summary && (
        <div style={{ background: "var(--accent-bg)", border: "1px solid var(--accent-border)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "12px", color: "var(--accent)", fontWeight: 600, marginBottom: "8px" }}>AI Summary</div>
          <p style={{ fontSize: "14px", color: "var(--text)", lineHeight: 1.6 }}>{insights.summary}</p>
        </div>
      )}

      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
        {/* AI Insights Button */}
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "16px" }}>
          <button onClick={generateAIInsights} disabled={loadingInsights2} style={{
            padding: "10px 20px", background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            border: "none", borderRadius: "8px", color: "white", fontSize: "13px",
            fontWeight: 600, cursor: loadingInsights2 ? "not-allowed" : "pointer",
            display: "flex", alignItems: "center", gap: "8px", opacity: loadingInsights2 ? 0.7 : 1
          }}>
            {loadingInsights2 ? "⏳ Analyzing..." : "✨ Generate AI Insights"}
          </button>
        </div>

        {/* AI Insights Panel */}
        {aiInsights && (
          <div style={{ background: "var(--bg2)", border: "1px solid var(--accent-border)", borderRadius: "12px", padding: "20px", marginBottom: "20px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 700, marginBottom: "12px", color: "var(--accent)" }}>✨ AI Analysis</h3>
            <p style={{ fontSize: "13px", color: "var(--text2)", marginBottom: "16px", lineHeight: 1.6 }}>{aiInsights.overall_assessment}</p>
            {aiInsights.quick_wins?.length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <h4 style={{ fontSize: "13px", fontWeight: 600, marginBottom: "8px" }}>⚡ Quick Wins</h4>
                {aiInsights.quick_wins.map((w, i) => (
                  <div key={i} style={{ background: "var(--bg)", borderRadius: "8px", padding: "10px 14px", marginBottom: "8px", borderLeft: "3px solid var(--accent)" }}>
                    <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "4px" }}>{w.title}</div>
                    <div style={{ fontSize: "12px", color: "var(--text3)" }}>{w.description}</div>
                    <div style={{ display: "flex", gap: "8px", marginTop: "6px" }}>
                      <span style={{ fontSize: "11px", padding: "2px 8px", borderRadius: "10px", background: w.impact === "high" ? "#fee2e2" : "#fef9c3", color: w.impact === "high" ? "#ef4444" : "#ca8a04" }}>{w.impact} impact</span>
                      <span style={{ fontSize: "11px", padding: "2px 8px", borderRadius: "10px", background: "var(--bg3)", color: "var(--text3)" }}>{w.effort} effort</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {aiInsights.sem_opportunities?.length > 0 && (
              <div>
                <h4 style={{ fontSize: "13px", fontWeight: 600, marginBottom: "8px" }}>🎯 SEM Opportunities</h4>
                {aiInsights.sem_opportunities.map((s, i) => (
                  <div key={i} style={{ background: "var(--bg)", borderRadius: "8px", padding: "10px 14px", marginBottom: "8px", borderLeft: "3px solid #22c55e" }}>
                    <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "4px" }}>{s.keyword}</div>
                    <div style={{ fontSize: "12px", color: "var(--text3)" }}>{s.reason}</div>
                    {s.suggested_bid && <div style={{ fontSize: "11px", color: "#22c55e", marginTop: "4px" }}>Suggested bid: {s.suggested_bid}</div>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {subTabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            padding: "8px 16px", borderRadius: "8px", border: "1px solid",
            borderColor: activeTab === t.id ? "var(--accent)" : "var(--border)",
            background: activeTab === t.id ? "var(--accent-bg)" : "transparent",
            color: activeTab === t.id ? "var(--accent)" : "var(--text3)",
            fontSize: "13px", cursor: "pointer", fontWeight: activeTab === t.id ? 600 : 400,
          }}>
            {t.label} <span style={{ background: "var(--bg3)", borderRadius: "99px", padding: "1px 7px", fontSize: "11px", marginLeft: "4px" }}>{t.count}</span>
          </button>
        ))}
      </div>

      {activeTab === "opportunities" && (
        <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: "12px", overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 600 }}>Keyword Opportunities</h3>
            <p style={{ fontSize: "12px", color: "var(--text3)", marginTop: "4px" }}>Keywords ranking position 4-20 — optimize to reach page 1</p>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr style={{ background: "var(--bg3)" }}>
                {["Keyword","Position","Clicks","Impressions","CTR","Potential"].map(h => (
                  <th key={h} style={{ padding: "10px 16px", textAlign: "left", fontSize: "11px", color: "var(--text3)", fontWeight: 600, textTransform: "uppercase" }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {opportunities.map((k,i) => {
                  const potential = Math.round(k.impressions * 0.15) - k.clicks
                  const posColor = k.position <= 10 ? "var(--green)" : k.position <= 15 ? "var(--yellow)" : "var(--red)"
                  return (
                    <tr key={i} style={{ borderTop: "1px solid var(--border)" }}>
                      <td style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500 }}>{k.query}</td>
                      <td style={{ padding: "12px 16px" }}><span style={{ background: posColor + "22", color: posColor, padding: "2px 8px", borderRadius: "99px", fontSize: "12px", fontWeight: 600 }}>#{pos(k.position)}</span></td>
                      <td style={{ padding: "12px 16px", fontSize: "13px" }}>{k.clicks}</td>
                      <td style={{ padding: "12px 16px", fontSize: "13px" }}>{fmt(k.impressions)}</td>
                      <td style={{ padding: "12px 16px", fontSize: "13px" }}>{pct(k.ctr)}</td>
                      <td style={{ padding: "12px 16px" }}><span style={{ color: "var(--green)", fontSize: "12px", fontWeight: 600 }}>+{potential} clicks</span></td>
                    </tr>
                  )
                })}
                {opportunities.length === 0 && <tr><td colSpan={6} style={{ padding: "32px", textAlign: "center", color: "var(--text3)" }}>No opportunities found</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "ctr" && (
        <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: "12px", overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 600 }}>CTR Optimizer</h3>
            <p style={{ fontSize: "12px", color: "var(--text3)", marginTop: "4px" }}>Low CTR keywords — optimize title/meta to increase clicks</p>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr style={{ background: "var(--bg3)" }}>
                {["Keyword","Impressions","Clicks","CTR","Target","Action"].map(h => (
                  <th key={h} style={{ padding: "10px 16px", textAlign: "left", fontSize: "11px", color: "var(--text3)", fontWeight: 600, textTransform: "uppercase" }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {lowCTR.map((k,i) => (
                  <tr key={i} style={{ borderTop: "1px solid var(--border)" }}>
                    <td style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500 }}>{k.query}</td>
                    <td style={{ padding: "12px 16px", fontSize: "13px" }}>{fmt(k.impressions)}</td>
                    <td style={{ padding: "12px 16px", fontSize: "13px" }}>{k.clicks}</td>
                    <td style={{ padding: "12px 16px" }}><span style={{ color: "var(--red)", fontWeight: 600, fontSize: "13px" }}>{pct(k.ctr)}</span></td>
                    <td style={{ padding: "12px 16px", color: "var(--green)", fontSize: "13px", fontWeight: 600 }}>3-5%</td>
                    <td style={{ padding: "12px 16px" }}><span style={{ background: "var(--accent-bg)", color: "var(--accent)", border: "1px solid var(--accent-border)", padding: "3px 10px", borderRadius: "6px", fontSize: "11px", fontWeight: 600 }}>Optimize</span></td>
                  </tr>
                ))}
                {lowCTR.length === 0 && <tr><td colSpan={6} style={{ padding: "32px", textAlign: "center", color: "var(--text3)" }}>CTR is good</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "gaps" && (
        <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: "12px", overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 600 }}>Content Gaps</h3>
            <p style={{ fontSize: "12px", color: "var(--text3)", marginTop: "4px" }}>Keywords users search for — but your site lacks content for</p>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr style={{ background: "var(--bg3)" }}>
                {["Keyword","Impressions","Clicks","Position","Action"].map(h => (
                  <th key={h} style={{ padding: "10px 16px", textAlign: "left", fontSize: "11px", color: "var(--text3)", fontWeight: 600, textTransform: "uppercase" }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {contentGaps.map((k,i) => (
                  <tr key={i} style={{ borderTop: "1px solid var(--border)" }}>
                    <td style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500 }}>{k.query}</td>
                    <td style={{ padding: "12px 16px", fontSize: "13px", color: "var(--accent)", fontWeight: 600 }}>{fmt(k.impressions)}</td>
                    <td style={{ padding: "12px 16px", fontSize: "13px", color: "var(--red)" }}>{k.clicks}</td>
                    <td style={{ padding: "12px 16px", fontSize: "13px" }}>#{pos(k.position)}</td>
                    <td style={{ padding: "12px 16px" }}><span style={{ background: "var(--bg3)", color: "var(--yellow, #ca8a04)", border: "1px solid var(--border)", padding: "3px 10px", borderRadius: "6px", fontSize: "11px", fontWeight: 600 }}>Create Content</span></td>
                  </tr>
                ))}
                {contentGaps.length === 0 && <tr><td colSpan={5} style={{ padding: "32px", textAlign: "center", color: "var(--text3)" }}>No gaps found</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "sem" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: "12px", padding: "16px 20px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 600, marginBottom: "4px" }}>SEM + SEO Connect</h3>
            <p style={{ fontSize: "12px", color: "var(--text3)" }}>Keywords not ranking organically — run Google Ads for instant traffic</p>
          </div>
          {semOpp.map((k,i) => (
            <div key={i} style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: "12px", padding: "16px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "16px" }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "4px" }}>{k.query}</div>
                <div style={{ fontSize: "12px", color: "var(--text3)" }}>Position #{pos(k.position)} - {fmt(k.impressions)} impressions - {k.clicks} clicks</div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", flexShrink: 0 }}>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "11px", color: "var(--text3)" }}>Est. Ad clicks</div>
                  <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--accent)" }}>+{Math.round(k.impressions * 0.05)}/mo</div>
                </div>
                <button style={{ padding: "8px 16px", background: "var(--accent)", border: "none", borderRadius: "8px", color: "white", fontSize: "12px", fontWeight: 600, cursor: "pointer" }}>Create Ad</button>
              </div>
            </div>
          ))}
          {semOpp.length === 0 && <div style={{ textAlign: "center", padding: "32px", color: "var(--text3)", fontSize: "13px" }}>No SEM opportunities</div>}
        </div>
      )}

      {activeTab === "pages" && (
        <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: "12px", overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 600 }}>Top Pages</h3>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr style={{ background: "var(--bg3)" }}>
                {["Page","Clicks","Impressions","CTR","Position"].map(h => (
                  <th key={h} style={{ padding: "10px 16px", textAlign: "left", fontSize: "11px", color: "var(--text3)", fontWeight: 600, textTransform: "uppercase" }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {pages.slice(0,20).map((p,i) => (
                  <tr key={i} style={{ borderTop: "1px solid var(--border)" }}>
                    <td style={{ padding: "12px 16px", fontSize: "12px", maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      <a href={p.page} target="_blank" rel="noreferrer" style={{ color: "var(--accent)", textDecoration: "none" }}>
                        {p.page.replace(/^https?:\/\/[^/]+/, "") || "/"}
                      </a>
                    </td>
                    <td style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 600 }}>{p.clicks}</td>
                    <td style={{ padding: "12px 16px", fontSize: "13px" }}>{fmt(p.impressions)}</td>
                    <td style={{ padding: "12px 16px", fontSize: "13px" }}>{pct(p.ctr)}</td>
                    <td style={{ padding: "12px 16px", fontSize: "13px" }}>#{pos(p.position)}</td>
                  </tr>
                ))}
                {pages.length === 0 && <tr><td colSpan={5} style={{ padding: "32px", textAlign: "center", color: "var(--text3)" }}>No page data</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
