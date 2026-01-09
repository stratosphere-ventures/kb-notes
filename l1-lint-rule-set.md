# Layer-1 Lint Rule Set v1 (Production Guardrails)

---

## 1.1 Philosophy

**Hard fails** protect Layer-1 purity and mechanical consistency.

**Soft fails** catch realism/quality issues that will ruin evaluation, but may be tolerable early.

---

## 1.2 Rule Taxonomy (Codes + Checks)

### A) Document / Governance Contract

#### L1-GOV-001 (HARD) Required governance fields present
```yaml
Required fields:
  - date
  - region
  - market_session
  - published_ts
  - asof_ts
  - doc_version
  - trust_tier
  - market_data_vendor
  - market_data_version
  - pipeline_version
  - doc_id
  - doc_key
```

#### L1-GOV-002 (HARD) Timestamp ordering
- `asof_ts <= published_ts`
- Both ISO8601 Zulu or explicit timezone

#### L1-GOV-003 (HARD) Deterministic doc_key format
- `doc_key == "market_wrap/us/YYYY-MM-DD"`

#### L1-GOV-004 (SOFT) Source declarations consistent
- If `market_data_vendor == Massive`, don't claim Bloomberg/Refinitiv as market_data sources unless you really route them.

---

### B) Layer-1 Purity / Language

#### L1-PUR-001 (HARD) No causal/interpretive vocabulary in headline or facts
**Reject if any of these appear (case-insensitive) in:**
- `headline_neutral`
- `events[].facts[]`
- `evidence_items[].excerpt`

**Forbidden tokens (starter list; tune over time):**
```
because, due to, driven by, as investors, on hopes, on fears, relief, 
concerns, sentiment, risk-on, risk-off, bullish, bearish, support, 
resistance, oversold, overbought, priced in, implies, signals, likely, 
expected to, should, could, may, outlook, forecast
```

**Also ban "leads/lagged" phrasing in L1 summary:**
```
led, dragged, weighed, boosted
```

#### L1-PUR-002 (HARD) Evidence excerpts must be "primary-fact style"
- Must include at least one concrete statement (number / date / named action) or be a verbatim excerpt from an authoritative source.
- For synthetic Tier-1: mark evidence as synthetic via `trust_tier` or `source_type` (recommended).

---

### C) Internal Consistency (Numbers & Cross-field)

#### L1-CON-001 (HARD) Price range validity
For every index with `{low, high, close}`, enforce:
- `low <= close <= high`
- `low < high`

#### L1-CON-002 (HARD) Return math sanity
If `prev_close` exists:
- `return_pct ≈ (close/prev_close-1)*100` within tolerance (e.g., 0.02%).

#### L1-CON-003 (HARD) Units consistent
- If `unit == "pct"` and symbol is a yield series, change must be in bps only if labeled bps; otherwise don't mix.

---

### D) Referential Integrity

#### L1-REF-001 (HARD) Event IDs are globally unique within a day
- No duplicates in `events[].event_id`.

#### L1-REF-002 (HARD) Reaction windows must reference existing events
- `reaction_windows[].event_id` must be in `events`.

#### L1-REF-003 (HARD) Evidence items must reference existing events
- `evidence_items[].event_id` must be in `events`.

---

### E) Realism / Anti-degeneracy (Tier-1 evaluation quality)

#### L1-REAL-001 (SOFT → HARD for eval-grade) "No duplication across dates" for key benchmarks
- Same DJIA.close (exact) repeated across dates should fail for Tier-1.
- Same for QQQ.close, IWM.close, etc.

#### L1-REAL-002 (SOFT) Correlation sanity
- If SPX is down >1.0%, VIX should not be sharply down most of the time (allow exceptions, but flag).

#### L1-REAL-003 (SOFT) Evidence URL scheme must be valid for the source_type
- If `source_type == sec_filing`, URL should match the ticker's CIK registry (or use `synthetic://sec/...`).

---

## 2) How to Enforce These Rules Mechanically

### 2.1 Lint Implementation Approach

**Implement linter as pure Python (no LLM).**

**Output JSON report with:**
```json
{
  "errors": [
    {
      "code": "L1-PUR-001",
      "severity": "HARD",
      "path": "events[0].facts[0]",
      "message": "Forbidden causal language detected: 'because'"
    }
  ],
  "warnings": [
    {
      "code": "L1-REAL-002",
      "severity": "SOFT",
      "path": "market_data.VIX",
      "message": "VIX down while SPX down >1%"
    }
  ]
}
```

**CI gates:**
- **Hard errors** → fail build
- **Warnings** → fail build only on "eval-grade" runs (toggle)

### 2.2 Required "Cross-file" Checks for Your Workflow

If you render `.md` from JSON, add an extra lint stage:

1. **JSON passes schema + consistency**
2. **Rendered MD passes formatting/purity checks**
   - No forbidden tokens
   - One bullet per line
   - Proper markdown structure

---

### Implementation Priority

**Phase 1 (Core):**
- All HARD rules (L1-GOV-*, L1-PUR-*, L1-CON-*, L1-REF-*)

**Phase 2 (Quality):**
- SOFT rules for evaluation-grade data (L1-REAL-*)

**Phase 3 (Integration):**
- Cross-file MD rendering checks
- CI/CD pipeline integration
