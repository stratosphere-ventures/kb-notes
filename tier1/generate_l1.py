#!/usr/bin/env python3
"""
Layer 1 Synthetic Data Generation (SDG) Script
Generates 5 realistic Layer 1 market fact graph JSON files
"""

import json
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys
import os
import argparse
import subprocess


# Configuration
DATES = ["2026-01-15", "2026-02-28", "2026-04-30", "2026-03-13", "2026-03-16"]
PREVIOUS_CLOSES = {}

# Master ticker universe (~50 stocks)
TICKER_UNIVERSE = [
    # Mega-cap
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "NVDA",
    "TSLA",
    "BRK.B",
    # Financials
    "JPM",
    "BAC",
    "WFC",
    "GS",
    "MS",
    "BLK",
    "SCHW",
    # Healthcare
    "UNH",
    "JNJ",
    "PFE",
    "ABT",
    "TMO",
    "LLY",
    "MRK",
    # Energy
    "XOM",
    "CVX",
    "COP",
    "SLB",
    "PXD",
    # Industrials
    "CAT",
    "DE",
    "HON",
    "GE",
    "UPS",
    # Consumer
    "PG",
    "KO",
    "MCD",
    "HD",
    "NKE",
    "PEP",
    # Sector ETFs
    "XLK",
    "XLF",
    "XLE",
    "XLU",
    "XLRE",
    "XLY",
    "XLC",
]

# Event types with fact generators
EVENT_TEMPLATES = {
    "fed_speech": {
        "speakers": [
            "Chair Jerome Powell",
            "Governor Michelle Bowman",
            "Governor Christopher Waller",
            "Governor Adriana Kugler",
            "Vice Chair Philip Jefferson",
        ],
        "topics": [
            "Monetary policy outlook",
            "Economic conditions",
            "Inflation trends",
            "Labor market dynamics",
            "Financial stability",
        ],
        "fact_templates": [
            [
                "Fed policy remains data-dependent",
                "Inflation has made progress toward 2% target",
                "No specific timing for rate adjustments provided",
            ],
            [
                "Committee continues to assess incoming data",
                "Policy stance remains restrictive",
                "Labor market shows signs of cooling",
            ],
            [
                "Inflation expectations remain anchored",
                "Economic activity has moderated",
                "Rate cuts depend on further progress on inflation",
            ],
            [
                "Financial system resilient",
                "Credit conditions tightening",
                "Banking sector stability improved",
            ],
        ],
    },
    "economic_release": {
        "indicators": {
            "CPI": {
                "units": ["% MoM", "% YoY", "Core % MoM", "Core % YoY"],
                "expected_range": (0.1, 0.5),
            },
            "PPI": {
                "units": ["% MoM", "% YoY", "Core % MoM", "Core % YoY"],
                "expected_range": (0.0, 0.4),
            },
            "PCE": {
                "units": ["% MoM", "% YoY", "Core % MoM", "% YoY"],
                "expected_range": (0.1, 0.4),
            },
            "ISM PMI": {
                "units": ["Index Level", "New Orders", "Employment", "Prices"],
                "expected_range": (48.0, 54.0),
            },
            "Jobless Claims": {
                "units": [
                    "Initial Claims (K)",
                    "Continuing Claims (K)",
                    "4-week Average",
                ],
                "expected_range": (200, 220),
            },
            "Retail Sales": {
                "units": ["% MoM", "Ex Auto % MoM", "Control Group % MoM"],
                "expected_range": (-0.3, 0.8),
            },
        }
    },
    "treasury_auction": {
        "tenors": ["2-year", "5-year", "10-year", "30-year"],
        "yield_ranges": {
            "2-year": (4.0, 4.5),
            "5-year": (4.0, 4.6),
            "10-year": (4.0, 4.7),
            "30-year": (4.1, 4.8),
        },
        "btc_range": (2.2, 2.6),
        "indirect_range": (62, 75),
    },
    "earnings_8k": {
        "companies": {
            "AAPL": "iPhone sales",
            "MSFT": "Cloud revenue",
            "GOOGL": "Ad revenue",
            "AMZN": "AWS growth",
            "META": "User engagement",
            "NVDA": "Data center revenue",
            "TSLA": "Deliveries",
            "JPM": "Net interest income",
            "BAC": "Loan growth",
            "UNH": "Medical costs",
            "JNJ": "Pharmaceutical sales",
            "XOM": "Production volumes",
            "CVX": "Refining margins",
            "CAT": "Equipment orders",
            "PG": "Volume growth",
        }
    },
    "corporate_action": {
        "types": [
            "M&A Announcement",
            "Buyback Authorization",
            "Dividend Declaration",
            "Spin-off Announcement",
            "Strategic Partnership",
        ],
        "deal_value_range": (1.0, 25.0),
    },
    "regulatory_release": {
        "agencies": ["SEC", "Federal Reserve", "Treasury Department", "CFTC", "OCC"],
        "actions": [
            "Enforcement Action",
            "Rule Proposal",
            "Guidance Update",
            "Policy Clarification",
            "Risk Advisory",
        ],
    },
}

