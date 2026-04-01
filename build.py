#!/usr/bin/env python3
"""Fishing Tribune — professional static site builder with product cards and hero images.

Generates SEO-optimized HTML with category-matched Unsplash heroes,
Wirecutter-style product cards from comparison tables, JSON-LD schemas,
RSS, sitemap, category pages.
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

# ── Article picks (manually curated, highest priority) ───────────
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

# ── Verified Unsplash hero photos (all 200 OK) ──────────────────
HERO_PHOTOS = {
    'electronics': 'photo-1529230117010-b6c436154f25',
    'rods': 'photo-1541742425281-c1d3fc8aff96',
    'reels': 'photo-1532015917327-c7c46aa1d930',
    'tackle': 'photo-1551131618-3f0a5cf594b4',
    'kayaks': 'photo-1493787039806-2edcbe808750',
    'accessories': 'photo-1545450660-3378a7f3a364',
    'default': 'photo-1601226041388-8bbabdd6e37e',
    'homepage': 'photo-1610741620547-1191d693e43d',
}

GA_ID = ''
GSC_VERIFICATION = ''
SKIP_PATTERNS = {'critique', 'notes', 'CLEAN', 'FULL', 'REVENUE', 'REWRITE', 'PIPELINE'}


def esc(s: str) -> str:
    return html.escape(str(s))


def unsplash(photo_id: str, w: int = 1200, h: int = 500) -> str:
    return f'https://images.unsplash.com/{photo_id}?w={w}&h={h}&fit=crop&auto=format&q=75'


def hero_url(cat: str, w: int = 1200, h: int = 500) -> str:
    return unsplash(HERO_PHOTOS.get(cat, HERO_PHOTOS['default']), w, h)


def read_time(words: int) -> str:
    return f'~{max(1, round(words / 250))} min read'


def ftc_disclosure(root='./'):
    return (
        'Fishing Tribune is reader-supported. When you buy through links on our site, '
        'we may earn an affiliate commission at no extra cost to you. '
        'We only recommend products we genuinely believe will help you catch more fish. '
        f'<a href="{root}affiliate-disclosure.html">Full disclosure</a>.'
    )


def classify_article(title: str, slug: str) -> str:
    text = (title + ' ' + slug).lower()
    for cat_id, cat in CATEGORIES.items():
        if any(kw in text for kw in cat['keywords']):
            return cat_id
    return 'accessories'


def find_related(current_slug, all_articles, n=4):
    current = next((a for a in all_articles if a['slug'] == current_slug), None)
    if not current: return []
    scored = []
    for a in all_articles:
        if a['slug'] == current_slug: continue
        sim = SequenceMatcher(None, current['title'].lower(), a['title'].lower()).ratio()
        if a.get('category') == current.get('category'): sim += 0.3
        scored.append((sim, a))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:n]]


def extract_faqs(md):
    faq_section = re.split(r'^##\s+(?:FAQ|Frequently\s+Asked)', md, flags=re.MULTILINE | re.IGNORECASE)
    if len(faq_section) < 2: return []
    section = faq_section[1].split('\n## ')[0]
    faqs, q, a_lines = [], None, []
    for line in section.split('\n'):
        line = line.strip()
        if line.startswith('### ') or (line.startswith('**') and line.endswith('**')):
            if q and a_lines: faqs.append({'q': q, 'a': ' '.join(a_lines)})
            q = line.lstrip('#').strip().strip('*').strip('?') + '?'; a_lines = []
        elif q and line and not line.startswith('#'):
            clean = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
            clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
            a_lines.append(clean)
    if q and a_lines: faqs.append({'q': q, 'a': ' '.join(a_lines)})
    return faqs


def extract_title(md, fallback):
    m = re.search(r'"headline"\s*:\s*"([^"]+)"', md[:2000])
    if m: return m.group(1).strip()
    for line in md.split('\n')[:20]:
        line = line.strip()
        if line.startswith('# '): return line[2:].strip().strip('*')
        m = re.match(r'^\*\*(.+)\*\*\s*$', line)
        if m: return m.group(1).strip()
    for line in md.split('\n')[:20]:
        line = line.strip()
        if (line and not line.startswith(('*', '#', '{', 'FTC', 'FishingTribune', 'Last Updated'))
                and 20 < len(line) < 120):
            return line[:100]
    return fallback


def extract_excerpt(md, max_len=155):
    m = re.search(r'"description"\s*:\s*"([^"]+)"', md[:2000])
    if m and len(m.group(1)) > 40:
        desc = m.group(1).strip()
        return desc[:max_len].rsplit(' ', 1)[0] + '...' if len(desc) > max_len else desc
    for line in md.split('\n'):
        line = line.strip()
        ll = line.lower()
        if (not line or line.startswith(('#', '*By ', '*Target', '{', 'FTC', 'FishingTribune', 'Last Updated'))
                or 'affiliate link' in ll or 'affiliate commission' in ll
                or 'reader-supported' in ll or 'ftc' in ll[:4]):
            continue
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
        clean = re.sub(r'\*(.+?)\*', r'\1', clean)
        clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
        if len(clean) > 40:
            return clean[:max_len].rsplit(' ', 1)[0] + '...' if len(clean) > max_len else clean
    return f'{SITE_NAME} - Expert fishing gear reviews and recommendations.'


# ── Content cleanup before rendering ─────────────────────────────

def clean_md(md: str, title: str) -> str:
    """Strip duplicate title, FTC disclosures, JSON-LD, code fences from body."""
    cleaned = []
    title_clean = title.lower().strip()
    for line in md.split('\n'):
        s = line.strip()
        # Skip raw JSON-LD
        if s.startswith('{"@context"'): continue
        if s.startswith('title:'): continue
        if s.startswith('```'): continue
        # Skip duplicate H1 (template already has it)
        if s.startswith('# '):
            if s[2:].strip().strip('*').lower() == title_clean: continue
        # Skip FTC disclosure paragraphs in body
        sl = s.lower()
        if ('reader-supported' in sl and 'affiliate' in sl): continue
        if s.startswith('FTC') and 'disclosure' in sl: continue
        if ('amazon services llc' in sl): continue
        cleaned.append(line)
    return '\n'.join(cleaned)


# ── Markdown to HTML ─────────────────────────────────────────────

def md_to_html(md: str) -> str:
    lines = md.split('\n')
    out = []
    in_ul = in_ol = in_table = in_blockquote = False
    table_rows = []
    table_count = 0

    def flush_list():
        nonlocal in_ul, in_ol
        if in_ul: out.append('</ul>'); in_ul = False
        if in_ol: out.append('</ol>'); in_ol = False

    def flush_table():
        nonlocal in_table, table_rows, table_count
        if not (in_table and table_rows):
            return
        # Parse header and rows
        header_cells = [c.strip() for c in table_rows[0].strip('|').split('|')]
        data_rows = []
        for row in table_rows[1:]:
            if set(row.replace('|', '').replace('-', '').replace(':', '').strip()) == set():
                continue  # separator
            data_rows.append([c.strip() for c in row.strip('|').split('|')])

        # Decide: product card or plain table?
        # Product card if header has Product/Price/Best For type columns
        h_lower = [h.lower() for h in header_cells]
        is_product = any(w in ' '.join(h_lower) for w in ['product', 'price', 'best for', 'model', 'kayak', 'rod', 'reel', 'lure'])

        if is_product and len(data_rows) >= 2:
            _render_product_cards(out, header_cells, data_rows, table_count == 0)
        else:
            out.append('<div class="table-wrap"><table>')
            out.append('<thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in header_cells) + '</tr></thead><tbody>')
            for row in data_rows:
                out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in row) + '</tr>')
            out.append('</tbody></table></div>')

        table_count += 1
        table_rows = []; in_table = False

    def flush_blockquote():
        nonlocal in_blockquote
        if in_blockquote: out.append('</blockquote>'); in_blockquote = False

    def inline(text):
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        def link_replace(m):
            label, url = m.group(1), m.group(2)
            if 'amazon.com' in url.lower():
                sep = '&' if '?' in url else '?'
                url = f'{url}{sep}tag={AFFILIATE_TAG}'
                return f'<a href="{esc(url)}" class="cta-button" rel="nofollow sponsored" target="_blank">{label} &rarr;</a>'
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
            flush_list(); continue  # Skip — handled by template
        elif stripped.startswith('---') or stripped.startswith('***'):
            flush_list(); out.append('<hr>')
        elif re.match(r'^[-*+]\s', stripped):
            if not in_ul: flush_list(); out.append('<ul>'); in_ul = True
            out.append(f'<li>{inline(stripped[2:].strip())}</li>')
        elif re.match(r'^\d+\.\s', stripped):
            if not in_ol: flush_list(); out.append('<ol>'); in_ol = True
            out.append(f'<li>{inline(re.sub(r"^\\d+\\.\\s*", "", stripped))}</li>')
        else:
            flush_list()
            out.append(f'<p>{inline(stripped)}</p>')
    flush_list(); flush_table(); flush_blockquote()
    return '\n'.join(out)


def _render_product_cards(out, headers, rows, is_first_table):
    """Render a comparison table as Wirecutter-style product cards."""
    # Map column indices
    h_lower = [h.lower() for h in headers]
    name_i = next((i for i, h in enumerate(h_lower) if any(w in h for w in ['product', 'model', 'kayak', 'rod', 'reel', 'lure', 'name'])), 0)
    price_i = next((i for i, h in enumerate(h_lower) if 'price' in h), -1)
    best_i = next((i for i, h in enumerate(h_lower) if 'best' in h), -1)
    link_i = next((i for i, h in enumerate(h_lower) if 'link' in h or 'buy' in h or 'url' in h), -1)

    # Spec columns = everything else
    spec_cols = [i for i in range(len(headers)) if i not in (name_i, price_i, best_i, link_i)]

    out.append('<div class="product-cards">')
    for idx, row in enumerate(rows):
        if len(row) <= name_i: continue
        name = re.sub(r'\*\*(.+?)\*\*', r'\1', row[name_i]).strip()
        price = row[price_i].strip() if price_i >= 0 and price_i < len(row) else ''
        best_for = row[best_i].strip() if best_i >= 0 and best_i < len(row) else ''

        # Extract Amazon link if present in any cell
        amazon_url = ''
        for cell in row:
            m = re.search(r'https?://[^\s)]+amazon[^\s)]*', cell)
            if m:
                amazon_url = m.group(0)
                sep = '&' if '?' in amazon_url else '?'
                amazon_url = f'{amazon_url}{sep}tag={AFFILIATE_TAG}'
                break
        # Fallback: Amazon search
        if not amazon_url:
            q = name.replace(' ', '+')
            amazon_url = f'https://www.amazon.com/s?k={q}&tag={AFFILIATE_TAG}'

        is_top = (idx == 0 and is_first_table)
        cls = ' top-pick' if is_top else ''
        badge = '<div class="top-pick-badge">Our Top Pick</div>' if is_top else ''

        specs_html = ''
        for si in spec_cols:
            if si < len(row) and row[si].strip() and si < len(headers):
                val = re.sub(r'\*\*(.+?)\*\*', r'\1', row[si]).strip()
                if val and val != '—' and val != '-':
                    specs_html += f'<div class="spec"><div class="spec-label">{esc(headers[si])}</div><div class="spec-value">{esc(val)}</div></div>'

        out.append(f'''<div class="product-card{cls}">
  {badge}
  <div class="product-info">
    <h3>{esc(name)}</h3>
    {f'<div class="product-price">{esc(price)}</div>' if price else ''}
    {f'<div class="product-subtitle">Best for: {esc(best_for)}</div>' if best_for else ''}
  </div>
  {f'<div class="specs-grid">{specs_html}</div>' if specs_html else ''}
  <div class="product-cta">
    <a href="{esc(amazon_url)}" class="cta-button" rel="nofollow sponsored" target="_blank">Check Price on Amazon &rarr;</a>
  </div>
</div>''')
    out.append('</div>')


# ── HTML Components ──────────────────────────────────────────────

HAMBURGER_JS = '''<script>
document.querySelector('.hamburger')?.addEventListener('click',function(){
  document.querySelector('.site-nav').classList.toggle('open');
});
</script>'''

def _head(title, description, canonical, og_type='website', extra_meta='', extra_schema='', root='./', og_image=''):
    title_tag = f'{title} - {SITE_NAME}' if SITE_NAME not in title else title
    if len(title_tag) > 65: title_tag = title_tag[:62] + '...'
    ga = f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{GA_ID}");</script>' if GA_ID else ''
    gsc = f'<meta name="google-site-verification" content="{GSC_VERIFICATION}">' if GSC_VERIFICATION else ''
    og_img = og_image or f'{BASE_URL}/og-default.png'
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
<meta property="og:image" content="{og_img}">
<meta name="twitter:card" content="summary_large_image">
{extra_meta}
{extra_schema}
<link rel="preconnect" href="https://images.unsplash.com">
<link rel="preconnect" href="https://www.amazon.com">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{root}articles.xml">
{ga}
<link rel="stylesheet" href="{root}style.css">
</head>'''


def _header(active='', root='./'):
    return f'''<body>
<header class="site-header">
  <div class="container wide">
    <div class="site-title"><a href="{root}"><span class="logo-icon">FT</span> Fishing <span>Tribune</span></a></div>
    <button class="hamburger" aria-label="Menu"><span></span><span></span><span></span></button>
    <nav class="site-nav">
      <a href="{root}">Home</a>
      <a href="{root}about.html">About</a>
      <a href="{root}affiliate-disclosure.html">Disclosure</a>
    </nav>
  </div>
</header>'''


def _footer(root='./'):
    cat_links = '\n'.join(f'      <a href="{root}categories/{cid}.html">{c["name"]}</a>' for cid, c in CATEGORIES.items())
    return f'''<footer class="site-footer">
  <div class="container wide">
    <div class="footer-grid">
      <div class="footer-section"><h4>Fishing Tribune</h4><p>Honest, data-driven fishing gear reviews from anglers who actually fish.</p></div>
      <div class="footer-section"><h4>Categories</h4>{cat_links}</div>
      <div class="footer-section"><h4>Company</h4><a href="{root}about.html">About</a><a href="{root}affiliate-disclosure.html">Disclosure</a><a href="{root}sitemap.xml">Sitemap</a><a href="{root}articles.xml">RSS</a></div>
      <div class="footer-section"><h4>Legal</h4><p style="font-size:.78rem">Amazon Associate. We earn from qualifying purchases.</p></div>
    </div>
    <div class="footer-bottom"><span>&copy; 2026 {SITE_NAME}</span><a href="{root}affiliate-disclosure.html">Disclosure</a></div>
  </div>
</footer>
{HAMBURGER_JS}
</body></html>'''


# ── Page Generators ──────────────────────────────────────────────

def article_page(title, body_html, slug, excerpt, date, category, faqs, related, root='../'):
    cat_name = CATEGORIES.get(category, {}).get('name', 'Gear')
    hero = hero_url(category)
    schemas = '<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL},
            {"@type": "ListItem", "position": 2, "name": cat_name, "item": f"{BASE_URL}/categories/{category}.html"},
            {"@type": "ListItem", "position": 3, "name": title},
        ]}) + '</script>\n<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": title, "description": excerpt, "image": hero,
        "url": f"{BASE_URL}/articles/{slug}.html",
        "datePublished": date, "dateModified": BUILD_DATE,
        "author": {"@type": "Organization", "name": f"{SITE_NAME} Editorial"},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": BASE_URL},
    }) + '</script>'
    if faqs:
        schemas += '\n<script type="application/ld+json">' + json.dumps({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]
        }) + '</script>'

    related_html = ''
    if related:
        cards = '\n'.join(f'      <div class="related-card"><h3><a href="{r["slug"]}.html">{esc(r["title"])}</a></h3></div>' for r in related)
        related_html = f'\n  <section class="related-articles"><h2>Related Articles</h2><div class="related-grid">{cards}</div></section>'

    return f'''{_head(title, excerpt, f"{BASE_URL}/articles/{slug}.html", "article", extra_schema=schemas, root=root, og_image=hero)}
{_header(root=root)}
<main class="container">
  <article>
    <div class="article-header">
      <nav class="breadcrumb"><a href="{root}">Home</a> &rsaquo; <a href="{root}categories/{category}.html">{esc(cat_name)}</a> &rsaquo; Review</nav>
      <h1>{esc(title)}</h1>
      <div class="article-meta">
        <span class="trust-badge"><svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg> Independently Reviewed</span>
        <span class="updated-badge"><svg viewBox="0 0 24 24" width="14" height="14"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11z"/></svg> Updated {BUILD_DATE}</span>
      </div>
    </div>
    <div class="article-hero"><img src="{hero}" alt="{esc(title)}" loading="eager" width="1200" height="500"></div>
    <div class="ftc-disclosure">{ftc_disclosure(root)}</div>
    <div class="article-body">
{body_html}
    </div>
    <div class="author-bio">
      <div class="bio-avatar">FT</div>
      <div class="bio-text"><h3>{SITE_NAME} Editorial Team</h3><p>We test, review, and recommend the best fishing gear. 50+ years of combined angling experience. Every product evaluated on real-world performance.</p></div>
    </div>
    <div class="email-signup">
      <h3>Get Weekly Fishing Gear Deals</h3>
      <p>Join 10,000+ anglers who get our best deals first.</p>
      <div class="signup-form"><input type="email" placeholder="Your email" aria-label="Email"><button class="signup-btn" type="button">Subscribe</button></div>
      <p class="signup-social">No spam. Unsubscribe anytime.</p>
    </div>{related_html}
  </article>
</main>
{_footer(root=root)}'''


def index_page(articles):
    cards = []
    for a in articles:
        cat_name = CATEGORIES.get(a.get('category', ''), {}).get('name', 'Gear')
        cards.append(f'''    <article class="article-card">
      <div class="card-body">
        <div class="card-category">{esc(cat_name)}</div>
        <h2><a href="articles/{a['slug']}.html">{esc(a['title'])}</a></h2>
        <p class="excerpt">{esc(a['excerpt'])}</p>
        <div class="card-footer"><span class="card-meta">{read_time(a['words'])}</span><a href="articles/{a['slug']}.html" class="read-more">Read review &rarr;</a></div>
      </div>
    </article>''')

    cat_tiles = '\n'.join(f'      <a href="categories/{cid}.html" class="category-tile"><span>{esc(c["name"])} ({sum(1 for a in articles if a.get("category")==cid)})</span></a>'
                          for cid, c in CATEGORIES.items())
    schema = json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": BASE_URL})
    hero = unsplash(HERO_PHOTOS['homepage'], 1400, 500)

    return f'''{_head(f"{SITE_NAME} — Expert Fishing Gear Reviews",
        "Honest fishing gear reviews. Fish finders, kayaks, rods — tested by anglers who actually fish.",
        f"{BASE_URL}/", extra_schema=f'<script type="application/ld+json">{schema}</script>', og_image=hero)}
{_header('home')}
<section class="hero-banner"><img src="{hero}" alt="Fishing at sunrise" loading="eager" width="1400" height="500"><div class="overlay"></div>
  <div class="hero-content"><h1>Expert Fishing Gear Reviews</h1><p>Honest reviews from anglers who fish. No fluff, no fake rankings.</p>
    <div class="hero-badge"><strong>{len(articles)}</strong> reviews &middot; Updated {BUILD_DATE}</div></div>
</section>
<main class="container wide">
  <section class="category-section"><h2>Browse by Category</h2><div class="category-grid">{cat_tiles}</div></section>
  <h2 class="section-label">Featured Reviews</h2>
  <section class="article-grid">{chr(10).join(cards[:8])}</section>
  {'<h2 class="section-label">More Reviews</h2><section class="article-grid">' + chr(10).join(cards[8:]) + '</section>' if len(cards) > 8 else ''}
</main>
{_footer()}'''


def category_page(cat_id, cat_info, articles, root='../'):
    cat_articles = [a for a in articles if a.get('category') == cat_id]
    hero = hero_url(cat_id)
    cards = '\n'.join(f'''    <article class="article-card"><div class="card-body">
        <h2><a href="{root}articles/{a['slug']}.html">{esc(a['title'])}</a></h2>
        <p class="excerpt">{esc(a['excerpt'])}</p>
        <div class="card-footer"><span class="card-meta">{read_time(a['words'])}</span><a href="{root}articles/{a['slug']}.html" class="read-more">Read review &rarr;</a></div>
      </div></article>''' for a in cat_articles) or '<p>No articles yet.</p>'
    return f'''{_head(f"{cat_info['name']} - {SITE_NAME}", f"Best {cat_info['name'].lower()} reviews.", f"{BASE_URL}/categories/{cat_id}.html", root=root, og_image=hero)}
{_header(root=root)}
<main class="container wide">
  <div class="category-hero"><img src="{hero}" alt="{esc(cat_info['name'])}" loading="eager" width="1200" height="400"><div class="overlay"></div><h1>{esc(cat_info['name'])}</h1></div>
  <section class="article-grid">{cards}</section>
</main>
{_footer(root=root)}'''


def about_page():
    hero = hero_url('default')
    return f'''{_head(f"About {SITE_NAME}", f"Independent fishing gear reviews by anglers, for anglers.", f"{BASE_URL}/about.html")}
{_header('about')}
<main class="container">
  <div class="category-hero" style="margin-top:24px"><img src="{hero}" alt="Fishing" loading="eager" width="1200" height="400"><div class="overlay"></div><h1>About {SITE_NAME}</h1></div>
  <div class="article-body">
    <h2>Why We Exist</h2>
    <p>The fishing gear market is flooded with paid placements and fake reviews. We started {SITE_NAME} because we were tired of buying gear based on hype. <strong>Every review is based on real specs, real user feedback, and real-world performance.</strong></p>
    <h2>Our Methodology</h2>
    <ul><li><strong>Market analysis</strong> — 50+ products per category narrowed to genuine contenders</li><li><strong>Spec comparison</strong> — manufacturer data and independent measurements</li><li><strong>User review aggregation</strong> — Amazon, Bass Pro, forums, YouTube cross-referenced</li><li><strong>Expert consultation</strong> — tournament anglers, guides, tackle shop owners</li><li><strong>Value assessment</strong> — performance per dollar, not just absolute quality</li></ul>
    <h2>Editorial Standards</h2><p>No brand pays for placement. No manufacturer sponsors our rankings. If a product is bad, we say so.</p>
    <h2>Our Team</h2><p>50+ years of combined angling experience — freshwater bass, saltwater fly, kayak fishing, ice fishing, tournament competition.</p>
    <h2>How We Make Money</h2><p>Reader-supported via Amazon affiliate commissions at no extra cost to you. See our <a href="affiliate-disclosure.html">full disclosure</a>.</p>
  </div>
</main>
{_footer()}'''


def disclosure_page():
    return f'''{_head(f"Affiliate Disclosure - {SITE_NAME}", "FTC compliance and affiliate disclosure.", f"{BASE_URL}/affiliate-disclosure.html")}
{_header('disclosure')}
<main class="container">
  <div class="page-header"><h1>Affiliate Disclosure</h1></div>
  <div class="article-body">
    <p>{SITE_NAME} is reader-supported. When you buy through our links, we may earn a commission at no extra cost to you.</p>
    <h2>How We Make Money</h2><p>We participate in the Amazon Services LLC Associates Program. Some links are affiliate links — we get a small commission if you purchase. This doesn't affect your price.</p>
    <h2>Our Promise</h2><p>We only recommend products we believe will help you catch more fish. No brand pays for placement. Your trust matters more than any commission.</p>
    <h2>FTC Compliance</h2><p>Per FTC 16 CFR Part 255, we disclose that we receive compensation for products reviewed or linked on this site. Contact: hello@fishingtribune.com</p>
  </div>
</main>
{_footer()}'''


def error_404_page():
    return f'''{_head("Page Not Found", "Page not found.", f"{BASE_URL}/404.html")}
{_header()}
<main class="container"><div class="error-page"><h1>404</h1><p>This page got away. Let's get you back on the water.</p><a href="./" class="cta-button">Homepage &rarr;</a></div></main>
{_footer()}'''


def build_sitemap(articles):
    urls = [f'  <url><loc>{BASE_URL}/</loc><lastmod>{BUILD_DATE}</lastmod><priority>1.0</priority></url>',
            f'  <url><loc>{BASE_URL}/about.html</loc><lastmod>{BUILD_DATE}</lastmod><priority>0.5</priority></url>',
            f'  <url><loc>{BASE_URL}/affiliate-disclosure.html</loc><lastmod>{BUILD_DATE}</lastmod><priority>0.3</priority></url>']
    for cid in CATEGORIES:
        urls.append(f'  <url><loc>{BASE_URL}/categories/{cid}.html</loc><lastmod>{BUILD_DATE}</lastmod><priority>0.6</priority></url>')
    for a in articles:
        urls.append(f'  <url><loc>{BASE_URL}/articles/{a["slug"]}.html</loc><lastmod>{BUILD_DATE}</lastmod><priority>0.8</priority></url>')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{chr(10).join(urls)}\n</urlset>'


def build_rss(articles):
    items = '\n'.join(f'  <item><title>{esc(a["title"])}</title><link>{BASE_URL}/articles/{a["slug"]}.html</link><description>{esc(a["excerpt"])}</description><guid>{BASE_URL}/articles/{a["slug"]}.html</guid></item>' for a in articles[:20])
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n  <title>{SITE_NAME}</title>\n  <link>{BASE_URL}</link>\n  <description>Expert fishing gear reviews.</description>\n  <atom:link href="{BASE_URL}/articles.xml" rel="self" type="application/rss+xml"/>\n{items}\n</channel></rss>'


# ── Main Build ───────────────────────────────────────────────────

def main():
    articles = []
    date = '2026-03-29'
    skipped = 0
    seen_slugs = set()

    def should_skip(fname, md):
        for pat in SKIP_PATTERNS:
            if pat in fname: return True
        first = '\n'.join(md.split('\n')[:5])
        if 'BRAND DNA' in first: return True
        if first.strip().startswith('title:'): return True
        return False

    def slug_from_filename(fname):
        s = re.sub(r'^article-\d+-', '', fname.replace('.md', ''))
        s = re.sub(r'-article$', '', s)
        return re.sub(r'-+', '-', re.sub(r'[^a-z0-9-]', '-', s.lower())).strip('-') or 'article'

    def process_md(md, title):
        md = clean_md(md, title)
        return md

    print(f'  Scanning articles...\n')

    # Phase 1a: PICKS
    for num in sorted(PICKS.keys(), key=lambda x: int(x)):
        fname, slug = PICKS[num]
        src = ARTICLES_SRC / fname
        if not src.exists(): skipped += 1; continue
        md = src.read_bytes().replace(b'\x00', b'').decode('utf-8', errors='replace')
        if len(md.split()) < 500: skipped += 1; continue
        title = extract_title(md, slug.replace('-', ' ').title())
        md = process_md(md, title)
        articles.append({'num': num, 'slug': slug, 'title': title,
                         'excerpt': extract_excerpt(md), 'words': len(md.split()),
                         'category': classify_article(title, slug),
                         'faqs': extract_faqs(md), 'md': md})
        seen_slugs.add(slug)

    # Phase 1b: Auto-discover
    picks_fnames = {v[0] for v in PICKS.values()}
    for src in sorted(ARTICLES_SRC.glob('article-*.md')):
        fname = src.name
        if fname in picks_fnames: continue
        md = src.read_bytes().replace(b'\x00', b'').decode('utf-8', errors='replace')
        if should_skip(fname, md): skipped += 1; continue
        if len(md.split()) < 1000: skipped += 1; continue
        if not re.search(r'^# .+', md, re.MULTILINE): skipped += 1; continue
        slug = slug_from_filename(fname)
        if slug in seen_slugs: slug += '-v2'
        if slug in seen_slugs: skipped += 1; continue
        title = extract_title(md, slug.replace('-', ' ').title())
        md = process_md(md, title)
        num = re.search(r'article-(\d+)', fname)
        articles.append({'num': num.group(1) if num else '99', 'slug': slug, 'title': title,
                         'excerpt': extract_excerpt(md), 'words': len(md.split()),
                         'category': classify_article(title, slug),
                         'faqs': extract_faqs(md), 'md': md})
        seen_slugs.add(slug)

    print(f'  {len(articles)} articles, {skipped} skipped\n')

    # Generate articles
    for a in articles:
        body = md_to_html(a['md'])
        related = find_related(a['slug'], articles)
        page = article_page(a['title'], body, a['slug'], a['excerpt'], date, a['category'], a['faqs'], related)
        (ARTICLES_DIR / f'{a["slug"]}.html').write_text(page, encoding='utf-8')
        faq = f' ({len(a["faqs"])} FAQs)' if a['faqs'] else ''
        print(f'  {a["slug"]}.html ({a["words"]:,}w, {a["category"]}){faq}')
    for a in articles: del a['md']

    # Pages
    (SITE_DIR / 'index.html').write_text(index_page(articles), encoding='utf-8')
    print(f'\n  index.html ({len(articles)} articles)')
    cat_dir = SITE_DIR / 'categories'; cat_dir.mkdir(exist_ok=True)
    for cid, ci in CATEGORIES.items():
        (cat_dir / f'{cid}.html').write_text(category_page(cid, ci, articles), encoding='utf-8')
    print(f'  {len(CATEGORIES)} category pages')
    for name, fn in [('about', about_page), ('affiliate-disclosure', disclosure_page), ('404', error_404_page)]:
        (SITE_DIR / f'{name}.html').write_text(fn(), encoding='utf-8')
    print(f'  about, disclosure, 404')
    (SITE_DIR / 'sitemap.xml').write_text(build_sitemap(articles), encoding='utf-8')
    (SITE_DIR / 'articles.xml').write_text(build_rss(articles), encoding='utf-8')
    (SITE_DIR / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml', encoding='utf-8')

    print(f'\n  === BUILD COMPLETE ===')
    print(f'  Articles: {len(articles)}')
    cats = ', '.join(f'{CATEGORIES[c]["name"]} ({sum(1 for a in articles if a.get("category")==c)})' for c in CATEGORIES)
    print(f'  Categories: {cats}')
    print(f'  Sitemap: {len(articles) + len(CATEGORIES) + 3} URLs | FAQs: {sum(len(a.get("faqs",[])) for a in articles)}')


if __name__ == '__main__':
    main()
