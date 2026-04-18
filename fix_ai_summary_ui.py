path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

old = """            {/* Summary */}
            <Card>
              <SectionTitle icon={Zap}>AI Summary</SectionTitle>
              <p style={{ color: 'var(--text2)', fontSize: '14px', lineHeight: 1.7 }}>{seo?.ai_summary || seo?.summary || 'AI analysis complete. Check the sections below for detailed insights.'}</p>

              {seo.priority_actions?.length > 0 && (
                <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '8px' }}>
                  {seo.priority_actions.slice(0, 6).map((a, i) => ("""

new = """            {/* Summary */}
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <SectionTitle icon={Zap}>AI Expert Analysis</SectionTitle>
                <div style={{ fontSize: '11px', color: 'var(--text3)', padding: '3px 8px', background: 'var(--bg3)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                  🤖 Gemini 2.5 Flash
                </div>
              </div>
              {(() => {
                const summary = seo?.ai_summary || seo?.summary || ''
                if (!summary) return <p style={{ color: 'var(--text3)', fontSize: '13px' }}>AI analysis complete. Check sections below.</p>
                const sentences = summary.split(/(?<=[.!?])\s+/).filter(s => s.trim())
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {sentences.map((s, i) => (
                      <div key={i} style={{ display: 'flex', gap: '10px', padding: '8px 12px', background: i === 0 ? 'var(--accent-bg)' : 'var(--bg3)', borderRadius: '8px', border: '1px solid ' + (i === 0 ? 'var(--accent-border)' : 'var(--border)') }}>
                        <span style={{ fontSize: '14px', flexShrink: 0 }}>{['🎯','💪','⚠️','🔍','🚀','💡'][i] || '📌'}</span>
                        <span style={{ fontSize: '13px', color: i === 0 ? 'var(--text)' : 'var(--text2)', lineHeight: 1.6 }}>{s}</span>
                      </div>
                    ))}
                  </div>
                )
              })()}

              {seo.priority_actions?.length > 0 && (
                <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '8px' }}>
                  {seo.priority_actions.slice(0, 6).map((a, i) => ("""

if old in content:
    content = content.replace(old, new)
    print("AI Summary UI enhanced!")
else:
    print("ERROR: not found")

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Done!")
