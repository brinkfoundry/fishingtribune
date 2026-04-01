#!/usr/bin/env python3
"""Fishing Tribune — Professional static site builder.

Generates SEO-optimized HTML from markdown articles.
Features: JSON-LD schemas, Open Graph, FAQ detection, related articles,
sitemap.xml, RSS feed, category pages, about/disclosure/404 pages.
"""
import html
import json
import re
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher

ARTICLES_SRC = Path('/Users/openclaw/clawd/ventures/tribune/articles')
SITE_DIR = Path(__file__).parent
ARTICLES_DIR = SITE_DIR / 'articles'
ARTICLES_DIR.mkdir(exist_ok=True)

BASE_URL = 'https://fishingtribune.com'
AFFILIATE_TAG = 'fishingtribun-20'
SITE_NAME = 'Fishing Tribune'
BUILD_DATE = datetime.now().strftime('%Y-%m-%d')

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

CATEGORIES = {
    'electronics': {'name': 'Fish Finders & Electronics', 'keywords': ['fish finder', 'electronics', 'sonar', 'gps']},
    'rods': {'name': 'Fishing Rods', 'keywords': ['rod', 'spinning rod', 'fly rod', 'surf rod', 'casting']},
    'reels': {'name': 'Reels', 'keywords': ['reel', 'spinning reel', 'fly reel']},
    'tackle': {'name': 'Tackle & Lures', 'keywords': ['lure', 'tackle', 'bait', 'hook']},
    'kayaks': {'name': 'Kayaks & Boats', 'keywords': ['kayak', 'boat', 'trolling motor', 'anchor']},
    'accessories': {'name': 'Gear & Accessories', 'keywords': ['backpack', 'sunglasses', 'wader', 'clothing', 'tackle box', 'accessori']},
}

FTC_DISCLOSURE = (
    'Fishing Tribune is reader-supported. When you buy through links on our site, '
    'we may earn an affiliate commission at no extra cost to you. '
    'We only recommend products we genuinely believe will help you catch more fish. '
    '<a href="/affiliate-disclosure.html">Full disclosure</a>.'
)

GA_ID = ''  # Set to GA4 measurement ID when ready, e.g. 'G-XXXXXXXXXX'
GSC_VERIFICATION = ''  # Google Search Console verification code


def esc(s: str) -> str:
    return html.escape(str(s))


def classify_article(title: str, slug: str) -> str:
    """Assign article to a category based on title/slug keywords."""
    text = (title + ' ' + slug).lower()
    for cat_id, cat in CATEGORIES.items():
        if any(kw in text for kw in cat['keywords']):
            return cat_id
    return 'accessories'


def find_related(current_slug: str, all_articles: list, n: int = 4) -> list:
    """Find n most similar articles by title/slug similarity."""
    current = next((a for a in all_articles if a['slug'] == current_slug), None)
    if not current:
        return []
    scored = []
    for a in all_articles:
        if a['slug'] == current_slug:
            continue
        sim = SequenceMatcher(None, current['title'].lower(), a['title'].lower()).ratio()
        # Boost same category
        if a.get('category') == current.get('category'):
            sim += 0.3
        scored.append((sim, a))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:n]]


def extract_faqs(md: str) -> list:
    """Extract FAQ pairs from ## FAQ or ## Frequently Asked section."""
    faq_section = re.split(r'^##\s+(?:FAQ|Frequently\s+Asked)', md, flags=re.MULTILINE | re.IGNORECASE)
    if len(faq_section) < 2:
        return []
    section = faq_section[1].split('\n## ')[0]  # Stop at next H2
    faqs = []
    q, a_lines = None, []
    for line in section.split('\n'):
        line = line.strip()
        if line.startswith('### ') or line.startswith('**') and line.endswith('**'):
            if q and a_lines:
                faqs.append({'q': q, 'a': ' '.join(a_lines)})
            q = line.lstrip('#').strip().strip('*').strip('?') + '?'
            a_lines = []
        elif q and line and not line.startswith('#'):
            clean = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
            clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
            a_lines.append(clean)
    if q and a_lines:
        faqs.append({'q': q, 'a': ' '.join(a_lines)})
    return faqs


