// Central API configuration
// Uses VITE_API_URL env var in production, falls back to Railway URL
export const BASE = import.meta.env.VITE_API_URL || 'https://sem-ai-production.up.railway.app'
