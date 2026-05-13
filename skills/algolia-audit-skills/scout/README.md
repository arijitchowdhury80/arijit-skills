# Scout — Web Intelligence Skill

Scout is a self-hosted web intelligence platform built on [Crawl4AI](https://github.com/unclecode/crawl4ai) + Playwright. It gives Claude the ability to crawl real company websites with stealth mode, JS rendering, and PDF extraction — capabilities that WebFetch and raw curl cannot provide.

It runs locally as a FastAPI server at `http://localhost:8421`. The Claude skill (`SKILL.md`) routes Claude to Scout automatically whenever the target is one of the five supported intelligence types.

---

## Five Supported Intelligence Types

| Type | What you get | Common URL patterns |
|---|---|---|
| **About / Company** | Mission, HQ, founding, size | `/about`, `/company`, `/who-we-are` |
| **Executive Team** | C-suite names + titles | `/team`, `/leadership`, `/about/team` |
| **Hiring / Roles** | Open positions, departments, locations | `/careers`, `/jobs`, `/join-us` |
| **Investor Relations** | IR page, earnings dates, SEC links | `/investors`, `/ir` |
| **Reports & PDFs** | Annual reports, investor decks | Any `.pdf` URL |

---

## Prerequisites

- Python 3.11+
- Git
- Claude Code CLI installed

---

## Install

### Step 1 — Clone and install the Scout server

```bash
git clone https://github.com/arijitchowdhury80/algolia-claude-skills.git
# Scout server lives at: https://github.com/arijitchowdhury80/Scout (separate repo)
# Clone the Scout server repo:
git clone https://github.com/arijitchowdhury80/Scout.git
cd Scout
pip install -e .
playwright install chromium
```

### Step 2 — Configure

```bash
cp .env.example .env
```

Edit `.env`:
```
SCOUT_API_KEY=your-secret-key   # use any string; keep it secret in production
LLM_API_KEY=                    # optional — only needed for /extract endpoint
PORT=8421
```

> For local development, the default `dev-key` works fine. Set a real key before sharing the server over a network.

### Step 3 — Install the Claude skill

```bash
bash install-skill.sh
```

This copies `scout/skill/scout.md` → `~/.claude/commands/scout.md`.

Restart Claude Code (or open a new session) to load the skill.

### Step 4 — Start the server

```bash
scout serve
```

Verify:
```bash
curl -s http://localhost:8421/health
# → {"status":"ok"}
```

---

## Usage

Once Scout is running and the skill is installed, Claude routes to it automatically. You can also invoke it explicitly:

```
/scout find the leadership team at homedepot.com.mx
/scout get the investor relations page for company.com
/scout scrape the careers section at target.com
```

### Direct API usage

```bash
# Map — discover all URLs on a domain
curl -s -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com", "max_pages": 300}'

# Scrape — fetch one page as clean markdown
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/about/leadership", "use_js": true}'

# Crawl — BFS multi-page crawl
curl -s -X POST http://localhost:8421/crawl \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/careers", "max_depth": 2, "max_pages": 30}'

# Screenshot — full-page PNG (base64)
curl -s -X POST http://localhost:8421/screenshot \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com"}'
```

### CLI

```bash
scout serve                              # start server
scout scrape https://company.com/about  # scrape one page
scout map https://company.com --pages 200
scout crawl https://company.com/careers --depth 2 --pages 30
scout extract https://company.com/team --llm-key $LLM_API_KEY
```

---

## Core Pattern: Map → Filter → Scrape

The correct usage pattern is always:

```
1. Map the domain   →  get all URLs
2. Filter the list  →  identify the right section (leadership, careers, IR, etc.)
3. Scrape those URLs
```

**Never guess URLs.** Company sites vary wildly: `/team` vs `/about/leadership` vs `/company/management`. Map first.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `curl: Connection refused` | Run `scout serve` to start the server |
| HTTP 403 | Add `-H "X-API-Key: $SCOUT_API_KEY"` to your request |
| Empty or sparse markdown | Page is JS-rendered — add `"use_js": true` |
| Timeout on `/crawl` | Reduce `max_pages`, or add `"use_js": false` for faster crawl |
| `"No LLM API key"` on `/extract` | Use `css_schema` instead, or set `LLM_API_KEY` in `.env` |

---

## Skill Routing (for Claude)

Claude routes to Scout automatically — no manual invocation needed — when any of these intelligence types are requested:

- "Find the leadership team at X"
- "Get the investor relations page for X"
- "What roles is X hiring for?"
- "Find their annual report / investor deck"
- "Tell me about X's company overview"

Scout is preferred over WebFetch and raw curl for these use cases because it handles JS-rendered pages, stealth mode, and PDF extraction natively.

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full component diagram.

---

## Attribution

Scout wraps [Crawl4AI](https://github.com/unclecode/crawl4ai) by UncleCode, licensed under Apache 2.0.