# Sector mappings for tickers
SECTOR_MAP = {
    "AAPL": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Technology",
    "AMZN": "Consumer Discretionary",
    "META": "Communication Services",
    "NVDA": "Technology",
    "TSLA": "Consumer Discretionary",
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
    "MCD": "Consumer Discretionary",
    "HD": "Consumer Discretionary",
    "NKE": "Consumer Discretionary",
    "PEP": "Consumer Staples",
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLY": "Consumer Discretionary",
    "XLC": "Communication Services",
}

# Initial price levels for tickers
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
    """Get mock CIK for ticker"""
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


def calculate_future_date(date_str: str, days: int) -> str:
    """Calculate future date"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    future_date = date_obj + timedelta(days=days)
    return future_date.strftime("%Y-%m-%d")


def generate_governance(date: str, doc_id: str) -> Dict[str, Any]:
    """Generate governance metadata"""
    published_time = f"{date}T20:00:00Z"
    asof_time = f"{date}T16:00:00Z"

    return {
        "date": date,
        "region": "US",
        "market_session": "post",
        "published_ts": published_time,
        "asof_ts": asof_time,
        "universe_scope": "SPX",
        "doc_version": 1,
        "trust_tier": 1,
        "license_policy": "internal",
        "market_data_vendor": "Massive",
        "market_data_version": "massive_bars_v3",
        "calc_versions": ["technicals_v1.2.1", "impact_v1.0.0"],
        "pipeline_version": "v2.1.0",
        "doc_id": doc_id,
        "doc_key": f"market_wrap/us/{date}",
        "is_current": True,
        "is_active": True,
        "sources_used": [
            {
                "source_name": "Bloomberg",
                "source_type": "market_data",
                "count": 1500,
                "max_age_days": 0,
            },
            {
                "source_name": "Refinitiv",
                "source_type": "market_data",
                "count": 920,
                "max_age_days": 0,
            },
        ],
    }


def generate_fed_speech_event(
    date: str, event_id: str, sequence: int
) -> Dict[str, Any]:
    """Generate Fed speech event"""
    template = EVENT_TEMPLATES["fed_speech"]
    speaker = random.choice(template["speakers"])
    topic = random.choice(template["topics"])
    facts = random.choice(template["fact_templates"])

    hour = 13 + random.randint(0, 1)
    minute = random.randint(0, 59)
    published_ts = f"{date}T{hour:02d}:{minute:02d}:00Z"

    entities = ["UST yields", "USD indices", "Financial sector", "SPX", "NDX"]
    random.shuffle(entities)
    entities = entities[:4]

    return {
        "event_id": event_id,
        "event_type": "fed_speech",
        "published_ts": published_ts,
        "market_session": "pre",
        "facts": facts,
        "source": {
            "name": "Federal Reserve",
            "source_type": "central_bank_release",
            "canonical_url": f"https://www.federalreserve.gov/newsevents/speech/{speaker.lower().replace(' ', '-').replace('.', '')}{date.replace('-', '')}.htm",
        },
        "entities": entities,
    }


def generate_economic_release_event(
    date: str, event_id: str, sequence: int
) -> Dict[str, Any]:
    """Generate economic release event"""
    template = EVENT_TEMPLATES["economic_release"]
    indicator = random.choice(list(template["indicators"].keys()))
    indicator_data = template["indicators"][indicator]

    expected_range = indicator_data["expected_range"]

    if "Claims" in indicator:
        actual = int(expected_range[0] + random.uniform(-10, 15))
        expected = int(expected_range[0] + random.uniform(-5, 5))
        actual_str = f"{actual}K vs {expected}K expected"
        actual_float = float(actual)
    else:
        actual_float = expected_range[0] + random.uniform(-0.05, 0.15)
        expected_float = expected_range[0] + random.uniform(-0.03, 0.03)
        if indicator in ["CPI", "PPI", "PCE"]:
            actual_str = f"{actual_float:+.1f}% vs {expected_float:+.1f}% expected"
        else:
            actual_str = f"{actual_float:.1f} vs {expected_float:.1f} expected"
        actual_float = actual_float

    facts = [f"{indicator}: {actual_str}"]

    if "CPI" in indicator:
        facts.extend(
            [
                f"YoY Headline: {random.uniform(2.5, 4.0):.1f}% vs {random.uniform(3.0, 3.5):.1f}% expected",
                f"Core {indicator}: {random.uniform(0.2, 0.5):+.1f}% MoM vs {random.uniform(0.2, 0.4):+.1f}% expected",
            ]
        )
    elif "PMI" in indicator:
        facts.extend(
            [
                f"New Orders: {random.uniform(48, 55):.1f}",
                f"Employment: {random.uniform(47, 54):.1f}",
                f"Prices Paid: {random.uniform(48, 56):.1f}",
            ]
        )
    elif "Claims" in indicator:
        facts.append(
            f"4-week average: {random.uniform(205, 215):.1f}K vs {random.uniform(205, 210):.1f}K prior week"
        )

    if "Claims" in indicator:
        published_ts = f"{date}T15:00:00Z"
    else:
        published_ts = f"{date}T13:30:00Z"

    entities = ["SPX", "NDX", "UST yields", "USD indices"]
    random.shuffle(entities)
    entities = entities[:3]

    return {
        "event_id": event_id,
        "event_type": "economic_release",
        "published_ts": published_ts,
        "market_session": "pre" if "13:30" in published_ts else "regular",
        "facts": facts,
        "source": {
            "name": "Bureau of Labor Statistics"
            if "CPI" in indicator or "Claims" in indicator
            else "Institute for Supply Management",
            "source_type": "government_release",
            "canonical_url": f"https://www.bls.gov/news.release/archives/{indicator.lower().replace(' ', '_')}_{date.replace('-', '')}.htm",
        },
        "entities": entities,
    }


def generate_treasury_auction_event(
    date: str, event_id: str, sequence: int
) -> Dict[str, Any]:
    """Generate treasury auction event"""
    template = EVENT_TEMPLATES["treasury_auction"]
    tenor = random.choice(template["tenors"])

    yield_value = round(random.uniform(*template["yield_ranges"][tenor]), 3)
    btc = round(random.uniform(*template["btc_range"]), 2)
    indirect = round(random.uniform(*template["indirect_range"]), 1)

    facts = [
        f"{tenor.capitalize()} Treasury auction: {yield_value:.3f}% high yield",
        f"Bid-to-cover ratio: {btc:.2f} vs {random.uniform(2.2, 2.5):.2f} prior",
        f"Indirect bidders: {indirect}% vs {random.uniform(62, 68):.1f}% prior",
    ]

    minute = random.randint(0, 59)
    published_ts = f"{date}T19:{minute:02d}:00Z"

    entities = ["UST yields", "USD indices", "Bond ETFs", "XLF"]

    return {
        "event_id": event_id,
        "event_type": "treasury_auction",
        "published_ts": published_ts,
        "market_session": "regular",
        "facts": facts,
        "source": {
            "name": "U.S. Department of Treasury",
            "source_type": "government_release",
            "canonical_url": f"https://www.treasury.gov/resource-center/data-chart-center/quarterly-refunding/Pages/auction-results-{date.replace('-', '')}.aspx",
        },
        "entities": entities,
    }


def generate_earnings_event(date: str, event_id: str, sequence: int) -> Dict[str, Any]:
    """Generate earnings 8-K event"""
    template = EVENT_TEMPLATES["earnings_8k"]
    companies_list = list(template["companies"].keys())
    company = random.choice(companies_list)
    focus_area = template["companies"][company]

    eps_actual = round(random.uniform(1.5, 5.5), 2)
    eps_expected = round(eps_actual + random.uniform(-0.3, 0.2), 2)

    revenue_actual = round(random.uniform(15, 50), 1)
    revenue_expected = round(revenue_actual + random.uniform(-2, 1.5), 1)

    guidance_next = round(revenue_actual * (1 + random.uniform(0.02, 0.08)), 1)
    guidance_expected = round(guidance_next + random.uniform(-1, 0.8), 1)

    facts = [
        f"EPS: ${eps_actual:.2f} vs ${eps_expected:.2f} expected",
        f"Revenue: ${revenue_actual}B vs ${revenue_expected}B expected",
        f"{focus_area}: {random.choice(['increased', 'decreased', 'remained flat'])} {random.randint(5, 20)}% YoY",
        f"Q{random.randint(1, 4)} Guidance: ${guidance_next}B vs ${guidance_expected}B expected",
        f"Gross margin: {random.randint(45, 75)}% vs {random.randint(42, 72)}% prior quarter",
    ]

    hour = 21 + random.randint(0, 1)
    minute = random.randint(0, 59)
    published_ts = f"{date}T{hour:02d}:{minute:02d}:00Z"

    entities = [company, "SPX", SECTOR_MAP.get(company, "Unknown"), f"{company} sector"]

    return {
        "event_id": event_id,
        "event_type": "earnings_8k",
        "published_ts": published_ts,
        "market_session": "post",
        "facts": facts,
        "source": {
            "name": f"{company}",
            "source_type": "sec_filing",
            "canonical_url": f"https://www.sec.gov/Archives/edgar/data/{get_cik(company)}/0000950170{date.replace('-', '')}{company.lower()}-8k.htm",
        },
        "entities": entities,
    }


def generate_corporate_action_event(
    date: str, event_id: str, sequence: int
) -> Dict[str, Any]:
    """Generate corporate action event"""
    template = EVENT_TEMPLATES["corporate_action"]
    action_type = random.choice(template["types"])

    if action_type == "M&A Announcement":
        deal_value = round(random.uniform(*template["deal_value_range"]), 1)
        acquirer = random.choice(["AAPL", "MSFT", "GOOGL", "JPM", "BAC", "XOM"])
        target = random.choice(["NVDA", "META", "TSLA", "GS", "CVX", "CAT"])
        facts = [
            f"{acquirer} to acquire {target} for ${deal_value}B",
            f"Transaction expected to close in Q{random.randint(2, 4)} {date[:4]}",
            f"Deal structure: {random.choice(['All-cash', 'Stock-for-stock', 'Cash and stock'])}",
            f"Financing: {random.choice(['Cash on hand', 'Debt financing', 'Combination'])}",
        ]
        entities = [acquirer, target, f"{acquirer} sector", f"{target} sector"]
    elif action_type == "Buyback Authorization":
        company = random.choice(["AAPL", "MSFT", "GOOGL", "JPM", "META"])
        amount = round(random.uniform(10, 100), 0)
        facts = [
            f"{company} board authorizes ${amount}B share repurchase program",
            f"Program represents approximately {random.uniform(2, 5):.1f}% of market cap",
            f"Effective period: {random.randint(2, 4)} years",
            f"Replaces previous {random.randint(10, 50)}B authorization",
        ]
        entities = [company, "SPX", SECTOR_MAP.get(company, "Unknown")]
    elif action_type == "Dividend Declaration":
        company = random.choice(["JPM", "XOM", "CVX", "PG", "KO", "UNH"])
        dividend = round(random.uniform(0.30, 2.50), 2)
        facts = [
            f"{company} declares quarterly dividend of ${dividend:.2f} per share",
            f"Ex-dividend date: {calculate_future_date(date, 14)}",
            f"Record date: {calculate_future_date(date, 18)}",
            f"Payable date: {calculate_future_date(date, 28)}",
            f"Yield: {random.uniform(1.5, 4.5):.2f}% at current price",
        ]
        entities = [
            company,
            "SPX",
            SECTOR_MAP.get(company, "Unknown"),
            "Dividend Aristocrats",
        ]
    elif action_type == "Spin-off Announcement":
        parent = random.choice(["GE", "JNJ", "PFE", "IBM"])
        unit = f"{parent} {random.choice(['Healthcare', 'Energy', 'Financial Services', 'Technology'])} unit"
        facts = [
            f"{parent} announces plan to spin off {unit}",
            f"Spin-off expected to complete in Q{random.randint(2, 4)} {date[:4]}",
            f"{parent} shareholders to receive shares in new entity",
            f"Transaction structured as tax-free distribution",
        ]
        entities = [parent, unit, "SPX", SECTOR_MAP.get(parent, "Unknown")]
    else:  # Strategic Partnership
        company1 = random.choice(["NVDA", "MSFT", "GOOGL", "AMZN"])
        company2 = random.choice(["JNJ", "PFE", "UNH", "BAC"])
        facts = [
            f"{company1} and {company2} form strategic partnership",
            f"Focus: {random.choice(['AI drug discovery', 'Cloud healthcare', 'Digital payments', 'Autonomous vehicles'])}",
            f"Initial investment: ${random.uniform(1, 10):.1f}B",
            f"Joint development agreement for {random.randint(3, 7)} years",
        ]
        entities = [company1, company2, "SPX", SECTOR_MAP.get(company1, "Unknown")]

    hour = 13 + random.randint(0, 5)
    minute = random.randint(0, 59)
    published_ts = f"{date}T{hour:02d}:{minute:02d}:00Z"

    market_session = "pre" if hour < 14 else "regular"

    return {
        "event_id": event_id,
        "event_type": "corporate_action",
        "published_ts": published_ts,
        "market_session": market_session,
        "facts": facts,
        "source": {
            "name": "SEC",
            "source_type": "regulatory_filing",
            "canonical_url": f"https://www.sec.gov/Archives/edgar/data/{get_cik('AAPL')}/000000000{date.replace('-', '')}corp-8k.htm",
        },
        "entities": entities,
    }


def generate_regulatory_release_event(
    date: str, event_id: str, sequence: int
) -> Dict[str, Any]:
    """Generate regulatory release event"""
    template = EVENT_TEMPLATES["regulatory_release"]
    agency = random.choice(template["agencies"])
    action = random.choice(template["actions"])

    if action == "Enforcement Action":
        company = random.choice(["BAC", "WFC", "GS", "MS", "META", "GOOGL"])
        penalty = round(random.uniform(50, 500), 0)
        facts = [
            f"{agency} announces enforcement action against {company}",
            f"Alleged violations: {random.choice(['anti-money laundering controls', 'data privacy', 'market manipulation', 'consumer protection'])}",
            f"Settlement amount: ${penalty}M",
            f"{company} neither admits nor denies wrongdoing",
        ]
        entities = [
            company,
            "SPX",
            SECTOR_MAP.get(company, "Unknown"),
            "Regulatory risk",
        ]
    elif action == "Rule Proposal":
        facts = [
            f"{agency} proposes new rule on {random.choice(['bank capital requirements', 'market structure', 'digital assets', 'climate disclosure'])}",
            f"Public comment period: {random.randint(30, 90)} days",
            f"Expected implementation: Q{random.randint(3, 4)} {date[:4]}",
            f"Affects approximately {random.randint(50, 500)} financial institutions",
        ]
        entities = ["SPX", "XLF", "Financial sector", "Regulatory compliance"]
    elif action == "Guidance Update":
        facts = [
            f"{agency} issues guidance on {random.choice(['interest rate risk management', 'cybersecurity', 'liquidity stress testing'])}",
            f"Applicable to: {random.choice(['large banks', 'asset managers', 'systemically important financial institutions'])}",
            f"Effective date: {calculate_future_date(date, random.randint(30, 90))}",
            f"Supervisory expectations clarified",
        ]
        entities = ["SPX", "XLF", "GS", "JPM"]
    elif action == "Policy Clarification":
        facts = [
            f"{agency} clarifies policy on {random.choice(['stablecoin reserves', 'bank mergers', 'custody of assets'])}",
            f"Applies to entities with assets over ${random.randint(10, 100)}B",
            f"Clarification addresses market uncertainty",
            f"No changes to existing regulations",
        ]
        entities = ["SPX", "XLC", "Crypto sector", "Financial sector"]
    else:  # Risk Advisory
        facts = [
            f"{agency} issues risk advisory on {random.choice(['AI in financial services', 'third-party service providers', 'foreign exchange volatility'])}",
            f"Key risks identified: {random.choice(['data quality', 'operational resilience', 'model governance'])}",
            f"Recommendations: Enhanced monitoring and controls",
            f"Advisory not binding but serves as best practices guidance",
        ]
        entities = ["SPX", "XLF", "Technology sector", "Risk management"]

    hour = 14 + random.randint(0, 5)
    minute = random.randint(0, 59)
    published_ts = f"{date}T{hour:02d}:{minute:02d}:00Z"

    return {
        "event_id": event_id,
        "event_type": "regulatory_release",
        "published_ts": published_ts,
        "market_session": "regular",
        "facts": facts,
        "source": {
            "name": agency,
            "source_type": "regulatory_release",
            "canonical_url": f"https://www.{agency.lower().replace(' ', '')}.gov/press-release/{date.replace('-', '')}.htm",
        },
        "entities": entities,
    }


def generate_events(
    date: str, num_events: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Generate events for day"""
    if num_events is None:
        num_events = random.randint(3, 6)

    events = []
    event_types = [
        "fed_speech",
        "economic_release",
        "treasury_auction",
        "earnings_8k",
        "corporate_action",
        "regulatory_release",
    ]

    for i in range(num_events):
        event_type = random.choice(event_types)
        event_id = f"evt_{event_type}_{date}_{i + 1}"

        if event_type == "fed_speech":
            event = generate_fed_speech_event(date, event_id, i)
        elif event_type == "economic_release":
            event = generate_economic_release_event(date, event_id, i)
        elif event_type == "treasury_auction":
            event = generate_treasury_auction_event(date, event_id, i)
        elif event_type == "earnings_8k":
            event = generate_earnings_event(date, event_id, i)
        elif event_type == "corporate_action":
            event = generate_corporate_action_event(date, event_id, i)
        elif event_type == "regulatory_release":
            event = generate_regulatory_release_event(date, event_id, i)
        else:
            # Fallback event
            event = generate_fed_speech_event(date, event_id, i)

        events.append(event)

    events.sort(key=lambda x: x["published_ts"])
    return events


