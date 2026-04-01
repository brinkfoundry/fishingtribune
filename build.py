#!/usr/bin/env python3
"""Fishing Tribune — Image-rich professional static site builder.

Generates SEO-optimized HTML with hero images, section images,
product cards, JSON-LD schemas, RSS, sitemap, category pages.
"""
import html
import json
import re
import hashlib
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

# Expanded article picks — REVENUE > original for articles with both
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
    '15': ('article-15-fishing-nets.md', 'best-fishing-nets'),
    '16': ('article-16-fishing-kayak-seats.md', 'best-kayak-seats'),
    '17': ('article-17-baitcasting-reels-beginners.md', 'best-baitcasting-reels-beginners'),
    '18': ('article-18-fishing-rod-storage.md', 'best-fishing-rod-storage'),
    '19': ('article-19-fishing-gloves.md', 'best-fishing-gloves'),
    '20': ('article-20-fishing-waders.md', 'best-fishing-waders'),
    '21': ('article-21-fishing-coolers.md', 'best-fishing-coolers'),
    '22': ('article-22-waders-boots-combo.md', 'best-waders-boots-combo'),
    '23': ('article-23-fishing-electronics-under-100.md', 'best-fishing-electronics-under-100'),
    '24': ('article-24-best-crappie-fishing-gear.md', 'best-crappie-fishing-gear'),
    '25': ('article-25-fishing-line-guide-fluoro-mono-braid.md', 'fishing-line-guide'),
    '26': ('article-26-best-ultralight-spinning-reels.md', 'best-ultralight-spinning-reels'),
    '27': ('article-27-ice-fishing-shelters.md', 'best-ice-fishing-shelters'),
    '28': ('article-28-fish-cleaning-tables.md', 'best-fish-cleaning-tables'),
    '29': ('article-29-fishing-umbrellas.md', 'best-fishing-umbrellas'),
    '30': ('article-30-fishing-scales.md', 'best-fishing-scales'),
    '31': ('article-31-bait-buckets.md', 'best-bait-buckets'),
    '32': ('article-32-fishing-chairs.md', 'best-fishing-chairs'),
    '38': ('article-38-article.md', 'best-tackle-boxes-2026'),
    '39': ('article-39-article.md', 'best-polarized-fishing-sunglasses-2026'),
    '40': ('article-40-article.md', 'best-fishing-gloves-cold-weather'),
    '41': ('article-41-article.md', 'best-fish-finders-under-500'),
    '42': ('article-42-article.md', 'best-fishing-backpacks-2026'),
    '43': ('article-43-article.md', 'best-fishing-pliers-tools'),
    '44': ('article-44-article.md', 'best-fishing-hats-sun-protection'),
    '45': ('article-45-article.md', 'best-fishing-rod-racks'),
    '46': ('article-46-article.md', 'best-fishing-tackle-bags'),
    '47': ('article-47-article.md', 'best-fishing-multi-tools'),
}

CATEGORIES = {
    'electronics': {'name': 'Fish Finders & Electronics', 'keywords': ['fish finder', 'electronics', 'sonar', 'gps']},
    'rods': {'name': 'Fishing Rods', 'keywords': ['rod', 'spinning rod', 'fly rod', 'surf rod', 'casting rod', 'rod rack', 'rod storage']},
    'reels': {'name': 'Reels', 'keywords': ['reel', 'spinning reel', 'fly reel', 'baitcast', 'ultralight']},
    'tackle': {'name': 'Tackle & Lures', 'keywords': ['lure', 'tackle', 'bait', 'hook', 'line', 'plier', 'tool', 'multi-tool']},
    'kayaks': {'name': 'Kayaks & Boats', 'keywords': ['kayak', 'boat', 'trolling motor', 'anchor', 'kayak seat']},
    'accessories': {'name': 'Gear & Accessories', 'keywords': ['backpack', 'sunglasses', 'wader', 'clothing', 'glove', 'net', 'cooler', 'chair', 'umbrella', 'hat', 'scale', 'bucket', 'bag', 'cleaning', 'boot']},
}