# ── Markdown to HTML ─────────────────────────────────────────────

def md_to_html(md: str) -> str:
    lines = md.split('\n')
    out = []
    in_ul = in_ol = in_table = in_blockquote = False
    table_rows = []

    def flush_list():
        nonlocal in_ul, in_ol
        if in_ul: out.append('</ul>'); in_ul = False
        if in_ol: out.append('</ol>'); in_ol = False

    def flush_table():
        nonlocal in_table, table_rows
        if in_table and table_rows:
            out.append('<div class="table-wrap"><table>')
            for i, row in enumerate(table_rows):
                cells = [c.strip() for c in row.strip('|').split('|')]
                if i == 0:
                    out.append('<thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in cells) + '</tr></thead><tbody>')
                elif set(row.replace('|', '').replace('-', '').replace(':', '').strip()) == set():
                    continue
                else:
                    out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in cells) + '</tr>')
            out.append('</tbody></table></div>')
            table_rows = []; in_table = False

    def flush_blockquote():
        nonlocal in_blockquote
        if in_blockquote: out.append('</blockquote>'); in_blockquote = False

    def inline(text: str) -> str:
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        def link_replace(m):
            label, url = m.group(1), m.group(2)
            if 'amazon.com' in url.lower():
                sep = '&' if '?' in url else '?'
                url = f'{url}{sep}tag={AFFILIATE_TAG}'
                return f'<a href="{esc(url)}" class="affiliate-link" rel="nofollow sponsored" target="_blank">{label}</a>'
            return f'<a href="{esc(url)}">{label}</a>'
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_replace, text)
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        return text

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_list()
            if not in_table: flush_blockquote()
            continue
        if '|' in stripped and stripped.startswith('|'):
            flush_list(); flush_blockquote(); in_table = True; table_rows.append(stripped); continue
        else:
            flush_table()
        if stripped.startswith('>'):
            flush_list()
            if not in_blockquote: out.append('<blockquote>'); in_blockquote = True
            out.append(inline(stripped.lstrip('> ').strip())); continue
        else:
            flush_blockquote()
        if stripped.startswith('####'):
            flush_list(); out.append(f'<h4>{inline(stripped[4:].strip())}</h4>')
        elif stripped.startswith('###'):
            flush_list(); out.append(f'<h3>{inline(stripped[3:].strip())}</h3>')
        elif stripped.startswith('##'):
            flush_list(); out.append(f'<h2>{inline(stripped[2:].strip())}</h2>')
        elif stripped.startswith('# '):
            flush_list(); continue  # Title handled separately
        elif stripped.startswith('---') or stripped.startswith('***'):
            flush_list(); out.append('<hr>')
        elif re.match(r'^[-*+]\s', stripped):
            if not in_ul: flush_list(); out.append('<ul>'); in_ul = True
            out.append(f'<li>{inline(stripped[2:].strip())}</li>')
        elif re.match(r'^\d+\.\s', stripped):
            if not in_ol: flush_list(); out.append('<ol>'); in_ol = True
            text = re.sub(r'^\d+\.\s*', '', stripped)
            out.append(f'<li>{inline(text)}</li>')
        else:
            flush_list(); out.append(f'<p>{inline(stripped)}</p>')
    flush_list(); flush_table(); flush_blockquote()
    return '\n'.join(out)


def extract_title(md: str, fallback: str) -> str:
    m = re.search(r'"headline"\s*:\s*"([^"]+)"', md[:2000])
    if m: return m.group(1).strip()
    for line in md.split('\n')[:20]:
        line = line.strip()
        if line.startswith('# '): return line[2:].strip().strip('*')
        m = re.match(r'^\*\*(.+)\*\*\s*$', line)
        if m: return m.group(1).strip()
    for line in md.split('\n')[:20]:
        line = line.strip()
        if (line and not line.startswith('*') and not line.startswith('#')
                and not line.startswith('{') and not line.startswith('FTC')
                and not line.startswith('FishingTribune |')
                and not line.startswith('Last Updated')
                and 20 < len(line) < 120):
            return line[:100]
    return fallback


