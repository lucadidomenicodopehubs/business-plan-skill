#!/usr/bin/env python3
"""What-if scenario recalculation script.

Modifies businessPlanInput.json, saves history, and re-runs the financial model.

Usage:
    whatif.py --field <dot.path> --value <val>
    whatif.py --patch '<json>'
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _coerce_value(raw: str):
    """Auto-detect type: try float, int, bool, else string."""
    # Try bool first (before int, since bool("true") would fail int())
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    # Try int
    try:
        int_val = int(raw)
        # But if it has a dot it's a float
        if "." not in raw:
            return int_val
    except ValueError:
        pass
    # Try float
    try:
        return float(raw)
    except ValueError:
        pass
    # Fallback to string
    return raw


def _set_nested(d: dict, dot_path: str, value):
    """Set a value in a nested dict using dot-notation path."""
    keys = dot_path.split(".")
    current = d
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            raise KeyError(f"Path segment '{key}' not found or not a dict in '{dot_path}'")
        current = current[key]
    current[keys[-1]] = value


def _diff_summary(old: dict, new: dict) -> str:
    """Print a summary diff of key changed metrics."""
    lines = []
    for scenario in ("base", "optimistic", "pessimistic"):
        old_s = old.get("scenarios", {}).get(scenario, {})
        new_s = new.get("scenarios", {}).get(scenario, {})
        if not old_s or not new_s:
            continue
        old_pl = old_s.get("pl", [])
        new_pl = new_s.get("pl", [])
        for i, (old_yr, new_yr) in enumerate(zip(old_pl, new_pl)):
            for metric in ("revenue_total", "ebitda", "net_income"):
                ov = old_yr.get(metric)
                nv = new_yr.get(metric)
                if ov != nv:
                    lines.append(
                        f"  [{scenario}] year {i+1} {metric}: {ov} -> {nv}"
                    )
    if lines:
        return "Changed metrics:\n" + "\n".join(lines)
    return "No metric changes detected."


def main():
    parser = argparse.ArgumentParser(description="What-if scenario recalculation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--field", metavar="DOT_PATH", help="Dot-notation field path")
    group.add_argument("--patch", metavar="JSON", help="JSON object with dot-notation keys")
    parser.add_argument("--value", metavar="VAL", help="Value for --field (required with --field)")

    args = parser.parse_args()

    if args.field and args.value is None:
        parser.error("--value is required when --field is specified")

    # 1. Locate .business-plan/ in cwd
    bp_dir = Path.cwd() / ".business-plan"
    if not bp_dir.is_dir():
        print(f"Error: .business-plan/ directory not found in {Path.cwd()}", file=sys.stderr)
        sys.exit(1)

    input_path = bp_dir / "businessPlanInput.json"
    financials_path = bp_dir / "financials.json"
    history_dir = bp_dir / "history"

    # 2. Read businessPlanInput.json
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    try:
        plan_input = json.loads(input_path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in businessPlanInput.json: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Read current financials.json
    old_financials = {}
    if financials_path.exists():
        try:
            old_financials = json.loads(financials_path.read_text())
        except json.JSONDecodeError:
            pass  # Non-fatal, just no diff summary

    # 4. Save current financials to history
    history_dir.mkdir(exist_ok=True)
    if financials_path.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        history_file = history_dir / f"financials_{ts}.json"
        history_file.write_text(financials_path.read_text())

    # 5. Apply field change(s)
    try:
        if args.field:
            value = _coerce_value(args.value)
            _set_nested(plan_input, args.field, value)
        else:
            patch = json.loads(args.patch)
            for dot_path, value in patch.items():
                _set_nested(plan_input, dot_path, value)
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error applying changes: {e}", file=sys.stderr)
        sys.exit(1)

    # 6. Write updated businessPlanInput.json
    input_path.write_text(json.dumps(plan_input, indent=2, ensure_ascii=False))

    # 7. Run financial_model.py with updated input as stdin
    financial_model = Path(__file__).parent / "financial_model.py"
    if not financial_model.exists():
        print(f"Error: financial_model.py not found at {financial_model}", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(
            [sys.executable, str(financial_model)],
            input=json.dumps(plan_input),
            capture_output=True,
            text=True,
        )
    except Exception as e:
        print(f"Error running financial_model.py: {e}", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0:
        print(f"Error: financial_model.py failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    # 8. Write output to financials.json
    financials_path.write_text(result.stdout)

    # 9. Print summary diff
    try:
        new_financials = json.loads(result.stdout)
        print(_diff_summary(old_financials, new_financials))
    except json.JSONDecodeError:
        print("Financials updated.")

    sys.exit(0)


if __name__ == "__main__":
    main()
