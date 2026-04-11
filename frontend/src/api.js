const BASE = 'https://sem-ai-production.up.railway.app'

export async function runFullReport({ url, businessDescription, targetKeywords }) {
  const res = await fetch(`${BASE}/api/full-report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      business_description: businessDescription,
      target_keywords: targetKeywords,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}