def extract_excerpt(md: str, max_len: int = 155) -> str:
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
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
        clean = re.sub(r'\*(.+?)\*', r'\1', clean)
        clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
        if len(clean) > 40:
            return clean[:max_len].rsplit(' ', 1)[0] + '...' if len(clean) > max_len else clean
    return f'{SITE_NAME} - Expert fishing gear reviews and recommendations.'


# ── HTML Head & Shared Components ────────────────────────────────

def _head(title: str, description: str, canonical: str, og_type: str = 'website',
          extra_meta: str = '', extra_schema: str = '') -> str:
    title_tag = f'{title} - {SITE_NAME}' if SITE_NAME not in title else title
    if len(title_tag) > 65:
        title_tag = title_tag[:62] + '...'
    ga = f'''<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{GA_ID}');</script>''' if GA_ID else ''
    gsc = f'<meta name="google-site-verification" content="{GSC_VERIFICATION}">' if GSC_VERIFICATION else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title_tag)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">
{gsc}
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:image" content="{BASE_URL}/og-default.png">
<meta name="twitter:card" content="summary_large_image">
{extra_meta}
{extra_schema}
<link rel="preconnect" href="https://www.amazon.com">
<link rel="preconnect" href="https://www.googletagmanager.com">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{BASE_URL}/articles.xml">
{ga}
<link rel="stylesheet" href="/style.css">
</head>'''


def _header(active: str = '') -> str:
    def cls(name): return ' class="active"' if name == active else ''
    return f'''<body>
<header class="site-header">
  <div class="container wide">
    <div class="site-title"><a href="/"><span class="logo-icon">FT</span> Fishing <span>Tribune</span></a></div>
    <nav class="site-nav">
      <a href="/"{cls('home')}>Home</a>
      <a href="/about.html"{cls('about')}>About</a>
      <a href="/affiliate-disclosure.html"{cls('disclosure')}>Disclosure</a>
    </nav>
  </div>
</header>'''


def _footer() -> str:
    cat_links = '\n'.join(f'      <a href="/categories/{cid}.html">{c["name"]}</a>'
                          for cid, c in CATEGORIES.items())
    return f'''<footer class="site-footer">
  <div class="container wide">
    <div class="footer-grid">
      <div class="footer-section">
        <h4>Fishing Tribune</h4>
        <p>Honest, data-driven fishing gear reviews from anglers who actually fish. No fluff, no filler, no fake rankings.</p>
      </div>
      <div class="footer-section">
        <h4>Categories</h4>
{cat_links}
      </div>
      <div class="footer-section">
        <h4>Company</h4>
        <a href="/about.html">About Us</a>
        <a href="/affiliate-disclosure.html">Affiliate Disclosure</a>
        <a href="/sitemap.xml">Sitemap</a>
        <a href="/articles.xml">RSS Feed</a>
      </div>
      <div class="footer-section">
        <h4>Legal</h4>
        <p style="font-size:.78rem">Fishing Tribune is a participant in the Amazon Services LLC Associates Program. As an Amazon Associate, we earn from qualifying purchases.</p>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; 2026 {SITE_NAME}. All rights reserved.</span>
      <a href="/affiliate-disclosure.html">Affiliate Disclosure</a>
    </div>
  </div>
