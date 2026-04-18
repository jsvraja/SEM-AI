path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Add SERP Preview after AI Summary card
old = """            {/* Charts row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>"""

new = """            {/* SERP Preview */}
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
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>"""

if old in content:
    content = content.replace(old, new)
    print("SERP Preview added!")
else:
    print("ERROR: marker not found")

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)

print("Done! Size:", len(content))
