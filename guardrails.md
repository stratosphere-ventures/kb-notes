# Guardrails: Layer-1 Lint Rule Set 

## Overview

Two layers of linting are enforced:

1. **Schema/metadata lint** (hard fail)
2. **Content purity lint** (hard fail or warn, depending on rule)

This MVP rule set is strict enough to prevent Layer-2 leakage while remaining workable.

---

## A) Schema + Metadata Lint (HARD FAIL)

### A1. Required Front-Matter Fields

**Fail if any missing:**
- `doc_type`, `doc_id`, `doc_key`, `doc_version`
- `published_ts`, `asof_ts`, `market_session`, `region`, `universe_scope`
- `trust_tier`, `license_policy`
- `market_data_vendor`, `market_data_version`, `calc_versions`, `pipeline_version`
- `is_current`, `is_active`

### A2. Field Type Validation

- `doc_version` must be `int`
- `is_current`, `is_active` must be `boolean`
- `published_ts`, `asof_ts` must be ISO-8601 timestamps
- `calc_versions` must be `list`
- `sources_used` (if present) must be `list` of objects with `source_name`, `source_type`

### A3. Time Semantics

- `published_ts >= asof_ts` for post-session wraps
- `market_session ∈ {pre, regular, post, weekend}`
- `region` must be one of allowed enums (e.g., US/EU/APAC)

### A4. Evidence Appendix Consistency

If document contains "Session Timeline" events, then Evidence Appendix must contain at least one evidence item per event, with:
- `source_name`, `source_type`, `published_ts`
- `doc_id` and `chunk_id` (or canonical url + doc_id)

### A5. Numeric Provenance Constraint

If document contains any numeric value in sections 1.2–1.4 or 3.x, then front matter must include `market_data_vendor` and `market_data_version`.

---

## B) Content Purity Lint (Layer-1 vs Layer-2 Separation)

### B1. Forbidden Causal Language (HARD FAIL)

**Fail if any of these appear (case-insensitive) outside the Evidence Appendix:**
- "because", "due to", "driven by", "on" (when used causally), "as investors", "as markets", "amid" (often causal)
- "following" is allowed only if paired with a timestamped event and a measured window (see B3)

**Good:** "Following the 08:30 ET release, SPX moved +0.6% in 60 minutes."
**Bad:** "SPX rallied because payrolls cooled."

### B2. Forbidden Subjective/Forecast Language (HARD FAIL)

**Fail if any of these appear outside Evidence Appendix:**

**Sentiment:** "bullish", "bearish", "risk-on", "risk-off", "panic", "euphoria"

**Forecast:** "likely", "expected to", "should", "will", "may", "could", "probable"

**Thesis words:** "undervalued", "overvalued", "strong", "weak", "healthy", "support", "resistance" (unless defined as a deterministic rule output—see B6)

### B3. Event Linkage Requirement (HARD FAIL)

If the doc mentions an event reaction (e.g., "NFP_t0_to_t+60m"), it must include:
- An explicit event header in the timeline with `published_ts` and `session`
- A measured reaction window section with numeric output

**Fail if you reference an event reaction window that does not map to a timeline event.**

### B4. "No News" / "No Material" Statements (WARN or FAIL)

**Default: WARN**

**Flag phrases:**
- "no material news", "no news", "nothing happened", "quiet session"

**Suggested compliant phrasing:**
- "No company-specific filings or press releases were identified in the ingested sources during the session."

If you can't substantiate "no news" from a defined source set, make it a WARN at minimum.

### B5. Source Specificity for Non-Primary Claims (HARD FAIL)

If the doc uses vague sources like:
- "industry reports", "sources", "reports said", "analysts said"

**Fail unless it includes a specific publisher name + URL (or internal doc_id).**

### B6. Technical Indicator Labeling Constraints (HARD FAIL for labels; allow raw metrics)

**Allow:**
- "RSI(14): 68"
- "MACD line crossed above signal line"

**Disallow:**
- "overbought/oversold", "bullish crossover", "bearish divergence", "support/resistance"

**Unless you explicitly tag them as deterministic classifier outputs:**

Example allowed if you do this:
- `trend_state: above_all_key_mas` (deterministic)

But still avoid "bullish/bearish" in Layer-1 prose.

### B7. Calendar / Forward-Looking Sections (HARD FAIL unless isolated)

Forward calendar is acceptable only if:
- It is purely factual (scheduled events)
- It has a distinct section title like "Forward Calendar (Factual)"
- It contains no inference about impact

**Fail if you mix forward calendar with "watch", "risk", "catalyst", etc.**

### B8. Citation Coverage (HARD FAIL for event facts)

Every timeline event must have:
- At least one evidence item
- At least one attribution line in the event block (publisher/agency)

---

## C) Numeric Integrity Lint

### C1. Numeric Format Standardization (WARN)

- Percentages must include `%`
- bps must include `bps`
- Currency should include `$` or explicit currency code

### C2. Sanity Checks (WARN/HARD depending on appetite)

- VIX negative?
- Yields outside `[0, 20]`?
- Returns outside plausible range?

These are guardrails against parser or unit errors.

### C3. Duplicate / Conflicting Numerics (WARN)

If SPX close appears twice with different values → flag.