def generate_market_outcomes(
    date: str, prev_date: Optional[str] = None
) -> Dict[str, Any]:
    """Generate market outcomes for day"""
    is_consecutive = prev_date is not None and prev_date in PREVIOUS_CLOSES

    base_spx = (
        4850.25 if not is_consecutive else PREVIOUS_CLOSES[prev_date]["indices"]["SPX"]
    )
    base_ndx = (
        19245.75 if not is_consecutive else PREVIOUS_CLOSES[prev_date]["indices"]["NDX"]
    )

    if is_consecutive:
        spx_drift = random.uniform(-0.015, 0.015)
        ndx_drift = random.uniform(-0.015, 0.015)
    else:
        spx_drift = random.uniform(-0.02, 0.02)
        ndx_drift = random.uniform(-0.025, 0.025)

    spx_close = round(base_spx * (1 + spx_drift), 2)
    ndx_close = round(base_ndx * (1 + ndx_drift), 2)

    spx_return = round((spx_close / base_spx - 1) * 100, 2)
    ndx_return = round((ndx_close / base_ndx - 1) * 100, 2)

    djia_close = round(38125.45 * (1 + random.uniform(-0.015, 0.015)), 2)
    rut_close = round(2150.80 * (1 + random.uniform(-0.02, 0.02)), 2)
    qqq_close = round(475.32 * (1 + random.uniform(-0.02, 0.02)), 2)
    iwm_close = round(215.45 * (1 + random.uniform(-0.02, 0.02)), 2)

    ust_2y_value = round(4.15 + random.uniform(-0.05, 0.05), 2)
    ust_2y_change = round(random.uniform(-3, 3), 1)

    ust_10y_value = round(4.35 + random.uniform(-0.08, 0.08), 2)
    ust_10y_change = round(random.uniform(-5, 5), 1)

    dxy_value = round(102.45 + random.uniform(-0.5, 0.5), 2)
    dxy_change = round(random.uniform(-0.3, 0.3), 2)

    eurusd_value = round(1.0850 + random.uniform(-0.01, 0.01), 4)
    eurusd_change = round(random.uniform(-0.15, 0.15), 2)

    wti_value = round(75.80 + random.uniform(-3, 3), 2)
    wti_change = round((wti_value / 75.80 - 1) * 100, 1)

    gold_value = round(2045.30 + random.uniform(-15, 15), 2)
    gold_change = round((gold_value / 2045.30 - 1) * 100, 1)

    vix_close = round(14.25 + random.uniform(-2, 2), 2)
    vix_change = round(random.uniform(-1, 1), 2)

    vix9d_close = round(15.10 + random.uniform(-2, 2), 2)
    vix9d_change = round(random.uniform(-1, 1), 2)

    advancers = random.randint(1500, 3500)
    decliners = random.randint(1500, 3500)
    pct_above_200dma = round(50 + spx_return * 5 + random.uniform(-5, 5), 1)
    pct_above_200dma = max(30, min(80, pct_above_200dma))

    if spx_return > 0.5:
        headline = f"US equities higher; SPX gains {spx_return}%, technology leads"
    elif spx_return < -0.5:
        headline = f"US equities lower; SPX falls {abs(spx_return)}%, energy stocks lead losses"
    else:
        headline = f"US equities mixed; SPX {spx_return:+.2f}%, sectors diverge"

    return {
        "headline_neutral": headline,
        "indices": [
            {
                "symbol": "SPX",
                "close": spx_close,
                "return_pct": spx_return,
                "high": round(spx_close * 1.008, 2),
                "low": round(spx_close * 0.992, 2),
            },
            {
                "symbol": "NDX",
                "close": ndx_close,
                "return_pct": ndx_return,
                "high": round(ndx_close * 1.008, 2),
                "low": round(ndx_close * 0.992, 2),
            },
            {
                "symbol": "RUT",
                "close": rut_close,
                "return_pct": round((rut_close / 2150.80 - 1) * 100, 2),
            },
            {
                "symbol": "DJIA",
                "close": djia_close,
                "return_pct": round((djia_close / 38125.45 - 1) * 100, 2),
            },
            {
                "symbol": "QQQ",
                "close": qqq_close,
                "return_pct": round((qqq_close / 475.32 - 1) * 100, 2),
            },
            {
                "symbol": "IWM",
                "close": iwm_close,
                "return_pct": round((iwm_close / 215.45 - 1) * 100, 2),
            },
        ],
        "rates_fx_commodities": [
            {
                "symbol": "UST 2Y",
                "value": ust_2y_value,
                "unit": "pct",
                "change": ust_2y_change,
            },
            {
                "symbol": "UST 10Y",
                "value": ust_10y_value,
                "unit": "pct",
                "change": ust_10y_change,
            },
            {
                "symbol": "DXY",
                "value": dxy_value,
                "unit": "index",
                "change": dxy_change,
            },
            {
                "symbol": "EURUSD",
                "value": eurusd_value,
                "unit": "index",
                "change": eurusd_change,
            },
            {
                "symbol": "WTI Crude",
                "value": wti_value,
                "unit": "usd",
                "change": wti_change,
            },
            {
                "symbol": "Gold",
                "value": gold_value,
                "unit": "usd",
                "change": gold_change,
            },
        ],
        "volatility": [
            {"symbol": "VIX", "close": vix_close, "change": vix_change},
            {"symbol": "VIX9D", "close": vix9d_close, "change": vix9d_change},
        ],
        "breadth": {
            "advancers": advancers,
            "decliners": decliners,
            "pct_above_200dma": pct_above_200dma,
        },
    }


