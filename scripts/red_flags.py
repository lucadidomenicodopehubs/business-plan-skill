#!/usr/bin/env python3
"""
QA Level 1: Deterministic red-flag detection.
Reads JSON payload from stdin, outputs JSON report to stdout.
Exit code always 0.
"""
import json
import re
import sys


def check_tam_top_down_only(input_data: dict) -> dict | None:
    """Flag if TAM methodology is top-down only and SOM estimate is missing/zero."""
    market = input_data.get("market", {})
    if market.get("tamMethodology") == "top_down":
        som = market.get("somEstimate", 0)
        if not som:
            return {
                "id": "tam_top_down_only",
                "severity": "HIGH",
                "message": "TAM methodology is top-down only with no SOM estimate.",
                "suggestion": "Add a bottom-up SOM estimate to validate market sizing assumptions.",
                "section": "Market Analysis",
            }
    return None


def check_no_competitors(competitors_count: int) -> dict | None:
    """Flag if no competitors were found."""
    if competitors_count == 0:
        return {
            "id": "no_competitors",
            "severity": "CRITICAL",
            "message": "No competitors identified in the competitive analysis.",
            "suggestion": "Research and document at least 3-5 direct or indirect competitors.",
            "section": "Competitive Analysis",
        }
    return None


def check_hockey_stick(financials: dict) -> dict | None:
    """Flag unrealistic hockey-stick revenue growth (>300% YoY)."""
    try:
        pl = financials["scenarios"]["base"]["pl"]
    except (KeyError, TypeError):
        return None

    for i in range(len(pl) - 1):
        prev_rev = pl[i].get("revenue_total", 0)
        next_rev = pl[i + 1].get("revenue_total", 0)
        if prev_rev == 0:
            continue
        ratio = next_rev / prev_rev
        if ratio > 4.0:
            return {
                "id": "hockey_stick",
                "severity": "HIGH",
                "message": f"Revenue growth from year {pl[i]['year']} to year {pl[i+1]['year']} exceeds 300% ({(ratio-1)*100:.0f}%).",
                "suggestion": "Provide detailed justification for exceptional growth projections or revise to more conservative assumptions.",
                "section": "Financial Projections",
            }
    return None


def check_pl_cf_mismatch(financials: dict) -> dict | None:
    """Flag if net_income in P&L vs cash flow differ by more than 1%."""
    try:
        pl = financials["scenarios"]["base"]["pl"]
        cf = financials["scenarios"]["base"]["cash_flow"]
    except (KeyError, TypeError):
        return None

    for i in range(min(len(pl), len(cf))):
        pl_ni = pl[i].get("net_income", 0)
        cf_ni = cf[i].get("net_income", 0)
        # Skip if both are zero
        if pl_ni == 0 and cf_ni == 0:
            continue
        # Calculate difference
        base = abs(pl_ni) if abs(pl_ni) > abs(cf_ni) else abs(cf_ni)
        if base == 0:
            continue
        diff_pct = abs(pl_ni - cf_ni) / base
        if diff_pct > 0.01:
            return {
                "id": "pl_cf_mismatch",
                "severity": "CRITICAL",
                "message": f"Net income mismatch between P&L ({pl_ni}) and Cash Flow ({cf_ni}) for year {pl[i]['year']} ({diff_pct*100:.1f}% difference).",
                "suggestion": "Ensure P&L and Cash Flow statements use the same net income figures for consistency.",
                "section": "Financial Statements",
            }
    return None


def check_negative_cash_no_funding(financials: dict, input_data: dict) -> dict | None:
    """Flag if any closing cash is negative and no funding is planned."""
    funding = input_data.get("planProfile", {}).get("fundingAmountEUR", 0) or 0
    if funding > 0:
        return None

    try:
        cf = financials["scenarios"]["base"]["cash_flow"]
    except (KeyError, TypeError):
        return None

    for entry in cf:
        closing = entry.get("closing_cash", 0)
        if closing is not None and closing < 0:
            return {
                "id": "negative_cash_no_funding",
                "severity": "CRITICAL",
                "message": f"Closing cash goes negative (€{closing:,.0f}) in year {entry['year']} with no funding planned.",
                "suggestion": "Either secure funding or revise the financial model to avoid negative cash positions.",
                "section": "Cash Flow",
            }
    return None


def check_impossible_unit_economics(financials: dict) -> dict | None:
    """Flag poor unit economics: LTV/CAC < 1 or payback > 60 months."""
    ue = financials.get("unit_economics", {})
    if not ue:
        return None

    ltv_cac = ue.get("ltv_cac_ratio")
    payback = ue.get("payback_months")

    if ltv_cac and ltv_cac > 0 and ltv_cac < 1:
        return {
            "id": "impossible_unit_economics",
            "severity": "HIGH",
            "message": f"LTV/CAC ratio is {ltv_cac:.2f}, which is below 1.0 — acquiring customers costs more than their lifetime value.",
            "suggestion": "Improve customer retention, increase pricing, or reduce customer acquisition costs.",
            "section": "Unit Economics",
        }

    if payback and payback > 0 and payback > 60:
        return {
            "id": "impossible_unit_economics",
            "severity": "HIGH",
            "message": f"Customer acquisition payback period is {payback:.0f} months (over 5 years).",
            "suggestion": "Reduce CAC or improve gross margin to achieve a payback period under 24 months.",
            "section": "Unit Economics",
        }

    return None


