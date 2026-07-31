"""Concept registry - contract 1 (per-concept absence definition).

Only STOCK (balance) concepts are admitted. Flow concepts are rejected at the
door: a live arrangement can legitimately have a zero current-period amount,
and XBRL rarely tags a zero, so "absent tag" carries no signal (form 5,
legitimate zero - spike 2, Thunder Mountain Gold). This is not a limitation
note; it is an input contract.

Industry-homonym exclusions (form 6) are per concept and labeled GROWING, not
complete - spike 3-V/4 kept finding new collisions (utility intangible plant
was not in anyone's pre-registration).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Concept:
    key: str
    nature: str  # "stock" | "flow"
    main_tags: tuple[str, ...]  # any present => the amount IS in its standard place
    # Component GROUPS. The subtotal is derivable when EVERY group has at least
    # one tag present - groups model synonyms (a gross leg can be tagged either
    # FiniteLivedIntangibleAssetsGross or IntangibleAssetsGrossExcludingGoodwill),
    # while separate groups model the distinct legs of the arithmetic.
    part_groups: tuple[tuple[str, ...], ...] = ()
    umbrella_tags: tuple[str, ...] = ()  # any present => reported elsewhere (form 2)
    # SIC prefixes where the concept word means something else (form 6). GROWING list.
    homonym_sic_prefixes: tuple[str, ...] = ()


_REGISTRY: dict[str, Concept] = {
    c.key: c
    for c in (
        Concept(
            key="operating_lease_liability",
            nature="stock",
            main_tags=("OperatingLeaseLiability",),
            part_groups=(("OperatingLeaseLiabilityCurrent",),
                         ("OperatingLeaseLiabilityNoncurrent",)),
            umbrella_tags=(),  # spike 1: no umbrella tag exists for this concept (measured)
            # mineral leases / BOEM right-of-use (spike 3-V, 42% of the sample)
            homonym_sic_prefixes=("13", "1382", "1000"),
        ),
        Concept(
            key="finite_lived_intangibles_net",
            nature="stock",
            main_tags=("FiniteLivedIntangibleAssetsNet",),
            part_groups=(
                # gross leg - synonyms (IntangibleAssetsGrossExcludingGoodwill
                # found on Trex by the M1 reproduction)
                ("FiniteLivedIntangibleAssetsGross", "IntangibleAssetsGrossExcludingGoodwill"),
                ("FiniteLivedIntangibleAssetsAccumulatedAmortization",),
            ),
            # GROWING list. The last three were added 2026-07-31 by the M1 golden
            # reproduction, which surfaced HCA / Trex / Lazard as false residuals -
            # the third time this project's tag list was caught incomplete, and the
            # fourth consecutive hit for the big-company self-check rule. The
            # aggregate-with-goodwill shape is oracle-sanctioned: the spike 4 census
            # classified Chemung Financial's "Goodwill and other intangible assets,
            # net" line as class b (reported elsewhere), not as an omission.
            umbrella_tags=(
                "IntangibleAssetsNetExcludingGoodwill",
                "IntangibleAssetsNetIncludingGoodwill",
                "OtherIntangibleAssetsNet",
            ),
            # REIT in-place lease intangibles / insurance DAC-VOBA / utility
            # intangible plant (spike 4 - the sixth form's widest expansion).
            # 6500 added 2026-07-31: the census's AEI Income & Growth Fund sits
            # there, and the registry had drifted behind the measured census.
            homonym_sic_prefixes=("6798", "6500", "631", "641", "4911"),
        ),
        Concept(
            key="goodwill",
            nature="stock",
            main_tags=("Goodwill",),
            homonym_sic_prefixes=(),
        ),
        # Registered ONLY so the rejection is by design, not by absence of an entry.
        Concept(key="share_based_compensation", nature="flow",
                main_tags=("ShareBasedCompensation",)),
    )
}


class FlowConceptRejected(ValueError):
    """Raised at the input door - not downstream where the harm is invisible."""


def resolve(key: str) -> Concept:
    """Return the concept, refusing flow concepts with the reason spelled out."""
    try:
        c = _REGISTRY[key]
    except KeyError:
        raise KeyError(f"unknown concept {key!r}; known: {sorted(_REGISTRY)}") from None
    if c.nature != "stock":
        raise FlowConceptRejected(
            f"{key} is a FLOW concept: a live arrangement can have a legitimate "
            f"zero this period and XBRL rarely tags zeros, so tag absence carries "
            f"no signal (form 5). Stock concepts only."
        )
    return c


def known_stock_concepts() -> list[str]:
    return sorted(k for k, c in _REGISTRY.items() if c.nature == "stock")
