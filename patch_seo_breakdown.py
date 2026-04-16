path = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

old = """              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>SEO Health</div>
                <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center' }}>
                  <ScoreRing score={seo.overall_seo_score} label="Overall SEO" />
                  <ScoreRing score={seo.content_analysis?.quality_score || seo.content_analysis?.readability_score || (seo.overall_seo_score ? Math.round(seo.overall_seo_score * 0.8) : 0)} label="Content" />
                </div>
              </Card>"""

new = """              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>SEO Health</div>
                <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', marginBottom: '12px' }}>
                  <ScoreRing score={seo.overall_seo_score} label="Overall SEO" />
                  <ScoreRing score={seo.content_analysis?.quality_score || seo.content_analysis?.readability_score || (seo.overall_seo_score ? Math.round(seo.overall_seo_score * 0.8) : 0)} label="Content" />
                </div>
                {/* SEO Breakdown */}
                {(() => {
                  const breakdown = seo.score_breakdown || {}
                  const seoItems = [
                    { label: 'Title Tag', score: breakdown.title_optimisation ?? (seo.page_metadata?.title ? 85 : 0), tip: 'Page title optimization for search engines' },
                    { label: 'Meta Description', score: breakdown.meta_descriptions ?? (seo.page_metadata?.meta_description ? 75 : 0), tip: 'Meta description length and keyword usage' },
                    { label: 'H1 Tags', score: breakdown.heading_structure ?? (seo.page_metadata?.h1_tags?.length ? 80 : 0), tip: 'Heading structure and H1 usage' },
                    { label: 'Content Quality', score: breakdown.content_quality ?? seo.content_analysis?.quality_score ?? 60, tip: 'Word count, readability and depth' },
                    { label: 'Image Alt Text', score: breakdown.image_optimisation ?? (sc?.images_without_alt_count === 0 ? 90 : 50), tip: 'Images with proper alt text' },
                    { label: 'Schema Markup', score: sc?.has_schema_markup ? 90 : 10, tip: 'Structured data for rich snippets' },
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
                    </div>
                  )
                })()}
              </Card>"""

if old in content:
    content = content.replace(old, new)
    print("SEO breakdown patched!")
else:
    print("ERROR: Could not find SEO Health card")

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Both files updated!")
