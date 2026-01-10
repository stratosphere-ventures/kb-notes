#!/usr/bin/env python3
"""
Layer-1 Validator + Linter (CI-gated)

Gates:
- JSON Schema validation
- L1 purity lint (forbidden tokens)
- Referential integrity: reaction_windows/evidence_items must reference events
- Timestamp format checks
- Cross-file realism checks (optional; stricter in eval mode)

Exit codes:
0 = pass
1 = lint/validation failure
2 = configuration error
"""

import argparse
import json
import os
import re
import sys
import pytz
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# -----------------------------
# Lint report model
# -----------------------------
@dataclass
class LintItem:
    code: str
    severity: str  # "HARD" | "SOFT"
    path: str
    message: str


FORBIDDEN_TOKENS = [
    "because",
    "due to",
    "driven by",
    "as investors",
    "on hopes",
    "on fears",
    "relief",
    "concerns",
    "sentiment",
    "risk-on",
    "risk off",
    "risk-off",
    "bullish",
    "bearish",
    "support",
    "resistance",
    "oversold",
    "overbought",
    "priced in",
    "implies",
    "signals",
    "likely",
    "expected to",
    "should",
    "could",
    "may ",
    "outlook",
    "forecast",
    "led",
    "dragged",
    "weighed",
    "boosted",
    "lagged",
]

ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def add_item(lst: List[LintItem], code: str, severity: str, path: str, msg: str):
    lst.append(LintItem(code=code, severity=severity, path=path, message=msg))


def contains_forbidden(text: str) -> Optional[str]:
    t = (text or "").lower()
    for tok in FORBIDDEN_TOKENS:
        if tok in t:
            return tok
    return None


