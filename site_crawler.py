"""
Full Site Crawler and Auditor
Crawls all pages of a website and provides SEO analysis
"""

import httpx
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Optional
import re


async def fetch_page(client: httpx.AsyncClient, url: str) -> Optional[dict]:
    """Fetch and parse a single page."""
    try:
        resp = await client.get(url, timeout=10, follow_redirects=True)
        if resp.status_code != 200:
            return None
        if 'text/html' not in resp.headers.get('content-type', ''):
            return None
        
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract data
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else ''
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_desc_text = meta_desc.get('content', '') if meta_desc else ''
        
        h1_tags = [h.get_text(strip=True) for h in soup.find_all('h1')]
        h2_tags = [h.get_text(strip=True) for h in soup.find_all('h2')]
        
        images = soup.find_all('img')
        images_without_alt = sum(1 for img in images if not img.get('alt'))
        
        links = soup.find_all('a', href=True)
        
        # Word count
        body = soup.find('body')
        word_count = len(body.get_text().split()) if body else 0
        
        # Calculate page score
        score = 100
        issues = []
        
        if not title_text:
            score -= 20
            issues.append('Missing title tag')
        elif len(title_text) > 60:
            score -= 5
            issues.append('Title too long')
        elif len(title_text) < 30:
            score -= 5
            issues.append('Title too short')
            
        if not meta_desc_text:
            score -= 15
            issues.append('Missing meta description')
        elif len(meta_desc_text) > 160:
            score -= 5
            issues.append('Meta description too long')
            
        if not h1_tags:
            score -= 10
            issues.append('Missing H1 tag')
        elif len(h1_tags) > 1:
            score -= 5
            issues.append('Multiple H1 tags')
            
        if images_without_alt > 0:
            score -= min(10, images_without_alt * 2)
            issues.append(f'{images_without_alt} images missing alt text')
            
        if word_count < 300:
            score -= 10
            issues.append('Thin content (< 300 words)')
        
        score = max(0, score)
        
        return {
            'url': str(resp.url),
            'title': title_text,
            'meta_description': meta_desc_text,
            'h1': h1_tags[0] if h1_tags else '',
            'h2_count': len(h2_tags),
            'word_count': word_count,
            'images': len(images),
            'images_without_alt': images_without_alt,
            'score': score,
            'issues': issues,
            'main_issue': issues[0] if issues else None,
            'links': [urljoin(str(resp.url), a['href']) for a in links],
        }
    except Exception as e:
        return None


def extract_internal_links(page_data: dict, base_domain: str) -> list:
    """Extract internal links from a page."""
    links = []
    for link in page_data.get('links', []):
        try:
            parsed = urlparse(link)
            if parsed.netloc == base_domain or parsed.netloc == '':
                clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                clean = clean.rstrip('/')
                if clean and not any(ext in clean for ext in ['.pdf', '.jpg', '.png', '.gif', '.css', '.js', '.xml', '.ico']):
                    links.append(clean)
        except:
            pass
    return links


