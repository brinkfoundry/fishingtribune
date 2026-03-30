#!/usr/bin/env python3
"""Fishing Tribune static site builder. Reads articles, generates HTML."""
import html
import json
import re
from datetime import datetime
from pathlib import Path

ARTICLES_SRC = Path('/Users/openclaw/clawd/ventures/tribune/articles')
SITE_DIR = Path(__file__).parent
ARTICLES_DIR = SITE_DIR / 'articles'
ARTICLES_DIR.mkdir(exist_ok=True)

BASE_URL = 'https://fishingtribune.com'
AFFILIATE_TAG = 'fishingtribun-20'
SITE_NAME = 'Fishing Tribune'

# Best version selection: prefer REWRITE > FULL > PIPELINE > CLEAN > original
# Skip critiques, notes, and short files (< 1500 words)
PICKS = {
    '01': ('article-01-fish-finders-under-200.md', 'best-fish-finders-under-200'),
    '02': ('article-02-fishing-kayaks-under-1000.md', 'best-fishing-kayaks-under-1000'),
    '03': ('article-03-trolling-motors-kayak-REVENUE.md', 'best-trolling-motors-for-kayak'),
    '04': ('article-04-spinning-rods-bass.md', 'best-spinning-rods-bass-fishing'),
    '05': ('article-05-fly-fishing-rods-REVENUE.md', 'best-fly-fishing-rods-beginners'),
    '06': ('article-06-saltwater-spinning-REVENUE.md', 'best-saltwater-spinning-rods'),
    '07': ('article-07-fish-finders-under-500-kayak.md', 'best-fish-finders-under-500-kayak'),
    '08': ('article-08-saltwater-fly-reels-under-300.md', 'best-saltwater-fly-reels-under-300'),
    '09': ('article-09-best-bass-fishing-lures.md', 'best-bass-fishing-lures'),
    '10': ('article-10-best-kayak-anchors.md', 'best-kayak-anchors'),
    '11': ('article-11-best-tackle-boxes.md', 'best-tackle-boxes'),
    '12': ('article-12-surf-fishing-rods.md', 'best-surf-fishing-rods'),
    '13': ('article-13-best-polarized-fishing-sunglasses.md', 'best-polarized-fishing-sunglasses'),
    '14': ('article-14-fishing-backpacks.md', 'best-fishing-backpacks'),
}

FTC_DISCLOSURE = (
    'Fishing Tribune is reader-supported. When you buy through links on our site, '
    'we may earn an affiliate commission at no extra cost to you. '
    'We only recommend products we genuinely believe will help you catch more fish. '
    '<a href="/affiliate-disclosure">Full disclosure</a>.'
)

FOOTER_DISCLOSURE = (
    'Fishing Tribune is a participant in the Amazon Services LLC Associates Program, '
    'an affiliate advertising program designed to provide a means for sites to earn '
    'advertising fees by advertising and linking to Amazon.com. As an Amazon Associate, '
    'we earn from qualifying purchases.'
)


def esc(s: str) -> str:
    return html.escape(str(s))


