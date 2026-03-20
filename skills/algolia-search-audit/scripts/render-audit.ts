#!/usr/bin/env deno run --allow-read --allow-write --allow-net
/**
 * Algolia Search Audit — Renderer
 * Version: 2.0
 * Usage:
 *   deno run --allow-read --allow-write render-audit.ts <company-slug> <mode>
 *
 * Modes:
 *   site         → index-template.html  → {slug}/index.html  (SPA — primary deliverable)
 *   binder       → book-template.html   → {slug}-book.html
 *   ae-report    → ae-action-report-template.html  → {slug}-ae-report.html
 *   battle-card  → strategic-battle-card-template.html → {slug}-battle-card.html
 *   leave-behind → prospect-leave-behind-template.html → {slug}-leave-behind.html
 *   all          → all modes above
 *
 * Example:
 *   deno run --allow-read --allow-write --allow-net render-audit.ts costco site
 *   deno run --allow-read --allow-write --allow-net render-audit.ts costco all
 */

import { join, dirname, fromFileUrl } from "https://deno.land/std@0.224.0/path/mod.ts";
import { ensureDir } from "https://deno.land/std@0.224.0/fs/mod.ts";

// ─── Constants ──────────────────────────────────────────────────────────────

const TEMPLATES_DIR = join(dirname(fromFileUrl(import.meta.url)), "..", "templates");
const BRAND_CSS_PATH = join(TEMPLATES_DIR, "algolia-brand.css");
const CRITICAL_TOKENS = ["COMPANY_NAME", "OVERALL_SCORE"];

// ─── Style Token Gate — blocks render if T token violations exist ────────────
function enforceStyleTokens(): void {
  const checkScript = join(dirname(fromFileUrl(import.meta.url)), "check-style-tokens.py");
  try {
    const result = new Deno.Command("python3", {
      args: [checkScript],
      stdout: "piped",
      stderr: "piped",
    }).outputSync();
    if (!result.success) {
      const out = new TextDecoder().decode(result.stdout);
      console.error("\n🚫 RENDER BLOCKED — Style token violations in index-template.html\n");
      console.error(out);
      console.error("Fix all violations before rendering. Use T.* tokens, not raw font-size values.\n");
      Deno.exit(1);
    }
  } catch {
    console.warn("⚠  check-style-tokens.py not found — skipping style gate");
  }
}

enforceStyleTokens();

// ─── JSON Schema Gate — blocks render if data keys don't match template ───────
// Called after slug is resolved (see below)
function enforceJsonSchema(slug: string): void {
  const validateScript = join(dirname(fromFileUrl(import.meta.url)), "validate-json-schema.py");
  try {
    const result = new Deno.Command("python3", {
      args: [validateScript, slug],
      stdout: "piped",
      stderr: "piped",
      cwd: Deno.cwd(),
    }).outputSync();
    if (!result.success) {
      const out = new TextDecoder().decode(result.stdout);
      console.error("\n🚫 RENDER BLOCKED — JSON schema violations\n");
      console.error(out);
      console.error("Fix key names to match what the template reads. Wrong keys render as blank sections.\n");
      Deno.exit(1);
    }
    const out = new TextDecoder().decode(result.stdout);
    console.log(out.trim());
  } catch {
    console.warn("⚠  validate-json-schema.py not found — skipping schema gate");
  }
}

// enforceJsonSchema called below after slug is defined

// ─── Load brand CSS (injected into every output HTML) ───────────────────────
function loadBrandCSS(): string {
  try {
    const css = Deno.readTextFileSync(BRAND_CSS_PATH);
    return `\n<!-- Algolia Brand CSS — edit algolia-brand.css to update all reports -->\n<style>\n${css}\n</style>\n`;
  } catch {
    console.warn(`⚠  algolia-brand.css not found at ${BRAND_CSS_PATH} — skipping brand injection`);
    return "";
  }
}

const BRAND_CSS_BLOCK = loadBrandCSS();

// Load Algolia brand mark PNG — Algolia-mark-blue.png lives one level above scripts/
const ALGOLIA_MARK_PNG = join(dirname(fromFileUrl(import.meta.url)), "..", "Algolia-mark-blue.png");

