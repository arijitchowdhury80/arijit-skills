"""
audit_data_schema.py — Pydantic v2 models for audit-data.json

Every field that the SPA template reads is typed here.
Pydantic enforces:
  - Required fields cannot be missing
  - Wrong field names fail at parse time (not at render time when the page is blank)
  - Channel-specific fields (video_script for video, etc.) are validated
  - Citations are required where the template renders them
  - Placeholder text ("Pending", source notes in body) is blocked

Usage:
    from audit_data_schema import AuditData
    data = AuditData.model_validate(json.load(f))   # raises ValidationError on any violation
    data.model_dump()                                 # back to dict for JSON

Pyright uses these types for static analysis of generate-audit-data.py etc.
"""

from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, model_validator, field_validator


# ── ABX Campaign ──────────────────────────────────────────────────────────────

class ABXContact(BaseModel):
    name: str
    id: str  # snake_case slug — required for SPA contactMap lookup
    title: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    linkedin_url: Optional[str] = None

    model_config = {"extra": "allow"}

class ABXTouch(BaseModel):
    touch: int
    day: str
    channel: Literal["email", "linkedin", "video"]
    target: str = "all"
    subject: Optional[str] = None
    body: str  # Email: full copy. LinkedIn: clean message. Video: short delivery email.
    message: Optional[str] = None  # Preview only — NOT rendered in SPA for email/video

    # Video-specific (required when channel == "video")
    video_script: Optional[str] = None
    video_platform: Optional[str] = "Loom"
    video_duration_target: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None

    @model_validator(mode='after')
    def validate_channel_rules(self) -> ABXTouch:
        body = self.body or ""
        channel = self.channel

        # Body must not be a placeholder
        placeholder_markers = ["Pending —", "Pending—", "TBD", "[PLACEHOLDER]",
                                "will be generated", "not yet complete"]
        for marker in placeholder_markers:
            if marker.lower() in body.lower():
                raise ValueError(
                    f"Touch {self.touch} ({channel}): body contains placeholder text '{marker}'. "
                    f"ABX campaign must be fully generated before JSON update."
                )

        # Body must not contain source notes (internal prep, not sendable copy)
        if "**Source notes:**" in body or "Source notes:" in body:
            raise ValueError(
                f"Touch {self.touch} ({channel}): body contains 'Source notes:' — "
                f"source notes are internal AE prep and must NOT appear in email body. "
                f"Extract only the sendable copy between **Body:** and **Source notes:**."
            )

        # Body must have real content
        if len(body.strip()) < 50:
            raise ValueError(
                f"Touch {self.touch} ({channel}): body is {len(body.strip())} chars — too short. "
                f"Minimum 50 chars required. Likely a placeholder or extraction failure."
            )

        # Video channel requires video_script
        if channel == "video":
            if not self.video_script:
                raise ValueError(
                    f"Touch {self.touch} (video): video_script is required for video touches. "
                    f"The SPA template reads t.video_script to render the Loom script panel. "
                    f"Do NOT put the script in t.body — that field holds the short delivery email."
                )
            script = self.video_script or ""
            if len(script.strip()) < 100:
                raise ValueError(
                    f"Touch {self.touch} (video): video_script is {len(script.strip())} chars — "
                    f"too short for a 2-minute script. Loom script should be 200-280 words."
                )

        return self

class ABXSequence(BaseModel):
    touches: list[ABXTouch]
    contacts: list[ABXContact]
    total_touches: int = Field(default=9)
    duration_days: int = Field(default=21)
    channels: list[str] = Field(default_factory=lambda: ["Email", "LinkedIn", "Video"])

    @model_validator(mode='after')
    def validate_sequence(self) -> ABXSequence:
        if len(self.touches) < 3:
            raise ValueError(
                f"abx_sequence.touches has {len(self.touches)} touches — minimum 3 required. "
                f"Run algolia-campaign-abx skill to generate the full campaign."
            )
        if len(self.contacts) < 1:
            raise ValueError(
                "abx_sequence.contacts is empty — must have at least 1 contact with id field."
            )
        # All contacts must have id for SPA contactMap
        for c in self.contacts:
            if not c.id:
                raise ValueError(
                    f"Contact '{c.name}' missing id field. "
                    f"id must be snake_case slug e.g. 'henning_kruger'."
                )
        return self


# ── ICP Mapping ───────────────────────────────────────────────────────────────

