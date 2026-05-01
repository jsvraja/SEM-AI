import { useState, useEffect } from 'react'
import { Users, TrendingUp, Shield, Trash2, Crown, Loader2, AlertCircle, ArrowLeft } from 'lucide-react'

const API = 'https://sem-ai-production.up.railway.app'

export default function AdminPanel({ user, token: tokenProp, onBack }) {
  const token = tokenProp || localStorage.getItem('sem_token') || ''
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updatingId, setUpdatingId] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  async function fetchData() {
    setLoading(true)
    try {
      const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache' }
      const [statsRes, usersRes] = await Promise.all([
        fetch(`${API}/api/admin/stats`, { headers }),
        fetch(`${API}/api/admin/users`, { headers }),
      ])
      const statsData = await statsRes.json()
      const usersData = await usersRes.json()
      console.log('Stats response:', statsData)
      console.log('Users response:', usersData)
      if (statsData.error) { setError('Stats error: ' + statsData.error); return }
      if (usersData.error) { setError('Users error: ' + usersData.error); return }
      setStats(statsData)
      setUsers(usersData.users || [])
    } catch (e) {
      setError('Failed to load admin data')
    } finally {
      setLoading(false)
    }
  }

  async function updatePlan(userId, plan) {
    setUpdatingId(userId)
    try {
      const res = await fetch(`${API}/api/admin/users/${userId}/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ plan }),
      })
      const data = await res.json()
      if (data.success) {
        setUsers(prev => prev.map(u => u.id === userId ? { ...u, plan } : u))
      }
    } finally {
      setUpdatingId(null)
    }
  }

  async function deleteUser(userId, email) {
    if (!confirm(`Delete user ${email}?`)) return
    setUpdatingId(userId)
    try {
      const res = await fetch(`${API}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      if (data.success) setUsers(prev => prev.filter(u => u.id !== userId))
    } finally {
      setUpdatingId(null)
    }
  }

  const planColors = { free: '#6b7280', pro: '#3b82f6', agency: '#8b5cf6' }
  const planBg = { free: 'var(--bg3)', pro: 'rgba(59,130,246,0.1)', agency: 'rgba(139,92,246,0.1)' }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', color: 'var(--text)', padding: '24px' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '28px' }}>
          <button onClick={onBack} style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'none', border: '1px solid var(--border)', borderRadius: '8px', padding: '7px 12px', color: 'var(--text2)', fontSize: '13px', cursor: 'pointer' }}>
            <ArrowLeft size={14} /> Back
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Shield size={20} color="var(--accent)" />
            <h1 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text)' }}>Admin Panel</h1>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text3)', background: 'var(--bg2)', border: '1px solid var(--border)', padding: '2px 8px', borderRadius: '4px' }}>Super Admin</span>
        </div>

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px', borderRadius: '8px', background: 'var(--red-bg)', color: 'var(--red)', fontSize: '13px', marginBottom: '20px' }}>
            <AlertCircle size={14} /> {error}
          </div>
        )}

        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '60px', color: 'var(--text3)' }}>
            <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> Loading...
          </div>
        ) : (
          <>
            {/* Stats */}
            {stats && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '28px' }}>
                {[
                  { label: 'Total Users', value: stats.total_users, icon: Users, color: 'var(--accent)' },
                  { label: 'Pro Users', value: stats.pro_users, icon: Crown, color: '#3b82f6' },
                  { label: 'Agency Users', value: stats.agency_users, icon: Shield, color: '#8b5cf6' },
                  { label: 'New This Week', value: stats.new_this_week, icon: TrendingUp, color: 'var(--green)' },
                ].map((s, i) => (
                  <div key={i} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text3)' }}>{s.label}</span>
                      <s.icon size={15} color={s.color} />
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text)' }}>{s.value}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Users Table */}
            <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden' }}>
              <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h2 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>All Users ({users.length})</h2>
                <button onClick={fetchData} style={{ fontSize: '12px', color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer' }}>Refresh</button>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: 'var(--bg3)' }}>
                      {['ID', 'Name', 'Email', 'Plan', 'Joined', 'Actions'].map(h => (
                        <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u, i) => (
                      <tr key={u.id} style={{ borderTop: '1px solid var(--border)', background: i % 2 === 0 ? 'transparent' : 'var(--bg)' }}>
                        <td style={{ padding: '12px 16px', fontSize: '12px', color: 'var(--text3)' }}>#{u.id}</td>
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{ width: '26px', height: '26px', borderRadius: '50%', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 600, color: 'white', flexShrink: 0 }}>
                              {(u.name || u.email)[0].toUpperCase()}
                            </div>
                            <span style={{ fontSize: '13px', color: 'var(--text)' }}>{u.name || '-'}</span>
                          </div>
                        </td>
                        <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text2)' }}>{u.email}</td>
                        <td style={{ padding: '12px 16px' }}>
                          <select value={u.plan || 'free'} onChange={e => updatePlan(u.id, e.target.value)}
                            disabled={updatingId === u.id}
                            style={{ padding: '4px 8px', borderRadius: '6px', fontSize: '12px', fontWeight: 500, border: '1px solid var(--border)', background: planBg[u.plan || 'free'], color: planColors[u.plan || 'free'], cursor: 'pointer', outline: 'none' }}>
                            <option value="free">Free</option>
                            <option value="pro">Pro</option>
                            <option value="agency">Agency</option>
                          </select>
                        </td>
                        <td style={{ padding: '12px 16px', fontSize: '12px', color: 'var(--text3)' }}>
                          {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          {u.email !== 'jsvking@gmail.com' && (
                            <button onClick={() => deleteUser(u.id, u.email)} disabled={updatingId === u.id}
                              style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '5px 10px', background: 'var(--red-bg)', border: '1px solid rgba(162,45,45,0.2)', borderRadius: '6px', color: 'var(--red)', fontSize: '11px', cursor: 'pointer' }}>
                              {updatingId === u.id ? <Loader2 size={11} style={{ animation: 'spin 1s linear infinite' }} /> : <Trash2 size={11} />}
                              Delete
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}