function _loadAlgoliaLogos(): { blue: string; white: string } {
  try {
    const pngBytes = Deno.readFileSync(ALGOLIA_MARK_PNG);
    let binary = "";
    for (let i = 0; i < pngBytes.length; i++) binary += String.fromCharCode(pngBytes[i]);
    const uri = `data:image/png;base64,${btoa(binary)}`;
    return { blue: uri, white: uri }; // CSS filter: brightness(0) invert(1) makes it white on dark backgrounds
  } catch {
    // Fallback: minimal SVG wordmark if PNG missing
    const mk = (fill: string) => `data:image/svg+xml;base64,${btoa(
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 148 36"><text x="2" y="28" ` +
      `font-family="Source Sans Pro,sans-serif" font-size="30" font-weight="900" fill="${fill}">algolia</text></svg>`
    )}`;
    console.warn(`⚠  Algolia-mark-blue.png not found at ${ALGOLIA_MARK_PNG} — using SVG fallback`);
    return { blue: mk("#003DFF"), white: mk("#FFFFFF") };
  }
}

const ALGOLIA_LOGOS = _loadAlgoliaLogos();
const b64Blue  = ALGOLIA_LOGOS.blue;
const b64White = ALGOLIA_LOGOS.white;

// Load a file from disk as a base64 data URI.
function loadFileAsDataUri(filePath: string, mime = "image/png"): string | null {
  try {
    const bytes = Deno.readFileSync(filePath);
    let binary = "";
    for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
    return `data:${mime};base64,${btoa(binary)}`;
  } catch {
    return null;
  }
}

// Fetch any remote URL and return a base64 data URI. Falls back to the original URL on error.
async function fetchAsDataUri(url: string): Promise<string> {
  try {
    const resp = await fetch(url, { signal: AbortSignal.timeout(8000) });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const contentType = resp.headers.get("content-type") || "image/png";
    const mimeBase = contentType.split(";")[0].trim();
    const buf = await resp.arrayBuffer();
    const bytes = new Uint8Array(buf);
    let binary = "";
    for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
    return `data:${mimeBase};base64,${btoa(binary)}`;
  } catch (e) {
    console.warn(`⚠  Could not fetch logo from ${url} — using URL directly (${e})`);
    return url;
  }
}

// ─── Types ───────────────────────────────────────────────────────────────────

interface AuditData {
  meta: {
    company: string;
    domain: string;
    audit_date: string;
    audited_by: string;
    version: string;
    data_vintage?: { similarweb?: string; builtwith?: string; yahoo_finance?: string };
  };
  cover: {
    photo_url: string;
    company_logo_url: string;
    status_line?: string;
  };
  score: {
    overall: number;
    verdict: string;
    verdict_class: "critical" | "moderate" | "ok";
    breakdown: Record<string, number>;
    critical_count: number;
    moderate_count: number;
    description?: string;
  };
  company_snapshot: {
    industry: string;
    hq?: string;
    employees?: string;
    revenue?: string;
    revenue_source?: string;
    revenue_source_label?: string;
    founded?: string;
    ticker?: string;
    current_search_vendor: string;
    ecommerce_platform?: string;
    monthly_visits: string;
    visits_source?: string;
  };
  executives?: Array<{
    name: string;
    title: string;
    quote: string;
    quote_source: string;
    quote_source_label?: string;
    quote_date: string;
    relevance?: string;
  }>;
  intelligence_signals?: Array<{
    type: string;
    badge_label: string;
    text: string;
    source_name?: string;
    source_url: string;
    source_date: string;
    relevance: string;
  }>;
  competitors?: Array<{
    name: string;
    domain: string;
    search_vendor?: string;
    monthly_traffic?: string;
    traffic_rank?: number;
    notes?: string;
  }>;
  findings: Array<{
    id: string;
    title: string;
    severity: "critical" | "moderate" | "positive";
    category: string;
    tested_query: string;
    expected_behavior?: string;
    actual_behavior: string;
    impact_stat?: string;
    impact_stat_source?: string;
    screenshot_file: string;
    prospect_description?: string;
    algolia_solution: string;
    algolia_case_study_url?: string;
    algolia_case_study_company?: string;
    algolia_case_study_result?: string;
  }>;
  gap_pairs?: Array<{
    said_quote: string;
    said_attr: string;
    said_source_url?: string;
    said_source_label?: string;
    said_date?: string;
    found_title: string;
    found_evidence: string;
  }>;
  toc?: Array<{
    act: string;
    sections: Array<{ title: string; anchor: string; page?: number }>;
  }>;
  financials?: {
    ticker?: string;
    market_cap?: string;
    revenue_3y?: Array<{ year: string; revenue: string }>;
    total_digital_revenue?: string;
    ecommerce_revenue_est?: string;
    search_roi_est?: string;
    search_addressable?: string;
    conservative_lift_label?: string;
    revenue_source?: string;
    revenue_source_label?: string;
  };
  tech_stack?: {
    ecommerce_platform?: string;
    cms?: string;
    search_provider?: string;
    personalization?: string;
    analytics?: string;
    tag_manager?: string;
    tech_stack_summary?: string;
    source_url?: string;
    headline?: string;
    takeaway?: string;
    vacuum_label?: string;
    vacuum_sublabel?: string;
    added?: string[];
    removed?: string[];
    ai_deployed?: string[];
    ai_absent?: string[];
  };
  traffic?: {
    monthly_visits?: string;
    visit_duration?: string;
    bounce_rate?: string;
    pages_per_visit?: string;
    top_channels?: Array<{ channel: string; share: string }>;
    source_url?: string;
    sources_breakdown?: Array<{ name: string; pct: number; color_class: string }>;
    demographics?: Array<{ age_group: string; pct: number; color: string }>;
  };
  ae_fields?: {
    ae_name?: string;
    ae_email?: string;
    next_step_action?: string;
    next_step_owner?: string;
    next_step_date?: string;
    urgency_level?: string;
    urgency_label?: string;
    urgency_color?: string;
    talk_track_opener?: string;
    talk_track_cta?: string;
    metric_1?: string;
    metric_2?: string;
    opportunity_headline?: string;
    benchmark_proof?: string;
    revenue_risk?: string;
    revenue_risk_desc?: string;
    the_ask_label?: string;
    the_ask_desc?: string;
    scorecard_headline?: string;
    scorecard_takeaway?: string;
    ai_gap_headline?: string;
    ai_gap_takeaway?: string;
    competitor_headline?: string;
    competitor_takeaway?: string;
    hiring_headline?: string;
    hiring_takeaway?: string;
    architecture_headline?: string;
    buyer_experience_label?: string;
    pilot_headline?: string;
    pilot_detail_headline?: string;
    pilot_takeaway?: string;
    pilot_scope_details?: string;
  };
  next_steps?: Array<{ step_num: number; title: string; description: string }>;
  methodology?: string;
  bibliography?: Array<{ n: number; label: string; url: string; accessed?: string }>;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function esc(s: unknown): string {
  if (s == null) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function s(val: unknown, fallback = "—"): string {
  if (val == null || val === "") return fallback;
  return esc(val);
}

function scoreColor(score: number): string {
  if (score < 4) return "#DC2626";   // red
  if (score < 6) return "#D97706";   // amber
  if (score < 8) return "#2563EB";   // blue
  return "#16A34A";                   // green
}

function verdictColor(cls: string): string {
  switch (cls) {
    case "critical": return "#DC2626";
    case "moderate": return "#D97706";
    case "ok":       return "#16A34A";
    default:         return "#6B7280";
  }
}

function formatLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, c => c.toUpperCase());
}

// ─── Dynamic HTML generators ─────────────────────────────────────────────────

function buildTocContent(data: AuditData): string {
  if (!data.toc || data.toc.length === 0) return "<p>No table of contents available.</p>";
  return data.toc.map(act => `
    <div class="toc__act">
      <div class="toc__act-title">${esc(act.act)}</div>
      ${act.sections.map(sec => `
        <div class="toc__entry">
          <a href="#${esc(sec.anchor)}">${esc(sec.title)}</a>
          ${sec.page ? `<span class="toc__page">${sec.page}</span>` : ""}
        </div>
      `).join("")}
    </div>
  `).join("\n");
}

function buildScoreBars(data: AuditData): string {
  const bd = data.score.breakdown;
  return Object.entries(bd).map(([key, val]) => {
    const pct = Math.round((val / 10) * 100);
    const color = scoreColor(val);
    return `
      <div class="score-bar-row">
        <span class="score-bar-label">${formatLabel(key)}</span>
        <div class="score-bar-track">
          <div class="score-bar-fill" style="width:${pct}%;background:${color}"></div>
        </div>
        <span class="score-bar-val" style="color:${color}">${val.toFixed(1)}</span>
      </div>`;
  }).join("\n");
}

function buildScoreHeatmap(data: AuditData): string {
  return buildScoreBars(data); // Same HTML, used interchangeably
}

function buildFindingCardsBinder(data: AuditData): string {
  return data.findings.map(f => {
    const sevColor = f.severity === "critical" ? "#DC2626" : f.severity === "moderate" ? "#D97706" : "#16A34A";
    const caseStudy = f.algolia_case_study_url
      ? `<a href="${esc(f.algolia_case_study_url)}" class="case-study-link" target="_blank">
           ${esc(f.algolia_case_study_company || "Case Study")} → ${esc(f.algolia_case_study_result || "See results")}
         </a>`
      : "";
    return `
    <div class="finding-section page-break" id="finding-${esc(f.id)}">
      <div class="page-header">
        <span>${esc(data.meta.company)} · ${esc(f.id)}: ${esc(f.title)}</span>
        <span class="finding-badge finding-badge--${esc(f.severity)}"
              style="background:${sevColor}">${esc(f.severity.toUpperCase())}</span>
      </div>
      <div class="finding-content">
        <div class="finding-meta">
          <span class="finding-category">${esc(f.category)}</span>
          <span class="finding-query">Query: "${esc(f.tested_query)}"</span>
        </div>
        <div class="finding-tef">
          <div class="tef-block">
            <div class="tef-label">TESTED</div>
            <div class="tef-body">${esc(f.tested_query)}</div>
          </div>
          <div class="tef-block">
            <div class="tef-label">EXPECTED</div>
            <div class="tef-body">${s(f.expected_behavior)}</div>
          </div>
          <div class="tef-block tef-block--found">
            <div class="tef-label">FOUND</div>
            <div class="tef-body">${esc(f.actual_behavior)}</div>
          </div>
        </div>
        ${f.screenshot_file
          ? `<div class="finding-screenshot">
               <img src="${esc(f.screenshot_file)}" alt="Screenshot: ${esc(f.title)}" loading="lazy" />
             </div>`
          : ""}
        ${f.impact_stat
          ? `<div class="impact-stat">
               <strong>${esc(f.impact_stat)}</strong>
               ${f.impact_stat_source ? `<a href="${esc(f.impact_stat_source)}" target="_blank" class="src-tag">source</a>` : ""}
             </div>`
          : ""}
        <div class="finding-solution">
          <div class="solution-label">ALGOLIA SOLUTION</div>
          <div class="solution-body">${esc(f.algolia_solution)}</div>
          ${caseStudy}
        </div>
      </div>
      <div class="page-footer">
        <span>${esc(data.meta.company)} Search Audit · Confidential</span>
        <img src="${b64Blue}" alt="Algolia" height="16" />
      </div>
    </div>`;
  }).join("\n");
}

function buildFindingCardsAE(data: AuditData): string {
  // AE report: top 3 critical findings as compact cards
  const top = data.findings
    .filter(f => f.severity === "critical")
    .slice(0, 3)
    .concat(data.findings.filter(f => f.severity === "moderate").slice(0, 3 - Math.min(3, data.findings.filter(f => f.severity === "critical").length)));
  const topThree = top.slice(0, 3);
  return topThree.map((f, i) => `
    <div class="finding-card finding-card--${esc(f.severity)}">
      <div class="finding-card__num">${i + 1}</div>
      <div class="finding-card__title">${esc(f.title)}</div>
      ${f.impact_stat ? `<div class="finding-card__stat">${esc(f.impact_stat)}</div>` : ""}
      <div class="finding-card__starter"><em>What to say:</em> "${esc(f.algolia_solution)}"</div>
    </div>`).join("\n");
}

function buildProspectFindingCards(data: AuditData): string {
  // Leave-behind: text-only, no screenshots, no internal intel
  // Uses finding-card__* classes matching prospect-leave-behind-template.html CSS
  return data.findings.map((f, i) => `
    <div class="finding-card">
      <div class="finding-card__num-col">
        <span class="finding-card__n">${i + 1}</span>
        <span class="finding-card__severity-dot dot--${esc(f.severity)}"></span>
      </div>
      <div class="finding-card__body">
        <div class="finding-card__category">${esc(f.challenge_area || f.severity.toUpperCase())}</div>
        <div class="finding-card__title">${esc(f.title)}</div>
        <div class="finding-card__desc">${esc(f.prospect_description || f.actual_behavior)}</div>
        ${f.impact_stat ? `<div class="finding-card__impact">
          <span class="finding-card__impact-stat">${esc(f.impact_stat)}</span>
        </div>` : ""}
        ${f.algolia_solution ? `<div class="finding-card__solution">
          <strong>Algolia solution:</strong> ${esc(f.algolia_solution)}
          ${f.algolia_case_study_url ? `<a href="${esc(f.algolia_case_study_url)}" target="_blank">Case study →</a>` : ""}
        </div>` : ""}
      </div>
    </div>`).join("\n");
}

function buildSignalCards(data: AuditData, maxCount?: number): string {
  const signals = maxCount
    ? (data.intelligence_signals || []).slice(0, maxCount)
    : (data.intelligence_signals || []);
  return signals.map(sig => `
    <div class="signal-card signal--${esc(sig.type)}">
      <div class="signal-card__header">
        <span class="signal-badge signal-badge--${esc(sig.type)}">${esc(sig.badge_label)}</span>
        <span class="signal-date">${esc(sig.source_date)}</span>
      </div>
      <div class="signal-card__text">${esc(sig.text)}</div>
      ${sig.source_name ? `<div class="signal-card__attr">— ${esc(sig.source_name)}</div>` : ""}
      <div class="signal-card__relevance">${esc(sig.relevance)}</div>
      <a href="${esc(sig.source_url)}" class="signal-card__src" target="_blank">Source →</a>
    </div>`).join("\n");
}

function buildGapPairs(data: AuditData): string {
  if (!data.gap_pairs || data.gap_pairs.length === 0) return "<p>No strategy gaps identified.</p>";
  return data.gap_pairs.map(gp => `
    <div class="gap-pair">
      <div class="gap-said">
        <div class="gap-said__label">THEY SAID</div>
        <blockquote class="gap-said__quote">"${esc(gp.said_quote)}"</blockquote>
        <div class="gap-said__attr">
          — ${esc(gp.said_attr)}
          ${gp.said_source_url
            ? `<a href="${esc(gp.said_source_url)}" target="_blank">${esc(gp.said_source_label || "source")}</a>`
            : ""}
          ${gp.said_date ? `· ${esc(gp.said_date)}` : ""}
        </div>
      </div>
      <div class="gap-arrow">→</div>
      <div class="gap-found">
        <div class="gap-found__label">WE FOUND</div>
        <div class="gap-found__title">${esc(gp.found_title)}</div>
        <div class="gap-found__evidence">${esc(gp.found_evidence)}</div>
      </div>
    </div>`).join("\n");
}

function buildFeatureComparisonRows(data: AuditData): string {
  const capabilityMap: Record<string, { vendor: string; algolia: string }> = {
    "Semantic Search":         { vendor: "❌ Keyword-only",            algolia: "✅ NLP + Vector search" },
    "No Results Handling":     { vendor: "❌ Empty page",              algolia: "✅ Fallback + suggestions" },
    "Personalization":         { vendor: "❌ None detected",           algolia: "✅ AI personalization" },
    "Facets & Filtering":      { vendor: "⚠️ Basic",                   algolia: "✅ Dynamic faceting" },
    "Type-ahead / SAYT":       { vendor: "⚠️ Text-only",               algolia: "✅ Visual + trending" },
    "Recommendations":         { vendor: "❌ None detected",           algolia: "✅ Recommend API" },
    "Analytics & Insights":    { vendor: "❓ Unknown",                 algolia: "✅ Query analytics dashboard" },
    "Performance":             { vendor: "⚠️ Varies",                  algolia: "✅ <1ms avg response" },
  };
  const vendorName = data.company_snapshot.current_search_vendor || "Current Vendor";
  const rows = Object.entries(capabilityMap).map(([cap, vals]) => {
    // Mark as tested if there's a finding in this category
    const tested = data.findings.some(f =>
      f.category.toLowerCase().includes(cap.toLowerCase().split(" ")[0])
    );
    return `
      <tr class="${tested ? "comparison-row--tested" : ""}">
        <td>${esc(cap)}${tested ? ' <span class="tested-badge">✓ tested</span>' : ""}</td>
        <td class="comp-vendor">${vals.vendor}</td>
        <td class="comp-algolia">${vals.algolia}</td>
      </tr>`;
  }).join("\n");
  return `
    <thead>
      <tr>
        <th>Capability</th>
        <th>${esc(vendorName)}</th>
        <th>Algolia</th>
      </tr>
    </thead>
    <tbody>${rows}</tbody>`;
}

function buildRevenue3yRows(data: AuditData): string {
  if (!data.financials?.revenue_3y) return "<tr><td colspan='2'>No data</td></tr>";
  return data.financials.revenue_3y.map(row => `
    <tr><td>${esc(row.year)}</td><td>${esc(row.revenue)}</td></tr>
  `).join("\n");
}

function buildNextSteps(data: AuditData): string {
  if (!data.next_steps || data.next_steps.length === 0) return "";
  return data.next_steps.map(ns => `
    <div class="next-step">
      <div class="next-step__num">${ns.step_num}</div>
      <div class="next-step__body">
        <div class="next-step__title">${esc(ns.title)}</div>
        <div class="next-step__desc">${esc(ns.description)}</div>
      </div>
    </div>`).join("\n");
}

function buildBibliography(data: AuditData): string {
  if (!data.bibliography || data.bibliography.length === 0) return "<p>No bibliography.</p>";
  return `<ol class="bibliography">` +
    data.bibliography.map(b =>
      `<li id="ref-${b.n}"><a href="${esc(b.url)}" target="_blank">${esc(b.label)}</a>${b.accessed ? ` — accessed ${esc(b.accessed)}` : ""}</li>`
    ).join("") +
    `</ol>`;
}

function buildCompetitorRows(data: AuditData): string {
  if (!data.competitors || data.competitors.length === 0) return "<tr><td colspan='5'>No competitor data</td></tr>";
  return data.competitors.map(c => `
    <tr>
      <td><a href="https://${esc(c.domain)}" target="_blank">${esc(c.name)}</a></td>
      <td>${s(c.search_vendor)}</td>
      <td>${s(c.monthly_traffic)}</td>
      <td>${c.traffic_rank ? `#${c.traffic_rank}` : "—"}</td>
      <td>${s(c.notes)}</td>
    </tr>`).join("\n");
}

// Compute SVG gauge dasharray + CSS class from score
function gaugeProps(score: number): { dasharray: string; colorClass: string; valueClass: string } {
  const circ = 283;
  const filled = (score / 10) * circ;
  const dasharray = `${filled.toFixed(1)} ${(circ - filled).toFixed(1)}`;
  let colorClass = "score-gauge__arc--critical";
  if (score >= 6) colorClass = "score-gauge__arc--good";
  else if (score >= 4) colorClass = "score-gauge__arc--moderate";
  const valueClass = colorClass.replace("__arc", "__value");
  return { dasharray, colorClass, valueClass };
}

// Compute SVG radar polygon points from score breakdown
function buildRadarPoints(data: AuditData, type: "expected" | "actual"): string {
  const bd = data.score.breakdown;
  const vals = Object.values(bd).slice(0, 5).map(v => Number(v) || 5);
  while (vals.length < 5) vals.push(5);
  const scores = type === "expected" ? vals.map(v => Math.min(v + 2.5, 10)) : vals;
  // Outer pentagon vertices for max score=10 (from SVG viewBox 300x300, center 150,150)
  const maxPts: [number, number][] = [[150,30],[252,95],[220,220],[80,220],[48,95]];
  return scores.map((score, i) => {
    const ratio = Math.max(0, Math.min(score, 10)) / 10;
    const x = (150 + (maxPts[i][0] - 150) * ratio).toFixed(1);
    const y = (150 + (maxPts[i][1] - 150) * ratio).toFixed(1);
    return `${x},${y}`;
  }).join(" ");
}

function buildLeadershipQuotes(data: AuditData): string {
  if (!data.executives || data.executives.length === 0) return "<p>No executive quotes available.</p>";
  return data.executives.map(e => `
    <div class="callout callout--quote mt-24">
      <blockquote class="callout__quote" style="font-style:italic;font-size:1.1rem;line-height:1.6;">"${esc(e.quote)}"</blockquote>
      <div class="callout__attr" style="margin-top:12px;font-weight:700;">— ${esc(e.name)}, ${esc(e.title)}</div>
      <div style="margin-top:6px;font-size:0.8rem;color:var(--dark-gray);">
        ${e.quote_date ? esc(e.quote_date) : ""}
        ${e.quote_source ? ` · <a href="${esc(e.quote_source)}" target="_blank" class="cite">[source]</a>` : ""}
      </div>
    </div>`).join("\n");
}

function buildExecCards(data: AuditData): string {
  if (!data.executives || data.executives.length === 0) return "<p>No executives identified.</p>";
  return data.executives.map(e => `
    <div class="exec-card" style="display:flex;gap:16px;padding:20px;background:var(--light-gray);border-radius:8px;margin-bottom:16px;">
      <div style="width:48px;height:48px;border-radius:50%;background:var(--nebula-blue);color:white;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:1.2rem;flex-shrink:0;">${esc(e.name.charAt(0).toUpperCase())}</div>
      <div>
        <div style="font-weight:700;">${esc(e.name)}</div>
        <div style="font-size:0.85rem;color:var(--dark-gray);">${esc(e.title)}</div>
        ${e.relevance ? `<div style="font-size:0.8rem;color:var(--nebula-blue);margin-top:4px;">${esc(e.relevance)}</div>` : ""}
      </div>
    </div>`).join("\n");
}

function buildStackBlocks(data: AuditData, type: "added" | "removed"): string {
  const items = type === "added" ? data.tech_stack?.added : data.tech_stack?.removed;
  if (!items || items.length === 0) {
    return `<div class="stack-block" style="background:var(--light-gray);padding:12px 16px;border-radius:6px;margin-bottom:8px;font-size:0.85rem;color:var(--dark-gray);">${type === "added" ? "No recent additions" : "No recent removals"}</div>`;
  }
  const cls = type === "added" ? "background:rgba(16,185,129,0.1);border-left:3px solid #10B981" : "background:rgba(220,38,38,0.1);border-left:3px solid #DC2626";
  return items.map(item =>
    `<div class="stack-block" style="${cls};padding:12px 16px;border-radius:0 6px 6px 0;margin-bottom:8px;">${esc(item)}</div>`
  ).join("\n");
}

function buildAIItems(data: AuditData, type: "deployed" | "absent"): string {
  const items = type === "deployed" ? data.tech_stack?.ai_deployed : data.tech_stack?.ai_absent;
  if (!items || items.length === 0) {
    const fallbacks = type === "deployed"
      ? ["Basic keyword matching", "Rule-based ranking"]
      : ["Semantic / NLP search", "AI personalization", "Predictive recommendations"];
    return `<ul style="padding-left:20px;margin:0;">${fallbacks.map(i => `<li style="margin-bottom:8px;">${esc(i)}</li>`).join("")}</ul>`;
  }
  return `<ul style="padding-left:20px;margin:0;">${items.map(i => `<li style="margin-bottom:8px;">${esc(i)}</li>`).join("")}</ul>`;
}

function buildCompetitorBarRows(data: AuditData): string {
  if (!data.competitors || data.competitors.length === 0) return "";
  const parseV = (v: string | undefined): number => {
    if (!v || v === "—") return 0;
    const n = parseFloat(v.replace(/[^\d.]/g, "")) || 0;
    if (v.includes("B")) return n * 1000;
    if (v.includes("M")) return n;
    if (v.includes("K")) return n / 1000;
    return n;
  };
  const all = [
    { name: data.meta.company, traffic: data.company_snapshot.monthly_visits, primary: true },
    ...data.competitors.map(c => ({ name: c.name, traffic: c.monthly_traffic ?? "—", primary: false })),
  ];
  const maxV = Math.max(...all.map(c => parseV(c.traffic)), 1);
  return all.map(c => {
    const pct = Math.round((parseV(c.traffic) / maxV) * 100);
    const fillCls = c.primary ? "bar-chart-h__fill--primary" : "bar-chart-h__fill--secondary";
    const hlCls = c.primary ? "font-weight:700;color:var(--nebula-blue)" : "";
    return `<div class="bar-chart-h__row" style="display:grid;grid-template-columns:120px 1fr 80px;gap:8px;align-items:center;margin-bottom:8px;">
      <div style="font-size:0.85rem;${hlCls}">${esc(c.name)}</div>
      <div style="height:8px;background:var(--light-gray);border-radius:4px;overflow:hidden;">
        <div class="${fillCls}" style="height:100%;width:${pct}%;background:${c.primary ? "var(--nebula-blue)" : "var(--algolia-purple)"};border-radius:4px;"></div>
      </div>
      <div style="font-size:0.85rem;text-align:right;${hlCls}">${esc(c.traffic)}</div>
    </div>`;
  }).join("\n");
}

function buildCompetitorDonut(data: AuditData): { dasharray: string; pct: string; label: string; description: string } {
  if (!data.competitors || data.competitors.length === 0) {
    return { dasharray: "0 251", pct: "0%", label: "Use Algolia", description: "No competitor data available" };
  }
  const withAlgolia = data.competitors.filter(c => c.search_vendor?.toLowerCase().includes("algolia")).length;
  const total = data.competitors.length;
  const pctNum = Math.round((withAlgolia / total) * 100);
  const circ = 251.33;
  const filled = (pctNum / 100) * circ;
  return {
    dasharray: `${filled.toFixed(1)} ${(circ - filled).toFixed(1)}`,
    pct: `${pctNum}%`,
    label: "Use Algolia",
    description: `${withAlgolia} of ${total} direct competitors use Algolia`,
  };
}

function buildHiringBarRows(data: AuditData): string {
  const hiringSignals = data.intelligence_signals?.filter(s => s.type === "hiring") ?? [];
  if (hiringSignals.length === 0) return `<p style="color:var(--dark-gray);font-size:0.9rem;">Hiring signal data not available.</p>`;
  const cats = [
    { label: "Engineering", kw: ["engineer","developer","software","backend","frontend","architect"] },
    { label: "Data & AI", kw: ["data","machine learning","ai ","ml ","analytics","intelligence"] },
    { label: "Product", kw: ["product manager","product owner","pm "] },
    { label: "Design / UX", kw: ["design","ux ","ui ","experience"] },
    { label: "Search / E-com", kw: ["search","ecommerce","commerce","merchandis"] },
  ];
  const text = hiringSignals.map(s => s.text.toLowerCase()).join(" ");
  const counts = cats.map(cat => ({ label: cat.label, count: cat.kw.filter(kw => text.includes(kw)).length * 3 + 2 }));
  const maxC = Math.max(...counts.map(c => c.count), 1);
  return counts.map(c => {
    const pct = Math.round((c.count / maxC) * 100);
    return `<div style="display:grid;grid-template-columns:120px 1fr 40px;gap:8px;align-items:center;margin-bottom:10px;">
      <div style="font-size:0.85rem;">${esc(c.label)}</div>
      <div style="height:8px;background:var(--light-gray);border-radius:4px;overflow:hidden;">
        <div style="height:100%;width:${pct}%;background:var(--nebula-blue);border-radius:4px;"></div>
      </div>
      <div style="font-size:0.8rem;color:var(--dark-gray);">${c.count}</div>
    </div>`;
  }).join("\n");
}

function buildHiringCallout(data: AuditData): string {
  const sig = data.intelligence_signals?.find(s => s.type === "hiring");
  if (!sig) return "";
  return `<div class="callout callout--insight" style="background:rgba(0,61,255,0.05);border-left:4px solid var(--nebula-blue);padding:20px;border-radius:0 8px 8px 0;">
    <div style="font-size:0.75rem;text-transform:uppercase;font-weight:700;color:var(--nebula-blue);margin-bottom:8px;">Hiring Signal</div>
    <p style="margin:0 0 8px;font-size:0.9rem;">${esc(sig.text)}</p>
    <a href="${esc(sig.source_url)}" class="cite" target="_blank" style="font-size:0.8rem;">${esc(sig.source_name ?? "Source")} →</a>
  </div>`;
}

function buildTrafficDonutSegments(data: AuditData): string {
  const sources = data.traffic?.sources_breakdown;
  const channels = data.traffic?.top_channels;
  const circ = 251.33;
  if (sources && sources.length > 0) {
    let offset = 0;
    return sources.map(src => {
      const len = (src.pct / 100) * circ;
      const seg = `<circle class="${esc(src.color_class)}" cx="50" cy="50" r="40" fill="none" stroke-width="16" stroke-dasharray="${len.toFixed(1)} ${(circ - len).toFixed(1)}" stroke-dashoffset="${(-offset).toFixed(1)}"/>`;
      offset += len;
      return seg;
    }).join("\n");
  }
  if (channels && channels.length > 0) {
    const colors = ["var(--nebula-blue)","var(--algolia-purple)","#10B981","#F59E0B","#6B7280"];
    let offset = 0;
    return channels.map((ch, i) => {
      const pct = parseFloat(String(ch.share).replace(/[^0-9.]/g, "")) || 0;
      const len = (pct / 100) * circ;
      const seg = `<circle cx="50" cy="50" r="40" fill="none" stroke="${colors[i % colors.length]}" stroke-width="16" stroke-dasharray="${len.toFixed(1)} ${(circ - len).toFixed(1)}" stroke-dashoffset="${(-offset).toFixed(1)}"/>`;
      offset += len;
      return seg;
    }).join("\n");
  }
  return `<circle cx="50" cy="50" r="40" fill="none" stroke="var(--nebula-blue)" stroke-width="16" stroke-dasharray="151 100"/>`;
}

function buildTrafficLegendItems(data: AuditData): string {
  const sources = data.traffic?.sources_breakdown;
  const channels = data.traffic?.top_channels;
  if (sources && sources.length > 0) {
    return sources.map(src => `
      <div class="donut-legend__item" style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <div style="width:12px;height:12px;border-radius:2px;" class="${esc(src.color_class)}"></div>
        <span style="font-size:0.85rem;">${esc(src.name)}</span>
        <span style="font-size:0.85rem;font-weight:700;margin-left:auto;">${src.pct}%</span>
      </div>`).join("\n");
  }
  if (channels && channels.length > 0) {
    const colors = ["#003DFF","#5468FF","#10B981","#F59E0B","#6B7280"];
    return channels.map((ch, i) => `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <div style="width:12px;height:12px;border-radius:2px;background:${colors[i % colors.length]}"></div>
        <span style="font-size:0.85rem;">${esc(ch.channel)}</span>
        <span style="font-size:0.85rem;font-weight:700;margin-left:auto;">${esc(String(ch.share))}</span>
      </div>`).join("\n");
  }
  return "";
}

function buildDemographicsPieSegments(data: AuditData): string {
  const demos = data.traffic?.demographics;
  if (!demos || demos.length === 0) return "";
  const cx = 50, cy = 50, r = 45;
  let startAngle = -90;
  return demos.map(d => {
    const angle = (d.pct / 100) * 360;
    const endAngle = startAngle + angle;
    const s = (startAngle * Math.PI) / 180;
    const e = (endAngle * Math.PI) / 180;
    const x1 = (cx + r * Math.cos(s)).toFixed(2);
    const y1 = (cy + r * Math.sin(s)).toFixed(2);
    const x2 = (cx + r * Math.cos(e)).toFixed(2);
    const y2 = (cy + r * Math.sin(e)).toFixed(2);
    const la = angle > 180 ? 1 : 0;
    const seg = `<path d="M ${cx},${cy} L ${x1},${y1} A ${r},${r} 0 ${la},1 ${x2},${y2} Z" fill="${esc(d.color)}"/>`;
    startAngle = endAngle;
    return seg;
  }).join("\n");
}

function buildDemographicsLegendItems(data: AuditData): string {
  const demos = data.traffic?.demographics;
  if (!demos || demos.length === 0) return "";
  return demos.map(d => `
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
      <div style="width:12px;height:12px;border-radius:50%;background:${esc(d.color)}"></div>
      <span style="font-size:0.85rem;">${esc(d.age_group)}</span>
      <span style="font-size:0.85rem;font-weight:700;margin-left:auto;">${d.pct}%</span>
    </div>`).join("\n");
}

function buildEngagementTableRows(data: AuditData): string {
  const t = data.traffic;
  if (!t) return "<tr><td colspan='4'>No traffic data</td></tr>";
  const rows: Array<{ m: string; v: string; avg: string; ok: boolean }> = [];
  if (t.visit_duration) rows.push({ m: "Visit Duration", v: t.visit_duration, avg: "2:45", ok: parseFloat(t.visit_duration) >= 2.5 });
  if (t.bounce_rate)    rows.push({ m: "Bounce Rate",    v: t.bounce_rate,    avg: "47%",  ok: parseFloat(t.bounce_rate) <= 47 });
  if (t.pages_per_visit) rows.push({ m: "Pages / Visit", v: t.pages_per_visit, avg: "4.2", ok: parseFloat(t.pages_per_visit) >= 4 });
  if (rows.length === 0) return "<tr><td colspan='4'>No engagement data</td></tr>";
  return rows.map(r => `<tr>
    <td>${esc(r.m)}</td><td>${esc(r.v)}</td><td>${esc(r.avg)}</td>
    <td style="color:${r.ok ? "#10B981" : "#D97706"}">${r.ok ? "✅ Above avg" : "⚠️ Below avg"}</td>
  </tr>`).join("\n");
}

function buildArchitectureBenefits(data: AuditData): string {
  const benefits = [
    { icon: `<svg viewBox="0 0 24 24" stroke-width="2" fill="none" stroke="white"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8"/></svg>`, title: "Speed", desc: "Sub-20ms response times across 100M+ records" },
    { icon: `<svg viewBox="0 0 24 24" stroke-width="2" fill="none" stroke="white"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>`, title: "Relevance", desc: `AI-powered ranking learns from ${esc(data.meta.company)} shopper behavior` },
    { icon: `<svg viewBox="0 0 24 24" stroke-width="2" fill="none" stroke="white"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>`, title: "Time to Value", desc: "Go live in 4 weeks with pre-built UI components and migration tools" },
  ];
  return benefits.map(b => `
    <div style="text-align:center;padding:24px;">
      <div style="width:56px;height:56px;border-radius:12px;background:var(--nebula-blue);display:flex;align-items:center;justify-content:center;margin:0 auto 16px;">${b.icon}</div>
      <h4 style="margin-bottom:8px;">${b.title}</h4>
      <p style="font-size:0.9rem;color:var(--dark-gray);margin:0;">${b.desc}</p>
    </div>`).join("\n");
}

