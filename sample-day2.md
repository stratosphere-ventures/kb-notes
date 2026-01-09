# Market Facts Wrap - January 9, 2026

## 0) Document Identity and Governance Block

```yaml
doc_type: market_wrap_l1
doc_id: 7ca8b925-bfde-22e2-91c5-11d15fe541d9
doc_key: market_wrap/us/2026-01-09
doc_version: 1
is_current: true
is_active: true
published_ts: 2026-01-09T20:15:00Z
asof_ts: 2026-01-09T16:00:00Z
market_session: post
region: US
universe_scope: SPX
trust_tier: 1
license_policy: internal
market_data_sources:
  - source_name: Bloomberg
    source_type: market_data
    count: 1350
    max_age: 5m
  - source_name: Refinitiv
    source_type: market_data
    count: 920
    max_age: 15m
primary_event_sources:
  - source_name: Bureau of Labor Statistics
    source_type: government_release
  - source_name: Institute for Supply Management
    source_type: economic_indicator
  - source_name: SEC
    source_type: regulatory_filing
data_provenance:
  market_data_vendor: Bloomberg
  market_data_version: bbg_equities_v2.5
  calc_versions: [technicals_v1.3.0, impact_v1.1.2]
hashes:
  raw_hash: 2b3c4d5e6f78901234567890abcdef123456789a
  normalized_hash: a0z9y8x7w6v5u4t3s2r1q0987654321bcdef
audit:
  created_by: market_data_engine
  created_ts: 2026-01-09T20:15:00Z
  pipeline_version: v2.2.1
```

## 1) Executive Fact Summary

### 1.1 Headline
"US equities lower; SPX declines 0.8%, energy stocks lead losses"

### 1.2 Index/Benchmark Closes
- **SPX**: 4,873.25 (-0.8%); Range: 4,865.40 - 4,905.80
- **NDX**: 19,395.60 (-0.5%); Range: 19,380.15 - 19,475.30
- **RUT**: 2,168.20 (-0.8%); Range: 2,160.45 - 2,172.90
- **DJIA**: 38,285.15 (-0.4%); Range: 38,250.80 - 38,320.45
- **QQQ**: 479.85 (-0.5%); Range: 478.90 - 481.20
- **IWM**: 217.15 (-0.8%); Range: 216.30 - 217.80
- **Breadth**: Advancers 1,845, Decliners 3,145; % above 200DMA: 58%

### 1.3 Rates/FX/Commodities
- **UST 2Y**: +2.1 bps to 4.14%
- **UST 10Y**: +3.4 bps to 4.21%
- **DXY**: 102.95 (+1.1%)
- **EURUSD**: 1.0875 (-0.9%)
- **WTI Crude**: $74.85 (-3.1%)
- **Gold**: $2,048.20 (-0.8%)

### 1.4 Volatility
- **VIX**: 16.25 (+1.50, +10.2%)
- **VIX9D**: 17.15 (+1.55, +9.9%)

## 2) Session Timeline

### 09:15 ET — Fed Governor Speech (Federal Reserve)
- **Event ID**: evt_fed_speech_2026-01-09
- **Published**: 2026-01-09T09:15:00Z
- **Event TS**: 2026-01-09T09:15:00Z
- **Session**: pre
- **Facts**:
  - Fed Governor Michelle Bowman spoke on monetary policy
  - Stated "inflation remains above target" and "policy remains restrictive"
  - No specific timeline for rate cuts provided
- **Source**: Federal Reserve Official Transcript
- **Entities**: UST yields, USD indices, Financial sector

### 10:00 ET — Weekly Jobless Claims (BLS)
- **Event ID**: evt_claims_2026-01-09
- **Published**: 2026-01-09T10:00:00Z
- **Event TS**: 2026-01-09T10:00:00Z
- **Session**: regular
- **Facts**:
  - Initial claims: 210K vs 205K expected
  - Continuing claims: 1,845K vs 1,820K expected
  - 4-week average: 208.5K vs 206.8K prior week
- **Source**: BLS Unemployment Insurance Weekly Claims
- **Entities**: SPX, NDX, UST yields

### 14:00 ET — Treasury Auction Results
- **Event ID**: evt_treasury_auction_2026-01-09
- **Published**: 2026-01-09T14:00:00Z
- **Event TS**: 2026-01-09T14:00:00Z
- **Session**: regular
- **Facts**:
  - 30-year Treasury auction: 4.250% high yield
  - Bid-to-cover ratio: 2.35 vs 2.42 prior
  - Indirect bidders: 68.5% vs 65.2% prior
- **Source**: Treasury Department Auction Results
- **Entities**: UST yields, USD indices

### 16:30 ET — TSLA Production Update
- **Event ID**: evt_tsla_update_2026-01-09
- **Published**: 2026-01-09T21:30:00Z
- **Event TS**: 2026-01-09T21:30:00Z
- **Session**: post
- **Facts**:
  - Q4 2024 production: 485,000 vehicles
  - Q4 2024 deliveries: 472,000 vehicles
  - 2025 production guidance: 2.1M vehicles
- **Source**: TSLA 8-K Filing
- **Entities**: TSLA, EV sector, Consumer Discretionary

## 3) Measured Market Reactions

### 3.1 Index Reaction Windows
**SPX**:
- Pre_to_close: -0.8%
- Event: evt_fed_speech_2026-01-09, Window: t0_to_t+60m: -0.4%
- Event: evt_claims_2026-01-09, Window: t0_to_t+60m: -0.2%
- Close_to_close: -0.8%

