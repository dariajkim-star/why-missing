"""M3 - the interactive path, tested offline (no network in tests).

The acquisition functions are monkeypatched; what is under test is the CLI's
CONTRACT: which filing it names, what it refuses, and what it must say when it
cannot see everything.
"""
from __future__ import annotations

import pytest

from adjudicator import cli, live
from adjudicator.identity import RowIdentity
from adjudicator.verdict import FORBIDDEN_PHRASES

FILING = live.FilingRef(
    identity=RowIdentity(cik=95029, accession="0001174947-25-000197"),
    company="STURM RUGER & CO INC", sic="3480", filed="2025-02-19",
    period="2024-12-31", form="10-K",
)


def _wire(monkeypatch, tags: set[str], sic: str = "3480"):
    monkeypatch.setattr(live, "resolve_company", lambda q: (95029, FILING.company))
    monkeypatch.setattr(live, "latest_annual",
                        lambda cik: live.FilingRef(FILING.identity, FILING.company, sic,
                                                   FILING.filed, FILING.period, FILING.form))
    monkeypatch.setattr(live, "tags_reported_in", lambda f, t: frozenset(tags))


def test_a_candidate_verdict_always_ships_its_blind_spots(monkeypatch, capsys):
    """KILLS: printing a candidate without saying what the tool cannot see.

    Sturm Ruger is the case in point - the census found its intangibles in a
    prose 'Other Assets' note, which this door cannot read. A candidate that
    hides that reads as "the machine says it is missing".
    """
    _wire(monkeypatch, {"FiniteLivedIntangibleAssetsAccumulatedAmortization"})
    assert cli.run(["RGR", "finite_lived_intangibles_net"]) == 0
    out = capsys.readouterr().out
    assert "CANDIDATE_OMISSION" in out
    assert "dimensional tags" in out and "prose-only" in out
    assert "detection power could not be validated" in out


def test_a_resolved_verdict_does_not_cry_wolf(monkeypatch, capsys):
    """KILLS: attaching the omission caveat to every verdict.

    A warning printed everywhere is a warning read nowhere.
    """
    _wire(monkeypatch, {"IntangibleAssetsNetIncludingGoodwill"})
    cli.run(["HCA", "finite_lived_intangibles_net"])
    out = capsys.readouterr().out
    assert "REPORTED_ELSEWHERE" in out
    assert "blind" not in out


def test_the_filing_that_was_read_is_always_named(monkeypatch, capsys):
    """KILLS: reporting a verdict without its accession (lineage clause 1).

    Without the accession the reader cannot tell which fiscal year, or which
    company, the answer belongs to.
    """
    _wire(monkeypatch, set())
    cli.run(["RGR"])
    out = capsys.readouterr().out
    assert "0001174947-25-000197" in out
    assert "CIK 95029" in out


def test_no_output_path_can_state_a_confirmed_omission(monkeypatch, capsys):
    """M4, enforced at the CLI boundary too."""
    for tags in ({"FiniteLivedIntangibleAssetsAccumulatedAmortization"}, set(),
                 {"IntangibleAssetsNetIncludingGoodwill"}):
        _wire(monkeypatch, tags)
        cli.run(["RGR"])
        out = capsys.readouterr().out.lower()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase.lower() not in out


def test_a_flow_concept_is_refused_before_any_fetch(monkeypatch, capsys):
    """KILLS: reaching the network for a question that cannot be answered.

    Also proves the refusal is at the door: the fetchers are wired to explode.
    """
    def boom(*a, **k):
        raise AssertionError("the CLI must not fetch for a rejected concept")

    monkeypatch.setattr(live, "resolve_company", boom)
    assert cli.run(["AAPL", "share_based_compensation"]) == 2
    assert "FLOW concept" in capsys.readouterr().err


def test_an_ambiguous_company_asks_instead_of_picking(monkeypatch, capsys):
    """KILLS: silently taking the first match.

    Answering about the wrong company is the failure mode this project's
    lineage contract exists for (the spike 5 mis-pairing).
    """
    def ambiguous(q):
        raise LookupError("'TRUST' matches 363 companies; be specific: DLR=..., NTRS=...")

    monkeypatch.setattr(live, "resolve_company", ambiguous)
    assert cli.run(["TRUST"]) == 1
    assert "be specific" in capsys.readouterr().err


def test_peer_context_absence_is_declared_not_omitted(monkeypatch, capsys):
    """KILLS: quietly dropping the peer line when there is no cached quarter.

    A verdict that looks peer-informed but is not is worse than one that says so.
    """
    _wire(monkeypatch, set())
    cli.run(["RGR"])
    assert "peer ctx : none" in capsys.readouterr().out


def test_companyfacts_is_only_ever_read_through_an_accession():
    """KILLS: reintroducing the merged-view read that spike 6 banned.

    The ban is structural: the only companyfacts call site takes a FilingRef and
    filters facts by its accession, so there is no unpinned path to remove.
    """
    import inspect
    src = inspect.getsource(live)
    calls = [ln for ln in src.splitlines() if "api/xbrl/companyfacts" in ln]
    assert len(calls) == 1, calls
    body = inspect.getsource(live.tags_reported_in)
    assert 'row.get("accn") == accession' in body
