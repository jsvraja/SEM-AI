path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(path) as f:
    content = f.read()

# Fix single page ai_summary prompt
old1 = '"ai_summary": "3 sentence assessment of this specific page SEO health and main opportunities",'
new1 = '"ai_summary": "5-6 sentence expert analysis covering: (1) overall SEO health with specific score explanation, (2) key strengths found in actual page data, (3) critical issues with specific details like word count/meta length/missing elements, (4) competitive positioning for target keywords, (5) top 2 immediate actions with expected score impact",'

content = content.replace(old1, new1)

# Fix whole site ai_summary prompt  
old2 = '"ai_summary": "3 sentence overall assessment of the website SEO health and main opportunities",'
new2 = '"ai_summary": "5-6 sentence expert analysis covering: (1) overall website SEO health score explanation, (2) strongest pages and what makes them rank well, (3) critical technical issues affecting the whole site with specifics, (4) content gaps and opportunities, (5) top 2 priority fixes with expected impact on rankings",'

content = content.replace(old2, new2)

# Also increase full_text passed to prompt for better analysis
old3 = "Content: {str(s.get('full_text',''))[:2000]}"
new3 = "Content: {str(s.get('full_text',''))[:3000]}"
content = content.replace(old3, new3)

with open(path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print("ERROR:", e)
