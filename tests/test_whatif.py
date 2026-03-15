"""Tests for whatif.py scenario recalculation."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "scripts"
FIXTURES = Path(__file__).parent / "fixtures"


def setup_whatif_dir(tmp):
    bp_dir = Path(tmp) / ".business-plan"
    bp_dir.mkdir()
    (bp_dir / "history").mkdir()
    shutil.copy(FIXTURES / "valid_input_saas.json", bp_dir / "businessPlanInput.json")
    shutil.copy(FIXTURES / "sample_financials.json", bp_dir / "financials.json")
    return bp_dir


def run_whatif(work_dir, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "whatif.py"), *args],
        capture_output=True, text=True, cwd=work_dir,
    )


class TestWhatifSingleField:
    def test_change_growth_rate(self):
        with tempfile.TemporaryDirectory() as tmp:
            bp_dir = setup_whatif_dir(tmp)
            result = run_whatif(tmp, "--field", "financialAssumptions.expectedAnnualGrowth", "--value", "0.5")
            assert result.returncode == 0, f"Failed: {result.stderr}"
            updated = json.loads((bp_dir / "businessPlanInput.json").read_text())
            assert updated["financialAssumptions"]["expectedAnnualGrowth"] == 0.5

    def test_history_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            bp_dir = setup_whatif_dir(tmp)
            run_whatif(tmp, "--field", "financialAssumptions.expectedAnnualGrowth", "--value", "0.5")
            history_files = list((bp_dir / "history").glob("financials_*.json"))
            assert len(history_files) == 1

    def test_financials_regenerated(self):
        with tempfile.TemporaryDirectory() as tmp:
            bp_dir = setup_whatif_dir(tmp)
            old_financials = json.loads((bp_dir / "financials.json").read_text())
            run_whatif(tmp, "--field", "financialAssumptions.expectedAnnualGrowth", "--value", "0.2")
            new_financials = json.loads((bp_dir / "financials.json").read_text())
            old_y2 = old_financials["scenarios"]["base"]["pl"][1]["revenue_total"]
            new_y2 = new_financials["scenarios"]["base"]["pl"][1]["revenue_total"]
            assert old_y2 != new_y2


class TestWhatifPatch:
    def test_multiple_fields_via_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            bp_dir = setup_whatif_dir(tmp)
            patch = json.dumps({
                "financialAssumptions.expectedAnnualGrowth": 0.2,
                "financialAssumptions.grossMarginPct": 0.65,
            })
            result = run_whatif(tmp, "--patch", patch)
            assert result.returncode == 0, f"Failed: {result.stderr}"
            updated = json.loads((bp_dir / "businessPlanInput.json").read_text())
            assert updated["financialAssumptions"]["expectedAnnualGrowth"] == 0.2
            assert updated["financialAssumptions"]["grossMarginPct"] == 0.65


class TestWhatifErrors:
    def test_no_business_plan_dir_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_whatif(tmp, "--field", "foo", "--value", "1")
            assert result.returncode == 1
