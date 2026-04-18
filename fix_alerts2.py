path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    c = f.read()

# Find and replace the alerts section
start = c.find('  const [alerts, setAlerts] = useState([])')
end = c.find('  }, [seo?.overall_seo_score])', start)
if end > 0:
    end += len('  }, [seo?.overall_seo_score])')
    old = c[start:end]
    print("Found section length:", len(old))
    
    new = """  const [showAlerts, setShowAlerts] = useState(false)

  const alerts = (() => {
    if (!seo) return []
    const a = []
    const score = seo?.overall_seo_score || 0
    const meta = sc?.meta_description || ''
    const imgMissing = sc?.images_without_alt_count || 0
    const title = sc?.title || ''
    if (score < 50) a.push({ type: 'critical', icon: '🚨', title: 'Critical SEO Score', msg: 'Score is ' + score + '/100 — urgent fixes needed', time: 'Just now' })
    else if (score < 70) a.push({ type: 'warning', icon: '⚠️', title: 'Low SEO Score', msg: 'Score is ' + score + '/100 — improvements needed', time: 'Just now' })
    if (!meta || meta.length < 50) a.push({ type: 'critical', icon: '📝', title: 'Meta Description Issue', msg: 'Missing or too short meta hurts CTR by 30%', time: 'Just now' })
    if (meta && meta.length > 160) a.push({ type: 'warning', icon: '✂️', title: 'Meta Too Long', msg: 'Meta is ' + meta.length + ' chars — truncated at 160', time: 'Just now' })
    if (imgMissing > 0) a.push({ type: 'warning', icon: '🖼️', title: imgMissing + ' Images Missing Alt', msg: 'Affects accessibility and SEO', time: 'Just now' })
    if (!title) a.push({ type: 'critical', icon: '🏷️', title: 'Page Title Missing', msg: 'Critical for SEO rankings', time: 'Just now' })
    return a
  })()"""
    
    c = c[:start] + new + c[end:]
    print("Replaced!")
else:
    print("End marker not found, trying alternative...")
    # Remove useEffect style
    start2 = c.find('  const [alerts, setAlerts] = useState([])\n  const [showAlerts')
    if start2 > 0:
        end2 = c.find('\n  const [showAlerts', start2) + 1
        print("Found at:", start2, "to", end2)

# Remove useEffect import if no longer needed
if 'useEffect(() =>' not in c and 'useEffect(' not in c[c.find('return ('):]:
    c = c.replace("import { useState, useEffect } from 'react'", "import { useState } from 'react'")
    print("Removed useEffect import")

with open(path, 'w') as f:
    f.write(c)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(c)
print("Done! alerts as computed:", 'const alerts = (() =>' in c)
