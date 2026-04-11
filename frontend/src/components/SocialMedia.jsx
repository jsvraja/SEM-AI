import { BASE } from '../api_config'
import { useState } from 'react'
import { RefreshCw, Copy, Check, Share2, Zap, Download } from "lucide-react"


function Card({ children, style }) {
  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: '12px', padding: '1.25rem', ...style
    }}>{children}</div>
  )
}

const PLATFORMS = [
  { id: 'linkedin', label: 'LinkedIn', icon: '💼', color: '#0077b5', charLimit: 3000, tone: 'professional' },
  { id: 'twitter', label: 'Twitter/X', icon: '𝕏', color: '#000000', charLimit: 280, tone: 'concise and punchy' },
  { id: 'instagram', label: 'Instagram', icon: '📸', color: '#e1306c', charLimit: 2200, tone: 'visual and engaging' },
  { id: 'facebook', label: 'Facebook', icon: '👥', color: '#1877f2', charLimit: 63206, tone: 'friendly and conversational' },
]

const POST_TYPES = [
  { id: 'service', label: 'Service Highlight', emoji: '✨' },
  { id: 'insight', label: 'Industry Insight', emoji: '💡' },
  { id: 'case_study', label: 'Case Study', emoji: '📊' },
  { id: 'tip', label: 'Quick Tip', emoji: '🎯' },
  { id: 'announcement', label: 'Announcement', emoji: '📣' },
  { id: 'thought_leadership', label: 'Thought Leadership', emoji: '🧠' },
]

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  return (
    <button onClick={() => {
      navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }} style={{
      display: 'flex', alignItems: 'center', gap: '4px',
      padding: '5px 10px', borderRadius: '6px', fontSize: '11px',
      background: copied ? 'rgba(34,197,94,0.1)' : 'var(--bg3)',
      border: `1px solid ${copied ? 'rgba(34,197,94,0.3)' : 'var(--border)'}`,
      color: copied ? '#4ade80' : 'var(--text2)', cursor: 'pointer',
    }}>
      {copied ? <Check size={11} /> : <Copy size={11} />}
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

function PostCard({ post, platform }) {
  const p = PLATFORMS.find(p => p.id === platform)
  const isOver = post.content.length > p.charLimit
  return (
    <div style={{
      background: 'var(--bg3)', border: `1px solid ${isOver ? 'rgba(239,68,68,0.3)' : 'var(--border)'}`,
      borderRadius: '10px', padding: '14px', marginBottom: '10px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '16px' }}>{p.icon}</span>
          <span style={{ fontSize: '12px', fontWeight: 600, color: p.color }}>{p.label}</span>
          <span style={{ fontSize: '11px', color: 'var(--text3)', background: 'var(--bg4)', padding: '2px 7px', borderRadius: '10px' }}>{post.type}</span>
        </div>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', color: isOver ? '#f87171' : 'var(--text3)' }}>
            {post.content.length}/{p.charLimit}
          </span>
          <CopyButton text={post.content} />
        </div>
      </div>
      <div style={{ fontSize: '13px', lineHeight: 1.7, color: 'var(--text)', whiteSpace: 'pre-wrap' }}>
        {post.content}
      </div>
      {post.hashtags && (
        <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {post.hashtags.map((h, i) => (
            <span key={i} style={{ fontSize: '11px', color: p.color, background: `${p.color}15`, padding: '2px 8px', borderRadius: '10px' }}>#{h}</span>
          ))}
        </div>
      )}
      {post.best_time && (
        <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text3)' }}>
          ⏰ Best time to post: {post.best_time}
        </div>
      )}
    </div>
  )
}

export default function SocialMedia({ seoReport, url }) {
  const [selectedPlatforms, setSelectedPlatforms] = useState(['linkedin', 'twitter'])
  const [selectedTypes, setSelectedTypes] = useState(['service', 'insight'])
  const [customTopic, setCustomTopic] = useState('')
  const [generating, setGenerating] = useState(false)
  const [posts, setPosts] = useState([])
  const [error, setError] = useState(null)
  const [schedule, setSchedule] = useState(false)

  const domain = (() => { try { return new URL(url).hostname } catch { return url } })()

  function togglePlatform(id) {
    setSelectedPlatforms(p => p.includes(id) ? p.filter(x => x !== id) : [...p, id])
  }

  function toggleType(id) {
    setSelectedTypes(t => t.includes(id) ? t.filter(x => x !== id) : [...t, id])
  }

  async function generatePosts() {
    if (selectedPlatforms.length === 0) { setError('Select at least one platform'); return }
    if (selectedTypes.length === 0) { setError('Select at least one post type'); return }
    setGenerating(true)
    setError(null)
    setPosts([])

    try {
      const keywords = (seoReport?.keyword_suggestions || []).slice(0, 5).map(k => k.keyword).join(', ')
      const services = seoReport?.content_analysis?.main_topics?.join(', ') || 'AI automation, machine learning'
      const score = seoReport?.overall_seo_score || 70
      const res = await fetch(`${BASE}/api/social/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: url || 'https://sakthivelraja.ai',
          platforms: selectedPlatforms,
          post_types: selectedTypes,
          custom_topic: customTopic,
          keywords: (seoReport?.keyword_suggestions || []).slice(0,5).map(k=>k.keyword),
          services: seoReport?.content_analysis?.main_topics?.join(', ') || 'AI automation and technology',
        }),
      })
      const data = await res.json()
      if (data.posts && data.posts.length > 0) {
        setPosts(data.posts)
      } else if (data.error) {
        setError('Generation failed: ' + data.error)
      } else {
        setError('No posts generated. Please try again.')
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(99,102,241,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Share2 size={18} color="#818cf8" />
        </div>
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '2px' }}>AI Social Media Generator</h2>
          <p style={{ fontSize: '12px', color: 'var(--text3)' }}>Generate platform-optimised posts for {domain}</p>
        </div>
      </div>

      {/* Platform selector */}
      <Card>
        <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px', color: 'var(--text)' }}>
          Select Platforms
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {PLATFORMS.map(p => (
            <button key={p.id} onClick={() => togglePlatform(p.id)} style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '8px 14px', borderRadius: '8px', fontSize: '13px', cursor: 'pointer',
              background: selectedPlatforms.includes(p.id) ? `${p.color}18` : 'var(--bg3)',
              border: `1px solid ${selectedPlatforms.includes(p.id) ? p.color + '60' : 'var(--border)'}`,
              color: selectedPlatforms.includes(p.id) ? p.color : 'var(--text2)',
              fontWeight: selectedPlatforms.includes(p.id) ? 600 : 400,
            }}>
              <span style={{ fontSize: '16px' }}>{p.icon}</span> {p.label}
            </button>
          ))}
        </div>
      </Card>

      {/* Post type selector */}
      <Card>
        <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px', color: 'var(--text)' }}>
          Post Types
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {POST_TYPES.map(t => (
            <button key={t.id} onClick={() => toggleType(t.id)} style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '7px 12px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer',
              background: selectedTypes.includes(t.id) ? 'rgba(99,102,241,0.12)' : 'var(--bg3)',
              border: `1px solid ${selectedTypes.includes(t.id) ? 'rgba(99,102,241,0.4)' : 'var(--border)'}`,
              color: selectedTypes.includes(t.id) ? '#818cf8' : 'var(--text2)',
            }}>
              {t.emoji} {t.label}
            </button>
          ))}
        </div>
      </Card>

      {/* Custom topic */}
      <Card>
        <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '8px', color: 'var(--text)' }}>
          Custom Topic (Optional)
        </div>
        <input
          value={customTopic}
          onChange={e => setCustomTopic(e.target.value)}
          placeholder="e.g. AI automation for retail businesses, new service launch..."
          style={{
            width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)',
            borderRadius: '8px', padding: '10px 12px', color: 'var(--text)',
            fontSize: '13px', outline: 'none', boxSizing: 'border-box',
          }}
        />
      </Card>

      {/* Generate button */}
      <button onClick={generatePosts} disabled={generating} style={{
        padding: '14px', borderRadius: '10px',
        background: generating ? 'var(--bg3)' : 'linear-gradient(135deg, #6366f1, #818cf8)',
        border: 'none', color: generating ? 'var(--text3)' : 'white',
        fontSize: '14px', fontWeight: 600, cursor: generating ? 'not-allowed' : 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
      }}>
        {generating
          ? <><RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} /> Generating posts...</>
          : <><Zap size={16} /> Generate {selectedPlatforms.length * selectedTypes.length} Posts with AI</>
        }
      </button>

      {error && (
        <div style={{ padding: '10px 14px', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '8px', fontSize: '13px', color: '#f87171' }}>
          ⚠ {error}
        </div>
      )}

      {/* Generated posts */}
      {posts.length > 0 && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ fontSize: '13px', fontWeight: 600 }}>
              ✅ {posts.length} posts generated
            </div>
            <button onClick={() => {
              const all = posts.map(p => `=== ${p.platform.toUpperCase()} - ${p.type} ===\n${p.content}\n${p.hashtags?.map(h=>'#'+h).join(' ')}\n`).join('\n')
              navigator.clipboard.writeText(all)
            }} style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              padding: '6px 12px', borderRadius: '7px', fontSize: '12px',
              background: 'var(--bg3)', border: '1px solid var(--border)',
              color: 'var(--text2)', cursor: 'pointer',
            }}>
              <Copy size={12} /> Copy All
            </button>
          </div>
          {posts.map((post, i) => (
            <PostCard key={i} post={post} platform={post.platform} />
          ))}
        </div>
      )}
    </div>
  )
}