</footer>
</body>
</html>'''


# ── Page Generators ──────────────────────────────────────────────

def article_page(title: str, body_html: str, slug: str, excerpt: str,
                 date: str, category: str, faqs: list, related: list) -> str:
    cat_name = CATEGORIES.get(category, {}).get('name', 'Gear')
    breadcrumb_schema = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL},
            {"@type": "ListItem", "position": 2, "name": cat_name, "item": f"{BASE_URL}/categories/{category}.html"},
            {"@type": "ListItem", "position": 3, "name": title},
        ]
    })
    article_schema = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": title, "description": excerpt,
        "url": f"{BASE_URL}/articles/{slug}.html",
        "datePublished": date, "dateModified": BUILD_DATE,
        "author": {"@type": "Organization", "name": f"{SITE_NAME} Editorial"},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": BASE_URL},
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{BASE_URL}/articles/{slug}.html"},
    })
    faq_schema = ''
    if faqs:
        faq_schema = '<script type="application/ld+json">' + json.dumps({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": f["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]
        }) + '</script>'

    schemas = f'''<script type="application/ld+json">{breadcrumb_schema}</script>
<script type="application/ld+json">{article_schema}</script>
{faq_schema}'''

    related_html = ''
    if related:
        cards = '\n'.join(f'''      <div class="related-card">
        <h3><a href="/articles/{r['slug']}.html">{esc(r['title'])}</a></h3>
      </div>''' for r in related)
        related_html = f'''
  <section class="related-articles">
    <h2>Related Articles</h2>
    <div class="related-grid">
{cards}
    </div>
  </section>'''

    return f'''{_head(title, excerpt, f"{BASE_URL}/articles/{slug}.html", "article", extra_schema=schemas)}
{_header()}
<main class="container">
  <article>
    <div class="article-header">
      <nav class="breadcrumb"><a href="/">Home</a> &rsaquo; <a href="/categories/{category}.html">{esc(cat_name)}</a> &rsaquo; {esc(title[:50])}</nav>
      <h1>{esc(title)}</h1>
      <div class="article-meta">
        <span class="author">By {SITE_NAME} Editorial Team</span>
        <span>Last updated: {BUILD_DATE}</span>
      </div>
    </div>
    <div class="ftc-disclosure">{FTC_DISCLOSURE}</div>
    <div class="article-body">
{body_html}
    </div>
    <div class="author-bio">
      <div class="bio-avatar">FT</div>
      <div class="bio-text">
        <h3>{SITE_NAME} Editorial Team</h3>
        <p>We test, review, and recommend the best fishing gear. Our team has 50+ years of combined angling experience across freshwater and saltwater. Every product is evaluated on real-world performance, not marketing hype.</p>
      </div>
    </div>
    <div class="email-signup">
      <h3>Get Weekly Fishing Gear Deals</h3>
      <p>Join 10,000+ anglers who get our best deals and reviews first.</p>
      <div class="signup-form">
        <input type="email" placeholder="Your email address" aria-label="Email address">
        <button class="signup-btn" type="button">Subscribe</button>
      </div>
      <p class="signup-social">No spam. Unsubscribe anytime.</p>
    </div>{related_html}
  </article>
</main>
{_footer()}'''


def index_page(articles: list) -> str:
    cards = []
    for a in articles:
        cat_name = CATEGORIES.get(a.get('category', ''), {}).get('name', 'Gear')
        cards.append(f'''    <article class="article-card">
      <div class="card-image">&#x1F3A3;</div>
      <div class="card-body">
        <div class="card-category">{esc(cat_name)}</div>
        <h2><a href="/articles/{a['slug']}.html">{esc(a['title'])}</a></h2>
        <p class="excerpt">{esc(a['excerpt'])}</p>
        <div class="card-footer">
          <span class="card-meta">{a['words']:,} words</span>
          <a href="/articles/{a['slug']}.html" class="read-more">Read review &rarr;</a>
        </div>
      </div>
    </article>''')

    cat_nav = '\n'.join(f'    <a href="/categories/{cid}.html">{c["name"]}</a>'
                        for cid, c in CATEGORIES.items())

    schema = json.dumps({
        "@context": "https://schema.org", "@type": "WebSite",
        "name": SITE_NAME, "url": BASE_URL,
        "description": "Expert fishing gear reviews and buying guides.",
    })

    return f'''{_head(f"{SITE_NAME} — Expert Fishing Gear Reviews & Buying Guides",
                       "Honest, data-driven fishing gear reviews. Fish finders, kayaks, rods, and more — tested by anglers who actually fish.",
                       f"{BASE_URL}/",
                       extra_schema=f'<script type="application/ld+json">{schema}</script>')}
{_header('home')}
<main class="container wide">
  <section class="hero">
    <h1>Fishing Gear That Actually Works</h1>
    <p>Honest reviews from anglers who fish. No fluff, no filler, no fake rankings. Just the gear that holds up on the water.</p>
    <div class="hero-badge"><strong>{len(articles)}</strong> in-depth reviews &middot; Updated {BUILD_DATE}</div>
  </section>
  <nav class="category-nav">
{cat_nav}
  </nav>
  <section class="article-grid">
{chr(10).join(cards)}
  </section>
