import os

path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(path) as f:
    content = f.read()

# 1. Enhance scraper to collect actual link data
old_links = """    internal_links = [l["href"] for l in all_links if url in l["href"] or l["href"].startswith("/")]
    external_links = [l["href"] for l in all_links if l["href"].startswith("http") and url not in l["href"]]"""

new_links = """    from urllib.parse import urlparse as _urlparse
    _base = _urlparse(url).netloc
    internal_links_raw = []
    external_links_raw = []
    for l in all_links:
        href = l.get("href", "").strip()
        text = l.get_text(strip=True)[:50]
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        if href.startswith("/") or _base in href:
            internal_links_raw.append({"url": href, "text": text})
        elif href.startswith("http"):
            external_links_raw.append({"url": href, "text": text})
    internal_links = internal_links_raw
    external_links = external_links_raw[:20]
    
    # Nofollow links
    nofollow_count = len([l for l in all_links if 'nofollow' in (l.get('rel') or [])])
    
    # Anchor text analysis
    anchor_texts = [l.get_text(strip=True) for l in all_links if l.get_text(strip=True)]
    empty_anchors = len([a for a in anchor_texts if not a or a.lower() in ['click here', 'here', 'read more', 'more']])"""

content = content.replace(old_links, new_links)

# 2. Update return to include link data
old_return_links = """            "internal_links_count": scraped["internal_links_count"],
            "has_schema_markup": scraped["has_schema_markup"],"""

new_return_links = """            "internal_links_count": scraped["internal_links_count"],
            "external_links_count": scraped.get("external_links_count", 0),
            "internal_links_sample": scraped.get("internal_links_sample", []),
            "external_links_sample": scraped.get("external_links_sample", []),
            "nofollow_count": scraped.get("nofollow_count", 0),
            "empty_anchors": scraped.get("empty_anchors", 0),
            "has_schema_markup": scraped["has_schema_markup"],"""

content = content.replace(old_return_links, new_return_links)

# 3. Update scraper return to include link samples
old_scraper_return = """        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),"""

new_scraper_return = """        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "internal_links_sample": internal_links[:15],
        "external_links_sample": external_links[:10],
        "nofollow_count": nofollow_count,
        "empty_anchors": empty_anchors,"""

content = content.replace(old_scraper_return, new_scraper_return)