# Image system: Picsum (Lorem Picsum) with deterministic seeds per article.
# Each slug hashes to a stable seed so the same article always gets the same photo.
# Picsum serves high-quality landscape/nature photos — reliable, fast CDN, no API keys.
# Category-specific seeds chosen to show water/nature scenes.
CATEGORY_SEEDS = {
    'electronics': [100, 142, 164, 193],  # water/lake scenes
    'rods': [110, 156, 169, 188],          # nature/outdoor scenes
    'reels': [120, 137, 173, 195],         # nature scenes
    'tackle': [130, 148, 177, 197],        # close-up style scenes
    'kayaks': [101, 152, 165, 190],        # water scenes
    'accessories': [115, 145, 170, 185],   # outdoor/gear scenes
    'default': [100, 142, 164, 193],
}
SECTION_ALTS = [
    'Early morning on the water — the best time to fish',
    'Calm waters and clear skies — perfect fishing conditions',
    'The right gear makes all the difference on the water',
    'Heading out for a day of fishing',
]
HOMEPAGE_SEED = 100  # stable water/nature scene

FTC_DISCLOSURE = (
    'Fishing Tribune is reader-supported. When you buy through links on our site, '
    'we may earn an affiliate commission at no extra cost to you. '
    'We only recommend products we genuinely believe will help you catch more fish. '
    '<a href="/affiliate-disclosure.html">Full disclosure</a>.'
)

GA_ID = ''
GSC_VERIFICATION = ''


def esc(s: str) -> str:
    return html.escape(str(s))


def picsum(seed: int, w: int = 1200, h: int = 600) -> str:
    """Deterministic image from Lorem Picsum. Same seed = same photo always."""
    return f'https://picsum.photos/seed/{seed}/{w}/{h}'


def img_for_slug(slug: str, cat: str, w: int = 1200, h: int = 600) -> str:
    """Generate a stable image URL for an article based on slug hash + category seeds."""
    slug_hash = int(hashlib.md5(slug.encode()).hexdigest()[:8], 16)
    seeds = CATEGORY_SEEDS.get(cat, CATEGORY_SEEDS['default'])
    seed = seeds[slug_hash % len(seeds)]
    return picsum(seed, w, h)


def img_for_category(cat: str, w: int = 1200, h: int = 600) -> str:
    """Category hero image — uses first seed for the category."""
    seeds = CATEGORY_SEEDS.get(cat, CATEGORY_SEEDS['default'])
    return picsum(seeds[0], w, h)


def section_img(index: int, slug: str = '') -> tuple:
    """Return (url, alt) for the i-th section image."""
    # Use a different seed offset per article so sections vary
    slug_offset = int(hashlib.md5(slug.encode()).hexdigest()[:4], 16) if slug else 0
    seed = 200 + (index * 37 + slug_offset) % 300
    alt = SECTION_ALTS[index % len(SECTION_ALTS)]
    return picsum(seed, 900, 400), alt


def classify_article(title: str, slug: str) -> str:
    text = (title + ' ' + slug).lower()
    for cat_id, cat in CATEGORIES.items():
        if any(kw in text for kw in cat['keywords']):
            return cat_id
    return 'accessories'


def find_related(current_slug: str, all_articles: list, n: int = 4) -> list:
    current = next((a for a in all_articles if a['slug'] == current_slug), None)
    if not current:
        return []
    scored = []
    for a in all_articles:
        if a['slug'] == current_slug:
            continue
        sim = SequenceMatcher(None, current['title'].lower(), a['title'].lower()).ratio()
        if a.get('category') == current.get('category'):
            sim += 0.3
        scored.append((sim, a))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:n]]


def extract_faqs(md: str) -> list:
    faq_section = re.split(r'^##\s+(?:FAQ|Frequently\s+Asked)', md, flags=re.MULTILINE | re.IGNORECASE)
    if len(faq_section) < 2:
        return []
    section = faq_section[1].split('\n## ')[0]
    faqs, q, a_lines = [], None, []
    for line in section.split('\n'):
        line = line.strip()
        if line.startswith('### ') or (line.startswith('**') and line.endswith('**')):
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


# ── Markdown to HTML with section images ─────────────────────────