def md_to_html(md: str) -> str:
    """Minimal markdown to HTML. Handles headings, bold, italic, links, lists, blockquotes, hr, tables."""
    lines = md.split('\n')
    out = []
    in_ul = False
    in_ol = False
    in_table = False
    in_blockquote = False
    table_rows = []

    def flush_list():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append('</ul>')
            in_ul = False
        if in_ol:
            out.append('</ol>')
            in_ol = False

    def flush_table():
        nonlocal in_table, table_rows
        if in_table and table_rows:
            out.append('<table>')
            for i, row in enumerate(table_rows):
                cells = [c.strip() for c in row.strip('|').split('|')]
                if i == 0:
                    out.append('<thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in cells) + '</tr></thead><tbody>')
                elif set(row.replace('|', '').replace('-', '').replace(':', '').strip()) == set():
                    continue  # separator row
                else:
                    out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in cells) + '</tr>')
            out.append('</tbody></table>')
            table_rows = []
            in_table = False

    def flush_blockquote():
        nonlocal in_blockquote
        if in_blockquote:
            out.append('</blockquote>')
            in_blockquote = False

    def inline(text: str) -> str:
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # Links — add affiliate tag to Amazon links
        def link_replace(m):
            label = m.group(1)
            url = m.group(2)
            if 'amazon.com' in url.lower():
                sep = '&' if '?' in url else '?'
                url = f'{url}{sep}tag={AFFILIATE_TAG}'
                return f'<a href="{esc(url)}" class="affiliate-link" rel="nofollow sponsored" target="_blank">{label}</a>'
            return f'<a href="{esc(url)}">{label}</a>'
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_replace, text)
        # Inline code
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        return text

    for line in lines:
        stripped = line.strip()

        # Blank line
        if not stripped:
            flush_list()
            if not in_table:
                flush_blockquote()
            continue

        # Table
        if '|' in stripped and stripped.startswith('|'):
            flush_list()
            flush_blockquote()
            in_table = True
            table_rows.append(stripped)
            continue
        else:
            flush_table()

        # Blockquote
        if stripped.startswith('>'):
            flush_list()
            if not in_blockquote:
                out.append('<blockquote>')
                in_blockquote = True
            out.append(inline(stripped.lstrip('> ').strip()))
            continue
        else:
            flush_blockquote()

        # Headings
        if stripped.startswith('######'):
            flush_list()
            out.append(f'<h6>{inline(stripped[6:].strip())}</h6>')
        elif stripped.startswith('#####'):
            flush_list()
            out.append(f'<h5>{inline(stripped[5:].strip())}</h5>')
        elif stripped.startswith('####'):
            flush_list()
            out.append(f'<h4>{inline(stripped[4:].strip())}</h4>')
        elif stripped.startswith('###'):
            flush_list()
            out.append(f'<h3>{inline(stripped[3:].strip())}</h3>')
        elif stripped.startswith('##'):
            flush_list()
            out.append(f'<h2>{inline(stripped[2:].strip())}</h2>')
        elif stripped.startswith('# '):
            flush_list()
            # Skip — title is handled separately
            continue
        elif stripped.startswith('---') or stripped.startswith('***'):
            flush_list()
            out.append('<hr>')
        # Unordered list
        elif re.match(r'^[-*+]\s', stripped):
            if not in_ul:
                flush_list()
                out.append('<ul>')
                in_ul = True
            out.append(f'<li>{inline(stripped[2:].strip())}</li>')
        # Ordered list
        elif re.match(r'^\d+\.\s', stripped):
            if not in_ol:
                flush_list()
                out.append('<ol>')
                in_ol = True
            text = re.sub(r'^\d+\.\s*', '', stripped)
            out.append(f'<li>{inline(text)}</li>')
        else:
            flush_list()
            out.append(f'<p>{inline(stripped)}</p>')

    flush_list()
    flush_table()
    flush_blockquote()
    return '\n'.join(out)


def extract_title(md: str, fallback: str) -> str:
    # Try JSON-LD headline first (articles 9-13 format)
    m = re.search(r'"headline"\s*:\s*"([^"]+)"', md[:2000])
    if m:
        return m.group(1).strip()
    for line in md.split('\n')[:20]:
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip().strip('*')
        # Bold-title lines like **Title Here**
        m = re.match(r'^\*\*(.+)\*\*\s*$', line)
        if m:
            return m.group(1).strip()
    # Try first non-empty non-meta line that looks like a title
    for line in md.split('\n')[:20]:
        line = line.strip()
        if (line and not line.startswith('*') and not line.startswith('#')
                and not line.startswith('{') and not line.startswith('FTC')
                and not line.startswith('FishingTribune |')
                and not line.startswith('Last Updated')
                and len(line) > 20 and len(line) < 120):
            return line[:100]
    return fallback


def extract_excerpt(md: str, max_len: int = 160) -> str:
    """Extract first substantive paragraph for meta description."""
    # Try JSON-LD description first
    m = re.search(r'"description"\s*:\s*"([^"]+)"', md[:2000])
    if m and len(m.group(1)) > 40:
        desc = m.group(1).strip()
        return desc[:max_len].rsplit(' ', 1)[0] + '...' if len(desc) > max_len else desc
    for line in md.split('\n'):
        line = line.strip()
        if (not line or line.startswith('#') or line.startswith('*By ')
                or line.startswith('*Target') or line.startswith('{')
                or line.startswith('FTC') or line.startswith('FishingTribune |')
                or line.startswith('Last Updated')):
            continue
        # Remove markdown formatting
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
        clean = re.sub(r'\*(.+?)\*', r'\1', clean)
        clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
        if len(clean) > 40:
            return clean[:max_len].rsplit(' ', 1)[0] + '...' if len(clean) > max_len else clean
    return f'{SITE_NAME} - Expert fishing gear reviews and recommendations.'


