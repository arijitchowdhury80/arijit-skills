#!/usr/bin/env python3
"""
platform_utils.py — Shared utilities for all Algolia Search Intelligence Platform scripts.

Import pattern:
  import sys, os
  sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
  from platform_utils import load_config, get_model, load_upstream, get_audit_dir

DATA-CONTRACT.md: Part 1 (Script Contract), Part 7 (Verification Gate)
"""

import os, json, re
from pathlib import Path

# ── Tavily search client ──────────────────────────────────────────────────────
# Tavily is the primary web/news search layer for scripts.
# It returns clean extracted text (not raw HTML), has a news topic mode,
# supports date filtering, and has a free tier (1,000 searches/month).
#
# Architecture note — when to use Tavily vs LLM:
#   Tavily only (no LLM):  structured data already in results (news articles,
#                          URLs, dates) — keyword/regex classification is enough
#   Tavily → LLM:          when you need to extract meaning from the returned
#                          content (e.g., find a verbatim quote inside a transcript)
#   Perplexity one-shot:   when you want synthesis + citations in one step
#                          without managing separate retrieval
#
# API key: TAVILY_API_KEY env var. Free tier: 1,000 searches/month.
# Sign up: https://tavily.com

TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY', '')

def tavily_search(query, topic='general', max_results=10, days=60,
                  include_answer=False, search_depth='basic'):
    """
    Search the web via Tavily and return clean structured results.

    Args:
        query:          Natural language search query
        topic:          'general' | 'news' — use 'news' for news-specific search
        max_results:    Max number of results (1-20)
        days:           Lookback window in days (only with topic='news')
        include_answer: If True, Tavily also returns an AI-generated summary
        search_depth:   'basic' (fast) | 'advanced' (deeper extraction, costs 2 credits)

    Returns:
        list of dicts: [{title, url, content, published_date, score}, ...]
        Empty list if API key not set or request fails — caller handles gracefully.

    Example:
        results = tavily_search(
            '"DSW" digital OR ecommerce OR technology',
            topic='news', days=60, max_results=10
        )
        for r in results:
            print(r['title'], r['url'], r.get('published_date'))
    """
    if not TAVILY_API_KEY:
        return []

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=TAVILY_API_KEY)

        kwargs = dict(
            query=query,
            max_results=max_results,
            include_answer=include_answer,
            search_depth=search_depth,
        )
        if topic == 'news':
            kwargs['topic'] = 'news'
            kwargs['days'] = days
        else:
            kwargs['topic'] = 'general'

        response = client.search(**kwargs)
        return response.get('results', [])

    except Exception as e:
        return []

def tavily_available():
    """Return True if TAVILY_API_KEY is set."""
    return bool(TAVILY_API_KEY)

# ── Config ────────────────────────────────────────────────────────────────────

PLATFORM_CONFIG_PATH = Path(__file__).parent.parent / 'platform.config.json'

def load_config():
    """Load platform.config.json. Returns empty dict on failure (graceful)."""
    try:
        with open(PLATFORM_CONFIG_PATH) as f:
            return json.load(f)
    except Exception:
        return {}

def get_model(module_name, config=None):
    """
    Return the Claude model ID for a given module name.
    Reads from platform.config.json module_tiers → models mapping.

    Returns None for programmatic modules (no LLM required).
    """
    if config is None:
        config = load_config()
    tier = config.get('module_tiers', {}).get(module_name, 'data_enrichment')
    model_id = config.get('models', {}).get(tier)
    return model_id  # None for programmatic tier

def is_mcp_available(mcp_name, config=None):
    """Check if a named MCP server is available per config."""
    if config is None:
        config = load_config()
    return config.get('mcp_available', {}).get(mcp_name, False)

def is_feature_enabled(flag_name, config=None):
    """Check if a feature flag is enabled."""
    if config is None:
        config = load_config()
    return config.get('feature_flags', {}).get(flag_name, True)  # default on

def get_audit_dir(config=None):
    """
    Return the base audit directory.
    Priority: ALGOLIA_AUDIT_DIR env var → config audit_dir → ~/algolia-audits
    """
    env_dir = os.environ.get('ALGOLIA_AUDIT_DIR')
    if env_dir:
        return os.path.expanduser(env_dir)
    if config is None:
        config = load_config()
    fallback = config.get('output', {}).get('audit_dir_fallback', '~/algolia-audits')
    return os.path.expanduser(fallback)

