import re, os

with open('main_with_ads.py') as f:
    c = f.read()

# Fix FastAPI imports
c = re.sub(r'from fastapi import [^\n]+',
    'from fastapi import FastAPI, HTTPException, Query, Request, BackgroundTasks', c, count=1)

# Fix datetime
if 'from datetime import datetime' not in c:
    c = c.replace('import os\n', 'import os\nfrom datetime import datetime\n')
    print("Fixed datetime import")

with open('main_with_ads.py', 'w') as f:
    f.write(c)
print("main_with_ads.py: OK")

# Fix Dashboard Share2
dash = '../frontend/src/components/Dashboard.jsx'
if os.path.exists(dash):
    with open(dash) as f: d = f.read()
    if 'Share2' not in d.split('lucide-react')[0]:
        d = d.replace("  Zap, Search, BarChart3\n} from 'lucide-react'",
                      "  Zap, Search, BarChart3, Share2\n} from 'lucide-react'")
        with open(dash, 'w') as f: f.write(d)
        print("Dashboard.jsx: Fixed Share2")
    print("Dashboard.jsx: OK")
