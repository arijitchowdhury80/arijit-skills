# Scout Skill Wrapper

This directory contains the Claude/Codex skill wrapper for Scout.

Scout itself is a standalone package:

```bash
pip install git+https://github.com/arijitchowdhury80/scout.git
playwright install chromium
```

Start the local service for agent use:

```bash
scout serve
curl http://localhost:8421/health
```

Install the skill wrapper:

```bash
bash install-skill.sh
```

The skill teaches the agent how to call Scout for:

- web page scraping
- sitemap and URL discovery
- multi-page crawls
- structured extraction
- screenshots
- product catalog crawling
- Algolia-ready product artifacts

The runtime, tests, Docker files, and product documentation live in the
standalone Scout repository: <https://github.com/arijitchowdhury80/scout>.
