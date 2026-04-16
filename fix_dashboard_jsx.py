path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Fix the unclosed conditional cards
# Budget card was changed to {!showGoogleScore && <Card> but never closed properly
old = """              {!showGoogleScore && <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Budget Range</div>"""

# Find what comes after and fix structure
idx = content.find(old)
print("Budget card at:", idx)
print("Context after:", content[idx:idx+100])

# Simpler approach - revert showGoogleScore changes to cards and just hide PageSpeed card
# Remove the showGoogleScore grid change
content = content.replace(
    "gridTemplateColumns: showGoogleScore && pageSpeed ? '1fr' : 'repeat(auto-fit, minmax(220px, 1fr))'",
    "gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))'"
)

# Revert budget card
content = content.replace(
    "              {!showGoogleScore && <Card>\n                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Budget Range</div>",
    "              <Card>\n                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Budget Range</div>"
)

# Keep PageSpeed card hidden until showGoogleScore
# Already done correctly

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Fixed!")
