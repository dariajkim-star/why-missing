"""M1 - golden test against spike 4's census (offline, deterministic).

The network half runs in `scripts/reproduce_spike4.py` and writes a snapshot;
this file compares that snapshot and the adjudicator's behaviour to the human
oracle in `goldens.py`. Tests never fetch.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from adjudicator import concepts, residual
from adjudicator.verdict import Form, adjudicate
from tests.goldens import (M1_REPRODUCTION, MACHINE_RESOLVED_SINCE_SPIKE4,
                           SPIKE4_CENSUS, SPIKE4_HOMONYM_SICS, SPIKE4_TOTALS)

CONCEPT = concepts.resolve("finite_lived_intangibles_net")
SNAPSHOT = Path(__file__).resolve().parents[1] / "docs" / "data" / "spike4-census-reproduced.json"


def test_the_golden_census_is_internally_consistent():
    named = {c: sum(1 for r in SPIKE4_CENSUS if r[1] == c) for c in "abc"}
    assert named == {"a": SPIKE4_TOTALS["a"], "b": SPIKE4_TOTALS["b"], "c": SPIKE4_TOTALS["c"]}
    assert len(SPIKE4_CENSUS) + SPIKE4_TOTALS["undetermined"] == SPIKE4_TOTALS["companies"]
    assert SPIKE4_TOTALS["d"] == 0


def test_every_homonym_sic_the_census_found_is_in_the_concept_list():
    """KILLS: a homonym list that drifted behind the measured census.

    The list is declared GROWING, and this is the mechanism that makes growth
    visible instead of silent - each measured collision must be registered.
    """
    missing = [s for s in SPIKE4_HOMONYM_SICS
               if not any(s.startswith(p) for p in CONCEPT.homonym_sic_prefixes)]
    assert not missing, f"census proved these SICs are homonyms but they are unregistered: {missing}"


@pytest.mark.parametrize("company,klass,form,reachable,evidence",
                         [r for r in SPIKE4_CENSUS if r[3]])
def test_machine_reachable_verdicts_match_the_human(company, klass, form, reachable, evidence):
    """The seven class-c firms must be reachable from SIC alone.

    KILLS: checking absence before homonym (Warrior Met's manufactured
    liability, intangibles edition), or losing a SIC prefix from the list.
    """
    sic = {"6798": "6798", "6500": "6500", "6311": "6311", "4911": "4911"}
    prefix = next(p for p in sic if p in evidence)
    v = adjudicate(CONCEPT, face_tags=set(), notes_tags={"FiniteLivedIntangibleAssetsGross"},
                   sic=prefix, concept_evidence=True)
    assert v.form is form, f"{company}: expected {form}, got {v.form}"


def test_prose_only_verdicts_are_never_guessed():
    """KILLS: emitting a confident verdict where only a human read can decide.

    Classes a and b (15 of 23) were settled by reading prose - Sturm Ruger's
    Note 6, SPOK's 'no remaining amortizable intangible assets'. From tags
    alone the honest answer is a CANDIDATE requiring confirmation, never
    'reported elsewhere' or 'not applicable'.
    """
    prose_only = [r for r in SPIKE4_CENSUS if not r[3]]
    assert len(prose_only) == 15
    v = adjudicate(CONCEPT, face_tags=set(), notes_tags={"FiniteLivedIntangibleAssetsGross"},
                   sic="3484", concept_evidence=True)  # Sturm Ruger's SIC
    assert v.form is Form.CANDIDATE_OMISSION
    assert "REQUIRED" in v.render()


@pytest.mark.skipif(not SNAPSHOT.exists(), reason="run scripts/reproduce_spike4.py first")
def test_no_census_company_is_lost_without_a_verdict():
    """M1 proper: committed code re-derives spike 4's census from SEC data.

    The contract is NOT population identity - spike 4's machine used a narrower
    tag vocabulary, so the corrected code legitimately finds a different set.
    The contract is that no censused company DISAPPEARS silently: each of the 22
    named firms must either still be a residual (awaiting the human read the
    census gave it) or be machine-resolved to a NON-omission form, which is
    recorded by name in goldens.

    KILLS: a vocabulary edit that quietly drops a company from view.
    """
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["concept"] == CONCEPT.key
    assert snap["window"] == ["2024q3", "2024q4", "2025q1", "2025q2"]

    reproduced = {c["company"].upper() for c in snap["companies"]}
    accounted, lost = 0, []
    for name, klass, *_ in SPIKE4_CENSUS:
        if any(name in r or r in name or name.split()[0] in r for r in reproduced):
            accounted += 1
        elif name in MACHINE_RESOLVED_SINCE_SPIKE4:
            assert klass == "b", f"{name}: only class b may be machine-resolved, not {klass}"
            accounted += 1
        else:
            lost.append(name)
    assert not lost, f"census companies vanished without a verdict: {sorted(lost)}"
    assert accounted == len(SPIKE4_CENSUS)


@pytest.mark.skipif(not SNAPSHOT.exists(), reason="run scripts/reproduce_spike4.py first")
def test_the_reproduction_delta_is_pinned():
    """KILLS: silent drift in the reproduced population.

    The delta from spike 4 is a measured fact, not an accident, so it is pinned:
    any future change to the tag vocabulary must move these numbers deliberately.
    """
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert len(snap["companies"]) == M1_REPRODUCTION["companies"]
    assert len(MACHINE_RESOLVED_SINCE_SPIKE4) == M1_REPRODUCTION["machine_resolved"]


def test_residual_excludes_a_complete_component_pair():
    """KILLS: forgetting form 3 in population selection - the residual inflates 5x
    (467 -> 94 was exactly this correction).
    """
    import pandas as pd
    sub = pd.DataFrame([{"adsh": "0000000000-24-000001", "cik": "1", "name": "X",
                         "sic": "7372", "form": "10-K", "period": "20241231",
                         "fy": "2024", "fp": "FY"}])
    legs = [g[0] for g in CONCEPT.part_groups]
    both = pd.DataFrame([{"adsh": "0000000000-24-000001", "tag": t} for t in legs])
    one = both.iloc[:1]
    assert residual.find_residuals(sub, both, CONCEPT, "2025q1") == []
    assert len(residual.find_residuals(sub, one, CONCEPT, "2025q1")) == 1


def _one_filing(tags: list[str], sic: str = "7372"):
    import pandas as pd
    sub = pd.DataFrame([{"adsh": "0000000000-24-000001", "cik": "1", "name": "X",
                         "sic": sic, "form": "10-K", "period": "20241231",
                         "fy": "2024", "fp": "FY"}])
    num = pd.DataFrame([{"adsh": "0000000000-24-000001", "tag": t} for t in tags])
    return sub, num


def test_a_filing_that_tags_the_net_is_not_a_residual():
    """KILLS: ignoring net-family presence during population selection.

    Without this the residual would contain every filer who tagged the value
    normally - the population would be meaningless and the tool would name
    companies that disclosed.
    """
    sub, num = _one_filing(["FiniteLivedIntangibleAssetsNet",
                            "FiniteLivedIntangibleAssetsAccumulatedAmortization"])
    assert residual.find_residuals(sub, num, CONCEPT, "2025q1") == []


def test_an_umbrella_tag_keeps_a_filing_out_of_the_residual():
    """KILLS: dropping a parallel-tag synonym from the registry.

    Measured in M1: HCA / Trex / Lazard report via IntangibleAssetsNetIncludingGoodwill;
    losing that entry puts three large filers back on a suspicion list, which is
    the incomplete-tag-list failure this project has now hit three times.
    """
    sub, num = _one_filing(["IntangibleAssetsNetIncludingGoodwill",
                            "FiniteLivedIntangibleAssetsAccumulatedAmortization"])
    assert residual.find_residuals(sub, num, CONCEPT, "2025q1") == []
    v = adjudicate(CONCEPT, face_tags=set(),
                   notes_tags={"IntangibleAssetsNetIncludingGoodwill"},
                   sic="8062", concept_evidence=True)
    assert v.form is Form.REPORTED_ELSEWHERE


def test_the_quarterly_to_monthly_switch_is_honoured():
    """KILLS: a naive quarter loop past 2025q2 (T1 trap).

    2025q3_notes.zip does not exist; the data lives in three monthly archives.
    A loop that asks for the quarterly name silently loses a year.
    """
    from adjudicator import sec
    assert sec.archive_names("2025q2") == ["2025q2_notes.zip"]
    assert sec.archive_names("2025q3") == ["2025_07_notes.zip", "2025_08_notes.zip",
                                           "2025_09_notes.zip"]
