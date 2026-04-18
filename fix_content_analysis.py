import re

# 1. Enhance backend content_analysis prompt
main_path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(main_path) as f:
    content = f.read()

# Fix single page content_analysis
old_ca = '''  "content_analysis": {{
    "word_count": {s.get('word_count', 0)},
    "readability": "Good",
    "keyword_density": "2.3%",
    "content_gaps": ["Add FAQ section", "Include comparison table"]
  }},
  "technical_issues": ["Missing meta description", "Images missing alt text"],
  "quick_wins": ["Add meta description (5 min fix)", "Add alt text to 3 images"],
  "recommendations": ["Write a 150-character meta description with primary keyword", "Expand content to 800+ words"],'''

new_ca = '''  "content_analysis": {{
    "word_count": {s.get('word_count', 0)},
    "readability": "Good — use Flesch Reading Ease score (0-100, higher is easier)",
    "reading_level": "Grade 8 — suitable for general audience",
    "keyword_density": "2.3% — analyse top 3 keywords from content",
    "primary_keyword": "most prominent keyword found in title+h1+content",
    "keyword_in_title": true,
    "keyword_in_meta": true,
    "keyword_in_h1": true,
    "content_score": 70,
    "content_gaps": ["Add FAQ section", "Include comparison table", "Add customer testimonials"],
    "tone": "Professional",
    "language": "English",
    "has_cta": true,
    "cta_text": "Get Started / Download / Contact Us etc",
    "content_strengths": ["Clear value proposition", "Technical depth"],
    "content_weaknesses": ["Thin content under 500 words", "No FAQ section"]
  }},
  "technical_issues": ["Missing meta description", "Images missing alt text"],
  "quick_wins": ["Add meta description (5 min fix)", "Add alt text to 3 images"],
  "recommendations": ["Write a 150-character meta description with primary keyword", "Expand content to 800+ words"],'''

content = content.replace(old_ca, new_ca)

