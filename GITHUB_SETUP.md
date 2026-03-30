# FishingTribune GitHub Setup

Date: 2026-03-29 HST
Repository: https://github.com/brinkfoundry/fishingtribune
Local path: /Users/openclaw/clawd/ventures/tribune/site

## What happened

- Confirmed GitHub auth for account `brinkfoundry` via `gh auth status`
- Confirmed repository already existed under the Foundry account: `brinkfoundry/fishingtribune`
- Initialized local git in the site directory
- Set remote `origin` to `git@github.com:brinkfoundry/fishingtribune.git`
- Fetched remote history and found an older static-site history already on `main`
- Force-pushed the current local static-site snapshot to `main` so Cloudflare Pages can deploy from the latest site files in this directory

## Commands run

```bash
gh auth status
git init -b main
git config user.name "Brink Foundry"
git config user.email "foundry@brinkfoundry.com"
git add .
git commit -m "Initial FishingTribune static site"
git remote set-url origin git@github.com:brinkfoundry/fishingtribune.git
git fetch origin main
git push -u origin main --force-with-lease
```

## Results

- Repo URL: https://github.com/brinkfoundry/fishingtribune
- Remote URL: git@github.com:brinkfoundry/fishingtribune.git
- Branch used for deploy: `main`
- Cloudflare Pages can be pointed at this repo/branch for automatic deploys

## Cloudflare Pages settings

- Framework preset: None
- Build command: none
- Build output directory: /
- Root directory: /
- Production branch: main

## Verification commands

```bash
gh repo view brinkfoundry/fishingtribune
git remote -v
git log -1 --oneline
git ls-remote --heads origin
```
