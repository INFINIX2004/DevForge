import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

CONTENT_TAGS = ["p", "h1", "h2", "h3", "h4", "li", "code", "pre", "td", "th"]
REMOVE_TAGS  = ["script", "style", "nav", "footer", "header", "aside"]

# ── Limits ────────────────────────────────────────────────────────
MAX_CHARS      = 12000   # was 40k — this is plenty for Gemini to find endpoints
MAX_SUBPAGES   = 2       # was 6 — main page + 2 sub pages max
MIN_TEXT_LEN   = 15      # skip trivial fragments


def fetch_page(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[scraper] Failed to fetch {url}: {e}")
        return None


def clean_html(html: str, char_limit: int = 8000) -> str:
    """Strip HTML to meaningful text, hard-capped at char_limit."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(REMOVE_TAGS):
        tag.decompose()

    parts = []
    total = 0
    seen  = set()
    for tag in soup.find_all(CONTENT_TAGS):
        text = tag.get_text(separator=" ", strip=True)
        if not text or len(text) <= MIN_TEXT_LEN or text in seen:
            continue
        seen.add(text)
        remaining = char_limit - total
        if remaining <= 0:
            break
        # Trim the text itself if it would exceed the remaining budget
        if len(text) > remaining:
            text = text[:remaining]
        parts.append(text)
        total += len(text)

    return "\n".join(parts)


def discover_doc_links(base_url: str, html: str, max_links: int = 3) -> list[str]:
    """Find the most relevant sub-pages — auth + reference pages prioritised."""
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(base_url).netloc

    # Higher priority keywords first
    priority_kw  = ["authentication", "auth", "reference", "endpoint"]
    fallback_kw  = ["api", "method", "resource", "quickstart", "getting-started"]

    seen   = set([base_url])
    found  = {"priority": [], "fallback": []}

    for a in soup.find_all("a", href=True):
        href     = a["href"].strip()
        full_url = urljoin(base_url, href)
        parsed   = urlparse(full_url)

        if parsed.netloc != base_domain: continue
        if parsed.scheme not in ("http", "https"): continue
        if full_url in seen: continue
        seen.add(full_url)

        path = parsed.path.lower()
        if any(kw in path for kw in priority_kw):
            found["priority"].append(full_url)
        elif any(kw in path for kw in fallback_kw):
            found["fallback"].append(full_url)

    # Return priority links first, fill up to max_links with fallbacks
    result = found["priority"][:max_links]
    if len(result) < max_links:
        result += found["fallback"][:max_links - len(result)]

    return result[:max_links]


def scrape_docs(url: str, recursive: bool = True) -> dict:
    """
    Scrape docs URL. Keeps total content under MAX_CHARS.
    Returns { main_url, content, pages_scraped }
    """
    print(f"[scraper] Scraping: {url}")

    main_html = fetch_page(url)
    if not main_html:
        return {"main_url": url, "content": "", "pages_scraped": 0}

    # Give main page most of the budget
    main_text    = clean_html(main_html, char_limit=6000)
    all_content  = [f"=== MAIN PAGE ===\n{main_text}"]
    pages_scraped = 1

    if recursive:
        sub_links = discover_doc_links(url, main_html, max_links=MAX_SUBPAGES)
        print(f"[scraper] Sub-pages to crawl: {len(sub_links)}")

        per_page_budget = max(1000, (MAX_CHARS - len(main_text)) // max(len(sub_links), 1))

        for link in sub_links:
            html = fetch_page(link)
            if not html:
                continue
            text = clean_html(html, char_limit=per_page_budget)
            all_content.append(f"=== {link} ===\n{text}")
            pages_scraped += 1

            if sum(len(c) for c in all_content) >= MAX_CHARS:
                print(f"[scraper] Content limit reached at {pages_scraped} pages")
                break

    combined = "\n\n".join(all_content)
    if len(combined) > MAX_CHARS:
        combined = combined[:MAX_CHARS] + "\n[truncated]"

    print(f"[scraper] Done — {pages_scraped} pages, {len(combined)} chars")

    return {
        "main_url": url,
        "content": combined,
        "pages_scraped": pages_scraped
    }