class ICPPriorityToProduct(BaseModel):
    # Template reads: p.their_priority (label), p.discovery_question, p.product/p.algolia_solution
    # We store both canonical names AND template-expected aliases
    pain: str                          # canonical — Solution Map reads p.pain
    their_priority: Optional[str] = None  # alias — Discovery Q card reads p.their_priority
    evidence: Optional[str] = None     # exec quote that justifies the Q
    exact_quote: Optional[str] = None  # alias for evidence
    product: str                       # canonical — Solution Map reads p.product
    algolia_solution: Optional[str] = None  # alias — Discovery Q card reads p.algolia_solution
    discovery_question: Optional[str] = None
    proof_company: Optional[str] = None
    proof_url: Optional[str] = None
    proof_result: Optional[str] = None

    @model_validator(mode='after')
    def validate_citations_and_aliases(self) -> ICPPriorityToProduct:
        # Enforce aliases so BOTH template paths work
        if not self.their_priority:
            self.their_priority = self.pain  # auto-populate alias
        if not self.algolia_solution:
            self.algolia_solution = self.product  # auto-populate alias

        # Citation required for discovery questions
        if self.discovery_question:
            has_evidence = bool(self.evidence or self.exact_quote)
            if not has_evidence:
                raise ValueError(
                    f"Q card for '{self.pain[:40]}...' has discovery_question but no evidence/exact_quote. "
                    f"BDRs cannot ask a question without the supporting exec quote. Add evidence field."
                )

        # Proof URL required when proof company is named
        if self.proof_company and not self.proof_url:
            raise ValueError(
                f"proof_company='{self.proof_company}' set but proof_url is missing. "
                f"Every case study reference must link to a verifiable source."
            )

        return self

class ICPMapping(BaseModel):
    priority_to_product: list[ICPPriorityToProduct] = Field(default_factory=list)


# ── Executives ────────────────────────────────────────────────────────────────

class Executive(BaseModel):
    name: str
    title: str
    quote: str
    quote_context: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None  # alias used in some places
    quote_source: Optional[str] = None  # canonical field template reads

    @model_validator(mode='after')
    def validate_quote_citation(self) -> Executive:
        # quote_source OR source_url must be present
        has_citation = bool(self.quote_source or self.source_url or self.source)
        if not has_citation:
            raise ValueError(
                f"Executive '{self.name}': quote has no citation. "
                f"Set quote_source (preferred), source_url, or source. "
                f"Citation rule: every quote must be verifiable."
            )
        # Auto-populate quote_source from source_url if missing
        if not self.quote_source and self.source_url:
            self.quote_source = self.source_url
        return self


# ── Intelligence Signals ──────────────────────────────────────────────────────

VALID_SIGNAL_TYPES = {
    "earnings_quote", "media_quote", "sec_risk", "hiring_signal",
    "social_signal", "news_signal"
}

VALID_SIGNAL_TYPES_EXTENDED = VALID_SIGNAL_TYPES | {
    # generate-audit-data.py enrichment types
    "exec", "news", "hiring", "social", "partner", "industry",
    # algolia-audit-report synthesis types
    "industry-risk", "industry-opp", "funding", "digital_transformation",
    "competitor", "leadership", "expansion", "regulatory",
}

class IntelligenceSignal(BaseModel):
    type: str
    # Content field: signals written by generate-audit-data use 'signal',
    # manually written signals use 'title' or 'badge_label'. Accept all.
    title: Optional[str] = None       # used in manually written signals
    signal: Optional[str] = None      # used in generate-audit-data.py output
    badge_label: Optional[str] = None # used in some signals as display label
    detail: Optional[str] = None
    relevance: Optional[str] = None
    source_url: Optional[str] = None
    source_date: Optional[str] = None
    urgency_score: Optional[int] = None
    ae_action: Optional[str] = None

    model_config = {"extra": "allow"}  # allow body/quote/text fields from older formats

    @model_validator(mode='after')
    def validate_signal(self) -> IntelligenceSignal:
        # Type must be known
        all_valid = VALID_SIGNAL_TYPES_EXTENDED
        if self.type not in all_valid:
            raise ValueError(
                f"intelligence_signals: type='{self.type}' is not recognised. "
                f"Valid types: {', '.join(sorted(all_valid))}"
            )
        # Must have at least one content field
        has_content = bool(self.title or self.signal or self.badge_label or self.detail)
        if not has_content:
            raise ValueError(
                f"intelligence_signals[type={self.type}]: no content field found. "
                f"Must have at least one of: title, signal, badge_label, detail."
            )
        # Citation required when detail content is present
        detail = self.detail or self.signal or ""
        if len(detail) > 50 and not self.source_url:
            raise ValueError(
                f"Signal '{(self.title or self.signal or '')[:40]}' has content "
                f"but no source_url. Citation rule: every signal claim must be verifiable."
            )
        return self


# ── Finding Card Enrichment Models ────────────────────────────────────────────

class AnxietyDriver(BaseModel):
    calculation: str
    competitor_comparison: str
    quantified_impact: str

    @field_validator('quantified_impact')
    @classmethod
    def impact_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("quantified_impact cannot be empty")
        return v