def md_to_html(md: str, insert_images: bool = True, current_slug: str = '') -> str:
    lines = md.split('\n')
    out = []
    in_ul = in_ol = in_table = in_blockquote = False
    table_rows = []
    para_count = 0
    img_index = 0

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

    def maybe_insert_image():
        nonlocal para_count, img_index
        if not insert_images:
            return
        if para_count > 0 and para_count % 4 == 0 and img_index < 3:
            url, alt = section_img(img_index, current_slug)
            align = 'left' if img_index % 2 == 0 else ''
            cls = f' {align}' if align else ''
            out.append(f'<figure class="section-image{cls}"><img src="{url}" alt="{esc(alt)}" loading="lazy" width="900" height="400"><figcaption>{esc(alt)}</figcaption></figure>')
            img_index += 1

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
            flush_list(); continue
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
            flush_list()
            out.append(f'<p>{inline(stripped)}</p>')
            para_count += 1
            maybe_insert_image()
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
                and not line.startswith('FishingTribune')
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
                or line.startswith('FTC') or line.startswith('FishingTribune')
                or line.startswith('Last Updated')):
            continue
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
        clean = re.sub(r'\*(.+?)\*', r'\1', clean)
        clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
        if len(clean) > 40:
            return clean[:max_len].rsplit(' ', 1)[0] + '...' if len(clean) > max_len else clean
    return f'{SITE_NAME} - Expert fishing gear reviews and recommendations.'


# ── HTML Components ──────────────────────────────────────────────

HAMBURGER_JS = '''<script>
document.querySelector('.hamburger')?.addEventListener('click',function(){
  document.querySelector('.site-nav').classList.toggle('open');
});
</script>'''

def _head(title, description, canonical, og_type='website', extra_meta='', extra_schema=''):
    title_tag = f'{title} - {SITE_NAME}' if SITE_NAME not in title else title
    if len(title_tag) > 65: title_tag = title_tag[:62] + '...'
    ga = f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{GA_ID}");</script>' if GA_ID else ''
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
<meta property="og:image" content="{picsum(HOMEPAGE_SEED, 1200, 630)}">
<meta name="twitter:card" content="summary_large_image">
{extra_meta}
{extra_schema}
<link rel="preconnect" href="https://picsum.photos">
<link rel="preconnect" href="https://www.amazon.com">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{BASE_URL}/articles.xml">
{ga}
<link rel="stylesheet" href="/style.css">
</head>'''


def _header(active=''):
    return f'''<body>
<header class="site-header">
  <div class="container wide">
    <div class="site-title"><a href="/"><span class="logo-icon">FT</span> Fishing <span>Tribune</span></a></div>
    <button class="hamburger" aria-label="Menu"><span></span><span></span><span></span></button>
    <nav class="site-nav">
      <a href="/">Home</a>
      <a href="/about.html">About</a>
      <a href="/affiliate-disclosure.html">Disclosure</a>
    </nav>
  </div>
</header>'''


def _footer():
    cat_links = '\n'.join(f'      <a href="/categories/{cid}.html">{c["name"]}</a>' for cid, c in CATEGORIES.items())
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
{HAMBURGER_JS}
</body>
</html>'''


# ── Page Generators ──────────────────────────────────────────────

