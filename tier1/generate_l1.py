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


def calculate_future_date(date_str: str, days: int) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return (d + timedelta(days=days)).strftime("%Y-%m-%d")


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
    # Use prev close if consecutive date in sorted list, else use baselines
    base = PREVIOUS_CLOSES.get(prev_date, {}).get("indices", {}) if prev_date else {}
    base_spx = base.get("SPX", 4850.25)
    base_ndx = base.get("NDX", 19245.75)
    base_djia = base.get("DJIA", 38125.45)
    base_rut = base.get("RUT", 2150.80)
    base_qqq = base.get("QQQ", 475.32)
    base_iwm = base.get("IWM", 215.45)

    # Risk drives SPX/NDX; idiosyncratic adds noise
    spx_ret = state["risk"] * 0.90 + rng.uniform(-0.40, 0.40)  # percent
    ndx_ret = state["risk"] * 1.15 + rng.uniform(-0.55, 0.55)
    djia_ret = state["risk"] * 0.70 + rng.uniform(-0.35, 0.35)
    rut_ret = state["risk"] * 1.00 + rng.uniform(-0.60, 0.60)
    qqq_ret = ndx_ret * 0.85 + rng.uniform(-0.25, 0.25)
    iwm_ret = rut_ret * 0.80 + rng.uniform(-0.25, 0.25)

    # Clamp to realistic daily ranges
    def clamp(x, lo, hi):
        return max(lo, min(hi, x))

    spx_ret = clamp(spx_ret, -2.5, 2.5)
    ndx_ret = clamp(ndx_ret, -3.0, 3.0)
    djia_ret = clamp(djia_ret, -2.2, 2.2)
    rut_ret = clamp(rut_ret, -3.2, 3.2)
    qqq_ret = clamp(qqq_ret, -3.0, 3.0)
    iwm_ret = clamp(iwm_ret, -3.0, 3.0)

    # Convert to closes
    spx_close = round(base_spx * (1 + spx_ret / 100), 2)
    ndx_close = round(base_ndx * (1 + ndx_ret / 100), 2)
    djia_close = round(base_djia * (1 + djia_ret / 100), 2)
    rut_close = round(base_rut * (1 + rut_ret / 100), 2)
    qqq_close = round(base_qqq * (1 + qqq_ret / 100), 2)
    iwm_close = round(base_iwm * (1 + iwm_ret / 100), 2)

    # Rates/FX/commodities - Standardize units: yields use bps, currencies use %, commodities use %
    ust_2y = round(4.15 + state["rates"] * 0.05 + rng.uniform(-0.03, 0.03), 2)
    ust_10y = round(4.35 + state["rates"] * 0.08 + rng.uniform(-0.05, 0.05), 2)
    # Yield changes in basis points (bps)
    ust_2y_chg = round(rng.uniform(-3, 3), 1)  # ±3 bps
    ust_10y_chg = round(rng.uniform(-5, 5), 1)  # ±5 bps

    dxy = round(102.45 + state["rates"] * 0.30 + rng.uniform(-0.25, 0.25), 2)
    dxy_chg = round(rng.uniform(-0.30, 0.30), 2)

    eurusd = round(1.0850 - state["rates"] * 0.004 + rng.uniform(-0.003, 0.003), 4)
    eurusd_chg = round(rng.uniform(-0.15, 0.15), 2)

    wti = round(75.80 + state["energy"] * 2.0 + rng.uniform(-1.2, 1.2), 2)
    wti_chg = round((wti / 75.80 - 1) * 100, 2)

    gold = round(2045.30 + (-state["rates"]) * 10 + rng.uniform(-8, 8), 2)
    gold_chg = round((gold / 2045.30 - 1) * 100, 2)

    # Vol inversely related to risk (mostly)
    vix = round(14.25 + (-state["risk"]) * 1.2 + rng.uniform(-0.6, 0.6), 2)
    vix9d = round(15.10 + (-state["risk"]) * 1.0 + rng.uniform(-0.6, 0.6), 2)
    vix_chg = round(rng.uniform(-1.0, 1.0), 2)
    vix9d_chg = round(rng.uniform(-1.0, 1.0), 2)

    adv = rng.randint(1500, 3500)
    dec = rng.randint(1500, 3500)
    pct_above_200 = clamp(50 + spx_ret * 5 + rng.uniform(-5, 5), 30, 80)
    pct_above_200 = round(pct_above_200, 1)

    # L1-neutral headline (no sector leadership, no causality)
    headline = f"US equities: SPX {spx_ret:+.2f}%, NDX {ndx_ret:+.2f}%, DJIA {djia_ret:+.2f}%, RUT {rut_ret:+.2f}%."

    out = {
        "headline_neutral": headline,
        "indices": [
            {
                "symbol": "SPX",
                "close": spx_close,
                "return_pct": round(spx_ret, 2),
                "high": round(spx_close * (1 + rng.uniform(0.002, 0.010)), 2),
                "low": round(spx_close * (1 - rng.uniform(0.002, 0.010)), 2),
            },
            {
                "symbol": "NDX",
                "close": ndx_close,
                "return_pct": round(ndx_ret, 2),
                "high": round(ndx_close * (1 + rng.uniform(0.002, 0.010)), 2),
                "low": round(ndx_close * (1 - rng.uniform(0.002, 0.010)), 2),
            },
            {"symbol": "RUT", "close": rut_close, "return_pct": round(rut_ret, 2)},
            {"symbol": "DJIA", "close": djia_close, "return_pct": round(djia_ret, 2)},
            {"symbol": "QQQ", "close": qqq_close, "return_pct": round(qqq_ret, 2)},
            {"symbol": "IWM", "close": iwm_close, "return_pct": round(iwm_ret, 2)},
        ],
        "rates_fx_commodities": [
            {"symbol": "UST 2Y", "value": ust_2y, "unit": "bps", "change": ust_2y_chg},
            {
                "symbol": "UST 10Y",
                "value": ust_10y,
                "unit": "bps",
                "change": ust_10y_chg,
            },
            {"symbol": "DXY", "value": dxy, "unit": "index", "change": dxy_chg},
            {
                "symbol": "EURUSD",
                "value": eurusd,
                "unit": "index",
                "change": eurusd_chg,
            },
            {"symbol": "WTI Crude", "value": wti, "unit": "usd", "change": wti_chg},
            {"symbol": "Gold", "value": gold, "unit": "usd", "change": gold_chg},
        ],
        "volatility": [
            {"symbol": "VIX", "close": vix, "change": vix_chg},
            {"symbol": "VIX9D", "close": vix9d, "change": vix9d_chg},
        ],
        "breadth": {
            "advancers": adv,
            "decliners": dec,
            "pct_above_200dma": pct_above_200,
        },
    }
    return out


