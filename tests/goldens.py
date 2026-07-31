"""Golden fixtures - SINGLE SOURCE (crm 4-1b pattern).

These verdicts are an ORACLE: a human opened each 10-K and judged it (spike 4,
census of 23, pre-registered classification a/b/c/d fixed before measurement).
They are not outputs of the code under test, so a test comparing code to these
can actually fail.

Mapping from spike 4's letters to the six forms:
    a (genuinely absent / fully amortized) -> NOT_APPLICABLE or DERIVABLE(=0)
    b (reported elsewhere)                 -> REPORTED_ELSEWHERE
    c (not an ASC 350 intangible)          -> INDUSTRY_HOMONYM
    d (genuine omission)                   -> CANDIDATE_OMISSION   [count: 0]

`machine_reachable` records whether the machine can reach the verdict from tags
alone. Where it is False the honest output is NO_VERDICT / candidate-with-
confirmation, never a guess - most of class (a) needs the prose read
("There were no remaining amortizable intangible assets").
"""
from __future__ import annotations

from adjudicator.verdict import Form

# (company, spike-4 class, expected form if machine-reachable, machine_reachable, evidence)
SPIKE4_CENSUS: tuple[tuple[str, str, Form | None, bool, str], ...] = (
    # --- b: reported elsewhere (8) ---
    ("STURM RUGER", "b", None, False, "Note 6 'Other Assets': patents/Marlin trade name/accum amort"),
    ("CHEMUNG FINANCIAL", "b", None, False, "'Goodwill and other intangible assets, net 21,824' combined line"),
    ("PERMA-PIPE", "b", None, False, "gross patents $2.7M, accumulated amortization ~$2.6M in prose"),
    ("INCORDEX", "b", None, False, "NOTE 4 INTANGIBLE ASSETS: website $5,000 being amortized"),
    ("ARTISAN CONSUMER GOODS", "b", None, False, "NOTE 3: acquired Paleo assets for $10,000"),
    ("VERSUS SYSTEMS", "b", None, False, "impairment $3,968,332 disclosed on an income-statement line"),
    ("IWALLET", "b", None, False, "trademark/software/website disclosed via dimensional tags"),
    ("EVA LIVE", "b", None, False, "ComputerSoftwareIntangibleAsset dimensional tag"),
    # --- a: genuinely absent / fully amortized (7) ---
    ("SPOK HOLDINGS", "a", None, False, "'no remaining amortizable intangible assets at December 31, 2024 and 2023'"),
    ("EHEALTH", "a", None, False, "gross $17.2M less accumulated $17.2M = net zero"),
    ("DLT RESOLUTION", "a", None, False, "intangible assets net 139,848 (139,848) -> zero at period end"),
    ("ERIE INDEMNITY", "a", None, False, "the word 'intangible' appears zero times in the 10-K"),
    ("ARK RESTAURANTS", "a", None, False, "all mentions are goodwill/collateral context"),
    ("KNOW LABS", "a", None, False, "deferred tax table shows 'Intangibles - -' (zero)"),
    ("NEWTON GOLF", "a", None, False, "only 'non-amortizing intangible assets' mentioned"),
    # --- c: not an ASC 350 intangible - industry homonym (7) ---
    ("MEDICAL PROPERTIES TRUST", "c", Form.INDUSTRY_HOMONYM, True, "SIC 6798 REIT: in-place/above-below-market lease intangible"),
    ("BRIXMOR", "c", Form.INDUSTRY_HOMONYM, True, "SIC 6798 REIT: ASC 805 acquisition allocation"),
    ("CARETRUST", "c", Form.INDUSTRY_HOMONYM, True, "SIC 6798 REIT: ASC 805 acquisition allocation"),
    ("JLL INCOME PROPERTY", "c", Form.INDUSTRY_HOMONYM, True, "SIC 6798 REIT: ASC 805 acquisition allocation"),
    ("AEI INCOME & GROWTH FUND", "c", Form.INDUSTRY_HOMONYM, True, "SIC 6500 real estate: same allocation"),
    ("FIRST TRINITY FINANCIAL", "c", Form.INDUSTRY_HOMONYM, True, "SIC 6311 insurance: DAC / VOBA"),
    ("PORTLAND GENERAL ELECTRIC", "c", Form.INDUSTRY_HOMONYM, True, "SIC 4911 utility: 'intangible plant' is a fixed-asset class"),
    # --- d: genuine omission --- (none; the census found zero)
)

# The census headline, pinned so a silent drift in the population is visible.
SPIKE4_TOTALS = {"companies": 23, "b": 8, "a": 7, "c": 7, "d": 0, "undetermined": 1}

# SIC codes the census proved to be homonym industries for this concept.
SPIKE4_HOMONYM_SICS = ("6798", "6500", "6311", "4911")


# Measured 2026-07-31 (M1): with the corrected tag vocabulary these three
# class-b firms are resolved by the MACHINE and therefore leave the residual.
# Leaving it is correct - both routes say "not an omission" - but the form
# label differs from the human's letter, so it is recorded, not hidden.
MACHINE_RESOLVED_SINCE_SPIKE4 = {
    "IWALLET": "IntangibleAssetsGrossExcludingGoodwill + accumulated amortization -> derivable",
    "VERSUS SYSTEMS": "OtherIntangibleAssetsNet -> reported elsewhere",
    "ARTISAN CONSUMER GOODS": "resolved outside the 2025q1 archive by the widened vocabulary",
}

# The reproduction is NOT population-identical to spike 4 (26 filings / 23 firms)
# because spike 4's machine used a narrower tag vocabulary. Pinned so drift is visible.
M1_REPRODUCTION = {"companies": 24, "golden_named_reproduced": 19,
                   "machine_resolved": 3, "new_residuals": 5}