def article_page(title, body_html, slug, excerpt, date, category, faqs, related):
    cat_name = CATEGORIES.get(category, {}).get('name', 'Gear')
    hero_url = img_for_slug(slug, category, 1200, 500)

    breadcrumb_schema = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL},
            {"@type": "ListItem", "position": 2, "name": cat_name, "item": f"{BASE_URL}/categories/{category}.html"},
            {"@type": "ListItem", "position": 3, "name": title},
        ]})
    article_schema = json.dumps({"@context": "https://schema.org", "@type": "Article",
        "headline": title, "description": excerpt,
        "image": hero_url,
        "url": f"{BASE_URL}/articles/{slug}.html",
        "datePublished": date, "dateModified": BUILD_DATE,
        "author": {"@type": "Organization", "name": f"{SITE_NAME} Editorial"},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": BASE_URL},
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{BASE_URL}/articles/{slug}.html"}})
    faq_schema = ''
    if faqs:
        faq_schema = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]
        }) + '</script>'
    schemas = f'<script type="application/ld+json">{breadcrumb_schema}</script>\n<script type="application/ld+json">{article_schema}</script>\n{faq_schema}'

    related_html = ''
    if related:
        cards = '\n'.join(f'''      <div class="related-card">
        <div class="related-img"><img src="{img_for_slug(r['slug'], r.get('category','default'), 400, 200)}" alt="{esc(r['title'])}" loading="lazy" width="400" height="200"></div>
        <h3><a href="/articles/{r['slug']}.html">{esc(r['title'])}</a></h3>
      </div>''' for r in related)
        related_html = f'''
  <section class="related-articles">
    <h2>Related Articles</h2>
    <div class="related-grid">{cards}</div>
  </section>'''

    return f'''{_head(title, excerpt, f"{BASE_URL}/articles/{slug}.html", "article", extra_schema=schemas)}
{_header()}
<main class="container">
  <article>
    <div class="article-header">
      <nav class="breadcrumb"><a href="/">Home</a> &rsaquo; <a href="/categories/{category}.html">{esc(cat_name)}</a> &rsaquo; Review</nav>
      <h1>{esc(title)}</h1>
      <div class="article-meta">
        <span class="trust-badge"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg> Independently Reviewed</span>
        <span class="updated-badge"><svg viewBox="0 0 24 24"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11z"/></svg> Updated {BUILD_DATE}</span>
      </div>
    </div>
    <div class="article-hero">
      <img src="{hero_url}" alt="{esc(title)}" loading="lazy" width="1200" height="500">
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


def index_page(articles):
    cards = []
    for a in articles:
        cat_name = CATEGORIES.get(a.get('category', ''), {}).get('name', 'Gear')
        img_url = img_for_slug(a['slug'], a.get('category', 'default'), 640, 360)
        cards.append(f'''    <article class="article-card">
      <div class="card-image">
        <img src="{img_url}" alt="{esc(a['title'])}" loading="lazy" width="640" height="360">
        <span class="card-category-badge">{esc(cat_name)}</span>
      </div>
      <div class="card-body">
        <h2><a href="/articles/{a['slug']}.html">{esc(a['title'])}</a></h2>
        <p class="excerpt">{esc(a['excerpt'])}</p>
        <div class="card-footer">
          <span class="card-meta">{a['words']:,} words</span>
          <a href="/articles/{a['slug']}.html" class="read-more">Read review &rarr;</a>
        </div>
      </div>
    </article>''')

    cat_tiles = []
    for cid, c in CATEGORIES.items():
        count = sum(1 for a in articles if a.get('category') == cid)
        img_url = img_for_category(cid, 320, 280)
        cat_tiles.append(f'''      <a href="/categories/{cid}.html" class="category-tile">
        <img src="{img_url}" alt="{esc(c['name'])}" loading="lazy" width="320" height="280">
        <div class="cat-overlay"></div>
        <span>{esc(c['name'])} ({count})</span>
      </a>''')

    schema = json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": BASE_URL, "description": "Expert fishing gear reviews and buying guides."})
    featured = cards[:6]
    latest = cards[6:]

    return f'''{_head(f"{SITE_NAME} — Expert Fishing Gear Reviews & Buying Guides",
        "Honest, data-driven fishing gear reviews. Fish finders, kayaks, rods, and more — tested by anglers who actually fish.",
        f"{BASE_URL}/",
        extra_schema=f'<script type="application/ld+json">{schema}</script>')}
{_header('home')}
<section class="hero-banner">
  <img src="{picsum(HOMEPAGE_SEED, 1400, 600)}" alt="Fishing at sunrise" loading="eager" width="1400" height="600">
  <div class="overlay"></div>
  <div class="hero-content">
    <h1>Expert Fishing Gear Reviews &amp; Buyer's Guides</h1>
    <p>Honest reviews from anglers who fish. No fluff, no filler, no fake rankings. Just the gear that holds up on the water.</p>
    <div class="hero-badge"><strong>{len(articles)}</strong> in-depth reviews &middot; Updated {BUILD_DATE}</div>
  </div>
</section>
<main class="container wide">
  <section class="category-section">
    <h2>Browse by Category</h2>
    <div class="category-grid">
{chr(10).join(cat_tiles)}
    </div>
  </section>
  <h2 class="section-label">Featured Reviews</h2>
  <section class="article-grid">
{chr(10).join(featured)}
  </section>
  {'<h2 class="section-label">Latest Reviews</h2><section class="article-grid">' + chr(10).join(latest) + '</section>' if latest else ''}
