import AITraffic from './AITraffic'
import AdCopy from './AdCopy'
import SiteAudit from './SiteAudit'
import SocialMedia from './SocialMedia'
import Competitor from './Competitor'
import AdsManager from './AdsManager'
import ThemeToggle from './ThemeToggle'
import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, PieChart, Pie, Cell, Legend
} from 'recharts'
import {
  ArrowLeft, Globe, CheckCircle, AlertTriangle, XCircle,
  TrendingUp, DollarSign, Target, Megaphone, Users,
  ChevronDown, ChevronUp, ChevronRight, Copy, Check, ExternalLink,
  Zap, Search, BarChart3, Share2
} from 'lucide-react'

function ScoreRing({ score, label, size = 80 }) {
  const color = score >= 75 ? 'var(--green)' : score >= 50 ? 'var(--yellow)' : 'var(--red)'
  const r = (size / 2) - 8
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - score / 100)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
      <svg width={size} height={size}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--bg4)" strokeWidth="6" />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="6"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round" transform={`rotate(-90 ${size/2} ${size/2})`}
          style={{ transition: 'stroke-dashoffset 1s ease' }} />
        <text x={size/2} y={size/2 + 1} textAnchor="middle" dominantBaseline="middle"
          fill={color} fontSize="17" fontWeight="600" fontFamily="'DM Sans', sans-serif">{score}</text>
      </svg>
      <span style={{ fontSize: '11px', color: 'var(--text3)', fontWeight: 500, textAlign: 'center' }}>{label}</span>
    </div>
  )
}

function Card({ children, style }) {
  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: '12px', padding: '1.25rem', ...style
    }}>
      {children}
    </div>
  )
}

function SectionTitle({ icon: Icon, children }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
      <Icon size={15} color="var(--accent)" />
      <h2 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
        {children}
      </h2>
    </div>
  )
}