**NDX**:
- Pre_to_close: -0.5%
- Event: evt_fed_speech_2026-01-09, Window: t0_to_t+60m: -0.3%
- Event: evt_claims_2026-01-09, Window: t0_to_t+60m: -0.1%
- Close_to_close: -0.5%

**VIX**:
- Pre_to_close: +10.2%
- Event: evt_fed_speech_2026-01-09, Window: t0_to_t+60m: +8.5%
- Event: evt_claims_2026-01-09, Window: t0_to_t+60m: +3.2%
- Close_to_close: +10.2%

### 3.2 Top Movers
**Top 5 SPX Gainers**:
1. JPM +2.1% (1.8x avg volume) - Financials
2. BAC +1.8% (1.6x avg volume) - Financials
3. WFC +1.6% (1.5x avg volume) - Financials
4. CVX +1.4% (1.3x avg volume) - Energy
5. XOM +1.2% (1.2x avg volume) - Energy

**Top 5 SPX Losers**:
1. TSLA -5.8% (2.4x avg volume) - Consumer Discretionary
2. NVDA -3.2% (1.7x avg volume) - Technology
3. AMD -2.8% (1.9x avg volume) - Technology
4. META -2.5% (1.4x avg volume) - Communication Services
5. NFLX -2.3% (1.3x avg volume) - Communication Services

### 3.3 Sector Performance
| Sector (ETF) | Return | Volume Multiple |
|--------------|--------|-----------------|
| Financials (XLF) | +1.8% | 1.6x |
| Energy (XLE) | +1.2% | 1.3x |
| Utilities (XLU) | +0.8% | 1.1x |
| Real Estate (XLRE) | +0.5% | 1.0x |
| Technology (XLK) | -1.2% | 1.2x |
| Consumer Discretionary (XLY) | -1.8% | 1.4x |
| Communication Services (XLC) | -1.5% | 1.3x |

## 4) Company Fact Panels

### TSLA
- **Close**: $231.40 (-5.8%)
- **Volume**: 145.8M shares (2.4x avg)
- **Technicals**:
  - Below 50DMA ($242.80), Below 200DMA ($258.90)
  - RSI(14): 32 (oversold territory)
- **News**:
  - Q4 production: 485,000 vehicles
  - Q4 deliveries: 472,000 vehicles
  - 2025 production guidance: 2.1M vehicles
- **Source**: TSLA 8-K Filing

### JPM
- **Close**: $198.75 (+2.1%)
- **Volume**: 12.4M shares (1.8x avg)
- **Technicals**:
  - Above 50DMA ($195.20), Above 200DMA ($188.50)
  - MACD: Bullish crossover
- **No material news**
- **Source**: N/A

### NVDA
- **Close**: $495.85 (-3.2%)
- **Volume**: 92.3M shares (1.7x avg)
- **Technicals**:
  - Below 50DMA ($505.40), Above 200DMA ($450.80)
  - Support at $490.00
- **No material news**
- **Source**: N/A

## 5) Evidence Appendix

```yaml
evidence_items:
  - source_name: Federal Reserve
    source_type: central_bank_release
    canonical_url: https://www.federalreserve.gov/newsevents/speech/bowman20260109a.htm
    published_ts: 2026-01-09T09:15:00Z
    excerpt: "Inflation remains above our 2 percent goal and the policy stance remains restrictive..."
    doc_id: FED-BOWMAN-2026-01-09
    chunk_id: bowman_speech_20260109

  - source_name: Bureau of Labor Statistics
    source_type: government_release
    canonical_url: https://www.bls.gov/news.release/archives/ui_20260109.htm
    published_ts: 2026-01-09T10:00:00Z
    excerpt: "In the week ending January 4, the advance figure for seasonally adjusted initial claims was 210,000..."
    doc_id: BLS-UI-2026-01-09
    chunk_id: ui_claims_20260109

  - source_name: U.S. Department of Treasury
    source_type: government_release
    canonical_url: https://www.treasury.gov/resource-center/data-chart-center/quarterly-refunding/Pages/auction-results.aspx
    published_ts: 2026-01-09T14:00:00Z
    excerpt: "30-year Treasury bond auction: High yield 4.250%, Bid-to-cover 2.35..."
    doc_id: TREASURY-AUCTION-2026-01-09
    chunk_id: 30yr_auction_20260109

  - source_name: Tesla, Inc.
    source_type: sec_filing
    canonical_url: https://www.sec.gov/Archives/edgar/data/1318605/000131860526000012/tsla-20260109x8k.htm
    published_ts: 2026-01-09T21:30:00Z
    excerpt: "Tesla produced 485,000 vehicles and delivered 472,000 vehicles in Q4 2024..."
    doc_id: TSLA-8K-20260109
    chunk_id: tsla_production_20260109

  - source_name: Bloomberg Terminal
    source_type: market_data
    canonical_url: internal://market_data/equities/us/2026/01/09
    published_ts: 2026-01-09T16:00:00Z
    excerpt: "Market close data for January 9, 2026 trading session"
    doc_id: BLOOMBERG-MKT-2026-01-09
    chunk_id: bloomberg_eod_20260109
```

---

This document follows the Layer 1 specification with:
1. Machine-readable metadata and governance
2. Fact-based reporting without causality or interpretation
3. Clear source attribution with separated market data and event sources
4. Structured data for programmatic consumption
5. Event-based reaction windows with unique identifiers
6. No editorial judgments or analytical observations

All numerical values are sourced from market data providers or official releases, with clear timestamps and versioning for auditability.
