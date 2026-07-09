#!/usr/bin/env python3
"""Sync the canonical audit-data.json into the live-served index.html's embedded
window.AUDIT_DATA blob. This is the mandatory last step after ANY change to a
company's audit-data.json — the live page (/opt/PRISM/v1/{company}/index.html)
bakes its data in as a static JS object, and drifts silently otherwise.

Root cause this exists: on 2026-07-09, Lululemon's audit-data.json was fixed
5 separate times (traffic, tech_stack, executives/citations, industry_context,
solution map) and the live page was only manually re-synced once, days into the
fix cycle — every fix before that sync point was live in the canonical data but
invisible on the actual served page. This script makes that sync deterministic
and one-command instead of a thing to remember.

Usage:
    python3 sync-live-page.py <company-slug>
    python3 sync-live-page.py --all   # syncs every company found under /opt/PRISM/v1

Exit 0 = synced (or already in sync). Exit 1 = error (missing file, parse failure).
Exit 2 = one or more companies skipped (reported, not silently dropped).
"""
import json
import sys
import os
import shutil
from datetime import datetime

CANONICAL_DIR = "/opt/prism-executor/audits"
LIVE_DIR = "/opt/PRISM/v1"


def sync_one(slug, quiet=False):
    canonical_path = os.path.join(CANONICAL_DIR, slug, "deliverables", f"{slug}-audit-data.json")
    live_path = os.path.join(LIVE_DIR, slug, "index.html")

    if not os.path.exists(canonical_path):
        print(f"[{slug}] SKIP — no canonical audit-data.json at {canonical_path}")
        return "skip"
    if not os.path.exists(live_path):
        print(f"[{slug}] SKIP — no live index.html at {live_path}")
        return "skip"

    canonical = json.load(open(canonical_path, encoding="utf-8"))
    html = open(live_path, encoding="utf-8").read()

    marker = "window.AUDIT_DATA = {"
    if marker not in html or "};</script>" not in html:
        print(f"[{slug}] SKIP — live page has no window.AUDIT_DATA blob (not this template)")
        return "skip"

    s = html.index(marker) + len("window.AUDIT_DATA = ")
    e = html.index("};</script>") + 1
    current_live = json.loads(html[s:e])

    if current_live == canonical:
        if not quiet:
            print(f"[{slug}] already in sync — no changes")
        return "in_sync"

    new_blob = json.dumps(canonical, indent=2)
    new_html = html[:s] + new_blob + html[e:]

    # sanity check the replacement parses before writing anything
    s2 = new_html.index(marker) + len("window.AUDIT_DATA = ")
    e2 = new_html.index("};</script>") + 1
    json.loads(new_html[s2:e2])

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"{live_path}.bak-sync-{stamp}"
    shutil.copy2(live_path, backup_path)
    with open(live_path, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"[{slug}] SYNCED — canonical data written to live page (backup: {os.path.basename(backup_path)})")
    return "synced"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--all":
        slugs = sorted(
            d for d in os.listdir(LIVE_DIR)
            if os.path.isdir(os.path.join(LIVE_DIR, d)) and not d.startswith(".")
        )
        results = {s: sync_one(s) for s in slugs}
        skipped = [s for s, r in results.items() if r == "skip"]
        if skipped:
            print(f"\n{len(skipped)} companies skipped (see above) — not silently dropped: {skipped}")
            sys.exit(2)
        sys.exit(0)
    else:
        result = sync_one(sys.argv[1])
        sys.exit(0 if result != "skip" else 1)


if __name__ == "__main__":
    main()