function buildTimelineSteps(data: AuditData): string {
  if (data.next_steps && data.next_steps.length > 0) {
    return data.next_steps.map((step, i) => `
      <div style="display:flex;gap:16px;margin-bottom:24px;">
        <div style="width:32px;height:32px;border-radius:50%;background:var(--nebula-blue);color:white;display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0;">${step.step_num || i + 1}</div>
        <div>
          <div style="font-weight:700;margin-bottom:4px;">${esc(step.title)}</div>
          <div style="font-size:0.9rem;color:var(--dark-gray);">${esc(step.description)}</div>
        </div>
      </div>`).join("\n");
  }
  const steps = [
    { n: 1, t: "Week 1–2: Discovery &amp; Scope", d: "Index audit, data sync plan, UX requirements" },
    { n: 2, t: "Week 3–4: Pilot Build",           d: "Algolia index live, UI integration, A/B test setup" },
    { n: 3, t: "Week 5–6: Measure",               d: "Conversion uplift, bounce rate, zero-results rate" },
  ];
  return steps.map(step => `
    <div style="display:flex;gap:16px;margin-bottom:24px;">
      <div style="width:32px;height:32px;border-radius:50%;background:var(--nebula-blue);color:white;display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0;">${step.n}</div>
      <div>
        <div style="font-weight:700;margin-bottom:4px;">${step.t}</div>
        <div style="font-size:0.9rem;color:var(--dark-gray);">${step.d}</div>
      </div>
    </div>`).join("\n");
}