def check_no_risk_section(plan_text: str) -> dict | None:
    """Flag if the business plan has no risk section."""
    if not re.search(r"^#{1,3}.*risk", plan_text, re.IGNORECASE | re.MULTILINE):
        return {
            "id": "no_risk_section",
            "severity": "MEDIUM",
            "message": "The business plan does not contain a dedicated risk analysis section.",
            "suggestion": "Add a risk section covering market, operational, financial, and regulatory risks.",
            "section": "Risk Analysis",
        }
    return None


def check_missing_team(input_data: dict) -> dict | None:
    """Flag if any founder lacks a background field."""
    founders = input_data.get("team", {}).get("founders", [])
    for founder in founders:
        bg = founder.get("background", "")
        if not bg:
            return {
                "id": "missing_team",
                "severity": "HIGH",
                "message": f"Founder '{founder.get('name', 'Unknown')}' is missing a background description.",
                "suggestion": "Add professional background, relevant experience, and key achievements for each founder.",
                "section": "Team",
            }
    return None


def check_smartstart_no_tech(input_data: dict, plan_text: str) -> dict | None:
    """Flag SmartStart applications without technology-related content."""
    program = input_data.get("planProfile", {}).get("targetProgram", "")
    if program != "smartstart":
        return None

    tech_terms = ["tecnolog", "innov", "R&D", "brevett", "software", "AI", "machine learning", "patent"]
    plan_lower = plan_text.lower()
    has_tech = any(term.lower() in plan_lower for term in tech_terms)

    if not has_tech:
        return {
            "id": "smartstart_no_tech",
            "severity": "CRITICAL",
            "message": "SmartStart application does not mention any technology or innovation-related terms.",
            "suggestion": "Include explicit references to technology, innovation, R&D, software, AI, or patents in the business plan.",
            "section": "Technology & Innovation",
        }
    return None


def check_esa_no_space(input_data: dict, plan_text: str) -> dict | None:
    """Flag ESA BIC applications without space-related content."""
    program = input_data.get("planProfile", {}).get("targetProgram", "")
    if program != "esa_bic":
        return None

    space_terms = ["space", "satellite", "ESA", "orbit", "earth observation", "navigation"]
    plan_lower = plan_text.lower()
    has_space = any(term.lower() in plan_lower for term in space_terms)

    if not has_space:
        return {
            "id": "esa_no_space",
            "severity": "CRITICAL",
            "message": "ESA BIC application does not mention space-related terms.",
            "suggestion": "Include explicit references to space technology, satellites, orbit, Earth observation, or navigation.",
            "section": "Technology & Space Application",
        }
    return None


def check_horizon_wrong_structure(input_data: dict, plan_text: str) -> dict | None:
    """Flag Horizon Europe applications missing required structural sections."""
    program = input_data.get("planProfile", {}).get("targetProgram", "")
    if program != "horizon_europe":
        return None

    required_headings = ["Excellence", "Impact", "Implementation"]
    missing = [h for h in required_headings if h.lower() not in plan_text.lower()]

    if missing:
        return {
            "id": "horizon_wrong_structure",
            "severity": "CRITICAL",
            "message": f"Horizon Europe application is missing required sections: {', '.join(missing)}.",
            "suggestion": "Structure the business plan with all three required Horizon Europe sections: Excellence, Impact, and Implementation.",
            "section": "Structure",
        }
    return None


def run_checks(payload: dict) -> dict:
    financials = payload.get("financials", {})
    input_data = payload.get("input", {})
    plan_text = payload.get("plan_text", "")
    competitors_count = payload.get("competitors_count", 0)

    flags = []

    checks = [
        check_tam_top_down_only(input_data),
        check_no_competitors(competitors_count),
        check_hockey_stick(financials),
        check_pl_cf_mismatch(financials),
        check_negative_cash_no_funding(financials, input_data),
        check_impossible_unit_economics(financials),
        check_no_risk_section(plan_text),
        check_missing_team(input_data),
        check_smartstart_no_tech(input_data, plan_text),
        check_esa_no_space(input_data, plan_text),
        check_horizon_wrong_structure(input_data, plan_text),
    ]

    for result in checks:
        if result is not None:
            flags.append(result)

    has_critical = any(f["severity"] == "CRITICAL" for f in flags)

    return {
        "level": 1,
        "flags_found": len(flags),
        "flags": flags,
        "pass": not has_critical,
    }


def main():
    try:
        payload = json.loads(sys.stdin.read())
        report = run_checks(payload)
        print(json.dumps(report, indent=2))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"error": str(e), "level": 1, "flags_found": 0, "flags": [], "pass": False}))
        sys.exit(0)


if __name__ == "__main__":
    main()
