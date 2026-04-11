import { useState, useEffect } from 'react'

export default function ThemeToggle() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light')

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.setAttribute('data-theme', 'dark')
    } else if (theme === 'light') {
      root.setAttribute('data-theme', 'light')
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      root.setAttribute('data-theme', prefersDark ? 'dark' : 'light')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  const options = [
    { id: 'light', label: '☀ Light' },
    { id: 'dark', label: '☾ Dark' },
    { id: 'system', label: '⊙ Auto' },
  ]

  return (
    <div style={{
      display: 'flex', background: 'var(--bg3)',
      borderRadius: '6px', padding: '2px', gap: '1px',
    }}>
      {options.map(o => (
        <button key={o.id} onClick={() => setTheme(o.id)} style={{
          flex: 1, padding: '4px 8px', borderRadius: '5px', border: 'none',
          background: theme === o.id ? 'var(--bg)' : 'transparent',
          color: theme === o.id ? 'var(--accent)' : 'var(--text3)',
          fontSize: '11px', fontWeight: theme === o.id ? 500 : 400,
          boxShadow: theme === o.id ? 'var(--shadow)' : 'none',
          transition: 'all 0.15s', cursor: 'pointer',
        }}>{o.label}</button>
      ))}
    </div>
  )
}
