#!/usr/bin/env python3
"""
generate-finding-cards.py — Finding Card Enrichment Synthesis

Reads all Phase 1 research files + scoring matrix, calls OpenAI gpt-5-mini to
generate the 9-element commercial loop for each finding, and patches {slug}-audit-data.json.

Usage:
  python3 generate-finding-cards.py <slug> <workspace_dir>

Requires: OPENAI_API_KEY in environment

Prompt caching: automatic on prompts >= 1024 tokens. Using a stable prompt_cache_key
ensures the research context (same across all 10 findings) routes to the same cache
prefix and gets reused — significant cost savings over the per-finding loop.

API source: openai==2.15.0 · chat.completions.create
File: openai/resources/chat/completions/completions.py:240
Signature: messages, model, max_completion_tokens, response_format,
           prompt_cache_key, reasoning_effort
"""

import os
import sys
import json
import re
import argparse

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed. Run: pip install openai")
    sys.exit(1)

# ── Research file map ─────────────────────────────────────────────────────────

RESEARCH_FILE_MAP: dict[str, str] = {
    "scoring_matrix":        "10-scoring-matrix.md",
    "browser_findings":      "09-browser-findings.md",
    "company_context":       "01-company-context.md",
    "tech_stack":            "02-tech-stack.md",
    "competitors":           "04-competitors.md",
    "financial_profile":     "08-financial-profile.md",
    "investor_intelligence": "11-investor-intelligence.md",
    "news_signals":          "09c-news-signals.md",
    "hiring_signals":        "09d-hiring-signals.md",
    "industry_intel":        "industry-intel.md",
}

REQUIRED_ENRICHMENT_KEYS: list[str] = [
    "pain_frame",
    "anxiety_driver",
    "industry_benchmark",
    "discovery_questions",
    "algolia_angle",
    "value_map",
    "objection_handling",
]

# ── Core functions ────────────────────────────────────────────────────────────

