#!/usr/bin/env python3
"""
Layer 1 Synthetic Data Generation (SDG) Script - v2
Improvements:
- Chronological dates for prev_close logic
- Single ticker universe per day (no mismatch across sections)
- Day-level latent state for realism + reduced duplication
- L1-neutral headlines (no "leads", no causal language)
- Evidence excerpts are fact-only (no "analysts", no "markets are")
- SEC/EDGAR URLs are either ticker-CIK consistent or synthetic://
"""

import json
import uuid
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse
import os
import sys
import subprocess
import hashlib

# 20 synthetic dates (5 specific patterns + 15 random dates)
DATES = [
    "2026-01-15",
    "2026-02-28",
    "2026-04-30",
    "2026-03-13",
    "2026-03-16",
    "2026-01-08",
    "2026-01-22",
    "2026-02-05",
    "2026-02-12",
    "2026-02-19",
    "2026-03-03",
    "2026-03-06",
    "2026-03-10",
    "2026-03-17",
    "2026-03-20",
    "2026-03-24",
    "2026-03-27",
    "2026-03-31",
    "2026-04-03",
    "2026-04-07",
    "2026-04-10",
    "2026-04-14",
    "2026-04-17",
    "2026-04-21",
    "2026-04-24",
    "2026-04-28",
]
PREVIOUS_CLOSES: Dict[str, Dict[str, Any]] = {}

# -----------------------------
# Universe + mappings (unchanged)
# -----------------------------
TICKER_UNIVERSE = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "NVDA",
    "TSLA",
    "BRK.B",
    "JPM",
    "BAC",
    "WFC",
    "GS",
    "MS",
    "BLK",
    "SCHW",
    "UNH",
    "JNJ",
    "PFE",
    "ABT",
    "TMO",
    "LLY",
    "MRK",
    "XOM",
    "CVX",
    "COP",
    "SLB",
    "PXD",
    "CAT",
    "DE",
    "HON",
    "GE",
    "UPS",
    "PG",
    "KO",
    "MCD",
    "HD",
    "NKE",
    "PEP",
    "XLK",
    "XLF",
    "XLE",
    "XLU",
    "XLRE",
    "XLY",
    "XLC",
]

SECTOR_MAP = {
    "AAPL": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Technology",
    "NVDA": "Technology",
    "AMZN": "Consumer Discretionary",
    "TSLA": "Consumer Discretionary",
    "META": "Communication Services",
    "BRK.B": "Financials",
    "JPM": "Financials",
    "BAC": "Financials",
    "WFC": "Financials",
    "GS": "Financials",
    "MS": "Financials",
    "BLK": "Financials",
    "SCHW": "Financials",
    "UNH": "Healthcare",
    "JNJ": "Healthcare",
    "PFE": "Healthcare",
    "ABT": "Healthcare",
    "TMO": "Healthcare",
    "LLY": "Healthcare",
    "MRK": "Healthcare",
    "XOM": "Energy",
    "CVX": "Energy",
    "COP": "Energy",
    "SLB": "Energy",
    "PXD": "Energy",
    "CAT": "Industrials",
    "DE": "Industrials",
    "HON": "Industrials",
    "GE": "Industrials",
    "UPS": "Industrials",
    "PG": "Consumer Staples",
    "KO": "Consumer Staples",
    "PEP": "Consumer Staples",
    "MCD": "Consumer Discretionary",
    "HD": "Consumer Discretionary",
    "NKE": "Consumer Discretionary",
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLY": "Consumer Discretionary",
    "XLC": "Communication Services",
}