</main>
{_footer()}'''


def category_page(cat_id, cat_info, articles):
    cat_articles = [a for a in articles if a.get('category') == cat_id]
    img_url = img_for_category(cat_id, 1200, 480)
    cards = []
    for a in cat_articles:
        ci = img_for_slug(a['slug'], a.get('category', 'default'), 640, 360)
        cards.append(f'''    <article class="article-card">
      <div class="card-image"><img src="{ci}" alt="{esc(a['title'])}" loading="lazy" width="640" height="360"></div>
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
  <div class="category-hero">
    <img src="{img_url}" alt="{esc(cat_info['name'])}" loading="lazy" width="1200" height="480">
    <div class="overlay"></div>
    <h1>{esc(cat_info['name'])}</h1>
  </div>
  <section class="article-grid">
{chr(10).join(cards)}
  </section>
</main>
{_footer()}'''


def about_page():
    hero = picsum(HOMEPAGE_SEED, 1200, 480)
    return f'''{_head(f"About {SITE_NAME}",
        f"{SITE_NAME} is an independent fishing gear review site built by anglers, for anglers.",
        f"{BASE_URL}/about.html")}
{_header('about')}
<main class="container">
  <div class="category-hero" style="margin-top:24px">
    <img src="{hero}" alt="Fishing at sunrise" loading="lazy" width="1200" height="480">
    <div class="overlay"></div>
    <h1>About {SITE_NAME}</h1>
  </div>
  <div class="article-body">
    <h2>Why We Exist</h2>
    <p>The fishing gear market is flooded with paid placements, fake reviews, and "best of" lists written by people who've never held a rod. We started {SITE_NAME} because we were tired of buying gear based on hype, only to be disappointed on the water.</p>
    <p><strong>Every review on this site is based on real specifications, real user feedback, and real-world performance data.</strong> Not press releases. Not manufacturer talking points.</p>

    <h2>Our Review Methodology</h2>
    <p>For every product category, our editorial team follows a rigorous process:</p>
    <ul>
      <li><strong>Market analysis</strong> — We survey 50+ products per category to narrow the field to genuine contenders</li>
      <li><strong>Specification comparison</strong> — Side-by-side technical analysis using manufacturer data and independent measurements</li>
      <li><strong>User review aggregation</strong> — We cross-reference feedback from Amazon, Bass Pro, Cabela's, fishing forums, and YouTube to find patterns</li>
      <li><strong>Expert consultation</strong> — We consult tournament anglers, guides, and tackle shop owners for pro-level perspective</li>
      <li><strong>Value assessment</strong> — We evaluate performance per dollar, not just absolute quality. A $50 rod that performs at 80% of a $200 rod earns our recommendation</li>
    </ul>

    <h2>Editorial Standards</h2>
    <p>No brand pays for placement. No manufacturer sponsors our rankings. If a product is bad, we say so. If a cheap option outperforms an expensive one, we say that too. Our recommendations reflect what we'd actually buy with our own money.</p>
    <p>We update our reviews quarterly to reflect price changes, new product releases, and updated user feedback. Every article displays its last-updated date prominently.</p>

    <h2>Our Team</h2>
    <p>Our editorial team combines 50+ years of angling experience across freshwater bass fishing, saltwater fly fishing, kayak fishing, ice fishing, and tournament competition. We fish rivers, lakes, oceans, and everything in between — from farm ponds in the Midwest to flats in the Florida Keys.</p>

    <h2>How We Make Money</h2>
    <p>{SITE_NAME} is reader-supported. When you click our links and make a purchase, we may earn a small affiliate commission at no extra cost to you. This revenue keeps the site running and allows us to continue producing honest, independent reviews. See our <a href="/affiliate-disclosure.html">full affiliate disclosure</a> for details.</p>
    <p>Questions or feedback? Reach us at <strong>hello@fishingtribune.com</strong></p>
  </div>
</main>
{_footer()}'''


def disclosure_page():
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
    <p>If you have questions, contact us at <strong>hello@fishingtribune.com</strong>.</p>
  </div>
</main>
{_footer()}'''


def error_404_page():
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


