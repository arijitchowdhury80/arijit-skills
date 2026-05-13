"""Crawl4AI version pin and upgrade notes.

To upgrade Crawl4AI: bump CRAWL4AI_VERSION, run tests, update UPGRADE_NOTES.
Nothing outside this file should import crawl4ai version directly.
"""

CRAWL4AI_VERSION = "0.7.7"
SCOUT_VERSION = "0.1.0"

UPGRADE_NOTES = """
v0.7.7 → next:
- Check BrowserConfig API for breaking changes
- Check CrawlerRunConfig parameter renames (wait_for, stream flag)
- Verify fit_markdown attribute path on CrawlResult (currently result.markdown.fit_markdown)
- Re-run: pytest tests/ -v && pytest tests/integration/ -v
- Update CRAWL4AI_VERSION above
"""