def generate_reaction_windows(
    events: List[Dict[str, Any]], day_tickers: List[str]
) -> List[Dict[str, Any]]:
    """Generate reaction windows for events"""
    reaction_windows = []
    indices = ["SPX", "NDX", "DJIA", "RUT", "VIX"]

    for event in events:
        event_type = event["event_type"]

        num_tickers = random.randint(3, min(5, len(day_tickers)))
        affected_tickers = random.sample(day_tickers, num_tickers)

        for idx in indices:
            move_pct = round(random.uniform(-2.5, 2.5), 3)
            reaction_windows.append(
                {
                    "event_id": event["event_id"],
                    "instrument": idx,
                    "window": "t0_to_t+60m",
                    "move_pct": move_pct,
                }
            )

        for ticker in affected_tickers:
            move_pct = round(random.uniform(-5.0, 5.0), 3)
            window_type = random.choice(["t0_to_t+30m", "t0_to_t+60m", "pre_to_close"])
            reaction_windows.append(
                {
                    "event_id": event["event_id"],
                    "instrument": ticker,
                    "window": window_type,
                    "move_pct": move_pct,
                }
            )

        if event == events[0]:
            for idx in ["SPX", "NDX", "VIX"]:
                move_pct = round(random.uniform(-1.5, 1.5), 3)
                reaction_windows.append(
                    {
                        "event_id": event["event_id"],
                        "instrument": idx,
                        "window": "close_to_close",
                        "move_pct": move_pct,
                    }
                )

    return reaction_windows


