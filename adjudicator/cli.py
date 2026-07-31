"""why-missing - answer "why is this amount not in standard XBRL?" (M3).

    python -m adjudicator.cli RGR finite_lived_intangibles_net

The report always names the filing it read (contract 9 clause 1) and, on a
candidate verdict, states what this door cannot see. Peer context appears only
when a cached bulk quarter can supply it; otherwise it is declared absent
rather than invented (contract 6's refusal, applied to context).
"""
from __future__ import annotations

import argparse
import sys
import time

from adjudicator import concepts, live, residual
from adjudicator.verdict import Form, adjudicate

# Stated wherever it matters, never only in a doc.
BLIND_SPOTS = (
    "dimensional tags (values tagged by intangible class or lease class) are not "
    "visible through this door",
    "prose-only disclosure (e.g. inside an 'Other Assets' note) is not visible",
)
CAVEAT = (
    "This tool's detection power could not be validated (positive-control sample "
    "too small, spike 5). A candidate is a question for a human, not a finding."
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="why-missing", description=__doc__)
    p.add_argument("company", help="ticker, CIK, or a distinctive part of the name")
    p.add_argument("concept", nargs="?", default="finite_lived_intangibles_net",
                   help=f"one of: {', '.join(concepts.known_stock_concepts())}")
    p.add_argument("--evidence", choices=("yes", "no", "unknown"), default="yes",
                   help="does independent evidence say the concept exists here? "
                        "(default yes: the caller is asking BECAUSE they expect it)")
    return p


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    started = time.monotonic()

    try:
        concept = concepts.resolve(args.concept)
    except concepts.FlowConceptRejected as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    except KeyError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2

    try:
        cik, _name = live.resolve_company(args.company)
        filing = live.latest_annual(cik)
        tags = live.tags_reported_in(filing, residual.tags_of_interest(concept))
    except (live.NotFound, LookupError) as e:
        print(f"cannot answer: {e}", file=sys.stderr)
        return 1

    verdict = adjudicate(
        concept,
        face_tags=frozenset(), notes_tags=tags,  # companyfacts spans both datasets
        sic=filing.sic,
        concept_evidence={"yes": True, "no": False, "unknown": None}[args.evidence],
    )

    elapsed = time.monotonic() - started
    print(f"{filing.company}  (CIK {filing.identity.cik}, SIC {filing.sic})")
    print(f"  filing   : {filing.form} {filing.identity.accession} "
          f"filed {filing.filed}, period {filing.period}")
    print(f"  concept  : {concept.key}")
    print(f"  tags seen: {', '.join(sorted(tags)) or '(none of the concept tag family)'}")
    print(f"  verdict  : {verdict.render()}")
    if verdict.form is Form.CANDIDATE_OMISSION:
        for blind in BLIND_SPOTS:
            print(f"  ! blind  : {blind}")
        print(f"  ! caveat : {CAVEAT}")
    print("  peer ctx : none (no cached bulk quarter) - this verdict rests on "
          "one filing, not on peer comparison")
    print(f"  elapsed  : {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
