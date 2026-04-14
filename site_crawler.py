"""
Full Site Crawler - Background processing with progress tracking
Supports up to 20,000 pages
"""

import httpx
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Optional
import time
import uuid

# Global job store - tracks running audits
_audit_jobs = {}


def get_job(job_id: str) -> dict:
    return _audit_jobs.get(job_id)


def create_job(job_id: str, url: str, max_pages: int) -> dict:
    job = {
        'id': job_id,
        'url': url,
        'max_pages': max_pages,
        'status': 'starting',
        'progress': 0,
        'pages_found': 0,
        'pages_crawled': 0,
        'current_url': '',
        'started_at': time.time(),
        'result': None,
        'error': None,
    }
    _audit_jobs[job_id] = job
    return job


async def get_urls_from_sitemap(client: httpx.AsyncClient, sitemap_url: str, base_domain: str, max_urls: int = 20000) -> list:
    """Recursively extract URLs from sitemap or sitemap index."""
    urls = []
    try:
        resp = await client.get(sitemap_url, timeout=20)
        if resp.status_code != 200:
            return urls

        soup = BeautifulSoup(resp.text, 'xml')

        # Sitemap index — recurse into sub-sitemaps
        sitemaps = soup.find_all('sitemap')
        if sitemaps:
            tasks = []
            for sitemap in sitemaps[:30]:
                loc = sitemap.find('loc')
                if loc and len(urls) < max_urls:
                    tasks.append(get_urls_from_sitemap(client, loc.text.strip(), base_domain, max_urls))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, list):
                    urls.extend(r)
                    if len(urls) >= max_urls:
                        break
        else:
            # Regular sitemap
            for url_tag in soup.find_all('url'):
                loc = url_tag.find('loc')
                if loc:
                    url = loc.text.strip()
                    parsed = urlparse(url)
                    if base_domain in parsed.netloc:
                        if url not in urls:
                            urls.append(url)
                if len(urls) >= max_urls:
                    break
    except Exception as e:
        print(f"Sitemap error for {sitemap_url}: {e}")

    return urls


async def fetch_page(client: httpx.AsyncClient, url: str) -> Optional[dict]:
    """Fetch and analyse a single page."""
    try:
        resp = await client.get(url, timeout=12, follow_redirects=True)
        if resp.status_code != 200:
            return {'url': url, 'score': 0, 'title': '', 'issues': [f'HTTP {resp.status_code}'], 'main_issue': f'HTTP {resp.status_code}', 'word_count': 0, 'images_without_alt': 0}

        if 'text/html' not in resp.headers.get('content-type', ''):
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')

        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else ''

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_desc_text = meta_desc.get('content', '') if meta_desc else ''

        h1_tags = [h.get_text(strip=True) for h in soup.find_all('h1')]
        images = soup.find_all('img')
        images_without_alt = sum(1 for img in images if not img.get('alt'))

        body = soup.find('body')
        word_count = len(body.get_text().split()) if body else 0

        score = 100
        issues = []

        if not title_text:
            score -= 20; issues.append('Missing title tag')
        elif len(title_text) > 60:
            score -= 5; issues.append('Title too long')
        elif len(title_text) < 20:
            score -= 5; issues.append('Title too short')

        if not meta_desc_text:
            score -= 15; issues.append('Missing meta description')
        elif len(meta_desc_text) > 160:
            score -= 5; issues.append('Meta description too long')

        if not h1_tags:
            score -= 10; issues.append('Missing H1 tag')
        elif len(h1_tags) > 1:
            score -= 3; issues.append('Multiple H1 tags')

        if images_without_alt > 0:
            score -= min(10, images_without_alt * 2)
            issues.append(f'{images_without_alt} images missing alt text')

        if word_count < 200:
            score -= 15; issues.append('Very thin content')
        elif word_count < 400:
            score -= 7; issues.append('Thin content')

        return {
            'url': str(resp.url),
            'title': title_text,
            'meta_description': meta_desc_text,
            'h1': h1_tags[0] if h1_tags else '',
            'word_count': word_count,
            'images': len(images),
            'images_without_alt': images_without_alt,
            'score': max(0, score),
            'issues': issues,
            'main_issue': issues[0] if issues else None,
        }
    except Exception:
        return None