def generate_movers(
    day_tickers: List[str], market_outcomes: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate top movers from day's tickers"""
    ticker_returns = {}
    for ticker in day_tickers:
        if ticker in INITIAL_PRICES:
            base_price = INITIAL_PRICES[ticker]
            return_pct = round(random.uniform(-6.0, 6.0), 2)
            ticker_returns[ticker] = {
                "return_pct": return_pct,
                "volume_multiple": round(
                    0.8 + abs(return_pct) / 10 + random.uniform(0.2, 0.5), 1
                ),
            }

    sorted_tickers = sorted(
        ticker_returns.items(), key=lambda x: x[1]["return_pct"], reverse=True
    )

    top_gainers = []
    for ticker, data in sorted_tickers[:5]:
        top_gainers.append(
            {
                "symbol": ticker,
                "return_pct": data["return_pct"],
                "sector": SECTOR_MAP.get(ticker, "Unknown"),
                "volume_multiple": data["volume_multiple"],
            }
        )

    top_decliners = []
    for ticker, data in sorted_tickers[-5:]:
        top_decliners.append(
            {
                "symbol": ticker,
                "return_pct": data["return_pct"],
                "sector": SECTOR_MAP.get(ticker, "Unknown"),
                "volume_multiple": data["volume_multiple"],
            }
        )

    return {"top_gainers": top_gainers, "top_decliners": top_decliners}


def generate_sectors(
    date: str, prev_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Generate sector performance data"""
    sector_data = []

    sector_bases = {
        "XLK": 195.50,
        "XLF": 38.75,
        "XLE": 92.40,
        "XLU": 68.85,
        "XLRE": 42.30,
        "XLY": 178.60,
        "XLC": 72.40,
    }

    for sector, base_value in sector_bases.items():
        return_pct = round(random.uniform(-2.0, 2.0), 2)
        volume_multiple = round(
            0.9 + abs(return_pct) / 15 + random.uniform(0.1, 0.4), 2
        )

        sector_data.append(
            {
                "name": sector,
                "return_pct": return_pct,
                "volume_multiple": volume_multiple,
            }
        )

    return sector_data


def generate_tickers(
    date: str, prev_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Generate ticker data for day"""
    num_tickers = random.randint(10, 15)
    selected_tickers = random.sample(
        TICKER_UNIVERSE, min(num_tickers, len(TICKER_UNIVERSE))
    )

    is_consecutive = prev_date is not None and prev_date in PREVIOUS_CLOSES

    tickers_data = []

    for ticker in selected_tickers:
        base_price = INITIAL_PRICES.get(ticker, 100.0)

        if is_consecutive and ticker in PREVIOUS_CLOSES[prev_date]["tickers"]:
            prev_close = PREVIOUS_CLOSES[prev_date]["tickers"][ticker]
            drift = random.uniform(-0.015, 0.015)
            close = round(prev_close * (1 + drift), 2)
            return_pct = round((close / prev_close - 1) * 100, 2)
        else:
            return_pct = round(random.uniform(-5.0, 5.0), 2)
            close = round(base_price * (1 + return_pct / 100), 2)

        sma_50 = round(close * random.uniform(0.95, 1.05), 2)
        sma_200 = round(close * random.uniform(0.88, 1.12), 2)
        rsi_14 = round(random.uniform(25, 75), 1)

        volume_multiple = round(
            0.8 + abs(return_pct) / 10 + random.uniform(0.2, 0.5), 1
        )

        filings_identified = random.random() < 0.2

        tickers_data.append(
            {
                "symbol": ticker,
                "close": close,
                "return_pct": return_pct,
                "volume_multiple": volume_multiple,
                "technicals": {"sma_50": sma_50, "sma_200": sma_200, "rsi_14": rsi_14},
                "filings_identified": filings_identified,
            }
        )

    return tickers_data


def generate_evidence_items(
    events: List[Dict[str, Any]], date: str
) -> List[Dict[str, Any]]:
    """Generate evidence items for events"""
    evidence_items = []

    for event in events:
        event_type = event["event_type"]
        event_id = event["event_id"]
        published_ts = event["published_ts"]
        source = event["source"]

        excerpts = {
            "fed_speech": [
                f"Federal Reserve officials emphasized data-dependent policy approach. Committee members noted progress toward inflation target.",
                f"Central bank officials discussed monetary policy outlook. The statement highlighted that inflation remains above 2% goal.",
                f"Fed speakers addressed market concerns about rate policy trajectory. Officials emphasized patient approach to policy adjustments.",
            ],
            "economic_release": [
                f"Economic data released shows key metrics. This represents a deviation from analyst expectations.",
                f"The latest economic indicators provide insights into current economic conditions. Markets are analyzing implications.",
                f"Government statistics show updated figures. Analysts are assessing impact on policy expectations.",
            ],
            "treasury_auction": [
                f"Treasury auction results show yield levels. Demand metrics indicate investor appetite for government debt.",
                f"The auction demonstrates demand patterns. Market participants monitor these for funding conditions.",
            ],
            "earnings_8k": [
                f"Company reported earnings per share figures. Revenue and earnings figures exceeded analyst projections.",
                f"Financial results show revenue levels. Management provided forward guidance for upcoming quarters.",
                f"Quarterly earnings release includes detailed financial metrics. The company disclosed performance metrics.",
            ],
            "corporate_action": [
                f"Corporate announcement details transaction. The action represents a strategic shift in company operations.",
                f"Company disclosed transaction terms. Board of directors approved corporate action.",
                f"SEC filing outlines action details. The transaction is subject to regulatory approval.",
            ],
            "regulatory_release": [
                f"Regulatory agency issued release. The release provides guidance to market participants.",
                f"Government officials addressed regulatory matters. The announcement applies to specific market sectors.",
                f"Regulatory body issued clarification. Market participants should review updated guidance.",
            ],
        }

        excerpt_list = excerpts.get(event_type)
        if excerpt_list is None:
            excerpt_list = ["Event details provided in official release."]
        excerpt = random.choice(excerpt_list)
        if random.random() < 0.3:
            excerpt += f" {event['facts'][random.randint(0, len(event['facts']) - 1)]}."

        chunk_id = f"event_{event_type}_{date}"
        doc_id = f"{source['name'].upper().replace(' ', '-')}-{date.replace('-', '')}"

        evidence_items.append(
            {
                "event_id": event_id,
                "source_name": source["name"],
                "source_type": source["source_type"],
                "published_ts": published_ts,
                "canonical_url": source["canonical_url"],
                "excerpt": excerpt,
                "doc_id": doc_id,
                "chunk_id": chunk_id,
            }
        )

    return evidence_items


def generate_day_data(
    date: str, prev_date: Optional[str] = None, seed: Optional[int] = None
) -> Dict[str, Any]:
    """Generate complete day data"""
    if seed is not None:
        random.seed(seed)

    print(f"Generating data for {date}...")

    doc_id = str(uuid.uuid4())
    governance = generate_governance(date, doc_id)

    print(f"  - Generated governance block")

    market_outcomes = generate_market_outcomes(date, prev_date)
    print(f"  - Generated market outcomes")

    events = generate_events(date)
    print(f"  - Generated {len(events)} events")

    day_tickers = [t["symbol"] for t in generate_tickers(date, prev_date)]
    reaction_windows = generate_reaction_windows(events, day_tickers)
    print(f"  - Generated {len(reaction_windows)} reaction windows")

    movers = generate_movers(day_tickers, market_outcomes)
    print(f"  - Generated movers")

    sectors = generate_sectors(date, prev_date)
    print(f"  - Generated sector data")

    tickers = generate_tickers(date, prev_date)
    print(f"  - Generated {len(tickers)} ticker entries")

    evidence_items = generate_evidence_items(events, date)
    print(f"  - Generated {len(evidence_items)} evidence items")

    day_data = {
        "governance": governance,
        "market_outcomes": market_outcomes,
        "events": events,
        "reaction_windows": reaction_windows,
        "movers": movers,
        "sectors": sectors,
        "tickers": tickers,
        "evidence_items": evidence_items,
    }

    PREVIOUS_CLOSES[date] = {
        "indices": {
            "SPX": market_outcomes["indices"][0]["close"],
            "NDX": market_outcomes["indices"][1]["close"],
        },
        "tickers": {t["symbol"]: t["close"] for t in tickers},
    }

    return day_data


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate Layer 1 synthetic data")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument(
        "--skip-validate", action="store_true", help="Skip validation step"
    )
    parser.add_argument(
        "--skip-render", action="store_true", help="Skip rendering step"
    )

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        print(f"Using random seed: {args.seed}")

    sample_data_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    sample_output_dir = os.path.join(os.path.dirname(__file__), "sample_output")

    os.makedirs(sample_data_dir, exist_ok=True)
    os.makedirs(sample_output_dir, exist_ok=True)

    prev_date = None
    for date in DATES:
        day_data = generate_day_data(date, prev_date, args.seed)

        output_file = os.path.join(sample_data_dir, f"day_{date}.json")
        with open(output_file, "w") as f:
            json.dump(day_data, f, indent=2)

        print(f"✓ Saved {output_file}")
        print()

        prev_date = date

    print("=" * 50)
    print("Data generation complete!")
    print(f"Generated {len(DATES)} day files")
    print("=" * 50)

    if not args.skip_validate:
        print("\nRunning validation...")
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "validate_l1.py")],
            cwd=os.path.dirname(__file__),
        )
        if result.returncode == 0:
            print("✓ Validation complete")

    if not args.skip_render:
        print("\nRunning rendering...")
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "render_l1.py")],
            cwd=os.path.dirname(__file__),
        )
        if result.returncode == 0:
            print("✓ Rendering complete")


if __name__ == "__main__":
    main()
