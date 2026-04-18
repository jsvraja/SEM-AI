path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(path) as f:
    content = f.read()

# Fix single page prompt - pass exact calculated data
old1 = '''def build_seo_prompt_single_page(s: dict) -> str:
    """Deep SEO analysis for a single page."""
    return f"""You are a senior SEO specialist. Do a deep analysis of this SINGLE PAGE and return ONE JSON object only.
URL: {s['url']} | Title: {s['title']} | Meta: {s['meta_description']} | H1: {s['h1_tags']} | Words: {s.get('word_count', 0)} | Images: {s['images_count']} | Images without alt: {s['images_without_alt_count']} | Schema: {s['has_schema_markup']} | Content: {str(s.get('full_text',''))[:3000]}'''

new1 = '''def build_seo_prompt_single_page(s: dict) -> str:
    """Deep SEO analysis for a single page."""
    title = s.get('title', '')
    meta = s.get('meta_description', '')
    h1s = s.get('h1_tags', [])
    word_count = s.get('word_count', 0)
    images = s.get('images_count', 0)
    img_missing_alt = s.get('images_without_alt_count', 0)
    has_schema = s.get('has_schema_markup', False)
    internal_links = s.get('internal_links_count', 0)
    html_size = s.get('html_size_kb', 0)
    
    # Pre-calculate diagnostic data
    title_len = len(title)
    meta_len = len(meta)
    title_status = "✓ GOOD (30-60 chars)" if 30 <= title_len <= 60 else f"✗ {'TOO LONG' if title_len > 60 else 'TOO SHORT'} ({title_len} chars, ideal 30-60)"
    meta_status = "✓ GOOD (120-160 chars)" if 120 <= meta_len <= 160 else ("✗ MISSING" if not meta else f"✗ {'TOO LONG' if meta_len > 160 else 'TOO SHORT'} ({meta_len} chars, ideal 120-160)")
    h1_status = f"✓ GOOD (1 H1 tag)" if len(h1s) == 1 else (f"✗ MISSING" if not h1s else f"✗ MULTIPLE H1s ({len(h1s)} found, use only 1)")
    content_status = "✓ GOOD (800+ words)" if word_count >= 800 else f"✗ THIN CONTENT ({word_count} words, need 800+)"
    img_status = "✓ ALL IMAGES HAVE ALT TEXT" if img_missing_alt == 0 else f"✗ {img_missing_alt} of {images} images missing alt text"
    schema_status = "✓ SCHEMA PRESENT" if has_schema else "✗ NO SCHEMA MARKUP"
    links_status = "✓ GOOD" if internal_links >= 5 else f"✗ LOW ({internal_links} internal links, need 5+)"
    
    return f"""You are a senior SEO specialist. Analyse this SINGLE PAGE using the exact diagnostic data below.
URL: {s['url']}
Page Content: {str(s.get('full_text',''))[:3000]}

EXACT DIAGNOSTIC DATA (use these specific numbers in your analysis):
- Title: "{title}" → {title_status}
- Meta Description: "{meta[:100]}..." → {meta_status}  
- H1 Tags: {h1s} → {h1_status}
- Word Count: {word_count} → {content_status}
- Images: {images} total, {img_missing_alt} missing alt → {img_status}
- Schema Markup: {has_schema} → {schema_status}
- Internal Links: {internal_links} → {links_status}
- HTML Size: {html_size} KB'''

content = content.replace(old1, new1)

# Fix whole site prompt too
old2 = '''def build_seo_prompt_whole_site(s: dict) -> str:
    """SEO analysis for a whole website."""
    return f"""You are a senior SEO specialist. Analyse this WEBSITE and return ONE JSON object only.
URL: {s['url']} | Title: {s['title']} | Meta: {s['meta_description']} | H1: {s['h1_tags']} | Words: {s.get('word_count', 0)} | Images: {s['images_count']} | Images without alt: {s['images_without_alt_count']} | Schema: {s['has_schema_markup']} | Content: {str(s.get('full_text',''))[:3000]}'''

new2 = '''def build_seo_prompt_whole_site(s: dict) -> str:
    """SEO analysis for a whole website."""
    title = s.get('title', '')
    meta = s.get('meta_description', '')
    h1s = s.get('h1_tags', [])
    word_count = s.get('word_count', 0)
    images = s.get('images_count', 0)
    img_missing_alt = s.get('images_without_alt_count', 0)
    has_schema = s.get('has_schema_markup', False)
    internal_links = s.get('internal_links_count', 0)
    html_size = s.get('html_size_kb', 0)

    title_len = len(title)
    meta_len = len(meta)
    title_status = "✓ GOOD" if 30 <= title_len <= 60 else f"✗ {'TOO LONG' if title_len > 60 else 'TOO SHORT'} ({title_len} chars)"
    meta_status = "✓ GOOD" if 120 <= meta_len <= 160 else ("✗ MISSING" if not meta else f"✗ {'TOO LONG' if meta_len > 160 else 'TOO SHORT'} ({meta_len} chars)")
    h1_status = "✓ GOOD" if len(h1s) == 1 else ("✗ MISSING" if not h1s else f"✗ {len(h1s)} H1s found")
    content_status = "✓ GOOD" if word_count >= 800 else f"✗ THIN ({word_count} words)"
    img_status = "✓ ALL ALT TEXT" if img_missing_alt == 0 else f"✗ {img_missing_alt}/{images} missing alt"
    schema_status = "✓ PRESENT" if has_schema else "✗ MISSING"

    return f"""You are a senior SEO specialist. Analyse this WEBSITE homepage using exact diagnostic data.
URL: {s['url']}
Page Content: {str(s.get('full_text',''))[:3000]}

EXACT DIAGNOSTIC DATA:
- Title: "{title}" → {title_status}
- Meta: "{meta[:80]}..." → {meta_status}
- H1: {h1s} → {h1_status}
- Words: {word_count} → {content_status}
- Images: {images} ({img_missing_alt} missing alt) → {img_status}
- Schema: {has_schema} → {schema_status}
- Internal Links: {internal_links}
- HTML Size: {html_size} KB'''

content = content.replace(old2, new2)

with open(path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print("ERROR:", e)