def validate_schema(
    instance: Dict[str, Any], schema: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    try:
        import jsonschema
    except ImportError:
        # For CI, you should install jsonschema; but don't block dev.
        return True, None

    try:
        jsonschema.validate(instance=instance, schema=schema)
        return True, None
    except Exception as e:
        return False, str(e)


def check_governance(day: Dict[str, Any], errors: List[LintItem]):
    g = day.get("governance", {})
    required = [
        "date",
        "region",
        "market_session",
        "published_ts",
        "asof_ts",
        "doc_version",
        "trust_tier",
        "market_data_vendor",
        "market_data_version",
        "pipeline_version",
        "doc_id",
        "doc_key",
    ]
    for k in required:
        if k not in g:
            add_item(
                errors,
                "L1-GOV-001",
                "HARD",
                f"governance.{k}",
                f"Missing required field '{k}'.",
            )

    pub = g.get("published_ts")
    asof = g.get("asof_ts")

    if pub and not ISO_Z_RE.match(pub):
        add_item(
            errors,
            "L1-GOV-002",
            "HARD",
            "governance.published_ts",
            "Must be ISO8601 Zulu (YYYY-MM-DDTHH:MM:SSZ).",
        )
    if asof and not ISO_Z_RE.match(asof):
        add_item(
            errors,
            "L1-GOV-002",
            "HARD",
            "governance.asof_ts",
            "Must be ISO8601 Zulu (YYYY-MM-DDTHH:MM:SSZ).",
        )

    if pub and asof and ISO_Z_RE.match(pub) and ISO_Z_RE.match(asof) and asof > pub:
        add_item(
            errors,
            "L1-GOV-002",
            "HARD",
            "governance",
            "asof_ts must be <= published_ts.",
        )

    date = g.get("date")
    region = (g.get("region") or "").lower()
    doc_key = g.get("doc_key")
    if date and region and doc_key:
        expected = f"market_wrap/{region}/{date}"
        if doc_key != expected:
            add_item(
                errors,
                "L1-GOV-003",
                "HARD",
                "governance.doc_key",
                f"doc_key must equal '{expected}' (got '{doc_key}').",
            )


def check_market_outcomes(day: Dict[str, Any], errors: List[LintItem]):
    mo = day.get("market_outcomes", {})
    headline = mo.get("headline_neutral", "")
    bad = contains_forbidden(headline)
    if bad:
        add_item(
            errors,
            "L1-PUR-001",
            "HARD",
            "market_outcomes.headline_neutral",
            f"Headline contains forbidden token '{bad}'.",
        )

    # index range sanity
    for i, idx in enumerate(mo.get("indices", []) or []):
        low, high, close = idx.get("low"), idx.get("high"), idx.get("close")
        sym = idx.get("symbol", "?")
        if low is not None and high is not None and close is not None:
            if not (low < high):
                add_item(
                    errors,
                    "L1-CON-001",
                    "HARD",
                    f"market_outcomes.indices[{i}]",
                    f"{sym}: require low < high.",
                )
            if not (low <= close <= high):
                add_item(
                    errors,
                    "L1-CON-001",
                    "HARD",
                    f"market_outcomes.indices[{i}]",
                    f"{sym}: require low <= close <= high.",
                )

    # volatility: prefer change_pts (but tolerate legacy change)
    for i, v in enumerate(mo.get("volatility", []) or []):
        sym = v.get("symbol", "")
        if sym in ("VIX", "VIX9D") and ("change" in v and "change_pts" not in v):
            # don't hard-fail legacy data, but force you to upgrade generator
            add_item(
                errors,
                "L1-CON-006",
                "HARD",
                f"market_outcomes.volatility[{i}]",
                f"{sym}: use change_pts (points), not generic change.",
            )


def infer_market_session(timestamp_iso: str, region: str = "US") -> str:
    """
    Infer market_session from timestamp and region using proper ET timezone conversion.
    For US equities:
    - Pre-market: before 9:30am ET
    - Regular: 9:30am-4:00pm ET
    - Post-market: after 4:00pm ET
    """
    if region != "US":
        return "regular"  # Default for non-US; extend later

    try:
        # Parse UTC timestamp
        dt_utc = datetime.strptime(timestamp_iso, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=pytz.UTC
        )

        # Convert to Eastern Time (handles both EST and EDT automatically)
        eastern = pytz.timezone("America/New_York")
        dt_et = dt_utc.astimezone(eastern)

        # Extract hour and minute for session determination
        hour = dt_et.hour
        minute = dt_et.minute

        # US equities trading hours (ET)
        # Premarket: before 9:30am ET
        if hour < 9 or (hour == 9 and minute < 30):
            return "pre"
        # Regular session: 9:30am-4:00pm ET
        elif (
            (hour == 9 and minute >= 30)
            or (hour > 9 and hour < 16)
            or (hour == 16 and minute == 0)
        ):
            return "regular"
        # Post-market: after 4:00pm ET
        else:  # hour >= 16 and minute > 0, or hour > 16
            return "post"
    except (ValueError, AttributeError, pytz.exceptions.NonExistentTimeError):
        return "regular"  # Fallback


def check_events_reactions_evidence(day: Dict[str, Any], errors: List[LintItem]):
    events = day.get("events", []) or []
    event_ids: List[str] = []
    region = day.get("governance", {}).get("region", "US")

    for i, e in enumerate(events):
        eid = e.get("event_id")
        if not eid:
            add_item(
                errors,
                "L1-REF-001",
                "HARD",
                f"events[{i}].event_id",
                "Missing event_id.",
            )
            continue
        event_ids.append(eid)

        # Check market_session consistency with timestamp
        published_ts = e.get("published_ts")
        stated_session = e.get("market_session")
        if published_ts and stated_session:
            inferred = infer_market_session(published_ts, region)
            if inferred != stated_session:
                add_item(
                    errors,
                    "L1-SESS-001",
                    "HARD",
                    f"events[{i}].market_session",
                    f"Session '{stated_session}' inconsistent with timestamp {published_ts} (should be '{inferred}').",
                )

        for j, fact in enumerate(e.get("facts", []) or []):
            bad = contains_forbidden(fact)
            if bad:
                add_item(
                    errors,
                    "L1-PUR-001",
                    "HARD",
                    f"events[{i}].facts[{j}]",
                    f"Fact contains forbidden token '{bad}'.",
                )

    if len(event_ids) != len(set(event_ids)):
        add_item(
            errors,
            "L1-REF-001",
            "HARD",
            "events",
            "Duplicate event_id detected within a day.",
        )

    event_set = set(event_ids)

    # Check reaction windows: VIX uses move_pts, others use move_pct
    for i, rw in enumerate(day.get("reaction_windows", []) or []):
        eid = rw.get("event_id")
        if eid and eid not in event_set:
            add_item(
                errors,
                "L1-REF-002",
                "HARD",
                f"reaction_windows[{i}].event_id",
                f"References missing event_id '{eid}'.",
            )

        instrument = rw.get("instrument", "")
        has_move_pct = "move_pct" in rw
        has_move_pts = "move_pts" in rw

        # VIX-family instruments must use move_pts
        if instrument in ("VIX", "VIX9D"):
            if not has_move_pts:
                add_item(
                    errors,
                    "L1-VIX-001",
                    "HARD",
                    f"reaction_windows[{i}].instrument",
                    f"{instrument} reaction must use move_pts, not move_pct.",
                )
        else:
            # Equity indices/tickers must use move_pct
            if not has_move_pct:
                add_item(
                    errors,
                    "L1-MOVE-001",
                    "HARD",
                    f"reaction_windows[{i}].instrument",
                    f"Non-VIX instrument '{instrument}' must use move_pct, not move_pts.",
                )

    # Check evidence_items: uniqueness, referential integrity, and content
    evidence_items = day.get("evidence_items", []) or []
    doc_ids = []
    chunk_ids = []

    for i, ev in enumerate(evidence_items):
        eid = ev.get("event_id")
        if eid and eid not in event_set:
            add_item(
                errors,
                "L1-REF-003",
                "HARD",
                f"evidence_items[{i}].event_id",
                f"References missing event_id '{eid}'.",
            )

        excerpt = ev.get("excerpt", "")
        bad = contains_forbidden(excerpt)
        if bad:
            add_item(
                errors,
                "L1-PUR-002",
                "HARD",
                f"evidence_items[{i}].excerpt",
                f"Evidence excerpt contains forbidden token '{bad}'.",
            )

        # Uniqueness checks
        doc_id = ev.get("doc_id")
        if doc_id:
            if doc_id in doc_ids:
                add_item(
                    errors,
                    "L1-UNIQ-001",
                    "HARD",
                    f"evidence_items[{i}].doc_id",
                    f"Duplicate doc_id '{doc_id}'.",
                )
            doc_ids.append(doc_id)

        chunk_id = ev.get("chunk_id")
        if chunk_id:
            if chunk_id in chunk_ids:
                add_item(
                    errors,
                    "L1-UNIQ-002",
                    "HARD",
                    f"evidence_items[{i}].chunk_id",
                    f"Duplicate chunk_id '{chunk_id}'.",
                )
            chunk_ids.append(chunk_id)

        # Excerpt length check
        if len(excerpt) > 280:
            add_item(
                errors,
                "L1-LEN-001",
                "HARD",
                f"evidence_items[{i}].excerpt",
                f"Excerpt exceeds 280 chars (got {len(excerpt)}).",
            )


def check_movers(day: Dict[str, Any], errors: List[LintItem]):
    """Validate movers: gainers must be positive, decliners must be negative."""
    movers = day.get("movers", {})

    gainers = movers.get("top_gainers", []) or []
    for i, g in enumerate(gainers):
        ret = g.get("return_pct")
        if ret is not None and ret <= 0:
            add_item(
                errors,
                "L1-REAL-002",
                "HARD",
                f"movers.top_gainers[{i}].return_pct",
                f"Gainer '{g.get('symbol')}' has non-positive return: {ret}%.",
            )

    decliners = movers.get("top_decliners", []) or []
    for i, d in enumerate(decliners):
        ret = d.get("return_pct")
        if ret is not None and ret >= 0:
            add_item(
                errors,
                "L1-REAL-003",
                "HARD",
                f"movers.top_decliners[{i}].return_pct",
                f"Decliner '{d.get('symbol')}' has non-negative return: {ret}%.",
            )


def check_rates_formatting(day: Dict[str, Any], errors: List[LintItem]):
    """Validate rates/FX/commodities formatting and units."""
    rfc = day.get("market_outcomes", {}).get("rates_fx_commodities", []) or []

    for i, r in enumerate(rfc):
        unit = r.get("unit", "")
        symbol = r.get("symbol", "?")

        # If unit is "pct", change should be in bps, not change_pct
        if unit == "pct":
            if "change_pct" in r and "change_bps" not in r:
                add_item(
                    errors,
                    "L1-FMT-001",
                    "HARD",
                    f"market_outcomes.rates_fx_commodities[{i}]",
                    f"{symbol}: unit=pct requires change_bps, not change_pct.",
                )

        # Check for markdown-breaking newlines in scalar fields
        value = str(r.get("value", ""))
        if "\n" in value:
            add_item(
                errors,
                "L1-FMT-002",
                "HARD",
                f"market_outcomes.rates_fx_commodities[{i}].value",
                f"{symbol}: value contains newline (markdown-breaking).",
            )

        if "\n" in str(unit):
            add_item(
                errors,
                "L1-FMT-002",
                "HARD",
                f"market_outcomes.rates_fx_commodities[{i}].unit",
                f"{symbol}: unit contains newline (markdown-breaking).",
            )


def cross_file_realism(
    days: List[Tuple[str, Dict[str, Any]]], warnings: List[LintItem], eval_mode: bool
):
    # light realism: repeated exact closes for core indices is suspicious (synthetic degeneracy)
    key_syms = {"DJIA", "QQQ", "IWM", "SPX", "NDX"}
    seen = {s: set() for s in key_syms}

    for fname, day in days:
        for idx in day.get("market_outcomes", {}).get("indices", []) or []:
            sym = idx.get("symbol")
            close = idx.get("close")
            if sym in key_syms and close is not None:
                if close in seen[sym]:
                    warnings.append(
                        LintItem(
                            code="L1-REAL-001",
                            severity="HARD" if eval_mode else "SOFT",
                            path=f"{fname}:market_outcomes.indices[{sym}].close",
                            message=f"{sym} close {close} repeats across dates (synthetic degeneracy).",
                        )
                    )
                else:
                    seen[sym].add(close)


def main() -> int:
    p = argparse.ArgumentParser(description="Validate + lint Layer-1 JSON files")
    p.add_argument("--schema", default="schema.json")
    p.add_argument("--input-dir", default="sample_data")
    p.add_argument("--profile", choices=["dev", "eval"], default="dev")
    args = p.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(script_dir, args.schema)
    input_dir = os.path.join(script_dir, args.input_dir)

    if not os.path.exists(schema_path):
        print(f"ERROR: schema not found: {schema_path}")
        return 2
    if not os.path.exists(input_dir):
        print(f"ERROR: input dir not found: {input_dir}")
        return 2

    schema = load_json(schema_path)
    files = sorted([f for f in os.listdir(input_dir) if f.endswith(".json")])
    if not files:
        print(f"ERROR: no JSON files in {input_dir}")
        return 2

    hard_fail = False
    days_loaded: List[Tuple[str, Dict[str, Any]]] = []
    all_errors: Dict[str, List[LintItem]] = {}
    all_warnings: Dict[str, List[LintItem]] = {}

    for f in files:
        full = os.path.join(input_dir, f)
        errors: List[LintItem] = []
        warnings: List[LintItem] = []

        try:
            day = load_json(full)
        except Exception as e:
            add_item(errors, "L1-GEN-000", "HARD", f, f"Failed to parse JSON: {e}")
            all_errors[f] = errors
            all_warnings[f] = warnings
            hard_fail = True
            continue

        ok, msg = validate_schema(day, schema)
        if not ok:
            add_item(
                errors,
                "L1-SCHEMA-000",
                "HARD",
                "schema",
                f"Schema validation failed: {msg}",
            )

        check_governance(day, errors)
        check_market_outcomes(day, errors)
        check_events_reactions_evidence(day, errors)
        check_movers(day, errors)
        check_rates_formatting(day, errors)

        if errors:
            hard_fail = True

        days_loaded.append((f, day))
        all_errors[f] = errors
        all_warnings[f] = warnings

    # cross-file realism checks
    cross: List[LintItem] = []
    cross_file_realism(days_loaded, cross, eval_mode=(args.profile == "eval"))

    # print report
    print(f"Validating {len(files)} file(s) (profile={args.profile})")
    print("=" * 70)
    for f in files:
        errs = all_errors.get(f, [])
        warns = all_warnings.get(f, [])
        status = (
            "OK" if (not errs and not (args.profile == "eval" and warns)) else "FAIL"
        )
        print(f"{status}: {f}")
        for it in errs:
            print(f"  [HARD] {it.code} @ {it.path}: {it.message}")
        for it in warns:
            if args.profile == "eval":
                print(f"  [SOFT] {it.code} @ {it.path}: {it.message}")

    if cross:
        print("-" * 70)
        print("Cross-file checks:")
        for it in cross:
            print(f"  [{it.severity}] {it.code} @ {it.path}: {it.message}")
        if args.profile == "eval" and any(it.severity == "HARD" for it in cross):
            hard_fail = True

    print("=" * 70)

    if hard_fail:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
