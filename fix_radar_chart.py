path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Add RadarChart import to recharts
old_recharts = """  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, PieChart, Pie, Cell, Legend"""

new_recharts = """  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, PieChart, Pie, Cell, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis"""

content = content.replace(old_recharts, new_recharts)

# Add Radar Chart card after URL type banner in SEO tab
old_seo = """            {/* Meta info */}
            <Card>
              <SectionTitle icon={Globe}>Page Metadata</SectionTitle>"""

new_seo = """            {/* SEO Score Radar Chart */}
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
              <SectionTitle icon={Globe}>Page Metadata</SectionTitle>"""

if old_seo in content:
    content = content.replace(old_seo, new_seo)
    print("Radar chart added!")
else:
    print("ERROR: marker not found")

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Done! Size:", len(content))
