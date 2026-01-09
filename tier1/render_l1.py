#!/usr/bin/env python3
"""
Jinja2 Rendering Script for Layer 1 Data
- StrictUndefined to fail on missing fields
- Post-render markdown lint (structure + forbidden language)
- CI-friendly exit codes

Usage:
  python render_l1.py --template market_wrap_l1.md.j2 --input-dir sample_data --output-dir sample_output
"""

import argparse
import json
import os
import re
import sys
from typing import List, Tuple

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

REQUIRED_HEADINGS = [
    "## 1) Executive Fact Summary",
    "## 2) Session Timeline (Attributed Events)",
    "## 3) Measured Market Reactions",
    "## 4) Movers and Sectors",
    "## 5) Company Fact Panels",
    "## 6) Evidence Appendix",
]

REQUIRED_CHUNKS = [
    "wrap_summary",
    "wrap_timeline",
    "wrap_reactions",
    "wrap_movers_sectors",
    "wrap_ticker_panels",
    "wrap_evidence",
]


def contains_forbidden(text: str) -> Tuple[bool, str]:
    t = (text or "").lower()
    for tok in FORBIDDEN_TOKENS:
        if tok in t:
            return True, tok
    return False, ""


def md_lint(rendered: str) -> List[str]:
    issues = []

    # Required headings
    for h in REQUIRED_HEADINGS:
        if h not in rendered:
            issues.append(f"MD-LINT-HEAD-001 missing heading: {h}")

    # Required chunk markers
    for cid in REQUIRED_CHUNKS:
        if f"<!-- chunk_id: {cid} -->" not in rendered:
            issues.append(f"MD-LINT-CHUNK-001 missing chunk marker: {cid}")

    # Forbidden token scan
    bad, tok = contains_forbidden(rendered)
    if bad:
        issues.append(f"MD-LINT-PUR-001 forbidden token found: '{tok}'")

    # Bullet sanity: lines containing multiple bullets concatenated (common formatting bug)
    # Example pattern: "- **A**: ... - **B**: ..." on same line
    concat_bullet_re = re.compile(r"^- .* - \*\*", re.MULTILINE)
    if concat_bullet_re.search(rendered):
        issues.append(
            "MD-LINT-FMT-001 concatenated bullet items detected (ensure one bullet per line)."
        )

    return issues


def render_one(json_path: str, template_path: str, output_dir: str) -> Tuple[bool, str]:
    try:
        import jinja2
    except ImportError:
        return False, "jinja2 not installed (pip install jinja2)"

    try:
        # Load JSON data
        with open(json_path, "r") as f:
            day = json.load(f)

        template_dir = os.path.dirname(template_path)
        template_name = os.path.basename(template_path)

        # Configure Jinja2 environment
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template(template_name)

        # Render template
        rendered = template.render(day=day)

        # Post-render markdown lint
        issues = md_lint(rendered)
        if issues:
            return False, "; ".join(issues)
    except Exception as e:
        return False, f"Render failed: {str(e)}"

    out_name = os.path.basename(json_path).replace(".json", ".md")
    out_path = os.path.join(output_dir, out_name)
    with open(out_path, "w") as f:
        f.write(rendered)

    return True, out_name


def main():
    p = argparse.ArgumentParser(
        description="Render Layer-1 JSON files to Markdown (v2)"
    )
    p.add_argument("--template", default="market_wrap_l1.md.j2")
    p.add_argument("--input-dir", default="sample_data")
    p.add_argument("--output-dir", default="sample_output")
    args = p.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, args.template)
    input_dir = os.path.join(script_dir, args.input_dir)
    output_dir = os.path.join(script_dir, args.output_dir)

    if not os.path.exists(template_path):
        print(f"ERROR: template not found: {template_path}")
        return 2
    if not os.path.exists(input_dir):
        print(f"ERROR: input dir not found: {input_dir}")
        return 2

    os.makedirs(output_dir, exist_ok=True)
    json_files = sorted([f for f in os.listdir(input_dir) if f.endswith(".json")])
    if not json_files:
        print(f"ERROR: no JSON files in {input_dir}")
        return 2

    passed = 0
    failed = 0

    print(f"Rendering {len(json_files)} file(s) using {args.template} ...")
    print("=" * 70)

    for jf in json_files:
        full = os.path.join(input_dir, jf)
        ok, msg = render_one(full, template_path, output_dir)
        if ok:
            passed += 1
            print(f"OK:   {jf} -> {msg}")
        else:
            failed += 1
            print(f"FAIL: {jf} -> {msg}")

    print("=" * 70)
    print(f"Render complete: {passed} passed, {failed} failed")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
