import { BASE } from '../api_config'
import { useState, useEffect } from 'react'
import { RefreshCw, Copy, Check, Share2, Zap, TrendingUp, Target, Users, Calendar } from "lucide-react"

function Card({ children, style }) {
  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: '12px', padding: '1.25rem', ...style
    }}>{children}</div>
  )
}

function ScoreBar({ label, score, color }) {
  return (
    <div style={{ marginBottom: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
        <span style={{ color: 'var(--text2)' }}>{label}</span>
        <span style={{ fontWeight: 600, color }}>{score}/100</span>
      </div>
      <div style={{ height: '6px', background: 'var(--bg4)', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${score}%`, background: color, borderRadius: '3px', transition: 'width 0.6s' }} />
      </div>
    </div>
  )
}

const PLATFORMS = [
  { id: 'linkedin', label: 'LinkedIn', icon: '💼', color: '#0077b5', audience: 'B2B Professionals', best_for: 'Case studies, thought leadership, project showcases' },
  { id: 'twitter', label: 'Twitter/X', icon: '𝕏', color: '#1a1a2e', audience: 'Tech community', best_for: 'Quick insights, lab notes, AI research updates' },
  { id: 'instagram', label: 'Instagram', icon: '📸', color: '#e1306c', audience: 'Visual learners', best_for: 'Project visuals, infographics, behind-the-scenes' },
  { id: 'youtube', label: 'YouTube', icon: '▶', color: '#ff0000', audience: 'Developers & learners', best_for: 'Project demos, tutorials, AI explainers' },
  { id: 'reddit', label: 'Reddit', icon: '🤖', color: '#ff4500', audience: 'Tech enthusiasts', best_for: 'r/MachineLearning, r/artificial, community Q&A' },
]

export default function SocialMedia({ url, seoReport }) {
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [generatingPost, setGeneratingPost] = useState(null)
  const [generatedPosts, setGeneratedPosts] = useState({})

  useEffect(() => {
    if (url) fetchAnalysis()
  }, [url])

  async function fetchAnalysis() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${BASE}/api/social-media/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, seo_report: seoReport })
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setAnalysis(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function generatePost(platform, postType) {
    const key = `${platform}_${postType}`
    setGeneratingPost(key)
    try {
      const res = await fetch(`${BASE}/api/social-media/generate-post`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, platform, post_type: postType, seo_report: seoReport })
      })
      const data = await res.json()
      setGeneratedPosts(prev => ({ ...prev, [key]: data.post }))
    } catch (e) {
      console.error(e)
    } finally {
      setGeneratingPost(null)
    }
  }

  function copyText(text, key) {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text3)' }}>
      <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 12px', display: 'block' }} />
      <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '6px' }}>Analyzing social media potential...</div>
      <div style={{ fontSize: '12px' }}>AI is analyzing your content for each platform</div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )

  if (error) return (
    <Card>
      <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--red)' }}>
        Failed: {error}
        <br />
        <button onClick={fetchAnalysis} style={{ marginTop: '12px', padding: '8px 16px', background: 'var(--accent)', border: 'none', borderRadius: '7px', color: 'white', cursor: 'pointer' }}>Retry</button>
      </div>
    </Card>
  )

  if (!analysis) return null

  const overallScore = analysis.overall_score || 0
  const scoreColor = overallScore >= 70 ? 'var(--green)' : overallScore >= 40 ? 'var(--yellow)' : 'var(--red)'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '3px' }}>Social Media Intelligence</h2>
          <p style={{ fontSize: '12px', color: 'var(--text3)' }}>AI-powered social strategy based on your website content</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '10px', background: 'rgba(79,125,255,0.12)', color: 'var(--accent)', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>AI Generated</span>
          <button onClick={fetchAnalysis} style={{ background: 'none', border: '1px solid var(--border)', borderRadius: '7px', padding: '6px 10px', color: 'var(--text2)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px' }}>
            <RefreshCw size={12} /> Refresh
          </button>
        </div>
      </div>

      {/* Tab navigation */}
      <div style={{ display: 'flex', gap: '4px', background: 'var(--bg3)', padding: '4px', borderRadius: '10px' }}>
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'platforms', label: 'Platform Fit' },
          { id: 'content', label: 'Content Ideas' },
          { id: 'strategy', label: 'Strategy' },
          { id: 'posts', label: 'Post Generator' },
        ].map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            flex: 1, padding: '6px', borderRadius: '7px', border: 'none', cursor: 'pointer', fontSize: '12px', fontWeight: 500,
            background: activeTab === t.id ? 'var(--bg2)' : 'transparent',
            color: activeTab === t.id ? 'var(--text)' : 'var(--text3)',
          }}>{t.label}</button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {activeTab === 'overview' && (
        <>
          {/* Score cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px' }}>
            {[
              { label: 'Social Readiness', value: analysis.overall_score, color: scoreColor },
              { label: 'Content Quality', value: analysis.content_score, color: 'var(--accent)' },
              { label: 'Shareability', value: analysis.shareability_score, color: 'var(--cyan)' },
              { label: 'Visual Potential', value: analysis.visual_score, color: '#e1306c' },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1rem', textAlign: 'center' }}>
                <div style={{ fontSize: '28px', fontWeight: 700, color }}>{value}</div>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '4px' }}>{label}</div>
              </div>
            ))}
          </div>

          {/* Summary */}
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>AI Summary</div>
            <p style={{ fontSize: '13px', color: 'var(--text2)', lineHeight: 1.7, margin: 0 }}>{analysis.summary}</p>
          </Card>

          {/* Strengths & Gaps */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Card>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--green)', marginBottom: '10px' }}>✅ Strengths</div>
              {(analysis.strengths || []).map((s, i) => (
                <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', padding: '6px 0', borderBottom: '1px solid var(--border)', lineHeight: 1.5 }}>→ {s}</div>
              ))}
            </Card>
            <Card>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--yellow)', marginBottom: '10px' }}>⚠️ Gaps to Fix</div>
              {(analysis.gaps || []).map((g, i) => (
                <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', padding: '6px 0', borderBottom: '1px solid var(--border)', lineHeight: 1.5 }}>→ {g}</div>
              ))}
            </Card>
          </div>
        </>
      )}

      {/* PLATFORM FIT TAB */}
      {activeTab === 'platforms' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {PLATFORMS.map(p => {
            const fit = analysis.platform_fit?.[p.id] || {}
            const fitScore = fit.score || 0
            const fitColor = fitScore >= 70 ? 'var(--green)' : fitScore >= 40 ? 'var(--yellow)' : 'var(--red)'
            return (
              <Card key={p.id}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: `${p.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px', flexShrink: 0 }}>
                    {p.icon}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ fontSize: '14px', fontWeight: 600 }}>{p.label}</div>
                      <div style={{ fontSize: '20px', fontWeight: 700, color: fitColor }}>{fitScore}<span style={{ fontSize: '12px', color: 'var(--text3)', fontWeight: 400 }}>/100</span></div>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{p.audience}</div>
                  </div>
                </div>
                <div style={{ height: '6px', background: 'var(--bg4)', borderRadius: '3px', overflow: 'hidden', marginBottom: '12px' }}>
                  <div style={{ height: '100%', width: `${fitScore}%`, background: fitColor, borderRadius: '3px', transition: 'width 0.6s' }} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '10px' }}>
                  <div style={{ background: 'var(--bg3)', borderRadius: '8px', padding: '8px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text3)', marginBottom: '3px' }}>WHY IT FITS</div>
                    <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.5 }}>{fit.why || p.best_for}</div>
                  </div>
                  <div style={{ background: 'var(--bg3)', borderRadius: '8px', padding: '8px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text3)', marginBottom: '3px' }}>CONTENT TYPES</div>
                    <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.5 }}>{fit.content_types || 'Posts, articles'}</div>
                  </div>
                </div>
                {fit.tip && (
                  <div style={{ background: 'rgba(79,125,255,0.08)', borderRadius: '8px', padding: '8px 10px', fontSize: '12px', color: 'var(--accent)' }}>
                    💡 {fit.tip}
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      )}

      {/* CONTENT IDEAS TAB */}
      {activeTab === 'content' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Content Ideas from Your Site</div>
            {(analysis.content_ideas || []).map((idea, i) => (
              <div key={i} style={{ padding: '12px', background: 'var(--bg3)', borderRadius: '10px', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span style={{ fontSize: '18px' }}>{idea.emoji || '💡'}</span>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>{idea.title}</div>
                  <span style={{ marginLeft: 'auto', fontSize: '10px', background: 'rgba(79,125,255,0.12)', color: 'var(--accent)', padding: '2px 6px', borderRadius: '4px' }}>{idea.platform}</span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6 }}>{idea.description}</div>
                {idea.hook && (
                  <div style={{ marginTop: '8px', padding: '6px 10px', background: 'var(--bg2)', borderRadius: '6px', fontSize: '12px', color: 'var(--text3)', fontStyle: 'italic' }}>
                    Hook: "{idea.hook}"
                  </div>
                )}
              </div>
            ))}
          </Card>

          {/* Hashtags */}
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Recommended Hashtags</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {(analysis.hashtags || []).map((tag, i) => (
                <span key={i} onClick={() => copyText(tag, `tag_${i}`)} style={{ fontSize: '12px', padding: '4px 10px', background: 'var(--bg3)', borderRadius: '20px', color: 'var(--accent)', cursor: 'pointer', border: '1px solid var(--border)' }}>
                  {copied === `tag_${i}` ? '✓ Copied' : tag}
                </span>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* STRATEGY TAB */}
      {activeTab === 'strategy' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Content Mix */}
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Recommended Content Mix</div>
            {(analysis.content_mix || []).map((item, i) => (
              <div key={i} style={{ marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text2)' }}>{item.type}</span>
                  <span style={{ fontWeight: 600, color: 'var(--accent)' }}>{item.percentage}%</span>
                </div>
                <div style={{ height: '6px', background: 'var(--bg4)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${item.percentage}%`, background: 'var(--accent)', borderRadius: '3px' }} />
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '3px' }}>{item.example}</div>
              </div>
            ))}
          </Card>

          {/* Posting Schedule */}
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Best Posting Times</div>
            {(analysis.posting_schedule || []).map((item, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '18px' }}>{item.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: 500 }}>{item.platform}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{item.best_time}</div>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--accent)', fontWeight: 600 }}>{item.frequency}</div>
              </div>
            ))}
          </Card>

          {/* Priority Actions */}
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Priority Actions</div>
            {(analysis.priority_actions || []).map((action, i) => (
              <div key={i} style={{ display: 'flex', gap: '10px', padding: '10px', background: 'var(--bg3)', borderRadius: '8px', marginBottom: '8px' }}>
                <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'var(--accent)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700, flexShrink: 0 }}>{i + 1}</div>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '3px' }}>{action.action}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{action.reason}</div>
                  <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '3px', background: action.effort === 'low' ? 'rgba(34,197,94,0.12)' : 'rgba(251,174,75,0.12)', color: action.effort === 'low' ? 'var(--green)' : 'var(--yellow)', marginTop: '4px', display: 'inline-block' }}>
                    {action.effort} effort
                  </span>
                </div>
              </div>
            ))}
          </Card>
        </div>
      )}

      {/* POST GENERATOR TAB */}
      {activeTab === 'posts' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Generate Ready-to-Post Content</div>
            <div style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '14px' }}>AI generates posts based on your actual website content</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px' }}>
              {[
                { platform: 'linkedin', type: 'thought_leadership', label: 'LinkedIn Article', icon: '💼' },
                { platform: 'twitter', type: 'insight', label: 'Twitter Thread', icon: '𝕏' },
                { platform: 'instagram', type: 'tip', label: 'Instagram Caption', icon: '📸' },
                { platform: 'linkedin', type: 'case_study', label: 'LinkedIn Case Study', icon: '📊' },
                { platform: 'twitter', type: 'announcement', label: 'Product Launch Tweet', icon: '🚀' },
                { platform: 'reddit', type: 'insight', label: 'Reddit Post', icon: '🤖' },
              ].map(({ platform, type, label, icon }) => {
                const key = `${platform}_${type}`
                const post = generatedPosts[key]
                const isGenerating = generatingPost === key
                return (
                  <div key={key} style={{ background: 'var(--bg3)', borderRadius: '10px', padding: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontSize: '13px', fontWeight: 500 }}>{icon} {label}</span>
                      <button onClick={() => generatePost(platform, type)} disabled={isGenerating} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '6px', background: 'var(--accent)', border: 'none', color: 'white', cursor: 'pointer' }}>
                        {isGenerating ? '...' : 'Generate'}
                      </button>
                    </div>
                    {post && (
                      <div style={{ position: 'relative' }}>
                        <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6, background: 'var(--bg2)', borderRadius: '8px', padding: '10px', marginTop: '8px', maxHeight: '120px', overflowY: 'auto' }}>{post}</div>
                        <button onClick={() => copyText(post, key)} style={{ position: 'absolute', top: '14px', right: '6px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '5px', padding: '3px 7px', cursor: 'pointer', fontSize: '11px', color: 'var(--text2)' }}>
                          {copied === key ? '✓' : <Copy size={11} />}
                        </button>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