INITIAL_PRICES = {
    "AAPL": 195.85,
    "MSFT": 415.30,
    "GOOGL": 175.50,
    "AMZN": 185.25,
    "META": 485.10,
    "NVDA": 485.09,
    "TSLA": 245.30,
    "BRK.B": 395.60,
    "JPM": 198.75,
    "BAC": 38.45,
    "WFC": 58.20,
    "GS": 420.15,
    "MS": 95.80,
    "BLK": 825.40,
    "SCHW": 72.30,
    "UNH": 525.80,
    "JNJ": 168.50,
    "PFE": 29.40,
    "ABT": 115.60,
    "TMO": 585.20,
    "LLY": 745.10,
    "MRK": 110.30,
    "XOM": 105.85,
    "CVX": 148.70,
    "COP": 108.50,
    "SLB": 48.90,
    "PXD": 245.80,
    "CAT": 295.60,
    "DE": 395.80,
    "HON": 215.40,
    "GE": 175.25,
    "UPS": 145.30,
    "PG": 158.75,
    "KO": 62.15,
    "MCD": 298.50,
    "HD": 385.40,
    "NKE": 98.50,
    "PEP": 175.80,
    "XLK": 195.50,
    "XLF": 38.75,
    "XLE": 92.40,
    "XLU": 68.85,
    "XLRE": 42.30,
    "XLY": 178.60,
    "XLC": 72.40,
}


def get_cik(ticker: str) -> str:
    cik_map = {
        "AAPL": "0000320193",
        "MSFT": "0000789019",
        "GOOGL": "0001652044",
        "AMZN": "0001018724",
        "META": "0001326801",
        "NVDA": "0001045810",
        "TSLA": "0001318605",
        "JPM": "0000019617",
        "BAC": "0000070858",
        "WFC": "0000072971",
        "GS": "0000886982",
        "MS": "0000029099",
        "UNH": "0000732516",
        "JNJ": "0000200406",
        "PFE": "0000078003",
    }
    return cik_map.get(ticker, "0000000000")


def stable_int_seed(*parts: str) -> int:
    h = hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def _short_hash(s: str, n: int = 8) -> str:
    """Generate short hash suffix for stable, unique IDs."""
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:n]


def calculate_future_date(date_str: str, days: int) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return (d + timedelta(days=days)).strftime("%Y-%m-%d")


def infer_market_session(timestamp_iso: str, region: str = "US") -> str:
    """
    Infer market_session from timestamp and region.
    For US equities (UTC timestamps):
    - Pre-market: 12:00-13:30 UTC (8:00-9:30 ET, accounting for ~UTC-5/UTC-4)
    - Regular: 13:30-20:30 UTC (9:30-16:30 ET, covers both EST and EDT)
    - Post-market: 20:30-01:00 UTC (16:30-21:00 ET, wraps to next day)
    """
    if region != "US":
        return "regular"  # Default for non-US; extend later
    
    try:
        dt = datetime.strptime(timestamp_iso, "%Y-%m-%dT%H:%M:%SZ")
        hour = dt.hour
        
        # US equities session windows (UTC)
        if hour < 13 or (hour == 13 and dt.minute < 30):
            return "pre"
        elif hour < 20 or (hour == 20 and dt.minute < 30):
            return "regular"
        else:  # 20:30+ UTC
            return "post"
    except (ValueError, AttributeError):
        return "regular"  # Fallback


# -----------------------------
# Text sanitization (L1-neutral, fact-only)
# -----------------------------
FORBIDDEN = ["should", "could", "may", "likely", "expected", "forecast", "outlook", "because", "due to", "driven by"]


def sanitize_l1_text(s: str) -> str:
    s2 = s or ""
    low = s2.lower()
    for tok in FORBIDDEN:
        if tok in low:
            # blunt but effective for Tier-1 synthetic
            s2 = re.sub(rf"\b{re.escape(tok)}\b", "reported", s2, flags=re.IGNORECASE)
            low = s2.lower()
    # strip interpretive connectors
    s2 = re.sub(r"\b(investors|sentiment|relief|concerns)\b", "", s2, flags=re.IGNORECASE)
    s2 = re.sub(r"\s{2,}", " ", s2).strip()
    return s2


# -----------------------------
# Day-level latent state (anti-degeneracy)
# -----------------------------
def generate_day_state(rng: random.Random) -> Dict[str, float]:
    # Simple bounded latent factors. These drive returns and co-movements.
    return {
        "risk": rng.uniform(-1.0, 1.0),  # negative = risk-off day
        "rates": rng.uniform(-1.0, 1.0),  # positive = rates up
        "energy": rng.uniform(-1.0, 1.0),  # positive = oil up
        "idiosyncratic": rng.uniform(-0.5, 0.5),
    }