def article_page(title: str, body_html: str, slug: str, excerpt: str, date: str) -> str:
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | {SITE_NAME}</title>
<meta name="description" content="{esc(excerpt)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{BASE_URL}/articles/{slug}.html">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(excerpt)}">
<meta property="og:url" content="{BASE_URL}/articles/{slug}.html">
<meta property="og:site_name" content="{SITE_NAME}">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": {json.dumps(title)},
  "description": {json.dumps(excerpt)},
  "url": "{BASE_URL}/articles/{slug}.html",
  "datePublished": "{date}",
  "dateModified": "{date}",
  "author": {{"@type": "Organization", "name": "{SITE_NAME}"}},
  "publisher": {{
    "@type": "Organization",
    "name": "{SITE_NAME}",
    "url": "{BASE_URL}"
  }}
}}
</script>
<link rel="stylesheet" href="/style.css">
</head>
<body>
<header class="site-header">
  <div class="container wide">
    <div class="site-title"><a href="/">Fishing <span>Tribune</span></a></div>
    <nav class="site-nav">
      <a href="/">Home</a>
      <a href="/affiliate-disclosure.html">Disclosure</a>
    </nav>
  </div>
</header>
<main class="container">
  <article>
    <div class="article-header">
      <h1>{esc(title)}</h1>
      <div class="article-meta">By Fishing Tribune Staff &middot; Updated March 2026</div>
    </div>
    <div class="ftc-disclosure">{FTC_DISCLOSURE}</div>
    <div class="article-body">
{body_html}
    </div>
  </article>
</main>
<footer class="site-footer">
  <div class="container wide">
    <div class="footer-links">
      <a href="/">Home</a>
      <a href="/affiliate-disclosure.html">Affiliate Disclosure</a>
    </div>
    <div class="footer-disclosure">{FOOTER_DISCLOSURE}</div>
    <div class="footer-copy">&copy; 2026 {SITE_NAME}. All rights reserved.</div>
  </div>
</footer>
</body>
</html>'''


def index_page(articles: list[dict]) -> str:
    cards = []
    for a in articles:
        cards.append(f'''  <article class="article-card">
    <h2><a href="/articles/{a['slug']}.html">{esc(a['title'])}</a></h2>
    <p class="excerpt">{esc(a['excerpt'])}</p>
    <div class="meta">{a['words']:,} words &middot; Updated March 2026</div>
    <a href="/articles/{a['slug']}.html" class="read-more">Read full review &rarr;</a>
  </article>''')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{SITE_NAME} — Expert Fishing Gear Reviews &amp; Buying Guides</title>
<meta name="description" content="Honest, data-driven fishing gear reviews. Fish finders, kayaks, rods, and more — tested by anglers who actually fish.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{BASE_URL}/">
<meta property="og:type" content="website">
<meta property="og:title" content="{SITE_NAME}">
<meta property="og:description" content="Expert fishing gear reviews and buying guides.">
<meta property="og:url" content="{BASE_URL}/">
<meta property="og:site_name" content="{SITE_NAME}">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "{SITE_NAME}",
  "url": "{BASE_URL}",
  "description": "Expert fishing gear reviews and buying guides."
}}
</script>
<link rel="stylesheet" href="/style.css">
</head>
<body>
<header class="site-header">
  <div class="container wide">
    <div class="site-title"><a href="/">Fishing <span>Tribune</span></a></div>
    <nav class="site-nav">
      <a href="/">Home</a>
      <a href="/affiliate-disclosure.html">Disclosure</a>
    </nav>
  </div>
</header>
<main class="container">
  <section class="hero">
    <h1>Fishing Gear That Actually Works</h1>
    <p>Honest reviews from anglers who fish. No fluff, no filler, no fake rankings. Just the gear that holds up on the water.</p>
  </section>
  <section class="article-grid">
{chr(10).join(cards)}
  </section>
</main>
<footer class="site-footer">
  <div class="container wide">
    <div class="footer-links">
      <a href="/">Home</a>
      <a href="/affiliate-disclosure.html">Affiliate Disclosure</a>
    </div>
    <div class="footer-disclosure">{FOOTER_DISCLOSURE}</div>
    <div class="footer-copy">&copy; 2026 {SITE_NAME}. All rights reserved.</div>
  </div>
</footer>
</body>
</html>'''


