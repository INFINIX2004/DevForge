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

# Tags we want to keep content from
CONTENT_TAGS = ["p", "h1", "h2", "h3", "h4", "li", "code", "pre", "td", "th"]

# Tags to fully remove (scripts, styles, nav clutter)
REMOVE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "advertisement"]

MAX_CHARS = 40000  # Gemini context limit safety


def fetch_page(url: str) -> str | None:
    """Fetch raw HTML from a URL."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[scraper] Failed to fetch {url}: {e}")
        return None


def clean_html(html: str) -> str:
    """Strip HTML down to meaningful text content."""
    soup = BeautifulSoup(html, "lxml")

    # Remove noise tags
    for tag in soup(REMOVE_TAGS):
        tag.decompose()

    # Extract text from content tags
    parts = []
    for tag in soup.find_all(CONTENT_TAGS):
        text = tag.get_text(separator=" ", strip=True)
        if text and len(text) > 10:  # skip trivial fragments
            parts.append(text)

    return "\n".join(parts)


def discover_doc_links(base_url: str, html: str, max_links: int = 8) -> list[str]:
    """
    Find internal links that look like API documentation pages.
    Looks for paths containing keywords like /api/, /reference/, /endpoints/, etc.
    """
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(base_url).netloc

    doc_keywords = [
        "api", "reference", "endpoint", "method", "resource",
        "authentication", "auth", "getting-started", "quickstart"
    ]

    seen = set()
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # Only same domain, only http(s), no duplicates
        if parsed.netloc != base_domain:
            continue
        if parsed.scheme not in ("http", "https"):
            continue
        if full_url in seen or full_url == base_url:
            continue

        path_lower = parsed.path.lower()
        if any(kw in path_lower for kw in doc_keywords):
            seen.add(full_url)
            links.append(full_url)

        if len(links) >= max_links:
            break

    return links


def scrape_docs(url: str, recursive: bool = True) -> dict:
    """
    Main entry point. Scrapes the given URL and optionally
    follows doc-related links to gather richer content.

    Returns:
        {
            "main_url": str,
            "content": str,       # cleaned text from main + sub pages
            "pages_scraped": int
        }
    """
    print(f"[scraper] Starting scrape: {url}")

    main_html = fetch_page(url)
    if not main_html:
        return {"main_url": url, "content": "", "pages_scraped": 0}

    main_text = clean_html(main_html)
    all_content = [f"=== PAGE: {url} ===\n{main_text}"]
    pages_scraped = 1

    if recursive:
        sub_links = discover_doc_links(url, main_html, max_links=6)
        print(f"[scraper] Found {len(sub_links)} sub-links to crawl")

        for link in sub_links:
            html = fetch_page(link)
            if not html:
                continue
            text = clean_html(html)
            all_content.append(f"=== PAGE: {link} ===\n{text}")
            pages_scraped += 1

            # Stay within context window limits
            combined = "\n\n".join(all_content)
            if len(combined) > MAX_CHARS:
                print(f"[scraper] Hit content limit at {pages_scraped} pages")
                break

    combined_content = "\n\n".join(all_content)

    # Final trim if still over limit
    if len(combined_content) > MAX_CHARS:
        combined_content = combined_content[:MAX_CHARS] + "\n\n[...content truncated...]"

    print(f"[scraper] Done. Pages: {pages_scraped}, Chars: {len(combined_content)}")

    return {
        "main_url": url,
        "content": combined_content,
        "pages_scraped": pages_scraped
    }
