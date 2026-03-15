#!/usr/bin/env python3
"""Deterministic financial model: reads BusinessPlanInput JSON from stdin,
writes financials.json to stdout."""

import json
import sys
from datetime import datetime, timezone

R = lambda v: round(v, 2)  # noqa: E731


def main():
    data = json.load(sys.stdin)
    fa = data["financialAssumptions"]
    pp = data["planProfile"]
    ue = data.get("unitEconomics") or {}
    bm = data.get("businessModel", {})

    horizon = pp["timeHorizonYears"]
    funding_type = pp["fundingType"]
    funding_amount = pp["fundingAmountEUR"]

    base_rev = fa["baseYearRevenue"]
    growth = fa["expectedAnnualGrowth"]
    gm = fa["grossMarginPct"]
    rd_pct = fa["rdPctRevenue"]
    sm_pct = fa["smPctRevenue"]
    ga_pct = fa["gaPctRevenue"]
    capex_yr = fa["capexPerYear"]
    dep_years = fa["depreciationYears"]
    days_recv = fa["daysReceivable"]
    days_pay = fa["daysPayable"]
    days_inv = fa["daysInventory"]
    interest_rate = fa["interestRatePct"]
    use_patent = fa.get("usePatentBox", False)
    use_credits = fa.get("useTaxCredits", False)
    use_sabatini = fa.get("useNuovaSabatini", False)
    rd_spend = fa.get("rdSpendingEUR", 0)

    scenario_params = {
        "pessimistic": {"revenue_growth_factor": 0.6, "cost_factor": 1.1},
        "base": {"revenue_growth_factor": 1.0, "cost_factor": 1.0},
        "optimistic": {"revenue_growth_factor": 1.4, "cost_factor": 0.95},
    }

    # ── Incentives (constant across years) ──────────────────────────────
    patent_box = _calc_patent_box(use_patent, rd_spend)
    credito_rs = _calc_credito_rs(use_credits, rd_spend)
    innov40 = _calc_innovazione_40(use_credits, rd_spend)
    sabatini = _calc_sabatini(use_sabatini, capex_yr)

    annual_pb_credit = patent_box["tax_saving"]
    annual_crs_credit = credito_rs["annual_credit"]
    annual_inn_credit = innov40["annual_credit"]

    # ── Build scenarios ─────────────────────────────────────────────────
    scenarios = {}
    for sc_name, sp in scenario_params.items():
        gf = sp["revenue_growth_factor"]
        cf = sp["cost_factor"]

        pl_rows = []
        cf_rows = []
        bs_rows = []
        cum_capex = 0.0
        cum_dep = 0.0
        cum_net_income = 0.0
        prev_recv = 0.0
        prev_pay = 0.0
        prev_inv = 0.0
        prev_closing = 10000.0  # seed capital

        initial_debt = funding_amount if funding_type == "debt" else 0.0
        outstanding_debt = initial_debt
        initial_equity = funding_amount if funding_type == "equity" else 10000.0

        cum_repayments = 0.0

        for yr in range(1, horizon + 1):
            # ── Revenue ──
            if yr == 1:
                revenue = R(base_rev)
            else:
                revenue = R(pl_rows[-1]["revenue_total"] * (1 + growth * gf))

            # ── P&L ──
            cogs = R(revenue * (1 - gm))
            gross_profit = R(revenue - cogs)
            gross_margin_pct = R(gm * 100)

            rd_val = R(revenue * rd_pct * cf)
            sm_val = R(revenue * sm_pct * cf)
            ga_val = R(revenue * ga_pct * cf)
            total_opex = R(rd_val + sm_val + ga_val)

            ebitda = R(gross_profit - total_opex)

            cum_capex += capex_yr
            depreciation = R(cum_capex / dep_years)
            cum_dep += depreciation

            ebit = R(ebitda - depreciation)

            interest_expense = R(outstanding_debt * interest_rate)
            ebt = R(ebit - interest_expense)

            ires = R(max(0, ebt * 0.24))
            irap = R(max(0, ebt * 0.039))

            tc_pb = R(annual_pb_credit)
            tc_crs = R(annual_crs_credit)
            tc_inn = R(annual_inn_credit)

            net_income = R(ebt - ires - irap + tc_pb + tc_crs + tc_inn)
            cum_net_income += net_income

            pl_rows.append({
                "year": yr,
                "revenue_total": revenue,
                "cogs": cogs,
                "gross_profit": gross_profit,
                "gross_margin_pct": gross_margin_pct,
                "rd": rd_val,
                "sales_marketing": sm_val,
                "general_admin": ga_val,
                "total_opex": total_opex,
                "ebitda": ebitda,
                "depreciation": depreciation,
                "ebit": ebit,
                "interest_expense": interest_expense,
                "ebt": ebt,
                "ires": ires,
                "irap": irap,
                "tax_credits": {
                    "patent_box": tc_pb,
                    "credito_rs": tc_crs,
                    "innovazione_40": tc_inn,
                },
                "net_income": net_income,
            })

            # ── Cash Flow ──
            recv = R(revenue * days_recv / 365)
            pay = R(cogs * days_pay / 365)
            inv = R(cogs * days_inv / 365)

            delta_recv = R(-(recv - prev_recv))
            delta_pay = R(pay - prev_pay)
            delta_inv = R(-(inv - prev_inv))

            cfo = R(net_income + depreciation + delta_recv + delta_inv + delta_pay)
            capex_cf = R(-capex_yr)
            fcf = R(cfo + capex_cf)

            financing = R(funding_amount) if yr == 1 and funding_type in ("debt", "equity", "grant", "mixed") else 0.0

            if funding_type == "debt" and yr >= 2 and outstanding_debt > 0:
                repayment = R(-initial_debt / horizon)
                outstanding_debt = R(outstanding_debt + repayment)  # repayment is negative
                cum_repayments += abs(repayment)
            else:
                repayment = 0.0

            net_cash_change = R(fcf + financing + repayment)
            opening_cash = R(prev_closing)
            closing_cash = R(opening_cash + net_cash_change)

            cf_rows.append({
                "year": yr,
                "net_income": net_income,
                "depreciation": depreciation,
                "delta_receivables": delta_recv,
                "delta_inventory": delta_inv,
                "delta_payables": delta_pay,
                "cfo": cfo,
                "capex": capex_cf,
                "fcf": fcf,
                "financing_received": financing,
                "debt_repayment": repayment,
                "net_cash_change": net_cash_change,
                "opening_cash": opening_cash,
                "closing_cash": closing_cash,
            })

            prev_recv = recv
            prev_pay = pay
            prev_inv = inv
            prev_closing = closing_cash

            # ── Balance Sheet ──
            fixed_net = R(cum_capex - cum_dep)
            bs_cash = closing_cash
            total_assets = R(fixed_net + recv + inv + bs_cash)

            equity_val = R(initial_equity)
            retained = R(cum_net_income)
            lt_debt = R(initial_debt - cum_repayments)
            total_liab = R(equity_val + retained + lt_debt + pay)

            # Balancing adjustment
            diff = R(total_assets - total_liab)
            if diff != 0:
                retained = R(retained + diff)
                total_liab = R(equity_val + retained + lt_debt + pay)

            bs_rows.append({
                "year": yr,
                "assets": {
                    "fixed_assets_net": fixed_net,
                    "receivables": recv,
                    "inventory": inv,
                    "cash": bs_cash,
                    "total": total_assets,
                },
                "liabilities": {
                    "equity": equity_val,
                    "retained_earnings": retained,
                    "long_term_debt": lt_debt,
                    "payables": pay,
                    "total": total_liab,
                },
            })

        scenarios[sc_name] = {
            "multipliers": sp,
            "pl": pl_rows,
            "cash_flow": cf_rows,
            "balance_sheet": bs_rows,
        }

    # ── Break-even ──────────────────────────────────────────────────────
    breakeven = _calc_breakeven(ue, scenarios.get("base", {}).get("cash_flow", []))

    # ── Unit Economics ──────────────────────────────────────────────────
    unit_econ = _calc_unit_economics(ue)

    # ── Sensitivity ─────────────────────────────────────────────────────
    sensitivity = _calc_sensitivity(
        base_rev, growth, gm, rd_pct, sm_pct, ga_pct,
        capex_yr, dep_years, horizon, bm.get("sector", ""),
    )

    # ── Output ──────────────────────────────────────────────────────────
    output = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_hash": "",
        "time_horizon_years": horizon,
        "scenarios": scenarios,
        "breakeven": breakeven,
        "unit_economics": unit_econ,
        "sensitivity": sensitivity,
        "incentives": {
            "patent_box": patent_box,
            "credito_rs": credito_rs,
            "innovazione_40": innov40,
            "nuova_sabatini": sabatini,
        },
    }
    json.dump(output, sys.stdout, indent=2)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _calc_patent_box(active: bool, rd_spend: float) -> dict:
    if active and rd_spend > 0:
        sup = R(rd_spend * 1.10)
        sav = R(sup * 0.279)
        return {"active": True, "eligible_spend": R(rd_spend), "super_deduction": sup, "tax_saving": sav}
    return {"active": False, "eligible_spend": 0.0, "super_deduction": 0.0, "tax_saving": 0.0}


