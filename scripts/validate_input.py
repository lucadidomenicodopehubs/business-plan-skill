#!/usr/bin/env python3
"""Validate a BusinessPlanInput JSON file against the schema."""
import json
import sys
from pathlib import Path

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "business-plan-input.schema.json"


def validate(input_path: str) -> dict:
    """Validate input JSON against schema. Returns {"valid": bool, "errors": [...]}."""
    path = Path(input_path)
    if not path.exists():
        return {"valid": False, "errors": [f"File not found: {input_path}"]}

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON: {e}"]}

    schema = json.loads(SCHEMA_PATH.read_text())

    if HAS_JSONSCHEMA:
        validator = jsonschema.Draft7Validator(schema)
        errors = [
            {"path": "/".join(str(p) for p in e.absolute_path), "message": e.message}
            for e in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
        ]
        return {"valid": len(errors) == 0, "errors": errors}

    # Fallback: manual validation of required fields and schema_version
    errors = []
    required_top = schema.get("required", [])
    for field in required_top:
        if field not in data:
            errors.append({"path": field, "message": f"'{field}' is a required property"})

    if data.get("schema_version") != "1.0":
        errors.append({"path": "schema_version", "message": "schema_version must be '1.0'"})

    if "company" in data:
        for field in ["name", "country", "legalForm"]:
            if field not in data["company"]:
                errors.append({"path": f"company/{field}", "message": f"'company.{field}' is required"})

    if "planProfile" in data:
        for field in ["purpose", "fundingType"]:
            if field not in data["planProfile"]:
                errors.append({"path": f"planProfile/{field}", "message": f"'planProfile.{field}' is required"})

    if "businessModel" in data:
        for field in ["sector", "revenueModel"]:
            if field not in data["businessModel"]:
                errors.append({"path": f"businessModel/{field}", "message": f"'businessModel.{field}' is required"})

    return {"valid": len(errors) == 0, "errors": errors}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"valid": False, "errors": ["Usage: validate_input.py <path>"]}))
        sys.exit(1)

    result = validate(sys.argv[1])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
