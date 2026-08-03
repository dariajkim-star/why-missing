"""Residual population selection - the machine half of the adjudicator.

"Residual" = filings where the concept's standard NET tag is absent from both
datasets AND the value is not derivable from tagged components. This is the
per-concept absence definition (contract 1) applied to a population; the
six-form verdict then explains each survivor.

The census this reproduces (spike 4): finite-lived intangibles, 2024Q3-2025Q2,
10-K only - 26 filings across 23 companies. One filing per company (latest
period) goes to adjudication.

v2 (preregistration-v2 s8): the residual now carries the FACT ROWS, not just
tag names. Three contracts implemented here:
  C-6  an empty value cell is UNOBSERVED, never 0 (no fillna(0), ever);
  the amounts are Decimal, never float (tau must not depend on binary error);
  facts are NOT filtered here - ddate/qtrs/uom selection is an accounting
  judgement and belongs to the rule layer (V-00), where it is auditable.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import pandas as pd

from adjudicator.concepts import Concept

_FORM = "10-K"

_FACT_COLS = ("ddate", "qtrs", "uom", "coreg", "value")


@dataclass(frozen=True)
class TaggedFact:
    """One num.tsv row, kept raw. Selection happens in the rule layer (V-00)."""

    tag: str
    ddate: str            # YYYYMMDD as filed - NOT normalised (source preserved)
    qtrs: int             # 0 = instant (balance). Balance rules accept only 0
    uom: str              # anything but "USD" forbids arithmetic (C-8)
    coreg: str            # "" = consolidated parent; non-empty rows are excluded
    value: Decimal | None  # None = empty cell or parse failure -> UNOBSERVED, not 0 (C-6)
    value_raw: str        # the source string, for tracing why value is None


@dataclass(frozen=True)
class ResidualFiling:
    cik: int
    accession: str
    company: str
    sic: str
    period: str                       # target-ddate anchor (V-00 step 2)
    quarter: str
    legs_present: tuple[str, ...]     # kept as a field - existing tests construct it
    facts: tuple[TaggedFact, ...] = ()          # ALL rows of interest tags, unfiltered
    evidence_facts: tuple[TaggedFact, ...] = ()  # schedule/expense/goodwill (s4-4 split)
    value_source_ok: bool = False     # did num carry the value columns at all (C-9)


def filter_tags(concept: Concept) -> frozenset[str]:
    """Tags used to SELECT the residual population (main + umbrella + parts)."""
    parts = tuple(t for g in concept.part_groups for t in g)
    return frozenset(concept.main_tags + concept.umbrella_tags + parts)


def tags_of_interest(concept: Concept) -> frozenset[str]:
    """Kept for callers of the v1 name: the residual-selection tag set."""
    return filter_tags(concept)


def evidence_tags() -> frozenset[str]:
    """Tags read as EVIDENCE only - they never affect residual selection (s4-4).

    Before this split the pipeline never loaded these rows at all, so R-06/R-08
    'fired 0 times' meant 'we did not look', not 'no such company' (contract 5).
    """
    from adjudicator.evidence_rules import (AMORTIZATION_EXPENSE_TAGS,
                                            FUTURE_AMORTIZATION_SCHEDULE_TAGS,
                                            GOODWILL_TAGS)
    return frozenset(AMORTIZATION_EXPENSE_TAGS | FUTURE_AMORTIZATION_SCHEDULE_TAGS
                     | GOODWILL_TAGS)


def load_tags(concept: Concept) -> frozenset[str]:
    """What to hand to sec.load_quarter: the union of filter and evidence tags."""
    return filter_tags(concept) | evidence_tags()


def _parse_value(raw: object) -> tuple[Decimal | None, str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None, ""
    s = str(raw).strip()
    if not s or s.lower() == "nan":
        return None, s
    try:
        return Decimal(s), s
    except InvalidOperation:
        return None, s


def _facts_from_rows(rows: pd.DataFrame) -> tuple[TaggedFact, ...]:
    out = []
    for _, r in rows.iterrows():
        value, raw = _parse_value(r.get("value"))
        try:
            qtrs = int(Decimal(str(r.get("qtrs") or "0").strip() or "0"))
        except InvalidOperation:
            qtrs = -1  # unparseable duration: never accepted as a balance row
        coreg = r.get("coreg")
        coreg = "" if coreg is None or (isinstance(coreg, float) and pd.isna(coreg)) \
            else str(coreg).strip()
        if coreg.lower() == "nan":
            coreg = ""
        out.append(TaggedFact(
            tag=str(r["tag"]), ddate=str(r.get("ddate") or "").strip(),
            qtrs=qtrs, uom=str(r.get("uom") or "").strip(), coreg=coreg,
            value=value, value_raw=raw,
        ))
    # exact duplicate rows collapse; DIFFERENT values for the same key survive
    # so the rule layer can flag them as VALUE_CONFLICT (C-8), not pick one.
    seen: set[tuple] = set()
    unique = []
    for f in out:
        key = (f.tag, f.ddate, f.qtrs, f.uom, f.coreg, f.value_raw)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return tuple(unique)


def find_residuals(sub: pd.DataFrame, num: pd.DataFrame, concept: Concept,
                   quarter: str) -> list[ResidualFiling]:
    """Filings whose net-family tags are absent and whose components are incomplete.

    Excluded by construction:
      - net or umbrella tag present  -> the amount is in a standard place (forms 0/2)
      - ALL component tags present   -> the net is derivable, not hidden (form 3)

    SELECTION uses filter_tags only. Evidence tags (schedule/expense/goodwill)
    never decide membership - they ride along as evidence_facts (s4-4).
    """
    net_family = set(concept.main_tags) | set(concept.umbrella_tags)
    groups = [set(g) for g in concept.part_groups]
    filt = filter_tags(concept)
    ev_tags = evidence_tags()
    has_value_cols = all(c in num.columns for c in _FACT_COLS)

    tenk = sub[sub["form"] == _FORM]
    num_filt = num[num["tag"].isin(filt)]
    present = (num_filt[num_filt["adsh"].isin(set(tenk["adsh"]))]
               .groupby("adsh")["tag"].agg(lambda s: frozenset(s)))

    out: list[ResidualFiling] = []
    for _, row in tenk.iterrows():
        seen = present.get(row["adsh"], frozenset())
        if not seen:
            continue  # the concept is not mentioned at all - not this concept's residual
        if seen & net_family:
            continue
        legs = seen & {t for g in groups for t in g}
        if not legs or all(g & seen for g in groups):
            continue  # no component, or every leg tagged (derivable)
        facts: tuple[TaggedFact, ...] = ()
        ev_facts: tuple[TaggedFact, ...] = ()
        if has_value_cols:
            mine = num[num["adsh"] == row["adsh"]]
            facts = _facts_from_rows(mine[mine["tag"].isin(filt)])
            ev_facts = _facts_from_rows(mine[mine["tag"].isin(ev_tags)])
        out.append(ResidualFiling(
            cik=int(row["cik"]), accession=row["adsh"], company=row["name"],
            sic=str(row["sic"] or ""), period=str(row["period"] or ""), quarter=quarter,
            legs_present=tuple(sorted(legs)),
            facts=facts, evidence_facts=ev_facts, value_source_ok=has_value_cols,
        ))
    return out


def one_per_company(filings: list[ResidualFiling]) -> list[ResidualFiling]:
    """Latest period per company (spike 4 procedure step 4)."""
    best: dict[int, ResidualFiling] = {}
    for f in filings:
        prev = best.get(f.cik)
        if prev is None or (f.period, f.quarter) > (prev.period, prev.quarter):
            best[f.cik] = f
    return sorted(best.values(), key=lambda f: f.cik)