# -----------------------------
# Governance (make sources consistent)
# -----------------------------
def generate_governance(date: str, doc_id: str) -> Dict[str, Any]:
    return {
        "date": date,
        "region": "US",
        "market_session": "post",
        "published_ts": f"{date}T20:00:00Z",
        "asof_ts": f"{date}T16:00:00Z",
        "universe_scope": "SPX",
        "doc_version": 1,
        "trust_tier": 1,
        "license_policy": "internal_synthetic",
        "market_data_vendor": "Massive",
        "market_data_version": "massive_bars_v3",
        "calc_versions": ["technicals_v1.2.1", "impact_v1.0.1"],
        "pipeline_version": "v2.2.0",
        "doc_id": doc_id,
        "doc_key": f"market_wrap/us/{date}",
        "is_current": True,
        "is_active": True,
        "sources_used": [
            {
                "source_name": "Massive",
                "source_type": "market_data",
                "count": 0,
                "max_age_days": 0,
            },
            {
                "source_name": "SyntheticWire",
                "source_type": "news_wire_synthetic",
                "count": 0,
                "max_age_days": 0,
            },
        ],
    }


# -----------------------------
# Market outcomes (correlated, less duplication)
# -----------------------------

def generate_market_outcomes(
    date: str, prev_date: Optional[str], rng: random.Random, state: Dict[str, float]
) -> Dict[str, Any]:
    base = PREVIOUS_CLOSES.get(prev_date, {}).get("indices", {}) if prev_date else {}

    def clamp(x: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, x))

    # Baselines (use prev close when available; else use static anchors)
    base_spx  = float(base.get("SPX", 4850.25))
    base_ndx  = float(base.get("NDX", 19245.75))
    base_djia = float(base.get("DJIA", 38125.45))
    base_rut  = float(base.get("RUT", 2150.80))
    base_qqq  = float(base.get("QQQ", 475.32))
    base_iwm  = float(base.get("IWM", 215.45))

    # Risk drives SPX/NDX; idiosyncratic adds noise (percent returns)
    spx_ret  = clamp(state["risk"] * 0.90 + rng.uniform(-0.40, 0.40), -2.5, 2.5)
    ndx_ret  = clamp(state["risk"] * 1.15 + rng.uniform(-0.55, 0.55), -3.0, 3.0)
    djia_ret = clamp(state["risk"] * 0.70 + rng.uniform(-0.35, 0.35), -2.2, 2.2)
    rut_ret  = clamp(state["risk"] * 1.00 + rng.uniform(-0.60, 0.60), -3.2, 3.2)
    qqq_ret  = clamp(ndx_ret * 0.85 + rng.uniform(-0.25, 0.25), -3.0, 3.0)
    iwm_ret  = clamp(rut_ret * 0.80 + rng.uniform(-0.25, 0.25), -3.0, 3.0)

    # Convert to closes
    spx_close  = round(base_spx  * (1 + spx_ret / 100), 2)
    ndx_close  = round(base_ndx  * (1 + ndx_ret / 100), 2)
    djia_close = round(base_djia * (1 + djia_ret / 100), 2)
    rut_close  = round(base_rut  * (1 + rut_ret / 100), 2)
    qqq_close  = round(base_qqq  * (1 + qqq_ret / 100), 2)
    iwm_close  = round(base_iwm  * (1 + iwm_ret / 100), 2)

    # High/low must bracket close; generate spreads first then apply
    def make_range(close: float) -> Dict[str, float]:
        up = rng.uniform(0.002, 0.010)
        dn = rng.uniform(0.002, 0.010)
        low = round(close * (1 - dn), 2)
        high = round(close * (1 + up), 2)
        # Guarantee strict ordering even after rounding
        if low >= close:
            low = round(close - max(0.01, close * 0.002), 2)
        if high <= close:
            high = round(close + max(0.01, close * 0.002), 2)
        if low >= high:
            high = round(low + 0.02, 2)
        return {"low": low, "high": high}

    spx_rng = make_range(spx_close)
    ndx_rng = make_range(ndx_close)

    # -----------------------------
    # Rates / FX / Commodities
    # -----------------------------
    # YIELDS ARE PERCENT LEVELS; CHANGES ARE IN BPS.
    ust_2y_level = round(4.15 + state["rates"] * 0.06 + rng.uniform(-0.03, 0.03), 2)
    ust_10y_level = round(4.35 + state["rates"] * 0.08 + rng.uniform(-0.05, 0.05), 2)

    ust_2y_change_bps = round(rng.uniform(-6.0, 6.0), 1)   # daily bps move
    ust_10y_change_bps = round(rng.uniform(-8.0, 8.0), 1)

    # DXY: index level + pct change
    dxy_level = round(102.45 + state["rates"] * 0.30 + rng.uniform(-0.25, 0.25), 2)
    dxy_change_pct = round(rng.uniform(-0.60, 0.60), 2)

    # EURUSD: ratio + abs + pct change
    eurusd_level = round(1.0850 - state["rates"] * 0.004 + rng.uniform(-0.003, 0.003), 4)
    eurusd_change_abs = round(rng.uniform(-0.0060, 0.0060), 4)
    eurusd_change_pct = round((eurusd_change_abs / max(1e-9, eurusd_level - eurusd_change_abs)) * 100, 2)

    # WTI: USD level + pct change
    wti_level = round(75.80 + state["energy"] * 2.0 + rng.uniform(-1.2, 1.2), 2)
    wti_change_pct = round((wti_level / 75.80 - 1) * 100, 2)

    # Gold: USD level + pct change
    gold_level = round(2045.30 + (-state["rates"]) * 10 + rng.uniform(-8, 8), 2)
    gold_change_pct = round((gold_level / 2045.30 - 1) * 100, 2)

    # Volatility: index levels + point change (not percent)
    vix_level = round(14.25 + (-state["risk"]) * 1.2 + rng.uniform(-0.6, 0.6), 2)
    vix9d_level = round(15.10 + (-state["risk"]) * 1.0 + rng.uniform(-0.6, 0.6), 2)
    vix_change_pts = round(rng.uniform(-1.5, 1.5), 2)
    vix9d_change_pts = round(rng.uniform(-1.5, 1.5), 2)

    adv = rng.randint(1500, 3500)
    dec = rng.randint(1500, 3500)
    pct_above_200 = round(clamp(50 + spx_ret * 5 + rng.uniform(-5, 5), 30, 80), 1)

    headline = sanitize_l1_text(
        f"US equities: SPX {spx_ret:+.2f}%, NDX {ndx_ret:+.2f}%, "
        f"DJIA {djia_ret:+.2f}%, RUT {rut_ret:+.2f}%."
    )

    out = {
        "headline_neutral": headline,
        "indices": [
            {
                "symbol": "SPX",
                "prev_close": round(base_spx, 2),
                "close": spx_close,
                "return_pct": round(spx_ret, 2),
                **spx_rng,
            },
            {
                "symbol": "NDX",
                "prev_close": round(base_ndx, 2),
                "close": ndx_close,
                "return_pct": round(ndx_ret, 2),
                **ndx_rng,
            },
            {"symbol": "RUT", "prev_close": round(base_rut, 2), "close": rut_close, "return_pct": round(rut_ret, 2)},
            {"symbol": "DJIA", "prev_close": round(base_djia, 2), "close": djia_close, "return_pct": round(djia_ret, 2)},
            {"symbol": "QQQ", "prev_close": round(base_qqq, 2), "close": qqq_close, "return_pct": round(qqq_ret, 2)},
            {"symbol": "IWM", "prev_close": round(base_iwm, 2), "close": iwm_close, "return_pct": round(iwm_ret, 2)},
        ],
        "rates_fx_commodities": [
            {"symbol": "UST 2Y", "value": ust_2y_level, "unit": "pct", "change_bps": ust_2y_change_bps},
            {"symbol": "UST 10Y", "value": ust_10y_level, "unit": "pct", "change_bps": ust_10y_change_bps},
            {"symbol": "DXY", "value": dxy_level, "unit": "index", "change_pct": dxy_change_pct},
            {"symbol": "EURUSD", "value": eurusd_level, "unit": "ratio", "change_abs": eurusd_change_abs, "change_pct": eurusd_change_pct},
            {"symbol": "WTI Crude", "value": wti_level, "unit": "usd", "change_pct": wti_change_pct},
            {"symbol": "Gold", "value": gold_level, "unit": "usd", "change_pct": gold_change_pct},
        ],
        "volatility": [
            {"symbol": "VIX", "close": vix_level, "change_pts": vix_change_pts},
            {"symbol": "VIX9D", "close": vix9d_level, "change_pts": vix9d_change_pts},
        ],
        "breadth": {"advancers": adv, "decliners": dec, "pct_above_200dma": pct_above_200},
    }
    return out

