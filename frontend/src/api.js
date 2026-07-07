const BASE = "https://sem-ai-production.up.railway.app"

async function fetchWithRetry(url, options, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 120000)
      const res = await fetch(url, { ...options, signal: controller.signal })
      clearTimeout(timeout)
      return res
    } catch (e) {
      if (e.name === "AbortError") throw new Error("Analysis timed out. Please try again.")
      if (i === retries - 1) throw e
      await new Promise(r => setTimeout(r, (i + 1) * 2000))
    }
  }
}

export async function runFullReport({ url, businessDescription, targetKeywords }) {
  const token = localStorage.getItem("sem_token") || ""
  const res = await fetchWithRetry(BASE + "/api/full-report", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": token ? "Bearer " + token : "",
    },
    body: JSON.stringify({
      url,
      business_description: businessDescription,
      target_keywords: targetKeywords,
    }),
  })
  const data = await res.json()

  // Usage limit check
  if (res.status === 429 || (data.detail && data.detail.includes('limit reached'))) {
    throw new Error("USAGE_LIMIT:3:free")
  }

  if (data.error === "usage_limit_exceeded") {
    throw new Error("USAGE_LIMIT:" + data.limit + ":" + data.plan)
  }

  if (!res.ok) {
    throw new Error(data.detail || data.error || "Could not analyse this website. Please check the URL and try again.")
  }

  return data
}
