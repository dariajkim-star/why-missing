"""Evidence rules -> ranked six-form opinion (pre-registration: docs/evidence-rules-preregistration.md).

Plain sentence: this module takes the observed XBRL tag names plus the SIC and
returns a RANKED opinion over the six forms, not a single label (party decision 1).
Scores are the WEIGHT OF EVIDENCE, not probabilities.

This module does NOT touch `adjudicator.verdict.adjudicate` - party decision 1 is
"judgement logic unchanged, output contract changed". It is also NOT a renderer
(party decision 3: hit rate first, renderer later). It emits structured data;
turning that into a screen is a later, separate step.

Hard constraints implemented here, quoting the pre-registration IDs:
  C-1  form 1 (CANDIDATE_OMISSION) never carries the "most likely" slot.
  C-2  a rule that cannot attach an observed-value line scores nothing.
  C-3  forms with score <= 0 are not displayed; display cap is 3 forms.
  C-4  nothing survives -> NO_VERDICT, no ranking is manufactured.
  C-5  an observation whose absence-reason is unknown is not scored.

NO company name, CIK or accession literal may appear in this file. Hardcoding a
counter-example from the answer key would make the measurement a tautology
(measurement pre-registration section 5.3).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from adjudicator.concepts import Concept, FlowConceptRejected
from adjudicator.verdict import Form

# ---------------------------------------------------------------------------
# Generic observation vocabulary (tag-name families, never company literals).
# ---------------------------------------------------------------------------

# R-06: amortisation EXPENSE tags. Used only as corroboration for a stock
# target, never as a target itself, so contract 4 (no flow concepts) holds.
AMORTIZATION_EXPENSE_TAGS: frozenset[str] = frozenset({
    "AmortizationOfIntangibleAssets",
    "AmortizationOfIntangibleAssetsAndDebtIssuanceCosts",
    "FiniteLivedIntangibleAssetsAmortizationExpense",
})

# R-08: future amortisation SCHEDULE tags. Disclosing next years' amortisation
# is a direct statement that an unamortised balance remains at period end.
FUTURE_AMORTIZATION_SCHEDULE_TAGS: frozenset[str] = frozenset({
    "FiniteLivedIntangibleAssetsAmortizationExpenseNextTwelveMonths",
    "FiniteLivedIntangibleAssetsAmortizationExpenseYearTwo",
    "FiniteLivedIntangibleAssetsAmortizationExpenseYearThree",
    "FiniteLivedIntangibleAssetsAmortizationExpenseYearFour",
    "FiniteLivedIntangibleAssetsAmortizationExpenseYearFive",
    "FiniteLivedIntangibleAssetsAmortizationExpenseAfterYearFive",
})

GOODWILL_TAGS: frozenset[str] = frozenset({"Goodwill"})

# The doors this machine cannot reach through, by name (pre-registration s5).
# Reported on every ranked opinion so the human knows what was NOT looked at.
BLIND_SPOTS: tuple[str, ...] = (
    "U-1 prose-only disclosure: an amount written in a note sentence leaves no XBRL tag",
    "U-2 dimension-only disclosure: this pipeline does not read axis tags",
    "U-3 fully-amortised (form 4) vs remaining balance (form 2): tag NAMES alone cannot separate these",
    "U-4 indefinite- vs finite-lived split lives in prose only",
    "U-6 a statement that the concept does not exist leaves no tag",
    "U-7 the industry-homonym SIC list is GROWING and never complete",
)

HUMAN_CONFIRMATION_HEADER = (
    "automatic confirmation not possible - a human must read the 10-K原文"
)

MAX_DISPLAYED_FORMS = 3  # C-3 / measurement pre-registration s2


# ---------------------------------------------------------------------------
# Input / output shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Observation:
    """One (company, concept) observation. Identity is deliberately NOT here."""

    concept: Concept
    face_tags: frozenset[str] = frozenset()
    notes_tags: frozenset[str] = frozenset()
    sic: str = ""
    concept_evidence: bool | None = None
    concept_evidence_source: str = ""
    # G-03 / contract 5: datasets we FAILED TO READ, as opposed to read-and-empty.
    unreadable_datasets: tuple[str, ...] = ()
    # R-13 / U-8: peer usage. None means "we cannot tell 'no peers' from
    # 'cache unreadable'", which under C-5 means the rule must not fire.
    peer_usage: tuple[int, int] | None = None
    peer_threshold: float = 0.5

    @property
    def seen(self) -> frozenset[str]:
        return frozenset(self.face_tags) | frozenset(self.notes_tags)


@dataclass(frozen=True)
class RankedLine:
    form: Form
    score: int
    observations: tuple[str, ...]  # C-2: never empty for a displayed line

    @property
    def slot(self) -> str:
        """C-1: form 1 can never be labelled 'most likely', whatever its score."""
        if self.form is Form.CANDIDATE_OMISSION:
            return "cannot be ruled out"
        return "candidate"


@dataclass(frozen=True)
class Opinion:
    status: str  # "PRESENT" | "NO_VERDICT" | "RANKED"
    ranked: tuple[RankedLine, ...] = ()
    gate_evidence: str = ""
    needs_human_confirmation: bool = False
    blind_spots: tuple[str, ...] = ()
    fired_rules: tuple[str, ...] = ()
    dormant_rules: tuple[str, ...] = ()
    # v2 additions (defaults keep every v1 construction site valid):
    tie: bool = False                        # rank 1 decided by enum order (s5-2)
    value_conflicts: tuple[str, ...] = ()    # C-8: surfaced, never arbitrated
    value_notes: tuple[str, ...] = ()        # scoreless value observations (V-05/U-10)
    # v3 additions (F4 support - preregistration-v3 s5, audit addendum s2-2):
    r15_attributed: tuple[str, ...] = ()     # rules whose evidence was attributed to form 6
    r15_bonus: int = 0                       # corroboration form 6 received via R-15 (cap +2)

    @property
    def top_form(self) -> Form | None:
        return self.ranked[0].form if self.ranked else None

    @property
    def most_likely(self) -> RankedLine | None:
        """C-1: the 'most likely' slot skips form 1 even if it ranks first."""
        for line in self.ranked:
            if line.form is not Form.CANDIDATE_OMISSION:
                return line
        return None


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------


@dataclass
class _Ledger:
    scores: dict[Form, int] = field(default_factory=dict)
    notes: dict[Form, list[str]] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)

    def award(self, rule_id: str, line: str, **weights: int) -> None:
        """C-2: `line` is mandatory. No observed-value line -> no score."""
        if not line or not line.strip():
            raise ValueError(f"{rule_id}: a rule without an observed-value line may not score")
        if rule_id not in self.fired:
            self.fired.append(rule_id)
        for name, weight in weights.items():
            form = _FORM_BY_ALIAS[name]
            self.scores[form] = self.scores.get(form, 0) + weight
            if weight > 0:
                self.notes.setdefault(form, []).append(f"[{rule_id}] {line}")


_FORM_BY_ALIAS = {
    "omission": Form.CANDIDATE_OMISSION,
    "elsewhere": Form.REPORTED_ELSEWHERE,
    "derivable": Form.DERIVABLE_SUBTOTAL,
    "not_applicable": Form.NOT_APPLICABLE,
    "homonym": Form.INDUSTRY_HOMONYM,
}


def _gross_group(concept: Concept) -> frozenset[str]:
    return frozenset(concept.part_groups[0]) if concept.part_groups else frozenset()


def _accum_group(concept: Concept) -> frozenset[str]:
    return frozenset(concept.part_groups[1]) if len(concept.part_groups) > 1 else frozenset()


def rank_forms(obs: Observation) -> Opinion:
    """Score the six forms and return a ranked opinion (or a gate result)."""
    concept = obs.concept
    if concept.nature != "stock":
        raise FlowConceptRejected(
            f"G-02: {concept.key} is a flow concept - tag absence carries no signal"
        )

    seen = obs.seen
    dormant: list[str] = [
        "R-09 dimension-only disclosure (pipeline does not read axis tags)",
        "R-13 peer usage (U-8: cannot separate 'no peers' from 'cache unreadable')",
        "s4.2-1 zero-balance check (census carries tag NAMES only, no amounts)",
        "s4.2-3 prior-period comparison (no time series in the pipeline)",
    ]

    # --- G-01: the amount is in its standard place. Not a gap. ---
    main_hit = sorted(t for t in concept.main_tags if t in seen)
    if main_hit:
        return Opinion(
            status="PRESENT",
            gate_evidence=f"standard tag {main_hit[0]} observed",
            dormant_rules=tuple(dormant),
            fired_rules=("G-01",),
        )

    # --- G-03: a dataset we could not READ is not an absence (contract 2/5). ---
    if obs.unreadable_datasets:
        names = ", ".join(obs.unreadable_datasets)
        return Opinion(
            status="NO_VERDICT",
            gate_evidence=f"{names} dataset lookup FAILED - not read as absence",
            needs_human_confirmation=True,
            blind_spots=BLIND_SPOTS,
            dormant_rules=tuple(dormant),
            fired_rules=("G-03",),
        )

    led = _Ledger()

    gross = _gross_group(concept)
    accum = _accum_group(concept)
    gross_hit = sorted(gross & seen)
    accum_hit = sorted(accum & seen)
    umbrella_hit = sorted(t for t in concept.umbrella_tags if t in seen)
    schedule_hit = sorted(FUTURE_AMORTIZATION_SCHEDULE_TAGS & seen)
    expense_hit = sorted(AMORTIZATION_EXPENSE_TAGS & seen)
    goodwill_hit = sorted(GOODWILL_TAGS & seen)

    # R-01 umbrella tag observed
    if umbrella_hit:
        led.award(
            "R-01",
            f"umbrella tag {umbrella_hit[0]} observed - the amount sits under a broader label",
            elsewhere=+3, omission=-3,
        )

    # R-02 both legs observed -> subtotal is arithmetic
    if gross_hit and accum_hit:
        led.award(
            "R-02",
            f"gross {gross_hit[0]} and accumulated amortisation {accum_hit[0]} both observed"
            " - the net is computable by subtraction",
            derivable=+3, omission=-3,
        )

    # R-03 industry homonym by SIC
    if obs.sic and any(obs.sic.startswith(p) for p in concept.homonym_sic_prefixes):
        led.award(
            "R-03",
            f"SIC {obs.sic} - in this industry the concept word is a different account"
            " (exclusion list is GROWING, not complete)",
            homonym=+3, omission=-2,
        )

    # R-04 ACCUM only
    if accum_hit and not gross_hit and not umbrella_hit and not main_hit:
        led.award(
            "R-04",
            f"accumulated amortisation {accum_hit[0]} observed, no gross tag - an amortisable"
            " asset EXISTED and was disclosed somewhere; whether a balance REMAINS is not"
            " decidable from tag names",
            elsewhere=+2, not_applicable=+2, omission=-2,
        )

    # R-05 GROSS only
    if gross_hit and not accum_hit and not umbrella_hit and not main_hit:
        led.award(
            "R-05",
            f"gross tag {gross_hit[0]} observed, no accumulated-amortisation tag"
            " - the acquisition cost IS disclosed",
            elsewhere=+2, omission=-2,
        )

    # R-06 amortisation expense with no balance tag at all
    if expense_hit and not (gross_hit or accum_hit or umbrella_hit):
        led.award(
            "R-06",
            f"amortisation expense {expense_hit[0]} observed - a balance existed to amortise",
            elsewhere=+2, omission=-1,
        )

    # R-07 goodwill only
    if goodwill_hit and not (gross_hit or accum_hit or umbrella_hit or expense_hit):
        led.award(
            "R-07",
            f"goodwill {goodwill_hit[0]} observed, no separate intangible tag",
            not_applicable=+1,
        )

    # R-08 future amortisation schedule -> a balance REMAINS at period end
    if schedule_hit:
        led.award(
            "R-08",
            f"future amortisation schedule tag {schedule_hit[0]} observed"
            " - an unamortised balance REMAINS at period end",
            elsewhere=+3, not_applicable=-3, omission=-3,
        )

    # R-10 independent evidence says the concept does not exist here
    if obs.concept_evidence is False:
        led.award(
            "R-10",
            f"no independent evidence that {concept.key} exists in this business"
            f"{': ' + obs.concept_evidence_source if obs.concept_evidence_source else ''}",
            not_applicable=+3, omission=-3,
        )

    # R-11 nothing observed and concept existence unknown -> C-4
    if obs.concept_evidence is None and not led.fired:
        return Opinion(
            status="NO_VERDICT",
            gate_evidence="concept existence unconfirmed - absence is not adjudicated",
            needs_human_confirmation=True,
            blind_spots=BLIND_SPOTS,
            dormant_rules=tuple(dormant),
            fired_rules=("R-11",),
        )

    # R-12 the standard tag is absent from BOTH datasets and the concept does exist
    if obs.concept_evidence is True:
        led.award(
            "R-12",
            "standard tag absent from face AND notes (both read successfully), yet "
            f"{obs.concept_evidence_source or 'independent evidence says the concept exists'}",
            omission=+2,
        )

    # R-13 peer usage - fires only when 'no peers' and 'cache unreadable' are separable (C-5)
    if obs.peer_usage is not None:
        used, total = obs.peer_usage
        if total and used / total >= obs.peer_threshold:
            led.award(
                "R-13",
                f"peer SIC {obs.sic}: {used} of {total} filers use {concept.main_tags[0]}",
                omission=+1,
            )
        dormant = [d for d in dormant if not d.startswith("R-13")]

    # R-14 form 1 is NOT deleted when 2/3 outrank it - exclusion is not proof
    if ("R-01" in led.fired or "R-02" in led.fired) and "R-12" in led.fired:
        led.fired.append("R-14")

    displayed = [
        RankedLine(form, score, tuple(led.notes.get(form, ())))
        for form, score in led.scores.items()
        if score > 0 and led.notes.get(form)
    ]
    if not displayed:
        return Opinion(
            status="NO_VERDICT",
            gate_evidence="no form survived with a positive score and an observed-value line",
            needs_human_confirmation=True,
            blind_spots=BLIND_SPOTS,
            dormant_rules=tuple(dormant),
            fired_rules=tuple(led.fired),
        )

    # Tie-break: declared BEFORE measurement - descending score, then ascending
    # Form enum value (form 1, 2, 3, 4, 6 order). This is a fixed lexicographic
    # rule, not a per-case choice.
    displayed.sort(key=lambda line: (-line.score, line.form.value))
    displayed = displayed[:MAX_DISPLAYED_FORMS]

    return Opinion(
        status="RANKED",
        ranked=tuple(displayed),
        needs_human_confirmation=True,
        blind_spots=BLIND_SPOTS,
        fired_rules=tuple(led.fired),
        dormant_rules=tuple(dormant),
    )


# ---------------------------------------------------------------------------
# v2 - amount-value layer (pre-registration: docs/evidence-rules-preregistration-v2.md,
# audit addendum: docs/evidence-rules-v2-audit-and-measurement-addendum.md).
#
# Contracts implemented here:
#   C-6  an empty value cell is UNOBSERVED, never 0; an explicitly tagged 0 IS
#        an active observation and scores.
#   C-7  every value-rule sentence carries amount + ddate + uom, or it scores 0.
#   C-8  incomparable values (ddate/qtrs/uom/coreg mismatch, duplicates, signs
#        that are arithmetically impossible) are never subtracted - recorded as
#        VALUE_CONFLICT, score 0, surfaced on screen.
#   C-9  a silent value layer leaves the name-layer ranking untouched.
#
# The v1 `rank_forms` above is PRESERVED verbatim: F2 (value-layer contribution)
# requires a name-only run, and history requires the 1st-measurement rules to
# stay runnable. NO company name, CIK or accession literal in this section.
# ---------------------------------------------------------------------------

from datetime import date as _date
from datetime import timedelta as _timedelta
from decimal import Decimal


@dataclass(frozen=True)
class ObservationV2(Observation):
    """v1 Observation + the fact rows (residual s8). Identity still absent."""

    facts: tuple = ()            # TaggedFact rows for filter tags (unfiltered)
    evidence_facts: tuple = ()   # TaggedFact rows for schedule/expense/goodwill
    period: str = ""             # balance-sheet date anchor (V-00 step 2)
    value_source_ok: bool = False


BLIND_SPOTS_V2: tuple[str, ...] = BLIND_SPOTS + (
    "U-9 a single frozen leg: an unmoving gross says nothing about amortisation progress",
    "U-10 no comparison date: movement rules are dormant, and dormancy is NOT read as form 4",
    "U-11 an indefinite-lived pool also shows a frozen accumulated-amortisation",
    "U-12 a dimensional subset value can impersonate the whole",
    "U-13 a true balance below tau is indistinguishable from 0 - the tolerance itself is a blind spot",
    "U-14 restated/corrected duplicate values: we record VALUE_CONFLICT and stay silent",
    "U-15 same-year impairment / sub-year lives / non-acquisition gross increases can defeat V-03",
)


def _tz(v: Decimal) -> int:
    """Trailing zeros of an integral amount; fractional amounts have precision 0."""
    if v == 0:
        return 0
    if v != v.to_integral_value():
        return 0
    s = str(abs(v.to_integral_value()))
    return len(s) - len(s.rstrip("0"))


def tau(x: Decimal, y: Decimal) -> Decimal:
    """tau = 10^k, k = min(trailing_zeros(x), trailing_zeros(y), 6); tau >= 1.

    A tagged 0 is an exact statement, so either side being 0 gives tau = 1.
    The disclosure's own display rounding IS the tolerance - no invented percent.
    """
    if x == 0 or y == 0:
        return Decimal(1)
    k = min(_tz(x), _tz(y), 6)
    return Decimal(10) ** k


def _parse_ddate(s: str) -> _date | None:
    try:
        return _date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    except (ValueError, IndexError):
        return None


@dataclass(frozen=True)
class _Point:
    """A selected balance value: amount at a ddate, with its C-7 credentials."""
    ddate: str
    tag: str
    value: Decimal
    note: str = ""   # e.g. negative-accum sign preserved in words


def _select_balance(facts, tags: frozenset[str], target: _date,
                    conflicts: list[str]) -> tuple[_Point | None, _Point | None, bool]:
    """V-00: pick the target-date and prior-year values for one leg.

    Returns (value_at_target, value_at_prior, had_any_candidate_date).
    Never subtracts incomparables; duplicates with different values become
    VALUE_CONFLICT and the leg goes silent (C-8).
    """
    eligible = []
    for f in facts:
        if f.tag not in tags or f.qtrs != 0:
            continue  # only instant rows are balances (contract 4, value edition)
        if f.coreg:
            continue  # a co-registrant row is not the consolidated parent balance
        if f.value is None:
            continue  # C-6: unobserved, not zero
        if f.uom != "USD":
            conflicts.append(
                f"uom-mismatch: {f.tag} {f.ddate} uom={f.uom} - arithmetic forbidden (C-8)")
            continue
        d = _parse_ddate(f.ddate)
        if d is None:
            continue
        eligible.append((d, f))
    if not eligible:
        return None, None, False

    def at(day_lo: _date, day_hi: _date) -> _Point | None:
        pool = [(d, f) for d, f in eligible if day_lo <= d <= day_hi]
        if not pool:
            return None
        best = max(d for d, _ in pool)
        rows = [f for d, f in pool if d == best]
        values = {f.value for f in rows}
        if len(values) > 1:
            conflicts.append(
                "duplicate-values: same (tag, ddate, qtrs=0, uom) carries "
                + " vs ".join(f"{f.tag}={f.value_raw}" for f in rows)
                + " - no value is picked (C-8/U-14)")
            return None
        f = rows[0]
        return _Point(ddate=f.ddate, tag=f.tag, value=f.value)

    tgt = at(target - _timedelta(days=45), target)
    prior = None
    if tgt is not None:
        t_day = _parse_ddate(tgt.ddate)
        prior = at(t_day - _timedelta(days=400), t_day - _timedelta(days=300))
    return tgt, prior, True


def _abs_accum(p: _Point | None, conflicts: list[str]) -> _Point | None:
    """Contra-asset convention: a negative ACCUM is used as |value| with the
    original sign preserved in the sentence (C-8 table row)."""
    if p is None or p.value >= 0:
        return p
    return _Point(ddate=p.ddate, tag=p.tag, value=-p.value,
                  note=f" (filed as {p.value}; contra-asset magnitude used)")


def rank_forms_v2(obs: ObservationV2, value_layer: bool = True) -> Opinion:
    """v2 ranked opinion: v1 name layer with R-05' symmetrised, plus V-rules.

    `value_layer=False` is the F2 OFF-run (audit addendum s2-2): name layer as
    in v2 (R-05' kept - the OFF baseline is v2's own name layer, so that the
    tie re-seating of R-05' cannot masquerade as a value contribution).
    """
    concept = obs.concept
    if concept.nature != "stock":
        raise FlowConceptRejected(
            f"G-02: {concept.key} is a flow concept - tag absence carries no signal")

    seen = obs.seen
    ev_seen = frozenset(f.tag for f in obs.evidence_facts)
    conflicts: list[str] = []
    value_notes: list[str] = []
    dormant: list[str] = [
        "R-09 dimension-only disclosure (pipeline does not read axis tags)",
        "R-13 peer usage (U-8: cannot separate 'no peers' from 'cache unreadable')",
    ]

    main_hit = sorted(t for t in concept.main_tags if t in seen)
    if main_hit:
        return Opinion(status="PRESENT",
                       gate_evidence=f"standard tag {main_hit[0]} observed",
                       dormant_rules=tuple(dormant), fired_rules=("G-01",))

    if obs.unreadable_datasets:
        names = ", ".join(obs.unreadable_datasets)
        return Opinion(status="NO_VERDICT",
                       gate_evidence=f"{names} dataset lookup FAILED - not read as absence",
                       needs_human_confirmation=True, blind_spots=BLIND_SPOTS_V2,
                       dormant_rules=tuple(dormant), fired_rules=("G-03",))

    led = _Ledger()
    gross = _gross_group(concept)
    accum = _accum_group(concept)
    gross_hit = sorted(gross & seen)
    accum_hit = sorted(accum & seen)
    umbrella_hit = sorted(t for t in concept.umbrella_tags if t in seen)
    schedule_hit = sorted(FUTURE_AMORTIZATION_SCHEDULE_TAGS & (seen | ev_seen))
    expense_hit = sorted(AMORTIZATION_EXPENSE_TAGS & (seen | ev_seen))
    goodwill_hit = sorted(GOODWILL_TAGS & (seen | ev_seen))

    # ---- name layer (v1 rules, with change A: R-05 -> R-05') ----
    if umbrella_hit:
        led.award("R-01",
                  f"umbrella tag {umbrella_hit[0]} observed - the amount sits under a broader label",
                  elsewhere=+3, omission=-3)
    if gross_hit and accum_hit:
        led.award("R-02",
                  f"gross {gross_hit[0]} and accumulated amortisation {accum_hit[0]} both observed"
                  " - the net is computable by subtraction",
                  derivable=+3, omission=-3)
    if obs.sic and any(obs.sic.startswith(p) for p in concept.homonym_sic_prefixes):
        led.award("R-03",
                  f"SIC {obs.sic} - in this industry the concept word is a different account"
                  " (exclusion list is GROWING, not complete)",
                  homonym=+3, omission=-2)
    if accum_hit and not gross_hit and not umbrella_hit and not main_hit:
        led.award("R-04",
                  f"accumulated amortisation {accum_hit[0]} observed, no gross tag - an amortisable"
                  " asset EXISTED and was disclosed somewhere; whether a balance REMAINS is not"
                  " decidable from tag names",
                  elsewhere=+2, not_applicable=+2, omission=-2)
    if gross_hit and not accum_hit and not umbrella_hit and not main_hit:
        # R-05' (change A): gross is a cumulative cost account; net = gross -
        # (unobserved) accum lies anywhere in [0, gross], and 0 is inside the
        # interval - so form 4 gets the SAME weight as form 2, symmetrically
        # with R-04. Direction is decided by values, not by the tag name.
        led.award("R-05'",
                  f"gross tag {gross_hit[0]} observed, no accumulated-amortisation tag"
                  " - an intangible WAS acquired and capitalised; whether a balance remains"
                  " at period end is not decided by the tag name",
                  elsewhere=+2, not_applicable=+2, omission=-2)
    if expense_hit and not (gross_hit or accum_hit or umbrella_hit):
        led.award("R-06",
                  f"amortisation expense {expense_hit[0]} observed - a balance existed to amortise",
                  elsewhere=+2, omission=-1)
    if goodwill_hit and not (gross_hit or accum_hit or umbrella_hit or expense_hit):
        led.award("R-07",
                  f"goodwill {goodwill_hit[0]} observed, no separate intangible tag",
                  not_applicable=+1)
    if schedule_hit:
        led.award("R-08",
                  f"future amortisation schedule tag {schedule_hit[0]} observed"
                  " - an unamortised balance REMAINS at period end",
                  elsewhere=+3, not_applicable=-3, omission=-3)
    if obs.concept_evidence is False:
        led.award("R-10",
                  f"no independent evidence that {concept.key} exists in this business"
                  f"{': ' + obs.concept_evidence_source if obs.concept_evidence_source else ''}",
                  not_applicable=+3, omission=-3)
    if obs.concept_evidence is None and not led.fired:
        return Opinion(status="NO_VERDICT",
                       gate_evidence="concept existence unconfirmed - absence is not adjudicated",
                       needs_human_confirmation=True, blind_spots=BLIND_SPOTS_V2,
                       dormant_rules=tuple(dormant), fired_rules=("R-11",))
    if obs.concept_evidence is True:
        led.award("R-12",
                  "standard tag absent from face AND notes (both read successfully), yet "
                  f"{obs.concept_evidence_source or 'independent evidence says the concept exists'}",
                  omission=+2)
    if obs.peer_usage is not None:
        used, total = obs.peer_usage
        if total and used / total >= obs.peer_threshold:
            led.award("R-13",
                      f"peer SIC {obs.sic}: {used} of {total} filers use {concept.main_tags[0]}",
                      omission=+1)
        dormant = [d for d in dormant if not d.startswith("R-13")]
    if ("R-01" in led.fired or "R-02" in led.fired) and "R-12" in led.fired:
        led.fired.append("R-14")

    # ---- value layer (V-00 .. V-11) ----
    target = _parse_ddate(obs.period)
    if not value_layer:
        dormant.append("V-01..V-11 value layer DISABLED (F2 OFF-run)")
    elif not obs.value_source_ok or (not obs.facts and not obs.evidence_facts):
        # C-9: a silent value layer leaves the name ranking untouched.
        dormant.append("V-01..V-11 no fact rows loaded - value layer dormant, "
                       "NOT read as form 4 (C-9)")
    elif target is None:
        dormant.append("V-01..V-11 balance-sheet date unparseable - value layer dormant (C-9)")
    else:
        g_t, g_p, g_any = _select_balance(obs.facts, gross, target, conflicts)
        a_t, a_p, a_any = _select_balance(obs.facts, accum, target, conflicts)
        u_t, _u_p, _ = _select_balance(obs.facts, frozenset(concept.umbrella_tags),
                                       target, conflicts)
        # contra-asset sign convention (C-8 table)
        a_t = _abs_accum(a_t, conflicts)
        a_p = _abs_accum(a_p, conflicts)
        # GROSS may not be negative: acquisition cost is a nonnegative cumulative
        if g_t is not None and g_t.value < 0:
            conflicts.append(f"gross-negative: {g_t.tag} {g_t.ddate} = {g_t.value} - "
                             "a cumulative acquisition cost cannot be negative (C-8)")
            g_t = None
        if g_p is not None and g_p.value < 0:
            conflicts.append(f"gross-negative: {g_p.tag} {g_p.ddate} = {g_p.value} - "
                             "a cumulative acquisition cost cannot be negative (C-8)")
            g_p = None

        # V-01 / V-01b: both legs at target (structurally absent in the residual;
        # kept so the dormancy is the document's statement, not an accident)
        if g_t is not None and a_t is not None:
            t = tau(g_t.value, a_t.value)
            if a_t.value - g_t.value > t:
                conflicts.append(
                    f"accum-exceeds-gross: {a_t.value} USD ({a_t.ddate}) > gross "
                    f"{g_t.value} USD by more than tau {t} - different pools (C-8/U-12)")
            elif abs(g_t.value - a_t.value) <= t:
                led.award("V-01",
                          f"as of {g_t.ddate}: gross {g_t.value} USD, accumulated "
                          f"{a_t.value} USD{a_t.note} - difference within display precision "
                          f"tau={t}; the period-end net is indistinguishable from 0",
                          not_applicable=+3, elsewhere=-2)
            else:
                led.award("V-01b",
                          f"as of {g_t.ddate}: net {g_t.value - a_t.value} USD REMAINS "
                          f"(gross {g_t.value} - accumulated {a_t.value} USD) with no standard net tag",
                          elsewhere=+3, not_applicable=-3, omission=-3)

        # V-02: an explicitly tagged 0 on an observed leg at the target date
        zero_legs = [p for p in (g_t, a_t) if p is not None and p.value == 0]
        if zero_legs:
            p = zero_legs[0]
            led.award("V-02",
                      f"as of {p.ddate}: {p.tag} = 0 USD (explicitly tagged) - a tagged 0 is"
                      " an active statement, not silence",
                      not_applicable=+3, elsewhere=-3, omission=-2)

        # V-03..V-05: gross movement (needs a prior-year point)
        if g_t is not None and g_p is not None:
            t = tau(g_t.value, g_p.value)
            if g_t.value - g_p.value > t:
                led.award("V-03",
                          f"gross moved {g_p.value} USD ({g_p.ddate}) -> {g_t.value} USD "
                          f"({g_t.ddate}): an INCREASE - an acquisition occurred in the period"
                          " (U-15: impairment/sub-year lives/non-acquisition increases can defeat this)",
                          elsewhere=+3, not_applicable=-3)
            elif g_p.value - g_t.value > t:
                led.award("V-04",
                          f"gross moved {g_p.value} USD ({g_p.ddate}) -> {g_t.value} USD "
                          f"({g_t.ddate}): a DECREASE - a disposal/write-off occurred (weak:"
                          " a partial disposal is not a full one)",
                          not_applicable=+1)
            elif g_t.value > 0:
                value_notes.append(
                    f"V-05: gross unchanged at {g_t.value} USD ({g_p.ddate} -> {g_t.ddate},"
                    f" tau={t}) - values do NOT separate forms 2 and 4 here (U-9); no score")
        elif g_t is not None and g_any and g_p is None:
            value_notes.append(
                "U-10: no prior-year gross within 300-400 days - V-03/V-04/V-05 dormant;"
                " dormancy is NOT read as form 4 (C-9)")

        # V-06..V-08: accumulated-amortisation movement
        if a_t is not None and a_p is not None:
            t = tau(a_t.value, a_p.value)
            if abs(a_t.value - a_p.value) <= t and a_t.value > 0:
                led.award("V-06",
                          f"accumulated amortisation unchanged at {a_t.value} USD"
                          f"{a_t.note} ({a_p.ddate} -> {a_t.ddate}, tau={t}) - no amortisation"
                          " occurred in the period: nothing left to amortise (U-11: an"
                          " indefinite-lived pool also freezes - this rule cannot tell them apart)",
                          not_applicable=+3, elsewhere=-2)
            elif a_t.value - a_p.value > t:
                led.award("V-07",
                          f"accumulated amortisation moved {a_p.value} USD ({a_p.ddate}) -> "
                          f"{a_t.value} USD ({a_t.ddate}): an INCREASE - an amortisable balance"
                          " existed during the period (it may have been exactly exhausted at"
                          " period end, so form 4 is only mildly discounted)",
                          elsewhere=+2, not_applicable=-1)
            elif a_p.value - a_t.value > t:
                led.award("V-08",
                          f"accumulated amortisation moved {a_p.value} USD ({a_p.ddate}) -> "
                          f"{a_t.value} USD ({a_t.ddate}): a DECREASE - a cumulative account"
                          " does not shrink by itself; the underlying asset was removed",
                          not_applicable=+2, elsewhere=-1)
        elif a_t is not None and a_any and a_p is None:
            value_notes.append(
                "U-10: no prior-year accumulated amortisation within 300-400 days -"
                " V-06/V-07/V-08 dormant; dormancy is NOT read as form 4 (C-9)")

        # V-09 / V-09b: future amortisation schedule values
        sched = [f for f in obs.evidence_facts
                 if f.tag in FUTURE_AMORTIZATION_SCHEDULE_TAGS and not f.coreg
                 and f.value is not None and f.uom == "USD"]
        sched_target = [f for f in sched
                        if (d := _parse_ddate(f.ddate)) is not None
                        and target - _timedelta(days=45) <= d <= target]
        if sched_target:  # one date only: the latest in the window (V-00 step 3)
            latest = max(f.ddate for f in sched_target)
            sched_target = [f for f in sched_target if f.ddate == latest]
        # C-8: duplicate DISTINCT values for the same (tag, ddate) are a
        # conflict, never summed - summing would double-count restatements or
        # flattened dimension members.
        by_key: dict[tuple[str, str], set] = {}
        for f in sched_target:
            by_key.setdefault((f.tag, f.ddate), set()).add(f.value)
        bad_tags = set()
        for (tg, dd_), vals in by_key.items():
            if len(vals) > 1:
                bad_tags.add(tg)
                conflicts.append(
                    f"duplicate-values: schedule {tg} {dd_} carries "
                    + " vs ".join(str(v) for v in sorted(vals))
                    + " - excluded from the V-09 sum (C-8/U-14)")
        sched_target = [f for f in sched_target if f.tag not in bad_tags]
        if sched_target:
            total = sum((v for (tg, _), vals in by_key.items()
                         if tg not in bad_tags for v in vals), Decimal(0))
            dd = max(f.ddate for f in sched_target)
            if total > Decimal(1):
                led.award("V-09",
                          f"future amortisation schedule totals {total} USD (as of {dd}) -"
                          " a DIRECT statement that an unamortised balance remains at period end",
                          elsewhere=+3, not_applicable=-3, omission=-3)
            elif all(f.value == 0 for f in sched_target):
                led.award("V-09b",
                          f"future amortisation schedule explicitly 0 USD for every year (as of {dd})"
                          " - nothing left to amortise",
                          not_applicable=+3, elsewhere=-2)

        # V-10: period amortisation expense with NO balance tag at all
        if not (gross_hit or accum_hit or umbrella_hit):
            exp = [f for f in obs.evidence_facts
                   if f.tag in AMORTIZATION_EXPENSE_TAGS and not f.coreg
                   and f.value is not None and f.uom == "USD" and f.qtrs > 0
                   and (d := _parse_ddate(f.ddate)) is not None
                   and target - _timedelta(days=45) <= d <= target]
            if exp and any(f.value > Decimal(1) for f in exp):
                f = max((f for f in exp if f.value > Decimal(1)), key=lambda f: f.ddate)
                led.award("V-10",
                          f"amortisation expense {f.value} USD ({f.qtrs} quarter(s) ending"
                          f" {f.ddate}) observed with no balance tag - a balance existed to amortise",
                          elsewhere=+2, omission=-1)

        # V-11: the umbrella tag's own target value is an explicit 0
        if u_t is not None and u_t.value == 0:
            led.award("V-11",
                      f"umbrella tag {u_t.tag} = 0 USD as of {u_t.ddate} - the broader label"
                      " itself is 0, so its subset is 0 (the one case where a value overturns R-01)",
                      not_applicable=+3, elsewhere=-3)

    displayed = [
        RankedLine(form, score, tuple(led.notes.get(form, ())))
        for form, score in led.scores.items()
        if score > 0 and led.notes.get(form)
    ]
    if not displayed:
        return Opinion(status="NO_VERDICT",
                       gate_evidence="no form survived with a positive score and an observed-value line",
                       needs_human_confirmation=True, blind_spots=BLIND_SPOTS_V2,
                       dormant_rules=tuple(dormant), fired_rules=tuple(led.fired),
                       value_conflicts=tuple(conflicts), value_notes=tuple(value_notes))

    # Tie-break: descending score, then ascending Form enum (declared before
    # measurement, audit addendum s2-1 - form 2 stays ahead of form 4 on ties;
    # the truth of the tie is carried by the TIE flag, not hidden in the order).
    displayed.sort(key=lambda line: (-line.score, line.form.value))
    tie = len(displayed) >= 2 and displayed[0].score == displayed[1].score
    displayed = displayed[:MAX_DISPLAYED_FORMS]

    return Opinion(status="RANKED", ranked=tuple(displayed),
                   needs_human_confirmation=True, blind_spots=BLIND_SPOTS_V2,
                   fired_rules=tuple(led.fired), dormant_rules=tuple(dormant),
                   tie=tie, value_conflicts=tuple(conflicts),
                   value_notes=tuple(value_notes))


# ---------------------------------------------------------------------------
# v3 - homonym evidence attribution (pre-registration: docs/evidence-rules-
# preregistration-v3.md, audit: docs/evidence-rules-v3-audit-and-measurement-
# addendum.md). Grade of anything measured with this layer: post-hoc**2
# in-sample fit - the label may not be dropped.
#
# What v3 adds on top of v2 (v1 and v2 above are PRESERVED verbatim - the
# comparison runs need them):
#   R-03' exact 4-digit SIC codes with a per-code account line (concepts.py).
#   R-15  in a homonym industry, shared-element rules (R-01/R-02/R-04/R-05'/
#         R-06/R-08 and V-02..V-10) award NO form-2/form-4 weight; their
#         observation sentences are generated anyway and ATTRIBUTED to the
#         form-6 line, each giving form 6 a +1 corroboration CAPPED at +2
#         total. The negative weight each rule gave form 1 is KEPT (an
#         actively-used element means the disclosure system is alive).
#   R-16  form-6 rebuttal by asset-class axis member - DORMANT (U-2: the
#         pipeline reads no axis tags). Registered so the unreachability is
#         the document's statement, not an accident (U-16).
#   V-03' scale aligned to V-07: form2 +2, form4 -1 (was +3/-3); sentence
#         replaced - an increase proves only that the pool grew in-period.
#   V-08' scale aligned to V-04: form4 +1 (was +2).
# NO company name, CIK or accession literal in this section.
# ---------------------------------------------------------------------------

BLIND_SPOTS_V3: tuple[str, ...] = BLIND_SPOTS_V2 + (
    "U-16 form-6 rebuttal is machine-unreachable: in a homonym industry the proof that a"
    " company ALSO holds ordinary ASC 350 intangibles lives in asset-class axis members or"
    " prose, neither of which this pipeline reads (U-2) - so a homonym industry's genuine"
    " forms 2 and 4 structurally rank behind form 6 (R-16 dormant)",
)


def rank_forms_v3(obs: ObservationV2, value_layer: bool = True) -> Opinion:
    """v3 ranked opinion: v2 with R-03' exact codes, the R-15 attribution gate,
    V-03'/V-08' scale alignment, R-16 dormant, U-16 on screen.

    `value_layer=False` is the F2 OFF-run (audit addendum s2-2): the v3 NAME
    layer - R-03' and R-15 included, since R-15 works from tag names and SIC
    alone; V-01..V-11 all disabled.
    """
    concept = obs.concept
    if concept.nature != "stock":
        raise FlowConceptRejected(
            f"G-02: {concept.key} is a flow concept - tag absence carries no signal")

    seen = obs.seen
    ev_seen = frozenset(f.tag for f in obs.evidence_facts)
    conflicts: list[str] = []
    value_notes: list[str] = []
    dormant: list[str] = [
        "R-09 dimension-only disclosure (pipeline does not read axis tags)",
        "R-13 peer usage (U-8: cannot separate 'no peers' from 'cache unreadable')",
        "R-16 form-6 rebuttal by asset-class axis member (DORMANT: the pipeline reads no"
        " axis tags (U-2); until axes are loaded this rebuttal cannot fire - U-16)",
    ]

    main_hit = sorted(t for t in concept.main_tags if t in seen)
    if main_hit:
        return Opinion(status="PRESENT",
                       gate_evidence=f"standard tag {main_hit[0]} observed",
                       dormant_rules=tuple(dormant), fired_rules=("G-01",))

    if obs.unreadable_datasets:
        names = ", ".join(obs.unreadable_datasets)
        return Opinion(status="NO_VERDICT",
                       gate_evidence=f"{names} dataset lookup FAILED - not read as absence",
                       needs_human_confirmation=True, blind_spots=BLIND_SPOTS_V3,
                       dormant_rules=tuple(dormant), fired_rules=("G-03",))

    led = _Ledger()
    gross = _gross_group(concept)
    accum = _accum_group(concept)
    gross_hit = sorted(gross & seen)
    accum_hit = sorted(accum & seen)
    umbrella_hit = sorted(t for t in concept.umbrella_tags if t in seen)
    schedule_hit = sorted(FUTURE_AMORTIZATION_SCHEDULE_TAGS & (seen | ev_seen))
    expense_hit = sorted(AMORTIZATION_EXPENSE_TAGS & (seen | ev_seen))
    goodwill_hit = sorted(GOODWILL_TAGS & (seen | ev_seen))

    # --- R-15 gate state. Active exactly when R-03' fires (exact-code match). ---
    homonym_account = concept.homonym_account(obs.sic) if obs.sic else None
    r15_active = homonym_account is not None
    r15_bonus = 0            # form-6 corroboration granted via R-15, cap +2
    r15_attributed: list[str] = []

    def award(rule_id: str, line: str, *, shared: bool, **weights: int) -> None:
        """R-15 (preregistration-v3 s1-3): in a homonym industry a shared-element
        rule awards no form-2/form-4 weight; its sentence is attributed to the
        form-6 line (+1 corroboration, capped at +2 in total) and only its
        NEGATIVE form-1 weight survives. Outside the gate: the rule as written."""
        nonlocal r15_bonus
        if not (r15_active and shared):
            led.award(rule_id, line, **weights)
            return
        kept = {k: w for k, w in weights.items() if k == "omission" and w < 0}
        bonus = 1 if r15_bonus < 2 else 0
        r15_bonus += bonus
        r15_attributed.append(rule_id + ("" if bonus else " (cap +2 reached: attributed, unscored)"))
        attributed_line = (line + f" - in this industry these elements carry"
                           f" {homonym_account} (R-15 attribution)")
        led.award(rule_id, attributed_line, homonym=bonus, **kept)
        if bonus == 0:
            # the sentence must still stand on the form-6 line (nothing is hidden)
            led.notes.setdefault(Form.INDUSTRY_HOMONYM, []).append(
                f"[{rule_id}] {attributed_line}")

    # ---- name layer ----
    if umbrella_hit:
        award("R-01",
              f"umbrella tag {umbrella_hit[0]} observed - the amount sits under a broader label",
              shared=True, elsewhere=+3, omission=-3)
    if gross_hit and accum_hit:
        award("R-02",
              f"gross {gross_hit[0]} and accumulated amortisation {accum_hit[0]} both observed"
              " - the net is computable by subtraction",
              shared=True, derivable=+3, omission=-3)
    if r15_active:
        led.award("R-03'",
                  f"SIC {obs.sic} - in this industry the concept word names a different"
                  f" account: {homonym_account} (exact-code list, GROWING, not complete)",
                  homonym=+3, omission=-2)
    if accum_hit and not gross_hit and not umbrella_hit and not main_hit:
        award("R-04",
              f"accumulated amortisation {accum_hit[0]} observed, no gross tag - an amortisable"
              " asset EXISTED and was disclosed somewhere; whether a balance REMAINS is not"
              " decidable from tag names",
              shared=True, elsewhere=+2, not_applicable=+2, omission=-2)
    if gross_hit and not accum_hit and not umbrella_hit and not main_hit:
        award("R-05'",
              f"gross tag {gross_hit[0]} observed, no accumulated-amortisation tag"
              " - an intangible WAS acquired and capitalised; whether a balance remains"
              " at period end is not decided by the tag name",
              shared=True, elsewhere=+2, not_applicable=+2, omission=-2)
    if expense_hit and not (gross_hit or accum_hit or umbrella_hit):
        award("R-06",
              f"amortisation expense {expense_hit[0]} observed - a balance existed to amortise",
              shared=True, elsewhere=+2, omission=-1)
    if goodwill_hit and not (gross_hit or accum_hit or umbrella_hit or expense_hit):
        led.award("R-07",
                  f"goodwill {goodwill_hit[0]} observed, no separate intangible tag",
                  not_applicable=+1)
    if schedule_hit:
        award("R-08",
              f"future amortisation schedule tag {schedule_hit[0]} observed"
              " - an unamortised balance REMAINS at period end",
              shared=True, elsewhere=+3, not_applicable=-3, omission=-3)
    if obs.concept_evidence is False:
        led.award("R-10",
                  f"no independent evidence that {concept.key} exists in this business"
                  f"{': ' + obs.concept_evidence_source if obs.concept_evidence_source else ''}",
                  not_applicable=+3, omission=-3)
    if obs.concept_evidence is None and not led.fired:
        return Opinion(status="NO_VERDICT",
                       gate_evidence="concept existence unconfirmed - absence is not adjudicated",
                       needs_human_confirmation=True, blind_spots=BLIND_SPOTS_V3,
                       dormant_rules=tuple(dormant), fired_rules=("R-11",))
    if obs.concept_evidence is True:
        led.award("R-12",
                  "standard tag absent from face AND notes (both read successfully), yet "
                  f"{obs.concept_evidence_source or 'independent evidence says the concept exists'}",
                  omission=+2)
    if obs.peer_usage is not None:
        used, total = obs.peer_usage
        if total and used / total >= obs.peer_threshold:
            led.award("R-13",
                      f"peer SIC {obs.sic}: {used} of {total} filers use {concept.main_tags[0]}",
                      omission=+1)
        dormant = [d for d in dormant if not d.startswith("R-13")]
    if ("R-01" in led.fired or "R-02" in led.fired) and "R-12" in led.fired:
        led.fired.append("R-14")

    # ---- value layer (V-00 .. V-11, with V-03' / V-08' and the R-15 gate) ----
    target = _parse_ddate(obs.period)
    if not value_layer:
        dormant.append("V-01..V-11 value layer DISABLED (F2 OFF-run; v3 name layer incl. R-15)")
    elif not obs.value_source_ok or (not obs.facts and not obs.evidence_facts):
        dormant.append("V-01..V-11 no fact rows loaded - value layer dormant, "
                       "NOT read as form 4 (C-9)")
    elif target is None:
        dormant.append("V-01..V-11 balance-sheet date unparseable - value layer dormant (C-9)")
    else:
        g_t, g_p, g_any = _select_balance(obs.facts, gross, target, conflicts)
        a_t, a_p, a_any = _select_balance(obs.facts, accum, target, conflicts)
        u_t, _u_p, _ = _select_balance(obs.facts, frozenset(concept.umbrella_tags),
                                       target, conflicts)
        a_t = _abs_accum(a_t, conflicts)
        a_p = _abs_accum(a_p, conflicts)
        if g_t is not None and g_t.value < 0:
            conflicts.append(f"gross-negative: {g_t.tag} {g_t.ddate} = {g_t.value} - "
                             "a cumulative acquisition cost cannot be negative (C-8)")
            g_t = None
        if g_p is not None and g_p.value < 0:
            conflicts.append(f"gross-negative: {g_p.tag} {g_p.ddate} = {g_p.value} - "
                             "a cumulative acquisition cost cannot be negative (C-8)")
            g_p = None

        # V-01 / V-01b: not in the R-15 shared list (structurally absent in the
        # residual; kept verbatim so the dormancy stays the document's statement)
        if g_t is not None and a_t is not None:
            t = tau(g_t.value, a_t.value)
            if a_t.value - g_t.value > t:
                conflicts.append(
                    f"accum-exceeds-gross: {a_t.value} USD ({a_t.ddate}) > gross "
                    f"{g_t.value} USD by more than tau {t} - different pools (C-8/U-12)")
            elif abs(g_t.value - a_t.value) <= t:
                led.award("V-01",
                          f"as of {g_t.ddate}: gross {g_t.value} USD, accumulated "
                          f"{a_t.value} USD{a_t.note} - difference within display precision "
                          f"tau={t}; the period-end net is indistinguishable from 0",
                          not_applicable=+3, elsewhere=-2)
            else:
                led.award("V-01b",
                          f"as of {g_t.ddate}: net {g_t.value - a_t.value} USD REMAINS "
                          f"(gross {g_t.value} - accumulated {a_t.value} USD) with no standard net tag",
                          elsewhere=+3, not_applicable=-3, omission=-3)

        zero_legs = [p for p in (g_t, a_t) if p is not None and p.value == 0]
        if zero_legs:
            p = zero_legs[0]
            award("V-02",
                  f"as of {p.ddate}: {p.tag} = 0 USD (explicitly tagged) - a tagged 0 is"
                  " an active statement, not silence",
                  shared=True, not_applicable=+3, elsewhere=-3, omission=-2)

        if g_t is not None and g_p is not None:
            t = tau(g_t.value, g_p.value)
            if g_t.value - g_p.value > t:
                # V-03' (preregistration-v3 s2): scale aligned to V-07 (+2/-1),
                # sentence replaced - the increase proves only in-period growth.
                award("V-03'",
                      f"gross moved {g_p.value} USD ({g_p.ddate}) -> {g_t.value} USD "
                      f"({g_t.ddate}): the asset pool GREW during the period. The cause"
                      " (acquisition/translation/reclassification/correction) and the"
                      " increase's survival at period end (impairment, sub-year lives)"
                      " are not separable from values (U-15)",
                      shared=True, elsewhere=+2, not_applicable=-1)
            elif g_p.value - g_t.value > t:
                award("V-04",
                      f"gross moved {g_p.value} USD ({g_p.ddate}) -> {g_t.value} USD "
                      f"({g_t.ddate}): a DECREASE - a disposal/write-off occurred (weak:"
                      " a partial disposal is not a full one)",
                      shared=True, not_applicable=+1)
            elif g_t.value > 0:
                value_notes.append(
                    f"V-05: gross unchanged at {g_t.value} USD ({g_p.ddate} -> {g_t.ddate},"
                    f" tau={t}) - values do NOT separate forms 2 and 4 here (U-9); no score")
        elif g_t is not None and g_any and g_p is None:
            value_notes.append(
                "U-10: no prior-year gross within 300-400 days - V-03/V-04/V-05 dormant;"
                " dormancy is NOT read as form 4 (C-9)")

        if a_t is not None and a_p is not None:
            t = tau(a_t.value, a_p.value)
            if abs(a_t.value - a_p.value) <= t and a_t.value > 0:
                award("V-06",
                      f"accumulated amortisation unchanged at {a_t.value} USD"
                      f"{a_t.note} ({a_p.ddate} -> {a_t.ddate}, tau={t}) - no amortisation"
                      " occurred in the period: nothing left to amortise (U-11: an"
                      " indefinite-lived pool also freezes - this rule cannot tell them apart)",
                      shared=True, not_applicable=+3, elsewhere=-2)
            elif a_t.value - a_p.value > t:
                award("V-07",
                      f"accumulated amortisation moved {a_p.value} USD ({a_p.ddate}) -> "
                      f"{a_t.value} USD ({a_t.ddate}): an INCREASE - an amortisable balance"
                      " existed during the period (it may have been exactly exhausted at"
                      " period end, so form 4 is only mildly discounted)",
                      shared=True, elsewhere=+2, not_applicable=-1)
            elif a_p.value - a_t.value > t:
                # V-08' (preregistration-v3 s2): scale aligned to V-04 (+1).
                award("V-08'",
                      f"accumulated amortisation moved {a_p.value} USD ({a_p.ddate}) -> "
                      f"{a_t.value} USD ({a_t.ddate}): a DECREASE - a cumulative account"
                      " does not shrink by itself; the underlying asset was removed"
                      " (a partial removal is not a full one)",
                      shared=True, not_applicable=+1, elsewhere=-1)
        elif a_t is not None and a_any and a_p is None:
            value_notes.append(
                "U-10: no prior-year accumulated amortisation within 300-400 days -"
                " V-06/V-07/V-08 dormant; dormancy is NOT read as form 4 (C-9)")

        sched = [f for f in obs.evidence_facts
                 if f.tag in FUTURE_AMORTIZATION_SCHEDULE_TAGS and not f.coreg
                 and f.value is not None and f.uom == "USD"]
        sched_target = [f for f in sched
                        if (d := _parse_ddate(f.ddate)) is not None
                        and target - _timedelta(days=45) <= d <= target]
        if sched_target:
            latest = max(f.ddate for f in sched_target)
            sched_target = [f for f in sched_target if f.ddate == latest]
        by_key: dict[tuple[str, str], set] = {}
        for f in sched_target:
            by_key.setdefault((f.tag, f.ddate), set()).add(f.value)
        bad_tags = set()
        for (tg, dd_), vals in by_key.items():
            if len(vals) > 1:
                bad_tags.add(tg)
                conflicts.append(
                    f"duplicate-values: schedule {tg} {dd_} carries "
                    + " vs ".join(str(v) for v in sorted(vals))
                    + " - excluded from the V-09 sum (C-8/U-14)")
        sched_target = [f for f in sched_target if f.tag not in bad_tags]
        if sched_target:
            total = sum((v for (tg, _), vals in by_key.items()
                         if tg not in bad_tags for v in vals), Decimal(0))
            dd = max(f.ddate for f in sched_target)
            if total > Decimal(1):
                award("V-09",
                      f"future amortisation schedule totals {total} USD (as of {dd}) -"
                      " a DIRECT statement that an unamortised balance remains at period end",
                      shared=True, elsewhere=+3, not_applicable=-3, omission=-3)
            elif all(f.value == 0 for f in sched_target):
                award("V-09b",
                      f"future amortisation schedule explicitly 0 USD for every year (as of {dd})"
                      " - nothing left to amortise",
                      shared=True, not_applicable=+3, elsewhere=-2)

        if not (gross_hit or accum_hit or umbrella_hit):
            exp = [f for f in obs.evidence_facts
                   if f.tag in AMORTIZATION_EXPENSE_TAGS and not f.coreg
                   and f.value is not None and f.uom == "USD" and f.qtrs > 0
                   and (d := _parse_ddate(f.ddate)) is not None
                   and target - _timedelta(days=45) <= d <= target]
            if exp and any(f.value > Decimal(1) for f in exp):
                f = max((f for f in exp if f.value > Decimal(1)), key=lambda f: f.ddate)
                award("V-10",
                      f"amortisation expense {f.value} USD ({f.qtrs} quarter(s) ending"
                      f" {f.ddate}) observed with no balance tag - a balance existed to amortise",
                      shared=True, elsewhere=+2, omission=-1)

        if u_t is not None and u_t.value == 0:
            led.award("V-11",
                      f"umbrella tag {u_t.tag} = 0 USD as of {u_t.ddate} - the broader label"
                      " itself is 0, so its subset is 0 (the one case where a value overturns R-01)",
                      not_applicable=+3, elsewhere=-3)

    displayed = [
        RankedLine(form, score, tuple(led.notes.get(form, ())))
        for form, score in led.scores.items()
        if score > 0 and led.notes.get(form)
    ]
    if not displayed:
        return Opinion(status="NO_VERDICT",
                       gate_evidence="no form survived with a positive score and an observed-value line",
                       needs_human_confirmation=True, blind_spots=BLIND_SPOTS_V3,
                       dormant_rules=tuple(dormant), fired_rules=tuple(led.fired),
                       value_conflicts=tuple(conflicts), value_notes=tuple(value_notes),
                       r15_attributed=tuple(r15_attributed), r15_bonus=r15_bonus)

    displayed.sort(key=lambda line: (-line.score, line.form.value))
    tie = len(displayed) >= 2 and displayed[0].score == displayed[1].score
    displayed = displayed[:MAX_DISPLAYED_FORMS]

    return Opinion(status="RANKED", ranked=tuple(displayed),
                   needs_human_confirmation=True, blind_spots=BLIND_SPOTS_V3,
                   fired_rules=tuple(led.fired), dormant_rules=tuple(dormant),
                   tie=tie, value_conflicts=tuple(conflicts),
                   value_notes=tuple(value_notes),
                   r15_attributed=tuple(r15_attributed), r15_bonus=r15_bonus)


def baseline_b(obs: Observation) -> Opinion:
    """Pre-registered baseline B: 'accumulated amortisation present -> form 2, else form 1'.

    Fixed in the measurement pre-registration s2-1 as the bar the new rules must
    clear. Kept here so it is run by the same harness, not re-derived by hand.
    """
    accum_hit = sorted(_accum_group(obs.concept) & obs.seen)
    if accum_hit:
        line = RankedLine(Form.REPORTED_ELSEWHERE, 1,
                          (f"[B] accumulated amortisation {accum_hit[0]} observed",))
    else:
        line = RankedLine(Form.CANDIDATE_OMISSION, 1,
                          ("[B] no accumulated-amortisation tag observed",))
    return Opinion(status="RANKED", ranked=(line,), needs_human_confirmation=True,
                   blind_spots=BLIND_SPOTS, fired_rules=("B",))
