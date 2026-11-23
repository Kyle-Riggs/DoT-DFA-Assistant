"""Consistency checks on the ground-truth fixture manifest (evidence E-01).

These tests do not evaluate anything. They check that the hand-written ground
truth is well-formed and agrees with rule set v1, so later evaluation tests can
trust it as the oracle.
"""

import calendar
from datetime import date
from pathlib import Path

import pytest
import yaml

from dfa_assistant.ruleset import load_rule_set

ROOT = Path(__file__).resolve().parent.parent
READ_STATES = {"readable", "illegible", "corrupt", "zero_byte"}
OUTCOMES = {"satisfied", "missing", "out_of_date", "unresolved"}


@pytest.fixture(scope="module")
def rs():
    return load_rule_set(ROOT / "rulesets" / "v1.yaml")


@pytest.fixture(scope="module")
def manifest():
    with open(ROOT / "fixtures" / "manifest.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _applicable(rs, fx):
    classes = {"both", fx["driver_class"]}
    if fx["medical_variance"]:
        classes.add("variance_declared")
    return {r["rule_id"]: r for r in rs["rules"] if r["applies_to"] in classes}


def _months_before(d, n):
    y, m = divmod(d.year * 12 + d.month - 1 - n, 12)
    m += 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def test_manifest_pins_rule_set_v1(manifest, rs):
    assert manifest["rule_set"] == {"rule_set_id": rs["rule_set_id"], "version": rs["version"]}


def test_fixture_ids_are_unique(manifest):
    ids = [f["id"] for f in manifest["fixtures"]]
    assert len(ids) == len(set(ids))


def test_all_scenarios_and_targeted_sets_are_present(manifest):
    scenarios = {f["scenario"] for f in manifest["fixtures"]}
    assert {"SC-01", "SC-02a", "SC-02b", "SC-03", "boundary", "degraded", "superseded", "class_mismatch"} <= scenarios


def test_documents_are_well_formed(manifest, rs):
    types = rs["document_types"]
    for fx in manifest["fixtures"]:
        files = [d["file"] for d in fx["documents"]]
        assert len(files) == len(set(files)), f"{fx['id']}: duplicate file names"
        for d in fx["documents"]:
            where = f"{fx['id']}/{d['file']}"
            assert d["type"] in types, f"{where}: undeclared type"
            assert set(d["dates"]) <= set(types[d["type"]]["date_fields"]), f"{where}: undeclared date field"
            assert d["read_state"] in READ_STATES, f"{where}: bad read_state"
            assert d["pages"] == (1 if d["read_state"] in ("readable", "illegible") else 0), f"{where}: bad page count"


def test_expected_covers_exactly_the_applicable_rules(manifest, rs):
    for fx in manifest["fixtures"]:
        assert set(fx["expected"]) == set(_applicable(rs, fx)), fx["id"]


def test_expected_entries_agree_with_rule_set(manifest, rs):
    for fx in manifest["fixtures"]:
        docs = {d["file"]: d for d in fx["documents"]}
        for rid, rule in _applicable(rs, fx).items():
            exp = fx["expected"][rid]
            where = f"{fx['id']}/{rid}"
            assert exp["outcome"] in OUTCOMES, where
            if exp["outcome"] == "satisfied":
                assert "severity" not in exp, where
            elif exp["outcome"] == "out_of_date":
                assert exp["severity"] == rule["severity_if_out_of_date"], where
            else:
                assert exp["severity"] == rule["severity_if_missing"], where
            if exp["outcome"] in ("satisfied", "out_of_date"):
                gov = docs[exp["governing"]]
                assert gov["read_state"] == "readable", where
                assert gov["type"] in rule["satisfied_by"], where
            else:
                assert "governing" not in exp, where
            for sup in exp.get("superseded", []):
                assert docs[sup]["type"] in rule["satisfied_by"], where
                assert sup != exp.get("governing"), where


def test_escalation_is_exactly_the_non_satisfied_disqualifying_rules(manifest):
    for fx in manifest["fixtures"]:
        expected = sorted(
            rid for rid, e in fx["expected"].items()
            if e["outcome"] != "satisfied" and e["severity"] == "disqualifying"
        )
        assert sorted(fx["escalation"]) == expected, fx["id"]


def test_unreadable_findings_are_exactly_the_unreadable_files(manifest):
    for fx in manifest["fixtures"]:
        unreadable = sorted(d["file"] for d in fx["documents"] if d["read_state"] != "readable")
        assert sorted(fx.get("unreadable_findings", [])) == unreadable, fx["id"]


def test_reviewer_link_variants_name_an_unreadable_file_and_an_applicable_rule(manifest, rs):
    for fx in manifest["fixtures"]:
        unreadable = {d["file"] for d in fx["documents"] if d["read_state"] != "readable"}
        for rid, link in fx.get("after_reviewer_link", {}).items():
            assert rid in fx["expected"], fx["id"]
            assert link["outcome"] == "unresolved" and link["linked"] in unreadable, fx["id"]


def test_boundary_fixtures_sit_11_12_13_months_before_evaluation_date(manifest):
    ev = manifest["evaluation_date"]
    by_id = {f["id"]: f for f in manifest["fixtures"]}
    for n in (11, 12, 13):
        fx = by_id[f"bnd-annual-{n}mo"]
        dates = {d["file"]: d["dates"] for d in fx["documents"]}
        assert dates["mvr-annual.png"]["inquiry_date"] == _months_before(ev, n)
        assert dates["annual-review.png"]["review_date"] == _months_before(ev, n)
    med = {d["file"]: d for d in by_id["bnd-medical-expires-on-evaluation-date"]["documents"]}
    assert med["medical-certificate.png"]["dates"]["expiration_date"] == ev


def test_class_mismatch_fixtures_record_true_class_differently(manifest):
    mismatched = [f for f in manifest["fixtures"] if f["scenario"] == "class_mismatch"]
    assert len(mismatched) == 2
    assert all(f["true_class"] != f["driver_class"] for f in mismatched)
