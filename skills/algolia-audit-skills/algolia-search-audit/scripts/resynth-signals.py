#!/usr/bin/env python3
"""resynth-signals.py — standalone sales-signal re-synthesis post-processor.

Lifted verbatim from generate-audit-data.py (synthesize_signals + helpers +
data tables + the media-quote lift logic) so a portfolio of already-rendered
audit-data.json files can be re-synthesized IN PLACE without re-running the
full generate step.

USAGE:
    python3 resynth-signals.py <path-to-audit-data.json>

Behaviour:
    - Loads the JSON.
    - If investor.media_quotes[] is present, lifts any not-yet-lifted quotes
      into intelligence_signals[] (idempotent: skips ones already lifted).
    - Runs the deterministic synthesis pass over intelligence_signals[]:
        SCORE (urgency_score + category_tag) -> DEDUPE/MERGE same-speaker
        quotes -> WHY_LEAD one-liner -> drop placeholder fields -> guarantee
        display/schema fields.
    - Writes the JSON back to the same path.

Idempotent: a second run over already-synthesized data is a no-op.
Stdlib only. No side effects beyond the target file.
"""

import json
import os
import re
import sys


def log(msg):
    print(f'  [resynth-signals] {msg}', flush=True)


# ── MEDIA QUOTES lifter ───────────────────────────────────────────────────────
# UI-chrome / non-quote fragments that scrapers pick up from LinkedIn, YouTube,
# comment threads and author bios. A "quote" containing any of these is not a real
# statement — drop it (conservative, deterministic; only obvious boilerplate).
MEDIA_QUOTE_JUNK_MARKERS = (
    'agree & join linkedin',
    'by clicking continue',
    'report this comment',
    'user agreement, privacy policy',
    'sign in to view',
    'about the author',
    "it's not everyday that you get to ask",
)


def _lift_one_media_quote(mq):
    """Turn one raw media_quotes[] entry into a signal-shaped dict, or return
    None if it is a placeholder / junk entry that should be skipped.

    Skips entries where:
      - source_url is null / empty
      - quote is '[COLLECT_VIA_SKILL]' or empty
      - quote is obvious UI-chrome / boilerplate (MEDIA_QUOTE_JUNK_MARKERS)
    """
    source_url = mq.get('source_url') or ''
    quote = mq.get('quote') or ''
    if not source_url.strip():
        return None
    if quote.strip() in ('', '[COLLECT_VIA_SKILL]'):
        return None
    if any(marker in quote.lower() for marker in MEDIA_QUOTE_JUNK_MARKERS):
        return None

    speaker = mq.get('speaker', '')
    speaker_title = mq.get('title', '')
    return {
        'type': 'media_quote',
        # Speaker kept as first-class fields so the synthesis step can group
        # multiple statements from the SAME person into one signal (see
        # dedupe_merge_signals). Without these, per-speaker merge is impossible.
        'speaker': speaker,
        'speaker_title': speaker_title,
        # Canonical fields the template reads (badge_label->title, signal->body,
        # algolia_angle->Algolia angle)
        'badge_label': f"{speaker}, {speaker_title}".strip(', ') if speaker else speaker_title,
        'signal': quote[:120],
        'algolia_angle': mq.get('context', '') or mq.get('algolia_relevance', ''),
        # Preserved originals for source attribution
        'source_url': source_url,
        'source_name': mq.get('publication', ''),
        'source_date': mq.get('source_date', ''),
        'confidence': mq.get('confidence', 'FACT'),
        'label': mq.get('label', ''),
        # Marker so a re-run can tell this signal came from investor.media_quotes
        # (idempotency: never lift the same media quote twice).
        '_from_media_quote': True,
    }


def _existing_media_source_urls(signals):
    """Collect every source_url already represented in intelligence_signals[],
    including those nested inside merged sub_quotes[]. Used to avoid re-lifting a
    media quote that a prior run already merged in."""
    seen = set()
    for sig in signals:
        u = (sig.get('source_url') or '').strip()
        if u:
            seen.add(u)
        for sq in sig.get('sub_quotes', []) or []:
            su = (sq.get('source_url') or '').strip()
            if su:
                seen.add(su)
    return seen


