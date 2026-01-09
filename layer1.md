# Layer 1 Financial Document: Market Facts Wrap

## Template Structure

### 0) Document Identity and Governance Block (required)

**Purpose**: provenance, time semantics, deletion/replay, entitlements

```yaml
doc_type: market_wrap_l1
doc_id: UUID
doc_key: market_wrap/us/2026-01-07
doc_version: 1
is_current: true
is_active: true
published_ts: 2026-01-07T20:00:00Z
asof_ts: 2026-01-07T16:00:00Z
market_session: post
region: US
universe_scope: SPX
trust_tier: 1
license_policy: internal
sources_used:
  - source_name: Massive
    source_type: market_data
    count: 1500
    max_age: 5m
data_provenance:
  market_data_vendor: Massive
  market_data_version: massive_bars_v3
  calc_versions: [technicals_v1.2.1, impact_v1.0.0]
hashes:
  raw_hash: abc123def456
  normalized_hash: def456abc789
audit:
  created_by: system
  created_ts: 2026-01-07T20:00:00Z
  pipeline_version: v2.1.0
```

**Hard rule**: This block is machine-validated. If missing, the document is not ingestable.

### 1) Executive Fact Summary (facts only; no drivers)

**Purpose**: one-screen snapshot of what happened

#### 1.1 Headline (factual, neutral)
"US equities higher; SPX closes at new high; VIX lower"

#### 1.2 Index/Benchmark closes (deterministic)
- **SPX**: 4,850.25 (+0.8%); Range: 4,810.50 - 4,852.00
- **NDX**: 19,245.75 (+1.1%); Range: 19,050.25 - 19,258.50
- **RUT**: 2,150.80 (+0.6%); Range: 2,135.20 - 2,155.40
- **DJIA**: 38,125.45 (+0.7%); Range: 37,890.15 - 38,140.80
- **QQQ**: 475.32 (+1.0%); Range: 470.15 - 476.25
- **IWM**: 215.45 (+0.5%); Range: 214.20 - 215.80
- **SPY**: 485.02 (+0.8%); Range: 481.05 - 485.20
- **Breadth**: Advancers 3,245, Decliners 1,845; % above 200DMA: 68%

#### 1.3 Rates/FX/Credit/Commodities (deterministic)
- **UST 2Y**: +3.2 bps to 4.25%
- **UST 10Y**: +4.1 bps to 4.35%
- **DXY**: 102.45 (+0.2%)
- **EURUSD**: 1.0850 (-0.1%)
- **WTI Crude**: $75.80 (+1.5%)
- **Gold**: $2,045.30 (+0.3%)

#### 1.4 Volatility (deterministic)
- **VIX**: 14.25 (-0.85, -5.6%)
- **VIX9D**: 15.10 (-0.45, -2.9%)

**Hard rule**: Every number here must come from the market data/analytics store, not from text recall.

### 2) Session Timeline (attributed events only; no causality asserted)

**Purpose**: "what happened when" with evidence

#### 08:30 ET — CPI Release (BLS)
- **Published**: 2026-01-07T08:30:00Z
- **Session**: pre
- **Facts**: 
  - Headline CPI: +0.3% MoM vs +0.2% expected
  - Core CPI: +0.4% MoM vs +0.3% expected
  - YoY Headline: 3.4% vs 3.2% expected
- **Source**: BLS Press Release BLA-2026-001
- **Entities**: SPX, NDX, UST yields

#### 10:00 ET — FOMC Minutes Release
- **Published**: 2026-01-07T14:00:00Z
- **Session**: regular
- **Facts**: 
  - Participants discussed data-dependent approach
  - Several members noted progress on inflation
  - No specific policy guidance provided
- **Source**: Federal Reserve FOMC Minutes
- **Entities**: UST yields, USD indices

#### 16:05 ET — NVDA Earnings
- **Published**: 2026-01-07T21:05:00Z
- **Session**: post
- **Facts**:
  - EPS: $4.05 vs $3.82 expected
  - Revenue: $25.3B vs $24.2B expected
  - Q1 Guidance: $26.0B vs $25.5B expected
- **Source**: NVDA 8-K Filing
- **Entities**: NVDA, SPX, Technology sector

**Hard rule**: If you cannot cite a source for a timeline item, it does not go in Layer 1.

### 3) Measured Market Reactions (deterministic windows; "effects" as measurement)

**Purpose**: quantify moves around events without claiming "because."

#### 3.1 Index reaction windows (deterministic)

**SPX**:
- Pre_to_close: +0.8%
- CPI_t0_to_t+60m: +0.6%
- Close_to_close: +0.8%

