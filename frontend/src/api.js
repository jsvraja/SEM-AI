const BASE = 'https://sem-ai-production.up.railway.app'

export async function runFullReport({ url, businessDescription, targetKeywords }) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 120000)
  
  try {
    const token = localStorage.getItem('sem_token') || ''
    const res = await fetch(`${BASE}/api/full-report`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify({
        url,
        business_description: businessDescription,
        target_keywords: targetKeywords,
      }),
      signal: controller.signal,
    })
    clearTimeout(timeout)
    const data = await res.json()
    if (data.error === 'usage_limit_exceeded') {
      throw new Error(`USAGE_LIMIT:${data.limit}:${data.plan}`)
    }
    if (!res.ok) {
      throw new Error(data.detail || 'Request failed')
    }
    return data
  } catch (e) {
    clearTimeout(timeout)
    if (e.name === 'AbortError') throw new Error('Analysis is taking longer than expected. Please try again.')
    throw e
  }
}
