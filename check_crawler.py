path = '/Users/sakthivel-1528/Personal/sem-app/backend/site_crawler.py'
with open(path) as f:
    content = f.read()

# Show the full run_audit_job function
idx = content.find('async def run_audit_job')
end = content.find('\nasync def ', idx + 10)
print(content[idx:end])
