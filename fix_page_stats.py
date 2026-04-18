path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

old = """              <Card>
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
              </Card>"""

new = """              <Card>
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
              </Card>"""

if old in content:
    content = content.replace(old, new)
    print("Page Stats enhanced!")
else:
    print("ERROR: not found")

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Done! Size:", len(content))