def disclosure_page() -> str:
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Affiliate Disclosure | {SITE_NAME}</title>
<meta name="description" content="{SITE_NAME} affiliate disclosure and FTC compliance.">
<link rel="canonical" href="{BASE_URL}/affiliate-disclosure.html">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<header class="site-header">
  <div class="container wide">
    <div class="site-title"><a href="/">Fishing <span>Tribune</span></a></div>
    <nav class="site-nav">
      <a href="/">Home</a>
      <a href="/affiliate-disclosure.html">Disclosure</a>
    </nav>
  </div>
</header>
<main class="container">
  <div class="article-header">
    <h1>Affiliate Disclosure</h1>
  </div>
  <div class="article-body">
    <p>{SITE_NAME} is reader-supported. When you buy through links on our site, we may earn an affiliate commission at no extra cost to you.</p>
    <h2>How We Make Money</h2>
    <p>We participate in the Amazon Services LLC Associates Program, an affiliate advertising program designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.com.</p>
    <p>Some links on our site are affiliate links, meaning we get a small commission if you click and make a purchase. This does not affect the price you pay.</p>
    <h2>Our Promise</h2>
    <p>We only recommend products we genuinely believe will help you catch more fish. Our reviews are based on real research, real specifications, and real angler feedback. No brand pays for placement. No manufacturer sponsors our rankings.</p>
    <p>If a product is bad, we say so. If a cheap option outperforms an expensive one, we say that too. Your trust matters more than any commission.</p>
    <h2>FTC Compliance</h2>
    <p>In accordance with the Federal Trade Commission's 16 CFR Part 255, "Guides Concerning the Use of Endorsements and Testimonials in Advertising," we disclose that we receive compensation for products reviewed or linked on this site.</p>
    <p>If you have questions about our disclosure policy, contact us at hello@fishingtribune.com.</p>
  </div>
</main>
<footer class="site-footer">
  <div class="container wide">
    <div class="footer-links"><a href="/">Home</a></div>
    <div class="footer-disclosure">{FOOTER_DISCLOSURE}</div>
    <div class="footer-copy">&copy; 2026 {SITE_NAME}. All rights reserved.</div>
  </div>
</footer>
</body>
</html>'''


def build_sitemap(articles: list[dict]) -> str:
    urls = [f'  <url><loc>{BASE_URL}/</loc><lastmod>2026-03-29</lastmod><priority>1.0</priority></url>']
    urls.append(f'  <url><loc>{BASE_URL}/affiliate-disclosure.html</loc><priority>0.3</priority></url>')
    for a in articles:
        urls.append(f'  <url><loc>{BASE_URL}/articles/{a["slug"]}.html</loc><lastmod>2026-03-29</lastmod><priority>0.8</priority></url>')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''


def build_robots() -> str:
    return f'''User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml'''


def main():
    articles = []
    date = '2026-03-29'

    for num in sorted(PICKS.keys()):
        fname, slug = PICKS[num]
        src = ARTICLES_SRC / fname
        if not src.exists():
            print(f'SKIP: {fname} not found')
            continue

        md = src.read_bytes().replace(b'\x00', b'').decode('utf-8', errors='replace')
        title = extract_title(md, slug.replace('-', ' ').title())
        excerpt = extract_excerpt(md)
        body_html = md_to_html(md)
        words = len(md.split())

        # Write article page
        page = article_page(title, body_html, slug, excerpt, date)
        (ARTICLES_DIR / f'{slug}.html').write_text(page, encoding='utf-8')
        print(f'Built: articles/{slug}.html ({words:,} words)')

        articles.append({'num': num, 'slug': slug, 'title': title,
                         'excerpt': excerpt, 'words': words})

    # Index
    idx = index_page(articles)
    (SITE_DIR / 'index.html').write_text(idx, encoding='utf-8')
    print(f'Built: index.html ({len(articles)} articles)')

    # Disclosure
    disc = disclosure_page()
    (SITE_DIR / 'affiliate-disclosure.html').write_text(disc, encoding='utf-8')
    print('Built: affiliate-disclosure.html')

    # Sitemap
    sm = build_sitemap(articles)
    (SITE_DIR / 'sitemap.xml').write_text(sm, encoding='utf-8')
    print('Built: sitemap.xml')

    # Robots
    rb = build_robots()
    (SITE_DIR / 'robots.txt').write_text(rb, encoding='utf-8')
    print('Built: robots.txt')

    print(f'\nDone. {len(articles)} articles, site at {SITE_DIR}/')


if __name__ == '__main__':
    main()