def _calc_credito_rs(active: bool, rd_spend: float) -> dict:
    if active and rd_spend > 0:
        credit = R(min(rd_spend * 0.20, 4_000_000))
        return {"active": True, "eligible_spend": R(rd_spend), "rate": 0.20, "annual_credit": credit}
    return {"active": False, "eligible_spend": 0.0, "rate": 0.20, "annual_credit": 0.0}


def _calc_innovazione_40(active: bool, rd_spend: float) -> dict:
    if active and rd_spend > 0:
        credit = R(rd_spend * 0.15)
        return {"active": True, "eligible_spend": R(rd_spend), "rate": 0.15, "annual_credit": credit}
    return {"active": False, "eligible_spend": 0.0, "rate": 0.15, "annual_credit": 0.0}


def _calc_sabatini(active: bool, capex: float) -> dict:
    if active and capex > 0:
        subsidy = R(capex * 0.0275 * 5)
        return {"active": True, "eligible_capex": R(capex), "interest_subsidy": subsidy}
    return {"active": False, "eligible_capex": 0.0, "interest_subsidy": 0.0}


def _calc_breakeven(ue: dict, base_cf: list) -> dict:
    up = ue.get("unitPrice", 0)
    uvc = ue.get("unitVariableCost", 0)
    fc = ue.get("fixedCostsAnnual", 0)

    if not ue or up <= uvc:
        return {"units": 0, "revenue": 0, "months_to_breakeven": None,
                "fixed_costs_annual": fc, "contribution_margin_per_unit": 0}

    cm = R(up - uvc)
    units = R(fc / cm)
    rev_be = R(units * up)

    # Estimate months to break-even from cumulative FCF
    months = None
    cum_fcf = 0.0
    for row in base_cf:
        cum_fcf += row["fcf"]
        if cum_fcf > 0:
            # Interpolate within the year
            prev = cum_fcf - row["fcf"]
            if row["fcf"] > 0:
                frac = (-prev) / row["fcf"]
                months = round((row["year"] - 1 + frac) * 12, 1)
            else:
                months = round(row["year"] * 12, 1)
            break

    return {
        "units": units,
        "revenue": rev_be,
        "months_to_breakeven": months,
        "fixed_costs_annual": R(fc),
        "contribution_margin_per_unit": cm,
    }