def generate_events(date: str, rng: random.Random) -> List[Dict[str, Any]]:
    # Keep your existing variety, but make IDs stable-ish
    event_types = [
        "economic_release",
        "fed_speech",
        "treasury_auction",
        "earnings_8k",
        "corporate_action",
        "regulatory_release",
    ]
    n = rng.randint(3, 6)
    events = []
    for i in range(n):
        et = rng.choice(event_types)
        event_id = f"evt_{et}_{date}_{i + 1}"
        # Simplified: produce fact-only content; use synthetic URLs where real linking is error-prone in SDG
        ts_hour = rng.randint(13, 21)
        ts_min = rng.randint(0, 59)
        published_ts = f"{date}T{ts_hour:02d}:{ts_min:02d}:00Z"
        session = infer_market_session(published_ts, region="US")

        if et == "earnings_8k":
            co = rng.choice(
                ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM"]
            )
            cik = get_cik(co)
            eps_actual = rng.uniform(1.5, 6.0)
            eps_prior = rng.uniform(1.5, 6.0)
            rev_actual = rng.uniform(15, 60)
            rev_prior = rng.uniform(15, 60)
            facts = [
                sanitize_l1_text(f"{co} reported EPS: ${eps_actual:.2f} (prior: ${eps_prior:.2f})"),
                sanitize_l1_text(f"{co} reported Revenue: ${rev_actual:.1f}B (prior: ${rev_prior:.1f}B)"),
            ]
            source = {
                "name": co,
                "source_type": "sec_filing_synthetic",
                "canonical_url": f"synthetic://sec/edgar/data/{cik}/{date}/{co}/8-k",
            }
            entities = [co, "SPX", SECTOR_MAP.get(co, "Unknown")]
            events.append(
                {
                    "event_id": event_id,
                    "event_type": "earnings_8k",
                    "published_ts": published_ts,
                    "market_session": session,
                    "facts": facts,
                    "source": source,
                    "entities": entities,
                }
            )
            continue

        if et == "corporate_action":
            co = rng.choice(
                ["JPM", "XOM", "CVX", "PG", "KO", "UNH", "AAPL", "MSFT", "META"]
            )
            cik = get_cik(co)
            facts = [
                sanitize_l1_text(f"{co} announced a corporate action filing."),
                sanitize_l1_text(f"Record date: {calculate_future_date(date, 18)}"),
            ]
            source = {
                "name": "SEC",
                "source_type": "regulatory_filing_synthetic",
                "canonical_url": f"synthetic://sec/edgar/data/{cik}/{date}/{co}/event",
            }
            entities = [co, "SPX", SECTOR_MAP.get(co, "Unknown")]
            events.append(
                {
                    "event_id": event_id,
                    "event_type": "corporate_action",
                    "published_ts": published_ts,
                    "market_session": session,
                    "facts": facts,
                    "source": source,
                    "entities": entities,
                }
            )
            continue

        # Structured facts for other event types
        if et == "economic_release":
            release_type = rng.choice(["CPI YoY", "ISM Manufacturing PMI", "Nonfarm Payrolls", "PPI YoY"])
            if "CPI" in release_type:
                value = round(rng.uniform(2.5, 3.5), 1)
                prior = round(value + rng.uniform(-0.3, 0.3), 1)
                facts = [sanitize_l1_text(f"BLS released {release_type}: {value}% (prior: {prior}%)")]
            elif "PMI" in release_type:
                value = round(rng.uniform(48.0, 54.0), 1)
                prior = round(value + rng.uniform(-1.5, 1.5), 1)
                facts = [sanitize_l1_text(f"ISM released {release_type}: {value} (prior: {prior})")]
            else:
                value = rng.randint(150, 250)
                prior = value + rng.randint(-30, 30)
                facts = [sanitize_l1_text(f"BLS released {release_type}: {value}K (prior: {prior}K)")]
        elif et == "treasury_auction":
            maturity = rng.choice(["10Y", "30Y", "2Y"])
            stop_out = round(rng.uniform(4.0, 4.5), 2)
            bid_cover = round(rng.uniform(2.3, 2.7), 2)
            facts = [sanitize_l1_text(f"Treasury auction {maturity}: stop-out {stop_out}%, bid-to-cover {bid_cover}")]
        elif et == "fed_speech":
            speaker = rng.choice(["Chair", "Vice Chair", "Regional President"])
            venue = rng.choice(["Economic Club of New York", "Brookings Institution", "Chamber of Commerce", "Federal Reserve Bank of St. Louis", "National Press Club"])
            topic = rng.choice(["monetary policy", "economic outlook", "inflation target"])
            
            # Generate realistic quotes based on topic
            if topic == "inflation target":
                quote = rng.choice([
                    "We remain committed to our 2% inflation target and will take appropriate action to achieve it.",
                    "Inflation is moving toward our 2% goal, but we need to see sustained progress.",
                    "The inflation target remains at 2% and we are confident in reaching it over time."
                ])
            elif topic == "monetary policy":
                quote = rng.choice([
                    "Monetary policy will remain data-dependent as we assess incoming economic information.",
                    "We will continue to adjust monetary policy based on economic conditions and inflation trends.",
                    "The current monetary policy stance is appropriate given economic conditions."
                ])
            else:  # economic outlook
                quote = rng.choice([
                    "The economic outlook remains positive with moderate growth expected in coming quarters.",
                    "We anticipate steady economic growth supported by strong labor market conditions.",
                    "Economic activity continues to expand at a sustainable pace."
                ])
            
            facts = [
                sanitize_l1_text(f"Fed {speaker} delivered speech on {topic}."),
                sanitize_l1_text(f"Venue: {venue}."),
                sanitize_l1_text(f"Quote: \"{quote}\"")
            ]
        else:
            facts = [sanitize_l1_text(f"{et} event recorded for {date}.")]
        source = {
            "name": "SyntheticWire",
            "source_type": "news_wire_synthetic",
            "canonical_url": f"synthetic://wire/{date}/{event_id}",
        }
        entities = ["SPX", "NDX"]
        events.append(
            {
                "event_id": event_id,
                "event_type": et,
                "published_ts": published_ts,
                "market_session": session,
                "facts": facts,
                "source": source,
                "entities": entities,
            }
        )

    events.sort(key=lambda x: x["published_ts"])
    return events

