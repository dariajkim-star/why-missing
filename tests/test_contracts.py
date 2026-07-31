"""Contract tests - one section per ported contract (MVP M2).

Rule inherited from the rehearsal: a test must be able to DIE. Each test below
names the mutation it kills; tests that no implementation defect could fail
(tautologies) do not belong here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from adjudicator import concepts, freshness, identity, peers, safewrite, sanity
from adjudicator.verdict import FORBIDDEN_PHRASES, Form, Verdict, adjudicate

LEASE = concepts.resolve("operating_lease_liability")
INTAN = concepts.resolve("finite_lived_intangibles_net")


# --- Contract 1: per-concept absence definition; stock-only input door -------

def test_flow_concepts_are_refused_at_the_door():
    """KILLS: dropping the nature check, or checking it downstream of judgement.

    A flow concept's absent tag carries no signal (form 5, unmachinable), so
    admitting one produces confident nonsense.
    """
    with pytest.raises(concepts.FlowConceptRejected) as e:
        concepts.resolve("share_based_compensation")
    assert "flow" in str(e.value).lower()


def test_unknown_concept_names_the_known_ones():
    with pytest.raises(KeyError) as e:
        concepts.resolve("free_cash_flow")
    assert "operating_lease_liability" in str(e.value)


def test_each_concept_carries_its_own_absence_shape():
    """KILLS: a single global tag list shared across concepts.

    Intangibles have an umbrella escape hatch and derivable components; the
    lease liability has NEITHER (measured, spike 5) - that asymmetry is why
    the lease residual held and the intangible residual collapsed to zero.
    """
    assert INTAN.umbrella_tags and INTAN.part_groups
    assert not LEASE.umbrella_tags


# --- Contract 2: absence counts only when BOTH datasets are silent ----------

def test_a_notes_only_tag_still_means_present():
    """KILLS: reading the face dataset alone.

    Measured: OperatingLeaseLiability face coverage 6.0% vs notes 79.4% -
    face-only would name ~94% of filers as omitting what they disclosed.
    """
    v = adjudicate(LEASE, face_tags=set(), notes_tags={"OperatingLeaseLiability"},
                   sic="7372", concept_evidence=True)
    assert v.form is Form.PRESENT


def test_absence_requires_silence_in_both():
    v = adjudicate(LEASE, face_tags=set(), notes_tags=set(),
                   sic="7372", concept_evidence=True)
    assert v.form is Form.CANDIDATE_OMISSION


# --- Contract 3: big-company self-suspicion ---------------------------------

def test_large_filers_at_the_top_raise_the_alarm_and_are_named():
    """KILLS: returning a bare boolean, or no check at all.

    Fired 3/3 in the rehearsal (LabCorp/FIS/ADM etc.). Positions are returned
    so the report can NAME which entries triggered it.
    """
    hits = sanity.large_company_alarm([5_000e6, 8e6, 12e6], population_median_assets=50e6)
    assert hits == [0]
    assert sanity.large_company_alarm([8e6, 12e6], population_median_assets=50e6) == []


# --- Contract 6: peer cell SIC4 -> SIC3 -> NO VERDICT ------------------------

def test_a_starved_cell_yields_no_verdict_not_a_padded_cell():
    """KILLS: falling back to "use whatever peers we have".

    Four peers is gossip; a forced cell manufactures a percentile out of noise.
    """
    assert peers.build_cell(sic4_members=list(range(4)), sic3_members=list(range(6)),
                            sic="7372") is None


def test_sic3_promotion_only_when_sic4_is_short():
    cell = peers.build_cell(list(range(12)), list(range(40)), "7372")
    assert cell.level == "SIC4"
    cell = peers.build_cell(list(range(3)), list(range(40)), "7372")
    assert cell.level == "SIC3"


# --- Contract 9 clause 1: row identity, and 404 != fetch failure -------------

def test_identity_refuses_a_non_canonical_accession():
    """KILLS: accepting a search-index id or a bare CIK pairing."""
    with pytest.raises(ValueError):
        identity.RowIdentity(cik=320193, accession="0000320193-24-123")  # short
    identity.RowIdentity(cik=320193, accession="0000320193-24-000123")  # canonical


def test_a_failed_fetch_may_not_testify_to_absence():
    """KILLS: treating any non-200 as "not there".

    Spike 6 run 1 did exactly this - a URL typo made every quarter look
    "unavailable", and the run recorded absence. Infrastructure edition of
    absence-is-not-omission.
    """
    assert identity.classify_http(404) is identity.FetchOutcome.NOT_FOUND
    assert identity.classify_http(503) is identity.FetchOutcome.FETCH_FAILED
    assert identity.classify_http(None) is identity.FetchOutcome.FETCH_FAILED
    identity.require_observable(identity.FetchOutcome.NOT_FOUND)  # allowed
    with pytest.raises(identity.AccessFailureIsNotAbsence):
        identity.require_observable(identity.FetchOutcome.FETCH_FAILED)


# --- Contract 9 clause 2: freshness pass bar --------------------------------

def test_upstream_change_without_recomputation_fails(tmp_path: Path):
    """THE pre-committed pass bar: if an upstream artifact changes and the
    downstream one passes unchanged, this test must fail.

    KILLS: timestamp-only freshness (the level transitive staleness walked
    through in the rehearsal).
    """
    meta = freshness.build_meta("verdicts.jsonl", {"sub.tsv": b"v1", "num.tsv": b"A"})
    assert freshness.is_stale(meta, {"sub.tsv": b"v1", "num.tsv": b"A"}) == []
    assert freshness.is_stale(meta, {"sub.tsv": b"v2", "num.tsv": b"A"}) == ["sub.tsv"]


def test_a_vanished_input_counts_as_changed():
    meta = freshness.build_meta("out", {"a": b"1", "b": b"2"})
    assert freshness.is_stale(meta, {"a": b"1"}) == ["b"]


def test_meta_survives_a_round_trip(tmp_path: Path):
    meta = freshness.build_meta("out", {"a": b"1"})
    p = tmp_path / "out.meta.json"
    freshness.save_meta(meta, p)
    assert freshness.load_meta(p) == meta


# --- Crash safety (implementation gate 3) -----------------------------------

def test_a_crash_leaves_no_finished_looking_file(tmp_path: Path):
    """KILLS: writing rows directly to the final path.

    A half-written named list is a lie with a filename.
    """
    out = tmp_path / "exclusions.txt"
    with pytest.raises(RuntimeError):
        safewrite.atomic_write_with_meta(out, ["a", "b"], rows_examined=2,
                                         _fail_before_commit=True)
    assert not out.exists()


def test_completion_meta_distinguishes_examined_from_written(tmp_path: Path):
    """KILLS: recording only the row count.

    "examined 100, wrote 50" and "examined 50 then crashed" produce the same
    row count and mean opposite things.
    """
    out = tmp_path / "verdicts.txt"
    safewrite.atomic_write_with_meta(out, ["x"] * 50, rows_examined=100)
    meta = json.loads((tmp_path / "verdicts.txt.meta.json").read_text(encoding="utf-8"))
    assert meta == {"rows_written": 50, "rows_examined": 100, "complete": True}


def test_writing_more_rows_than_examined_is_refused(tmp_path: Path):
    with pytest.raises(ValueError):
        safewrite.atomic_write_with_meta(tmp_path / "o.txt", ["a", "b"], rows_examined=1)


# --- M4: the permanent caveat, productized ----------------------------------

def test_the_system_cannot_state_a_confirmed_omission():
    """KILLS: any renderer path that could emit certainty about form 1.

    Detection power is unverifiable (spike 5, X1 unmet), so form 1 is forever
    a candidate. This is the product-level edition of the permanent caveat.
    """
    v = Verdict(Form.CANDIDATE_OMISSION, evidence="no tag in face or notes")
    text = v.render()
    assert "REQUIRED" in text
    for phrase in FORBIDDEN_PHRASES:
        assert phrase.lower() not in text.lower()


def test_every_verdict_carries_an_evidence_line():
    """KILLS: allowing a verdict with no reason - that is a blacklist entry."""
    with pytest.raises(ValueError):
        Verdict(Form.REPORTED_ELSEWHERE, evidence="   ")


# --- Contract 8 + 9: the acquisition layer's absence gate --------------------

def test_a_server_error_during_acquisition_raises_instead_of_caching_absence(tmp_path, monkeypatch):
    """KILLS: dropping the require_observable gate in the fetch path.

    Spike 6 run 1 recorded "dataset unavailable" for archives it had merely
    failed to reach. A 5xx must stop the run; only an authoritative 404 may be
    remembered as "this file does not exist".
    """
    from adjudicator import sec

    class Resp:
        status_code = 503
        content = b""

    monkeypatch.setattr(sec.requests, "get", lambda *a, **k: Resp())
    monkeypatch.setattr(sec.time, "sleep", lambda *_: None)
    with pytest.raises(identity.AccessFailureIsNotAbsence):
        sec._get("https://example.invalid/x.zip", tmp_path, "x.zip")
    assert not (tmp_path / "x.zip.notfound").exists()


def test_an_authoritative_404_is_remembered_as_nonexistence(tmp_path, monkeypatch):
    from adjudicator import sec

    class Resp:
        status_code = 404
        content = b""

    monkeypatch.setattr(sec.requests, "get", lambda *a, **k: Resp())
    monkeypatch.setattr(sec.time, "sleep", lambda *_: None)
    assert sec._get("https://example.invalid/x.zip", tmp_path, "x.zip") is None
    assert (tmp_path / "x.zip.notfound").exists()