# -----------------------------
# Events (keep yours, but fix URL schemes where needed)
# -----------------------------
# Minimal changes here: fix corporate_action SEC URL to use correct company CIK or synthetic scheme.
# For brevity, we only patch the two problematic URL patterns: corporate_action and earnings_8k.


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
        session = "pre" if ts_hour < 14 else ("post" if ts_hour >= 20 else "regular")

        if et == "earnings_8k":
            co = rng.choice(
                ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM"]
            )
            cik = get_cik(co)
            facts = [
                f"EPS: ${rng.uniform(1.5, 6.0):.2f} vs ${rng.uniform(1.5, 6.0):.2f} expected",
                f"Revenue: ${rng.uniform(15, 60):.1f}B vs ${rng.uniform(15, 60):.1f}B expected",
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
                    "market_session": "post",
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
                f"{co} announced a corporate action filing.",
                f"Record date: {calculate_future_date(date, 18)}",
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

        # Generic fact-only stub for other event types
        facts = [f"{et} event recorded for {date}."]
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
    top_g = [
        {
            "symbol": t["symbol"],
            "return_pct": t["return_pct"],
            "sector": SECTOR_MAP.get(t["symbol"], "Unknown"),
            "volume_multiple": t["volume_multiple"],
        }
        for t in sorted_t[:5]
    ]
    top_d = [
        {
            "symbol": t["symbol"],
            "return_pct": t["return_pct"],
            "sector": SECTOR_MAP.get(t["symbol"], "Unknown"),
            "volume_multiple": t["volume_multiple"],
        }
        for t in sorted_t[-5:]
    ]
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
                move = (-shock) * 0.8 + rng.uniform(-0.4, 0.4)
            else:
                move = shock * 0.9 + rng.uniform(-0.4, 0.4)
            move = max(-2.5, min(2.5, move))
            rw.append(
                {
                    "event_id": e["event_id"],
                    "instrument": idx,
                    "window": "t0_to_t+60m",
                    "move_pct": round(move, 3),
                }
            )

        affected = rng.sample(ticker_syms, k=min(5, max(3, len(ticker_syms) // 4)))
        for sym in affected:
            beta = 1.3 if SECTOR_MAP.get(sym) == "Technology" else 1.0
            move = shock * beta + rng.uniform(-1.2, 1.2)
            move = max(-5.0, min(5.0, move))
            rw.append(
                {
                    "event_id": e["event_id"],
                    "instrument": sym,
                    "window": rng.choice(
                        ["t0_to_t+30m", "t0_to_t+60m", "pre_to_close"]
                    ),
                    "move_pct": round(move, 3),
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
        excerpt = f"{fact}"
        out.append(
            {
                "event_id": e["event_id"],
                "source_name": e["source"]["name"],
                "source_type": e["source"]["source_type"],
                "published_ts": e["published_ts"],
                "canonical_url": e["source"]["canonical_url"],
                "excerpt": excerpt,
                "doc_id": f"{e['source']['name'].upper().replace(' ', '-')}-{date.replace('-', '')}",
                "chunk_id": f"evidence_{e['event_type']}_{date}",
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