# -----------------------------
# Tickers/sectors/movers (single generation per day)
# -----------------------------
def generate_tickers(
    date: str, prev_date: Optional[str], rng: random.Random, state: Dict[str, float]
) -> List[Dict[str, Any]]:
    n = rng.randint(10, 15)
    chosen = rng.sample(TICKER_UNIVERSE, min(n, len(TICKER_UNIVERSE)))
    out = []
    for t in chosen:
        base = INITIAL_PRICES.get(t, 100.0)

        # sector tilt
        sector = SECTOR_MAP.get(t, "Unknown")
        sector_beta = {
            "Technology": 1.2,
            "Financials": 0.9,
            "Energy": 0.8,
            "Healthcare": 0.7,
            "Consumer Discretionary": 1.0,
            "Consumer Staples": 0.5,
            "Industrials": 0.8,
            "Utilities": 0.4,
            "Real Estate": 0.6,
            "Communication Services": 1.0,
        }.get(sector, 0.8)

        # correlate to day risk + sector beta
        ret = (state["risk"] * sector_beta * 1.8) + rng.uniform(-2.2, 2.2)
        ret = max(-7.0, min(7.0, ret))
        close = round(base * (1 + ret / 100), 2)

        sma_50 = round(close * rng.uniform(0.96, 1.04), 2)
        sma_200 = round(close * rng.uniform(0.90, 1.10), 2)
        rsi_14 = round(rng.uniform(25, 75), 1)

        vol_mult = round(0.9 + abs(ret) / 8 + rng.uniform(0.1, 0.4), 1)
        filings = rng.random() < 0.15

        out.append(
            {
                "symbol": t,
                "close": close,
                "return_pct": round(ret, 2),
                "volume_multiple": vol_mult,
                "technicals": {"sma_50": sma_50, "sma_200": sma_200, "rsi_14": rsi_14},
                "filings_identified": filings,
            }
        )
    return out


