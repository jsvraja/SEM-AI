import { BASE } from '../api_config'
import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend, PieChart, Pie, Cell
} from 'recharts'
import { RefreshCw, TrendingUp, Users, ShoppingCart, DollarSign, ExternalLink, Zap } from 'lucide-react'


function Card({ children, style }) {
  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: '12px', padding: '1.25rem', ...style
    }}>{children}</div>
  )
}

function StatCard({ label, value, sub, color, icon: Icon }) {
  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: '12px', padding: '1.25rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
        <div style={{
          width: '32px', height: '32px', borderRadius: '8px',
          background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={15} color={color} />
        </div>
        <span style={{ fontSize: '12px', color: 'var(--text3)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</span>
      </div>
      <div style={{ fontSize: '28px', fontWeight: 600, color, letterSpacing: '-0.02em' }}>{value}</div>
      {sub && <div style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '4px' }}>{sub}</div>}
    </div>
  )
}

const CUSTOM_TOOLTIP = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--bg3)', border: '1px solid var(--border)',
      borderRadius: '8px', padding: '10px 14px', fontSize: '12px',
    }}>
      <div style={{ color: 'var(--text2)', marginBottom: '6px', fontWeight: 500 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: p.color, display: 'inline-block' }} />
          {p.name}: <strong>{p.value}</strong>
        </div>
      ))}
    </div>
  )
}