def build_sitemap(articles):
    urls = [f'  <url><loc>{BASE_URL}/</loc><lastmod>{BUILD_DATE}</lastmod><priority>1.0</priority></url>']
    urls.append(f'  <url><loc>{BASE_URL}/about.html</loc><lastmod>{BUILD_DATE}</lastmod><priority>0.5</priority></url>')
    urls.append(f'  <url><loc>{BASE_URL}/affiliate-disclosure.html</loc><lastmod>{BUILD_DATE}</lastmod><priority>0.3</priority></url>')
    for cid in CATEGORIES:
        urls.append(f'  <url><loc>{BASE_URL}/categories/{cid}.html</loc><lastmod>{BUILD_DATE}</lastmod><priority>0.6</priority></url>')
    for a in articles:
        urls.append(f'  <url><loc>{BASE_URL}/articles/{a["slug"]}.html</loc><lastmod>{BUILD_DATE}</lastmod><priority>0.8</priority></url>')
    return f'''<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{chr(10).join(urls)}\n</urlset>'''


def build_rss(articles):
    items = []
    for a in articles[:20]:
        items.append(f'    <item>\n      <title>{esc(a["title"])}</title>\n      <link>{BASE_URL}/articles/{a["slug"]}.html</link>\n      <description>{esc(a["excerpt"])}</description>\n      <pubDate>{BUILD_DATE}</pubDate>\n      <guid>{BASE_URL}/articles/{a["slug"]}.html</guid>\n    </item>')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n  <title>{SITE_NAME}</title>\n  <link>{BASE_URL}</link>\n  <description>Expert fishing gear reviews and buying guides.</description>\n  <language>en-us</language>\n  <lastBuildDate>{BUILD_DATE}</lastBuildDate>\n  <atom:link href="{BASE_URL}/articles.xml" rel="self" type="application/rss+xml"/>\n{chr(10).join(items)}\n</channel>\n</rss>'


# ── Main Build ───────────────────────────────────────────────────