# ── Upstream data reading ─────────────────────────────────────────────────────

def load_upstream(output_dir, filename):
    """
    Load an upstream JSON output file if it exists.
    Returns {} gracefully if file missing — scripts must not fail on missing upstream.

    Usage:
        ctx = load_upstream(output_dir, '01-company-context.json')
        company_name = ctx.get('company_name') or domain
    """
    path = os.path.join(output_dir, filename)
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

# ── Domain normalization ──────────────────────────────────────────────────────

def normalize_domain(raw):
    """
    Normalize domain input per DATA-CONTRACT.md Part 1.1.
    Strips protocol, www, trailing path, lowercases.

    normalize_domain('https://www.Costco.com/about') → 'costco.com'
    """
    return (raw.lower()
               .replace('https://', '').replace('http://', '')
               .replace('www.', '')
               .split('/')[0]
               .strip())

# ── stdout JSON summary ───────────────────────────────────────────────────────

def build_summary(module, script, domain, company_name,
                  output_md, output_json,
                  sources_succeeded=None, sources_failed=None,
                  skill_enrichment_required=None, errors=None):
    """
    Build the standard stdout JSON summary per DATA-CONTRACT.md Part 1.5.
    Call json.dumps(build_summary(...), indent=2) and print to stdout.
    """
    from datetime import date

    md_size = os.path.getsize(output_md) if output_md and os.path.exists(output_md) else 0
    json_size = os.path.getsize(output_json) if output_json and os.path.exists(output_json) else 0

    errs = errors or []
    status = 'success' if not errs else ('partial' if (md_size > 0) else 'failed')

    return {
        'status': status,
        'domain': domain,
        'company_name': company_name,
        'module': module,
        'script': script,
        'output_md': output_md,
        'output_json': output_json,
        'size_md_bytes': md_size,
        'size_json_bytes': json_size,
        'sources_succeeded': sources_succeeded or [],
        'sources_failed': sources_failed or [],
        'skill_enrichment_required': skill_enrichment_required or [],
        'errors': errs,
        'collected_at': date.today().isoformat(),
    }

# ── Base JSON meta block ──────────────────────────────────────────────────────

def base_meta(module, module_id, script, domain, company_name,
              sources_succeeded=None, sources_failed=None,
              skill_enrichment_required=None):
    """
    Build the _meta block required by DATA-CONTRACT.md Part 3.1.
    Include in every module's JSON output.
    """
    from datetime import date
    return {
        'meta': {
            'module': module,
            'module_id': module_id,
            'script': script,
            'domain': domain,
            'company_name': company_name,
            'collected_at': date.today().isoformat(),
            'sources_succeeded': sources_succeeded or [],
            'sources_failed': sources_failed or [],
            'skill_enrichment_required': skill_enrichment_required or [],
            'skill_enrichment_completed': False,
            'schema_version': '1.0',
        }
    }

# ── Verification gate ─────────────────────────────────────────────────────────

def verify_gate(output_dir, md_filename, json_filename, min_md_bytes=1000):
    """
    Run the standard verification gate check per DATA-CONTRACT.md Part 7.
    Returns (passed, reason_if_failed).

    Usage in SKILL orchestrators:
        passed, reason = verify_gate(output_dir, '03-traffic-data.md', '03-traffic-data.json')
        if not passed:
            raise RuntimeError(f'Gate FAIL: {reason}')
    """
    md_path = os.path.join(output_dir, md_filename)
    json_path = os.path.join(output_dir, json_filename)

    if not os.path.exists(md_path):
        return False, f'{md_filename} does not exist'
    if os.path.getsize(md_path) < min_md_bytes:
        return False, f'{md_filename} is only {os.path.getsize(md_path)} bytes (min {min_md_bytes})'
    if not os.path.exists(json_path):
        return False, f'{json_filename} does not exist'
    try:
        with open(json_path) as f:
            data = json.load(f)
        if data.get('meta', {}).get('status') == 'failed':
            return False, f'{json_filename} status is "failed"'
    except Exception as e:
        return False, f'{json_filename} is not valid JSON: {e}'

    return True, None