with open(main_path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(main_path, doraise=True)
    print("Backend Syntax OK!")
except py_compile.PyCompileError as e:
    print("Backend ERROR:", e)

# 2. Add Content Analysis Deep Dive card to SEO Report tab
dash_path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(dash_path) as f:
    dcontent = f.read()

# Add after Strengths & Weaknesses section - find the keyword suggestions card
old_marker = """            {/* Keyword suggestions */}"""

new_content_card = """            {/* Content Analysis Deep Dive */}
            <Card>
              <SectionTitle icon={FileText}>Content Analysis</SectionTitle>
              {(() => {
                const ca = seo?.content_analysis || {}
                const wordCount = ca.word_count || sc?.word_count || 0
                const readability = ca.readability || 'N/A'
                const readingLevel = ca.reading_level || 'N/A'
                const keywordDensity = ca.keyword_density || 'N/A'
                const primaryKeyword = ca.primary_keyword || 'N/A'
                const contentScore = ca.content_score || ca.quality_score || 0
                const gaps = ca.content_gaps || []
                const tone = ca.tone || 'N/A'
                const hasCTA = ca.has_cta
                const ctaText = ca.cta_text || ''
                const strengths = ca.content_strengths || []
                const weaknesses = ca.content_weaknesses || []
                const kwInTitle = ca.keyword_in_title
                const kwInMeta = ca.keyword_in_meta
                const kwInH1 = ca.keyword_in_h1

                const wordStatus = wordCount >= 800 ? 'good' : wordCount >= 400 ? 'warn' : 'bad'
                const wordColor = wordStatus === 'good' ? 'var(--green)' : wordStatus === 'warn' ? 'var(--yellow)' : 'var(--red)'

                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {/* Top metrics */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px' }}>
                      {[
                        { label: 'Word Count', value: wordCount, unit: ' words', color: wordColor, tip: wordCount >= 800 ? '✓ Good' : 'Need 800+' },
                        { label: 'Content Score', value: contentScore, unit: '/100', color: contentScore >= 70 ? 'var(--green)' : contentScore >= 40 ? 'var(--yellow)' : 'var(--red)', tip: 'AI quality score' },
                        { label: 'Readability', value: readability.split('—')[0].trim(), unit: '', color: 'var(--cyan)', tip: readability },
                        { label: 'Reading Level', value: readingLevel.split('—')[0].trim(), unit: '', color: 'var(--text2)', tip: readingLevel },
                        { label: 'Tone', value: tone, unit: '', color: 'var(--purple)', tip: 'Content tone' },
                        { label: 'CTA Present', value: hasCTA ? '✓ Yes' : '✗ No', unit: '', color: hasCTA ? 'var(--green)' : 'var(--red)', tip: ctaText || 'Call to action' },
                      ].map(({ label, value, unit, color, tip }) => (
                        <div key={label} style={{ padding: '10px', background: 'var(--bg3)', borderRadius: '8px', textAlign: 'center' }} title={tip}>
                          <div style={{ fontSize: '16px', fontWeight: 700, color }}>{value}{unit}</div>
                          <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '2px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
                        </div>
                      ))}
                    </div>

                    {/* Keyword usage */}
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text2)', marginBottom: '8px' }}>🔑 Primary Keyword: <span style={{ color: 'var(--accent)' }}>"{primaryKeyword}"</span> — Density: {keywordDensity}</div>
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        {[
                          { label: 'In Title', val: kwInTitle },
                          { label: 'In Meta', val: kwInMeta },
                          { label: 'In H1', val: kwInH1 },
                        ].map(({ label, val }) => (
                          <div key={label} style={{ padding: '4px 10px', borderRadius: '6px', background: val ? 'var(--green-bg)' : 'var(--red-bg)', border: '1px solid ' + (val ? 'var(--green)' : 'var(--red)'), fontSize: '12px', fontWeight: 600, color: val ? 'var(--green)' : 'var(--red)' }}>
                            {val ? '✓' : '✗'} {label}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Word count bar */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontSize: '12px', color: 'var(--text3)' }}>Content Length</span>
                        <span style={{ fontSize: '12px', fontWeight: 700, color: wordColor }}>{wordCount} / 800+ words recommended</span>
                      </div>
                      <div style={{ height: '8px', background: 'var(--bg4)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: Math.min(100, (wordCount/800)*100) + '%', background: wordColor, borderRadius: '4px' }} />
                      </div>
                    </div>

                    {/* Content Strengths & Weaknesses */}
                    {(strengths.length > 0 || weaknesses.length > 0) && (
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                        <div>
                          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--green)', marginBottom: '6px', textTransform: 'uppercase' }}>💪 Content Strengths</div>
                          {strengths.map((s, i) => (
                            <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '4px', paddingLeft: '8px', borderLeft: '2px solid var(--green)' }}>✓ {s}</div>
                          ))}
                        </div>
                        <div>
                          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--red)', marginBottom: '6px', textTransform: 'uppercase' }}>⚠ Content Weaknesses</div>
                          {weaknesses.map((w, i) => (
                            <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '4px', paddingLeft: '8px', borderLeft: '2px solid var(--red)' }}>✗ {w}</div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Content Gaps */}
                    {gaps.length > 0 && (
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>📋 Content Gaps to Fill</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {gaps.map((g, i) => (
                            <span key={i} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '6px', background: 'var(--yellow-bg)', border: '1px solid var(--yellow)', color: 'var(--yellow)', fontWeight: 500 }}>+ {g}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })()}
            </Card>

            {/* Keyword suggestions */}"""

if old_marker in dcontent:
    dcontent = dcontent.replace(old_marker, new_content_card)
    print("Content Analysis card added!")
else:
    print("ERROR: marker not found")

# Add FileText to lucide imports if missing
if 'FileText' not in dcontent:
    dcontent = dcontent.replace(
        'TrendingUp, DollarSign, Target,',
        'TrendingUp, DollarSign, Target, FileText,'
    )
    print("Added FileText import!")

with open(dash_path, 'w') as f:
    f.write(dcontent)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(dcontent)

print("Done! Size:", len(dcontent))