function buildFinancialCardRows(data: AuditData): string {
  const fin = data.financials;
  if (!fin) return "";
  const rows: Array<{ l: string; v: string | undefined }> = [
    { l: "Digital Revenue Est.", v: fin.total_digital_revenue },
    { l: "Search-Addressable",   v: fin.search_addressable },
    { l: "Conservative Lift",    v: fin.conservative_lift_label },
    { l: "Search ROI Est.",      v: fin.search_roi_est },
  ].filter(r => r.v);
  return rows.map(r => `
    <div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--light-gray);">
      <span style="font-size:0.85rem;color:var(--dark-gray);">${esc(r.l)}</span>
      <span style="font-weight:700;">${esc(r.v!)}</span>
    </div>`).join("\n");
}

function buildPanelItems(data: AuditData, type: "positive" | "critical"): string {
  const severity = type === "positive" ? "positive" : "critical";
  const items = data.findings.filter(f => f.severity === severity);
  if (items.length === 0) {
    return type === "positive"
      ? `<div style="padding:8px 0;color:var(--dark-gray);font-size:0.9rem;">No positive signals detected</div>`
      : `<div style="padding:8px 0;font-size:0.9rem;">Multiple critical gaps identified in audit</div>`;
  }
  return items.map(f => `
    <div style="display:flex;align-items:flex-start;gap:8px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.15);">
      <span>${type === "positive" ? "✅" : "⚠️"}</span>
      <span style="font-size:0.9rem;">${esc(f.title)}</span>
    </div>`).join("\n");
}

