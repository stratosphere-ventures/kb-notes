# Layer 1 Synthetic Data Generation (SDG) System

Generates realistic Layer 1 market fact graph JSON files and renders them using Jinja2 templates.

## Files

### Scripts
- **generate_l1.py** - Main SDG script that generates synthetic day JSON data
- **validate_l1.py** - Validates generated JSON files against schema.json (warn-only)
- **render_l1.py** - Renders JSON files to markdown using Jinja2 templates

### Templates
- **market_wrap_l1.md.j2** - Jinja2 template for Layer 1 daily market wrap
- **schema.json** - JSON Schema for Layer 1 fact graph validation

### Output Directories
- **sample_data/** - Generated JSON files (5 days)
- **sample_output/** - Rendered markdown files (5 days)

## Usage

### Generate, Validate, and Render (Full Pipeline)
```bash
# Generate 5 days with specific random seed (reproducible)
python3 kb-notes/tier1/generate_l1.py --seed 42

# Generate without validation/rendering
python3 kb-notes/tier1/generate_l1.py --skip-validate --skip-render

# Generate without rendering
python3 kb-notes/tier1/generate_l1.py --skip-render

# Generate without validation
python3 kb-notes/tier1/generate_l1.py --skip-validate
```

### Validate Only
```bash
python3 kb-notes/tier1/validate_l1.py

# Validate with custom schema
python3 kb-notes/tier1/validate_l1.py --schema custom_schema.json
```

### Render Only
```bash
python3 kb-notes/tier1/render_l1.py

# Render with custom template
python3 kb-notes/tier1/render_l1.py --template custom_template.j2

# Render from custom input directory
python3 kb-notes/tier1/render_l1.py --input-dir custom_data/
```

## Generated Data

### 5 Synthetic Days

**Specific Dates with Known Market Patterns:**
1. **2026-01-15** (Thursday) - Options expiration, Fed Chair speech
2. **2026-02-28** (Friday) - Month-end, PCE release
3. **2026-04-30** (Thursday) - Q1 GDP release, major earnings

**Consecutive Trading Days:**
4. **2026-03-13** (Friday) - CPI release
5. **2026-03-16** (Monday) - Follow-through from CPI, Treasury auction

### Content Structure

Each generated JSON file includes:
- **Governance**: UUID doc_id, timestamps, versioning, provenance
- **Market Outcomes**: Indices (SPX, NDX, DJIA, RUT, QQQ, IWM), Rates/FX/Commodities, Volatility, Breadth
- **Events** (3-6 per day): Fed speeches, economic releases, Treasury auctions, earnings 8-K, corporate actions, regulatory releases
- **Reaction Windows** (per event): Measured moves for indices + 3-5 affected tickers
- **Movers**: Top 5 gainers and decliners with volume multiples
- **Sectors**: 7 sector ETFs (XLK, XLF, XLE, XLU, XLRE, XLY, XLC)
- **Tickers** (10-15 per day): Close, return, volume multiple, technicals, filings identified
- **Evidence Items** (one per event): Source, URL, excerpt, doc_id, chunk_id

### Event Types

Random mix of:
- **Fed Speech**: Speaker, topic, factual quotes (no interpretation)
- **Economic Releases**: CPI, PPI, PCE, ISM PMI, Jobless Claims, Retail Sales with detailed breakdowns
- **Treasury Auctions**: 2Y/5Y/10Y/30Y with yield, bid-to-cover, indirect bidder %
- **Earnings 8-K**: EPS, revenue, guidance, segment data
- **Corporate Actions**: M&A announcements, buyback authorizations, dividend declarations, spin-offs, partnerships
- **Regulatory Releases**: SEC enforcement, rule proposals, guidance updates, policy clarifications

### Key Features

1. **No Interpretation**: All statements are factual observations. No "because", "due to", "caused by"
2. **Detailed Event Facts**: EPS, revenue, guidance breakdowns for earnings; YoY/MoM data for releases
3. **Consecutive Day Continuity**: Mar 16 prices based on Mar 13 closes ±1.5% drift
4. **Reaction Windows**: Factual observations of price moves around events
5. **Evidence Links**: Each event has corresponding evidence item with event_id linkage
6. **UTC Timestamps**: All timestamps in UTC format (e.g., 2026-01-15T14:30:00Z)
7. **Reproducible UUIDs**: Random UUID4 for each doc_id
8. **Chunk Markers**: 6 chunk_id markers for retrieval (wrap_summary, wrap_timeline, wrap_reactions, wrap_movers_sectors, wrap_ticker_panels, wrap_evidence)

### Ticker Universe (~50 stocks)

**Mega-cap:** AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA, BRK.B

**Financials:** JPM, BAC, WFC, GS, MS, BLK, SCHW

**Healthcare:** UNH, JNJ, PFE, ABT, TMO, LLY, MRK

**Energy:** XOM, CVX, COP, SLB, PXD

**Industrials:** CAT, DE, HON, GE, UPS

**Consumer:** PG, KO, MCD, HD, NKE, PEP

**Sector ETFs:** XLK (Tech), XLF (Financials), XLE (Energy), XLU (Utilities), XLRE (Real Estate), XLY (Consumer Disc), XLC (Comm Services)

## Validation

JSON schema validation uses `jsonschema` library:

```bash
pip install jsonschema
```

Validation prints warnings (not errors) for any schema violations and always exits with code 0.

## Rendering

Jinja2 template rendering:

```bash
pip install jinja2
```

Template renders with chunk_id markers preserved for retrieval systems.

## Dependencies

- Python 3.7+
- jsonschema (for validation)
- jinja2 (for rendering)

## Notes

- All market data is synthetic and for testing/development purposes only
- Use `--seed` parameter for reproducible results
- Scripts automatically create output directories if they don't exist
- Scripts can be run independently or as part of the full pipeline