def lift_media_quotes_into(signals, media_quotes):
    """Lift investor.media_quotes[] into intelligence_signals[] IN a returned
    new list. Idempotent: a media quote whose source_url is already present in
    signals (top-level or in a merged sub_quotes[]) is skipped, so re-running
    never duplicates. Order: existing signals first, then newly lifted quotes."""
    if not media_quotes:
        return list(signals)
    already = _existing_media_source_urls(signals)
    lifted, skipped = [], 0
    for mq in media_quotes:
        sig = _lift_one_media_quote(mq)
        if sig is None:
            skipped += 1
            continue
        if (sig.get('source_url') or '').strip() in already:
            skipped += 1  # already lifted in a prior run — idempotent skip
            continue
        lifted.append(sig)
    if lifted:
        log(f'media_quotes: {len(lifted)} lifted into intelligence_signals'
            + (f', {skipped} skipped (placeholder/junk/already-lifted)' if skipped else ''))
    elif skipped:
        log(f'media_quotes: 0 new lifted, {skipped} skipped (placeholder/junk/already-lifted)')
    return list(signals) + lifted


# ── SIGNAL ENRICHMENT (SCORE) ────────────────────────────────────────────────

URGENCY_BY_TYPE = {
    'earnings_quote': 8,
    'media_quote':    6,
    'sec_risk':       7,
    'hiring':         7,
    'hiring_signal':  7,
    'funding':        8,
    'news_signal':    5,
    'social_signal':  4,
    'media':          6,
    'competitor':     7,
    'partner':        6,
    'exec':           8,
    'industry-opp':   6,
    'industry-risk':  5,
    'customer':       7,
}

CATEGORY_KEYWORDS = {
    'ai_disruption':          ['ai', 'artificial intelligence', 'machine learning', 'neural', 'generative', 'llm', 'chatgpt'],
    'digital_transformation': ['digital', 'ecommerce', 'online', 'dtc', 'd2c', 'direct-to-consumer', 'website', 'platform'],
    'cost_pressure':          ['revenue', 'decline', 'margin', 'cost', 'layoff', 'restructure', 'tariff', 'headwind'],
    'leadership_change':      ['ceo', 'cto', 'cio', 'coo', 'cmo', 'president', 'appoint', 'hire', 'depart', 'resign', 'exit'],
    'competitive_threat':     ['competitor', 'adidas', 'puma', 'under armour', 'asics', 'market share', 'losing'],
    'tech_investment':        ['invest', 'platform', 'technology', 'infrastructure', 'moderniz', 'upgrade', 'cloud'],
    'expansion':              ['launch', 'expand', 'market', 'international', 'new product', 'growth'],
}


def _kw_hit(kw, text):
    """True if keyword-stem kw appears at a word start in text. Start-boundary
    only, so 'ai' matches 'ai'/'ai-native' but NOT 'chairman'/'email', while
    prefixes like 'moderniz'/'appoint' still match their inflected forms."""
    return re.search(r'\b' + re.escape(kw), text) is not None