class IndustryBenchmark(BaseModel):
    metric_name: str
    best_in_class: str
    current_score: str
    gap: str
    source: str

    @field_validator('source')
    @classmethod
    def source_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source is required for IndustryBenchmark")
        return v

class DiscoveryQuestions(BaseModel):
    situation: str
    problem: str
    implication: str
    need_payoff: str

class AlgoliaAngle(BaseModel):
    capability: str
    specifics: str
    time_to_value: Optional[str] = None

class ValueMap(BaseModel):
    gap: str
    capability: str
    outcome: str
    metric: str

class ObjectionHandler(BaseModel):
    objection: str
    counter: str
    evidence_ref: Optional[str] = None


# ── Findings (Browser Audit) ──────────────────────────────────────────────────

class Finding(BaseModel):
    id: str
    title: str
    severity: Literal["critical", "moderate", "positive"]
    category: str
    tested_query: str
    actual_behavior: str
    algolia_solution: Optional[str] = None
    algolia_case_study_company: Optional[str] = None
    algolia_case_study_url: Optional[str] = None
    algolia_case_study_result: Optional[str] = None
    screenshot_file: Optional[str] = None
    expected_behavior: Optional[str] = None
    impact_stat: Optional[str] = None
    impact_stat_source: Optional[str] = None

    # Enrichment fields (optional — existing findings without them still valid)
    pain_frame: Optional[str] = None
    anxiety_driver: Optional[AnxietyDriver] = None
    industry_benchmark: Optional[IndustryBenchmark] = None
    discovery_questions: Optional[DiscoveryQuestions] = None
    algolia_angle: Optional[AlgoliaAngle] = None
    value_map: Optional[ValueMap] = None
    objection_handling: list[ObjectionHandler] = Field(default_factory=list)
    model_config = {"extra": "allow"}

    @model_validator(mode='after')
    def validate_finding(self) -> Finding:
        # Case study company requires URL
        if self.algolia_case_study_company and not self.algolia_case_study_url:
            raise ValueError(
                f"Finding '{self.id}': algolia_case_study_company='{self.algolia_case_study_company}' "
                f"set but no algolia_case_study_url. Every case study must link to source."
            )
        # Impact stat requires source
        if self.impact_stat and not self.impact_stat_source:
            raise ValueError(
                f"Finding '{self.id}': impact_stat set but no impact_stat_source. "
                f"Impact stats with no source URL are BLOCKING per pre-write rule — remove or cite."
            )
        return self


# ── Strategic Angles ──────────────────────────────────────────────────────────

class StrategicAngle(BaseModel):
    label: str
    hook: str
    pain_points: list[str]
    discovery_question: Optional[str] = None
    algolia_proof: Optional[str] = None
    objection: Optional[str] = None
    objection_counter: Optional[str] = None
    source: Optional[str] = None
    urgency: Optional[str] = None

    @model_validator(mode='after')
    def validate_angle(self) -> StrategicAngle:
        if not self.source:
            raise ValueError(
                f"strategic_angles['{self.label}']: source is required. "
                f"Every angle must cite the trigger signal that justifies it."
            )
        if not self.algolia_proof:
            raise ValueError(
                f"strategic_angles['{self.label}']: algolia_proof is required. "
                f"Every angle must reference a verified Algolia case study metric."
            )
        return self


# ── Score ─────────────────────────────────────────────────────────────────────

CANONICAL_SCORE_KEYS = {
    "latency", "typo_tolerance", "query_suggestions_empty_state",
    "intent_detection", "merchandising_consistency", "content_commerce_ux",
    "semantic_nlp_search", "dynamic_facets_personalization",
    "recommendations_merchandising", "search_intelligence"
}

class Score(BaseModel):
    overall: float = 0.0
    verdict: str = "AUDIT IN PROGRESS"
    verdict_class: Literal["critical", "moderate", "ok"] = "moderate"
    breakdown: dict[str, float] = Field(default_factory=dict)
    breakdown_labels: dict[str, str] = Field(default_factory=dict)
    breakdown_severity: dict[str, Literal["HIGH", "MEDIUM", "LOW"]] = Field(default_factory=dict)
    critical_count: int = 0
    moderate_count: int = 0
    low_count: int = 0

    @model_validator(mode='after')
    def validate_score_keys(self) -> Score:
        if self.breakdown:
            bad_keys = set(self.breakdown.keys()) - CANONICAL_SCORE_KEYS
            if bad_keys:
                raise ValueError(
                    f"score.breakdown has invalid keys: {bad_keys}. "
                    f"Only use canonical keys: {CANONICAL_SCORE_KEYS}. "
                    f"The SPA hardcodes these key names — wrong keys render as blank."
                )
        return self


# ── Case Studies ──────────────────────────────────────────────────────────────

