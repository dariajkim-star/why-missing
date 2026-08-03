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
    # v3 R-03': EXACT 4-digit SIC codes where the concept word means something
    # else (form 6), each with the one-line account it names in that industry.
    # GROWING list (U-7): exact codes trade over-inclusion (the 6411 class) for
    # a larger risk of unregistered-code silence. Never claimed complete.
    homonym_sic_accounts: tuple[tuple[str, str], ...] = ()

    @property
    def homonym_sic_prefixes(self) -> tuple[str, ...]:
        """Exact 4-digit codes. SICs are 4 digits, so the pre-existing
        `startswith` call sites (verdict.py, v1/v2 rules) become exact matching
        without touching the judgement logic - party decision 1 preserved."""
        return tuple(code for code, _ in self.homonym_sic_accounts)

    def homonym_account(self, sic: str) -> str | None:
        """The account the concept word names in this SIC, or None."""
        for code, account in self.homonym_sic_accounts:
            if sic == code:
                return account
        return None


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
            # v3 R-03' promotion of the old prefixes ("13", "1382", "1000"):
            # mineral leases are NOT right-of-use leases (ASC 842-10-15-1
            # scopes out mineral exploration rights).
            homonym_sic_accounts=(
                ("1311", "mineral lease - a mineral right, not a right-of-use lease (ASC 932)"),
                ("1381", "mineral lease - a mineral right, not a right-of-use lease (ASC 932)"),
                ("1382", "mineral lease - a mineral right, not a right-of-use lease (ASC 932)"),
                ("1389", "mineral lease - a mineral right, not a right-of-use lease (ASC 932)"),
                ("1000", "mineral lease - a mineral right, not a right-of-use lease (ASC 930)"),
                ("1040", "mineral lease - a mineral right, not a right-of-use lease (ASC 930)"),
                ("1090", "mineral lease - a mineral right, not a right-of-use lease (ASC 930)"),
            ),
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
            # v3 R-03' (preregistration-v3 s3): exact 4-digit codes, one account
            # line per code, derived from the accounting standard of the
            # industry FAMILY - not an enumeration of the answer key (only 4 of
            # these 22 codes occur in the sample). 6411 (insurance agents &
            # brokers) is EXCLUDED: brokers do not underwrite, so they hold no
            # DAC/VOBA - the old "641" prefix was over-inclusive.
            homonym_sic_accounts=(
                # real estate operators/investors - acquired in-place lease and
                # above/below-market lease intangibles (ASC 805-20-25-10)
                ("6500", "acquired-property in-place lease intangibles (ASC 805-20-25-10)"),
                ("6512", "acquired-property in-place lease intangibles (ASC 805-20-25-10)"),
                ("6513", "acquired-property in-place lease intangibles (ASC 805-20-25-10)"),
                ("6514", "acquired-property in-place lease intangibles (ASC 805-20-25-10)"),
                ("6519", "acquired-property in-place lease intangibles (ASC 805-20-25-10)"),
                # audit 1-2: 6531/6552 carry an UNREINFORCED accounting line -
                # firings must be named and their cases quoted only with that flag
                ("6531", "lease intangibles of managed real estate (accounting basis UNREINFORCED - audit 1-2)"),
                ("6552", "acquired-property lease intangibles (accounting basis UNREINFORCED - audit 1-2)"),
                ("6798", "acquired-property in-place lease and above/below-market lease intangibles (ASC 805-20-25-10)"),
                # insurance UNDERWRITERS - DAC / VOBA (ASC 944-30); 6411 excluded
                ("6311", "deferred acquisition costs / VOBA (ASC 944-30)"),
                ("6321", "deferred acquisition costs / VOBA (ASC 944-30)"),
                ("6324", "deferred acquisition costs (ASC 944-30)"),
                ("6331", "deferred acquisition costs (ASC 944-30)"),
                ("6351", "deferred acquisition costs (ASC 944-30)"),
                ("6361", "deferred acquisition costs (ASC 944-30)"),
                ("6399", "deferred acquisition costs (ASC 944-30)"),
                # rate-regulated utilities - intangible plant, a utility-plant
                # component (ASC 980; 4941 cited on ASC 980 only - audit 1-2)
                ("4911", "intangible plant, a utility-plant component (ASC 980)"),
                ("4922", "intangible plant, a utility-plant component (ASC 980)"),
                ("4923", "intangible plant, a utility-plant component (ASC 980)"),
                ("4924", "intangible plant, a utility-plant component (ASC 980)"),
                ("4931", "intangible plant, a utility-plant component (ASC 980)"),
                ("4932", "intangible plant, a utility-plant component (ASC 980)"),
                ("4941", "intangible plant, a utility-plant component (ASC 980)"),
            ),
        ),
        Concept(
            key="goodwill",
            nature="stock",
            main_tags=("Goodwill",),
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
