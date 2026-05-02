import { useState, useEffect } from 'react'
import { Users, Plus, Mail, Shield, Eye, BarChart2, Loader2, X, Check, Building2 } from 'lucide-react'

const API = 'https://sem-ai-production.up.railway.app'

export default function Workspaces({ user }) {
  const token = localStorage.getItem('sem_token')
  const [workspaces, setWorkspaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [showInvite, setShowInvite] = useState(null)
  const [newName, setNewName] = useState('')
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('viewer')
  const [creating, setCreating] = useState(false)
  const [inviting, setInviting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [members, setMembers] = useState({})

  useEffect(() => { fetchWorkspaces() }, [])

  async function fetchWorkspaces() {
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/workspaces`, { headers: { Authorization: `Bearer ${token}` } })
      const data = await res.json()
      setWorkspaces(data.workspaces || [])
      // Fetch members for each workspace
      for (const ws of data.workspaces || []) {
        fetchMembers(ws.id)
      }
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  async function fetchMembers(wsId) {
    try {
      const res = await fetch(`${API}/api/workspaces/${wsId}/members`, { headers: { Authorization: `Bearer ${token}` } })
      const data = await res.json()
      setMembers(prev => ({ ...prev, [wsId]: data.members || [] }))
    } catch (e) {}
  }

  async function createWorkspace() {
    if (!newName.trim()) return
    setCreating(true)
    setError('')
    try {
      const res = await fetch(`${API}/api/workspaces/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ name: newName }),
      })
      const data = await res.json()
      if (data.error) { setError(data.error); return }
      setWorkspaces(prev => [data.workspace, ...prev])
      setNewName('')
      setShowCreate(false)
      setSuccess('Workspace created successfully!')
      setTimeout(() => setSuccess(''), 3000)
    } catch (e) { setError(e.message) }
    finally { setCreating(false) }
  }

  async function inviteMember() {
    if (!inviteEmail.trim()) return
    setInviting(true)
    setError('')
    try {
      const res = await fetch(`${API}/api/workspaces/invite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ workspace_id: showInvite, email: inviteEmail, role: inviteRole }),
      })
      const data = await res.json()
      if (data.error) { setError(data.error); return }
      setSuccess(`Invite sent to ${inviteEmail}!`)
      setInviteEmail('')
      setShowInvite(null)
      setTimeout(() => setSuccess(''), 3000)
    } catch (e) { setError(e.message) }
    finally { setInviting(false) }
  }

  const roleColors = { admin: '#6366f1', analyst: '#3b82f6', viewer: '#6b7280' }
  const roleIcons = { admin: Shield, analyst: BarChart2, viewer: Eye }

  const canCreateWorkspace = user?.plan === 'pro' || user?.plan === 'agency'

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Building2 size={20} color="var(--accent)" /> Team Workspaces
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text3)', marginTop: '4px' }}>Collaborate with your team on campaigns and analyses</p>
        </div>
        {canCreateWorkspace && (
          <button onClick={() => setShowCreate(true)} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '9px 16px', background: 'var(--accent)', border: 'none', borderRadius: '8px', color: 'white', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}>
            <Plus size={14} /> New Workspace
          </button>
        )}
      </div>

      {!canCreateWorkspace && (
        <div style={{ padding: '16px', borderRadius: '10px', background: 'linear-gradient(135deg, #6366f120, #8b5cf620)', border: '1px solid #6366f130', marginBottom: '20px', fontSize: '13px', color: 'var(--text2)' }}>
          🔒 Upgrade to <strong>Pro</strong> or <strong>Agency</strong> to create and manage team workspaces.
        </div>
      )}

      {success && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px', borderRadius: '8px', background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)', color: '#22c55e', fontSize: '13px', marginBottom: '16px' }}>
          <Check size={14} /> {success}
        </div>
      )}

      {error && (
        <div style={{ padding: '12px', borderRadius: '8px', background: 'var(--red-bg)', color: 'var(--red)', fontSize: '13px', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '60px', color: 'var(--text3)' }}>
          <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> Loading workspaces...
        </div>
      ) : workspaces.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text3)' }}>
          <Building2 size={40} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
          <p style={{ fontSize: '14px' }}>No workspaces yet</p>
          {canCreateWorkspace && <p style={{ fontSize: '12px', marginTop: '4px' }}>Create your first workspace to collaborate with your team</p>}
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '16px' }}>
          {workspaces.map(ws => {
            const wsMembers = members[ws.id] || []
            return (
              <div key={ws.id} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '36px', height: '36px', borderRadius: '9px', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '16px', fontWeight: 700, color: 'white' }}>
                      {ws.name[0].toUpperCase()}
                    </div>
                    <div>
                      <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text)' }}>{ws.name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text3)' }}>Created {new Date(ws.created_at).toLocaleDateString()}</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '4px', background: `${roleColors[ws.role]}20`, color: roleColors[ws.role], fontWeight: 500, textTransform: 'capitalize' }}>{ws.role}</span>
                    {ws.role === 'admin' && (
                      <button onClick={() => setShowInvite(ws.id)} style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '6px 12px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '6px', color: 'var(--text2)', fontSize: '12px', cursor: 'pointer' }}>
                        <Mail size={12} /> Invite
                      </button>
                    )}
                  </div>
                </div>

                {/* Members */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text3)' }}><Users size={11} style={{ display: 'inline', marginRight: '4px' }} />{wsMembers.length} members:</span>
                  {wsMembers.map(m => {
                    const RoleIcon = roleIcons[m.role] || Eye
                    return (
                      <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '4px 8px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '6px', fontSize: '12px' }}>
                        <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: roleColors[m.role] || '#6b7280', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '9px', color: 'white', fontWeight: 700 }}>
                          {(m.name || m.email)[0].toUpperCase()}
                        </div>
                        <span style={{ color: 'var(--text2)' }}>{m.name || m.email}</span>
                        <RoleIcon size={10} color={roleColors[m.role]} />
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Create Workspace Modal */}
      {showCreate && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div style={{ background: 'var(--bg)', borderRadius: '14px', padding: '28px', width: '100%', maxWidth: '420px', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text)' }}>Create Workspace</h3>
              <button onClick={() => setShowCreate(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)' }}><X size={18} /></button>
            </div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px' }}>Workspace Name</label>
            <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="e.g. Marketing Team"
              style={{ width: '100%', padding: '10px 12px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text)', fontSize: '13px', outline: 'none', marginBottom: '16px' }}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'} />
            <button onClick={createWorkspace} disabled={creating || !newName.trim()} style={{ width: '100%', padding: '10px', background: creating || !newName.trim() ? 'var(--bg3)' : 'var(--accent)', border: 'none', borderRadius: '8px', color: creating || !newName.trim() ? 'var(--text3)' : 'white', fontSize: '14px', fontWeight: 500, cursor: creating || !newName.trim() ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
              {creating ? <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Creating...</> : 'Create Workspace'}
            </button>
          </div>
        </div>
      )}

      {/* Invite Member Modal */}
      {showInvite && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div style={{ background: 'var(--bg)', borderRadius: '14px', padding: '28px', width: '100%', maxWidth: '420px', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text)' }}>Invite Team Member</h3>
              <button onClick={() => setShowInvite(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)' }}><X size={18} /></button>
            </div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px' }}>Email Address</label>
            <input value={inviteEmail} onChange={e => setInviteEmail(e.target.value)} placeholder="teammate@company.com" type="email"
              style={{ width: '100%', padding: '10px 12px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text)', fontSize: '13px', outline: 'none', marginBottom: '12px' }}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'} />
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px' }}>Role</label>
            <select value={inviteRole} onChange={e => setInviteRole(e.target.value)}
              style={{ width: '100%', padding: '10px 12px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text)', fontSize: '13px', outline: 'none', marginBottom: '16px', cursor: 'pointer' }}>
              <option value="admin">Admin — Full access</option>
              <option value="analyst">Analyst — View + analyze</option>
              <option value="viewer">Viewer — View only</option>
            </select>
            <button onClick={inviteMember} disabled={inviting || !inviteEmail.trim()} style={{ width: '100%', padding: '10px', background: inviting || !inviteEmail.trim() ? 'var(--bg3)' : 'var(--accent)', border: 'none', borderRadius: '8px', color: inviting || !inviteEmail.trim() ? 'var(--text3)' : 'white', fontSize: '14px', fontWeight: 500, cursor: inviting || !inviteEmail.trim() ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
              {inviting ? <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Sending...</> : <><Mail size={14} /> Send Invite</>}
            </button>
          </div>
        </div>
      )}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}