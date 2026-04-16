path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/SiteAudit.jsx'
with open(path) as f:
    content = f.read()

# Find the component function and rewrite the hooks section cleanly
old = """export default function SiteAudit({ autoUrl = null, savedResults = null, onResults = null }) {
  const [url, setUrl] = useState(autoUrl || '')
  const [maxPages, setMaxPages] = useState(100)
  const [autoStarted, setAutoStarted] = useState(false)

  // Restore results when switching back to this tab
  useEffect(() => {
    if (savedResults && !results) {
      setResults(savedResults)
    }
  }, [savedResults])


  


  useEffect(() => {
    if (autoUrl && !autoStarted) {
      setAutoStarted(true)
      // Small delay to let component render
      setTimeout(() => startAudit(autoUrl), 500)
    }
  }, [autoUrl])
  const [auditing, setAuditing] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [progress, setProgress] = useState(null)
  const [results, setResults] = useState(savedResults || null)
  const savedResultsRef = React.useRef(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const pollRef = useRef(null)"""

new = """export default function SiteAudit({ autoUrl = null, savedResults = null, onResults = null }) {
  const [url, setUrl] = useState(autoUrl || '')
  const [maxPages, setMaxPages] = useState(100)
  const [autoStarted, setAutoStarted] = useState(false)
  const [auditing, setAuditing] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [progress, setProgress] = useState(null)
  const [results, setResults] = useState(savedResults || null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const pollRef = useRef(null)

  // Restore results when switching back to this tab
  useEffect(() => {
    if (savedResults && !results) {
      setResults(savedResults)
    }
  }, [savedResults])

  useEffect(() => {
    if (autoUrl && !autoStarted) {
      setAutoStarted(true)
      setTimeout(() => startAudit(autoUrl), 500)
    }
  }, [autoUrl])"""

if old in content:
    content = content.replace(old, new)
    print("Fixed hooks order!")
else:
    print("ERROR: Could not find hooks section")
    # Show what's there
    idx = content.find('export default function SiteAudit')
    print(content[idx:idx+500])

with open(path, 'w') as f:
    f.write(content)

# Also fix local frontend
path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/SiteAudit.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Both files fixed!")
