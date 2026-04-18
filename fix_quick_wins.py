path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Add Quick Wins card after AI Summary
old = """            {/* SERP Preview */}"""

new = """            {/* Quick Win Suggestions */}
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

            {/* SERP Preview */}"""

if old in content:
    content = content.replace(old, new)
    print("Quick Wins added!")
else:
    print("ERROR: marker not found")

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Done! Size:", len(content))