**NDX**:
- Pre_to_close: +1.1%
- CPI_t0_to_t+60m: +0.9%
- Close_to_close: +1.1%

**VIX**:
- Pre_to_close: -5.6%
- CPI_t0_to_t+60m: -8.2%
- Close_to_close: -5.6%

#### 3.2 Top movers (deterministic, rules-based)

**Top 10 SPX Gainers**:
1. NVDA +5.2% (2.1x avg volume) - Technology
2. TSLA +4.8% (1.8x avg volume) - Consumer Discretionary
3. META +3.9% (1.5x avg volume) - Communication Services
4. AMD +3.7% (1.9x avg volume) - Technology
5. GOOGL +3.2% (1.3x avg volume) - Communication Services

**Top 10 SPX Losers**:
1. JPM -2.1% (1.4x avg volume) - Financials
2. BAC -1.8% (1.3x avg volume) - Financials
3. WMT -1.5% (1.2x avg volume) - Consumer Staples
4. KO -1.3% (1.1x avg volume) - Consumer Staples
5. PEP -1.2% (1.1x avg volume) - Consumer Staples

#### 3.3 Sector/industry performance (deterministic)

| Sector | Return | Volume |
|--------|--------|---------|
| Technology (XLK) | +2.1% | 1.3x |
| Communication Services (XLC) | +1.8% | 1.2x |
| Consumer Discretionary (XLY) | +1.5% | 1.1x |
| Financials (XLF) | -1.2% | 1.4x |
| Consumer Staples (XLP) | -0.8% | 1.0x |
| Energy (XLE) | +1.5% | 1.5x |

**Hard rule**: Use "following" not "because."
- **Allowed**: "Following the CPI print at 08:30, SPX rose +0.6% in 60 minutes."
- **Not allowed**: "SPX rose because CPI was cooler."

### 4) Company/Earnings Fact Panels

**Purpose**: facts for key tickers

#### NVDA
- **Close**: $485.09 (+5.2%)
- **Volume**: 82.5M shares (2.1x avg)
- **Technicals**: Above 50DMA ($465.20), Above 200DMA ($425.80)
- **Earnings**: EPS $4.05 vs $3.82 est; Revenue $25.3B vs $24.2B est
- **Guidance**: Q1 $26.0B vs $25.5B est
- **Source**: NVDA 8-K Filing, 2026-01-07

#### AAPL
- **Close**: $195.85 (+1.2%)
- **Volume**: 58.2M shares (1.1x avg)
- **Technicals**: Above 50DMA ($192.40), Above 200DMA ($185.60)
- **No earnings today**
- **Source**: N/A

#### TSLA
- **Close**: $245.30 (+4.8%)
- **Volume**: 125.8M shares (1.8x avg)
- **Technicals**: Above 50DMA ($235.50), Below 200DMA ($258.90)
- **No earnings today**
- **Source**: N/A

**Hard rule**: Keep "beats/misses" strictly numeric; no "strong results" language.

### 5) Evidence Appendix (citations ledger)

**Purpose**: audit and replay

```yaml
evidence_items:
  - source_name: Bureau of Labor Statistics
    source_type: government_release
    canonical_url: https://www.bls.gov/news.release/cpi.nr0.htm
    published_ts: 2026-01-07T08:30:00Z
    excerpt: "CPI for All Urban Consumers increased 0.3 percent in December on a seasonally adjusted basis..."
    doc_id: BLA-2026-001
    chunk_id: cpi_dec_2025
    
  - source_name: Federal Reserve
    source_type: central_bank_release
    canonical_url: https://www.federalreserve.gov/monetarypolicy/fomcminutes20260107.htm
    published_ts: 2026-01-07T14:00:00Z
    excerpt: "Participants emphasized that the Committee's policy decisions would remain data dependent..."
    doc_id: FOMC-2026-01-07
    chunk_id: minutes_intro
    
  - source_name: NVIDIA Corporation
    source_type: sec_filing
    canonical_url: https://www.sec.gov/Archives/edgar/data/0001045810/000095017026000123/nvda-20260107.htm
    published_ts: 2026-01-07T21:05:00Z
    excerpt: "Revenue for the fourth quarter ended January 26, 2025 was $25.3 billion, an increase of 16% from the previous quarter..."
    doc_id: NVDA-8K-20260107
    chunk_id: earnings_summary
    
  - source_name: Massive Market Data
    source_type: market_data_vendor
    canonical_url: internal://market_data/bars/spx/20260107
    published_ts: 2026-01-07T16:00:00Z
    excerpt: "SPX close: 4850.25, volume: 2.1B shares"
    doc_id: MASSIVE-BARS-20260107
    chunk_id: spx_eod
```

This appendix is what makes the system defensible.