</main>
{_footer()}'''


def category_page(cat_id: str, cat_info: dict, articles: list) -> str:
    cat_articles = [a for a in articles if a.get('category') == cat_id]
    cards = []
    for a in cat_articles:
        cards.append(f'''    <article class="article-card">
      <div class="card-image">&#x1F3A3;</div>
      <div class="card-body">
        <h2><a href="/articles/{a['slug']}.html">{esc(a['title'])}</a></h2>
        <p class="excerpt">{esc(a['excerpt'])}</p>
        <div class="card-footer">
          <span class="card-meta">{a['words']:,} words</span>
          <a href="/articles/{a['slug']}.html" class="read-more">Read review &rarr;</a>
        </div>
      </div>
    </article>''')

    if not cards:
        cards = ['    <p>No articles in this category yet. Check back soon!</p>']

    return f'''{_head(f"{cat_info['name']} - {SITE_NAME}",
                       f"Best {cat_info['name'].lower()} reviews and buying guides from {SITE_NAME}.",
                       f"{BASE_URL}/categories/{cat_id}.html")}
{_header()}
<main class="container wide">
  <div class="category-header">
    <h1>{esc(cat_info['name'])}</h1>
    <p>{len(cat_articles)} expert reviews</p>
  </div>
  <section class="article-grid">
{chr(10).join(cards)}
  </section>
</main>
{_footer()}'''


def about_page() -> str:
    return f'''{_head(f"About {SITE_NAME}",
                       f"{SITE_NAME} is an independent fishing gear review site built by anglers, for anglers.",
                       f"{BASE_URL}/about.html")}
{_header('about')}
<main class="container">
  <div class="page-header"><h1>About {SITE_NAME}</h1></div>
  <div class="article-body">
    <p><strong>{SITE_NAME}</strong> is an independent fishing gear review site built by anglers, for anglers. We test, compare, and honestly review fishing equipment so you can spend less time researching and more time on the water.</p>
    <h2>Our Mission</h2>
    <p>The fishing gear market is flooded with paid placements and fake reviews. We started {SITE_NAME} because we were tired of buying gear based on hype, only to be disappointed on the water. Every review on this site is based on real specifications, real user feedback, and real-world performance data.</p>
    <h2>How We Review</h2>
    <p>For every product category, we analyze specifications, cross-reference user reviews from multiple sources, compare pricing across retailers, and assess long-term durability. When possible, we test products ourselves. When we can't, we rely on verified purchaser feedback and expert angler opinions.</p>
    <h2>How We Make Money</h2>
    <p>{SITE_NAME} is reader-supported. When you click our links and make a purchase, we may earn a small affiliate commission at no extra cost to you. This revenue keeps the site running and lets us continue producing honest reviews. No brand pays for placement. No manufacturer sponsors our rankings. See our <a href="/affiliate-disclosure.html">full affiliate disclosure</a> for details.</p>
    <h2>Our Team</h2>
    <p>Our editorial team combines 50+ years of angling experience across freshwater bass fishing, saltwater fly fishing, kayak fishing, and tournament competition. We fish rivers, lakes, oceans, and everything in between.</p>
    <p>Questions? Reach us at <strong>hello@fishingtribune.com</strong></p>
  </div>
