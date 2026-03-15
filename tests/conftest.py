"""Shared fixtures and helpers for all test files."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def saas_input():
    return json.loads((FIXTURES / "valid_input_saas.json").read_text())


@pytest.fixture
def bank_input():
    return json.loads((FIXTURES / "valid_input_bank.json").read_text())


@pytest.fixture
def horizon_input():
    return json.loads((FIXTURES / "valid_input_horizon.json").read_text())


@pytest.fixture
def zero_revenue_input():
    return json.loads((FIXTURES / "edge_case_zero_revenue.json").read_text())


@pytest.fixture
def sample_financials():
    path = FIXTURES / "sample_financials.json"
    if not path.exists():
        pytest.skip("sample_financials.json not yet generated - run Task 3 Step 5 first")
    return json.loads(path.read_text())


def run_script(script_name: str, *args, stdin_data: str = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script_name), *args],
        input=stdin_data,
        capture_output=True,
        text=True,
    )