function buildAppendixTechTable(data: AuditData): string {
  const tech = data.tech_stack;
  if (!tech) return "<p>No tech stack data available.</p>";
  const entries: Array<[string, string | undefined]> = [
    ["E-commerce Platform", tech.ecommerce_platform],
    ["CMS", tech.cms],
    ["Search Provider", tech.search_provider],
    ["Personalization", tech.personalization],
    ["Analytics", tech.analytics],
    ["Tag Manager", tech.tag_manager],
    ["Recently Added", tech.added?.join(", ")],
    ["Recently Removed", tech.removed?.join(", ")],
  ].filter(([, v]) => v) as Array<[string, string]>;
  return `<table class="data-table mt-24">
    <thead><tr><th>Category</th><th>Technology</th></tr></thead>
    <tbody>${entries.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>`).join("")}</tbody>
  </table>`;
}

function buildAppendixQueriesTable(data: AuditData): string {
  if (!data.findings || data.findings.length === 0) return "<p>No test queries recorded.</p>";
  return `<table class="data-table mt-24">
    <thead><tr><th>#</th><th>Query</th><th>Category</th><th>Severity</th><th>Finding</th></tr></thead>
    <tbody>${data.findings.map((f, i) => `
      <tr>
        <td>${i + 1}</td>
        <td><code>"${esc(f.tested_query)}"</code></td>
        <td>${esc(f.category)}</td>
        <td style="color:${f.severity === "critical" ? "#DC2626" : f.severity === "moderate" ? "#D97706" : "#10B981"}">${f.severity.toUpperCase()}</td>
        <td>${esc(f.title)}</td>
      </tr>`).join("")}
    </tbody>
  </table>`;
}

function buildAppendixFinancialData(data: AuditData): string {
  const fin = data.financials;
  if (!fin) return "<p>No financial data available.</p>";
  let html = "";
  if (fin.revenue_3y && fin.revenue_3y.length > 0) {
    html += `<h3 class="mt-24">Revenue Trend</h3>
    <table class="data-table mt-16">
      <thead><tr><th>Year</th><th>Revenue</th></tr></thead>
      <tbody>${fin.revenue_3y.map(r => `<tr><td>${esc(r.year)}</td><td>${esc(r.revenue)}</td></tr>`).join("")}</tbody>
    </table>`;
  }
  const summary: Array<[string, string | undefined]> = [
    ["Market Cap", fin.market_cap],
    ["E-commerce Revenue Est.", fin.ecommerce_revenue_est],
    ["Digital Revenue Est.", fin.total_digital_revenue],
    ["Search-Addressable Revenue", fin.search_addressable],
    ["Conservative Search Lift", fin.conservative_lift_label],
    ["Search ROI Est.", fin.search_roi_est],
  ].filter(([, v]) => v) as Array<[string, string]>;
  if (summary.length > 0) {
    html += `<h3 class="mt-32">Financial Summary</h3>
    <table class="data-table mt-16">
      <thead><tr><th>Metric</th><th>Value</th></tr></thead>
      <tbody>${summary.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>`).join("")}</tbody>
    </table>`;
  }
  return html || "<p>No financial data available.</p>";
}