function GA4ConnectCard({ sessionId, onConnected }) {
  const [propertyId, setPropertyId] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState(null)

  useEffect(() => {
    if (!sessionId) return
    fetch(`${BASE}/api/ga4/status?session_id=${sessionId}`)
      .then(r => r.json())
      .then(d => { if (d.connected) setStatus(d) })
  }, [sessionId])

  async function handleConnect() {
    if (!propertyId.trim()) return alert('GA4 Property ID enter pannunga')
    setLoading(true)
    try {
      const res = await fetch(`${BASE}/api/ga4/auth?session_id=${sessionId}&property_id=${propertyId}`)
      const data = await res.json()
      if (data.auth_url) window.location.href = data.auth_url
    } catch(e) {
      alert('Connection failed')
    }
    setLoading(false)
  }

  if (status?.connected) return (
    <div style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '12px', padding: '1rem 1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span style={{ fontSize: '20px' }}>📊</span>
        <div>
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#4ade80' }}>Google Analytics 4 Connected</div>
          <div style={{ fontSize: '11px', color: 'var(--text3)' }}>Property: {status.property_id}</div>
        </div>
      </div>
      <button onClick={onConnected} style={{ fontSize: '11px', padding: '4px 12px', borderRadius: '6px', background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.3)', color: '#4ade80', cursor: 'pointer', fontWeight: 600 }}>Load GA4 Data</button>
    </div>
  )

  return (
    <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
        <span style={{ fontSize: '20px' }}>📊</span>
        <div>
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>Connect Google Analytics 4</div>
          <div style={{ fontSize: '12px', color: 'var(--text3)' }}>Real AI traffic data from your GA4 property</div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          value={propertyId}
          onChange={e => setPropertyId(e.target.value)}
          placeholder="GA4 Property ID (e.g. 123456789)"
          style={{ flex: 1, padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg3)', color: 'var(--text)', fontSize: '13px', outline: 'none' }}
        />
        <button onClick={handleConnect} disabled={loading} style={{ padding: '8px 16px', borderRadius: '8px', background: 'var(--accent)', border: 'none', color: '#fff', fontSize: '13px', fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}>
          {loading ? 'Connecting...' : '🔗 Connect GA4'}
        </button>
      </div>
      <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '8px' }}>
        💡 GA4 Property ID: Google Analytics → Admin → Property Settings → Property ID
      </div>
    </div>
  )
}

export default function AITraffic() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(14)
  const [loadingDemo, setLoadingDemo] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => { fetchStats() }, [days])

  async function fetchStats() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${BASE}/api/ai-traffic?days=${days}`)
      if (!res.ok) throw new Error('Failed to fetch')
      const data = await res.json()
      setStats(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadDemo() {
    setLoadingDemo(true)
    try {
      await fetch(`${BASE}/api/ai-traffic/demo`, { method: 'POST' })
      await fetchStats()
    } finally {
      setLoadingDemo(false)
    }
  }

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text3)' }}>
      <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 12px', display: 'block' }} />
      Loading AI traffic data...
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )

  if (error) return (
    <Card>
      <div style={{ textAlign: 'center', padding: '2rem', color: '#f87171' }}>
        Failed to load: {error}
        <br />
        <button onClick={fetchStats} style={{ marginTop: '12px', padding: '8px 16px', background: 'var(--accent)', border: 'none', borderRadius: '7px', color: 'white', cursor: 'pointer', fontSize: '13px' }}>
          Retry
        </button>
      </div>
    </Card>
  )

  const isEmpty = !stats || stats.total_visits === 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '3px' }}>AI Platform Traffic</h2>
          <p style={{ fontSize: '12px', color: 'var(--text3)' }}>
            Visitors from ChatGPT, Perplexity, Claude, Gemini and other AI platforms
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <select
            value={days}
            onChange={e => setDays(Number(e.target.value))}
            style={{
              background: 'var(--bg3)', border: '1px solid var(--border)',
              borderRadius: '7px', padding: '6px 10px', color: 'var(--text)',
              fontSize: '13px', outline: 'none', cursor: 'pointer',
            }}
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button onClick={fetchStats} style={{
            background: 'none', border: '1px solid var(--border)', borderRadius: '7px',
            padding: '6px 10px', color: 'var(--text2)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px',
          }}>
            <RefreshCw size={12} /> Refresh
          </button>
        </div>
      </div>

      {/* Empty state */}
      {isEmpty && (
        <Card>
          <div style={{ textAlign: 'center', padding: '2.5rem 1rem' }}>
            <div style={{
              width: '60px', height: '60px', borderRadius: '16px',
              background: 'rgba(79,125,255,0.08)', border: '1px solid rgba(79,125,255,0.15)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 1rem',
            }}>
              <Zap size={28} color="var(--accent)" />
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>No AI traffic yet</h3>
            <p style={{ fontSize: '13px', color: 'var(--text2)', marginBottom: '1.5rem', lineHeight: 1.6, maxWidth: '420px', margin: '0 auto 1.5rem' }}>
              Add the tracking snippet to your website to start capturing visitors from ChatGPT, Perplexity, Claude, and other AI platforms.
            </p>

            {/* Tracking snippet */}
            <div style={{
              background: 'var(--bg3)', borderRadius: '10px', padding: '14px',
              border: '1px solid var(--border)', textAlign: 'left', marginBottom: '1.5rem',
            }}>
              <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '8px', fontWeight: 500, letterSpacing: '0.04em' }}>
                ADD TO YOUR WEBSITE — paste before &lt;/body&gt;
              </div>
              <pre style={{
                fontSize: '11px', color: 'var(--cyan)', overflowX: 'auto',
                fontFamily: 'var(--mono)', lineHeight: 1.6, margin: 0,
              }}>{`<script>