def generate_sectors(
    rng: random.Random, state: Dict[str, float]
) -> List[Dict[str, Any]]:
    # Use ETF tickers as sector buckets, but returns should be correlated with risk + factor tilts.
    buckets = ["XLK", "XLF", "XLE", "XLU", "XLRE", "XLY", "XLC"]
    out = []
    for s in buckets:
        if s == "XLK":
            ret = state["risk"] * 2.0 + rng.uniform(-1.0, 1.0)
        elif s == "XLF":
            ret = state["risk"] * 1.2 + state["rates"] * 0.8 + rng.uniform(-1.0, 1.0)
        elif s == "XLE":
            ret = state["energy"] * 1.6 + rng.uniform(-1.2, 1.2)
        else:
            ret = state["risk"] * 1.0 + rng.uniform(-1.0, 1.0)

        ret = max(-3.0, min(3.0, ret))
        vol_mult = round(0.9 + abs(ret) / 10 + rng.uniform(0.1, 0.4), 2)
        out.append(
            {"name": s, "return_pct": round(ret, 2), "volume_multiple": vol_mult}
        )
    return out


def generate_movers(tickers: List[Dict[str, Any]]) -> Dict[str, Any]:
    sorted_t = sorted(tickers, key=lambda x: x["return_pct"], reverse=True)
    
    # Only include positive returns for gainers, negative for decliners
    gainers = [t for t in sorted_t if t["return_pct"] > 0]
    decliners = [t for t in sorted_t if t["return_pct"] < 0]
    
    top_g = [
        {
            "symbol": t["symbol"],
            "return_pct": t["return_pct"],
            "sector": SECTOR_MAP.get(t["symbol"], "Unknown"),
            "volume_multiple": t["volume_multiple"],
        }
        for t in gainers[:5]
    ]
    top_d = [
        {
            "symbol": t["symbol"],
            "return_pct": t["return_pct"],
            "sector": SECTOR_MAP.get(t["symbol"], "Unknown"),
            "volume_multiple": t["volume_multiple"],
        }
        for t in decliners[-5:]  # Take last 5 (most negative)
    ]
    
    # Reverse decliners to show most negative first
    top_d.reverse()
    
    return {"top_gainers": top_g, "top_decliners": top_d}