def enrich_signals(signals):
    """Add urgency_score, category_tag to each signal. Non-destructive — preserves existing fields."""
    if not signals:
        return signals
    for sig in signals:
        sig_type = (sig.get('type') or '').lower()
        text = ' '.join(filter(None, [
            sig.get('text', ''), sig.get('body', ''), sig.get('signal', ''),
            sig.get('relevance', ''), sig.get('badge_label', ''),
            sig.get('headline', ''), sig.get('description', ''),
            sig.get('context', ''), sig.get('quote', ''),
            sig.get('title', ''),
        ])).lower()

        # urgency_score — start from type-based default, boost for high-value keywords.
        # _kw_hit uses a start word-boundary so short stems ('ai') do not falsely
        # match inside longer words ('ch-ai-rman') while prefixes ('moderniz',
        # 'appoint') still match their inflections.
        score = URGENCY_BY_TYPE.get(sig_type, 5)
        if any(_kw_hit(w, text) for w in ['leadership', 'ceo', 'cto', 'cio', 'appoint', 'depart', 'resign']):
            score = min(10, score + 2)
        if any(_kw_hit(w, text) for w in ['funding', 'acquisition', 'merger', 'ipo']):
            score = min(10, score + 1)
        if not sig.get('urgency_score'):
            sig['urgency_score'] = score

        # category_tag
        if not sig.get('category_tag'):
            matched = 'strategic_signal'
            for cat, keywords in CATEGORY_KEYWORDS.items():
                if any(_kw_hit(kw, text) for kw in keywords):
                    matched = cat
                    break
            sig['category_tag'] = matched

    return signals


# ── SALES-SIGNAL SYNTHESIS ────────────────────────────────────────────────────

# Values that mean "no data" — never emitted as a field value.
_PLACEHOLDER_VALUES = {
    '', '-', '--', '—', '–', 'n/a', 'na', 'null', 'none', 'tbd', 'todo',
    '[collect_via_skill]', '[collect]', 'unknown', '?',
}

# Quote-type signals are the only ones grouped by speaker (an exec making 5
# statements = ONE priority, not 5 signals). Event signals (news/hiring/etc.)
# each stand alone and are never merged.
_QUOTE_TYPES = {'media_quote', 'earnings_quote', 'executive_quote', 'exec', 'media'}

# category_tag → short human label used to synthesize a grouped headline.
CATEGORY_LABEL = {
    'ai_disruption':          'AI',
    'digital_transformation': 'digital transformation',
    'cost_pressure':          'cost & margin',
    'leadership_change':      'leadership change',
    'competitive_threat':     'competitive',
    'tech_investment':        'tech investment',
    'expansion':              'expansion',
    'strategic_signal':       'strategic',
}

# why_lead: the AE's reason to open with this signal. Category first, type fallback.
WHY_LEAD_BY_CATEGORY = {
    'ai_disruption':          'AI is a stated exec priority — lead with Algolia as the AI-native search layer that ships this quarter.',
    'digital_transformation': 'Digital/DTC is the growth bet — lead with search as the conversion lever on the site they are already investing in.',
    'cost_pressure':          'Margin pressure is on record — lead with ROI-positive search that pays back in under a quarter, no re-platform.',
    'leadership_change':      'New leadership resets the budget cycle — lead now, before status-quo tools get re-committed.',
    'competitive_threat':     'A competitor is named as a threat — lead with the head-to-head search-experience gap.',
    'tech_investment':        'Tech investment is confirmed — lead with Algolia as the search modernization layer with immediate ROI.',
    'expansion':              'Expansion/launch is underway — lead with search that scales across new markets and catalog.',
    'strategic_signal':       'A live strategic signal — lead with how Algolia advances the stated priority.',
}
WHY_LEAD_BY_TYPE = {
    'hiring':        'Open ICP roles signal budget and ownership — lead with the team being built to own search/discovery.',
    'hiring_signal': 'Open ICP roles signal budget and ownership — lead with the team being built to own search/discovery.',
    'news_signal':   'A fresh, dated event — lead with the timing window it opens.',
    'competitor':    'A competitor uses or lacks modern search — lead with the head-to-head gap.',
    'partner':       'A warm partner path exists — lead with the co-sell introduction.',
}


def _is_placeholder(value):
    return isinstance(value, str) and value.strip().lower() in _PLACEHOLDER_VALUES


def drop_placeholder_fields(sig):
    """Return a copy of sig with empty / placeholder string fields removed
    (no bare '—' angle entries). None values and placeholders are dropped;
    numbers, lists and dicts are kept as-is."""
    return {
        k: v for k, v in sig.items()
        if v is not None and not _is_placeholder(v)
    }


