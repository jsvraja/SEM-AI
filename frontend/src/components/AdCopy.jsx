import { useState, useEffect } from 'react'
import { RefreshCw, Zap, Target, Copy, Check, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react'
import { BASE } from '../api_config'

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  return (
    <button onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
      style={{ padding: '3px 8px', borderRadius: '5px', border: '1px solid var(--border)', background: 'var(--bg4)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--text3)' }}>
      {copied ? <Check size={10} color="var(--green)" /> : <Copy size={10} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function AdPreview({ page, index }) {
  const [open, setOpen] = useState(index === 0)
  const { ad_copy: ac, url, title, reason, ad_intent, suggested_keywords } = page

  const intentColors = {
    commercial: { bg: 'var(--green-bg)', color: 'var(--green)' },
    transactional: { bg: 'var(--accent-bg)', color: 'var(--accent)' },
    informational: { bg: 'var(--yellow-bg)', color: 'var(--yellow)' },
  }
  const intentStyle = intentColors[ad_intent] || intentColors.commercial

  return (
    <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden' }}>
      {/* Header */}
      <div onClick={() => setOpen(!open)} style={{ padding: '14px 16px', cursor: 'pointer', display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
        <div style={{
          width: '28px', height: '28px', borderRadius: '8px', flexShrink: 0,
          background: 'var(--accent-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '13px', fontWeight: 700, color: 'var(--accent)',
        }}>{index + 1}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '3px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>{title}</span>
            <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '4px', fontWeight: 500, background: intentStyle.bg, color: intentStyle.color }}>
              {ad_intent}
            </span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--accent)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{url}</div>
          <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>✓ {reason}</div>
        </div>
        <div style={{ flexShrink: 0, color: 'var(--text3)' }}>
          {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>

      {/* Ad copy details */}
      {open && ac && (
        <div style={{ padding: '0 16px 16px', borderTop: '1px solid var(--border)' }}>
          {/* Google Ads Preview */}
          <div style={{ padding: '12px', background: 'var(--bg)', borderRadius: '8px', border: '1px solid var(--border)', marginTop: '12px', marginBottom: '12px' }}>
            <div style={{ fontSize: '10px', color: 'var(--text3)', marginBottom: '6px', fontWeight: 500, letterSpacing: '0.05em' }}>AD PREVIEW</div>
            <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '2px' }}>Ad · {url.replace('https://', '').split('/')[0]}{ac.display_path || ''}</div>
            <div style={{ fontSize: '14px', color: '#1a73e8', fontWeight: 500, marginBottom: '3px', lineHeight: 1.4 }}>
              {ac.headline_1} | {ac.headline_2} | {ac.headline_3}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.5 }}>{ac.description_1}</div>
            <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.5 }}>{ac.description_2}</div>
          </div>

          {/* Headlines */}
          <div style={{ marginBottom: '10px' }}>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', letterSpacing: '0.05em', marginBottom: '6px' }}>HEADLINES</div>
            {[ac.headline_1, ac.headline_2, ac.headline_3].filter(Boolean).map((h, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '7px 10px', background: 'var(--bg3)', borderRadius: '7px', marginBottom: '4px' }}>
                <span style={{ fontSize: '13px', color: 'var(--text)' }}>{h}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                  <span style={{ fontSize: '10px', color: h.length > 30 ? 'var(--red)' : 'var(--text3)' }}>{h.length}/30</span>
                  <CopyButton text={h} />
                </div>
              </div>
            ))}
          </div>

          {/* Descriptions */}
          <div style={{ marginBottom: '10px' }}>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', letterSpacing: '0.05em', marginBottom: '6px' }}>DESCRIPTIONS</div>
            {[ac.description_1, ac.description_2].filter(Boolean).map((d, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px', padding: '7px 10px', background: 'var(--bg3)', borderRadius: '7px', marginBottom: '4px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text)', lineHeight: 1.5 }}>{d}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                  <span style={{ fontSize: '10px', color: d.length > 90 ? 'var(--red)' : 'var(--text3)' }}>{d.length}/90</span>
                  <CopyButton text={d} />
                </div>
              </div>
            ))}
          </div>

          {/* Keywords */}
          {suggested_keywords?.length > 0 && (
            <div style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', letterSpacing: '0.05em', marginBottom: '6px' }}>SUGGESTED KEYWORDS</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                {suggested_keywords.map((kw, i) => (
                  <span key={i} style={{ fontSize: '11px', padding: '3px 9px', borderRadius: '10px', background: 'var(--accent-bg)', color: 'var(--accent)', border: '1px solid var(--accent-border)' }}>{kw}</span>
                ))}
              </div>
            </div>
          )}

          {/* Final URL */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', background: 'var(--bg3)', borderRadius: '7px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text3)' }}>Final URL:</span>
            <a href={url} target="_blank" rel="noreferrer" style={{ fontSize: '11px', color: 'var(--accent)', textDecoration: 'none', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{url}</a>
            <ExternalLink size={11} color="var(--text3)" />
          </div>
        </div>
      )}
    </div>
  )
}