# -----------------------------
# Reaction windows (coherent w/ day state; VIX inverse-ish)
# -----------------------------
def generate_reaction_windows(
    events: List[Dict[str, Any]],
    rng: random.Random,
    state: Dict[str, float],
    tickers: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rw = []
    ticker_syms = [t["symbol"] for t in tickers]
    indices = ["SPX", "NDX", "DJIA", "RUT", "VIX"]

    for e in events:
        # event shock sign depends on day risk + small idio
        shock = state["risk"] * 0.6 + rng.uniform(-0.6, 0.6)

        for idx in indices:
            if idx == "VIX":
                # VIX reactions in points (vol points), not percent
                move_pts = (-shock) * 0.8 + rng.uniform(-0.4, 0.4)
                move_pts = max(-2.5, min(2.5, move_pts))
                rw.append(
                    {
                        "event_id": e["event_id"],
                        "instrument": idx,
                        "window": "t0_to_t+60m",
                        "move_pts": round(move_pts, 3),
                        "move_type": "pts",
                    }
                )
            else:
                # Equity indices use percent
                move_pct = shock * 0.9 + rng.uniform(-0.4, 0.4)
                move_pct = max(-2.5, min(2.5, move_pct))
                rw.append(
                    {
                        "event_id": e["event_id"],
                        "instrument": idx,
                        "window": "t0_to_t+60m",
                        "move_pct": round(move_pct, 3),
                        "move_type": "pct",
                    }
                )

        affected = rng.sample(ticker_syms, k=min(5, max(3, len(ticker_syms) // 4)))
        for sym in affected:
            beta = 1.3 if SECTOR_MAP.get(sym) == "Technology" else 1.0
            move_pct = shock * beta + rng.uniform(-1.2, 1.2)
            move_pct = max(-5.0, min(5.0, move_pct))
            rw.append(
                {
                    "event_id": e["event_id"],
                    "instrument": sym,
                    "window": rng.choice(
                        ["t0_to_t+30m", "t0_to_t+60m", "pre_to_close"]
                    ),
                    "move_pct": round(move_pct, 3),
                    "move_type": "pct",
                }
            )

    return rw


# -----------------------------
# Evidence items (fact-only excerpts)
# -----------------------------
def generate_evidence_items(
    events: List[Dict[str, Any]], date: str, rng: random.Random
) -> List[Dict[str, Any]]:
    out = []
    for e in events:
        # Fact-only excerpt: pick one fact line verbatim
        fact = rng.choice(e["facts"])
        excerpt = sanitize_l1_text(fact).strip()
        
        # stable per evidence record
        evid_suffix = _short_hash(e["event_id"])
        
        source_name = e["source"]["name"]
        source_slug = source_name.upper().replace(" ", "-")
        date_slug = date.replace("-", "")
        
        out.append(
            {
                "event_id": e["event_id"],
                "source_name": source_name,
                "source_type": e["source"]["source_type"],
                "published_ts": e["published_ts"],
                "canonical_url": e["source"]["canonical_url"],
                "excerpt": excerpt[:280],  # hard cap for chunk stability
                "doc_id": f"{source_slug}-{date_slug}-{evid_suffix}",
                "chunk_id": f"evidence_{e['event_type']}_{date}_{evid_suffix}",
            }
        )
    return out


def generate_day_data(
    date: str, prev_date: Optional[str], global_seed: Optional[int]
) -> Dict[str, Any]:
    seed = stable_int_seed(str(global_seed or ""), date)
    rng = random.Random(seed)
    doc_id = str(uuid.uuid4())
    governance = generate_governance(date, doc_id)

    state = generate_day_state(rng)
    market_outcomes = generate_market_outcomes(date, prev_date, rng, state)

    events = generate_events(date, rng)
    tickers = generate_tickers(date, prev_date, rng, state)  # single source for tickers
    movers = generate_movers(tickers)
    sectors = generate_sectors(rng, state)
    reaction_windows = generate_reaction_windows(events, rng, state, tickers)
    evidence_items = generate_evidence_items(events, date, rng)

    # Persist prev closes for all indices
    idx_map = {i["symbol"]: i["close"] for i in market_outcomes["indices"]}
    PREVIOUS_CLOSES[date] = {
        "indices": idx_map,
        "tickers": {t["symbol"]: t["close"] for t in tickers},
    }

    return {
        "governance": governance,
        "market_outcomes": market_outcomes,
        "events": events,
        "reaction_windows": reaction_windows,
        "movers": movers,
        "sectors": sectors,
        "tickers": tickers,
        "evidence_items": evidence_items,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--skip-validate", action="store_true")
    parser.add_argument("--skip-render", action="store_true")
    args = parser.parse_args()

    dates = sorted(DATES)  # critical for prev close logic
    base_dir = os.path.dirname(__file__)
    sample_data_dir = os.path.join(base_dir, "sample_data")
    sample_output_dir = os.path.join(base_dir, "sample_output")
    os.makedirs(sample_data_dir, exist_ok=True)
    os.makedirs(sample_output_dir, exist_ok=True)

    prev = None
    for d in dates:
        day = generate_day_data(d, prev, args.seed)
        out_file = os.path.join(sample_data_dir, f"day_{d}.json")
        with open(out_file, "w") as f:
            json.dump(day, f, indent=2)
        print(f"✓ Saved {out_file}")
        prev = d

    if not args.skip_validate:
        subprocess.run(
            [sys.executable, os.path.join(base_dir, "validate_l1.py")], cwd=base_dir
        )
    if not args.skip_render:
        subprocess.run(
            [sys.executable, os.path.join(base_dir, "render_l1.py")], cwd=base_dir
        )


if __name__ == "__main__":
    main()