function buildDataVintageNote(data: AuditData): string {
  const v = data.meta.data_vintage;
  if (!v) return "";
  const parts: string[] = [];
  if (v.similarweb) parts.push(`SimilarWeb: ${v.similarweb}`);
  if (v.builtwith)  parts.push(`BuiltWith: ${v.builtwith}`);
  if (v.yahoo_finance) parts.push(`Yahoo Finance: ${v.yahoo_finance}`);
  return parts.length > 0 ? `Data as of: ${parts.join(" · ")}` : "";
}

// Best matching case study (from findings with highest severity)
function bestCaseStudy(data: AuditData): { url: string; company: string; result: string } {
  const priority = ["critical", "moderate", "positive"] as const;
  for (const sev of priority) {
    const f = data.findings.find(x => x.severity === sev && x.algolia_case_study_url);
    if (f) return {
      url: f.algolia_case_study_url!,
      company: f.algolia_case_study_company || "Customer",
      result: f.algolia_case_study_result || "Improved search performance",
    };
  }
  return { url: "https://www.algolia.com/customers/", company: "Algolia Customer", result: "See results" };
}

// ─── Token replacement ────────────────────────────────────────────────────────

function buildTokenMap(data: AuditData): Record<string, string> {
  const cs = data.company_snapshot;
  const fin = data.financials || {};
  const ae = data.ae_fields || {};
  const traffic = data.traffic || {};
  const tech = data.tech_stack || {};
  const cover = data.cover;
  const meta = data.meta;
  const score = data.score;
  const bcs = bestCaseStudy(data);

  return {
    ALGOLIA_LOGO_BLUE:  b64Blue,
    ALGOLIA_LOGO_WHITE: b64White,
    COMPANY_NAME:           s(meta.company),
    DOMAIN:                 s(meta.domain),
    AUDIT_DATE:             s(meta.audit_date),
    AUDITED_BY:             s(meta.audited_by),
    VERSION:                s(meta.version),
    DATA_VINTAGE_NOTE:      buildDataVintageNote(data),
    COVER_PHOTO_URL:        s(cover.photo_url, "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=1200"),
    COMPANY_LOGO_URL:       s(cover.company_logo_url, `https://logo.clearbit.com/${meta.domain}`),
    STATUS_LINE:            s(cover.status_line, "Confidential · For Internal Use Only"),
    OVERALL_SCORE:          String(score.overall),
    SCORE_VERDICT:          s(score.verdict),
    SCORE_VERDICT_CLASS:    s(score.verdict_class),
    SCORE_VERDICT_COLOR:    verdictColor(score.verdict_class),
    SCORE_COLOR:            scoreColor(score.overall),
    CRITICAL_COUNT:         String(score.critical_count),
    MODERATE_COUNT:         String(score.moderate_count),
    FINDINGS_COUNT:         String(data.findings.length),
    INDUSTRY:               s(cs.industry),
    HQ:                     s(cs.hq),
    EMPLOYEES:              s(cs.employees),
    REVENUE:                s(cs.revenue),
    REVENUE_SOURCE:         s(cs.revenue_source),
    REVENUE_SOURCE_LABEL:   s(cs.revenue_source_label),
    FOUNDED:                s(cs.founded),
    TICKER:                 s(cs.ticker),
    SEARCH_VENDOR:          s(cs.current_search_vendor),
    ECOMMERCE_PLATFORM:     s(cs.ecommerce_platform || tech.ecommerce_platform),
    MONTHLY_VISITS:         s(cs.monthly_visits || traffic.monthly_visits),
    VISITS_SOURCE:          s(cs.visits_source || traffic.source_url),
    SW_VINTAGE:             s(meta.data_vintage?.similarweb),
    TECH_STACK_SUMMARY:     s(tech.tech_stack_summary),
    TOTAL_DIGITAL_REVENUE:  s(fin.total_digital_revenue),
    SEARCH_ADDRESSABLE:     s(fin.search_addressable),
    CONSERVATIVE_LIFT_LABEL: s(fin.conservative_lift_label),
    SEARCH_ROI:             s(fin.search_roi_est),
    URGENCY_LEVEL:          s(ae.urgency_level),
    URGENCY_LABEL:          s(ae.urgency_label),
    URGENCY_COLOR:          s(ae.urgency_color, "#D97706"),
    NEXT_STEP_ACTION:       s(ae.next_step_action),
    NEXT_STEP_OWNER:        s(ae.next_step_owner),
    NEXT_STEP_DATE:         s(ae.next_step_date),
    TALK_TRACK_OPENER:      s(ae.talk_track_opener),
    TALK_TRACK_CTA:         s(ae.talk_track_cta),
    AE_NAME:                s(ae.ae_name),
    AE_EMAIL:               s(ae.ae_email),
    TEST_QUERY_COUNT:       String(data.findings.length),
    CASE_STUDY_URL:         esc(bcs.url),
    CASE_STUDY_COMPANY:     esc(bcs.company),
    CASE_STUDY_RESULT_STAT: esc(bcs.result),
    VISIT_DURATION:         s(traffic.visit_duration),
    BOUNCE_RATE:            s(traffic.bounce_rate),
    PAGES_PER_VISIT:        s(traffic.pages_per_visit),
    MARKET_CAP:             s(fin.market_cap),
    ECOMMERCE_REVENUE_EST:  s(fin.ecommerce_revenue_est),
    METHODOLOGY:            s(data.methodology),
    DISCLAIMER:             "This document contains confidential analysis prepared for Algolia sales purposes. All search observations were made on publicly accessible pages. No systems were accessed beyond public browsing. All data sources cited.",

    // Dynamic blocks
    TOC_CONTENT:                  buildTocContent(data),
    FINDINGS_SECTIONS:            buildFindingCardsBinder(data),
    FINDINGS_CONTENT:             buildFindingCardsBinder(data), // alias
    FINDING_CARDS:                buildFindingCardsAE(data),
    PROSPECT_FINDING_CARDS:       buildProspectFindingCards(data),
    SIGNAL_CARDS:                 buildSignalCards(data, 2), // AE report: top 2
    INTELLIGENCE_SIGNALS:         buildSignalCards(data),
    GAP_PAIRS:                    buildGapPairs(data),
    SCORE_BARS:                   buildScoreBars(data),
    SCORE_HEATMAP:                buildScoreHeatmap(data),
    FEATURE_COMPARISON_ROWS:      buildFeatureComparisonRows(data),
    REVENUE_3Y_ROWS:              buildRevenue3yRows(data),
    NEXT_STEPS:                   buildNextSteps(data),
    BIBLIOGRAPHY:                 buildBibliography(data),
    COMPETITOR_ROWS:              buildCompetitorRows(data),

    // First executive (ae-report exec quote slot)
    EXEC_QUOTE_TEXT:    s(data.executives?.[0]?.quote),
    EXEC_NAME:          s(data.executives?.[0]?.name),
    EXEC_TITLE:         s(data.executives?.[0]?.title),
    QUOTE_SOURCE_URL:   s(data.executives?.[0]?.quote_source),
    QUOTE_SOURCE_LABEL: s(data.executives?.[0]?.quote_source_label),
    QUOTE_DATE:         s(data.executives?.[0]?.quote_date),
    EXEC_QUOTE_CARD:    data.executives?.[0]
      ? `<div class="exec-quote__text">"${esc(data.executives[0].quote)}"</div>
         <div class="exec-quote__attr">${esc(data.executives[0].name)}, ${esc(data.executives[0].title)}</div>
         <div class="exec-quote__source"><a href="${esc(data.executives[0].quote_source)}" target="_blank">${esc(data.executives[0].quote_source_label || "Source")}</a> · ${esc(data.executives[0].quote_date)}</div>`
      : "",

    // First finding (ae-report inline finding slots outside FINDING_CARDS block)
    IMPACT_SOURCE_URL:  s(data.findings?.[0]?.impact_stat_source),
    TESTED_QUERY:       s(data.findings?.[0]?.tested_query),
    SCREENSHOT_FILE:    s(data.findings?.[0]?.screenshot_file),

    // Generic source URL (signal card fallback)
    SOURCE_URL:         s(data.bibliography?.[0]?.url || data.company_snapshot.visits_source),

    // Battle-card case study detail tokens
    CASE_STUDY_INDUSTRY: s(data.company_snapshot.industry),
    CASE_STUDY_CHALLENGE: s(data.findings?.[0]?.actual_behavior),
    CASE_STUDY_RESULT_LABEL: s(bcs.result),

    // ── Aliases (same content, different token names used in book-template) ──
    STATUS_HEADLINE:        s(cover.status_line, "Confidential · For Internal Use Only"),
    REPORT_DATE:            s(meta.audit_date),
    BIBLIOGRAPHY_ENTRIES:   buildBibliography(data),
    SCORING_HEATMAP_ROWS:   buildScoreHeatmap(data),
    NEXT_STEPS_ITEMS:       buildNextSteps(data),
    STRATEGY_EXECUTION_PAIRS: buildGapPairs(data),
    COMPETITOR_TABLE_ROWS:  buildCompetitorRows(data),
    TOTAL_MONTHLY_VISITS:   s(cs.monthly_visits || traffic.monthly_visits),
    PAGE_NUM:               "",
    METHODOLOGY_DESCRIPTION: s(data.methodology),
    DATA_SOURCE_LABEL:      "SimilarWeb · BuiltWith · Yahoo Finance · SEC EDGAR",

    // ── Score gauge (SVG dasharray + color classes) ──
    GAUGE_DASHARRAY:        gaugeProps(score.overall).dasharray,
    GAUGE_COLOR_CLASS:      gaugeProps(score.overall).colorClass,
    SCORE_VALUE_CLASS:      gaugeProps(score.overall).valueClass,
    SCORE_DESCRIPTION:      s(score.description, `Search experience scored ${score.overall}/10 — ${score.verdict}`),

    // ── Cover page KPI metrics ──
    METRIC_1: s(ae.metric_1, cs.monthly_visits ? `${cs.monthly_visits} monthly visitors` : "—"),
    METRIC_2: s(ae.metric_2, cs.current_search_vendor ? `${cs.current_search_vendor} search` : "—"),

    // ── Critical gap KPI cards ──
    CRITICAL_GAP_LABEL: (() => { const f = data.findings.find(x => x.severity === "critical"); return s(f?.impact_stat, s(f?.category, "Critical Gap")); })(),
    CRITICAL_GAP_TITLE: s(data.findings.find(x => x.severity === "critical")?.title, "Top Critical Gap"),
    CRITICAL_GAP_DESC:  s(data.findings.find(x => x.severity === "critical")?.actual_behavior, "See findings section for details"),
    REVENUE_RISK:       s(ae.revenue_risk, fin.search_roi_est ?? "TBD"),
    REVENUE_RISK_DESC:  s(ae.revenue_risk_desc, "Based on current search conversion rates vs. industry benchmarks"),
    THE_ASK_LABEL:      s(ae.the_ask_label, "Pilot"),
    THE_ASK_DESC:       s(ae.the_ask_desc, "4-week search experience pilot with A/B measurement"),

    // ── Opportunity / pilot page tokens ──
    OPPORTUNITY_HEADLINE: s(ae.opportunity_headline, `The ${s(cs.industry)} Search Opportunity`),
    BENCHMARK_PROOF:      s(ae.benchmark_proof, "Algolia customers see avg. +12% conversion uplift within 90 days."),
    PILOT_HEADLINE:       s(ae.pilot_headline, "Pilot Roadmap"),
    PILOT_TAKEAWAY:       s(ae.pilot_takeaway, "4-week proof of value — measurable results before full commitment."),
    PILOT_DETAIL_HEADLINE: s(ae.pilot_detail_headline, ae.pilot_headline ?? "Pilot Roadmap"),
    PILOT_SCOPE_DETAILS:  s(ae.pilot_scope_details, "Scope: Primary search experience, 1 storefront, SAYT, and zero-results pages."),
    TIMELINE_STEPS:       buildTimelineSteps(data),
    PILOT_TIMELINE_STEPS: buildTimelineSteps(data),
    FINANCIAL_CARD_ROWS:  buildFinancialCardRows(data),
    PILOT_FINANCIAL_ROWS: buildFinancialCardRows(data),

    // ── Scorecard tokens ──
    SCORECARD_HEADLINE:   s(ae.scorecard_headline, `${s(cs.industry)} Search Scorecard`),
    SCORECARD_TAKEAWAY:   s(ae.scorecard_takeaway, `Addressing the critical gaps would position ${s(meta.company)} as the search leader in ${s(cs.industry)}.`),
    PANEL_POSITIVE_TITLE: "What's Working",
    PANEL_CRITICAL_TITLE: "Critical Gaps",
    PANEL_POSITIVE_ITEMS: buildPanelItems(data, "positive"),
    PANEL_CRITICAL_ITEMS: buildPanelItems(data, "critical"),

    // ── Radar chart ──
    RADAR_EXPECTED_POINTS: buildRadarPoints(data, "expected"),
    RADAR_ACTUAL_POINTS:   buildRadarPoints(data, "actual"),

    // ── Leadership / exec chapter ──
    LEADERSHIP_QUOTES:    buildLeadershipQuotes(data),
    EXEC_CARDS:           buildExecCards(data),
    CLOSING_QUOTE:        s(data.executives?.slice(-1)[0]?.quote ?? data.executives?.[0]?.quote, `Search is central to how our customers find and buy.`),

    // ── Tech stack chapter ──
    TECH_STACK_HEADLINE:  s(tech.headline, "Tech Stack in Transition"),
    TECH_STACK_TAKEAWAY:  s(tech.takeaway, `The technology changes underway at ${s(meta.company)} create a window for a modern search platform.`),
    VACUUM_LABEL:         s(tech.vacuum_label, "Search Gap"),
    VACUUM_SUBLABEL:      s(tech.vacuum_sublabel, "Opportunity for Algolia"),
    STACK_ADDED_BLOCKS:   buildStackBlocks(data, "added"),
    STACK_REMOVED_BLOCKS: buildStackBlocks(data, "removed"),

    // ── AI gap chapter ──
    AI_GAP_HEADLINE:      s(ae.ai_gap_headline, `The AI Search Gap at ${s(meta.company)}`),
    AI_GAP_TAKEAWAY:      s(ae.ai_gap_takeaway, "Every week without AI search is a week of lost discovery revenue."),
    AI_DEPLOYED_TITLE:    "AI Features Deployed",
    AI_ABSENT_TITLE:      "Missing AI Capabilities",
    AI_DEPLOYED_ITEMS:    buildAIItems(data, "deployed"),
    AI_ABSENT_ITEMS:      buildAIItems(data, "absent"),

    // ── Competitor chapter ──
    COMPETITOR_HEADLINE:  s(ae.competitor_headline, "Competitor Pressure"),
    COMPETITOR_TAKEAWAY:  s(ae.competitor_takeaway, "Competitors investing in search now will capture disproportionate market share."),
    COMPETITOR_BAR_ROWS:  buildCompetitorBarRows(data),
    COMPETITIVE_DIMENSION: "Algolia Adoption Among Competitors",
    DONUT_DASHARRAY:      buildCompetitorDonut(data).dasharray,
    DONUT_PCT:            buildCompetitorDonut(data).pct,
    DONUT_LABEL:          buildCompetitorDonut(data).label,
    DONUT_DESCRIPTION:    buildCompetitorDonut(data).description,

    // ── Hiring chapter ──
    HIRING_HEADLINE:      s(ae.hiring_headline, "Hiring Signals Reveal Investment Priorities"),
    HIRING_TAKEAWAY:      s(ae.hiring_takeaway, "Active engineering and data hiring signals infrastructure investment."),
    HIRING_BAR_ROWS:      buildHiringBarRows(data),
    HIRING_CALLOUT:       buildHiringCallout(data),

    // ── Architecture chapter ──
    ARCHITECTURE_HEADLINE:  s(ae.architecture_headline, `Why Algolia Fits ${s(meta.company)}`),
    ARCHITECTURE_BENEFITS:  buildArchitectureBenefits(data),
    BUYER_EXPERIENCE_LABEL: s(ae.buyer_experience_label, "Shopper converts faster"),

    // ── Appendix tokens ──
    APPENDIX_TECH_TABLE:      buildAppendixTechTable(data),
    APPENDIX_QUERIES_TABLE:   buildAppendixQueriesTable(data),
    APPENDIX_FINANCIAL_DATA:  buildAppendixFinancialData(data),

    // ── Traffic appendix charts ──
    TRAFFIC_DONUT_SEGMENTS:      buildTrafficDonutSegments(data),
    TRAFFIC_LEGEND_ITEMS:        buildTrafficLegendItems(data),
    DEMOGRAPHICS_PIE_SEGMENTS:   buildDemographicsPieSegments(data),
    DEMOGRAPHICS_LEGEND_ITEMS:   buildDemographicsLegendItems(data),
    ENGAGEMENT_TABLE_ROWS:       buildEngagementTableRows(data),

    // ── Scoring appendix ──
    HIGH_COUNT: String(data.findings.filter(f => f.severity === "critical").length),
    MED_COUNT:  String(data.findings.filter(f => f.severity === "moderate").length),
    LOW_COUNT:  String(data.findings.filter(f => f.severity === "positive").length),
    HIGH_WEIGHTED_SUM: (data.findings.filter(f => f.severity === "critical").length * 2).toFixed(1),
    MED_WEIGHTED_SUM:  (data.findings.filter(f => f.severity === "moderate").length).toFixed(1),
    LOW_WEIGHTED_SUM:  (data.findings.filter(f => f.severity === "positive").length * 0.5).toFixed(1),
    TOTAL_WEIGHTED: (
      data.findings.filter(f => f.severity === "critical").length * 2 +
      data.findings.filter(f => f.severity === "moderate").length * 1 +
      data.findings.filter(f => f.severity === "positive").length * 0.5
    ).toFixed(1),
    TOTAL_WEIGHTS: (
      data.findings.filter(f => f.severity === "critical").length * 2 +
      data.findings.filter(f => f.severity === "moderate").length * 1 +
      data.findings.filter(f => f.severity === "positive").length * 0.5
    ).toFixed(1),
  };
}