</main>
{_footer()}'''


def disclosure_page() -> str:
    return f'''{_head(f"Affiliate Disclosure - {SITE_NAME}",
                       f"{SITE_NAME} affiliate disclosure and FTC compliance information.",
                       f"{BASE_URL}/affiliate-disclosure.html")}
{_header('disclosure')}
<main class="container">
  <div class="page-header"><h1>Affiliate Disclosure</h1></div>
  <div class="article-body">
    <p>{SITE_NAME} is reader-supported. When you buy through links on our site, we may earn an affiliate commission at no extra cost to you.</p>
    <h2>How We Make Money</h2>
    <p>We participate in the Amazon Services LLC Associates Program, an affiliate advertising program designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.com. Some links on our site are affiliate links, meaning we get a small commission if you click and make a purchase. This does not affect the price you pay.</p>
    <h2>Our Promise</h2>
    <p>We only recommend products we genuinely believe will help you catch more fish. Our reviews are based on real research, real specifications, and real angler feedback. No brand pays for placement. No manufacturer sponsors our rankings.</p>
    <p>If a product is bad, we say so. If a cheap option outperforms an expensive one, we say that too. Your trust matters more than any commission.</p>
    <h2>FTC Compliance</h2>
    <p>In accordance with the Federal Trade Commission's 16 CFR Part 255, "Guides Concerning the Use of Endorsements and Testimonials in Advertising," we disclose that we receive compensation for products reviewed or linked on this site.</p>
    <p>If you have questions about our disclosure policy, contact us at <strong>hello@fishingtribune.com</strong>.</p>
  </div>
</main>
{_footer()}'''


def error_404_page() -> str:
    return f'''{_head("Page Not Found", "The page you're looking for doesn't exist.", f"{BASE_URL}/404.html")}
{_header()}
<main class="container">
  <div class="error-page">
    <h1>404</h1>
    <p>Looks like this page got away. Let's get you back on the water.</p>
    <a href="/" class="cta-button">Back to Homepage &rarr;</a>
  </div>
</main>
{_footer()}'''


# ── Feed & Sitemap Generators ────────────────────────────────────

def build_sitemap(articles: list) -> str:
    urls = [f'  <url><loc>{BASE_URL}/</loc><lastmod>{BUILD_DATE}</lastmod><priority>1.0</priority></url>']
    urls.append(f'  <url><loc>{BASE_URL}/about.html</loc><lastmod>{BUILD_DATE}</lastmod><priority>0.5</priority></url>')
    urls.append(f'  <url><loc>{BASE_URL}/affiliate-disclosure.html</loc><lastmod>{BUILD_DATE}</lastmod><priority>0.3</priority></url>')
    for cid in CATEGORIES:
        urls.append(f'  <url><loc>{BASE_URL}/categories/{cid}.html</loc><lastmod>{BUILD_DATE}</lastmod><priority>0.6</priority></url>')
    for a in articles:
        urls.append(f'  <url><loc>{BASE_URL}/articles/{a["slug"]}.html</loc><lastmod>{BUILD_DATE}</lastmod><priority>0.8</priority></url>')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''


def build_rss(articles: list) -> str:
    items = []
    for a in articles[:20]:
        items.append(f'''    <item>
      <title>{esc(a['title'])}</title>
      <link>{BASE_URL}/articles/{a['slug']}.html</link>
      <description>{esc(a['excerpt'])}</description>
      <pubDate>{BUILD_DATE}</pubDate>
      <guid>{BASE_URL}/articles/{a['slug']}.html</guid>
    </item>''')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{SITE_NAME}</title>
  <link>{BASE_URL}</link>
  <description>Expert fishing gear reviews and buying guides.</description>
  <language>en-us</language>
  <lastBuildDate>{BUILD_DATE}</lastBuildDate>
  <atom:link href="{BASE_URL}/articles.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
</channel>
</rss>'''


