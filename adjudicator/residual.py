"""Residual population selection - the machine half of the adjudicator.

"Residual" = filings where the concept's standard NET tag is absent from both
datasets AND the value is not derivable from tagged components. This is the
per-concept absence definition (contract 1) applied to a population; the
six-form verdict then explains each survivor.

The census this reproduces (spike 4): finite-lived intangibles, 2024Q3-2025Q2,
10-K only - 26 filings across 23 companies. One filing per company (latest
period) goes to adjudication.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from adjudicator.concepts import Concept

_FORM = "10-K"


@dataclass(frozen=True)
class ResidualFiling:
    cik: int
    accession: str
    company: str
    sic: str
    period: str
    quarter: str
    legs_present: tuple[str, ...]  # which component tags WERE tagged


def tags_of_interest(concept: Concept) -> frozenset[str]:
    parts = tuple(t for g in concept.part_groups for t in g)
    return frozenset(concept.main_tags + concept.umbrella_tags + parts)


def find_residuals(sub: pd.DataFrame, num: pd.DataFrame, concept: Concept,
                   quarter: str) -> list[ResidualFiling]:
    """Filings whose net-family tags are absent and whose components are incomplete.

    Excluded by construction:
      - net or umbrella tag present  -> the amount is in a standard place (forms 0/2)
      - ALL component tags present   -> the net is derivable, not hidden (form 3)
    """
    net_family = set(concept.main_tags) | set(concept.umbrella_tags)
    groups = [set(g) for g in concept.part_groups]

    tenk = sub[sub["form"] == _FORM]
    present = (num[num["adsh"].isin(set(tenk["adsh"]))]
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
        out.append(ResidualFiling(
            cik=int(row["cik"]), accession=row["adsh"], company=row["name"],
            sic=str(row["sic"] or ""), period=str(row["period"] or ""), quarter=quarter,
            legs_present=tuple(sorted(legs)),
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
