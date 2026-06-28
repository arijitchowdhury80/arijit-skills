#!/usr/bin/env python3
"""migrate-audit-data.py — bring an older/drifted audit-data.json up to the latest
canonical schema (audit_data_schema.py) deterministically, so it re-renders in the
current format. NO LLM. Idempotent. Fixes the mechanical violation classes seen across
the May-13-era reports; flags the few genuinely-missing-content cases for review.

Usage:  python3 migrate-audit-data.py <slug>-audit-data.json [--write]
        (default = dry-run: prints the changes; --write saves in place after a .bak)

What it fixes (all deterministic):
  - findings[].severity         HIGH/high→critical, MEDIUM/medium→moderate, LOW/low→positive
  - intelligence_signals[].type alias→canonical (media→media_quote, traffic_signal→industry, …)
  - score.breakdown keys        old→canonical (empty_state→query_suggestions_empty_state, …)
  - abx_sequence.touches[].day   int→str; missing→derived from sequence
  - abx_sequence.touches[].channel  loom→video; lowercased
  - abx_sequence.touches[].body  strip internal "Source notes:" tail (sendable copy only)
  - icp_mapping.priority_to_product[]  reverse alias-fill (pain↔their_priority, product↔algolia_solution)

Flags (NOT auto-fixed — genuinely missing content; reported, item left for module-fill/review):
  - abx touch with empty body
  - strategic_angles[] missing algolia_proof
"""
import json
import re
import sys

VALID_SIGNAL_TYPES = {
    "competitor", "digital_transformation", "earnings_quote", "exec", "expansion",
    "funding", "hiring", "hiring_signal", "industry", "industry-opp", "industry-risk",
    "leadership", "media_quote", "news", "news_signal", "partner", "regulatory",
    "sec_risk", "social", "social_signal",
}
SIGNAL_TYPE_ALIASES = {
    "media": "media_quote", "media_signal": "media_quote", "press": "media_quote",
    "traffic_signal": "industry", "traffic": "industry",
    "earnings": "earnings_quote", "quote": "media_quote",
    "sec": "sec_risk", "risk": "sec_risk", "exec_quote": "exec",
    "news_event": "news_signal", "hiring_event": "hiring_signal",
}
SEVERITY_ALIASES = {
    "high": "critical", "medium": "moderate", "low": "positive",
    "critical": "critical", "moderate": "moderate", "positive": "positive",
    "warning": "moderate", "info": "positive", "ok": "positive",
}
CANONICAL_SCORE_KEYS = {
    "latency", "typo_tolerance", "query_suggestions_empty_state", "intent_detection",
    "merchandising_consistency", "content_commerce_ux", "semantic_nlp_search",
    "dynamic_facets_personalization", "recommendations_merchandising", "search_intelligence",
}
SCORE_KEY_ALIASES = {
    "empty_state": "query_suggestions_empty_state",
    "query_suggestions": "query_suggestions_empty_state",
    "nlp_semantic": "semantic_nlp_search", "semantic": "semantic_nlp_search",
    "nlp": "semantic_nlp_search",
    "recommendations": "recommendations_merchandising", "recs": "recommendations_merchandising",
    "merchandising": "merchandising_consistency",
    "facets": "dynamic_facets_personalization", "personalization": "dynamic_facets_personalization",
    "content_commerce": "content_commerce_ux", "ux": "content_commerce_ux",
    "intent": "intent_detection", "typo": "typo_tolerance",
    # ambiguous — nearest-canonical (FLAGGED): SAYT≈suggestions, federated≈search-intelligence
    "sayt": "query_suggestions_empty_state", "federated_search": "search_intelligence",
    "federated": "search_intelligence",
}
CHANNEL_ALIASES = {"loom": "video", "vid": "video", "li": "linkedin", "mail": "email"}
DAY_BY_INDEX = ["1", "3", "5", "8", "11", "14", "18", "22", "26"]  # typical 9-touch cadence


def strip_source_notes(body: str) -> str:
    """Keep only the sendable copy: drop everything from a Source-notes marker onward,
    and unwrap a leading **Body:** label if present. Mirrors generate-abx-json.py."""
    if not isinstance(body, str):
        return body
    b = body
    m = re.search(r"(?im)^\s*\**\s*source\s*notes\s*:?", b)
    if m:
        b = b[: m.start()]
    b = re.sub(r"(?is)^\s*\**\s*body\s*:?\**\s*", "", b)  # unwrap leading **Body:**
    return b.strip()


