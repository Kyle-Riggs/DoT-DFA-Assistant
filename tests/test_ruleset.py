import copy
from pathlib import Path

import pytest

from dfa_assistant.ruleset import RuleSetError, load_rule_set, validate_rule_set

V1 = Path(__file__).resolve().parent.parent / "rulesets" / "v1.yaml"


@pytest.fixture
def rs():
    return load_rule_set(V1)


def test_v1_loads_and_validates(rs):
    assert rs["rule_set_id"] and rs["version"] == "1"


def test_v1_has_nine_entries_rs01_to_rs09(rs):
    assert [r["rule_id"] for r in rs["rules"]] == [f"RS-{i:02d}" for i in range(1, 10)]


def test_every_rule_cites_a_subsection(rs):
    assert all(r["citation"].startswith("§ 391.51(b)") for r in rs["rules"])


def test_medical_rules_are_disqualifying_and_class_qualified(rs):
    by_id = {r["rule_id"]: r for r in rs["rules"]}
    assert by_id["RS-06"]["applies_to"] == "non_cdl"
    assert by_id["RS-07"]["applies_to"] == "cdl"
    for rid in ("RS-06", "RS-07"):
        assert by_id[rid]["severity_if_missing"] == "disqualifying"
        assert by_id[rid]["severity_if_out_of_date"] == "disqualifying"


def test_selection_is_per_entry_for_shared_motor_vehicle_record(rs):
    by_id = {r["rule_id"]: r for r in rs["rules"]}
    assert by_id["RS-02"]["selection"]["order"] == "earliest"
    assert by_id["RS-04"]["selection"]["order"] == "latest"
    assert by_id["RS-07"]["selection"]["order"] == "latest"


def _mutated(rs, fn):
    data = copy.deepcopy(rs)
    fn(data)
    return data


def test_rejects_missing_required_key(rs):
    with pytest.raises(RuleSetError, match="schema validation failed"):
        validate_rule_set(_mutated(rs, lambda d: d["rules"][0].pop("citation")))


def test_rejects_unknown_severity(rs):
    with pytest.raises(RuleSetError, match="schema validation failed"):
        validate_rule_set(_mutated(rs, lambda d: d["rules"][0].update(severity_if_missing="minor")))


def test_rejects_undeclared_document_type(rs):
    with pytest.raises(RuleSetError, match="undeclared document type"):
        validate_rule_set(_mutated(rs, lambda d: d["rules"][0].update(satisfied_by=["nonexistent"])))


def test_rejects_date_field_not_declared_for_type(rs):
    with pytest.raises(RuleSetError, match="not a declared date field"):
        validate_rule_set(_mutated(rs, lambda d: d["rules"][3]["currency"].update(date_field="review_date")))


def test_rejects_duplicate_rule_id(rs):
    with pytest.raises(RuleSetError, match="duplicate rule_id"):
        validate_rule_set(_mutated(rs, lambda d: d["rules"][1].update(rule_id="RS-01")))


def test_rejects_out_of_date_severity_without_currency_rule(rs):
    with pytest.raises(RuleSetError, match="currency kind is 'none'"):
        validate_rule_set(_mutated(rs, lambda d: d["rules"][0].update(severity_if_out_of_date="recordkeeping")))


def test_rejects_reserved_unclassified_type(rs):
    with pytest.raises(RuleSetError, match="schema validation failed"):
        validate_rule_set(
            _mutated(rs, lambda d: d["document_types"].update(unclassified={"label": "x", "date_fields": []}))
        )
