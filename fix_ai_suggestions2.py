path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(path) as f:
    content = f.read()

# Add fix_suggestions to single page prompt
old_fix = '''  "technical_issues": ["Missing meta description", "Images missing alt text"],
  "quick_wins": ["Add meta description (5 min fix)", "Add alt text to 3 images"],
  "recommendations": ["Write a 150-character meta description with primary keyword", "Expand content to 800+ words"],'''

new_fix = '''  "fix_suggestions": [
    {{
      "issue": "Missing Schema Markup",
      "priority": "high",
      "effort": "medium",
      "time_to_fix": "2-3 hours",
      "impact": "Can improve CTR by 20-30% with rich snippets",
      "exact_fix": "Add JSON-LD Product/Organization schema to page <head>",
      "steps": [
        "Open your page HTML file",
        "Add the JSON-LD script tag before </head>",
        "Test using Google Rich Results Test tool"
      ],
      "code_example": "<script type=\\"application/ld+json\\">{{\\n  \\"@context\\": \\"https://schema.org\\",\\n  \\"@type\\": \\"SoftwareApplication\\",\\n  \\"name\\": \\"Product Name\\"\\n}}</script>"
    }}
  ],
  "technical_issues": ["Missing meta description", "Images missing alt text"],
  "quick_wins": ["Add meta description (5 min fix)", "Add alt text to 3 images"],
  "recommendations": ["Write a 150-character meta description with primary keyword", "Expand content to 800+ words"],'''

content = content.replace(old_fix, new_fix)

# Also add to build_seo_prompt_single_page return
old_prompt_fix = '''  "technical_issues": [
    {{"issue": "name", "severity": "critical/high/medium", "description": "what is wrong", "recommendation": "how to fix it"}}
  ],'''

new_prompt_fix = '''  "fix_suggestions": [
    {{
      "issue": "exact issue name from page data",
      "priority": "high/medium/low based on SEO impact",
      "effort": "easy/medium/hard",
      "time_to_fix": "estimated time e.g. 30 minutes",
      "impact": "specific improvement expected",
      "exact_fix": "one line specific fix instruction",
      "steps": ["step 1", "step 2", "step 3"],
      "code_example": "actual HTML/JSON code if applicable"
    }}
  ],
  "technical_issues": [
    {{"issue": "name", "severity": "critical/high/medium", "description": "what is wrong", "recommendation": "how to fix it"}}
  ],'''

content = content.replace(old_prompt_fix, new_prompt_fix)

with open(path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print("ERROR:", e)

# Also update Dashboard to add expandedFix and show code_example
dash_path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(dash_path) as f:
    dcontent = f.read()

# Add expandedFix state
if 'expandedFix' not in dcontent:
    dcontent = dcontent.replace(
        '  const [showAlerts, setShowAlerts] = useState(false)',
        '  const [showAlerts, setShowAlerts] = useState(false)\n  const [expandedFix, setExpandedFix] = useState(null)'
    )
    print("Added expandedFix state!")

# Make fix items clickable with code example
old_fix_item = """                      {items.slice(0, 5).map((fix, i) => {
                        const priorityColor = fix.priority === 'high' ? 'var(--red)' : fix.priority === 'medium' ? 'var(--yellow)' : 'var(--green)'
                        const priorityBg = fix.priority === 'high' ? 'var(--red-bg)' : fix.priority === 'medium' ? 'var(--yellow-bg)' : 'var(--green-bg)'
                        const effortColor = fix.effort === 'easy' ? 'var(--green)' : fix.effort === 'medium' ? 'var(--yellow)' : 'var(--red)'
                        return (
                          <div key={i} style={{ border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden', borderLeft: '3px solid ' + priorityColor }}>
                            {/* Header */}
                            <div style={{ padding: '12px 14px', background: priorityBg, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>"""

new_fix_item = """                      {items.slice(0, 6).map((fix, i) => {
                        const priorityColor = fix.priority === 'high' ? 'var(--red)' : fix.priority === 'medium' ? 'var(--yellow)' : 'var(--green)'
                        const priorityBg = fix.priority === 'high' ? 'var(--red-bg)' : fix.priority === 'medium' ? 'var(--yellow-bg)' : 'var(--green-bg)'
                        const effortColor = fix.effort === 'easy' ? 'var(--green)' : fix.effort === 'medium' ? 'var(--yellow)' : 'var(--red)'
                        return (
                          <div key={i} style={{ border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden', borderLeft: '3px solid ' + priorityColor }}>
                            {/* Header - clickable */}
                            <div onClick={() => setExpandedFix(expandedFix === i ? null : i)} style={{ padding: '12px 14px', background: priorityBg, display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}>"""

dcontent = dcontent.replace(old_fix_item, new_fix_item)

# Add code_example display after steps
old_steps_end = """                              {fix.steps?.length > 0 && (
                                <div style={{ marginTop: '10px' }}>
                                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>Step-by-Step:</div>
                                  {fix.steps.map((step, j) => (
                                    <div key={j} style={{ display: 'flex', gap: '8px', marginBottom: '4px', alignItems: 'flex-start' }}>
                                      <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent)', background: 'var(--accent-bg)', width: '20px', height: '20px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{j+1}</span>
                                      <span style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.5 }}>{step}</span>
                                    </div>
                                  ))}
                                </div>
                              )}"""

new_steps_end = """                              {fix.steps?.length > 0 && (
                                <div style={{ marginTop: '10px' }}>
                                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>Step-by-Step:</div>
                                  {fix.steps.map((step, j) => (
                                    <div key={j} style={{ display: 'flex', gap: '8px', marginBottom: '4px', alignItems: 'flex-start' }}>
                                      <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent)', background: 'var(--accent-bg)', width: '20px', height: '20px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{j+1}</span>
                                      <span style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.5 }}>{step}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                              {fix.code_example && (
                                <div style={{ marginTop: '10px' }}>
                                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '4px', textTransform: 'uppercase' }}>Code Example:</div>
                                  <pre style={{ background: 'var(--bg4)', padding: '10px 12px', borderRadius: '7px', fontSize: '11px', color: 'var(--cyan)', overflowX: 'auto', margin: 0, lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{fix.code_example}</pre>
                                </div>
                              )}"""

dcontent = dcontent.replace(old_steps_end, new_steps_end)

with open(dash_path, 'w') as f:
    f.write(dcontent)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(dcontent)
print("Done! expandedFix:", 'expandedFix' in dcontent)
