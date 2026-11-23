"""Load and validate a versioned rule set.

A rule set is data, not program logic (FR-05): the required contents of the
driver qualification file are read from a YAML file, validated against a JSON
schema, and checked for internal consistency before any evaluation uses them.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


class RuleSetError(ValueError):
    """Raised when a rule set fails schema or consistency validation."""


def _schema() -> dict[str, Any]:
    text = resources.files("dfa_assistant").joinpath("schemas/ruleset.schema.json").read_text(encoding="utf-8")
    return json.loads(text)


def validate_rule_set(data: Any) -> dict[str, Any]:
    """Validate parsed rule-set data; return it unchanged or raise RuleSetError."""
    errors = sorted(Draft202012Validator(_schema()).iter_errors(data), key=lambda e: list(e.path))
    if errors:
        details = "; ".join(f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors)
        raise RuleSetError(f"schema validation failed: {details}")
    _check_consistency(data)
    return data


def _check_consistency(data: dict[str, Any]) -> None:
    types: dict[str, dict[str, Any]] = data["document_types"]
    problems: list[str] = []

    ids = [r["rule_id"] for r in data["rules"]]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"duplicate rule_id {dup}")

    for rule in data["rules"]:
        rid = rule["rule_id"]
        unknown = [t for t in rule["satisfied_by"] if t not in types]
        for t in unknown:
            problems.append(f"{rid}: satisfied_by names undeclared document type '{t}'")

        # Every date field a rule relies on must be declared for every type that satisfies it.
        used: list[tuple[str, str]] = []
        if rule["selection"]:
            used.append(("selection.by", rule["selection"]["by"]))
        currency = rule["currency"]
        if currency["kind"] != "none":
            used.append(("currency.date_field", currency["date_field"]))
        for where, field in used:
            for t in rule["satisfied_by"]:
                if t in types and field not in types[t]["date_fields"]:
                    problems.append(f"{rid}: {where} '{field}' is not a declared date field of '{t}'")

        # An out-of-date outcome exists only where there is a currency rule.
        if currency["kind"] == "none" and rule["severity_if_out_of_date"] is not None:
            problems.append(f"{rid}: severity_if_out_of_date set but currency kind is 'none'")
        if currency["kind"] != "none" and rule["severity_if_out_of_date"] is None:
            problems.append(f"{rid}: currency rule present but severity_if_out_of_date is null")

    if problems:
        raise RuleSetError("consistency check failed: " + "; ".join(problems))


def load_rule_set(path: str | Path) -> dict[str, Any]:
    """Read a rule-set YAML file and return it validated."""
    with open(path, encoding="utf-8") as fh:
        return validate_rule_set(yaml.safe_load(fh))