def migrate(data: dict, log: list) -> dict:
    # findings severity
    for f in data.get("findings", []) or []:
        sev = f.get("severity")
        if isinstance(sev, str) and sev not in ("critical", "moderate", "positive"):
            new = SEVERITY_ALIASES.get(sev.strip().lower())
            if new and new != sev:
                log.append(f"findings.severity {sev!r}→{new!r}")
                f["severity"] = new

    # intelligence signal types
    for s in data.get("intelligence_signals", []) or []:
        t = s.get("type")
        if isinstance(t, str) and t not in VALID_SIGNAL_TYPES:
            new = SIGNAL_TYPE_ALIASES.get(t.strip().lower())
            if new:
                log.append(f"intelligence_signals.type {t!r}→{new!r}")
                s["type"] = new
            else:
                log.append(f"!! intelligence_signals.type {t!r} UNMAPPED (left as-is, will fail)")

    # score.breakdown keys
    sc = data.get("score", {})
    bd = sc.get("breakdown") if isinstance(sc, dict) else None
    if isinstance(bd, dict):
        for k in list(bd.keys()):
            if k not in CANONICAL_SCORE_KEYS:
                new = SCORE_KEY_ALIASES.get(k.strip().lower())
                if new and new not in bd:
                    log.append(f"score.breakdown key {k!r}→{new!r}"
                               + ("  [FLAG: nearest-canonical guess]" if k.lower() in ("sayt", "federated_search", "federated") else ""))
                    bd[new] = bd.pop(k)
                elif new:
                    log.append(f"score.breakdown key {k!r} drop (target {new!r} exists)")
                    bd.pop(k)
                else:
                    log.append(f"!! score.breakdown key {k!r} UNMAPPED")

    # icp_mapping alias-fill (older field names: priority/algolia_product/question)
    icp = data.get("icp_mapping", {})
    for p in (icp.get("priority_to_product", []) if isinstance(icp, dict) else []) or []:
        if not p.get("pain"):
            for alt in ("their_priority", "priority"):
                if p.get(alt):
                    p["pain"] = p[alt]; log.append(f"icp.pain ← {alt}"); break
        if not p.get("product"):
            for alt in ("algolia_solution", "algolia_product"):
                if p.get(alt):
                    p["product"] = p[alt]; log.append(f"icp.product ← {alt}"); break
        if not p.get("discovery_question") and p.get("question"):
            p["discovery_question"] = p["question"]; log.append("icp.discovery_question ← question")

    # case_studies alias-fill (older field name: stat→result)
    for cs in data.get("case_studies", []) or []:
        if not cs.get("result") and cs.get("stat"):
            cs["result"] = cs["stat"]; log.append("case_study.result ← stat")
        if not cs.get("product"):
            log.append(f"!! case_study[{cs.get('company','?')!r}] missing product (review)")
        if not cs.get("why"):
            log.append(f"!! case_study[{cs.get('company','?')!r}] missing why (review)")

    # abx touches: day, channel, body
    abx = data.get("abx_sequence", {})
    touches = abx.get("touches", []) if isinstance(abx, dict) else []
    keep = []
    for i, t in enumerate(touches or []):
        if "day" in t and not isinstance(t["day"], str):
            log.append(f"abx.touch[{i}].day {t['day']!r}→str"); t["day"] = str(t["day"])
        if not t.get("day"):
            t["day"] = DAY_BY_INDEX[i] if i < len(DAY_BY_INDEX) else str(i + 1)
            log.append(f"abx.touch[{i}].day filled→{t['day']}")
        # channel: extract the canonical enum from a possibly-descriptive string
        ch = t.get("channel")
        if isinstance(ch, str) and ch not in ("email", "linkedin", "video"):
            low = ch.strip().lower()
            if "linkedin" in low or low == "li":
                new = "linkedin"
            elif "email" in low or "mail" in low:
                new = "email"
            elif any(w in low for w in ("video", "loom", "demo", "call", "vid")):
                new = "video"
            else:
                new = CHANNEL_ALIASES.get(low, low)
            log.append(f"abx.touch[{i}].channel {ch!r}→{new!r}"); t["channel"] = new
        if isinstance(t.get("body"), str) and "source notes" in t["body"].lower():
            t["body"] = strip_source_notes(t["body"]); log.append(f"abx.touch[{i}].body stripped Source notes")
        # video touches: the Loom script belongs in video_script (old data kept it in body)
        if t.get("channel") == "video" and not (t.get("video_script") or "").strip() and (t.get("body") or "").strip():
            t["video_script"] = t["body"]; log.append(f"abx.touch[{i}].video_script ← body")
        # drop touches with no real body — empty/missing content can't be fabricated
        if not (t.get("body") or "").strip():
            log.append(f"abx.touch[{i}] ({t.get('channel')}) DROPPED — empty body")
            continue
        keep.append(t)
    if isinstance(abx, dict) and isinstance(abx.get("touches"), list):
        abx["touches"] = keep

    # flags: strategic_angles missing proof
    for a in data.get("strategic_angles", []) or []:
        if not a.get("algolia_proof"):
            log.append(f"!! strategic_angles[{a.get('label','?')!r}] missing algolia_proof (review)")

    return data


def main():
    if len(sys.argv) < 2:
        print("usage: migrate-audit-data.py <file.json> [--write]"); sys.exit(2)
    path = sys.argv[1]
    write = "--write" in sys.argv[2:]
    with open(path) as f:
        data = json.load(f)
    log: list = []
    migrate(data, log)
    flags = [m for m in log if m.startswith("!!")]
    fixes = [m for m in log if not m.startswith("!!")]
    print(f"== {path} ==")
    print(f"   {len(fixes)} deterministic fixes, {len(flags)} flags")
    for m in fixes:
        print("   ✓", m)
    for m in flags:
        print("  ", m)
    if write:
        import shutil
        shutil.copy(path, path + ".bak")
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"   WROTE {path} (backup {path}.bak)")


if __name__ == "__main__":
    main()
