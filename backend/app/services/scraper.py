import httpx
import re
from bs4 import BeautifulSoup
from fastapi import HTTPException


async def scrape_website(url: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SEMBot/1.0)"}
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as c:
            response = await c.get(url, headers=headers)
            html = response.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch URL: {str(e)}")

    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("title")
    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta_kw = soup.find("meta", attrs={"name": "keywords"})
    canonical = soup.find("link", attrs={"rel": "canonical"})
    robots = soup.find("meta", attrs={"name": "robots"})
    viewport = soup.find("meta", attrs={"name": "viewport"})
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_desc = soup.find("meta", attrs={"property": "og:description"})

    h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2")][:10]
    h3s = [h.get_text(strip=True) for h in soup.find_all("h3")][:10]

    all_links = soup.find_all("a", href=True)
    internal_links = [l["href"] for l in all_links if url in l["href"] or l["href"].startswith("/")]
    external_links = [l["href"] for l in all_links if l["href"].startswith("http") and url not in l["href"]]

    images = soup.find_all("img")
    images_without_alt = [img.get("src", "") for img in images if not img.get("alt")]

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    body_text = soup.get_text(separator=" ", strip=True)
    body_text = re.sub(r'\s+', ' ', body_text)[:3000]

    schema_tags = soup.find_all("script", attrs={"type": "application/ld+json"})

    return {
        "url": url,
        "title": title.get_text(strip=True) if title else None,
        "meta_description": meta_desc["content"] if meta_desc and meta_desc.get("content") else None,
        "meta_keywords": meta_kw["content"] if meta_kw and meta_kw.get("content") else None,
        "canonical_url": canonical["href"] if canonical and canonical.get("href") else None,
        "robots_meta": robots["content"] if robots and robots.get("content") else None,
        "has_viewport": viewport is not None,
        "og_title": og_title["content"] if og_title and og_title.get("content") else None,
        "og_description": og_desc["content"] if og_desc and og_desc.get("content") else None,
        "h1_tags": h1s,
        "h2_tags": h2s,
        "h3_tags": h3s,
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "images_count": len(images),
        "images_without_alt_count": len(images_without_alt),
        "has_schema_markup": len(schema_tags) > 0,
        "body_text_sample": body_text,
        "html_size_kb": round(len(html) / 1024, 1),
    }
