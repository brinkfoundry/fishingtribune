# FishingTribune — GitHub + Cloudflare Pages Deployment
_Last updated: 2026-03-30_

## Repository
- **GitHub:** https://github.com/brinkfoundry/fishingtribune
- **Account:** brinkfoundry
- **Branch:** main
- **Remote:** git@github.com:brinkfoundry/fishingtribune.git
- **Local path:** ~/clawd/ventures/tribune/site/
- **Latest commit:** 1bd2f8a

## Auth
- `gh auth status`: authenticated as brinkfoundry, token scopes include `repo`
- SSH key configured for git push (no HTTPS credentials needed)

## Current Site State
- index.html: full editorial homepage, 6 article cards, hero, FTC disclosure
- 6 article HTML pages converted from REVENUE markdown sources
- styles.css: responsive, 3-col desktop / 1-col mobile
- sitemap.xml: index + 6 article URLs
- robots.txt: allow all, points to sitemap
- JSON-LD Article schema on all article pages
- Amazon affiliate links using tag `fishingtribun-20`

## Cloudflare Pages Setup
To connect auto-deploy:
1. Go to https://dash.cloudflare.com → Pages → Create a project
2. Connect to GitHub → select `brinkfoundry/fishingtribune`
3. Settings:
   - **Framework preset:** None (plain HTML)
   - **Build command:** _(leave blank)_
   - **Build output directory:** `/`
   - **Root directory:** _(leave blank)_
   - **Branch:** main
4. Deploy → Cloudflare assigns a `*.pages.dev` subdomain
5. Add custom domain: `fishingtribune.com`
   - Add CNAME record in DNS: `fishingtribune.com → <project>.pages.dev`
   - Or use Cloudflare nameservers if domain is on Cloudflare

## Deploy Workflow
Every `git push origin main` from ~/clawd/ventures/tribune/site/ triggers a Cloudflare Pages auto-deploy. No build step needed — static files served directly.

## Git Push Commands
```bash
cd ~/clawd/ventures/tribune/site
git add -A
git commit -m "Your message"
git push origin main
```

## Article Source Files
Articles are generated from markdown in ~/clawd/ventures/tribune/articles/.
Use REVENUE variants for 03/05/06. Run the site generator script to rebuild HTML after markdown changes.
