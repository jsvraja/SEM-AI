const BASE = 'https://sem-ai-production.up.railway.app'

export async function runFullReport({ url, businessDescription, targetKeywords }) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 120000)
  
  try {
    const res = await fetch(`${BASE}/api/full-report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        business_description: businessDescription,
        target_keywords: targetKeywords,
      }),
      signal: controller.signal,
    })
    clearTimeout(timeout)
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || 'Request failed')
    }
    return res.json()
  } catch (e) {
    clearTimeout(timeout)
    if (e.name === 'AbortError') throw new Error('Analysis is taking longer than expected. Please try again.')
    throw e
  }
}