def load_research_files(research_dir: str) -> dict[str, str]:
    """
    Load all markdown files that exist in research_dir per RESEARCH_FILE_MAP.
    Skip missing files with a warning. Return dict of {key: content}.
    """
    result: dict[str, str] = {}
    for key, filename in RESEARCH_FILE_MAP.items():
        filepath = os.path.join(research_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                result[key] = f.read()
        else:
            print(f"  [WARN] Missing research file (skipping): {filename}", file=sys.stderr)
    return result


def build_synthesis_prompt(finding: dict, research: dict) -> str:
    """
    Build the user prompt for one finding. Includes the finding metadata,
    a grounding constraint block, the required JSON structure with all 7 enrichment
    keys, and prospect-specific SPIN framing.
    """
    finding_id   = finding.get("id", "UNKNOWN")
    title        = finding.get("title", "")
    severity     = finding.get("severity", "")
    tested_query = finding.get("tested_query", "")
    actual_behav = finding.get("actual_behavior", "")
    category     = finding.get("category", "")

    # Condense research keys into a brief index
    research_summary_lines = []
    for key in RESEARCH_FILE_MAP.keys():
        if key in research:
            word_count = len(research[key].split())
            research_summary_lines.append(f"  - {key}: {word_count} words loaded")
        else:
            research_summary_lines.append(f"  - {key}: NOT AVAILABLE")
    research_index = "\n".join(research_summary_lines)

    prompt = f"""You are generating the commercial enrichment loop for a single Algolia search audit finding.

## FINDING METADATA
- ID: {finding_id}
- Title: {title}
- Category: {category}
- Severity: {severity}
- Tested Query: {tested_query}
- Actual Behavior: {actual_behav}

## RESEARCH CONTEXT AVAILABLE
The system prompt contains the full text of these research files:
{research_index}

## CONSTRAINT BLOCK
Every field you generate MUST be grounded in the research files provided in the system prompt.
Do NOT invent statistics, company names, competitor details, or financial figures.
All numbers must trace back to the research content.
For SPIN discovery questions, use prospect-specific context:
- Reference actual platform context (e.g. WCS/IBM WebSphere Commerce if present in tech stack)
- Reference promotional events specific to the company (e.g. "Hot Sale" for Mexico retailers)
- Reference the actual tested query ({tested_query}) and the actual failure ({actual_behav})

## REQUIRED OUTPUT FORMAT
Return ONLY valid JSON (no markdown prose outside the JSON block) with this exact structure:

```json
{{
  "pain_frame": "<one sentence that names the business pain without using product jargon>",
  "anxiety_driver": {{
    "calculation": "<revenue-at-risk calculation formula, e.g. 'GMV x session_share x search_usage_rate x conversion_delta'>",
    "competitor_comparison": "<named competitor + what they do differently with a search capability>",
    "quantified_impact": "<single monetary or % figure with currency, e.g. 'MXN ~200M/year'>"
  }},
  "industry_benchmark": {{
    "metric_name": "<name of the benchmark metric>",
    "best_in_class": "<best-in-class value, e.g. '97%'>",
    "current_score": "<prospect's observed score, e.g. '0%'>",
    "gap": "<gap expressed in points or %, e.g. '97pts'>",
    "source": "<full URL or citation, e.g. 'https://baymard.com/research/product-search'>"
  }},
  "discovery_questions": {{
    "situation": "<SPIN Situation question — factual, opens the conversation>",
    "problem": "<SPIN Problem question — surfaces a pain point the prospect owns>",
    "implication": "<SPIN Implication question — connects the problem to downstream business cost>",
    "need_payoff": "<SPIN Need-Payoff question — frames the solution value in the prospect's own terms>"
  }},
  "algolia_angle": {{
    "capability": "<Algolia product or feature name, e.g. 'Rules Engine'>",
    "specifics": "<one-line technical description of what the capability does for this finding>",
    "time_to_value": "<realistic implementation estimate, e.g. '< 1 hour', '1 sprint'>"
  }},
  "value_map": {{
    "gap": "<the gap as observed in testing>",
    "capability": "<Algolia capability that closes this gap>",
    "outcome": "<business outcome, e.g. 'Promotional recovery'>",
    "metric": "<measurable improvement, e.g. '+2.1% conversion'>"
  }},
  "objection_handling": [
    {{
      "objection": "<verbatim-style objection the AE will hear from the prospect>",
      "counter": "<concise technical counter — one or two sentences>",
      "evidence_ref": "<filename of screenshot or research file that backs this counter>"
    }}
  ]
}}
```

Generate the enrichment for finding {finding_id}: {title}.
"""
    return prompt


def parse_enrichment_json(response_text: str) -> dict:
    """
    Extract JSON from LLM response. Handles ```json ... ``` code fences or raw JSON.
    Raises ValueError if any of the REQUIRED_ENRICHMENT_KEYS are missing.
    """
    # Try to extract from a ```json ... ``` fence first
    fence_match = re.search(r"```json\s*([\s\S]+?)\s*```", response_text, re.IGNORECASE)
    if fence_match:
        json_str = fence_match.group(1).strip()
    else:
        # Fallback: try to find raw JSON object in the response
        brace_match = re.search(r"\{[\s\S]+\}", response_text)
        if brace_match:
            json_str = brace_match.group(0).strip()
        else:
            raise ValueError(
                f"No JSON found in LLM response. Response text: {response_text[:300]}"
            )

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in LLM response: {e}\nJSON string: {json_str[:300]}"
        )

    # Validate all required keys are present
    missing = [k for k in REQUIRED_ENRICHMENT_KEYS if k not in data]
    if missing:
        raise ValueError(
            f"Enrichment JSON is missing required keys: {', '.join(missing)}. "
            f"Got keys: {list(data.keys())}"
        )

    return data


def _build_research_system_content(research: dict) -> str:
    """
    Assemble the system prompt content that will be cached.
    Combines all research file contents into a structured block.
    """
    lines = [
        "You are an expert Algolia sales engineer and search UX consultant.",
        "You help Account Executives prepare for discovery calls by generating",
        "commercially-grounded enrichment for each search audit finding.",
        "",
        "## RESEARCH FILES (source of truth — all enrichment must be grounded here)",
        "",
    ]

    section_headers = {
        "scoring_matrix":        "### Scoring Matrix (10-scoring-matrix.md)",
        "browser_findings":      "### Browser Test Findings (09-browser-findings.md)",
        "company_context":       "### Company Context (01-company-context.md)",
        "tech_stack":            "### Tech Stack (02-tech-stack.md)",
        "competitors":           "### Competitor Intelligence (04-competitors.md)",
        "financial_profile":     "### Financial Profile (08-financial-profile.md)",
        "investor_intelligence": "### Investor & Executive Intelligence (11-investor-intelligence.md)",
        "news_signals":          "### News Signals (09c-news-signals.md)",
        "hiring_signals":        "### Hiring Signals (09d-hiring-signals.md)",
        "industry_intel":        "### Industry Intelligence (industry-intel.md)",
    }

    for key, header in section_headers.items():
        if key in research:
            lines.append(header)
            lines.append("")
            lines.append(research[key])
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