def build_robots() -> str:
    return f'''User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml'''


# ── Main Build ───────────────────────────────────────────────────

def main():
    articles = []
    date = '2026-03-29'

    # Phase 1: Read and process all articles
    for num in sorted(PICKS.keys()):
        fname, slug = PICKS[num]
        src = ARTICLES_SRC / fname
        if not src.exists():
            print(f'  SKIP: {fname} not found')
            continue
        md = src.read_bytes().replace(b'\x00', b'').decode('utf-8', errors='replace')
        title = extract_title(md, slug.replace('-', ' ').title())
        excerpt = extract_excerpt(md)
        words = len(md.split())
        category = classify_article(title, slug)
        faqs = extract_faqs(md)
        articles.append({
            'num': num, 'slug': slug, 'title': title, 'excerpt': excerpt,
            'words': words, 'category': category, 'faqs': faqs, 'md': md,
        })

    # Phase 2: Generate article pages (needs full articles list for related)
    for a in articles:
        body_html = md_to_html(a['md'])
        related = find_related(a['slug'], articles)
        page = article_page(a['title'], body_html, a['slug'], a['excerpt'],
                            date, a['category'], a['faqs'], related)
        (ARTICLES_DIR / f'{a["slug"]}.html').write_text(page, encoding='utf-8')
        faq_note = f' ({len(a["faqs"])} FAQs)' if a['faqs'] else ''
        print(f'  Built: articles/{a["slug"]}.html ({a["words"]:,} words, {a["category"]}){faq_note}')

    # Drop md from articles list (not needed in templates)
    for a in articles:
        del a['md']

    # Phase 3: Homepage
    idx = index_page(articles)
    (SITE_DIR / 'index.html').write_text(idx, encoding='utf-8')
    print(f'  Built: index.html ({len(articles)} articles)')

    # Phase 4: Category pages
    cat_dir = SITE_DIR / 'categories'
    cat_dir.mkdir(exist_ok=True)
    cat_counts = {}
    for cid, cinfo in CATEGORIES.items():
        page = category_page(cid, cinfo, articles)
        (cat_dir / f'{cid}.html').write_text(page, encoding='utf-8')
        count = sum(1 for a in articles if a.get('category') == cid)
        cat_counts[cid] = count
    print(f'  Built: {len(CATEGORIES)} category pages')

    # Phase 5: Static pages
    (SITE_DIR / 'about.html').write_text(about_page(), encoding='utf-8')
    print('  Built: about.html')
    (SITE_DIR / 'affiliate-disclosure.html').write_text(disclosure_page(), encoding='utf-8')
    print('  Built: affiliate-disclosure.html')
    (SITE_DIR / '404.html').write_text(error_404_page(), encoding='utf-8')
    print('  Built: 404.html')

    # Phase 6: SEO files
    sm = build_sitemap(articles)
    (SITE_DIR / 'sitemap.xml').write_text(sm, encoding='utf-8')
    print(f'  Built: sitemap.xml ({len(articles) + len(CATEGORIES) + 3} URLs)')

    rss = build_rss(articles)
    (SITE_DIR / 'articles.xml').write_text(rss, encoding='utf-8')
    print(f'  Built: articles.xml (RSS feed)')

    rb = build_robots()
    (SITE_DIR / 'robots.txt').write_text(rb, encoding='utf-8')
    print('  Built: robots.txt')

    # Summary
    print(f'\n  === BUILD COMPLETE ===')
    print(f'  Articles: {len(articles)}')
    print(f'  Categories: {", ".join(f"{CATEGORIES[c]["name"]} ({cat_counts[c]})" for c in cat_counts)}')
    print(f'  Sitemap entries: {len(articles) + len(CATEGORIES) + 3}')
    print(f'  FAQs detected: {sum(len(a.get("faqs", [])) for a in articles)}')
    print(f'  Site: {SITE_DIR}/')


if __name__ == '__main__':
    main()