function SeverityBadge({ severity }) {
  const map = {
    critical: 'badge-red', warning: 'badge-yellow', info: 'badge-blue',
    high: 'badge-red', medium: 'badge-yellow', low: 'badge-green',
  }
  return <span className={`badge ${map[severity] || 'badge-gray'}`}>{severity}</span>
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <button onClick={copy} style={{
      background: 'none', border: '1px solid var(--border)',
      borderRadius: '5px', padding: '3px 7px', color: 'var(--text2)',
      display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px',
      transition: 'all 0.15s',
    }}>
      {copied ? <Check size={11} color="var(--green)" /> : <Copy size={11} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function AdVariant({ variant, url }) {
  const [open, setOpen] = useState(true)
  const domain = url.replace(/https?:\/\//, '').split('/')[0]
  const colors = ['var(--accent)', 'var(--cyan)', 'var(--accent2)']
  const idx = ['Value-Led','Feature-Led','Social Proof'].indexOf(variant.variant_name)
  const color = colors[idx] ?? colors[0]

  return (
    <div style={{
      border: '1px solid var(--border)', borderRadius: '10px', overflow: 'hidden',
      background: 'var(--bg3)',
    }}>
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          padding: '12px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          cursor: 'pointer', borderBottom: open ? '1px solid var(--border)' : 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: color }}></div>
          <span style={{ fontWeight: 500, fontSize: '14px' }}>{variant.variant_name}</span>
          <span style={{ fontSize: '12px', color: 'var(--text3)' }}>{variant.angle}</span>
        </div>
        {open ? <ChevronUp size={14} color="var(--text3)" /> : <ChevronDown size={14} color="var(--text3)" />}
      </div>

      {open && (
        <div style={{ padding: '14px' }}>
          {/* Google Ads preview */}
          <div style={{
            background: 'var(--bg4)', borderRadius: '8px', padding: '12px 14px',
            border: '1px solid var(--border)', marginBottom: '14px',
          }}>
            <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '4px', fontFamily: 'var(--mono)' }}>Ad preview</div>
            <div style={{ fontSize: '12px', color: 'var(--green)', marginBottom: '2px' }}>
              Ad · {domain}{variant.display_url_path}
            </div>
            <div style={{ fontSize: '16px', color: 'var(--accent)', marginBottom: '4px', lineHeight: 1.3 }}>
              {variant.headlines.slice(0,3).map(h => h.text).join(' | ')}
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text2)', lineHeight: 1.5 }}>
              {variant.descriptions[0]?.text}
            </div>
          </div>

          {/* Headlines */}
          <div style={{ marginBottom: '12px' }}>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Headlines ({variant.headlines.length})
            </div>
            {variant.headlines.map((h, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '6px 10px', background: 'var(--bg4)', borderRadius: '6px',
                marginBottom: '4px', gap: '8px',
              }}>
                <span style={{ fontSize: '13px', flex: 1 }}>{h.text}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                  <span style={{
                    fontSize: '11px', fontFamily: 'var(--mono)',
                    color: h.char_count > 30 ? 'var(--red)' : h.char_count > 25 ? 'var(--yellow)' : 'var(--text3)',
                  }}>
                    {h.char_count}/30
                  </span>
                  <CopyButton text={h.text} />
                </div>
              </div>
            ))}
          </div>

          {/* Descriptions */}
          <div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Descriptions ({variant.descriptions.length})
            </div>
            {variant.descriptions.map((d, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
                padding: '8px 10px', background: 'var(--bg4)', borderRadius: '6px',
                marginBottom: '4px', gap: '8px',
              }}>
                <span style={{ fontSize: '13px', flex: 1, lineHeight: 1.5 }}>{d.text}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                  <span style={{
                    fontSize: '11px', fontFamily: 'var(--mono)',
                    color: d.char_count > 90 ? 'var(--red)' : d.char_count > 80 ? 'var(--yellow)' : 'var(--text3)',
                  }}>
                    {d.char_count}/90
                  </span>
                  <CopyButton text={d.text} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

const TABS = [
  { id: 'overview', label: 'Overview', icon: BarChart3 },
  { id: 'seo', label: 'SEO Report', icon: Search },
  { id: 'ads', label: 'Ad Copy', icon: Megaphone },
  { id: 'sem', label: 'SEM Plan', icon: TrendingUp },
  { id: 'google-ads', label: 'Google Ads', icon: Zap },
  { id: 'site-audit', label: 'Site Audit', icon: Globe },
  { id: 'ai-traffic', label: 'AI Traffic', icon: Globe },
  { id: 'social', label: 'Social Media', icon: Share2 },
  { id: 'competitor', label: 'Competitors', icon: Target },
]

export default function Dashboard({ data, onReset, sessionId, googleEmail }) {
  const [tab, setTab] = useState('overview')
  const [recommendedPages, setRecommendedPages] = useState([])
  const [siteAuditResults, setSiteAuditResults] = useState(null)
  const { url, scraped_data: sc, seo_report: seo, ad_copy: ads, mock_campaign } = data
  
  const urlType = seo?.url_type || ((() => {
    const path = url.replace(/https?:\/\//, '').split('?')[0]
    const exts = ['.html', '.htm', '.php', '.aspx', '.asp']
    if (exts.some(e => path.endsWith(e))) return 'single_page'
    const segs = path.split('/').filter(s => s)
    if (segs.length >= 3) return 'single_page'
    return 'whole_site'
  })())
  const isWholeSite = urlType === 'whole_site'

  const domain = url.replace(/https?:\/\//, '').split('/')[0]

  const keywordChartData = (seo.keyword_suggestions || []).slice(0, 8).map(k => ({
    name: k.keyword.length > 18 ? k.keyword.slice(0, 18) + '…' : k.keyword,
    difficulty: k.difficulty === 'low' ? 30 : k.difficulty === 'medium' ? 60 : 90,
    priority: k.priority === 'primary' ? 1 : 0,
  }))

  const budgetData = seo?.sem_recommendations ? [
    { name: 'Search', value: 60 },
    { name: 'Display', value: 25 },
    { name: 'Remarketing', value: 15 },
  ] : []
  const PIE_COLORS = ['var(--accent)', 'var(--cyan)', 'var(--accent2)']

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg)', color: 'var(--text)', overflow: 'hidden' }}>

      {/* ── Sidebar ── */}
      <aside style={{
        width: '220px', flexShrink: 0, background: 'var(--bg2)',
        borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column', height: '100vh',
        position: 'sticky', top: 0,
      }}>
        {/* Logo */}
        <div style={{ padding: '16px 16px 12px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text)', letterSpacing: '-0.01em' }}>SEM AI</div>
          <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{domain}</div>
        </div>

        {/* Nav items */}
        <nav style={{ flex: 1, padding: '8px 0', overflowY: 'auto' }}>
          {TABS.map(t => {
            const Icon = t.icon
            const isActive = tab === t.id
            return (
              <button key={t.id} onClick={() => setTab(t.id)} style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: '9px',
                padding: '8px 14px', border: 'none', borderRadius: '0',
                background: isActive ? 'var(--accent-bg)' : 'transparent',
                color: isActive ? 'var(--accent)' : 'var(--text2)',
                fontSize: '13px', fontWeight: isActive ? 500 : 400,
                cursor: 'pointer', textAlign: 'left',
                borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
                transition: 'all 0.1s',
              }}
              onMouseEnter={e => { if (!isActive) { e.currentTarget.style.background = 'var(--bg3)'; e.currentTarget.style.color = 'var(--text)' }}}
              onMouseLeave={e => { if (!isActive) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text2)' }}}
              >
                <Icon size={14} />
                {t.label}
              </button>
            )
          })}
        </nav>

        {/* Bottom - Google status + theme */}
        <div style={{ padding: '12px 14px', borderTop: '1px solid var(--border)' }}>
          {googleEmail ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '10px' }}>
              <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: 'var(--green)', flexShrink: 0 }} />
              <div style={{ fontSize: '11px', color: 'var(--text2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {googleEmail}
              </div>
            </div>
          ) : null}
          <ThemeToggle />
          <button onClick={onReset} style={{
            marginTop: '8px', width: '100%', padding: '6px 10px',
            border: '1px solid var(--border)', borderRadius: 'var(--radius)',
            background: 'transparent', color: 'var(--text3)',
            fontSize: '12px', cursor: 'pointer',
          }}>← New analysis</button>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main style={{ flex: 1, overflowY: 'auto', padding: '24px 28px' }}>

        {/* Page header */}
        <div style={{ marginBottom: '20px' }}>
          <h1 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text)', marginBottom: '3px' }}>
            {TABS.find(t => t.id === tab)?.label || 'Overview'}
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text3)' }}>
            {domain} · Analysed today
          </p>
        </div>

        {tab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Score row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>SEO Health</div>
                <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center' }}>
                  <ScoreRing score={seo.overall_seo_score} label="Overall SEO" />
                  <ScoreRing score={seo.content_analysis?.quality_score || seo.content_analysis?.readability_score || (seo.overall_seo_score ? Math.round(seo.overall_seo_score * 0.8) : 0)} label="Content" />
                </div>
              </Card>

              <Card>
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
              </Card>

              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Est. Monthly Clicks</div>
                {seo.sem_recommendations && (
                  <>
                    <div style={{ fontSize: '28px', fontWeight: 600, letterSpacing: '-0.03em', color: 'var(--cyan)' }}>
                      {seo?.sem_recommendations?.estimated_monthly_clicks ? `${(seo.sem_recommendations.estimated_monthly_clicks.min || 0).toLocaleString()}-${(seo.sem_recommendations.estimated_monthly_clicks.max || 0).toLocaleString()}` : (seo?.sem_recommendations?.monthly_clicks_estimate || "N/A")}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '4px' }}>
                      ₹{seo?.sem_recommendations?.estimated_cpc_inr || seo?.sem_recommendations?.estimated_cpc_usd?.min || 0} avg CPC
                    </div>
                  </>
                )}
              </Card>

              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Page Stats</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {[
                    { label: 'HTML size', value: `${sc.html_size_kb} KB` },
                    { label: 'Images', value: sc.images_count },
                    { label: 'Missing alt', value: sc.images_without_alt_count, warn: sc.images_without_alt_count > 0 },
                    { label: 'Schema markup', value: sc.has_schema_markup ? '✓ Yes' : '✗ No', warn: !sc.has_schema_markup },
                  ].map(({ label, value, warn }) => (
                    <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                      <span style={{ color: 'var(--text3)' }}>{label}</span>
                      <span style={{ color: warn ? 'var(--yellow)' : 'var(--text2)', fontFamily: 'var(--mono)', fontSize: '12px' }}>{value}</span>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            {/* Summary */}
            <Card>
              <SectionTitle icon={Zap}>AI Summary</SectionTitle>
              <p style={{ color: 'var(--text2)', fontSize: '14px', lineHeight: 1.7 }}>{seo?.ai_summary || seo?.summary || 'AI analysis complete. Check the sections below for detailed insights.'}</p>

              {seo.priority_actions?.length > 0 && (
                <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '8px' }}>
                  {seo.priority_actions.slice(0, 6).map((a, i) => (
                    <div key={i} style={{
                      display: 'flex', gap: '8px', padding: '10px',
                      background: 'var(--bg3)', borderRadius: '8px',
                      border: '1px solid var(--border)',
                    }}>
                      <span style={{
                        minWidth: '20px', height: '20px', borderRadius: '50%',
                        background: 'rgba(79,125,255,0.15)', color: 'var(--accent)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '11px', fontWeight: 600, flexShrink: 0,
                      }}>{i + 1}</span>
                      <div>
                        <div style={{ fontSize: '13px', marginBottom: '4px' }}>{a.action}</div>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          <span className="badge badge-gray">{a.effort} effort</span>
                          <SeverityBadge severity={a.impact} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* Charts row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <Card>
                <SectionTitle icon={Search}>Keyword Difficulty</SectionTitle>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={keywordChartData} layout="vertical" margin={{ left: 10, right: 20 }}>
                    <XAxis type="number" domain={[0, 100]} tick={{ fill: 'var(--text3)', fontSize: 11 }} />
                    <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text2)', fontSize: 11 }} width={120} />
                    <Tooltip
                      contentStyle={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }}
                      labelStyle={{ color: 'var(--text)' }}
                    />
                    <Bar dataKey="difficulty" fill="var(--accent)" radius={[0, 4, 4, 0]} opacity={0.8} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              <Card>
                <SectionTitle icon={DollarSign}>Budget Allocation</SectionTitle>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={budgetData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value">
                      {budgetData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                    </Pie>
                    <Legend iconSize={10} wrapperStyle={{ fontSize: '12px', color: 'var(--text2)' }} />
                    <Tooltip contentStyle={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </div>
          </div>
        )}

        {/* ── SEO TAB ── */}
        {tab === 'seo' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* URL type banner */}
            <div style={{ padding: '10px 14px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '10px',
              background: isWholeSite ? 'var(--accent-bg)' : 'var(--purple-bg)',
              border: `1px solid ${isWholeSite ? 'var(--accent-border)' : 'rgba(83,74,183,0.2)'}`,
            }}>
              <span style={{ fontSize: '18px' }}>{isWholeSite ? '🌐' : '📄'}</span>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: isWholeSite ? 'var(--accent)' : 'var(--purple)' }}>
                  {isWholeSite ? 'Whole Site Analysis' : 'Single Page Analysis'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text3)' }}>
                  {isWholeSite 
                    ? 'Based on homepage data. Go to Site Audit tab for full page-by-page analysis.' 
                    : `Deep analysis of: ${url}`}
                </div>
              </div>
              {isWholeSite && (
                <button onClick={() => setTab('site-audit')} style={{ marginLeft: 'auto', padding: '5px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: 500, background: 'var(--accent)', border: 'none', color: 'white', cursor: 'pointer', flexShrink: 0 }}>
                  View Site Audit →
                </button>
              )}
            </div>
            {/* Meta info */}
            <Card>
              <SectionTitle icon={Globe}>Page Metadata</SectionTitle>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {[
                  { label: 'Title', value: sc.title },
                  { label: 'Meta description', value: sc.meta_description },
                  { label: 'H1 tags', value: sc.h1_tags?.join(', ') || 'None found' },
                ].map(({ label, value }) => (
                  <div key={label} style={{
                    padding: '10px 12px', background: 'var(--bg3)',
                    borderRadius: '8px', border: '1px solid var(--border)',
                  }}>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '3px', fontWeight: 500 }}>{label}</div>
                    <div style={{ fontSize: '13px', color: value ? 'var(--text)' : 'var(--red)' }}>
                      {value || '⚠ Missing'}
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Strengths & Weaknesses */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <Card>
                <SectionTitle icon={CheckCircle}>Strengths</SectionTitle>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {(seo?.strengths || []).map((s, i) => (
                    <div key={i} style={{
                      display: 'flex', gap: '8px', padding: '8px 10px',
                      background: 'rgba(34,197,94,0.05)', borderRadius: '7px',
                      border: '1px solid rgba(34,197,94,0.1)',
                    }}>
                      <CheckCircle size={13} color="var(--green)" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <div style={{ fontSize: '13px', lineHeight: 1.4 }}>{typeof s === 'string' ? s : s.point}</div>
                        {s.impact && <SeverityBadge severity={s.impact} />}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
              <Card>
                <SectionTitle icon={AlertTriangle}>Weaknesses</SectionTitle>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {(seo?.weaknesses || []).map((w, i) => (
                    <div key={i} style={{
                      display: 'flex', gap: '8px', padding: '8px 10px',
                      background: 'rgba(245,158,11,0.05)', borderRadius: '7px',
                      border: '1px solid rgba(245,158,11,0.1)',
                    }}>
                      <AlertTriangle size={13} color="var(--yellow)" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <div style={{ fontSize: '13px', marginBottom: '3px', lineHeight: 1.4 }}>{typeof w === 'string' ? w : w.point}</div>
                        {w.fix && <div style={{ fontSize: '12px', color: 'var(--text3)', fontStyle: 'italic' }}>Fix: {w.fix}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            {/* Technical Issues */}
            <Card>
              <SectionTitle icon={XCircle}>Technical Issues</SectionTitle>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {(seo?.technical_issues || []).map((issue, i) => (
                  <div key={i} style={{
                    padding: '12px', background: 'var(--bg3)',
                    borderRadius: '8px', border: '1px solid var(--border)',
                  }}>
                    {typeof issue === 'string' ? (
                      <div style={{ fontSize: '13px', color: 'var(--text2)' }}>{issue}</div>
                    ) : (
                      <>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          {issue.severity && <SeverityBadge severity={issue.severity} />}
                          <span style={{ fontSize: '13px', fontWeight: 500 }}>{issue.issue || issue.title}</span>
                        </div>
                        {issue.description && <div style={{ fontSize: '13px', color: 'var(--text2)', marginBottom: '4px' }}>{issue.description}</div>}
                        {issue.recommendation && <div style={{ fontSize: '12px', color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <ChevronRight size={11} />{issue.recommendation}
                        </div>}
                      </>
                    )}
                  </div>
                ))}
              </div>
            </Card>

            {/* Keywords */}
            <Card>
              <SectionTitle icon={Search}>Keyword Suggestions</SectionTitle>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '6px' }}>
                {(seo.keyword_suggestions || []).map((k, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '8px 12px', background: 'var(--bg3)',
                    borderRadius: '8px', border: '1px solid var(--border)',
                    borderLeft: `2px solid ${k.priority === 'primary' ? 'var(--accent)' : 'var(--border)'}`,
                  }}>
                    <span style={{ fontSize: '13px' }}>{k.keyword}</span>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <span className="badge badge-gray">{k.intent}</span>
                      <SeverityBadge severity={k.difficulty} />
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Content Analysis */}
            {seo.content_analysis && (
              <Card>
                <SectionTitle icon={BarChart3}>Content Analysis</SectionTitle>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                  <div style={{ padding: '12px', background: 'var(--bg3)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '4px' }}>Readability</div>
                    <div style={{ fontSize: '13px' }}>{seo.content_analysis.readability}</div>
                  </div>
                  <div style={{ padding: '12px', background: 'var(--bg3)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '4px' }}>Keyword Density</div>
                    <div style={{ fontSize: '13px' }}>{seo.content_analysis.keyword_density}</div>
                  </div>
                  <div style={{ padding: '12px', background: 'var(--bg3)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '4px' }}>Content Gaps</div>
                    {(seo.content_analysis.content_gaps || []).map((g, i) => (
                      <div key={i} style={{ fontSize: '13px', color: 'var(--text2)' }}>• {g}</div>
                    ))}
                  </div>
                </div>
              </Card>
            )}
          </div>
        )}

        {/* ── ADS TAB ── */}
        {tab === 'ads' && (
          <AdCopy 
            url={url} 
            seoReport={seo} 
            adCopy={ads} 
            urlType={urlType}
            savedRecommendations={recommendedPages.length > 0 ? {recommended_pages: recommendedPages} : null}
            onRecommendations={(data) => setRecommendedPages(data.recommended_pages || [])}
          />
        )}

        
        {tab === 'sem' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ padding: '10px 14px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '10px',
              background: isWholeSite ? 'var(--accent-bg)' : 'var(--purple-bg)',
              border: `1px solid ${isWholeSite ? 'var(--accent-border)' : 'rgba(83,74,183,0.2)'}`,
            }}>
              <span style={{ fontSize: '18px' }}>{isWholeSite ? '🌐' : '📄'}</span>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: isWholeSite ? 'var(--accent)' : 'var(--purple)' }}>
                  {isWholeSite ? 'Site-Wide SEM Strategy' : 'Single Page SEM Strategy'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text3)' }}>
                  {isWholeSite ? 'Campaign strategy based on full website analysis.' : `Optimised for: ${url}`}
                </div>
              </div>
            </div>

            {!seo?.sem_recommendations ? (
              <div style={{ padding: '14px', background: 'var(--bg3)', borderRadius: '10px', textAlign: 'center', color: 'var(--text3)', fontSize: '13px' }}>
                No SEM recommendations available. Try re-analysing the URL.
              </div>
            ) : (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                  {[
                    { label: 'Monthly Budget', value: `₹${(seo.sem_recommendations.monthly_budget_inr || 0).toLocaleString()}/mo`, icon: DollarSign, color: 'var(--green)' },
                    { label: 'Est. Clicks/mo', value: seo.sem_recommendations.monthly_clicks_estimate || 'N/A', icon: TrendingUp, color: 'var(--cyan)' },
                    { label: 'Avg CPC', value: `₹${seo.sem_recommendations.estimated_cpc_inr || 0}`, icon: Target, color: 'var(--accent)' },
                  ].map(({ label, value, icon: Icon, color }) => (
                    <Card key={label}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                        <Icon size={15} color={color} />
                        <span style={{ fontSize: '11px', color: 'var(--text3)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</span>
                      </div>
                      <div style={{ fontSize: '22px', fontWeight: 600, color: color, letterSpacing: '-0.02em' }}>{value}</div>
                    </Card>
                  ))}
                </div>

                <Card>
                  <SectionTitle icon={Target}>Bidding Strategy</SectionTitle>
                  <p style={{ fontSize: '14px', color: 'var(--text2)', lineHeight: 1.7 }}>{seo.sem_recommendations.bidding_strategy || ''}</p>
                </Card>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <Card>
                    <SectionTitle icon={Globe}>Country-Wise Budget</SectionTitle>
                    {(seo.sem_recommendations.country_budgets || []).length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {(seo.sem_recommendations.country_budgets || []).map((cb, i) => {
                          const cc = cb.competition === 'high' ? 'var(--red)' : cb.competition === 'medium' ? 'var(--yellow)' : 'var(--green)'
                          const cbg = cb.competition === 'high' ? 'var(--red-bg)' : cb.competition === 'medium' ? 'var(--yellow-bg)' : 'var(--green-bg)'
                          const flag = {IN:'🇮🇳',US:'🇺🇸',GB:'🇬🇧',UK:'🇬🇧',AU:'🇦🇺',CA:'🇨🇦',SG:'🇸🇬',AE:'🇦🇪'}[cb.code] || '🌍'
                          return (
                            <div key={i} style={{ padding: '10px 12px', background: 'var(--bg3)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <span style={{ fontSize: '16px' }}>{flag}</span>
                                  <div>
                                    <div style={{ fontSize: '12px', fontWeight: 600 }}>{cb.country}</div>
                                    <div style={{ fontSize: '10px', color: 'var(--text3)' }}>{cb.notes}</div>
                                  </div>
                                </div>
                                <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: cbg, color: cc, fontWeight: 500 }}>{cb.competition}</span>
                              </div>
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '4px' }}>
                                {[
                                  { label: 'Budget', val: '\u20b9' + (cb.budget_inr||0).toLocaleString(), color: 'var(--green)' },
                                  { label: 'Share', val: cb.budget_pct + '%', color: 'var(--accent)' },
                                  { label: 'Avg CPC', val: '\u20b9' + cb.avg_cpc_inr, color: 'var(--yellow)' },
                                  { label: 'Clicks', val: cb.monthly_clicks, color: 'var(--cyan)' },
                                ].map(({ label, val, color }) => (
                                  <div key={label} style={{ textAlign: 'center', padding: '5px', background: 'var(--bg4)', borderRadius: '5px' }}>
                                    <div style={{ fontSize: '12px', fontWeight: 700, color }}>{val}</div>
                                    <div style={{ fontSize: '9px', color: 'var(--text3)', textTransform: 'uppercase' }}>{label}</div>
                                  </div>
                                ))}
                              </div>
                              <div style={{ marginTop: '6px', height: '4px', background: 'var(--bg4)', borderRadius: '2px' }}>
                                <div style={{ height: '100%', width: cb.budget_pct + '%', background: 'var(--accent)', borderRadius: '2px' }} />
                              </div>
                            </div>
                          )
                        })}
                        <div style={{ padding: '8px 10px', background: 'var(--accent-bg)', border: '1px solid var(--accent-border)', borderRadius: '8px', fontSize: '11px', color: 'var(--accent-text)', lineHeight: 1.5 }}>
                          US/UK markets cost more per click but deliver higher-value leads. India offers volume at lower cost.
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {(seo.sem_recommendations.target_countries || []).map((c, i) => (
                          <span key={i} className="badge badge-blue">{c}</span>
                        ))}
                      </div>
                    )}
                  </Card>
                  <Card>
                    <SectionTitle icon={Users}>Audience Segments</SectionTitle>
                    {(seo.sem_recommendations.audience_segments || []).map((seg, i) => (
                      <div key={i} style={{ padding: '10px', background: 'var(--bg3)', borderRadius: '8px', border: '1px solid var(--border)', marginBottom: '6px' }}>
                        <div style={{ fontWeight: 500, fontSize: '13px', marginBottom: '4px' }}>{seg.segment}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '6px' }}>Age: {seg.age_range}</div>
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                          {(seg.interests || []).map((int, j) => (
                            <span key={j} className="badge badge-gray">{int}</span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </Card>
                </div>

                {budgetData.length > 0 && (
                  <Card>
                    <SectionTitle icon={BarChart3}>Budget Allocation</SectionTitle>
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie data={budgetData} cx="50%" cy="50%" outerRadius={80} dataKey="value"
                          label={({ cx, cy, midAngle, innerRadius, outerRadius, name, value }) => {
                            const RADIAN = Math.PI / 180
                            const radius = outerRadius + 25
                            const x = cx + radius * Math.cos(-midAngle * RADIAN)
                            const y = cy + radius * Math.sin(-midAngle * RADIAN)
                            return <text x={x} y={y} fill="var(--text2)" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize={11}>{`${name} ${value}%`}</text>
                          }}>
                          {budgetData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                        </Pie>
                        <Tooltip formatter={(value) => `${value}%`} />
                      </PieChart>
                    </ResponsiveContainer>
                  </Card>
                )}
              </>
            )}
          </div>
        )}

        {tab === 'ai-traffic' && <AITraffic />}

        {tab === 'social' && (
          url
            ? <SocialMedia seoReport={seo} url={url} />
            : <div style={{textAlign:'center',padding:'3rem',color:'var(--text3)',fontSize:'13px'}}>
                Run a URL analysis first to generate social media posts
              </div>
        )}

        {tab === 'competitor' && (
          url 
            ? <Competitor url={url} seoReport={seo} />
            : <div style={{textAlign:'center',padding:'3rem',color:'var(--text3)',fontSize:'13px'}}>
                Run a URL analysis first to enable competitor analysis
              </div>
        )}

        {tab === 'google-ads' && (
          <AdsManager
            sessionId={sessionId}
            adCopy={ads}
            seoReport={seo}
            url={url}
            recommendedPages={recommendedPages}
            onRecommendedPages={setRecommendedPages}
          />
        )}
      </main>
    </div>
  )
}

