"""Tests for validate_input.py"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "scripts"
FIXTURES = Path(__file__).parent / "fixtures"


def run_validate(input_path: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "validate_input.py"), input_path],
        capture_output=True,
        text=True,
    )


def test_valid_saas_input_passes():
    result = run_validate(str(FIXTURES / "valid_input_saas.json"))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["valid"] is True
    assert output["errors"] == []


def test_valid_bank_input_passes():
    result = run_validate(str(FIXTURES / "valid_input_bank.json"))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["valid"] is True


def test_valid_horizon_input_passes():
    result = run_validate(str(FIXTURES / "valid_input_horizon.json"))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["valid"] is True


def test_missing_required_fields_fails():
    result = run_validate(str(FIXTURES / "invalid_input_missing.json"))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["valid"] is False
    assert len(output["errors"]) > 0


def test_nonexistent_file_fails():
    result = run_validate("/tmp/nonexistent_file.json")
    assert result.returncode == 1


def test_invalid_json_fails():
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not valid json {{{")
        f.flush()
        result = run_validate(f.name)
    assert result.returncode == 1


def test_wrong_schema_version_fails():
    import tempfile
    data = json.loads((FIXTURES / "valid_input_saas.json").read_text())
    data["schema_version"] = "99.0"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        result = run_validate(f.name)
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["valid"] is False
