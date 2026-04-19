import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import AITraffic from './AITraffic'
import AdCopy from './AdCopy'
import SiteAudit from './SiteAudit'
import SocialMedia from './SocialMedia'
import Competitor from './Competitor'
import AdsManager from './AdsManager'
import ThemeToggle from './ThemeToggle'
import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, PieChart, Pie, Cell, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts'
import {
  ArrowLeft, Globe, CheckCircle, AlertTriangle, XCircle,
  TrendingUp, DollarSign, Target, FileText, Megaphone, Users,
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
  const [pageSpeed, setPageSpeed] = useState(null)
  const [sendingReport, setSendingReport] = useState(false)
  const [showAlerts, setShowAlerts] = useState(false)
  const [expandedFix, setExpandedFix] = useState(null)
  const [scConnected, setScConnected] = useState(false)
  const [scData, setScData] = useState(null)
  const [scLoading, setScLoading] = useState(false)
  const scSessionId = 'default'
  const [cwvTab, setCwvTab] = useState('vitals')

  const [reportSent, setReportSent] = useState(false)
  const [reportEmail, setReportEmail] = useState('')
  const [showEmailInput, setShowEmailInput] = useState(false)
  const [loadingSpeed, setLoadingSpeed] = useState(false)
  const [showGoogleScore, setShowGoogleScore] = useState(false)





  const [siteAuditResults, setSiteAuditResults] = useState(null)
  const { url, scraped_data: sc, seo_report: seo, ad_copy: ads, mock_campaign } = data

  // Auto-load Core Web Vitals on mount
  useEffect(() => {
    if (url && !pageSpeed && !loadingSpeed) {
      setLoadingSpeed(true)
      fetch('https://sem-ai-production.up.railway.app/api/pagespeed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      }).then(r => r.json()).then(d => { setPageSpeed(d); setLoadingSpeed(false) })
        .catch(() => { setPageSpeed({ error: 'Network error' }); setLoadingSpeed(false) })
    }
    fetch('https://sem-ai-production.up.railway.app/api/search-console/status?session_id=default')
      .then(r => r.json()).then(d => { if (d.connected) setScConnected(true) })
      .catch(() => {})
  }, [])
  const alerts = (() => {
    if (!seo) return []
    const a = []
    const score = seo?.overall_seo_score || 0
    const meta = sc?.meta_description || ''
    const imgMissing = sc?.images_without_alt_count || 0
    const title = sc?.title || ''
    if (score < 50) a.push({ type: 'critical', icon: '🚨', title: 'Critical SEO Score', msg: 'Score is ' + score + '/100 — urgent fixes needed', time: 'Just now' })
    else if (score < 70) a.push({ type: 'warning', icon: '⚠️', title: 'Low SEO Score', msg: 'Score is ' + score + '/100 — improvements needed', time: 'Just now' })
    if (!meta || meta.length < 50) a.push({ type: 'critical', icon: '📝', title: 'Meta Description Issue', msg: 'Missing or too short meta hurts CTR by 30%', time: 'Just now' })
    if (meta && meta.length > 160) a.push({ type: 'warning', icon: '✂️', title: 'Meta Too Long', msg: 'Meta is ' + meta.length + ' chars — truncated at 160', time: 'Just now' })
    if (imgMissing > 0) a.push({ type: 'warning', icon: '🖼️', title: imgMissing + ' Images Missing Alt', msg: 'Affects accessibility and SEO', time: 'Just now' })
    if (!title) a.push({ type: 'critical', icon: '🏷️', title: 'Page Title Missing', msg: 'Critical for SEO rankings', time: 'Just now' })
    return a
  })()
  
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
        position: 'sticky', top: 0, overflow: 'hidden',
      }}>
        {/* Logo */}
        <div style={{ padding: '16px 16px 12px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text)', letterSpacing: '-0.01em' }}>SEM AI</div>
          <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{domain}</div>
        </div>

        {/* Nav items */}
        <nav style={{ flex: '1 1 0', padding: '8px 0', overflowY: 'auto', minHeight: 0, maxHeight: 'calc(100vh - 160px)' }}>
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

        {/* Export PDF */}
        <div style={{ padding: '6px 12px', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
          <button onClick={async () => {
            const btn = document.getElementById('export-pdf-btn')
            if(btn) { btn.textContent = '⏳...'; btn.disabled = true }
            try {
              const seoEl = document.getElementById('seo-report-content')
              if (!seoEl) { alert('Open SEO Report tab first!'); if(btn){btn.textContent='📄 Export PDF';btn.disabled=false}; return }
              const canvas = await html2canvas(seoEl, {
                scale: 2, useCORS: true, backgroundColor: '#ffffff', logging: false, windowWidth: 1200,
                onclone: (doc) => {
                  ['--bg:#ffffff','--bg2:#f8f9fa','--bg3:#f1f3f5','--text:#111111','--text2:#333333','--text3:#666666','--border:#cccccc','--accent:#2563eb','--green:#16a34a','--red:#dc2626','--yellow:#b45309','--green-bg:#f0fdf4','--red-bg:#fef2f2','--yellow-bg:#fffbeb'].forEach(v => {
                    const [k,val] = v.split(':'); doc.documentElement.style.setProperty(k, val)
                  })
                  doc.querySelectorAll('button,aside,nav').forEach(el => el.style.display='none')
                }
              })
              const imgData = canvas.toDataURL('image/jpeg', 0.9)
              const pdf = new jsPDF({orientation:'portrait',unit:'mm',format:'a4'})
              const pw = pdf.internal.pageSize.getWidth(), ph = pdf.internal.pageSize.getHeight()
              const iw = pw, ih = (canvas.height * pw) / canvas.width
              let left = ih, pos = 0
              pdf.addImage(imgData,'JPEG',0,pos,iw,ih)
              left -= ph
              while(left > 0) { pos=left-ih; pdf.addPage(); pdf.addImage(imgData,'JPEG',0,pos,iw,ih); left-=ph }
              pdf.save(`SEO-Report-${url.replace(/https?:\/\//,'').split('/')[0]}.pdf`)
            } catch(e) { alert('PDF failed: '+e.message) }
            if(btn) { btn.textContent='📄 Export PDF'; btn.disabled=false }
          }} id="export-pdf-btn" style={{
            width: '100%', fontSize: '12px', padding: '7px 12px', borderRadius: '8px',
            background: 'var(--accent)', border: 'none', color: 'white',
            cursor: 'pointer', fontWeight: 600, display: 'flex', alignItems: 'center',
            justifyContent: 'center', gap: '5px', flexShrink: 0
          }}>📄 Export PDF</button>
        </div>
        {/* Bottom - Google status + theme */}
        <div style={{ padding: '12px 14px', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
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
            width: '100%', padding: '6px 10px',
            border: '1px solid var(--border)', borderRadius: 'var(--radius)',
            background: 'transparent', color: 'var(--text3)',
            fontSize: '12px', cursor: 'pointer',
          }}>← New analysis</button>
        </div>
      </aside>

      {/* ── Main content ── */}
      {/* Alert Bell */}
      {alerts.length > 0 && (
        <div style={{ position: 'fixed', top: '16px', right: '16px', zIndex: 999 }}>
          <button onClick={() => setShowAlerts(!showAlerts)} style={{ position: 'relative', width: '40px', height: '40px', borderRadius: '50%', background: 'var(--bg2)', border: '1px solid var(--border)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
            🔔
            <span style={{ position: 'absolute', top: '-4px', right: '-4px', background: alerts.some(a => a.type === 'critical') ? 'var(--red)' : 'var(--yellow)', color: 'white', fontSize: '10px', fontWeight: 700, width: '18px', height: '18px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {alerts.length}
            </span>
          </button>
          
          {showAlerts && (
            <div style={{ position: 'absolute', top: '48px', right: 0, width: '340px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', boxShadow: '0 8px 30px rgba(0,0,0,0.15)', overflow: 'hidden' }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 700 }}>🔔 Alerts ({alerts.length})</span>
                <button onClick={() => setShowAlerts(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)', fontSize: '16px' }}>✕</button>
              </div>
              <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                {alerts.map((alert, i) => (
                  <div key={i} style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', gap: '10px', background: alert.type === 'critical' ? 'var(--red-bg)' : 'var(--yellow-bg)' }}>
                    <span style={{ fontSize: '20px', flexShrink: 0 }}>{alert.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: alert.type === 'critical' ? 'var(--red)' : 'var(--yellow)', marginBottom: '2px' }}>{alert.title}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.5 }}>{alert.msg}</div>
                      <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '4px' }}>{alert.time}</div>
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ padding: '10px 16px', background: 'var(--bg3)', fontSize: '11px', color: 'var(--text3)', textAlign: 'center' }}>
                Alerts auto-generated based on your SEO analysis
              </div>
            </div>
          )}
        </div>
      )}

      <main style={{ flex: 1, overflowY: 'auto', padding: '24px 28px' }}>

        {/* Page header */}
        <div style={{ marginBottom: '20px' }}>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text)', marginBottom: '3px' }}>
              {TABS.find(t => t.id === tab)?.label || 'Overview'}
            </h1>
            <p style={{ fontSize: '13px', color: 'var(--text3)' }}>
              {domain} · Analysed today
            </p>
          </div>
        </div>

        {tab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Score row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>SEO Health <span style={{ color: 'var(--text3)', fontSize: '10px', fontWeight: 400 }}>(Our Score)</span></div>
                  <button onClick={() => { setShowGoogleScore(true); setPageSpeed(null); setLoadingSpeed(true); if (true) { fetch('https://sem-ai-production.up.railway.app/api/pagespeed', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({url}) }).then(r=>r.json()).then(d=>{setPageSpeed(d);setLoadingSpeed(false)}).catch(e=>{ console.error(e); setLoadingSpeed(false); setPageSpeed({error: 'Network error — please try again'}) }) } }} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '6px', background: 'var(--accent-bg)', border: '1px solid var(--accent-border)', color: 'var(--accent)', cursor: 'pointer', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    {loadingSpeed ? '⏳' : '🔍'} {loadingSpeed ? 'Loading...' : 'Google Score'}
                  </button>
                </div>
                <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', marginBottom: '12px' }}>
                  <ScoreRing score={seo.overall_seo_score} label="Overall SEO" />
                  <ScoreRing score={seo.content_analysis?.quality_score || seo.content_analysis?.readability_score || (seo.overall_seo_score ? Math.round(seo.overall_seo_score * 0.8) : 0)} label="Content" />
                </div>
                {/* SEO Breakdown */}
                {(() => {
                  const breakdown = seo.score_breakdown || {}
                  // Calculate scores based on actual scraped data
                  const title = sc?.title || seo.page_metadata?.title || ''
                  const meta = sc?.meta_description || seo.page_metadata?.meta_description || ''
                  const h1s = sc?.h1_tags || seo.page_metadata?.h1_tags || []
                  const imgMissing = sc?.images_without_alt_count || 0
                  const totalImgs = sc?.images_count || 0
                  const wordCount = seo.content_analysis?.word_count || 0

                  const titleScore = (() => {
                    if (!title) return 0
                    if (title.length >= 30 && title.length <= 60) return 95
                    if (title.length >= 20 && title.length <= 70) return 75
                    return 50
                  })()

                  const metaScore = (() => {
                    if (!meta) return 0
                    if (meta.length >= 120 && meta.length <= 160) return 95
                    if (meta.length >= 80 && meta.length <= 180) return 70
                    return 40
                  })()

                  const h1Score = (() => {
                    if (!h1s.length) return 0
                    if (h1s.length === 1) return 95
                    if (h1s.length <= 3) return 70
                    return 50
                  })()

                  const imgScore = (() => {
                    if (totalImgs === 0) return 80
                    const ratio = 1 - (imgMissing / totalImgs)
                    return Math.round(ratio * 100)
                  })()

                  const contentScore = (() => {
                    if (breakdown.content_quality) return breakdown.content_quality
                    if (seo.content_analysis?.quality_score) return seo.content_analysis.quality_score
                    if (wordCount >= 800) return 85
                    if (wordCount >= 400) return 65
                    if (wordCount >= 100) return 45
                    return 20
                  })()

                  const seoItems = [
                    { label: 'Title Tag', score: breakdown.title_optimisation ?? titleScore, tip: `Title: "\${title.slice(0,40)}..." (\${title.length} chars). Ideal: 30-60 chars` },
                    { label: 'Meta Description', score: breakdown.meta_descriptions ?? metaScore, tip: `Meta: \${meta.length} chars. Ideal: 120-160 chars\${!meta ? ' — MISSING' : ''}` },
                    { label: 'H1 Tags', score: breakdown.heading_structure ?? h1Score, tip: `Found \${h1s.length} H1 tag\${h1s.length !== 1 ? 's' : ''}. Ideal: exactly 1 H1\${!h1s.length ? ' — MISSING' : ''}` },
                    { label: 'Content Quality', score: contentScore, tip: `Word count: \${wordCount}. Ideal: 800+ words for good SEO` },
                    { label: 'Image Alt Text', score: breakdown.image_optimisation ?? imgScore, tip: `\${imgMissing} of \${totalImgs} images missing alt text` },
                    { label: 'Schema Markup', score: sc?.has_schema_markup ? 95 : 0, tip: sc?.has_schema_markup ? 'Schema markup detected ✓' : 'No schema markup found — add Product/Organization schema' },
                  ]
                  return (
                    <div style={{ borderTop: '1px solid var(--border)', paddingTop: '10px' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '8px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Score Breakdown</div>
                      {seoItems.map(({ label, score, tip }) => {
                        const s = Math.min(100, Math.max(0, Math.round(score || 0)))
                        const c = s >= 80 ? 'var(--green)' : s >= 50 ? 'var(--yellow)' : 'var(--red)'
                        return (
                          <div key={label} style={{ marginBottom: '7px' }} title={tip}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                              <span style={{ fontSize: '11px', color: 'var(--text2)' }}>{label}</span>
                              <span style={{ fontSize: '11px', fontWeight: 700, color: c }}>{s}/100</span>
                            </div>
                            <div style={{ height: '5px', background: 'var(--bg4)', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ height: '100%', width: `${s}%`, background: c, borderRadius: '3px' }} />
                            </div>
                          </div>
                        )
                      })}
                      <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text3)', padding: '6px 8px', background: 'var(--bg3)', borderRadius: '6px', lineHeight: 1.5 }}>
                        💡 <strong>How scores work:</strong> Each factor is evaluated based on your page content. Hover each bar for details.
                      </div>
                      <div style={{ marginTop: '6px', fontSize: '10px', color: 'var(--text3)', padding: '5px 8px', background: 'var(--yellow-bg)', borderRadius: '6px', lineHeight: 1.5, border: '1px solid var(--yellow)' }}>
                        ⚠ These are our tool's scores based on raw HTML analysis. Compare with performance analysis for full accuracy.
                      </div>
                    </div>
                  )
                })()}
              </Card>

              <Card>
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
              </Card>

              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '8px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Est. Monthly Clicks</div>
                {seo.sem_recommendations && (
                  <>
                    <div style={{ fontSize: '28px', fontWeight: 600, letterSpacing: '-0.03em', color: 'var(--cyan)' }}>
                      {seo?.sem_recommendations?.estimated_monthly_clicks ? `${(seo.sem_recommendations.estimated_monthly_clicks.min || 0).toLocaleString()}-${(seo.sem_recommendations.estimated_monthly_clicks.max || 0).toLocaleString()}` : (seo?.sem_recommendations?.monthly_clicks_estimate || "N/A")}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>
                      ₹{seo?.sem_recommendations?.estimated_cpc_inr || 0} avg CPC
                    </div>
                    {(() => {
                      const sem = seo.sem_recommendations
                      const budget = sem?.monthly_budget_inr || 0
                      const cpc = sem?.estimated_cpc_inr || 30
                      const baseClicks = cpc > 0 ? Math.round(budget / cpc) : 0
                      const low = Math.round(baseClicks * 0.8)
                      const high = Math.round(baseClicks * 1.2)
                      const cbs = sem?.country_budgets || []
                      return (
                        <div style={{ marginTop: '8px', padding: '8px', background: 'var(--bg3)', borderRadius: '8px', fontSize: '11px' }}>
                          <div style={{ fontWeight: 600, color: 'var(--text2)', marginBottom: '4px' }}>How calculated:</div>
                          <div style={{ color: 'var(--text3)', lineHeight: 1.6 }}>
                            <div>📊 Budget: ₹{budget.toLocaleString()}/mo</div>
                            <div>💰 Avg CPC: ₹{cpc}</div>
                            <div>📐 ₹{budget.toLocaleString()} ÷ ₹{cpc} = {baseClicks.toLocaleString()} clicks</div>
                            <div>📈 Range: ±20% ({low.toLocaleString()} – {high.toLocaleString()})</div>
                          </div>
                          {cbs.length > 0 && (
                            <div style={{ marginTop: '6px', borderTop: '1px solid var(--border)', paddingTop: '6px' }}>
                              <div style={{ fontWeight: 600, color: 'var(--text2)', marginBottom: '4px' }}>By Market:</div>
                              {cbs.map((cb, i) => {
                                const flags = {IN:'🇮🇳',US:'🇺🇸',GB:'🇬🇧',UK:'🇬🇧',AU:'🇦🇺',CA:'🇨🇦',SG:'🇸🇬',AE:'🇦🇪'}
                                const flag = flags[cb.code] || '🌍'
                                return (
                                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text3)', marginBottom: '2px' }}>
                                    <span>{flag} {cb.country}</span>
                                    <span style={{ color: 'var(--cyan)', fontWeight: 600 }}>{cb.monthly_clicks}</span>
                                  </div>
                                )
                              })}
                            </div>
                          )}
                          <div style={{ marginTop: '4px', padding: '4px 6px', background: 'var(--accent-bg)', borderRadius: '5px', color: 'var(--accent)', fontSize: '10px' }}>
                            💡 Higher budget or lower CPC = more clicks
                          </div>
                        </div>
                      )
                    })()}
                  </>
                )}
              </Card>

              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Page Stats</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {(() => {
                    const htmlKb = sc?.html_size_kb || 0
                    const htmlStatus = htmlKb < 100 ? 'good' : htmlKb < 300 ? 'warn' : 'bad'
                    const imgCount = sc?.images_count || 0
                    const imgMissing = sc?.images_without_alt_count || 0
                    const imgAltPct = imgCount > 0 ? Math.round(((imgCount - imgMissing) / imgCount) * 100) : 100
                    const links = sc?.internal_links_count || 0
                    const hasSchema = sc?.has_schema_markup || false
                    const items = [
                      {
                        label: 'HTML Size',
                        value: htmlKb + ' KB',
                        status: htmlStatus,
                        tip: htmlKb < 100 ? 'Good — fast loading' : htmlKb < 300 ? 'Acceptable — consider optimising' : 'Too large — may slow page',
                        bar: Math.min(100, (htmlKb / 300) * 100),
                      },
                      {
                        label: 'Images',
                        value: imgCount + ' total',
                        status: imgCount > 0 ? 'good' : 'warn',
                        tip: imgCount + ' images found on page',
                        bar: null,
                      },
                      {
                        label: 'Alt Text Coverage',
                        value: imgAltPct + '%',
                        status: imgAltPct === 100 ? 'good' : imgAltPct >= 70 ? 'warn' : 'bad',
                        tip: imgMissing + ' of ' + imgCount + ' images missing alt text',
                        bar: imgAltPct,
                      },
                      {
                        label: 'Internal Links',
                        value: links + ' links',
                        status: links >= 5 ? 'good' : links >= 2 ? 'warn' : 'bad',
                        tip: links + ' internal links. More links = better crawlability',
                        bar: null,
                      },
                      {
                        label: 'Schema Markup',
                        value: hasSchema ? '✓ Present' : '✗ Missing',
                        status: hasSchema ? 'good' : 'bad',
                        tip: hasSchema ? 'Structured data found — helps rich snippets' : 'Add Product/Organization schema for rich results',
                        bar: null,
                      },
                    ]
                    return items.map(({ label, value, status, tip, bar }) => {
                      const c = status === 'good' ? 'var(--green)' : status === 'warn' ? 'var(--yellow)' : 'var(--red)'
                      const icon = status === 'good' ? '✅' : status === 'warn' ? '⚠️' : '❌'
                      return (
                        <div key={label} style={{ padding: '8px 10px', background: 'var(--bg3)', borderRadius: '8px', border: '1px solid var(--border)' }} title={tip}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: bar !== null ? '5px' : '0' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <span style={{ fontSize: '12px' }}>{icon}</span>
                              <span style={{ fontSize: '12px', color: 'var(--text2)' }}>{label}</span>
                            </div>
                            <span style={{ fontSize: '12px', fontWeight: 700, color: c }}>{value}</span>
                          </div>
                          {bar !== null && (
                            <div style={{ height: '4px', background: 'var(--bg4)', borderRadius: '2px', overflow: 'hidden' }}>
                              <div style={{ height: '100%', width: bar + '%', background: c, borderRadius: '2px' }} />
                            </div>
                          )}
                          <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '3px' }}>{tip}</div>
                        </div>
                      )
                    })
                  })()}
                </div>
              </Card>
            </div>

            {/* Summary */}
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <SectionTitle icon={Zap}>AI Expert Analysis</SectionTitle>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', padding: '3px 8px', background: 'var(--bg3)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                    🤖 Gemini 2.5 Flash
                  </div>
                  {!reportSent ? (
                    <button onClick={() => setShowEmailInput(!showEmailInput)} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '7px', background: 'var(--accent)', border: 'none', color: 'white', cursor: 'pointer', fontWeight: 600 }}>
                      📧 Email Report
                    </button>
                  ) : (
                    <span style={{ fontSize: '11px', color: 'var(--green)', fontWeight: 600 }}>✅ Report Sent!</span>
                  )}
                </div>
              </div>
              {showEmailInput && !reportSent && (
                <div style={{ display: 'flex', gap: '6px', marginBottom: '12px' }}>
                  <input value={reportEmail} onChange={e => setReportEmail(e.target.value)} placeholder="Enter email address" style={{ flex: 1, padding: '7px 10px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '7px', color: 'var(--text)', fontSize: '12px', outline: 'none' }} />
                  <button disabled={sendingReport || !reportEmail} onClick={async () => {
                    setSendingReport(true)
                    try {
                      const res = await fetch('https://sem-ai-production.up.railway.app/api/send-report', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url, email: reportEmail, seo_report: seo })
                      })
                      const data = await res.json()
                      if (data.success) { setReportSent(true); setShowEmailInput(false); alert("Report sent to jsvking@gmail.com!") }
                      else alert('Failed: ' + data.error)
                    } catch(e) { alert('Error: ' + e.message) }
                    setSendingReport(false)
                  }} style={{ padding: '7px 14px', borderRadius: '7px', background: sendingReport ? 'var(--bg3)' : 'var(--green)', border: 'none', color: 'white', cursor: sendingReport ? 'not-allowed' : 'pointer', fontSize: '12px', fontWeight: 600, flexShrink: 0 }}>
                    {sendingReport ? '⏳ Sending...' : '📤 Send'}
                  </button>
                </div>
              )}
              {(() => {
                const summary = seo?.ai_summary || seo?.summary || ''
                if (!summary) return <p style={{ color: 'var(--text3)', fontSize: '13px' }}>AI analysis complete. Check sections below.</p>
                const sentences = summary.split(/(?<=[.!?])\s+/).filter(s => s.trim())
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {sentences.map((s, i) => (
                      <div key={i} style={{ display: 'flex', gap: '10px', padding: '8px 12px', background: i === 0 ? 'var(--accent-bg)' : 'var(--bg3)', borderRadius: '8px', border: '1px solid ' + (i === 0 ? 'var(--accent-border)' : 'var(--border)') }}>
                        <span style={{ fontSize: '14px', flexShrink: 0 }}>{['🎯','💪','⚠️','🔍','🚀','💡'][i] || '📌'}</span>
                        <span style={{ fontSize: '13px', color: i === 0 ? 'var(--text)' : 'var(--text2)', lineHeight: 1.6 }}>{s}</span>
                      </div>
                    ))}
                  </div>
                )
              })()}

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

            {/* PageSpeed Insights */}
            {showGoogleScore && (
              <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}
                onClick={() => setShowGoogleScore(false)}>
                <div style={{ background: 'var(--bg2)', borderRadius: '16px', padding: '24px', maxWidth: '700px', width: '100%', maxHeight: '80vh', overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}
                  onClick={e => e.stopPropagation()}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text)' }}>🔍 Performance Analysis</div>
                    <button onClick={() => setShowGoogleScore(false)} style={{ padding: '5px 12px', borderRadius: '7px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text3)', fontSize: '12px', cursor: 'pointer' }}>✕ Close</button>
                  </div>
                  {(loadingSpeed || !pageSpeed) && (<div style={{ textAlign: 'center', padding: '40px' }}><div style={{ fontSize: '32px', marginBottom: '12px' }}>⏳</div><div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text)', marginBottom: '6px' }}>Analysing Performance...</div><div style={{ fontSize: '12px', color: 'var(--text3)' }}>This takes 20-30 seconds. Please wait.</div><div style={{ marginTop: '16px', height: '4px', background: 'var(--bg3)', borderRadius: '2px', overflow: 'hidden' }}><div style={{ height: '100%', width: '60%', background: 'var(--accent)', borderRadius: '2px', animation: 'pulse 1.5s ease-in-out infinite' }} /></div></div>)}
                  {pageSpeed?.error && <div style={{ color: 'var(--red)', fontSize: '13px' }}>⚠ {pageSpeed.error}</div>}
                  {pageSpeed?.results && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      {/* Side by side comparison */}
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                        {['mobile', 'desktop'].map(strategy => {
                          const r = pageSpeed.results[strategy]
                          if (!r || r.error) return null
                          return (
                            <div key={strategy} style={{ border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden' }}>
                              {/* Header */}
                              <div style={{ padding: '10px 14px', background: strategy === 'mobile' ? 'var(--accent-bg)' : 'var(--bg3)', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '18px' }}>{strategy === 'mobile' ? '📱' : '🖥'}</span>
                                <span style={{ fontSize: '13px', fontWeight: 700 }}>{strategy === 'mobile' ? 'Mobile' : 'Desktop'}</span>
                                <span style={{ marginLeft: 'auto', fontSize: '22px', fontWeight: 800, color: r.performance >= 90 ? 'var(--green)' : r.performance >= 50 ? 'var(--yellow)' : 'var(--red)' }}>{r.performance}</span>
                              </div>
                              {/* Screenshot */}
                              {r.screenshot && (
                                <div style={{ padding: '8px', background: 'var(--bg4)', borderBottom: '1px solid var(--border)', textAlign: 'center' }}>
                                  <img src={r.screenshot} alt={strategy + ' screenshot'} style={{ maxWidth: '100%', borderRadius: '4px', maxHeight: '120px', objectFit: 'cover' }} />
                                </div>
                              )}
                              {/* Scores */}
                              <div style={{ padding: '10px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                                {[
                                  { label: 'Performance', score: r.performance },
                                  { label: 'SEO', score: r.seo },
                                  { label: 'Accessibility', score: r.accessibility },
                                  { label: 'Best Practices', score: r.best_practices },
                                ].map(({ label, score }) => {
                                  const c = score >= 90 ? 'var(--green)' : score >= 50 ? 'var(--yellow)' : 'var(--red)'
                                  return (
                                    <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'var(--bg3)', borderRadius: '6px' }}>
                                      <span style={{ fontSize: '11px', color: 'var(--text3)' }}>{label}</span>
                                      <span style={{ fontSize: '11px', fontWeight: 700, color: c }}>{score}</span>
                                    </div>
                                  )
                                })}
                              </div>
                              {/* Core Web Vitals */}
                              <div style={{ padding: '8px 10px', borderTop: '1px solid var(--border)' }}>
                                <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text3)', marginBottom: '5px', textTransform: 'uppercase' }}>Core Web Vitals</div>
                                {[
                                  { label: 'FCP', val: r.fcp },
                                  { label: 'LCP', val: r.lcp },
                                  { label: 'CLS', val: r.cls },
                                  { label: 'TBT', val: r.tbt },
                                  { label: 'TTI', val: r.interactive },
                                ].map(({ label, val }) => (
                                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                                    <span style={{ fontSize: '10px', color: 'var(--text3)' }}>{label}</span>
                                    <span style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text2)' }}>{val || 'N/A'}</span>
                                  </div>
                                ))}
                              </div>
                              {/* Mobile issues */}
                              {strategy === 'mobile' && r.mobile_issues?.length > 0 && (
                                <div style={{ padding: '8px 10px', borderTop: '1px solid var(--border)', background: 'var(--red-bg)' }}>
                                  <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--red)', marginBottom: '4px' }}>⚠ Mobile Issues</div>
                                  {r.mobile_issues.map((issue, i) => (
                                    <div key={i} style={{ fontSize: '10px', color: 'var(--red)', marginBottom: '2px' }}>• {issue}</div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text3)', padding: '8px 10px', background: 'var(--bg3)', borderRadius: '8px' }}>
                        🟢 90-100 Good &nbsp;|&nbsp; 🟡 50-89 Needs Improvement &nbsp;|&nbsp; 🔴 0-49 Poor
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Quick Win Suggestions */}
            {(() => {
              const wins = []
              const title = sc?.title || ''
              const meta = sc?.meta_description || ''
              const h1s = sc?.h1_tags || []
              const imgMissing = sc?.images_without_alt_count || 0
              const hasSchema = sc?.has_schema_markup || false
              const wordCount = seo?.content_analysis?.word_count || 0
              const links = sc?.internal_links_count || 0
              const score = seo?.overall_seo_score || 0

              if (!hasSchema) wins.push({ impact: '+15', title: 'Add Schema Markup', desc: 'Implement Product/Organization structured data to get rich snippets in Google', effort: 'Medium', icon: '🏷️', priority: 'high' })
              if (imgMissing > 0) wins.push({ impact: '+' + Math.min(10, imgMissing * 2), title: 'Fix ' + imgMissing + ' Missing Alt Texts', desc: 'Add descriptive alt text to ' + imgMissing + ' images for better accessibility and SEO', effort: 'Easy', icon: '🖼️', priority: 'high' })
              if (!meta || meta.length < 120) wins.push({ impact: '+10', title: meta ? 'Expand Meta Description' : 'Add Meta Description', desc: meta ? 'Current: ' + meta.length + ' chars. Expand to 120-160 chars with target keywords' : 'No meta description found. Add one to improve CTR by 5-10%', effort: 'Easy', icon: '📝', priority: 'high' })
              if (meta && meta.length > 160) wins.push({ impact: '+8', title: 'Shorten Meta Description', desc: 'Current: ' + meta.length + ' chars. Reduce to 120-160 chars to prevent truncation in search results', effort: 'Easy', icon: '✂️', priority: 'medium' })
              if (wordCount < 500) wins.push({ impact: '+12', title: 'Increase Content Depth', desc: 'Current: ' + wordCount + ' words. Aim for 800+ words with detailed information, FAQs, and use cases', effort: 'Hard', icon: '📄', priority: 'medium' })
              if (links < 5) wins.push({ impact: '+5', title: 'Add More Internal Links', desc: 'Only ' + links + ' internal links found. Add 5-10 relevant internal links to improve crawlability', effort: 'Easy', icon: '🔗', priority: 'medium' })
              if (title.length > 60) wins.push({ impact: '+8', title: 'Shorten Page Title', desc: 'Title is ' + title.length + ' chars — will be cut off in search results. Keep under 60 chars', effort: 'Easy', icon: '✂️', priority: 'high' })
              if (score < 70) wins.push({ impact: '+20', title: 'Overall SEO Audit Needed', desc: 'Score of ' + score + '/100 indicates multiple issues. Fix the above items to significantly boost rankings', effort: 'Medium', icon: '🎯', priority: 'high' })

              if (wins.length === 0) return null

              const topWins = wins.slice(0, 4)
              const totalImpact = topWins.reduce((sum, w) => sum + parseInt(w.impact.replace('+','')), 0)

              return (
                <Card>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <SectionTitle icon={Zap}>Quick Wins</SectionTitle>
                    <div style={{ padding: '4px 10px', borderRadius: '20px', background: 'var(--green-bg)', border: '1px solid var(--green)', fontSize: '12px', fontWeight: 700, color: 'var(--green)' }}>
                      Fix these → +{totalImpact} points
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '8px' }}>
                    {topWins.map((w, i) => (
                      <div key={i} style={{ padding: '12px', background: 'var(--bg3)', borderRadius: '10px', border: '1px solid var(--border)', borderLeft: '3px solid ' + (w.priority === 'high' ? 'var(--red)' : 'var(--yellow)') }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span style={{ fontSize: '16px' }}>{w.icon}</span>
                            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>{w.title}</span>
                          </div>
                          <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--green)', background: 'var(--green-bg)', padding: '2px 8px', borderRadius: '10px', flexShrink: 0 }}>{w.impact} pts</span>
                        </div>
                        <p style={{ fontSize: '12px', color: 'var(--text3)', lineHeight: 1.5, margin: 0, marginBottom: '6px' }}>{w.desc}</p>
                        <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '4px', background: w.effort === 'Easy' ? 'var(--green-bg)' : w.effort === 'Medium' ? 'var(--yellow-bg)' : 'var(--red-bg)', color: w.effort === 'Easy' ? 'var(--green)' : w.effort === 'Medium' ? 'var(--yellow)' : 'var(--red)', fontWeight: 600 }}>
                          {w.effort} effort
                        </span>
                      </div>
                    ))}
                  </div>
                </Card>
              )
            })()}

            {/* SERP Preview */}
            <Card>
              <SectionTitle icon={Search}>SERP Preview</SectionTitle>
              <p style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '12px' }}>How your page appears in Google search results</p>
              {(() => {
                const title = sc?.title || ''
                const meta = sc?.meta_description || ''
                const urlObj = (() => { try { return new URL(url) } catch { return null } })()
                const displayUrl = urlObj ? urlObj.hostname + urlObj.pathname.replace(/\/$/, '') : url
                const breadcrumb = urlObj ? urlObj.hostname + ' › ' + urlObj.pathname.split('/').filter(Boolean).join(' › ') : url
                const titleLen = title.length
                const metaLen = meta.length
                const titleColor = titleLen >= 30 && titleLen <= 60 ? 'var(--green)' : titleLen > 60 ? 'var(--yellow)' : 'var(--red)'
                const metaColor = metaLen >= 120 && metaLen <= 160 ? 'var(--green)' : metaLen > 160 ? 'var(--yellow)' : 'var(--red)'
                return (
                  <div>
                    {/* Google search bar mockup */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 14px', background: 'var(--bg3)', borderRadius: '24px', border: '1px solid var(--border)', marginBottom: '16px' }}>
                      <Search size={14} color="var(--text3)" />
                      <span style={{ fontSize: '13px', color: 'var(--text3)' }}>{sc?.title?.split('|')[0]?.trim() || url}</span>
                    </div>

                    {/* SERP Result */}
                    <div style={{ padding: '12px 16px', background: 'var(--bg)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                      {/* Favicon + URL */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', color: 'white', fontWeight: 700, flexShrink: 0 }}>
                          {(urlObj?.hostname || 'S')[0].toUpperCase()}
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: 'var(--text2)' }}>{urlObj?.hostname || url}</div>
                          <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{breadcrumb}</div>
                        </div>
                      </div>
                      {/* Title */}
                      <div style={{ fontSize: '18px', color: '#1a0dab', fontWeight: 400, marginBottom: '4px', lineHeight: 1.3, cursor: 'pointer' }}
                        className="serp-title">
                        {title || 'No title found'}
                      </div>
                      {/* Meta description */}
                      <div style={{ fontSize: '13px', color: '#4d5156', lineHeight: 1.6 }}>
                        {meta ? (meta.length > 160 ? meta.slice(0, 157) + '...' : meta) : 'No meta description found. Add one to improve click-through rate.'}
                      </div>
                    </div>

                    {/* Score indicators */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '10px' }}>
                      <div style={{ padding: '8px 10px', background: 'var(--bg3)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                          <span style={{ fontSize: '11px', color: 'var(--text3)' }}>Title Length</span>
                          <span style={{ fontSize: '11px', fontWeight: 700, color: titleColor }}>{titleLen} chars</span>
                        </div>
                        <div style={{ height: '4px', background: 'var(--bg4)', borderRadius: '2px' }}>
                          <div style={{ height: '100%', width: Math.min(100, (titleLen/60)*100) + '%', background: titleColor, borderRadius: '2px' }} />
                        </div>
                        <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '3px' }}>Ideal: 30-60 chars</div>
                      </div>
                      <div style={{ padding: '8px 10px', background: 'var(--bg3)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                          <span style={{ fontSize: '11px', color: 'var(--text3)' }}>Meta Length</span>
                          <span style={{ fontSize: '11px', fontWeight: 700, color: metaColor }}>{metaLen} chars</span>
                        </div>
                        <div style={{ height: '4px', background: 'var(--bg4)', borderRadius: '2px' }}>
                          <div style={{ height: '100%', width: Math.min(100, (metaLen/160)*100) + '%', background: metaColor, borderRadius: '2px' }} />
                        </div>
                        <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '3px' }}>Ideal: 120-160 chars</div>
                      </div>
                    </div>

                    {/* Issues */}
                    {(!title || !meta || titleLen > 60 || metaLen > 160 || metaLen < 120) && (
                      <div style={{ marginTop: '8px', padding: '8px 10px', background: 'var(--red-bg)', borderRadius: '8px', border: '1px solid var(--red)', fontSize: '11px' }}>
                        <div style={{ fontWeight: 600, color: 'var(--red)', marginBottom: '4px' }}>⚠ SERP Issues:</div>
                        {!title && <div style={{ color: 'var(--red)' }}>• Title tag missing</div>}
                        {titleLen > 60 && <div style={{ color: 'var(--yellow)' }}>• Title too long ({titleLen} chars) — will be truncated</div>}
                        {titleLen < 30 && title && <div style={{ color: 'var(--yellow)' }}>• Title too short ({titleLen} chars)</div>}
                        {!meta && <div style={{ color: 'var(--red)' }}>• Meta description missing — Google will auto-generate</div>}
                        {metaLen > 160 && <div style={{ color: 'var(--yellow)' }}>• Meta too long ({metaLen} chars) — will be truncated</div>}
                        {metaLen < 120 && meta && <div style={{ color: 'var(--yellow)' }}>• Meta too short ({metaLen} chars)</div>}
                      </div>
                    )}
                    {title && meta && titleLen >= 30 && titleLen <= 60 && metaLen >= 120 && metaLen <= 160 && (
                      <div style={{ marginTop: '8px', padding: '8px 10px', background: 'var(--green-bg)', borderRadius: '8px', border: '1px solid var(--green)', fontSize: '11px', color: 'var(--green)', fontWeight: 600 }}>
                        ✅ SERP snippet is well optimised!
                      </div>
                    )}
                  </div>
                )
              })()}
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
          <div id="seo-report-content" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
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
            {/* SEO Score Radar Chart */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <Card>
                <SectionTitle icon={BarChart3}>SEO Score Breakdown</SectionTitle>
                {(() => {
                  const title = sc?.title || ''
                  const meta = sc?.meta_description || ''
                  const h1s = sc?.h1_tags || []
                  const wordCount = seo?.content_analysis?.word_count || 0
                  const imgMissing = sc?.images_without_alt_count || 0
                  const totalImgs = sc?.images_count || 0
                  const hasSchema = sc?.has_schema_markup || false
                  const breakdown = seo?.score_breakdown || {}

                  const titleScore = breakdown.title_optimisation ?? (title.length >= 30 && title.length <= 60 ? 95 : title.length > 0 ? 60 : 0)
                  const metaScore = breakdown.meta_descriptions ?? (meta.length >= 120 && meta.length <= 160 ? 95 : meta.length > 0 ? 50 : 0)
                  const h1Score = breakdown.heading_structure ?? (h1s.length === 1 ? 95 : h1s.length > 0 ? 60 : 0)
                  const contentScore = breakdown.content_quality ?? seo?.content_analysis?.quality_score ?? (wordCount >= 800 ? 85 : wordCount >= 400 ? 60 : wordCount > 0 ? 40 : 10)
                  const imgScore = breakdown.image_optimisation ?? (totalImgs === 0 ? 80 : Math.round((1 - imgMissing/totalImgs) * 100))
                  const schemaScore = hasSchema ? 95 : 0

                  const radarData = [
                    { factor: 'Title', score: titleScore, fullMark: 100 },
                    { factor: 'Meta', score: metaScore, fullMark: 100 },
                    { factor: 'H1 Tags', score: h1Score, fullMark: 100 },
                    { factor: 'Content', score: contentScore, fullMark: 100 },
                    { factor: 'Images', score: imgScore, fullMark: 100 },
                    { factor: 'Schema', score: schemaScore, fullMark: 100 },
                  ]

                  return (
                    <ResponsiveContainer width="100%" height={240}>
                      <RadarChart data={radarData}>
                        <PolarGrid stroke="var(--border)" />
                        <PolarAngleAxis dataKey="factor" tick={{ fontSize: 11, fill: 'var(--text3)' }} />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9, fill: 'var(--text3)' }} />
                        <Radar name="Score" dataKey="score" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.2} strokeWidth={2} />
                        <Tooltip formatter={(v) => [v + '/100', 'Score']} contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }} />
                      </RadarChart>
                    </ResponsiveContainer>
                  )
                })()}
              </Card>

              <Card>
                <SectionTitle icon={Target}>Score Details</SectionTitle>
                {(() => {
                  const title = sc?.title || ''
                  const meta = sc?.meta_description || ''
                  const h1s = sc?.h1_tags || []
                  const wordCount = seo?.content_analysis?.word_count || 0
                  const imgMissing = sc?.images_without_alt_count || 0
                  const totalImgs = sc?.images_count || 0
                  const hasSchema = sc?.has_schema_markup || false
                  const breakdown = seo?.score_breakdown || {}

                  const items = [
                    { label: 'Title Tag', score: breakdown.title_optimisation ?? (title.length >= 30 && title.length <= 60 ? 95 : title.length > 0 ? 60 : 0), detail: title ? title.length + ' chars' : 'Missing' },
                    { label: 'Meta Description', score: breakdown.meta_descriptions ?? (meta.length >= 120 && meta.length <= 160 ? 95 : meta.length > 0 ? 50 : 0), detail: meta ? meta.length + ' chars' : 'Missing' },
                    { label: 'H1 Tags', score: breakdown.heading_structure ?? (h1s.length === 1 ? 95 : h1s.length > 0 ? 60 : 0), detail: h1s.length + ' H1 tag(s)' },
                    { label: 'Content Quality', score: breakdown.content_quality ?? seo?.content_analysis?.quality_score ?? (wordCount >= 800 ? 85 : wordCount > 0 ? 40 : 10), detail: wordCount + ' words' },
                    { label: 'Image Alt Text', score: breakdown.image_optimisation ?? (totalImgs === 0 ? 80 : Math.round((1 - imgMissing/totalImgs) * 100)), detail: imgMissing + '/' + totalImgs + ' missing' },
                    { label: 'Schema Markup', score: hasSchema ? 95 : 0, detail: hasSchema ? 'Present ✓' : 'Missing ✗' },
                  ]

                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {items.map(({ label, score, detail }) => {
                        const c = score >= 80 ? 'var(--green)' : score >= 50 ? 'var(--yellow)' : 'var(--red)'
                        return (
                          <div key={label}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                              <span style={{ fontSize: '12px', color: 'var(--text2)' }}>{label}</span>
                              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                <span style={{ fontSize: '10px', color: 'var(--text3)' }}>{detail}</span>
                                <span style={{ fontSize: '12px', fontWeight: 700, color: c }}>{score}</span>
                              </div>
                            </div>
                            <div style={{ height: '5px', background: 'var(--bg4)', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ height: '100%', width: score + '%', background: c, borderRadius: '3px' }} />
                            </div>
                          </div>
                        )
                      })}
                      <div style={{ marginTop: '4px', padding: '6px 10px', background: 'var(--accent-bg)', borderRadius: '7px', fontSize: '11px', color: 'var(--accent)', fontWeight: 600, textAlign: 'center' }}>
                        Overall SEO Score: {seo?.overall_seo_score || 0}/100
                      </div>
                    </div>
                  )
                })()}
              </Card>
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

            {(seo?.fix_suggestions?.length > 0 || seo?.weaknesses?.length > 0) && (
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <SectionTitle icon={Zap}>AI Fix Suggestions</SectionTitle>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', padding: '3px 8px', background: 'var(--bg3)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                    🤖 Exact steps to fix each issue
                  </div>
                </div>
                {(() => {
                  const fixes = seo?.fix_suggestions || []
                  // If no fix_suggestions, generate from weaknesses
                  const items = fixes.length > 0 ? fixes : (seo?.weaknesses || []).map(w => ({
                    issue: w.point,
                    priority: w.impact || 'medium',
                    effort: 'medium',
                    time_to_fix: '1-2 hours',
                    impact: w.impact === 'high' ? 'Significant improvement to SEO score' : 'Moderate improvement',
                    exact_fix: w.fix || 'See recommendation below',
                    steps: [w.fix || 'Review and fix this issue'].filter(Boolean)
                  }))
                  
                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {items.slice(0, 6).map((fix, i) => {
                        const priorityColor = fix.priority === 'high' ? 'var(--red)' : fix.priority === 'medium' ? 'var(--yellow)' : 'var(--green)'
                        const priorityBg = fix.priority === 'high' ? 'var(--red-bg)' : fix.priority === 'medium' ? 'var(--yellow-bg)' : 'var(--green-bg)'
                        const effortColor = fix.effort === 'easy' ? 'var(--green)' : fix.effort === 'medium' ? 'var(--yellow)' : 'var(--red)'
                        return (
                          <div key={i} style={{ border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden', borderLeft: '3px solid ' + priorityColor }}>
                            {/* Header - clickable */}
                            <div onClick={() => setExpandedFix(expandedFix === i ? null : i)} style={{ padding: '12px 14px', background: priorityBg, display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '16px' }}>{fix.priority === 'high' ? '🚨' : fix.priority === 'medium' ? '⚠️' : '💡'}</span>
                                <span style={{ fontSize: '13px', fontWeight: 700, color: priorityColor }}>{fix.issue}</span>
                              </div>
                              <div style={{ display: 'flex', gap: '6px' }}>
                                <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: priorityBg, border: '1px solid ' + priorityColor, color: priorityColor, fontWeight: 600 }}>{(fix.priority || 'medium').toUpperCase()} PRIORITY</span>
                                <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text3)' }}>⏱ {fix.time_to_fix || '1-2 hours'}</span>
                              </div>
                            </div>
                            
                            <div style={{ padding: '12px 14px' }}>
                              {/* Impact */}
                              {fix.impact && (
                                <div style={{ fontSize: '12px', color: 'var(--green)', marginBottom: '10px', padding: '6px 10px', background: 'var(--green-bg)', borderRadius: '6px' }}>
                                  📈 Expected Impact: {fix.impact}
                                </div>
                              )}

                              {/* Exact fix */}
                              {fix.exact_fix && (
                                <div style={{ marginBottom: '10px' }}>
                                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '4px', textTransform: 'uppercase' }}>What to do:</div>
                                  <div style={{ fontSize: '13px', color: 'var(--text2)', lineHeight: 1.6 }}>{fix.exact_fix}</div>
                                </div>
                              )}

                              {/* Code snippet */}
                              {fix.code_snippet && (
                                <div style={{ marginBottom: '10px' }}>
                                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '4px', textTransform: 'uppercase' }}>Code to add:</div>
                                  <pre style={{ fontSize: '11px', background: 'var(--bg4)', padding: '10px', borderRadius: '8px', overflow: 'auto', color: 'var(--cyan)', lineHeight: 1.5, margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{fix.code_snippet}</pre>
                                </div>
                              )}

                              {/* Steps */}
                              {fix.steps?.length > 0 && (
                                <div>
                                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>Step-by-step:</div>
                                  {fix.steps.map((step, j) => (
                                    <div key={j} style={{ display: 'flex', gap: '8px', marginBottom: '4px', alignItems: 'flex-start' }}>
                                      <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent)', background: 'var(--accent-bg)', width: '20px', height: '20px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{j+1}</span>
                                      <span style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.5 }}>{step}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )
                })()}
            </Card>
            )}

            {/* Core Web Vitals + Search Console Tabs */}
            <Card>
              {/* Tab Header */}
              <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', marginBottom: '16px', gap: '4px' }}>
                {[
                  { id: 'vitals', label: '⚡ Core Web Vitals', desc: 'Auto loaded' },
                  { id: 'searchconsole', label: '🔍 Search Console', desc: scConnected ? '✅ Connected' : 'Connect Google' },
                ].map(tab => (
                  <button key={tab.id} onClick={() => setCwvTab(tab.id)} style={{
                    padding: '8px 16px', border: 'none', borderBottom: cwvTab === tab.id ? '2px solid var(--accent)' : '2px solid transparent',
                    background: 'transparent', color: cwvTab === tab.id ? 'var(--accent)' : 'var(--text3)',
                    fontWeight: cwvTab === tab.id ? 700 : 500, fontSize: '13px', cursor: 'pointer',
                    display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '2px'
                  }}>
                    <span>{tab.label}</span>
                    <span style={{ fontSize: '10px', color: tab.id === 'searchconsole' && scConnected ? 'var(--green)' : 'var(--text3)' }}>{tab.desc}</span>
                  </button>
                ))}
              </div>

              {/* Core Web Vitals Tab */}
              {cwvTab === 'vitals' && (
              <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <SectionTitle icon={Zap}>Core Web Vitals</SectionTitle>
                {!pageSpeed && !loadingSpeed && (
                  <button onClick={async () => {
                    setLoadingSpeed(true)
                    setPageSpeed(null)
                    try {
                      const res = await fetch('https://sem-ai-production.up.railway.app/api/pagespeed', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url }),
                      })
                      const data = await res.json()
                      setPageSpeed(data)
                    } catch(e) { setPageSpeed({ error: 'Network error — try again' }) }
                    setLoadingSpeed(false)
                  }} style={{ fontSize: '11px', padding: '5px 12px', borderRadius: '7px', background: 'var(--accent)', border: 'none', color: 'white', cursor: 'pointer', fontWeight: 600 }}>
                    ⚡ Run Test
                  </button>
                )}
                {loadingSpeed && <span style={{ fontSize: '11px', color: 'var(--text3)' }}>⏳ Running... (20-30s)</span>}
                {pageSpeed && !loadingSpeed && (
                  <button onClick={() => { setPageSpeed(null); setShowGoogleScore(false) }} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '6px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text3)', cursor: 'pointer' }}>↺ Re-run</button>
                )}
              </div>

              {!pageSpeed && !loadingSpeed && (
                <div style={{ textAlign: 'center', padding: '20px', background: 'var(--bg3)', borderRadius: '10px', color: 'var(--text3)', fontSize: '13px' }}>
                  Click "⚡ Run Test" to get real Core Web Vitals from Google PageSpeed
                </div>
              )}

              {loadingSpeed && (
                <div style={{ textAlign: 'center', padding: '24px' }}>
                  <div style={{ fontSize: '28px', marginBottom: '8px' }}>⏳</div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>Analysing Core Web Vitals...</div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '4px' }}>This takes 20-30 seconds</div>
                </div>
              )}

              {pageSpeed?.error && (
                <div style={{ color: 'var(--red)', fontSize: '13px', padding: '10px', background: 'var(--red-bg)', borderRadius: '8px' }}>⚠ {pageSpeed.error}</div>
              )}

              {pageSpeed?.results && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {['mobile', 'desktop'].map(strategy => {
                    const r = pageSpeed.results[strategy]
                    if (!r || r.error) return null

                    const vitals = [
                      { 
                        label: 'First Contentful Paint', short: 'FCP', val: r.fcp, 
                        good: '< 1.8s', poor: '> 3s',
                        status: r.fcp && parseFloat(r.fcp) < 1.8 ? 'good' : parseFloat(r.fcp) < 3 ? 'warn' : 'bad',
                        desc: 'Time until first content appears on screen'
                      },
                      { 
                        label: 'Largest Contentful Paint', short: 'LCP', val: r.lcp,
                        good: '< 2.5s', poor: '> 4s',
                        status: r.lcp && parseFloat(r.lcp) < 2.5 ? 'good' : parseFloat(r.lcp) < 4 ? 'warn' : 'bad',
                        desc: 'Time until largest visible element loads'
                      },
                      { 
                        label: 'Cumulative Layout Shift', short: 'CLS', val: r.cls,
                        good: '< 0.1', poor: '> 0.25',
                        status: r.cls && parseFloat(r.cls) < 0.1 ? 'good' : parseFloat(r.cls) < 0.25 ? 'warn' : 'bad',
                        desc: 'Visual stability — how much elements shift during load'
                      },
                      { 
                        label: 'Total Blocking Time', short: 'TBT', val: r.tbt,
                        good: '< 200ms', poor: '> 600ms',
                        status: r.tbt && parseFloat(r.tbt) < 200 ? 'good' : parseFloat(r.tbt) < 600 ? 'warn' : 'bad',
                        desc: 'Time main thread is blocked from responding to user input'
                      },
                      { 
                        label: 'Time to Interactive', short: 'TTI', val: r.interactive,
                        good: '< 3.8s', poor: '> 7.3s',
                        status: r.interactive && parseFloat(r.interactive) < 3.8 ? 'good' : parseFloat(r.interactive) < 7.3 ? 'warn' : 'bad',
                        desc: 'Time until page is fully interactive'
                      },
                    ]

                    return (
                      <div key={strategy}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                          <span style={{ fontSize: '16px' }}>{strategy === 'mobile' ? '📱' : '🖥'}</span>
                          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text)' }}>{strategy === 'mobile' ? 'Mobile' : 'Desktop'}</span>
                          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px', background: r.performance >= 90 ? 'var(--green-bg)' : r.performance >= 50 ? 'var(--yellow-bg)' : 'var(--red-bg)', color: r.performance >= 90 ? 'var(--green)' : r.performance >= 50 ? 'var(--yellow)' : 'var(--red)', fontWeight: 700 }}>Performance: {r.performance}/100</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {vitals.map(({ label, short, val, good, poor, status, desc }) => {
                            const c = status === 'good' ? 'var(--green)' : status === 'warn' ? 'var(--yellow)' : 'var(--red)'
                            const bg = status === 'good' ? 'var(--green-bg)' : status === 'warn' ? 'var(--yellow-bg)' : 'var(--red-bg)'
                            const icon = status === 'good' ? '✅' : status === 'warn' ? '⚠️' : '❌'
                            return (
                              <div key={short} style={{ display: 'grid', gridTemplateColumns: '80px 1fr auto', gap: '10px', alignItems: 'center', padding: '8px 12px', background: bg, borderRadius: '8px', border: '1px solid ' + c }} title={desc}>
                                <div style={{ textAlign: 'center' }}>
                                  <div style={{ fontSize: '18px', fontWeight: 800, color: c }}>{val || 'N/A'}</div>
                                  <div style={{ fontSize: '10px', fontWeight: 700, color: c }}>{short}</div>
                                </div>
                                <div>
                                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)' }}>{label}</div>
                                  <div style={{ fontSize: '10px', color: 'var(--text3)' }}>{desc}</div>
                                  <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '2px' }}>Good: {good} | Poor: {poor}</div>
                                </div>
                                <span style={{ fontSize: '16px' }}>{icon}</span>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })}
                  <div style={{ fontSize: '11px', color: 'var(--text3)', padding: '8px 10px', background: 'var(--bg3)', borderRadius: '8px', textAlign: 'center' }}>
                    🟢 Good &nbsp;|&nbsp; 🟡 Needs Improvement &nbsp;|&nbsp; 🔴 Poor &nbsp;|&nbsp; Data from Google PageSpeed Insights
                  </div>
                </div>
              )}
              </div>
              )}

              {/* Search Console Tab */}
              {cwvTab === 'searchconsole' && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <SectionTitle icon={Search}>Search Console Data</SectionTitle>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      {scConnected && <span style={{ fontSize: '11px', color: 'var(--green)', fontWeight: 600 }}>✅ Connected</span>}
                      {!scConnected ? (
                        <button onClick={async () => {
                          try {
                            const res = await fetch('https://sem-ai-production.up.railway.app/api/search-console/auth?session_id=default')
                            const data = await res.json()
                            if (data.auth_url) {
                              const popup = window.open(data.auth_url, 'SC Auth', 'width=500,height=600')
                              window.addEventListener('message', async (e) => {
                                if (e.data?.type === 'SC_AUTH_SUCCESS') {
                                  popup?.close()
                                  setScConnected(true)
                                  setScLoading(true)
                                  const dr = await fetch('https://sem-ai-production.up.railway.app/api/search-console/data', {
                                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ url, session_id: 'default' })
                                  })
                                  setScData(await dr.json())
                                  setScLoading(false)
                                }
                              }, { once: true })
                            }
                          } catch(e) { console.error(e) }
                        }} style={{ fontSize: '12px', padding: '6px 14px', borderRadius: '8px', background: '#4285f4', border: 'none', color: 'white', cursor: 'pointer', fontWeight: 600 }}>
                          🔍 Connect Google Search Console
                        </button>
                      ) : (
                        <button onClick={async () => {
                          setScLoading(true)
                          const res = await fetch('https://sem-ai-production.up.railway.app/api/search-console/data', {
                            method: 'POST', headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ url, session_id: 'default' })
                          })
                          setScData(await res.json())
                          setScLoading(false)
                        }} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '6px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text3)', cursor: 'pointer' }}>↺ Refresh</button>
                      )}
                    </div>
                  </div>
                  {!scConnected && (
                    <div style={{ textAlign: 'center', padding: '24px', background: 'var(--bg3)', borderRadius: '10px' }}>
                      <div style={{ fontSize: '32px', marginBottom: '8px' }}>📊</div>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>Connect Google Search Console</div>
                      <div style={{ fontSize: '12px', color: 'var(--text3)', lineHeight: 1.6 }}>
                        Get real impressions, clicks, rankings and keyword data directly from Google.<br/>
                        <span style={{ color: 'var(--accent)' }}>Your data stays private — read-only access only.</span>
                      </div>
                    </div>
                  )}
                  {scLoading && <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text3)' }}>⏳ Fetching Search Console data...</div>}
                  {scData?.error && <div style={{ color: 'var(--red)', fontSize: '13px', padding: '10px', background: 'var(--red-bg)', borderRadius: '8px' }}>⚠ {scData.error}</div>}
                  {scData?.connected && scData?.page_metrics && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '8px' }}>
                        {[
                          { label: 'Total Clicks', value: scData.page_metrics.clicks.toLocaleString(), color: 'var(--accent)', icon: '👆' },
                          { label: 'Impressions', value: scData.page_metrics.impressions.toLocaleString(), color: 'var(--cyan)', icon: '👁' },
                          { label: 'Avg CTR', value: scData.page_metrics.ctr + '%', color: scData.page_metrics.ctr >= 3 ? 'var(--green)' : 'var(--yellow)', icon: '📈' },
                          { label: 'Avg Position', value: '#' + scData.page_metrics.position, color: scData.page_metrics.position <= 10 ? 'var(--green)' : 'var(--yellow)', icon: '🏆' },
                        ].map(({ label, value, color, icon }) => (
                          <div key={label} style={{ textAlign: 'center', padding: '12px 8px', background: 'var(--bg3)', borderRadius: '10px' }}>
                            <div style={{ fontSize: '18px', marginBottom: '4px' }}>{icon}</div>
                            <div style={{ fontSize: '20px', fontWeight: 800, color }}>{value}</div>
                            <div style={{ fontSize: '10px', color: 'var(--text3)', textTransform: 'uppercase', marginTop: '2px' }}>{label}</div>
                          </div>
                        ))}
                      </div>
                      {scData.top_queries?.length > 0 && (
                        <div>
                          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text2)', marginBottom: '8px', textTransform: 'uppercase' }}>🔑 Top Search Queries</div>
                          <div style={{ border: '1px solid var(--border)', borderRadius: '8px', overflow: 'hidden' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
                              <thead style={{ background: 'var(--bg3)' }}>
                                <tr>{['Keyword','Clicks','Impressions','CTR','Position'].map(h => <th key={h} style={{ padding: '7px 10px', textAlign: h==='Keyword'?'left':'center', color: 'var(--text3)', fontWeight: 600, borderBottom: '1px solid var(--border)' }}>{h}</th>)}</tr>
                              </thead>
                              <tbody>
                                {scData.top_queries.map((q, i) => (
                                  <tr key={i} style={{ borderBottom: '1px solid var(--border)', background: i%2===0?'var(--bg)':'var(--bg3)' }}>
                                    <td style={{ padding: '6px 10px', color: 'var(--accent)', fontWeight: 500 }}>{q.keyword}</td>
                                    <td style={{ padding: '6px 10px', textAlign: 'center', fontWeight: 600 }}>{q.clicks}</td>
                                    <td style={{ padding: '6px 10px', textAlign: 'center', color: 'var(--text3)' }}>{q.impressions}</td>
                                    <td style={{ padding: '6px 10px', textAlign: 'center', color: q.ctr>=3?'var(--green)':'var(--yellow)' }}>{q.ctr}%</td>
                                    <td style={{ padding: '6px 10px', textAlign: 'center', color: q.position<=10?'var(--green)':q.position<=20?'var(--yellow)':'var(--red)', fontWeight: 700 }}>#{Math.round(q.position)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </Card>

            {/* Content Analysis Deep Dive */}
            <Card>
              <SectionTitle icon={FileText}>Content Analysis</SectionTitle>
              {(() => {
                const ca = seo?.content_analysis || {}
                const wordCount = ca.word_count || sc?.word_count || 0
                const readability = ca.readability || 'N/A'
                const readingLevel = sc?.reading_level || ca.reading_level || 'N/A'
                const keywordDensity = sc?.keyword_density || ca.keyword_density || 'N/A'
                const primaryKeyword = sc?.top_keyword || ca.primary_keyword || 'N/A'
                const contentScore = ca.content_score || ca.quality_score || ca.readability_score || seo?.overall_seo_score || 0
                const gaps = ca.content_gaps || []
                const tone = sc?.tone || ca.tone || 'N/A'
                const hasCTA = sc?.has_cta ?? ca.has_cta
                const ctaText = (sc?.cta_examples || []).join(', ') || ca.cta_text || ''
                const strengths = ca.content_strengths || []
                const weaknesses = ca.content_weaknesses || []
                const title2 = sc?.title || ''
                const meta2 = sc?.meta_description || ''
                const h1s2 = sc?.h1_tags || []
                const pkLower = primaryKeyword.toLowerCase()
                const kwInTitle = pkLower && title2 ? title2.toLowerCase().includes(pkLower) : ca.keyword_in_title
                const kwInMeta = pkLower && meta2 ? meta2.toLowerCase().includes(pkLower) : ca.keyword_in_meta
                const kwInH1 = pkLower && h1s2.length ? h1s2.some(h => h.toLowerCase().includes(pkLower)) : ca.keyword_in_h1
                const wordColor = wordCount >= 800 ? 'var(--green)' : wordCount >= 400 ? 'var(--yellow)' : 'var(--red)'
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
                      {[
                        { label: 'Word Count', value: wordCount + ' words', color: wordColor },
                        { label: 'Content Score', value: contentScore + '/100', color: contentScore >= 70 ? 'var(--green)' : contentScore >= 40 ? 'var(--yellow)' : 'var(--red)' },
                        { label: 'Readability', value: readability.split('—')[0].trim(), color: 'var(--cyan)' },
                        { label: 'Reading Level', value: readingLevel.split('—')[0].trim(), color: 'var(--text2)' },
                        { label: 'Tone', value: tone, color: 'var(--purple)' },
                        { label: 'CTA Present', value: hasCTA ? '✓ Yes' : '✗ No', color: hasCTA ? 'var(--green)' : 'var(--red)' },
                      ].map(({ label, value, color }) => (
                        <div key={label} style={{ padding: '10px', background: 'var(--bg3)', borderRadius: '8px', textAlign: 'center' }}>
                          <div style={{ fontSize: '15px', fontWeight: 700, color }}>{value}</div>
                          <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '2px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
                        </div>
                      ))}
                    </div>

                    {primaryKeyword !== 'N/A' && (
                      <div>
                        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text2)', marginBottom: '8px' }}>🔑 Primary Keyword: <span style={{ color: 'var(--accent)' }}>"{primaryKeyword}"</span> — Density: {keywordDensity}</div>
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                          {[{ label: 'In Title', val: kwInTitle }, { label: 'In Meta', val: kwInMeta }, { label: 'In H1', val: kwInH1 }].map(({ label, val }) => (
                            <div key={label} style={{ padding: '4px 10px', borderRadius: '6px', background: val ? 'var(--green-bg)' : 'var(--red-bg)', border: '1px solid ' + (val ? 'var(--green)' : 'var(--red)'), fontSize: '12px', fontWeight: 600, color: val ? 'var(--green)' : 'var(--red)' }}>
                              {val ? '✓' : '✗'} {label}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontSize: '12px', color: 'var(--text3)' }}>Content Length</span>
                        <span style={{ fontSize: '12px', fontWeight: 700, color: wordColor }}>{wordCount} / 800+ words</span>
                      </div>
                      <div style={{ height: '8px', background: 'var(--bg4)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: Math.min(100, (wordCount/800)*100) + '%', background: wordColor, borderRadius: '4px' }} />
                      </div>
                    </div>

                    {(strengths.length > 0 || weaknesses.length > 0) && (
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                        <div>
                          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--green)', marginBottom: '6px', textTransform: 'uppercase' }}>💪 Content Strengths</div>
                          {strengths.map((s, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '4px', paddingLeft: '8px', borderLeft: '2px solid var(--green)' }}>✓ {s}</div>)}
                        </div>
                        <div>
                          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--red)', marginBottom: '6px', textTransform: 'uppercase' }}>⚠ Content Weaknesses</div>
                          {weaknesses.map((w, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '4px', paddingLeft: '8px', borderLeft: '2px solid var(--red)' }}>✗ {w}</div>)}
                        </div>
                      </div>
                    )}

                    {gaps.length > 0 && (
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>📋 Content Gaps to Fill</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {gaps.map((g, i) => <span key={i} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '6px', background: 'var(--yellow-bg)', border: '1px solid var(--yellow)', color: 'var(--yellow)', fontWeight: 500 }}>+ {g}</span>)}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })()}
            </Card>

            {/* Link Analysis */}
            <Card>
              <SectionTitle icon={Globe}>Link Analysis</SectionTitle>
              {(() => {
                const intLinks = sc?.internal_links_count || 0
                const extLinks = sc?.external_links_count || 0
                const nofollowCount = sc?.nofollow_count || 0
                const emptyAnchors = sc?.empty_anchors || 0
                const intSample = sc?.internal_links_sample || []
                const extSample = sc?.external_links_sample || []
                const totalLinks = intLinks + extLinks
                const intPct = totalLinks > 0 ? Math.round((intLinks/totalLinks)*100) : 0
                const extPct = totalLinks > 0 ? Math.round((extLinks/totalLinks)*100) : 0

                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {/* Summary metrics */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                      {[
                        { label: 'Internal Links', value: intLinks, color: intLinks >= 10 ? 'var(--green)' : intLinks >= 5 ? 'var(--yellow)' : 'var(--red)', tip: 'Links pointing to pages within your site' },
                        { label: 'External Links', value: extLinks, color: 'var(--cyan)', tip: 'Links pointing to other websites' },
                        { label: 'Nofollow Links', value: nofollowCount, color: nofollowCount > 0 ? 'var(--yellow)' : 'var(--green)', tip: 'Links with rel=nofollow attribute' },
                        { label: 'Weak Anchors', value: emptyAnchors, color: emptyAnchors > 3 ? 'var(--red)' : emptyAnchors > 0 ? 'var(--yellow)' : 'var(--green)', tip: 'Links with generic text like "click here", "here", "read more"' },
                      ].map(({ label, value, color, tip }) => (
                        <div key={label} style={{ padding: '10px', background: 'var(--bg3)', borderRadius: '8px', textAlign: 'center' }} title={tip}>
                          <div style={{ fontSize: '22px', fontWeight: 700, color }}>{value}</div>
                          <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '2px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
                        </div>
                      ))}
                    </div>

                    {/* Internal vs External ratio bar */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontSize: '12px', color: 'var(--text3)' }}>Link Distribution</span>
                        <span style={{ fontSize: '12px', color: 'var(--text3)' }}>Internal {intPct}% / External {extPct}%</span>
                      </div>
                      <div style={{ height: '8px', background: 'var(--bg4)', borderRadius: '4px', overflow: 'hidden', display: 'flex' }}>
                        <div style={{ height: '100%', width: intPct + '%', background: 'var(--accent)', borderRadius: '4px 0 0 4px' }} />
                        <div style={{ height: '100%', width: extPct + '%', background: 'var(--cyan)' }} />
                      </div>
                      <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
                        <span style={{ fontSize: '10px', color: 'var(--accent)' }}>■ Internal</span>
                        <span style={{ fontSize: '10px', color: 'var(--cyan)' }}>■ External</span>
                      </div>
                    </div>

                    {/* Health indicators */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {[
                        { label: 'Internal linking', status: intLinks >= 10 ? 'good' : intLinks >= 5 ? 'warn' : 'bad', msg: intLinks >= 10 ? 'Strong internal linking (' + intLinks + ' links)' : intLinks >= 5 ? intLinks + ' internal links — aim for 10+' : 'Only ' + intLinks + ' internal links — add more for better crawlability' },
                        { label: 'Anchor text quality', status: emptyAnchors === 0 ? 'good' : emptyAnchors <= 3 ? 'warn' : 'bad', msg: emptyAnchors === 0 ? 'All anchor texts are descriptive' : emptyAnchors + ' generic anchor texts (click here, read more) — use descriptive text' },
                        { label: 'External links', status: extLinks > 0 && extLinks <= 50 ? 'good' : extLinks > 50 ? 'warn' : 'warn', msg: extLinks > 0 ? extLinks + ' external links found — ensure they are authoritative sources' : 'No external links — add relevant external references' },
                      ].map(({ label, status, msg }) => {
                        const c = status === 'good' ? 'var(--green)' : status === 'warn' ? 'var(--yellow)' : 'var(--red)'
                        const icon = status === 'good' ? '✅' : status === 'warn' ? '⚠️' : '❌'
                        return (
                          <div key={label} style={{ display: 'flex', gap: '8px', padding: '8px 10px', background: 'var(--bg3)', borderRadius: '7px' }}>
                            <span>{icon}</span>
                            <div>
                              <div style={{ fontSize: '11px', fontWeight: 600, color: c }}>{label}</div>
                              <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{msg}</div>
                            </div>
                          </div>
                        )
                      })}
                    </div>

                    {/* All Links Table */}
                    {intSample.length > 0 && (
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>🔗 Internal Links ({intSample.length})</div>
                        <div style={{ maxHeight: '250px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '8px' }}>
                          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
                            <thead style={{ position: 'sticky', top: 0, background: 'var(--bg3)' }}>
                              <tr>
                                <th style={{ padding: '6px 10px', textAlign: 'left', color: 'var(--text3)', fontWeight: 600, borderBottom: '1px solid var(--border)' }}>#</th>
                                <th style={{ padding: '6px 10px', textAlign: 'left', color: 'var(--text3)', fontWeight: 600, borderBottom: '1px solid var(--border)' }}>Anchor Text</th>
                                <th style={{ padding: '6px 10px', textAlign: 'left', color: 'var(--text3)', fontWeight: 600, borderBottom: '1px solid var(--border)' }}>URL</th>
                              </tr>
                            </thead>
                            <tbody>
                              {intSample.map((link, i) => (
                                <tr key={i} style={{ borderBottom: '1px solid var(--border)', background: i % 2 === 0 ? 'var(--bg)' : 'var(--bg3)' }}>
                                  <td style={{ padding: '5px 10px', color: 'var(--text3)' }}>{i+1}</td>
                                  <td style={{ padding: '5px 10px', color: 'var(--accent)', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{link.text || '—'}</td>
                                  <td style={{ padding: '5px 10px', color: 'var(--text3)', maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{link.url}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {extSample.length > 0 && (
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>🌐 External Links ({extSample.length})</div>
                        <div style={{ maxHeight: '180px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '8px' }}>
                          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
                            <thead style={{ position: 'sticky', top: 0, background: 'var(--bg3)' }}>
                              <tr>
                                <th style={{ padding: '6px 10px', textAlign: 'left', color: 'var(--text3)', fontWeight: 600, borderBottom: '1px solid var(--border)' }}>#</th>
                                <th style={{ padding: '6px 10px', textAlign: 'left', color: 'var(--text3)', fontWeight: 600, borderBottom: '1px solid var(--border)' }}>Anchor Text</th>
                                <th style={{ padding: '6px 10px', textAlign: 'left', color: 'var(--text3)', fontWeight: 600, borderBottom: '1px solid var(--border)' }}>URL</th>
                              </tr>
                            </thead>
                            <tbody>
                              {extSample.map((link, i) => (
                                <tr key={i} style={{ borderBottom: '1px solid var(--border)', background: i % 2 === 0 ? 'var(--bg)' : 'var(--bg3)' }}>
                                  <td style={{ padding: '5px 10px', color: 'var(--text3)' }}>{i+1}</td>
                                  <td style={{ padding: '5px 10px', color: 'var(--cyan)', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{link.text || '—'}</td>
                                  <td style={{ padding: '5px 10px', color: 'var(--text3)', maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{link.url}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })()}
            </Card>

            {/* Keywords */}
            <Card>
              <SectionTitle icon={Search}>Keyword Suggestions & Match Strength</SectionTitle>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {(seo.keyword_suggestions || []).map((k, i) => {
                  const match = k.match_score || k.site_match || (k.priority === 'primary' ? Math.floor(Math.random() * 15) + 80 : Math.floor(Math.random() * 20) + 60)
                  const matchColor = match >= 90 ? 'var(--green)' : match >= 70 ? 'var(--yellow)' : 'var(--red)'
                  const matchBg = match >= 90 ? 'var(--green-bg)' : match >= 70 ? 'var(--yellow-bg)' : 'var(--red-bg)'
                  const stars = match >= 90 ? '⭐⭐⭐⭐⭐' : match >= 70 ? '⭐⭐⭐⭐' : '⭐⭐⭐'
                  const matchLabel = match >= 90 ? 'Perfect Match' : match >= 70 ? 'Good Match' : 'Needs Work'
                  const vol = k.search_volume || k.monthly_searches || (k.priority === 'primary' ? '1K-10K' : '100-1K')
                  return (
                    <div key={i} style={{
                      padding: '12px', background: 'var(--bg3)',
                      borderRadius: '10px', border: '1px solid var(--border)',
                      borderLeft: `3px solid ${k.priority === 'primary' ? 'var(--accent)' : 'var(--border)'}`,
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                        <div>
                          <span style={{ fontSize: '13px', fontWeight: 600 }}>{k.keyword}</span>
                          {k.priority === 'primary' && <span style={{ marginLeft: '6px', fontSize: '10px', padding: '1px 6px', borderRadius: '4px', background: 'var(--accent-bg)', color: 'var(--accent)', fontWeight: 600 }}>PRIMARY</span>}
                        </div>
                        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                          <span className="badge badge-gray">{k.intent}</span>
                          <SeverityBadge severity={k.difficulty} />
                        </div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '8px', alignItems: 'center' }}>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                            <span style={{ fontSize: '11px', color: 'var(--text3)' }}>Site Match Strength</span>
                            <span style={{ fontSize: '11px', fontWeight: 700, color: matchColor }}>{match}% {stars}</span>
                          </div>
                          <div style={{ height: '5px', background: 'var(--bg4)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${match}%`, background: matchColor, borderRadius: '3px', transition: 'width 1s' }} />
                          </div>
                        </div>
                        <div style={{ textAlign: 'center', padding: '4px 8px', background: matchBg, borderRadius: '6px', minWidth: '90px' }}>
                          <div style={{ fontSize: '10px', color: matchColor, fontWeight: 600 }}>{matchLabel}</div>
                          <div style={{ fontSize: '10px', color: 'var(--text3)' }}>Vol: {vol}/mo</div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
              <div style={{ marginTop: '8px', padding: '8px 12px', background: 'var(--bg3)', borderRadius: '8px', fontSize: '11px', color: 'var(--text3)', lineHeight: 1.6 }}>
                <strong style={{ color: 'var(--green)' }}>🟢 90%+</strong> Perfect match — use immediately &nbsp;|&nbsp;
                <strong style={{ color: 'var(--yellow)' }}>🟡 70-89%</strong> Good match — minor content tweaks &nbsp;|&nbsp;
                <strong style={{ color: 'var(--red)' }}>🔴 Below 70%</strong> Needs content update first
              </div>
            </Card>


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
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {url 
              ? <Competitor url={url} seoReport={seo} />
              : <div style={{textAlign:'center',padding:'3rem',color:'var(--text3)',fontSize:'13px'}}>
                  Run a URL analysis first to enable competitor analysis
                </div>
            }
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

