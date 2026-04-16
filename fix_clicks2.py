path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

print("File size:", len(content))
print("Has export default:", "export default function Dashboard" in content)

# Find the exact Est Monthly Clicks closing
idx = content.find("Est. Monthly Clicks")
snippet = content[idx:idx+800]
print("Snippet:")
print(repr(snippet))
