# Market Facts Wrap - January 8, 2026

## 0) Document Identity and Governance Block

```yaml
doc_type: market_wrap_l1
doc_id: 6ba7b814-9adc-11d1-80b4-00c04fd430c8
doc_key: market_wrap/us/2026-01-08
doc_version: 1
is_current: true
is_active: true
published_ts: 2026-01-08T20:15:00Z
asof_ts: 2026-01-08T16:00:00Z
market_session: post
region: US
universe_scope: SPX
trust_tier: 1
license_policy: internal
sources_used:
  - source_name: Bloomberg
    source_type: market_data
    count: 1200
    max_age: 5m
  - source_name: Refinitiv
    source_type: market_data
    count: 850
    max_age: 15m
data_provenance:
  market_data_vendor: Bloomberg
  market_data_version: bbg_equities_v2.5
  calc_versions: [technicals_v1.3.0, impact_v1.1.2]
hashes:
  raw_hash: 1a2b3c4d5e6f78901234567890abcdef12345678
  normalized_hash: 9z8y7x6w5v4u3t2s1r0q9876543210abcdef
audit:
  created_by: market_data_engine
  created_ts: 2026-01-08T20:15:00Z
  pipeline_version: v2.2.1
```

## 1) Executive Fact Summary

### 1.1 Headline
"Tech leads market rally on cooling jobs data; SPX up 1.2%, VIX drops below 15"

### 1.2 Index/Benchmark Closes
- **SPX**: 4,912.50 (+1.2%); Range: 4,855.75 - 4,915.20
- **NDX**: 19,487.30 (+1.8%); Range: 19,100.45 - 19,495.60
- **RUT**: 2,185.40 (+0.9%); Range: 2,165.30 - 2,188.90
- **DJIA**: 38,450.75 (+0.8%); Range: 38,150.30 - 38,465.20
- **QQQ**: 482.15 (+1.9%); Range: 472.85 - 482.75
- **IWM**: 218.90 (+0.8%); Range: 216.40 - 219.20
- **Breadth**: Advancers 2,845, Decliners 2,145; % above 200DMA: 62%

### 1.3 Rates/FX/Commodities
- **UST 2Y**: -5.4 bps to 4.12%
- **UST 10Y**: -6.1 bps to 4.18%
- **DXY**: 101.85 (-0.6%)
- **EURUSD**: 1.0980 (+0.4%)
- **WTI Crude**: $77.25 (+2.1%)
- **Gold**: $2,065.80 (+1.2%)

### 1.4 Volatility
- **VIX**: 14.75 (-1.25, -7.8%)
- **VIX9D**: 15.60 (-0.90, -5.5%)

## 2) Session Timeline

### 08:30 ET — Nonfarm Payrolls (BLS)
- **Published**: 2026-01-08T08:30:00Z
- **Session**: pre
- **Facts**:
  - NFP: +175K vs +190K expected
  - Unemployment Rate: 3.8% vs 3.7% expected
  - Average Hourly Earnings: +0.2% MoM vs +0.3% expected
- **Source**: BLS Employment Situation Summary
- **Entities**: SPX, NDX, UST yields, USD

### 10:00 ET — ISM Services PMI
- **Published**: 2026-01-08T10:00:00Z
- **Session**: regular
- **Facts**:
  - ISM Services PMI: 52.4 vs 50.8 expected
  - Prices Paid: 56.2 vs 58.1 prior
  - New Orders: 53.8 vs 51.5 prior
- **Source**: Institute for Supply Management
- **Entities**: Cyclical sectors, Financials

### 16:05 ET — AMZN Guidance Update
- **Published**: 2026-01-08T21:05:00Z
- **Session**: post
- **Facts**:
  - Raises Q1 revenue guidance to $158-162B from $150-155B
  - AWS growth outlook raised to +18-20% YoY
- **Source**: AMZN 8-K Filing
- **Entities**: AMZN, Cloud sector, NDX

## 3) Measured Market Reactions

### 3.1 Index Reaction Windows
**SPX**:
- Pre_to_close: +1.2%
- NFP_t0_to_t+60m: +0.8%
- Close_to_close: +1.2%

**NDX**:
- Pre_to_close: +1.8%
- NFP_t0_to_t+60m: +1.2%
- Close_to_close: +1.8%

**VIX**:
- Pre_to_close: -7.8%
- NFP_t0_to_t+60m: -10.2%
- Close_to_close: -7.8%

### 3.2 Top Movers
**Top 5 SPX Gainers**:
1. AMZN +4.8% (2.3x avg volume) - Consumer Discretionary
2. NVDA +3.9% (1.9x avg volume) - Technology
3. META +3.7% (1.6x avg volume) - Communication Services
4. GOOGL +3.2% (1.4x avg volume) - Communication Services
5. AMD +2.9% (1.8x avg volume) - Technology