(function() {
  var ref = document.referrer;
  var aiDomains = [
    'chat.openai.com','chatgpt.com',
    'perplexity.ai','claude.ai',
    'gemini.google.com','copilot.microsoft.com',
    'grok.x.ai','you.com','meta.ai'
  ];
  var isAI = aiDomains.some(function(d) {
    return ref.indexOf(d) > -1;
  });
  if (isAI) {
    fetch('https://sem-ai-production.up.railway.app/api/track', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        referrer: ref,
        page: window.location.pathname
      })
    });
  }
})();
</script>`}</pre>
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <button onClick={loadDemo} disabled={loadingDemo} style={{
                padding: '10px 20px', background: 'var(--accent)', border: 'none',
                borderRadius: '8px', color: 'white', fontSize: '13px', fontWeight: 500,
                cursor: loadingDemo ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', gap: '6px',
              }}>
                {loadingDemo
                  ? <><RefreshCw size={13} style={{ animation: 'spin 1s linear infinite' }} /> Loading...</>
                  : <><Zap size={13} /> Load Demo Data</>
                }
              </button>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '10px' }}>
              Load demo data to preview the dashboard
            </p>
          </div>
        </Card>
      )}

      {/* Stats with data */}
      {!isEmpty && stats && (
        <>
          {/* KPI Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
            <StatCard label="Total Visits" value={stats.total_visits.toLocaleString()} sub={`Last ${days} days`} color="var(--accent)" icon={Users} />
            <StatCard label="Conversions" value={stats.total_conversions.toLocaleString()} sub={`${stats.overall_conversion_rate}% rate`} color="var(--green)" icon={ShoppingCart} />
            <StatCard label="Revenue from AI" value={`$${stats.total_conversion_value.toFixed(2)}`} sub="Conversion value" color="var(--cyan)" icon={DollarSign} />
            <StatCard label="AI Sources" value={stats.platforms.length} sub="Platforms sending traffic" color="var(--yellow)" icon={TrendingUp} />
          </div>

          {/* Platform breakdown + Pie */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Card>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '1rem' }}>
                Platform Breakdown
              </div>
              {stats.platforms.map((p, i) => (
                <div key={p.id} style={{ marginBottom: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: p.color }} />
                      <span style={{ fontWeight: 500 }}>{p.name}</span>
                    </div>
                    <div style={{ display: 'flex', gap: '12px', color: 'var(--text2)' }}>
                      <span>{p.visits} visits</span>
                      <span style={{ color: 'var(--green)' }}>{p.conversion_rate}% CVR</span>
                    </div>
                  </div>
                  <div style={{ height: '6px', background: 'var(--bg4)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%', borderRadius: '3px',
                      width: `${stats.total_visits > 0 ? (p.visits / stats.total_visits * 100) : 0}%`,
                      background: p.color, transition: 'width 0.5s',
                    }} />
                  </div>
                </div>
              ))}
            </Card>

            <Card>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '1rem' }}>
                Traffic Share
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={stats.platforms}
                    dataKey="visits"
                    nameKey="name"
                    cx="50%" cy="50%"
                    innerRadius={50} outerRadius={80}
                    paddingAngle={2}
                  >
                    {stats.platforms.map((p, i) => (
                      <Cell key={i} fill={p.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }} />
                  <Legend iconSize={10} wrapperStyle={{ fontSize: '12px', color: 'var(--text2)' }} />
                </PieChart>
              </ResponsiveContainer>
            </Card>
          </div>

          {/* Daily trend */}
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '1rem' }}>
              Daily Trend (Last 14 Days)
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={stats.daily_trend} margin={{ left: -20, right: 10 }}>
                <XAxis dataKey="date" tick={{ fill: 'var(--text3)', fontSize: 10 }} tickFormatter={d => d.slice(5)} />
                <YAxis tick={{ fill: 'var(--text3)', fontSize: 10 }} />
                <Tooltip content={<CUSTOM_TOOLTIP />} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: '11px', color: 'var(--text2)' }} />
                {stats.platforms.slice(0, 5).map(p => (
                  <Line
                    key={p.id}
                    type="monotone"
                    dataKey={p.id}
                    name={p.name}
                    stroke={p.color}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Top pages */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Card>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '1rem' }}>
                Top Landing Pages
              </div>
              {stats.top_pages.map((p, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '8px 0', borderBottom: '1px solid var(--border)',
                  fontSize: '13px',
                }}>
                  <div>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--accent)' }}>{p.page}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>
                      {p.platforms.slice(0, 3).join(', ')}
                    </div>
                  </div>
                  <span style={{
                    background: 'var(--bg3)', padding: '3px 8px', borderRadius: '4px',
                    fontSize: '12px', fontWeight: 500, color: 'var(--text2)',
                  }}>{p.visits}</span>
                </div>
              ))}
            </Card>

            {/* Recent visits */}
            <Card>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '1rem' }}>
                Recent Visits
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {stats.recent_visits.slice(0, 8).map((v, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: '8px',
                    padding: '7px 10px', background: 'var(--bg3)',
                    borderRadius: '7px', border: '1px solid var(--border)',
                  }}>
                    <div style={{
                      width: '8px', height: '8px', borderRadius: '50%', flexShrink: 0,
                      background: v.platform_color,
                    }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '12px', fontWeight: 500 }}>{v.platform_name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text3)', fontFamily: 'var(--mono)' }}>{v.page}</div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      {v.converted && (
                        <span style={{ fontSize: '10px', background: 'rgba(34,197,94,0.12)', color: '#4ade80', padding: '2px 6px', borderRadius: '3px', display: 'block', marginBottom: '2px' }}>
                          Converted
                        </span>
                      )}
                      <div style={{ fontSize: '10px', color: 'var(--text3)' }}>
                        {new Date(v.timestamp).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Keywords */}
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '1rem' }}>
              Search Keywords
            </div>
            {!stats.top_keywords?.length ? (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text3)', fontSize: '12px', lineHeight: 1.7 }}>
                No keywords tracked yet.<br/>
                Share links with <code style={{color:'var(--accent)', background:'var(--bg3)', padding:'2px 6px', borderRadius:'4px'}}>?utm_source=chatgpt&amp;utm_term=your+keyword</code>
              </div>
            ) : stats.top_keywords.slice(0, 10).map((k, i) => (
              <div key={i} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: '13px',
              }}>
                <div>
                  <div style={{ fontWeight: 500, color: 'var(--text)' }}>"{k.keyword}"</div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>
                    {k.platforms.slice(0, 2).join(', ')}
                    {k.conversions > 0 && <span style={{ color: 'var(--green)', marginLeft: '6px' }}>✓ {k.conversions} converted</span>}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontWeight: 600, color: 'var(--accent)', fontSize: '15px' }}>{k.visits}</div>
                  <div style={{ fontSize: '10px', color: 'var(--text3)' }}>visits</div>
                </div>
              </div>
            ))}
          </Card>

          {/* Impressions */}
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '6px' }}>
              Impressions by Platform
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px' }}>
              Total visits (impressions) per AI platform
            </div>
            {(stats.platforms || []).map((p, i) => (
              <div key={i} style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: p.color }} />
                    <span style={{ fontWeight: 500 }}>{p.name}</span>
                  </div>
                  <span style={{ color: 'var(--text2)', fontWeight: 500 }}>{p.visits.toLocaleString()} impressions</span>
                </div>
                <div style={{ height: '6px', background: 'var(--bg4)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', borderRadius: '3px',
                    width: `${stats.total_visits > 0 ? (p.visits / stats.total_visits * 100) : 0}%`,
                    background: p.color, transition: 'width 0.5s',
                  }} />
                </div>
              </div>
            ))}
          </Card>

          {/* Tracking snippet */}
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <ExternalLink size={14} color="var(--accent)" />
              <span style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                Tracking Snippet
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text3)' }}>— Add to your website</span>
            </div>
            <pre style={{
              fontSize: '11px', color: 'var(--cyan)', overflowX: 'auto',
              fontFamily: 'var(--mono)', lineHeight: 1.6, margin: 0,
              background: 'var(--bg3)', padding: '12px', borderRadius: '8px',
              border: '1px solid var(--border)',
            }}>{`<script>
(function() {
  var ref = document.referrer;
  var aiDomains = [
    'chat.openai.com','chatgpt.com','perplexity.ai',
    'claude.ai','gemini.google.com','copilot.microsoft.com',
    'grok.x.ai','you.com','meta.ai'
  ];
  var isAI = aiDomains.some(function(d) { return ref.indexOf(d) > -1; });
  if (isAI) {
    fetch('https://sem-ai-production.up.railway.app/api/track', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ referrer: ref, page: window.location.pathname })
    });
  }
})();
</script>`}</pre>
            <p style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '8px' }}>
              Replace <code style={{ color: 'var(--accent)' }}>YOUR_BACKEND_URL</code> with your deployed backend URL. Paste this before the &lt;/body&gt; tag on every page.
            </p>
          </Card>
        </>
      )}
    </div>
  )
}