async def run_audit_job(job_id: str, url: str, max_pages: int):
    """Background job that crawls site and updates progress."""
    job = _audit_jobs[job_id]
    
    try:
        parsed = urlparse(url)
        base_domain = parsed.netloc
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
        }

        job['status'] = 'discovering'
        job['current_url'] = 'Discovering pages from sitemap...'

        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=20) as client:
            
            # Find sitemap
            urls_to_fetch = []
            sitemap_candidates = []
            
            path = parsed.path.rstrip('/')
            while path:
                sitemap_candidates.append(f"{base_url}{path}/sitemap.xml")
                path = '/'.join(path.split('/')[:-1])
            sitemap_candidates.extend([
                f"{base_url}/sitemap.xml",
                f"{base_url}/sitemap_index.xml",
            ])

            for sitemap_url in sitemap_candidates:
                job['current_url'] = f'Checking: {sitemap_url}'
                found = await get_urls_from_sitemap(client, sitemap_url, base_domain, max_pages)
                if found:
                    urls_to_fetch = found
                    print(f"Found {len(found)} URLs from {sitemap_url}")
                    break

            # Fallback crawl if no sitemap
            if not urls_to_fetch:
                job['current_url'] = 'No sitemap found, crawling...'
                visited = set()
                queue = [url]
                while queue and len(urls_to_fetch) < min(max_pages, 500):
                    current = queue.pop(0)
                    if current in visited:
                        continue
                    visited.add(current)
                    urls_to_fetch.append(current)
                    try:
                        resp = await client.get(current, timeout=10)
                        if 'text/html' in resp.headers.get('content-type', ''):
                            soup = BeautifulSoup(resp.text, 'html.parser')
                            for a in soup.find_all('a', href=True):
                                link = urljoin(current, a['href']).split('?')[0].split('#')[0]
                                if urlparse(link).netloc == base_domain and link not in visited:
                                    queue.append(link)
                    except:
                        pass

            # Filter to relevant URLs
            base_path = parsed.path.rstrip('/')
            if base_path and len(urls_to_fetch) > max_pages:
                relevant = [u for u in urls_to_fetch if base_path in u]
                other = [u for u in urls_to_fetch if base_path not in u]
                if len(relevant) >= max_pages:
                    urls_to_fetch = relevant[:max_pages]
                else:
                    urls_to_fetch = relevant + other[:max_pages - len(relevant)]
            else:
                urls_to_fetch = urls_to_fetch[:max_pages]

            job['pages_found'] = len(urls_to_fetch)
            job['status'] = 'crawling'

            # Crawl pages in batches of 20
            pages = []
            batch_size = 5
            total = len(urls_to_fetch)

            for i in range(0, total, batch_size):
                batch = urls_to_fetch[i:i + batch_size]
                job['current_url'] = batch[0] if batch else ''
                job['pages_crawled'] = i
                job['progress'] = round((i / total) * 100) if total > 0 else 0

                tasks = [fetch_page(client, u) for u in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for r in results:
                    if r and isinstance(r, dict):
                        pages.append(r)

                await asyncio.sleep(0.5)

            job['pages_crawled'] = len(pages)
            job['progress'] = 100
            job['status'] = 'analyzing'
            job['current_url'] = 'Generating report...'

            # Analyze and store result
            result = analyze_site(pages, url)
            job['result'] = result
            job['status'] = 'complete'

    except Exception as e:
        import traceback
        traceback.print_exc()
        job['status'] = 'error'
        job['error'] = str(e)


def analyze_site(pages: list, url: str) -> dict:
    """Generate comprehensive site audit report."""
    if not pages:
        return {"error": "No pages could be crawled"}

    avg_score = round(sum(p['score'] for p in pages) / len(pages))
    sorted_pages = sorted(pages, key=lambda p: p['score'], reverse=True)
    top_pages = sorted_pages[:20]
    bottom_pages = [p for p in sorted_pages if p['score'] < 100][-20:][::-1]

    missing_title = sum(1 for p in pages if not p.get('title'))
    missing_meta = sum(1 for p in pages if not p.get('meta_description'))
    missing_h1 = sum(1 for p in pages if not p.get('h1'))
    thin_content = sum(1 for p in pages if p.get('word_count', 0) < 300)
    images_no_alt = sum(1 for p in pages if p.get('images_without_alt', 0) > 0)

    issues = []
    if missing_title > 0:
        issues.append({'title': 'Missing Title Tags', 'description': f'{missing_title} of {len(pages)} pages have no title tag.', 'severity': 'critical', 'affected_pages': missing_title})
    if missing_meta > 0:
        issues.append({'title': 'Missing Meta Descriptions', 'description': f'{missing_meta} pages have no meta description.', 'severity': 'warning', 'affected_pages': missing_meta})
    if missing_h1 > 0:
        issues.append({'title': 'Missing H1 Tags', 'description': f'{missing_h1} pages have no H1 heading.', 'severity': 'warning', 'affected_pages': missing_h1})
    if thin_content > 0:
        issues.append({'title': 'Thin Content Pages', 'description': f'{thin_content} pages have less than 300 words.', 'severity': 'warning', 'affected_pages': thin_content})
    if images_no_alt > 0:
        issues.append({'title': 'Images Missing Alt Text', 'description': f'{images_no_alt} pages have images without alt text.', 'severity': 'warning', 'affected_pages': images_no_alt})

    score_breakdown = {
        'title_optimisation': round(max(0, 100 - (missing_title / len(pages) * 100))),
        'meta_descriptions': round(max(0, 100 - (missing_meta / len(pages) * 100))),
        'heading_structure': round(max(0, 100 - (missing_h1 / len(pages) * 100))),
        'content_quality': round(max(0, 100 - (thin_content / len(pages) * 100))),
        'image_optimisation': round(max(0, 100 - (images_no_alt / len(pages) * 100))),
    }

    strengths = []
    weaknesses = []
    for k, v in score_breakdown.items():
        label = k.replace('_', ' ').title()
        if v >= 80:
            strengths.append(f'Good {label} ({v}% of pages optimised)')
        elif v < 50:
            weaknesses.append(f'Poor {label} — only {v}% of pages optimised')

    action_plan = []
    if missing_title > 0:
        action_plan.append({'title': 'Fix Missing Title Tags', 'description': f'Add unique title tags to {missing_title} pages (30-60 chars).', 'priority': 'high', 'estimated_impact': '+15-25% search visibility'})
    if missing_meta > 0:
        action_plan.append({'title': 'Write Meta Descriptions', 'description': f'Create meta descriptions for {missing_meta} pages (120-160 chars).', 'priority': 'medium', 'estimated_impact': '+10-20% click-through rate'})
    if thin_content > 0:
        action_plan.append({'title': 'Expand Thin Content', 'description': f'Add more content to {thin_content} pages (target 500+ words).', 'priority': 'medium', 'estimated_impact': 'Better keyword rankings'})
    if images_no_alt > 0:
        action_plan.append({'title': 'Add Alt Text to Images', 'description': f'Add alt text across {images_no_alt} pages.', 'priority': 'low', 'estimated_impact': 'Improved accessibility'})

    parsed = urlparse(url)
    return {
        'site_score': avg_score,
        'pages_crawled': len(pages),
        'critical_issues': len([i for i in issues if i['severity'] == 'critical']),
        'warnings': len([i for i in issues if i['severity'] == 'warning']),
        'summary': f'Audited {len(pages)} pages from {parsed.netloc}. Average SEO score: {avg_score}/100. Found {len([i for i in issues if i["severity"] == "critical"])} critical issues and {len([i for i in issues if i["severity"] == "warning"])} warnings.',
        'strengths': strengths or ['Site crawled successfully'],
        'weaknesses': weaknesses or ['No major weaknesses detected'],
        'score_breakdown': score_breakdown,
        'top_pages': [{'url': p['url'], 'title': p['title'] or p['url'], 'score': p['score'], 'word_count': p.get('word_count', 0)} for p in top_pages],
        'bottom_pages': [{'url': p['url'], 'title': p['title'] or p['url'], 'score': p['score'], 'main_issue': p['main_issue'], 'word_count': p.get('word_count', 0)} for p in bottom_pages],
        'issues': issues,
        'action_plan': action_plan,
    }