MODEL = "gpt-5-mini"
MAX_COMPLETION_TOKENS = 4096
PROMPT_CACHE_KEY = "algolia-audit-finding-cards-v1"


def enrich_finding(finding: dict, research: dict, client: "OpenAI") -> dict:
    """
    Call gpt-5-mini with research context as the system message and finding-specific
    user prompt. OpenAI automatic prompt caching reuses the same research context
    across all 10 findings (>=1024 tokens, identical prefix, stable prompt_cache_key).

    Returns merged finding dict (original + enrichment fields).

    Protocol Read Receipt:
      Source: openai/resources/chat/completions/completions.py:240
      Quote:  "def create(self, *, messages, model, ..., max_completion_tokens,
               ..., response_format, ..., prompt_cache_key, ...)"
      Mapping: client.chat.completions.create(model=MODEL,
               messages=[system, user], max_completion_tokens=4096,
               response_format={"type": "json_object"},
               prompt_cache_key=PROMPT_CACHE_KEY)
    """
    research_system_content = _build_research_system_content(research)
    user_prompt = build_synthesis_prompt(finding, research)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": research_system_content},
            {"role": "user", "content": user_prompt},
        ],
        max_completion_tokens=MAX_COMPLETION_TOKENS,
        response_format={"type": "json_object"},
        prompt_cache_key=PROMPT_CACHE_KEY,
    )

    response_text = response.choices[0].message.content or ""
    enrichment = parse_enrichment_json(response_text)

    return {**finding, **enrichment}


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate finding card enrichment (9-element commercial loop) "
            "for each audit finding."
        )
    )
    parser.add_argument("slug", help="Audit slug, e.g. homedepot-mexico")
    parser.add_argument("workspace_dir", help="Path to the workspace directory")
    args = parser.parse_args()

    slug = args.slug
    workspace_dir = os.path.expanduser(args.workspace_dir)

    # Resolve paths
    research_dir = os.path.join(workspace_dir, "research")
    data_path = os.path.join(
        workspace_dir, "deliverables", f"{slug}-audit-data.json"
    )

    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    # Validate paths
    if not os.path.isdir(research_dir):
        print(f"ERROR: research_dir not found: {research_dir}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(data_path):
        print(f"ERROR: audit data JSON not found: {data_path}", file=sys.stderr)
        sys.exit(1)

    # Load research files
    print(f"Loading research files from: {research_dir}")
    research = load_research_files(research_dir)
    print(f"  Loaded {len(research)} of {len(RESEARCH_FILE_MAP)} research files.")

    # Load audit data
    print(f"Loading audit data from: {data_path}")
    with open(data_path, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    findings: list[dict] = audit_data.get("findings", [])
    if not findings:
        print("WARNING: No findings found in audit data JSON.", file=sys.stderr)
        sys.exit(0)

    print(f"Found {len(findings)} finding(s) to enrich.")

    # Initialise OpenAI client
    client = OpenAI(api_key=api_key)

    # Enrich each finding
    enriched_findings: list[dict] = []
    for i, finding in enumerate(findings, start=1):
        fid = finding.get("id", f"F{i:02d}")
        ftitle = finding.get("title", "Untitled")
        print(f"  [{i}/{len(findings)}] Enriching {fid}: {ftitle} ...", end=" ", flush=True)
        try:
            enriched = enrich_finding(finding, research, client)
            enriched_findings.append(enriched)
            print("OK")
        except Exception as e:
            print(f"FAILED — {e}", file=sys.stderr)
            # Keep original finding without enrichment so we don't lose data
            enriched_findings.append(finding)

    # Patch audit data and write back
    audit_data["findings"] = enriched_findings
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)

    print(f"\nPatched {len(enriched_findings)} finding(s) -> {data_path}")

    # Validate schema gate (if validate-json-schema.py is present)
    validator_path = os.path.join(os.path.dirname(__file__), "validate-json-schema.py")
    if os.path.isfile(validator_path):
        import subprocess
        deliverables_dir = os.path.join(workspace_dir, "deliverables")
        result = subprocess.run(
            ["python3", validator_path, slug],
            capture_output=True,
            text=True,
            cwd=deliverables_dir,
        )
        if result.returncode == 0:
            print("Schema validation: PASS")
        else:
            print(
                f"Schema validation: FAIL\n{result.stdout}\n{result.stderr}",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        print("Schema validator not found — skipping schema gate.")


if __name__ == "__main__":
    main()
