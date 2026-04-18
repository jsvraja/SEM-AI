import os

# 1. Copy seo_trends.py to backend
src = '/mnt/user-data/outputs/seo_trends.py'
dst = '/Users/sakthivel-1528/Personal/sem-app/backend/seo_trends.py'
with open(src) as f:
    content = f.read()
with open(dst, 'w') as f:
    f.write(content)
print("seo_trends.py created!")

# 2. Add trend recording to full-report endpoint and add trend API
main_path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(main_path) as f:
    main = f.read()

# Add import
if 'from seo_trends import' not in main:
    main = main.replace(
        'from sem_agent import',
        'from seo_trends import record_score, get_trend\nfrom sem_agent import'
    )
    print("Added seo_trends import!")

# Add trend recording after seo_report is finalized
old_return = """    # Force correct url_type regardless of what AI returned
    seo_report['url_type'] = _detected_url_type"""

new_return = """    # Force correct url_type regardless of what AI returned
    seo_report['url_type'] = _detected_url_type
    
    # Record SEO trend
    try:
        content_score = seo_report.get('content_analysis', {}).get('quality_score', 0) or 0
        record_score(url, seo_report.get('overall_seo_score', 0), content_score)
    except:
        pass"""

main = main.replace(old_return, new_return)

# Add trend API endpoint
trend_endpoint = '''
@app.get("/api/seo-trend")
async def get_seo_trend(url: str):
    """Get SEO score trend for a URL."""
    try:
        from seo_trends import get_trend
        data = get_trend(url)
        return {"url": url, "trend": data}
    except Exception as e:
        return {"url": url, "trend": [], "error": str(e)}

'''

# Insert before agent routes
if '/api/seo-trend' not in main:
    main = main.replace(
        '@app.get("/api/agent/status")',
        trend_endpoint + '@app.get("/api/agent/status")'
    )
    print("Added trend endpoint!")

with open(main_path, 'w') as f:
    f.write(main)

import py_compile
try:
    py_compile.compile(main_path, doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print("ERROR:", e)
