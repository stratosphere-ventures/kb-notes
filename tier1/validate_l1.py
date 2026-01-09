#!/usr/bin/env python3
"""
Layer-1 Validator + Linter
- JSON Schema validation
- Layer-1 lint rules (hard/soft) with error codes
- Cross-file realism checks for Tier-1 evaluation quality
- CI-friendly exit codes

Usage:
  python validate_l1.py --schema schema.json --input-dir sample_data --profile dev
  python validate_l1.py --profile eval   # warnings treated as errors
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
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


@dataclass
class FileReport:
    filename: str
    schema_ok: bool
    errors: List[LintItem]
    warnings: List[LintItem]


FORBIDDEN_TOKENS = [
    # causal / interpretive / forecast-ish
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
    # leadership language (often interpretation)
    "led",
    "dragged",
    "weighed",
    "boosted",
    "lagged",
]

ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


def safe_get(d: Dict[str, Any], keys: List[str]) -> Any:
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def add_item(lst: List[LintItem], code: str, severity: str, path: str, msg: str):
    lst.append(LintItem(code=code, severity=severity, path=path, message=msg))


def contains_forbidden(text: str) -> Optional[str]:
    t = (text or "").lower()
    for tok in FORBIDDEN_TOKENS:
        if tok in t:
            return tok
    return None


# -----------------------------
# Rule checks
# -----------------------------
def check_governance(
    day: Dict[str, Any], errors: List[LintItem], warnings: List[LintItem], filename: str
):
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
                f"Missing required governance field '{k}'.",
            )

    
    # Volatility validation: VIX/VIX9D must use change_pts field
    vol = mo.get("volatility", [])
    for i, v in enumerate(vol):
        sym = v.get("symbol", "")
        if sym in ("VIX", "VIX9D"):
            if "change_pts" not in v and any(k.startswith("change") for k in v):
                add_item(
                    errors,
                    "L1-CON-006",
                    "HARD",
                    f"market_outcomes.volatility[{i}]",
                    f"{sym} must have 'change_pts' field (found {list(v.keys())}).",
                )
    
    # timestamp format + ordering
    pub = g.get("published_ts")
    asof = g.get("asof_ts")

    if pub and not ISO_Z_RE.match(pub):
        add_item(
            errors,
            "L1-GOV-002",
            "HARD",
            "governance.published_ts",
            "published_ts must be ISO8601 Zulu (YYYY-MM-DDTHH:MM:SSZ).",
        )
    if asof and not ISO_Z_RE.match(asof):
        add_item(
            errors,
            "L1-GOV-002",
            "HARD",
            "governance.asof_ts",
            "asof_ts must be ISO8601 Zulu (YYYY-MM-DDTHH:MM:SSZ).",
        )

    # lexical compare works for Zulu timestamps
    if pub and asof and ISO_Z_RE.match(pub) and ISO_Z_RE.match(asof) and asof > pub:
        add_item(
            errors,
            "L1-GOV-002",
            "HARD",
            "governance",
            "asof_ts must be <= published_ts.",
        )

    # doc_key convention
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


def check_market_outcomes(
    day: Dict[str, Any], errors: List[LintItem], warnings: List[LintItem]
):
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

    # Index range sanity
    indices = mo.get("indices", [])
    for i, idx in enumerate(indices):
        low = idx.get("low")
        high = idx.get("high")
        close = idx.get("close")
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

        # Return math sanity if prev_close exists
        prev = idx.get("prev_close")
        ret = idx.get("return_pct")
        if prev is not None and close is not None and ret is not None and prev != 0:
            calc = (close / prev - 1.0) * 100.0
            if abs(calc - ret) > 0.02:
                add_item(
                    errors,
                    "L1-CON-002",
                    "HARD",
                    f"market_outcomes.indices[{i}]",
                    f"{sym}: return_pct inconsistent with close/prev_close (calc={calc:.3f}, got={ret:.3f}).",
                )

    # Units sanity
    rfc = mo.get("rates_fx_commodities", [])
    for i, r in enumerate(rfc):
        unit = r.get("unit")
        sym = r.get("symbol", "")
        if unit not in ("pct", "bps", "usd", "index", "other", "ratio"):
            add_item(
                errors,
                "L1-CON-003",
                "HARD",
                f"market_outcomes.rates_fx_commodities[{i}].unit",
                f"Unknown unit '{unit}' for {sym}.",
            )


def check_events_reactions_evidence(
    day: Dict[str, Any], errors: List[LintItem], warnings: List[LintItem]
):
    events = day.get("events", [])
    event_ids = []
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

        # facts purity
        facts = e.get("facts", [])
        for j, f in enumerate(facts):
            bad = contains_forbidden(f)
            if bad:
                add_item(
                    errors,
                    "L1-PUR-001",
                    "HARD",
                    f"events[{i}].facts[{j}]",
                    f"Event fact contains forbidden token '{bad}'.",
                )

    # uniqueness
    if len(event_ids) != len(set(event_ids)):
        add_item(
            errors,
            "L1-REF-001",
            "HARD",
            "events",
            "Duplicate event_id detected within a day.",
        )

    # reactions referential integrity
    rws = day.get("reaction_windows", [])
    for i, rw in enumerate(rws):
        eid = rw.get("event_id")
        if eid and eid not in set(event_ids):
            add_item(
                errors,
                "L1-REF-002",
                "HARD",
                f"reaction_windows[{i}].event_id",
                f"reaction_windows references missing event_id '{eid}'.",
            )

    # evidence referential integrity + purity
    evs = day.get("evidence_items", [])
    for i, ev in enumerate(evs):
        eid = ev.get("event_id")
        if eid and eid not in set(event_ids):
            add_item(
                errors,
                "L1-REF-003",
                "HARD",
                f"evidence_items[{i}].event_id",
                f"evidence_items references missing event_id '{eid}'.",
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

        # Evidence must be "fact style": at least one digit or a named action word
        if not re.search(r"\d", excerpt) and not re.search(
            r"\b(announced|reported|filed|released|approved|priced)\b", excerpt.lower()
        ):
            add_item(
                warnings,
                "L1-PUR-002",
                "SOFT",
                f"evidence_items[{i}].excerpt",
                "Evidence excerpt may not be fact-style (no digits/action verbs).",
            )


def cross_file_realism(
    days: List[Tuple[str, Dict[str, Any]]],
    errors: List[LintItem],
    warnings: List[LintItem],
    eval_mode: bool,
):
    """
    Check duplication across dates for key symbols (Tier-1 quality).
    """
    key_syms = {"DJIA", "QQQ", "IWM", "SPX", "NDX"}
    seen: Dict[str, Dict[float, str]] = {s: {} for s in key_syms}

    for fname, day in days:
        date = safe_get(day, ["governance", "date"]) or "unknown_date"
        for idx in safe_get(day, ["market_outcomes", "indices"]) or []:
            sym = idx.get("symbol")
            if sym in key_syms:
                close = idx.get("close")
                if close is None:
                    continue
                prev = seen[sym].get(close)
                if prev is not None:
                    # repeated close across days -> degeneracy
                    item = LintItem(
                        code="L1-REAL-001",
                        severity="HARD" if eval_mode else "SOFT",
                        path=f"{fname}:market_outcomes.indices[{sym}].close",
                        message=f"{sym} close {close} repeats across dates ({prev} and {date}). This degrades eval realism.",
                    )
                    (errors if eval_mode else warnings).append(item)
                else:
                    seen[sym][close] = date


def validate_schema(
    instance: Dict[str, Any], schema: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    try:
        import jsonschema
    except ImportError:
        # If you want strictness, flip this to False.
        return True, None

    try:
        jsonschema.validate(instance=instance, schema=schema)
        return True, None
    except Exception as e:
        return False, str(e)


def main():
    p = argparse.ArgumentParser(description="Validate + lint Layer-1 JSON files (v2)")
    p.add_argument("--schema", default="schema.json")
    p.add_argument("--input-dir", default="sample_data")
    p.add_argument(
        "--profile",
        choices=["dev", "eval"],
        default="dev",
        help="dev: fail on HARD only; eval: fail on HARD + SOFT realism/purity warnings.",
    )
    p.add_argument("--report", default="lint_report.json")
    args = p.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(script_dir, args.schema)
    input_dir = os.path.join(script_dir, args.input_dir)
    report_path = os.path.join(script_dir, args.report)

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

    reports: List[FileReport] = []
    loaded_days: List[Tuple[str, Dict[str, Any]]] = []

    # per-file validation + lint
    for f in files:
        full = os.path.join(input_dir, f)
        errors: List[LintItem] = []
        warnings: List[LintItem] = []

        try:
            day = load_json(full)
        except Exception as e:
            add_item(errors, "L1-GEN-000", "HARD", f, f"Failed to parse JSON: {e}")
            reports.append(
                FileReport(
                    filename=f, schema_ok=False, errors=errors, warnings=warnings
                )
            )
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
        else:
            loaded_days.append((f, day))

        # L1 lint checks (only if JSON parsed)
        check_governance(day, errors, warnings, f)
        check_market_outcomes(day, errors, warnings)
        check_events_reactions_evidence(day, errors, warnings)

        reports.append(
            FileReport(filename=f, schema_ok=ok, errors=errors, warnings=warnings)
        )

    # cross-file realism checks
    cross_errors: List[LintItem] = []
    cross_warnings: List[LintItem] = []
    cross_file_realism(
        loaded_days, cross_errors, cross_warnings, eval_mode=(args.profile == "eval")
    )

    # Summarize
    hard_fail = False
    soft_fail = False

    print(f"Validating {len(files)} file(s) (profile={args.profile})")
    print("=" * 70)

    for r in reports:
        if r.errors:
            hard_fail = True
        if r.warnings and args.profile == "eval":
            soft_fail = True

        status = (
            "OK"
            if (not r.errors and (args.profile != "eval" or not r.warnings))
            else "FAIL"
        )
        print(f"{status}: {r.filename}  (schema_ok={r.schema_ok})")
        for it in r.errors:
            print(f"  [HARD] {it.code} @ {it.path}: {it.message}")
        for it in r.warnings:
            sev = it.severity
            print(f"  [{sev}] {it.code} @ {it.path}: {it.message}")

    # cross-file results
    if cross_errors or cross_warnings:
        print("-" * 70)
        print("Cross-file checks:")
        for it in cross_errors:
            print(f"  [HARD] {it.code} @ {it.path}: {it.message}")
        for it in cross_warnings:
            print(f"  [SOFT] {it.code} @ {it.path}: {it.message}")

    # Write JSON report
    def to_dict_item(it: LintItem) -> Dict[str, Any]:
        return {
            "code": it.code,
            "severity": it.severity,
            "path": it.path,
            "message": it.message,
        }

    report_json = {
        "profile": args.profile,
        "files": [
            {
                "filename": r.filename,
                "schema_ok": r.schema_ok,
                "errors": [to_dict_item(e) for e in r.errors],
                "warnings": [to_dict_item(w) for w in r.warnings],
            }
            for r in reports
        ],
        "cross_file": {
            "errors": [to_dict_item(e) for e in cross_errors],
            "warnings": [to_dict_item(w) for w in cross_warnings],
        },
    }
    with open(report_path, "w") as f:
        json.dump(report_json, f, indent=2)

    print("=" * 70)
    print(f"Wrote report: {report_path}")

    # Exit code behavior:
    # 0 = pass
    # 1 = lint fail (hard, or eval-mode warnings)
    # 2 = configuration error
    if hard_fail:
        return 1
    if args.profile == "eval" and (soft_fail or cross_warnings or cross_errors):
        # in eval profile, warnings can fail, and cross-file SOFT become HARD earlier
        return 1
    if cross_errors:
        return 1
    if args.profile == "eval" and cross_warnings:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
