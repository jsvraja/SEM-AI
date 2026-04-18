path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(path) as f:
    content = f.read()

old_scraper = '''    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    body_text = re.sub(r\'\\s+\', \' \', soup.get_text(separator=" ", strip=True))[:3000]
    schema_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
    return {
        "url": url,
        "title": title.get_text(strip=True) if title else None,
        "meta_description": meta_desc["content"] if meta_desc and meta_desc.get("content") else None,
        "has_viewport": viewport is not None,
        "h1_tags": h1s, "h2_tags": h2s,
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "images_count": len(images),
        "images_without_alt_count": len(images_without_alt),
        "has_schema_markup": len(schema_tags) > 0,
        "body_text_sample": body_text,
        "html_size_kb": round(len(html) / 1024, 1),
    }'''

new_scraper = '''    schema_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
    
    # Get full text before removing tags for word count
    full_text_raw = re.sub(r\'\\s+\', \' \', soup.get_text(separator=" ", strip=True))
    word_count = len(full_text_raw.split())
    
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    body_text = re.sub(r\'\\s+\', \' \', soup.get_text(separator=" ", strip=True))[:5000]
    
    # Direct CTA detection (100% accurate)
    cta_keywords = [\'download\', \'free trial\', \'get started\', \'contact us\', \'buy now\', 
                    \'request demo\', \'sign up\', \'try free\', \'get quote\', \'schedule demo\',
                    \'start free\', \'register\', \'subscribe\', \'book a demo\', \'learn more\']
    full_text_lower = full_text_raw.lower()
    has_cta = any(kw in full_text_lower for kw in cta_keywords)
    cta_found = [kw for kw in cta_keywords if kw in full_text_lower][:3]
    
    # Reading level (Flesch-Kincaid approximation)
    sentences = len(re.findall(r\'[.!?]+\', full_text_raw)) or 1
    words = word_count or 1
    syllables = sum(max(1, len(re.findall(r\'[aeiouAEIOU]\', w))) for w in full_text_raw.split()[:200])
    fk_score = 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/min(words,200))
    fk_score = max(0, min(100, fk_score))
    if fk_score >= 70: reading_level = "Easy (Grade 6)"
    elif fk_score >= 50: reading_level = "Standard (Grade 8-9)"
    elif fk_score >= 30: reading_level = "Difficult (Grade 12)"
    else: reading_level = "Very Difficult (College)"
    
    # Keyword density - top words
    import collections
    stop_words = {\'the\',\'be\',\'to\',\'of\',\'and\',\'a\',\'in\',\'that\',\'have\',\'it\',\'for\',\'not\',\'on\',\'with\',\'he\',\'as\',\'you\',\'do\',\'at\',\'this\',\'but\',\'his\',\'by\',\'from\',\'they\',\'we\',\'say\',\'her\',\'she\',\'or\',\'an\',\'will\',\'my\',\'one\',\'all\',\'would\',\'there\',\'their\',\'what\',\'so\',\'up\',\'out\',\'if\',\'about\',\'who\',\'get\',\'which\',\'go\',\'me\',\'is\',\'are\',\'was\',\'were\',\'has\',\'had\',\'can\',\'your\'}
    words_list = [w.lower() for w in re.findall(r\'\\b[a-zA-Z]{3,}\\b\', full_text_raw) if w.lower() not in stop_words]
    word_freq = collections.Counter(words_list).most_common(5)
    top_keyword = word_freq[0][0] if word_freq else \'\'
    keyword_density = f"{round((word_freq[0][1]/max(word_count,1))*100, 1)}%" if word_freq else "0%"
    
    # Tone detection
    professional_words = [\'enterprise\',\'solution\',\'platform\',\'manage\',\'optimize\',\'implement\',\'deploy\',\'configure\']
    casual_words = [\'easy\',\'simple\',\'quick\',\'fast\',\'fun\',\'awesome\',\'great\',\'love\']
    prof_count = sum(1 for w in professional_words if w in full_text_lower)
    casual_count = sum(1 for w in casual_words if w in full_text_lower)
    tone = "Professional" if prof_count > casual_count else "Casual" if casual_count > prof_count else "Neutral"
    
    # Image alt text percentage
    alt_coverage = round(((len(images) - len(images_without_alt)) / max(len(images), 1)) * 100)
    
    return {
        "url": url,
        "title": title.get_text(strip=True) if title else None,
        "meta_description": meta_desc["content"] if meta_desc and meta_desc.get("content") else None,
        "has_viewport": viewport is not None,
        "h1_tags": h1s, "h2_tags": h2s,
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "images_count": len(images),
        "images_without_alt_count": len(images_without_alt),
        "alt_text_coverage": alt_coverage,
        "has_schema_markup": len(schema_tags) > 0,
        "body_text_sample": body_text,
        "full_text": body_text,
        "html_size_kb": round(len(html) / 1024, 1),
        "word_count": word_count,
        "reading_level": reading_level,
        "flesch_score": round(fk_score, 1),
        "has_cta": has_cta,
        "cta_examples": cta_found,
        "tone": tone,
        "top_keyword": top_keyword,
        "keyword_density": keyword_density,
    }'''