export default function AdCopy({ url, seoReport, adCopy, urlType, savedRecommendations, onRecommendations }) {
  const [loading, setLoading] = useState(false)
  const [recommendations, setRecommendations] = useState(() => {
    if (savedRecommendations) return savedRecommendations
    try { const s = sessionStorage.getItem('adcopy_recommendations'); return s ? JSON.parse(s) : null } catch(e) { return null }
  })
  const [error, setError] = useState(null)
  const [maxPages, setMaxPages] = useState(50)
  const isWholeSite = urlType === 'whole_site'

  useEffect(() => {
    if (savedRecommendations && !recommendations) {
      setRecommendations(savedRecommendations)
    }
  }, [savedRecommendations])



  async function analyseAndRecommend() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${BASE}/api/ads/recommend-pages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, max_pages: maxPages }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setRecommendations(data)
      if (onRecommendations) onRecommendations(data)
      try { sessionStorage.setItem('adcopy_recommendations', JSON.stringify(data)) } catch(e) {}
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'var(--accent-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Zap size={18} color="var(--accent)" />
        </div>
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '2px' }}>Smart Ad Copy</h2>
          <p style={{ fontSize: '12px', color: 'var(--text3)' }}>
            {isWholeSite ? 'AI crawls your site and recommends the best pages to advertise' : 'AI-generated ad copy for this page'}
          </p>
        </div>
      </div>

      {/* Whole site — AI recommendation mode */}
      {isWholeSite && (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '6px' }}>AI Page Recommender</div>
          <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6, marginBottom: '12px' }}>
            SEMA will crawl <strong>{url}</strong>, analyse all pages, and recommend only the best pages for Google Ads — with generated ad copy for each.
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '12px', color: 'var(--text3)' }}>Pages to scan:</span>
            {[25, 50, 100, 200].map(n => (
              <button key={n} onClick={() => setMaxPages(n)} style={{
                padding: '4px 10px', borderRadius: '5px', fontSize: '12px',
                background: maxPages === n ? 'var(--accent-bg)' : 'var(--bg3)',
                border: `1px solid ${maxPages === n ? 'var(--accent-border)' : 'var(--border)'}`,
                color: maxPages === n ? 'var(--accent)' : 'var(--text3)',
                cursor: 'pointer', fontWeight: maxPages === n ? 600 : 400,
              }}>{n}</button>
            ))}
          </div>
          <button onClick={analyseAndRecommend} disabled={loading} style={{
            width: '100%', padding: '12px', borderRadius: '10px', fontSize: '14px', fontWeight: 600,
            background: loading ? 'var(--bg3)' : 'linear-gradient(135deg, #6366f1, #818cf8)',
            border: 'none', color: loading ? 'var(--text3)' : 'white',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
          }}>
            {loading
              ? <><RefreshCw size={15} style={{ animation: 'spin 1s linear infinite' }} /> Analysing pages...</>
              : <><Target size={15} /> {recommendations ? 'Re-analyse Pages' : 'Find Best Pages to Advertise'}</>
            }
          </button>
        </div>
      )}

      {error && <div style={{ padding: '10px 14px', background: 'var(--red-bg)', border: '1px solid rgba(163,45,45,0.2)', borderRadius: '8px', fontSize: '13px', color: 'var(--red)' }}>⚠ {error}</div>}

      {/* Recommendations results */}
      {recommendations && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {/* Summary */}
          <div style={{ padding: '12px 14px', background: 'var(--accent-bg)', border: '1px solid var(--accent-border)', borderRadius: '10px' }}>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent)', marginBottom: '4px' }}>
              ✅ Found {recommendations.recommended_pages?.length || 0} pages to advertise from {recommendations.total_pages_analysed} analysed
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6 }}>{recommendations.campaign_strategy}</div>
          </div>

          {/* Recommended pages */}
          {(recommendations.recommended_pages || []).map((page, i) => (
            <AdPreview key={i} page={page} index={i} />
          ))}

          {/* Excluded pages */}
          {recommendations.excluded_pages?.length > 0 && (
            <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '10px', padding: '12px 14px' }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', letterSpacing: '0.05em', marginBottom: '8px' }}>EXCLUDED PAGES ({recommendations.excluded_pages.length})</div>
              {recommendations.excluded_pages.slice(0, 5).map((p, i) => (
                <div key={i} style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '3px', display: 'flex', gap: '6px' }}>
                  <span style={{ color: 'var(--red)' }}>✗</span>
                  <span style={{ color: 'var(--accent)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.url}</span>
                  <span>— {p.reason}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Single page — show existing ad copy */}
      {!isWholeSite && adCopy && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ padding: '10px 14px', background: 'var(--purple-bg)', border: '1px solid rgba(83,74,183,0.2)', borderRadius: '10px', fontSize: '12px', color: 'var(--purple)' }}>
            📄 Single page analysis — showing AI-generated ad copy for this specific page
          </div>
          {(adCopy.ad_variants || []).map((variant, i) => (
            <AdPreview key={i} page={{
              url: url,
              title: variant.angle || `Variant ${i + 1}`,
              reason: 'Generated from page content analysis',
              ad_intent: 'commercial',
              suggested_keywords: (seoReport?.keyword_suggestions || []).slice(0, 5).map(k => k.keyword),
              ad_copy: {
                headline_1: variant.headlines?.[0]?.text || '',
                headline_2: variant.headlines?.[1]?.text || '',
                headline_3: variant.headlines?.[2]?.text || '',
                description_1: variant.descriptions?.[0]?.text || '',
                description_2: variant.descriptions?.[1]?.text || '',
                display_path: '',
              }
            }} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}