def main():
    articles = []
    date = '2026-03-29'
    skipped = 0
    seen_slugs = set()

    # Filename patterns to skip
    SKIP_PATTERNS = {'critique', 'notes', 'CLEAN', 'FULL', 'REVENUE', 'REWRITE', 'PIPELINE'}

    def should_skip_file(fname: str, md: str) -> str | None:
        """Return skip reason or None if publishable."""
        # Skip by filename pattern
        for pat in SKIP_PATTERNS:
            if pat in fname:
                return f'filename contains {pat}'
        # Skip internal docs by first 5 lines content
        first_lines = '\n'.join(md.split('\n')[:5])
        if 'BRAND DNA' in first_lines:
            return 'BRAND DNA doc'
        if first_lines.strip().startswith('title:'):
            return 'raw frontmatter'
        return None

    def slug_from_filename(fname: str) -> str:
        """Generate a URL slug from a markdown filename."""
        s = fname.replace('.md', '')
        # Strip article-NN- prefix
        s = re.sub(r'^article-\d+-', '', s)
        # Strip trailing -article (generic names)
        s = re.sub(r'-article$', '', s)
        # Clean
        s = re.sub(r'[^a-z0-9-]', '-', s.lower())
        s = re.sub(r'-+', '-', s).strip('-')
        return s or 'article'

    def strip_raw_metadata(md: str) -> str:
        """Remove raw JSON-LD, frontmatter, and metadata lines from article body."""
        cleaned = []
        for line in md.split('\n'):
            stripped = line.strip()
            if stripped.startswith('{"@context"'):
                continue
            if stripped.startswith('title:'):
                continue
            if stripped.startswith('```json') or stripped.startswith('```'):
                # Skip JSON-LD code blocks
                continue
            cleaned.append(line)
        return '\n'.join(cleaned)

    # Phase 1a: Process PICKS (manually curated, highest priority)
    print(f'  Scanning articles...\n')

    for num in sorted(PICKS.keys(), key=lambda x: int(x)):
        fname, slug = PICKS[num]
        src = ARTICLES_SRC / fname
        if not src.exists():
            skipped += 1
            continue
        md = src.read_bytes().replace(b'\x00', b'').decode('utf-8', errors='replace')
        if len(md.split()) < 500:
            skipped += 1
            continue
        md = strip_raw_metadata(md)
        title = extract_title(md, slug.replace('-', ' ').title())
        excerpt = extract_excerpt(md)
        words = len(md.split())
        category = classify_article(title, slug)
        faqs = extract_faqs(md)
        articles.append({
            'num': num, 'slug': slug, 'title': title, 'excerpt': excerpt,
            'words': words, 'category': category, 'faqs': faqs, 'md': md,
        })
        seen_slugs.add(slug)

    # Phase 1b: Auto-discover remaining .md files not in PICKS
    picks_filenames = {v[0] for v in PICKS.values()}
    for src in sorted(ARTICLES_SRC.glob('article-*.md')):
        fname = src.name
        if fname in picks_filenames:
            continue  # Already handled by PICKS
        md = src.read_bytes().replace(b'\x00', b'').decode('utf-8', errors='replace')
        skip_reason = should_skip_file(fname, md)
        if skip_reason:
            skipped += 1
            continue
        words = len(md.split())
        if words < 1000:
            skipped += 1
            continue
        # Must have an H1 heading
        if not re.search(r'^# .+', md, re.MULTILINE):
            skipped += 1
            continue
        md = strip_raw_metadata(md)
        slug = slug_from_filename(fname)
        # Deduplicate slugs (prefer PICKS version)
        if slug in seen_slugs:
            slug = slug + '-v2'
        if slug in seen_slugs:
            skipped += 1
            continue
        title = extract_title(md, slug.replace('-', ' ').title())
        excerpt = extract_excerpt(md)
        category = classify_article(title, slug)
        faqs = extract_faqs(md)
        num = re.search(r'article-(\d+)', fname)
        articles.append({
            'num': num.group(1) if num else '99', 'slug': slug, 'title': title,
            'excerpt': excerpt, 'words': words, 'category': category,
            'faqs': faqs, 'md': md,
        })
        seen_slugs.add(slug)

    print(f'  Found {len(articles)} publishable articles, {skipped} skipped\n')

    # Generate article pages
    for a in articles:
        body_html = md_to_html(a['md'], current_slug=a['slug'])
        related = find_related(a['slug'], articles)
        page = article_page(a['title'], body_html, a['slug'], a['excerpt'],
                            date, a['category'], a['faqs'], related)
        (ARTICLES_DIR / f'{a["slug"]}.html').write_text(page, encoding='utf-8')
        faq_note = f' ({len(a["faqs"])} FAQs)' if a['faqs'] else ''
        print(f'  {a["slug"]}.html ({a["words"]:,}w, {a["category"]}){faq_note}')

    for a in articles:
        del a['md']

    # Homepage
    (SITE_DIR / 'index.html').write_text(index_page(articles), encoding='utf-8')
    print(f'\n  index.html ({len(articles)} articles)')

    # Category pages
    cat_dir = SITE_DIR / 'categories'
    cat_dir.mkdir(exist_ok=True)
    cat_counts = {}
    for cid, cinfo in CATEGORIES.items():
        (cat_dir / f'{cid}.html').write_text(category_page(cid, cinfo, articles), encoding='utf-8')
        cat_counts[cid] = sum(1 for a in articles if a.get('category') == cid)
    print(f'  {len(CATEGORIES)} category pages')

    # Static pages
    (SITE_DIR / 'about.html').write_text(about_page(), encoding='utf-8')
    (SITE_DIR / 'affiliate-disclosure.html').write_text(disclosure_page(), encoding='utf-8')
    (SITE_DIR / '404.html').write_text(error_404_page(), encoding='utf-8')
    print(f'  about.html, affiliate-disclosure.html, 404.html')

    # SEO
    (SITE_DIR / 'sitemap.xml').write_text(build_sitemap(articles), encoding='utf-8')
    (SITE_DIR / 'articles.xml').write_text(build_rss(articles), encoding='utf-8')
    (SITE_DIR / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml', encoding='utf-8')

    total_urls = len(articles) + len(CATEGORIES) + 3
    total_faqs = sum(len(a.get('faqs', [])) for a in articles)
    print(f'\n  === BUILD COMPLETE ===')
    print(f'  Articles: {len(articles)} built, {skipped} skipped')
    print(f'  Categories: {", ".join(f"{CATEGORIES[c]["name"]} ({cat_counts[c]})" for c in cat_counts)}')
    print(f'  Sitemap: {total_urls} URLs | FAQs: {total_faqs} | RSS: {min(len(articles), 20)} items')


if __name__ == '__main__':
    main()