async def crawl_site(url: str, max_pages: int = 50) -> dict:
    """Crawl a website and return all page data."""
    parsed = urlparse(url)
    base_domain = parsed.netloc
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    visited = set()
    to_visit = [url]
    pages = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; SEMAIBot/1.0; +https://sakthivelraja.ai)',
        'Accept': 'text/html,application/xhtml+xml',
    }
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        while to_visit and len(pages) < max_pages:
            # Process up to 5 pages concurrently
            batch = []
            while to_visit and len(batch) < 5:
                next_url = to_visit.pop(0)
                if next_url not in visited:
                    visited.add(next_url)
                    batch.append(next_url)
            
            if not batch:
                break
                
            # Fetch batch concurrently
            tasks = [fetch_page(client, u) for u in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for page_data in results:
                if page_data and isinstance(page_data, dict):
                    pages.append(page_data)
                    
                    # Add new links to queue
                    internal_links = extract_internal_links(page_data, base_domain)
                    for link in internal_links:
                        if link not in visited and link not in to_visit:
                            to_visit.append(link)
    
    return pages


def analyze_site(pages: list, url: str) -> dict:
    """Analyze crawled pages and generate site audit report."""
    if not pages:
        return {"error": "No pages could be crawled"}
    
    # Calculate site-wide metrics
    avg_score = sum(p['score'] for p in pages) / len(pages)
    
    # Count issues
    all_issues = {}
    for page in pages:
        for issue in page.get('issues', []):
            all_issues[issue] = all_issues.get(issue, 0) + 1
    
    # Sort pages by score
    sorted_pages = sorted(pages, key=lambda p: p['score'], reverse=True)
    top_pages = sorted_pages[:10]
    bottom_pages = sorted_pages[-10:][::-1]
    
    # Count issue types
    missing_title = sum(1 for p in pages if not p['title'])
    missing_meta = sum(1 for p in pages if not p['meta_description'])
    missing_h1 = sum(1 for p in pages if not p['h1'])
    thin_content = sum(1 for p in pages if p['word_count'] < 300)
    images_no_alt = sum(1 for p in pages if p['images_without_alt'] > 0)
    
    critical_issues = []
    warnings = []
    
    if missing_title > 0:
        critical_issues.append({
            'title': 'Missing Title Tags',
            'description': f'{missing_title} pages have no title tag. This severely impacts SEO rankings.',
            'severity': 'critical',
            'affected_pages': missing_title,
        })
    
    if missing_meta > 0:
        warnings.append({
            'title': 'Missing Meta Descriptions',
            'description': f'{missing_meta} pages have no meta description. This reduces click-through rates from search results.',
            'severity': 'warning',
            'affected_pages': missing_meta,
        })
    
    if missing_h1 > 0:
        warnings.append({
            'title': 'Missing H1 Tags',
            'description': f'{missing_h1} pages have no H1 heading. H1 tags are crucial for SEO and content structure.',
            'severity': 'warning',
            'affected_pages': missing_h1,
        })
    
    if thin_content > 0:
        warnings.append({
            'title': 'Thin Content Pages',
            'description': f'{thin_content} pages have less than 300 words. Search engines prefer substantial content.',
            'severity': 'warning',
            'affected_pages': thin_content,
        })
    
    if images_no_alt > 0:
        warnings.append({
            'title': 'Images Missing Alt Text',
            'description': f'{images_no_alt} pages have images without alt text. This affects accessibility and image SEO.',
            'severity': 'warning',
            'affected_pages': images_no_alt,
        })
    
    all_found_issues = critical_issues + warnings
    
    # Score breakdown
    score_breakdown = {
        'title_optimisation': max(0, 100 - (missing_title / len(pages) * 100)),
        'meta_descriptions': max(0, 100 - (missing_meta / len(pages) * 100)),
        'heading_structure': max(0, 100 - (missing_h1 / len(pages) * 100)),
        'content_quality': max(0, 100 - (thin_content / len(pages) * 100)),
        'image_optimisation': max(0, 100 - (images_no_alt / len(pages) * 100)),
    }
    score_breakdown = {k: round(v) for k, v in score_breakdown.items()}
    
    # Strengths and weaknesses
    strengths = []
    weaknesses = []
    
    if score_breakdown['title_optimisation'] >= 80:
        strengths.append('Good title tag coverage across pages')
    else:
        weaknesses.append(f'Only {100-score_breakdown["title_optimisation"]}% of pages missing title tags')
    
    if score_breakdown['content_quality'] >= 80:
        strengths.append('Most pages have substantial content')
    else:
        weaknesses.append(f'{thin_content} pages have thin content that needs expansion')
    
    if avg_score >= 70:
        strengths.append(f'Good overall SEO health with {round(avg_score)}/100 average score')
    else:
        weaknesses.append(f'Overall site health needs improvement ({round(avg_score)}/100)')

    # Action plan
    action_plan = []
    
    if missing_title > 0:
        action_plan.append({
            'title': 'Fix Missing Title Tags',
            'description': f'Add unique, descriptive title tags to {missing_title} pages. Keep titles between 30-60 characters.',
            'priority': 'high',
            'estimated_impact': f'+{min(20, missing_title * 2)}% improvement in search visibility',
        })
    
    if missing_meta > 0:
        action_plan.append({
            'title': 'Write Meta Descriptions',
            'description': f'Create compelling meta descriptions for {missing_meta} pages. Keep between 120-160 characters with a call to action.',
            'priority': 'medium',
            'estimated_impact': f'+{min(15, missing_meta)}% improvement in click-through rate',
        })
    
    if thin_content > 0:
        action_plan.append({
            'title': 'Expand Thin Content Pages',
            'description': f'Add more valuable content to {thin_content} pages. Aim for at least 500 words per page.',
            'priority': 'medium',
            'estimated_impact': 'Better rankings for targeted keywords',
        })
    
    if images_no_alt > 0:
        action_plan.append({
            'title': 'Add Alt Text to Images',
            'description': f'Add descriptive alt text to images across {images_no_alt} pages for better accessibility and image SEO.',
            'priority': 'low',
            'estimated_impact': 'Improved accessibility score and image search visibility',
        })
    
    action_plan.append({
        'title': 'Focus on Lowest Scoring Pages',
        'description': f'Prioritise improving the {min(5, len(bottom_pages))} lowest scoring pages first for maximum impact.',
        'priority': 'high',
        'estimated_impact': f'Potential {10-20}% overall score improvement',
    })

    return {
        'site_score': round(avg_score),
        'pages_crawled': len(pages),
        'critical_issues': len(critical_issues),
        'warnings': len(warnings),
        'summary': f'Crawled {len(pages)} pages across {urlparse(url).netloc}. The site has an average SEO score of {round(avg_score)}/100. Found {len(critical_issues)} critical issues and {len(warnings)} warnings that need attention.',
        'strengths': strengths,
        'weaknesses': weaknesses,
        'score_breakdown': score_breakdown,
        'top_pages': [{'url': p['url'], 'title': p['title'], 'score': p['score']} for p in top_pages],
        'bottom_pages': [{'url': p['url'], 'title': p['title'], 'score': p['score'], 'main_issue': p['main_issue']} for p in bottom_pages],
        'issues': all_found_issues,
        'action_plan': action_plan,
    }
