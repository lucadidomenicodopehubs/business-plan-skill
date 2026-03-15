"""Tests for financial_model.py — TDD approach."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
FIXTURES = TESTS / "fixtures"
SCRIPTS = TESTS.parent / "scripts"

FIXTURE_SAAS = str(FIXTURES / "valid_input_saas.json")


def run_model(input_path: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "financial_model.py")],
        input=Path(input_path).read_text(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def output():
    return run_model(FIXTURE_SAAS)


# ── P&L ──────────────────────────────────────────────────────────────────────


class TestPLGeneration:
    def test_generates_three_scenarios(self, output):
        assert set(output["scenarios"].keys()) == {"pessimistic", "base", "optimistic"}

    def test_each_scenario_has_correct_years(self, output):
        for name, sc in output["scenarios"].items():
            years = [row["year"] for row in sc["pl"]]
            assert years == [1, 2, 3], f"{name} years wrong: {years}"

    def test_pl_has_required_fields(self, output):
        required = {
            "year", "revenue_total", "cogs", "gross_profit",
            "gross_margin_pct", "rd", "sales_marketing", "general_admin",
            "total_opex", "ebitda", "depreciation", "ebit",
            "interest_expense", "ebt", "ires", "irap", "tax_credits",
            "net_income",
        }
        for sc in output["scenarios"].values():
            for row in sc["pl"]:
                assert required.issubset(row.keys()), f"Missing fields: {required - set(row.keys())}"

    def test_base_year1_revenue_matches_input(self, output):
        assert output["scenarios"]["base"]["pl"][0]["revenue_total"] == 120000.0

    def test_pessimistic_revenue_lower_than_base(self, output):
        pess_rev = [r["revenue_total"] for r in output["scenarios"]["pessimistic"]["pl"]]
        base_rev = [r["revenue_total"] for r in output["scenarios"]["base"]["pl"]]
        # Year 1 is the same; year 2+ pessimistic should be lower
        for yr in range(1, len(pess_rev)):
            assert pess_rev[yr] < base_rev[yr], f"Year {yr+1}: pess {pess_rev[yr]} not < base {base_rev[yr]}"

    def test_gross_margin_calculation(self, output):
        for sc in output["scenarios"].values():
            for row in sc["pl"]:
                expected_gp = round(row["revenue_total"] * 0.78, 2)
                assert row["gross_profit"] == expected_gp, (
                    f"Year {row['year']}: gross_profit {row['gross_profit']} != {expected_gp}"
                )

    def test_ebitda_is_gross_profit_minus_opex(self, output):
        for sc in output["scenarios"].values():
            for row in sc["pl"]:
                expected = round(row["gross_profit"] - row["total_opex"], 2)
                assert row["ebitda"] == expected

    def test_net_income_after_taxes(self, output):
        for sc in output["scenarios"].values():
            for row in sc["pl"]:
                credits = row["tax_credits"]
                total_credits = credits["patent_box"] + credits["credito_rs"] + credits["innovazione_40"]
                expected = round(row["ebt"] - row["ires"] - row["irap"] + total_credits, 2)
                assert row["net_income"] == expected, (
                    f"Year {row['year']}: net_income {row['net_income']} != {expected}"
                )


# ── Cash Flow ────────────────────────────────────────────────────────────────


class TestCashFlow:
    def test_cash_flow_present_for_all_scenarios(self, output):
        for name, sc in output["scenarios"].items():
            assert "cash_flow" in sc, f"{name} missing cash_flow"
            assert len(sc["cash_flow"]) == 3

    def test_cash_flow_has_required_fields(self, output):
        required = {
            "year", "net_income", "depreciation",
            "delta_receivables", "delta_inventory", "delta_payables",
            "cfo", "capex", "fcf",
            "financing_received", "debt_repayment",
            "net_cash_change", "opening_cash", "closing_cash",
        }
        for sc in output["scenarios"].values():
            for row in sc["cash_flow"]:
                assert required.issubset(row.keys()), f"Missing: {required - set(row.keys())}"

    def test_closing_cash_equals_opening_plus_change(self, output):
        for sc in output["scenarios"].values():
            for row in sc["cash_flow"]:
                expected = round(row["opening_cash"] + row["net_cash_change"], 2)
                assert row["closing_cash"] == expected, (
                    f"Year {row['year']}: closing {row['closing_cash']} != {expected}"
                )


# ── Balance Sheet ────────────────────────────────────────────────────────────


class TestBalanceSheet:
    def test_balance_sheet_present(self, output):
        for name, sc in output["scenarios"].items():
            assert "balance_sheet" in sc
            assert len(sc["balance_sheet"]) == 3

    def test_assets_equal_liabilities(self, output):
        for name, sc in output["scenarios"].items():
            for row in sc["balance_sheet"]:
                assert row["assets"]["total"] == row["liabilities"]["total"], (
                    f"{name} year {row['year']}: assets {row['assets']['total']} != liabilities {row['liabilities']['total']}"
                )


# ── Break-even ───────────────────────────────────────────────────────────────


class TestBreakeven:
    def test_breakeven_present(self, output):
        assert "breakeven" in output
        required = {"units", "revenue", "months_to_breakeven", "fixed_costs_annual", "contribution_margin_per_unit"}
        assert required.issubset(output["breakeven"].keys())

    def test_breakeven_units_positive(self, output):
        be = output["breakeven"]
        assert be["units"] > 0
        assert be["revenue"] > 0
        assert be["contribution_margin_per_unit"] > 0


# ── Unit Economics ───────────────────────────────────────────────────────────


class TestUnitEconomics:
    def test_unit_economics_present(self, output):
        assert "unit_economics" in output
        required = {"ltv", "cac", "ltv_cac_ratio", "payback_months", "gross_margin_per_unit"}
        assert required.issubset(output["unit_economics"].keys())

    def test_ltv_cac_ratio_calculation(self, output):
        ue = output["unit_economics"]
        # LTV = (unitPrice - unitVariableCost) * avgCustomerLifetimeMonths = (1600 - 352) * 36 = 44928
        assert ue["ltv"] == 44928.0
        assert ue["cac"] == 1200.0
        expected_ratio = round(44928.0 / 1200.0, 1)
        assert ue["ltv_cac_ratio"] == expected_ratio


# ── Sensitivity ──────────────────────────────────────────────────────────────


class TestSensitivity:
    def test_sensitivity_matrix_present(self, output):
        s = output["sensitivity"]
        assert s["dimensions"] == ["revenue_growth", "gross_margin"]
        assert s["variations"] == [-0.20, -0.10, 0.0, 0.10, 0.20]
        assert len(s["matrix"]) == 5
        assert all(len(row) == 5 for row in s["matrix"])

    def test_sensitivity_center_matches_base_ebitda(self, output):
        base_last_ebitda = output["scenarios"]["base"]["pl"][-1]["ebitda"]
        center = output["sensitivity"]["matrix"][2][2]
        assert center == base_last_ebitda


# ── Incentives ───────────────────────────────────────────────────────────────


class TestIncentives:
    def test_patent_box_calculated_when_active(self, output):
        pb = output["incentives"]["patent_box"]
        assert pb["active"] is True
        assert pb["eligible_spend"] == 42000.0
        # super_deduction = 42000 * 1.10 = 46200
        assert pb["super_deduction"] == 46200.0
        # tax_saving = 46200 * 0.279 = 12889.80
        assert pb["tax_saving"] == 12889.8

    def test_credito_rs_calculated_when_active(self, output):
        cr = output["incentives"]["credito_rs"]
        assert cr["active"] is True
        assert cr["eligible_spend"] == 42000.0
        assert cr["rate"] == 0.20
        # annual_credit = min(42000 * 0.20, 4_000_000) = 8400
        assert cr["annual_credit"] == 8400.0


# ── Schema Version ───────────────────────────────────────────────────────────


class TestSchemaVersion:
    def test_output_has_schema_version(self, output):
        assert output["schema_version"] == "1.0"

    def test_output_has_generated_at(self, output):
        assert "generated_at" in output
        assert len(output["generated_at"]) > 0