// ─── Template rendering ───────────────────────────────────────────────────────

function replaceTokens(html: string, tokens: Record<string, string>): string {
  // Replace all {{TOKEN}} placeholders
  return html.replace(/\{\{([A-Z0-9_]+)\}\}/g, (match, key) => {
    return key in tokens ? tokens[key] : match;
  });
}

function checkUnreplacedTokens(html: string, slug: string, mode: string): boolean {
  const unreplaced = html.match(/\{\{[A-Z_]+\}\}/g);
  if (!unreplaced) return true;
  const unique = [...new Set(unreplaced)];
  console.warn(`\n⚠  ${unique.length} unreplaced token(s) in ${slug}-${mode}:`);
  unique.forEach(t => console.warn(`   ${t}`));
  const critical = unique.filter(t => CRITICAL_TOKENS.some(ct => t.includes(ct)));
  if (critical.length > 0) {
    console.error(`\n✗ CRITICAL tokens unreplaced — aborting write: ${critical.join(", ")}`);
    return false;
  }
  return true;
}

// ─── Site mode (SPA) ─────────────────────────────────────────────────────────

async function renderSite(data: AuditData, slug: string, cwd: string): Promise<void> {
  const templatePath = join(TEMPLATES_DIR, "index-template.html");
  let html: string;
  try {
    html = await Deno.readTextFile(templatePath);
  } catch {
    throw new Error(`Template not found: ${templatePath}`);
  }

  // Screenshots are in {slug}/screenshots/ (same folder as index.html)
  // Path "screenshots/file.png" resolves correctly from {slug}/index.html
  // DO NOT prefix with ../ — screenshots are no longer in hub root
  const siteData = JSON.parse(JSON.stringify(data)) as AuditData;

  // Inject window.AUDIT_DATA before closing </head>
  const script = `<script>window.AUDIT_DATA = ${JSON.stringify(siteData, null, 2)};</script>`;
  if (html.includes("<!-- AUDIT_DATA_PLACEHOLDER -->")) {
    html = html.replace("<!-- AUDIT_DATA_PLACEHOLDER -->", script);
  } else if (html.includes("</head>")) {
    html = html.replace("</head>", `${script}\n</head>`);
  } else {
    html = script + "\n" + html;
  }

  // Also do token replacement for any static tokens in the template
  const tokens = buildTokenMap(data);
  html = replaceTokens(html, tokens);

  // Inject brand CSS (Sora font, tokens, type scale) before </head>
  if (BRAND_CSS_BLOCK) {
    html = html.includes("</head>")
      ? html.replace("</head>", `${BRAND_CSS_BLOCK}</head>`)
      : BRAND_CSS_BLOCK + html;
  }

  const outDir = join(cwd, slug);
  await ensureDir(outDir);
  const outPath = join(outDir, "index.html");
  await Deno.writeTextFile(outPath, html);
  const size = (new TextEncoder().encode(html).length / 1024).toFixed(1);
  console.log(`✓ [site]        ${outPath} (${size} KB)`);
}