def _calc_unit_economics(ue: dict) -> dict:
    if not ue:
        return {"ltv": 0, "cac": 0, "ltv_cac_ratio": None, "payback_months": None, "gross_margin_per_unit": 0}

    up = ue.get("unitPrice", 0)
    uvc = ue.get("unitVariableCost", 0)
    cac = ue.get("cac", 0)
    lifetime = ue.get("avgCustomerLifetimeMonths", 0)

    margin = R(up - uvc)
    ltv = R(margin * lifetime)
    ratio = round(ltv / cac, 1) if cac > 0 else None
    payback = round(cac / margin, 1) if margin > 0 else None

    return {
        "ltv": ltv,
        "cac": R(cac),
        "ltv_cac_ratio": ratio,
        "payback_months": payback,
        "gross_margin_per_unit": margin,
    }


def _calc_sensitivity(base_rev, growth, gm, rd_pct, sm_pct, ga_pct,
                       capex_yr, dep_years, horizon, sector):
    variations = [-0.20, -0.10, 0.0, 0.10, 0.20]
    matrix = []
    for dg in variations:
        row = []
        for dm in variations:
            adj_growth = growth + dg
            adj_gm = gm + dm
            # Compute last-year EBITDA for base scenario with adjusted params
            rev = base_rev
            cum_capex = 0.0
            for yr in range(1, horizon + 1):
                if yr > 1:
                    rev = rev * (1 + adj_growth)
                cogs = rev * (1 - adj_gm)
                gp = rev - cogs
                opex = rev * (rd_pct + sm_pct + ga_pct)
                ebitda = gp - opex
            row.append(R(ebitda))
        matrix.append(row)

    is_saas = "saas" in sector.lower() if sector else False

    return {
        "dimensions": ["revenue_growth", "gross_margin"],
        "variations": variations,
        "metric": f"ebitda_year_{horizon}",
        "matrix": matrix,
        "additional_saas_churn_sensitivity": None,  # placeholder for SaaS
    }


if __name__ == "__main__":
    main()