def _signal_body(sig):
    """The strongest human-readable body text in a signal, for emptiness checks."""
    for k in ('signal', 'text', 'body', 'headline', 'badge_label', 'quote', 'title', 'relevance'):
        v = sig.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ''


def _ensure_display_fields(sig):
    """Guarantee every signal carries the fields the renderer AND schema need:
      - `text`  — render-audit.ts reads sig.text for hiring/news bars (backfill from signal).
      - `badge_label` — audit_data_schema requires one of title/signal/badge_label/detail;
                        text-only hiring signals would otherwise fail validation.
    Backfill only — never overwrites an existing value."""
    if not sig.get('text') and sig.get('signal'):
        sig['text'] = sig['signal']
    if not sig.get('badge_label'):
        for k in ('title', 'signal', 'text', 'headline'):
            v = sig.get(k)
            if isinstance(v, str) and v.strip():
                sig['badge_label'] = v.strip()[:120]
                break
    return sig


def _short_role(title):
    """Extract a compact role token (CEO/CTO/CIO/…) from a free-text title."""
    t = (title or '').lower()
    for role, needles in (
        ('CEO',       ('chief executive', 'ceo')),
        ('CTO',       ('chief technology', 'chief ai', 'cto')),
        ('CIO',       ('chief information', 'chief digital', 'cio', 'cdo')),
        ('CFO',       ('chief financial', 'cfo')),
        ('COO',       ('chief operating', 'co-coo', 'coo')),
        ('Chairman',  ('chairman',)),
        ('President', ('president',)),
        ('VP',        ('vice president', 'vp ', ' svp', ' evp')),
    ):
        if any(n in t for n in needles):
            return role
    return 'Exec'


def build_why_lead(sig):
    """One concise line: why an AE leads with this signal. Deterministic —
    category_tag first, then signal type, then a safe generic."""
    cat = (sig.get('category_tag') or '').lower()
    if cat in WHY_LEAD_BY_CATEGORY:
        return WHY_LEAD_BY_CATEGORY[cat]
    stype = (sig.get('type') or '').lower()
    if stype in WHY_LEAD_BY_TYPE:
        return WHY_LEAD_BY_TYPE[stype]
    return 'A live buying signal — lead with how it maps to an Algolia search win.'


def dedupe_merge_signals(signals):
    """Collapse quote signals from the SAME speaker into ONE grouped signal.

    Conservative + deterministic: only signals whose type is in _QUOTE_TYPES and
    that carry a non-empty `speaker` are grouped. Everything else (news, hiring,
    competitor, partner, unattributed quotes) passes through untouched, order
    preserved. Within a speaker group:
      - the highest-urgency member becomes the primary (its angle/source lead),
      - a synthesized headline is written: "<role>: <category> priority",
      - every member quote is preserved under sub_quotes[],
      - urgency_score = max member score, merged_count = group size.
    A speaker with only ONE quote is left as a plain signal (no forced grouping).
    """
    if not signals:
        return signals

    groups = {}          # speaker_key -> [members]
    group_order = []     # first-seen order of speaker_keys
    passthrough = []     # (index, signal) for non-grouped signals

    for idx, sig in enumerate(signals):
        stype = (sig.get('type') or '').lower()
        speaker = (sig.get('speaker') or '').strip()
        if stype in _QUOTE_TYPES and speaker:
            key = speaker.lower()
            if key not in groups:
                groups[key] = []
                group_order.append((idx, key))
            groups[key].append(sig)
        else:
            passthrough.append((idx, sig))

    merged_by_first_idx = {}
    for first_idx, key in group_order:
        members = groups[key]
        if len(members) == 1:
            merged_by_first_idx[first_idx] = members[0]
            continue

        primary = max(members, key=lambda s: s.get('urgency_score') or 0)
        merged = dict(primary)

        title = primary.get('speaker_title') or primary.get('title') or ''
        role = _short_role(title)
        cat_label = CATEGORY_LABEL.get(primary.get('category_tag', ''), 'strategic')
        speaker_name = primary.get('speaker', '')

        merged['badge_label'] = f"{role}: {cat_label} priority ({len(members)} sourced statements)"
        merged['merged_count'] = len(members)
        merged['urgency_score'] = max((s.get('urgency_score') or 0) for s in members)
        merged['sub_quotes'] = [
            drop_placeholder_fields({
                'speaker': m.get('speaker', speaker_name),
                'quote': (m.get('quote') or m.get('signal') or m.get('text') or '').strip(),
                'source_url': m.get('source_url', ''),
                'source_name': m.get('source_name') or m.get('publication', ''),
                'source_date': m.get('source_date') or m.get('date', ''),
            })
            for m in members
            if (m.get('quote') or m.get('signal') or m.get('text') or '').strip()
        ]
        merged_by_first_idx[first_idx] = merged

    # Reassemble by original index: grouped signals land at their first-seen
    # position, passthrough signals keep their slots — stable, predictable order.
    passthrough_indexed = sorted(passthrough, key=lambda t: t[0])
    group_first_indexed = sorted(merged_by_first_idx.items(), key=lambda t: t[0])
    combined = []
    gi = gp = 0
    while gi < len(group_first_indexed) or gp < len(passthrough_indexed):
        next_group_idx = group_first_indexed[gi][0] if gi < len(group_first_indexed) else float('inf')
        next_pass_idx = passthrough_indexed[gp][0] if gp < len(passthrough_indexed) else float('inf')
        if next_group_idx <= next_pass_idx:
            combined.append(group_first_indexed[gi][1])
            gi += 1
        else:
            combined.append(passthrough_indexed[gp][1])
            gp += 1
    return combined


