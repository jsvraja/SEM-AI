import os

# 1. Enhance backend to return detailed fix suggestions
main_path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(main_path) as f:
    content = f.read()

# Add fix_suggestions to single page prompt
old_weaknesses = '''  "weaknesses": [
    {{"point": "weakness", "fix": "specific actionable fix", "impact": "high/medium/low"}}
  ],'''

new_weaknesses = '''  "weaknesses": [
    {{"point": "weakness", "fix": "specific actionable fix", "impact": "high/medium/low"}}
  ],
  "fix_suggestions": [
    {{
      "issue": "Missing Schema Markup",
      "priority": "high",
      "effort": "medium",
      "time_to_fix": "2-3 hours",
      "impact": "Can increase CTR by 20-30% through rich snippets",
      "exact_fix": "Add this JSON-LD to your <head> tag",
      "code_snippet": "<script type=\\"application/ld+json\\">{{\\n  \\"@context\\": \\"https://schema.org\\",\\n  \\"@type\\": \\"SoftwareApplication\\",\\n  \\"name\\": \\"Your Product Name\\",\\n  \\"description\\": \\"Your meta description\\"\\n}}</script>",
      "steps": ["Open your HTML file or CMS", "Add the JSON-LD script to <head>", "Validate at schema.org/validator", "Submit URL to Google Search Console"]
    }}
  ],'''

content = content.replace(old_weaknesses, new_weaknesses)

with open(main_path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(main_path, doraise=True)
    print("Backend Syntax OK!")
except py_compile.PyCompileError as e:
    print("Backend ERROR:", e)

# 2. Add AI Fix Suggestions card to SEO Report tab
dash_path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(dash_path) as f:
    dcontent = f.read()

# Add after Technical Issues card
old_marker = """            {/* Content Analysis Deep Dive */}"""

new_fix_card = """            {/* AI Fix Suggestions */}
            {(seo?.fix_suggestions?.length > 0 || seo?.weaknesses?.length > 0) && (
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <SectionTitle icon={Zap}>AI Fix Suggestions</SectionTitle>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', padding: '3px 8px', background: 'var(--bg3)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                    🤖 Exact steps to fix each issue
                  </div>
                </div>
                {(() => {
                  const fixes = seo?.fix_suggestions || []
                  // If no fix_suggestions, generate from weaknesses
                  const items = fixes.length > 0 ? fixes : (seo?.weaknesses || []).map(w => ({
                    issue: w.point,
                    priority: w.impact || 'medium',
                    effort: 'medium',
                    time_to_fix: '1-2 hours',
                    impact: w.impact === 'high' ? 'Significant improvement to SEO score' : 'Moderate improvement',
                    exact_fix: w.fix || 'See recommendation below',
                    steps: [w.fix || 'Review and fix this issue'].filter(Boolean)
                  }))
                  
                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {items.slice(0, 5).map((fix, i) => {
                        const priorityColor = fix.priority === 'high' ? 'var(--red)' : fix.priority === 'medium' ? 'var(--yellow)' : 'var(--green)'
                        const priorityBg = fix.priority === 'high' ? 'var(--red-bg)' : fix.priority === 'medium' ? 'var(--yellow-bg)' : 'var(--green-bg)'
                        const effortColor = fix.effort === 'easy' ? 'var(--green)' : fix.effort === 'medium' ? 'var(--yellow)' : 'var(--red)'
                        return (
                          <div key={i} style={{ border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden', borderLeft: '3px solid ' + priorityColor }}>
                            {/* Header */}
                            <div style={{ padding: '12px 14px', background: priorityBg, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '16px' }}>{fix.priority === 'high' ? '🚨' : fix.priority === 'medium' ? '⚠️' : '💡'}</span>
                                <span style={{ fontSize: '13px', fontWeight: 700, color: priorityColor }}>{fix.issue}</span>
                              </div>
                              <div style={{ display: 'flex', gap: '6px' }}>
                                <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: priorityBg, border: '1px solid ' + priorityColor, color: priorityColor, fontWeight: 600 }}>{(fix.priority || 'medium').toUpperCase()} PRIORITY</span>
                                <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text3)' }}>⏱ {fix.time_to_fix || '1-2 hours'}</span>
                              </div>
                            </div>
                            
                            <div style={{ padding: '12px 14px' }}>
                              {/* Impact */}
                              {fix.impact && (
                                <div style={{ fontSize: '12px', color: 'var(--green)', marginBottom: '10px', padding: '6px 10px', background: 'var(--green-bg)', borderRadius: '6px' }}>
                                  📈 Expected Impact: {fix.impact}
                                </div>
                              )}

                              {/* Exact fix */}
                              {fix.exact_fix && (
                                <div style={{ marginBottom: '10px' }}>
                                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '4px', textTransform: 'uppercase' }}>What to do:</div>
                                  <div style={{ fontSize: '13px', color: 'var(--text2)', lineHeight: 1.6 }}>{fix.exact_fix}</div>
                                </div>
                              )}

                              {/* Code snippet */}
                              {fix.code_snippet && (
                                <div style={{ marginBottom: '10px' }}>
                                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '4px', textTransform: 'uppercase' }}>Code to add:</div>
                                  <pre style={{ fontSize: '11px', background: 'var(--bg4)', padding: '10px', borderRadius: '8px', overflow: 'auto', color: 'var(--cyan)', lineHeight: 1.5, margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{fix.code_snippet}</pre>
                                </div>
                              )}

                              {/* Steps */}
                              {fix.steps?.length > 0 && (
                                <div>
                                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>Step-by-step:</div>
                                  {fix.steps.map((step, j) => (
                                    <div key={j} style={{ display: 'flex', gap: '8px', marginBottom: '4px', alignItems: 'flex-start' }}>
                                      <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent)', background: 'var(--accent-bg)', width: '20px', height: '20px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{j+1}</span>
                                      <span style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.5 }}>{step}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )
                })()}
              </Card>
            )}

            {/* Content Analysis Deep Dive */}"""

if old_marker in dcontent:
    dcontent = dcontent.replace(old_marker, new_fix_card)
    print("AI Fix Suggestions added!")
else:
    print("ERROR: marker not found")

with open(dash_path, 'w') as f:
    f.write(dcontent)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(dcontent)
print("Done! Size:", len(dcontent))