**Top 5 SPX Losers**:
1. UNH -2.1% (1.6x avg volume) - Health Care
2. JNJ -1.8% (1.4x avg volume) - Health Care
3. PG -1.5% (1.3x avg volume) - Consumer Staples
4. KO -1.3% (1.2x avg volume) - Consumer Staples
5. XOM -1.1% (1.1x avg volume) - Energy

### 3.3 Sector Performance
| Sector (ETF) | Return | Volume Multiple |
|--------------|--------|-----------------|
| Technology (XLK) | +2.3% | 1.4x |
| Communication Services (XLC) | +2.1% | 1.3x |
| Consumer Discretionary (XLY) | +1.9% | 1.5x |
| Financials (XLF) | +0.8% | 1.1x |
| Energy (XLE) | -0.5% | 0.9x |
| Health Care (XLV) | -0.7% | 1.2x |
| Consumer Staples (XLP) | -1.0% | 1.0x |

## 4) Company Fact Panels

### AMZN
- **Close**: $185.75 (+4.8%)
- **Volume**: 58.4M shares (2.3x avg)
- **Technicals**: 
  - Above 50DMA ($175.40), Above 200DMA ($168.20)
  - RSI(14): 68 (approaching overbought)
- **News**: 
  - Raised Q1 revenue guidance to $158-162B
  - AWS growth outlook increased to +18-20% YoY
- **Source**: AMZN 8-K Filing

### NVDA
- **Close**: $512.30 (+3.9%)
- **Volume**: 78.2M shares (1.9x avg)
- **Technicals**:
  - Above 50DMA ($490.20), Above 200DMA ($450.80)
  - MACD: Bullish crossover
- **No material news**
- **Source**: N/A

### UNH
- **Close**: $485.20 (-2.1%)
- **Volume**: 4.8M shares (1.6x avg)
- **Technicals**:
  - Below 50DMA ($498.50), Below 200DMA ($505.30)
  - Support at $480.00
- **News**: 
  - Medicare Advantage rate concerns resurface
- **Source**: Industry reports

## 5) Evidence Appendix

```yaml
evidence_items:
  - source_name: Bureau of Labor Statistics
    source_type: government_release
    canonical_url: https://www.bls.gov/news.release/empsit.nr0.htm
    published_ts: 2026-01-08T08:30:00Z
    excerpt: "Total nonfarm payroll employment increased by 175,000 in December..."
    doc_id: BLS-2026-01-08-NFP
    chunk_id: nfp_dec_2025

  - source_name: Institute for Supply Management
    source_type: economic_indicator
    canonical_url: https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/services/
    published_ts: 2026-01-08T10:00:00Z
    excerpt: "The Services PMI® registered 52.4 percent in December, 1.6 percentage points higher than November's reading of 50.8 percent."
    doc_id: ISM-SERVICES-2026-01
    chunk_id: ism_services_jan2026

  - source_name: Amazon.com, Inc.
    source_type: sec_filing
    canonical_url: https://www.sec.gov/Archives/edgar/data/1018724/000101872426000012/amzn-20260108x8k.htm
    published_ts: 2026-01-08T21:05:00Z
    excerpt: "Amazon.com today announced it is raising its Q1 2026 revenue guidance to $158-162 billion..."
    doc_id: AMZN-8K-20260108
    chunk_id: amzn_guidance_update

  - source_name: Bloomberg Terminal
    source_type: market_data
    canonical_url: internal://market_data/equities/us/2026/01/08
    published_ts: 2026-01-08T16:00:00Z
    excerpt: "Market close data for January 8, 2026 trading session"
    doc_id: BLOOMBERG-MKT-2026-01-08
    chunk_id: bloomberg_eod_20260108
```

## Market Context
- **Trading Volume**: 4.2B shares (SPX components)
- **Market Sentiment**: Bullish (AAII Bull-Bear Spread: +12.5)
- **Notable Flows**: $1.2B into Tech ETFs, $850M out of Health Care ETFs
- **Earnings Watch**: AAPL, MSFT, GOOGL report next week
- **Economic Calendar**: CPI (Jan 13), PPI (Jan 14), Retail Sales (Jan 15)

---

This document follows the Layer 1 specification with:
1. Machine-readable metadata and governance
2. Fact-based reporting without speculation
3. Clear source attribution
4. Structured data for programmatic consumption
5. Separation of facts from interpretation

All numerical values are sourced from market data providers or official releases, with clear timestamps and versioning for auditability.