# _archive — quarantined per-company browser forks

These ~22 scripts were **abandoned per-prospect forks** of `audit-browser.js` (BUG-6 in the
determinism survey, `D-skills-determinism-survey.md` §4). Each was hand-edited for one company
(The North Face, JBL, Dell, Home Depot México, Torrid, TheRealReal, …) because the original
`audit-browser.js` only supported typing into an on-page search box and could not handle:

- sites whose results page is reached by **URL navigation** (`/search?q=`) — the WAF/CAPTCHA-robust
  path (PerimeterX/Akamai trip on keystrokes, not on navigation),
- **per-site search selectors** (e.g. `#type-ahead-site-search-desktop`),
- **per-vertical query sets**,
- **cookie/CAPTCHA/modal dismissal**.

`audit-browser.js` is now **general-purpose**: all of those are parameters
(`--search-url-template`, `--mode url`, `--search-selector`, `--config <json>`, `--queries-file`).
A new prospect needs a small JSON config, **not** a new script. These forks are kept here only as a
historical record of the per-site quirks that informed the parameterization; nothing live calls them.

Live browser entry points (in the parent `scripts/` dir): `audit-browser.js`,
`collect-similarweb-browser.js`.
