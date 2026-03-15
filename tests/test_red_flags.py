"""Tests for red_flags.py QA Level 1 detection."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "scripts"
FIXTURES = Path(__file__).parent / "fixtures"


def run_red_flags(financials_path, input_path, plan_md="", competitors_count=3):
    payload = {
        "financials": json.loads(Path(financials_path).read_text()) if financials_path else {},
        "input": json.loads(Path(input_path).read_text()),
        "plan_text": plan_md,
        "competitors_count": competitors_count,
    }
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "red_flags.py")],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return json.loads(result.stdout)


class TestRedFlagDetection:
    def test_clean_input_no_critical_flags(self):
        output = run_red_flags(
            str(FIXTURES / "sample_financials.json"),
            str(FIXTURES / "valid_input_saas.json"),
            plan_md="## Risk Analysis\n### Risks\n1. Market risk...",
            competitors_count=5,
        )
        critical = [f for f in output["flags"] if f["severity"] == "CRITICAL"]
        assert len(critical) == 0

    def test_no_competitors_flagged_critical(self):
        output = run_red_flags(
            str(FIXTURES / "sample_financials.json"),
            str(FIXTURES / "valid_input_saas.json"),
            competitors_count=0,
        )
        ids = [f["id"] for f in output["flags"]]
        assert "no_competitors" in ids
        flag = next(f for f in output["flags"] if f["id"] == "no_competitors")
        assert flag["severity"] == "CRITICAL"

    def test_missing_team_background_flagged(self):
        data = json.loads((FIXTURES / "valid_input_saas.json").read_text())
        for f in data["team"]["founders"]:
            del f["background"]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(data, tmp)
            tmp.flush()
            output = run_red_flags(str(FIXTURES / "sample_financials.json"), tmp.name, competitors_count=3)
        ids = [f["id"] for f in output["flags"]]
        assert "missing_team" in ids

    def test_no_risk_section_flagged(self):
        output = run_red_flags(
            str(FIXTURES / "sample_financials.json"),
            str(FIXTURES / "valid_input_saas.json"),
            plan_md="## Executive Summary\nSome content without risk section",
            competitors_count=3,
        )
        ids = [f["id"] for f in output["flags"]]
        assert "no_risk_section" in ids

    def test_output_structure(self):
        output = run_red_flags(
            str(FIXTURES / "sample_financials.json"),
            str(FIXTURES / "valid_input_saas.json"),
            competitors_count=3,
        )
        assert "level" in output and output["level"] == 1
        assert "flags_found" in output
        assert "flags" in output
        assert "pass" in output

    def test_esa_bic_without_space_flagged(self):
        data = json.loads((FIXTURES / "valid_input_saas.json").read_text())
        data["planProfile"]["targetProgram"] = "esa_bic"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(data, tmp)
            tmp.flush()
            output = run_red_flags(
                str(FIXTURES / "sample_financials.json"), tmp.name,
                plan_md="## Product\nOur SaaS product does document automation.",
                competitors_count=3,
            )
        ids = [f["id"] for f in output["flags"]]
        assert "esa_no_space" in ids

    def test_pass_true_when_no_critical(self):
        output = run_red_flags(
            str(FIXTURES / "sample_financials.json"),
            str(FIXTURES / "valid_input_saas.json"),
            plan_md="## Risk Analysis\n### Risks\n1. Market risk...",
            competitors_count=5,
        )
        assert output["pass"] is True

    def test_pass_false_when_critical(self):
        output = run_red_flags(
            str(FIXTURES / "sample_financials.json"),
            str(FIXTURES / "valid_input_saas.json"),
            competitors_count=0,
        )
        assert output["pass"] is False

    def test_flags_found_count_matches(self):
        output = run_red_flags(
            str(FIXTURES / "sample_financials.json"),
            str(FIXTURES / "valid_input_saas.json"),
            competitors_count=0,
        )
        assert output["flags_found"] == len(output["flags"])

    def test_tam_top_down_only_flagged(self):
        data = json.loads((FIXTURES / "valid_input_saas.json").read_text())
        data["market"]["tamMethodology"] = "top_down"
        data["market"]["somEstimate"] = 0
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(data, tmp)
            tmp.flush()
            output = run_red_flags(
                str(FIXTURES / "sample_financials.json"), tmp.name,
                plan_md="## Risk Analysis\nRisk section here",
                competitors_count=3,
            )
        ids = [f["id"] for f in output["flags"]]
        assert "tam_top_down_only" in ids

    def test_horizon_europe_missing_sections(self):
        data = json.loads((FIXTURES / "valid_input_saas.json").read_text())
        data["planProfile"]["targetProgram"] = "horizon_europe"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(data, tmp)
            tmp.flush()
            output = run_red_flags(
                str(FIXTURES / "sample_financials.json"), tmp.name,
                plan_md="## Risk Analysis\nSome content without required headings",
                competitors_count=3,
            )
        ids = [f["id"] for f in output["flags"]]
        assert "horizon_wrong_structure" in ids

    def test_smartstart_no_tech_flagged(self):
        data = json.loads((FIXTURES / "valid_input_saas.json").read_text())
        data["planProfile"]["targetProgram"] = "smartstart"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(data, tmp)
            tmp.flush()
            output = run_red_flags(
                str(FIXTURES / "sample_financials.json"), tmp.name,
                plan_md="## Business Plan\nWe sell consulting services to businesses.",
                competitors_count=3,
            )
        ids = [f["id"] for f in output["flags"]]
        assert "smartstart_no_tech" in ids

    def test_flag_has_required_fields(self):
        output = run_red_flags(
            str(FIXTURES / "sample_financials.json"),
            str(FIXTURES / "valid_input_saas.json"),
            competitors_count=0,
        )
        flag = next(f for f in output["flags"] if f["id"] == "no_competitors")
        assert "id" in flag
        assert "severity" in flag
        assert "message" in flag
        assert "suggestion" in flag
        assert "section" in flag