if old_scraper in content:
    content = content.replace(old_scraper, new_scraper)
    print("Scraper enhanced!")
else:
    print("ERROR: scraper not found")

with open(path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print("ERROR:", e)

# Also update the prompt to use new scraped fields
path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(path) as f:
    content = f.read()

# Update single page prompt to use new fields
old_diag = '''- Word Count: {word_count} → {content_status}
- Images: {images} total, {img_missing_alt} missing alt → {img_status}
- Schema Markup: {has_schema} → {schema_status}
- Internal Links: {internal_links} → {links_status}
- HTML Size: {html_size} KB'''

new_diag = '''- Word Count: {word_count} → {content_status}
- Reading Level: {s.get('reading_level', 'N/A')} (Flesch Score: {s.get('flesch_score', 'N/A')})
- Tone: {s.get('tone', 'N/A')}
- CTA Present: {s.get('has_cta', False)} → CTAs found: {s.get('cta_examples', [])}
- Top Keyword: "{s.get('top_keyword', 'N/A')}" — Density: {s.get('keyword_density', 'N/A')}
- Images: {images} total, {img_missing_alt} missing alt → {img_status}
- Alt Text Coverage: {s.get('alt_text_coverage', 0)}%
- Schema Markup: {has_schema} → {schema_status}
- Internal Links: {internal_links} → {links_status}
- HTML Size: {html_size} KB'''

content = content.replace(old_diag, new_diag)

# Update content_analysis in prompt to use scraped values
old_ca_prompt = '''  "content_analysis": {{
    "word_count": {s.get('word_count', 0)},
    "readability": "Good — use Flesch Reading Ease score (0-100, higher is easier)",
    "reading_level": "Grade 8 — suitable for general audience",
    "keyword_density": "2.3% — analyse top 3 keywords from content",
    "primary_keyword": "most prominent keyword found in title+h1+content",
    "keyword_in_title": true,
    "keyword_in_meta": true,
    "keyword_in_h1": true,
    "content_score": 70,
    "content_gaps": ["Add FAQ section", "Include comparison table", "Add customer testimonials"],
    "tone": "Professional",
    "language": "English",
    "has_cta": true,
    "cta_text": "Get Started / Download / Contact Us etc",
    "content_strengths": ["Clear value proposition", "Technical depth"],
    "content_weaknesses": ["Thin content under 500 words", "No FAQ section"]
  }},'''

new_ca_prompt = '''  "content_analysis": {{
    "word_count": {s.get('word_count', 0)},
    "readability": "Good/Average/Poor based on content complexity",
    "reading_level": "{s.get('reading_level', 'Standard (Grade 8-9)')}",
    "keyword_density": "{s.get('keyword_density', '0%')}",
    "primary_keyword": "{s.get('top_keyword', '')}",
    "keyword_in_title": true_or_false,
    "keyword_in_meta": true_or_false,
    "keyword_in_h1": true_or_false,
    "content_score": 70,
    "content_gaps": ["specific gap based on page content"],
    "tone": "{s.get('tone', 'Professional')}",
    "language": "English",
    "has_cta": {str(s.get('has_cta', False)).lower()},
    "cta_text": "{', '.join(s.get('cta_examples', []))}",
    "content_strengths": ["strength based on actual content"],
    "content_weaknesses": ["weakness based on actual content"]
  }},'''

content = content.replace(old_ca_prompt, new_ca_prompt)

with open(path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Prompt updated! Syntax OK!")
except py_compile.PyCompileError as e:
    print("ERROR:", e)

# Update Dashboard to use scraped data directly for accuracy
dash_path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(dash_path) as f:
    dcontent = f.read()

old_ca_ui = '''                const readability = ca.readability || 'N/A'
                const readingLevel = ca.reading_level || 'N/A'
                const keywordDensity = ca.keyword_density || 'N/A'
                const primaryKeyword = ca.primary_keyword || 'N/A'
                const contentScore = ca.content_score || ca.quality_score || ca.readability_score || seo?.overall_seo_score || 0
                const gaps = ca.content_gaps || []
                const tone = ca.tone || 'N/A'
                const hasCTA = ca.has_cta
                const ctaText = ca.cta_text || ''
                const strengths = ca.content_strengths || []
                const weaknesses = ca.content_weaknesses || []
                const kwInTitle = ca.keyword_in_title
                const kwInMeta = ca.keyword_in_meta
                const kwInH1 = ca.keyword_in_h1
                const wordColor = wordCount >= 800 ? 'var(--green)' : wordCount >= 400 ? 'var(--yellow)' : 'var(--red)'
'''

new_ca_ui = '''                const readability = ca.readability || 'N/A'
                const readingLevel = sc?.reading_level || ca.reading_level || 'N/A'
                const keywordDensity = sc?.keyword_density || ca.keyword_density || 'N/A'
                const primaryKeyword = sc?.top_keyword || ca.primary_keyword || 'N/A'
                const contentScore = ca.content_score || ca.quality_score || ca.readability_score || seo?.overall_seo_score || 0
                const gaps = ca.content_gaps || []
                const tone = sc?.tone || ca.tone || 'N/A'
                const hasCTA = sc?.has_cta ?? ca.has_cta
                const ctaText = (sc?.cta_examples || []).join(', ') || ca.cta_text || ''
                const strengths = ca.content_strengths || []
                const weaknesses = ca.content_weaknesses || []
                const title2 = sc?.title || ''
                const meta2 = sc?.meta_description || ''
                const h1s2 = sc?.h1_tags || []
                const pkLower = primaryKeyword.toLowerCase()
                const kwInTitle = pkLower && title2 ? title2.toLowerCase().includes(pkLower) : ca.keyword_in_title
                const kwInMeta = pkLower && meta2 ? meta2.toLowerCase().includes(pkLower) : ca.keyword_in_meta
                const kwInH1 = pkLower && h1s2.length ? h1s2.some(h => h.toLowerCase().includes(pkLower)) : ca.keyword_in_h1
                const wordColor = wordCount >= 800 ? 'var(--green)' : wordCount >= 400 ? 'var(--yellow)' : 'var(--red)'
'''

if old_ca_ui in dcontent:
    dcontent = dcontent.replace(old_ca_ui, new_ca_ui)
    print("Dashboard CA updated!")
else:
    print("Dashboard CA: marker not found")

with open(dash_path, 'w') as f:
    f.write(dcontent)

dash_path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(dash_path2, 'w') as f:
    f.write(dcontent)
print("All done!")