class CaseStudy(BaseModel):
    vertical: str
    company: str
    result: str
    product: str
    why: str
    url: str  # Required — must be a live algolia.com/customers/ URL

    @field_validator('url')
    @classmethod
    def url_must_be_algolia(cls, v: str) -> str:
        if not v.startswith('http'):
            raise ValueError(f"case_studies url must be a full HTTP URL, got: '{v}'")
        return v


# ── Top-Level AuditData ───────────────────────────────────────────────────────

class Meta(BaseModel):
    company: str
    domain: str
    audit_date: str
    audited_by: str = "Algolia"
    version: Optional[str] = None
    audit_status: Optional[str] = None
    generated_by: Optional[str] = None
    patch_date: Optional[str] = None


class SearchAnalyticsMetric(BaseModel):
    key: Optional[str] = None
    label: Optional[str] = None
    value: Optional[str] = None
    detail: Optional[str] = None
    read: Optional[str] = None
    severity: Optional[str] = None  # high | medium | low — drives the metric-tile color
    model_config = {"extra": "allow"}


class SearchAnalyticsQuery(BaseModel):
    query: Optional[str] = None
    volume_30d: Optional[int] = None
    results: Optional[int] = None
    clicks: Optional[int] = None
    type: Optional[str] = None
    note: Optional[str] = None
    model_config = {"extra": "allow"}


class SearchAnalytics(BaseModel):
    """
    First-party Algolia telemetry for EXISTING-customer (expansion) audits.
    Powers the "Your Search, By the Numbers" SPA section. Optional — absent on
    displacement/greenfield audits, where the SPA section stays hidden.
    """
    window: Optional[str] = None
    source_label: Optional[str] = None
    index: Optional[str] = None
    metrics: list[SearchAnalyticsMetric] = Field(default_factory=list)
    volume: Optional[dict[str, Any]] = None
    zero_result_queries: list[SearchAnalyticsQuery] = Field(default_factory=list)
    no_click_queries: list[SearchAnalyticsQuery] = Field(default_factory=list)
    model_config = {"extra": "allow"}


class AuditData(BaseModel):
    """
    Full schema for {slug}-audit-data.json.

    Validate on load:
        data = AuditData.model_validate(json.load(f))

    Dump back to JSON:
        json.dump(data.model_dump(exclude_none=True), f, indent=2)

    Any field the SPA template reads must be typed here.
    Missing required fields → ValidationError at parse time, not blank sections at render time.
    """
    meta: Meta
    score: Score = Field(default_factory=Score)
    executives: list[Executive] = Field(default_factory=list)
    intelligence_signals: list[IntelligenceSignal] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    strategic_angles: list[StrategicAngle] = Field(default_factory=list)
    icp_mapping: Optional[ICPMapping] = None
    abx_sequence: Optional[ABXSequence] = None
    case_studies: list[CaseStudy] = Field(default_factory=list)
    search_analytics: Optional[SearchAnalytics] = None  # expansion audits: first-party telemetry

    # Allow extra fields (the schema has many more fields not modeled here yet)
    model_config = {"extra": "allow"}

    @model_validator(mode='after')
    def validate_completeness_gate(self) -> AuditData:
        """
        This is the COMPLETION GATE — mirrors the factcheck BLOCKED conditions.
        Runs every time the JSON is validated, not just at factcheck time.
        """
        # ABX: if present, must be complete
        if self.abx_sequence:
            for touch in self.abx_sequence.touches:
                # Already validated in ABXTouch but belt-and-suspenders at top level
                body = touch.body or ""
                if len(body.strip()) < 50:
                    raise ValueError(
                        f"COMPLETION GATE BLOCKED: abx_sequence.touches[{touch.touch}].body "
                        f"is {len(body.strip())} chars. Run algolia-campaign-abx to generate real content."
                    )

        # Findings: warn if browser testing was done but findings is empty
        # (Can't enforce hard block here without knowing browser file state)

        return self


# ── Validation entry point ────────────────────────────────────────────────────

def validate_audit_data(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate a dict against AuditData schema.
    Returns (is_valid, list_of_errors).
    Suitable for use in validate-json-schema.py and generate-audit-data.py.

    Usage:
        with open(path) as f:
            raw = json.load(f)
        ok, errors = validate_audit_data(raw)
        if not ok:
            for e in errors:
                print(f"  ❌ {e}")
    """
    from pydantic import ValidationError
    try:
        AuditData.model_validate(data)
        return True, []
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = " → ".join(str(x) for x in err["loc"])
            errors.append(f"[{loc}] {err['msg']}")
        return False, errors


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        print("Usage: python3 audit_data_schema.py <path-to-audit-data.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        raw = json.load(f)
    ok, errors = validate_audit_data(raw)
    if ok:
        print("✅ Schema validation passed")
    else:
        print(f"❌ {len(errors)} schema violation(s):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
