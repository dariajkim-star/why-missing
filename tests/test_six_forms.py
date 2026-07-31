"""The six-form classifier, exercised on the shapes measured in the spikes.

Each case names the real filing that taught it. These are ORACLE tests: the
expected form comes from a human who opened the 10-K, not from re-running the
code that is under test.
"""
from __future__ import annotations

import pytest

from adjudicator import concepts
from adjudicator.verdict import Form, adjudicate

LEASE = concepts.resolve("operating_lease_liability")
INTAN = concepts.resolve("finite_lived_intangibles_net")


def test_form2_reported_elsewhere_sturm_ruger_shape():
    """Sturm Ruger: patents/trade name/amortization all inside Note 6 'Other
    Assets', so the dedicated tag never appears but an umbrella tag does.
    """
    v = adjudicate(INTAN, face_tags=set(),
                   notes_tags={"IntangibleAssetsNetExcludingGoodwill"},
                   sic="3484", concept_evidence=True)
    assert v.form is Form.REPORTED_ELSEWHERE
    assert "IntangibleAssetsNetExcludingGoodwill" in v.evidence


def test_form3_derivable_subtotal_ehealth_shape():
    """eHealth: gross $17.2M and accumulated amortization $17.2M both tagged -
    the net subtotal is computable, not hidden (and here it is zero).
    """
    v = adjudicate(INTAN, face_tags={"FiniteLivedIntangibleAssetsGross",
                                     "FiniteLivedIntangibleAssetsAccumulatedAmortization"},
                   notes_tags=set(), sic="7389", concept_evidence=True)
    assert v.form is Form.DERIVABLE_SUBTOTAL


def test_form4_not_applicable_spac_shape():
    """58% of lease 'absences' were SPACs/funds/REIT-lessors with no leases."""
    v = adjudicate(LEASE, face_tags=set(), notes_tags=set(),
                   sic="6770", concept_evidence=False)
    assert v.form is Form.NOT_APPLICABLE


def test_form6_industry_homonym_warrior_met_shape():
    """Oil/gas and mining 'lease' means mineral rights (spike 3-V: 42% of the
    sample). Homonym is checked BEFORE absence, or we manufacture a liability
    that does not exist ($131.9M, Warrior Met Coal).
    """
    v = adjudicate(LEASE, face_tags=set(), notes_tags=set(),
                   sic="1311", concept_evidence=True)
    assert v.form is Form.INDUSTRY_HOMONYM


def test_homonym_outranks_candidate_omission():
    """KILLS: ordering the checks so absence wins first.

    Both conditions hold for Warrior Met; if CANDIDATE_OMISSION won, the tool
    would name a company for omitting something it never had.
    """
    homonym = adjudicate(LEASE, set(), set(), sic="1311", concept_evidence=True)
    normal = adjudicate(LEASE, set(), set(), sic="7372", concept_evidence=True)
    assert homonym.form is Form.INDUSTRY_HOMONYM
    assert normal.form is Form.CANDIDATE_OMISSION


def test_present_outranks_everything():
    """A standard tag in a homonym industry is still simply present."""
    v = adjudicate(LEASE, face_tags={"OperatingLeaseLiability"}, notes_tags=set(),
                   sic="1311", concept_evidence=True)
    assert v.form is Form.PRESENT


def test_unknown_evidence_yields_no_verdict_not_a_guess():
    """KILLS: defaulting unknown evidence to 'absent' (the whole project's sin)."""
    v = adjudicate(LEASE, set(), set(), sic="7372", concept_evidence=None)
    assert v.form is Form.NO_VERDICT


def test_component_pair_only_counts_when_complete():
    """One leg tagged is not a derivable subtotal."""
    v = adjudicate(INTAN, face_tags={"FiniteLivedIntangibleAssetsGross"},
                   notes_tags=set(), sic="7372", concept_evidence=True)
    assert v.form is not Form.DERIVABLE_SUBTOTAL


def test_form5_is_unreachable_at_runtime():
    """Legitimate zero exists in the taxonomy but must never be PRODUCED -
    flow concepts are refused at the input door instead.
    """
    with pytest.raises(concepts.FlowConceptRejected):
        concepts.resolve("share_based_compensation")