// ─── PDF template modes ───────────────────────────────────────────────────────

const TEMPLATE_MAP: Record<string, { file: string; out: string; inSlugDir: boolean }> = {
  binder:        { file: "book-template.html",                   out: "{slug}-book.html",  inSlugDir: false },
  "ae-report":   { file: "ae-action-report-template.html",       out: "ae-report.html",    inSlugDir: true },
  "battle-card": { file: "strategic-battle-card-template.html",  out: "battle-card.html",  inSlugDir: true },
  "leave-behind":{ file: "prospect-leave-behind-template.html",  out: "leave-behind.html", inSlugDir: true },
};

async function renderPdfTemplate(data: AuditData, slug: string, mode: string, cwd: string): Promise<void> {
  const cfg = TEMPLATE_MAP[mode];
  if (!cfg) throw new Error(`Unknown mode: ${mode}. Valid: site, binder, ae-report, battle-card, leave-behind, all`);

  const templatePath = join(TEMPLATES_DIR, cfg.file);
  let html: string;
  try {
    html = await Deno.readTextFile(templatePath);
  } catch {
    throw new Error(`Template not found: ${templatePath}`);
  }

  const tokens = buildTokenMap(data);
  html = replaceTokens(html, tokens);

  // Inject brand CSS (Sora font, tokens, type scale) before </head>
  if (BRAND_CSS_BLOCK) {
    html = html.includes("</head>")
      ? html.replace("</head>", `${BRAND_CSS_BLOCK}</head>`)
      : BRAND_CSS_BLOCK + html;
  }

  const ok = checkUnreplacedTokens(html, slug, mode);
  if (!ok) return;

  const outFile = cfg.out.replace("{slug}", slug);
  // ae-report, battle-card, leave-behind go into {slug}/ subfolder (mirrors Vercel URL structure)
  // binder stays at cwd root (local-only, not published)
  const outPath = cfg.inSlugDir ? join(cwd, slug, outFile) : join(cwd, outFile);
  await Deno.writeTextFile(outPath, html);
  const size = (new TextEncoder().encode(html).length / 1024).toFixed(1);
  console.log(`✓ [${mode.padEnd(12)}] ${outPath} (${size} KB)`);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const args = Deno.args;
  if (args.length < 2) {
    console.error("Usage: render-audit.ts <company-slug> <mode>");
    console.error("Modes: site | binder | ae-report | battle-card | leave-behind | all");
    console.error("Example: render-audit.ts costco site");
    Deno.exit(1);
  }

  const slug = args[0];
  const mode = args[1];
  const cwd = Deno.cwd();

  // JSON Schema Gate — must run after slug is known
  enforceJsonSchema(slug);

  // Load audit data
  const jsonPath = join(cwd, `${slug}-audit-data.json`);
  let data: AuditData;
  try {
    const raw = await Deno.readTextFile(jsonPath);
    data = JSON.parse(raw);
  } catch (e) {
    console.error(`✗ Could not read ${jsonPath}: ${e}`);
    Deno.exit(1);
  }

  console.log(`\nAlgolia Search Audit Renderer v2.0`);
  console.log(`Company : ${data.meta.company}`);
  console.log(`Mode    : ${mode}`);
  console.log(`Data    : ${jsonPath}\n`);

  // Embed company logo as base64 data URI so output files are fully self-contained.
  // Priority: (1) disk cache ({slug}-logo.png), (2) network fetch, (3) SVG text fallback.
  const rawLogoUrl = data.cover.company_logo_url || `https://logo.clearbit.com/${data.meta.domain}`;
  const diskLogoPath = join(cwd, `${slug}-logo.png`);
  const diskLogo = loadFileAsDataUri(diskLogoPath);
  if (diskLogo) {
    data.cover.company_logo_url = diskLogo;
    console.log(`✓ Company logo loaded from disk (${diskLogoPath})`);
  } else {
    console.log(`Fetching company logo …  ${rawLogoUrl}`);
    const fetched = await fetchAsDataUri(rawLogoUrl);
    if (fetched.startsWith("data:")) {
      data.cover.company_logo_url = fetched;
      console.log("✓ Company logo embedded as data URI");
    } else {
      // Network unavailable — keep the URL as-is so the browser loads it directly at runtime.
      // clearbit.com URLs work in browsers even when Deno can't reach them during build.
      // The topbar <img onerror> will hide it gracefully if clearbit fails for any reason.
      data.cover.company_logo_url = rawLogoUrl;
      console.log(`✓ Company logo: URL kept for browser-side loading (${rawLogoUrl})`);
    }
  }

  const modes = mode === "all"
    ? ["site", "binder", "ae-report", "battle-card", "leave-behind"]
    : [mode];

  for (const m of modes) {
    try {
      if (m === "site") {
        await renderSite(data, slug, cwd);
      } else {
        await renderPdfTemplate(data, slug, m, cwd);
      }
    } catch (e) {
      console.error(`✗ [${m}] ${e}`);
    }
  }

  console.log("\nDone. Run generate-pdf.sh to convert HTML files to PDF.\n");
}

main();