with open(path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Backend Syntax OK!")
except py_compile.PyCompileError as e:
    print("Backend ERROR:", e)

# 4. Add Link Analysis card to SEO Report in Dashboard
dash_path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(dash_path) as f:
    dcontent = f.read()

old_marker = """            {/* Keywords */}
            <Card>
              <SectionTitle icon={Search}>Keyword Suggestions & Match Strength</SectionTitle>"""

new_link_card = """            {/* Link Analysis */}
            <Card>
              <SectionTitle icon={Globe}>Link Analysis</SectionTitle>
              {(() => {
                const intLinks = sc?.internal_links_count || 0
                const extLinks = sc?.external_links_count || 0
                const nofollowCount = sc?.nofollow_count || 0
                const emptyAnchors = sc?.empty_anchors || 0
                const intSample = sc?.internal_links_sample || []
                const extSample = sc?.external_links_sample || []
                const totalLinks = intLinks + extLinks
                const intPct = totalLinks > 0 ? Math.round((intLinks/totalLinks)*100) : 0
                const extPct = totalLinks > 0 ? Math.round((extLinks/totalLinks)*100) : 0

                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {/* Summary metrics */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                      {[
                        { label: 'Internal Links', value: intLinks, color: intLinks >= 10 ? 'var(--green)' : intLinks >= 5 ? 'var(--yellow)' : 'var(--red)', tip: 'Links pointing to pages within your site' },
                        { label: 'External Links', value: extLinks, color: 'var(--cyan)', tip: 'Links pointing to other websites' },
                        { label: 'Nofollow Links', value: nofollowCount, color: nofollowCount > 0 ? 'var(--yellow)' : 'var(--green)', tip: 'Links with rel=nofollow attribute' },
                        { label: 'Weak Anchors', value: emptyAnchors, color: emptyAnchors > 3 ? 'var(--red)' : emptyAnchors > 0 ? 'var(--yellow)' : 'var(--green)', tip: 'Links with generic text like "click here", "here", "read more"' },
                      ].map(({ label, value, color, tip }) => (
                        <div key={label} style={{ padding: '10px', background: 'var(--bg3)', borderRadius: '8px', textAlign: 'center' }} title={tip}>
                          <div style={{ fontSize: '22px', fontWeight: 700, color }}>{value}</div>
                          <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '2px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
                        </div>
                      ))}
                    </div>

                    {/* Internal vs External ratio bar */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontSize: '12px', color: 'var(--text3)' }}>Link Distribution</span>
                        <span style={{ fontSize: '12px', color: 'var(--text3)' }}>Internal {intPct}% / External {extPct}%</span>
                      </div>
                      <div style={{ height: '8px', background: 'var(--bg4)', borderRadius: '4px', overflow: 'hidden', display: 'flex' }}>
                        <div style={{ height: '100%', width: intPct + '%', background: 'var(--accent)', borderRadius: '4px 0 0 4px' }} />
                        <div style={{ height: '100%', width: extPct + '%', background: 'var(--cyan)' }} />
                      </div>
                      <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
                        <span style={{ fontSize: '10px', color: 'var(--accent)' }}>■ Internal</span>
                        <span style={{ fontSize: '10px', color: 'var(--cyan)' }}>■ External</span>
                      </div>
                    </div>

                    {/* Health indicators */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {[
                        { label: 'Internal linking', status: intLinks >= 10 ? 'good' : intLinks >= 5 ? 'warn' : 'bad', msg: intLinks >= 10 ? 'Strong internal linking (' + intLinks + ' links)' : intLinks >= 5 ? intLinks + ' internal links — aim for 10+' : 'Only ' + intLinks + ' internal links — add more for better crawlability' },
                        { label: 'Anchor text quality', status: emptyAnchors === 0 ? 'good' : emptyAnchors <= 3 ? 'warn' : 'bad', msg: emptyAnchors === 0 ? 'All anchor texts are descriptive' : emptyAnchors + ' generic anchor texts (click here, read more) — use descriptive text' },
                        { label: 'External links', status: extLinks > 0 && extLinks <= 50 ? 'good' : extLinks > 50 ? 'warn' : 'warn', msg: extLinks > 0 ? extLinks + ' external links found — ensure they are authoritative sources' : 'No external links — add relevant external references' },
                      ].map(({ label, status, msg }) => {
                        const c = status === 'good' ? 'var(--green)' : status === 'warn' ? 'var(--yellow)' : 'var(--red)'
                        const icon = status === 'good' ? '✅' : status === 'warn' ? '⚠️' : '❌'
                        return (
                          <div key={label} style={{ display: 'flex', gap: '8px', padding: '8px 10px', background: 'var(--bg3)', borderRadius: '7px' }}>
                            <span>{icon}</span>
                            <div>
                              <div style={{ fontSize: '11px', fontWeight: 600, color: c }}>{label}</div>
                              <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{msg}</div>
                            </div>
                          </div>
                        )
                      })}
                    </div>

                    {/* Internal links sample */}
                    {intSample.length > 0 && (
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>🔗 Internal Links Sample</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '150px', overflowY: 'auto' }}>
                          {intSample.slice(0, 8).map((link, i) => (
                            <div key={i} style={{ display: 'flex', gap: '8px', fontSize: '11px', padding: '4px 8px', background: 'var(--bg3)', borderRadius: '5px' }}>
                              <span style={{ color: 'var(--accent)', flexShrink: 0 }}>→</span>
                              <span style={{ color: 'var(--text2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{link.text || link.url}</span>
                              <span style={{ color: 'var(--text3)', flexShrink: 0, marginLeft: 'auto' }}>{(link.url || '').slice(0, 30)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* External links sample */}
                    {extSample.length > 0 && (
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>🌐 External Links Sample</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '120px', overflowY: 'auto' }}>
                          {extSample.slice(0, 5).map((link, i) => (
                            <div key={i} style={{ display: 'flex', gap: '8px', fontSize: '11px', padding: '4px 8px', background: 'var(--bg3)', borderRadius: '5px' }}>
                              <span style={{ color: 'var(--cyan)', flexShrink: 0 }}>↗</span>
                              <span style={{ color: 'var(--text2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{link.text || link.url}</span>
                            </div>
                          ))}
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

if old_marker in dcontent:
    dcontent = dcontent.replace(old_marker, new_link_card)
    print("Link Analysis card added!")
else:
    print("ERROR: marker not found")

with open(dash_path, 'w') as f:
    f.write(dcontent)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(dcontent)
print("Done! Size:", len(dcontent))
