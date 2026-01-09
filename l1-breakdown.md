# Layer-1 Documentation Production Playbook

Below is the end-to-end, production-ready breakdown of how you create Layer-1 (L1) documentation using real data and real sources, mapped explicitly to the L1 framework you already defined. This is written as an operational playbook—not theory.

---

## 1. What Layer-1 is (lock this in)

Layer-1 documentation answers exactly one question:

> **"What happened, when did it happen, and what were the measured outcomes—without interpretation."**

### Layer-1 is not:

- Why it happened (unless explicitly attributed to a source)
- What it means
- What to do next

That separation is what keeps your RAG system reliable for institutions.

---

## 2. Real-world inputs you will consume

You will ingest three classes of real inputs, each with a different handling rule.

### A. Deterministic market data (numbers)

**Source examples:**
- Massive (prices, returns, OHLCV, indicators)
- Later: Polygon, Bloomberg, Refinitiv, etc.

**Characteristics:**
- Timestamped
- Structured
- Computable
- Canonical

**Examples:**
- SPX close = 5,120.40
- NVDA return = +3.2%
- VIX close = 15.10
- SMA(50), RSI(14), etc.

**Rule:**
These never come from documents or LLMs. They come from market data services and are stored in time-series / analytical stores.

### B. Primary news & filings (events)

**Source examples:**
- Reuters API
- Bloomberg API
- Yahoo Finance news feed
- SEC filings (EDGAR)
- Company press releases

**Characteristics:**
- Timestamped
- Attributed
- Textual
- Non-deterministic language

**Examples:**
- "BLS reported payroll growth of X…"
- "Company X filed an 8-K…"

**Rule:**
These become events, not truths about causality.

### C. Aggregated / secondary feeds (optional early)

**Source examples:**
- Yahoo Finance aggregated headlines
- TipRanks daily ETF updates
- ETF.com research summaries

**Characteristics:**
- Summarized
- Sometimes interpretive
- Often mixes facts + framing

**Rule:**
Allowed in Layer-1 only if:
- You extract factual statements
- You preserve attribution
- You do not adopt their interpretation as truth

---

## 3. The real L1 pipeline (step by step)

This is the exact flow you should implement.

### Step 1 — Ingest raw inputs (no transformation yet)

#### 1.1 Market data ingestion

Pull daily (or intraday) bars and indicators from Massive

Store in:
- TimescaleDB / ClickHouse (or equivalent)
- Version and timestamp everything

This produces:
- `market_outcomes`
- `technicals`
- Later: `reaction_windows`

#### 1.2 News / event ingestion

You ingest raw news items as they arrive.

Each raw item minimally contains:
- `headline`
- `body / summary`
- `published_ts`
- `source`
- `canonical_url`
- `tickers` (if provided or extracted)

Store these raw items unchanged in object storage (MinIO) for audit.

### Step 2 — Normalize news into Layer-1 events

Each real news item becomes a Layer-1 event object.

#### Example transformation

**Raw Reuters item:**
"U.S. job growth slowed in December, the Labor Department said on Friday…"

**Normalized L1 event:**
```json
{
  "event_id": "evt_jobs_2026-01-06",
  "event_type": "macro_release",
  "published_ts": "2026-01-06T13:30:00Z",
  "market_session": "pre",
  "facts": [
    "The Labor Department reported slower job growth in December."
  ],
  "source": {
    "name": "Reuters",
    "source_type": "news_wire",
    "canonical_url": "https://www.reuters.com/..."
  },
  "entities": ["SPX", "UST", "USD"]
}
```

**Important:**
- You do not infer impact
- You do not explain market behavior
- You only record what was reported

### Step 3 — Measure reactions (deterministic)

Now—and only now—you compute reaction windows using market data.

#### Example:
```json
{
  "event_id": "evt_jobs_2026-01-06",
  "instrument": "SPX",
  "window": "t0_to_t+60m",
  "move_pct": "+0.62"
}
```

This comes from:
- Event published_ts
- Massive price data

This step is pure math, not NLP.

### Step 4 — Assemble the daily L1 fact graph

At the end of the trading day, you assemble one canonical fact graph:

It contains:
- Governance metadata (date, region, session)
- Deterministic market outcomes
- Event timeline (attributed)
- Measured reactions
- Movers and sectors
- Ticker fact panels
- Evidence ledger

This fact graph is structured JSON and is your single source of truth.

---

## 4. Rendering L1 documentation (human-readable)

You now render the fact graph into Layer-1 documents.

### Key rule
**Rendering ≠ generation of truth**  
You are formatting existing truth.

### How rendering works (recap)

- Use Jinja2 templates
- No LLM
- No free-form prose
- Fixed headings
- Deterministic chunk IDs

### Output
- `market_wrap_l1_YYYY-MM-DD.md`
- (Later) `macro_event_l1_*.md`
- (Later) `ticker_panel_l1_*.md`

These are views, not the canonical store.

---

## 5. How real L1 documents map to your L1 outline

Here is a direct mapping.

| L1 Outline | Real Data Sources |
|------------|-------------------|
| **0) Governance block** | From: your pipeline, ingestion metadata, data vendor versions |
| **1) Executive Fact Summary** | From: Massive price data, daily index closes, volatility measures<br>Never from: news text |
| **2) Session Timeline (Attributed Events)** | From: Reuters / Bloomberg / Yahoo / SEC, normalized into event objects<br>Rules: Timestamped, Source named, Facts only |
| **3) Measured Market Reactions** | From: Massive, deterministic calculations<br>Rules: Linked to event_id, Numeric only |
| **4) Movers and Sectors** | From: Massive universe data, rules-based ranking<br>Rules: No "led" or "lagged" language |
| **5) Company Fact Panels** | From: Massive prices, SEC filings (presence/absence), technical indicators<br>Rules: "Filings identified: true/false", no quality judgments |
| **6) Evidence Appendix** | From: raw news objects, preserved URLs, excerpts<br>Purpose: audit, citation, trust |

---

## 6. Enforcement: how you keep it L1

Your ingestion worker enforces:

### Gate 1 — L1 linter
- No causal language
- No subjective terms
- No forecasts

### Gate 2 — Numeric consistency
- Every number must match fact graph or market data

### Gate 3 — Referential integrity
- Every reaction → valid event
- Every event → evidence

### Gate 4 — Phrase flagging
- Warnings for borderline language
- Fail closed.

---

## 7. Where Massive fits perfectly

Massive is ideal for L1 because:
- It handles numbers
- It is deterministic
- It is time-aligned
- It does not hallucinate

**Massive feeds:**
- Market outcomes
- Reaction windows
- Technicals
- Movers

**News feeds feed:**
- Event timeline
- Evidence only

This separation is what institutions expect.

---

## 8. What happens next (beyond L1)

Once L1 is stable:

- **Layer-2:** interpretation, attribution of causality, outlooks (LLM-generated, but grounded in L1)
- **Layer-3:** portfolio-specific mapping ("how did our thesis differ?")

But those layers consume L1. They never redefine it.

---

### Final mental model (keep this)

- **L1 = ledger of record**
- **L2 = analysis**
- **L3 = decision context**

If L1 is clean, everything above it becomes safe.
