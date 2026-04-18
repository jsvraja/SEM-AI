path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

old_marker = """            {/* Keywords */}
            <Card>
              <SectionTitle icon={Search}>Keyword Suggestions & Match Strength</SectionTitle>"""

new_content = """            {/* Content Analysis Deep Dive */}
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

            {/* Keywords */}
            <Card>
              <SectionTitle icon={Search}>Keyword Suggestions & Match Strength</SectionTitle>"""

if old_marker in content:
    content = content.replace(old_marker, new_content)
    print("Content Analysis added!")
else:
    print("ERROR: marker not found")

# Add FileText import if missing
if 'FileText' not in content:
    content = content.replace(
        'TrendingUp, DollarSign, Target,',
        'TrendingUp, DollarSign, Target, FileText,'
    )
    print("Added FileText import!")

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Done! Size:", len(content))