def synthesize_signals(signals):
    """The full deterministic sales-signal synthesis pass (steps 2-4 + cleanup).
    GATHER (step 1) happens upstream; this runs on the collated array.
    Idempotent: safe to re-run over already-synthesized data."""
    if not signals:
        return signals

    # cleanup — drop empty / placeholder fields, then drop bodyless signals
    cleaned = [drop_placeholder_fields(s) for s in signals]
    cleaned = [s for s in cleaned if _signal_body(s)]

    # step 2 — score + category
    cleaned = enrich_signals(cleaned)

    # step 3 — dedupe/merge same-speaker quote signals
    cleaned = dedupe_merge_signals(cleaned)

    # merged signals inherit urgency_score already; re-run enrich only to fill any gaps
    cleaned = enrich_signals(cleaned)

    # step 4 — why_lead one-liner per signal + guarantee display/schema fields
    for s in cleaned:
        s['why_lead'] = build_why_lead(s)
        _ensure_display_fields(s)

    return cleaned


# ── MAIN ──────────────────────────────────────────────────────────────────────

def resynth(data):
    """Apply the full re-synthesis to an in-memory audit-data dict, IN PLACE.
    Returns (before_count, after_count)."""
    signals = data.get('intelligence_signals') or []
    before = len(signals)

    # Lift investor.media_quotes[] (idempotent) before synthesis so same-speaker
    # media + earnings quotes group together.
    investor = data.get('investor')
    if isinstance(investor, dict):
        media_quotes = investor.get('media_quotes') or []
        if media_quotes:
            signals = lift_media_quotes_into(signals, media_quotes)

    synthesized = synthesize_signals(signals)
    data['intelligence_signals'] = synthesized
    return before, len(synthesized)


def main():
    if len(sys.argv) != 2:
        print('Usage: python3 resynth-signals.py <path-to-audit-data.json>', file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f'error: file not found: {path}', file=sys.stderr)
        sys.exit(1)

    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f'error: could not read/parse {path} — {e}', file=sys.stderr)
        sys.exit(1)

    before, after = resynth(data)

    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')
    except OSError as e:
        print(f'error: could not write {path} — {e}', file=sys.stderr)
        sys.exit(1)

    log(f'{os.path.basename(path)}: intelligence_signals {before} -> {after} '
        f'(synthesized in place)')


if __name__ == '__main__':
    main()
