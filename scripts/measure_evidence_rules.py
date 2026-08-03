"""Measure the pre-registered evidence rules against the spike-4 golden census.

Plain sentence: this script joins the reproduced census (observed tags + SIC) to
the human answer key, runs `adjudicator.evidence_rules` and the pre-registered
baseline B over it, and prints G1-G4 pass/fail with the per-case table.

It is a MEASURING INSTRUMENT, not a product output (party decision 3: hit rate
first, renderer later).

Denominators, metrics and pass marks come from
`docs/evidence-rules-measurement-preregistration.md` and are NOT re-derived here.
The rule file's SHA-256 is printed first so the measurement log records which
version of the rules produced these numbers (pre-registration s5-3).

    .venv/Scripts/python.exe scripts/measure_evidence_rules.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adjudicator.concepts import resolve  # noqa: E402
from adjudicator.evidence_rules import (MAX_DISPLAYED_FORMS, Observation,  # noqa: E402
                                        baseline_b, rank_forms)
from adjudicator.verdict import Form  # noqa: E402
from tests.goldens import (M1_REPRODUCTION, MACHINE_RESOLVED_SINCE_SPIKE4,  # noqa: E402
                           SPIKE4_CENSUS)

SNAPSHOT = ROOT / "docs" / "data" / "spike4-census-reproduced.json"
RULE_FILE = ROOT / "adjudicator" / "evidence_rules.py"
CONCEPT = resolve("finite_lived_intangibles_net")

# Answer key letter -> accepted forms (measurement pre-registration s2).
# `a` counts as a hit for EITHER NOT_APPLICABLE or DERIVABLE(=0); which one is
# recorded per case.
LETTER_FORMS: dict[str, tuple[Form, ...]] = {
    "a": (Form.NOT_APPLICABLE, Form.DERIVABLE_SUBTOTAL),
    "b": (Form.REPORTED_ELSEWHERE,),
    "c": (Form.INDUSTRY_HOMONYM,),
    "d": (Form.CANDIDATE_OMISSION,),
}

HOLDOUT_NOTE = "no human has read this 10-K - holdout, reported case by case only"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_census() -> list[dict]:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))["companies"]


def match(golden_name: str, census: list[dict]) -> dict | None:
    hits = [c for c in census
            if golden_name in c["company"].upper()
            or c["company"].upper() in golden_name
            or c["company"].upper().startswith(golden_name.split()[0])]
    if len(hits) != 1:
        return None
    return hits[0]


def observe(row: dict) -> Observation:
    return Observation(
        concept=CONCEPT,
        notes_tags=frozenset(row["legs_present"]),
        sic=row["sic"],
        concept_evidence=None,          # the census carries no independent evidence field
        unreadable_datasets=(),         # all four archives were read (snapshot lineage)
        peer_usage=None,                # U-8: dormant, C-5 forbids firing
    )


def main() -> int:
    print(f"rule file      : {RULE_FILE.relative_to(ROOT)}")
    print(f"rule sha256    : {sha256(RULE_FILE)}")
    print(f"census sha256  : {sha256(SNAPSHOT)}")
    print(f"goldens sha256 : {sha256(ROOT / 'tests' / 'goldens.py')}")
    print()

    census = load_census()
    strata: dict[str, list[tuple[str, str, dict]]] = {"M": [], "H": []}
    unmatched: list[str] = []
    for name, klass, _form, reachable, _ev in SPIKE4_CENSUS:
        row = match(name, census)
        if row is None:
            unmatched.append(f"{name} ({'machine-resolved' if name in MACHINE_RESOLVED_SINCE_SPIKE4 else 'NO MATCH'})")
            continue
        strata["M" if reachable else "H"].append((name, klass, row))

    print(f"excluded from the denominator: {unmatched}")
    print(f"denominator M={len(strata['M'])} H={len(strata['H'])} "
          f"total={len(strata['M']) + len(strata['H'])} "
          f"(pre-registered: M 7, H 12, total 19 = {M1_REPRODUCTION['golden_named_reproduced']})")
    print()

    results = []
    e1 = e2 = e3 = 0
    for stratum in ("M", "H"):
        for name, klass, row in strata[stratum]:
            op = rank_forms(observe(row))
            b_op = baseline_b(observe(row))
            accepted = LETTER_FORMS[klass]
            shown = [line.form for line in op.ranked]
            top = op.top_form
            p1 = top in accepted
            rany = any(f in accepted for f in shown)
            hit_as = next((f.name for f in shown if f in accepted), "-")
            b_p1 = b_op.top_form in accepted

            if top is Form.CANDIDATE_OMISSION:
                e1 += 1
            if any(not line.observations for line in op.ranked):
                e2 += 1
            if stratum == "H" and not (op.needs_human_confirmation and op.blind_spots):
                e3 += 1
            if len(shown) > MAX_DISPLAYED_FORMS:
                print(f"!! {name}: {len(shown)} forms displayed - R@any is INVALID")

            results.append(dict(stratum=stratum, name=name, klass=klass, sic=row["sic"],
                                tags=row["legs_present"], status=op.status,
                                shown=[f.name for f in shown],
                                scores=[line.score for line in op.ranked],
                                rules=list(op.fired_rules), p1=p1, rany=rany,
                                hit_as=hit_as, b_top=b_op.top_form.name, b_p1=b_p1,
                                obs=[o for line in op.ranked for o in line.observations]))

    # holdout: reproduced but not in the answer key
    golden_rows = {id(r[2]) for s in strata.values() for r in s}
    holdout = [c for c in census if id(c) not in golden_rows]

    def rate(stratum, key):
        rows = [r for r in results if r["stratum"] == stratum]
        return sum(1 for r in rows if r[key]), len(rows)

    m_p1, m_n = rate("M", "p1")
    h_p1, h_n = rate("H", "p1")
    rany = sum(1 for r in results if r["rany"])
    b_h = sum(1 for r in results if r["stratum"] == "H" and r["b_p1"])
    b_e1_h = sum(1 for r in results if r["stratum"] == "H"
                 and r["b_top"] == "CANDIDATE_OMISSION")
    b_e1_all = sum(1 for r in results if r["b_top"] == "CANDIDATE_OMISSION")

    # E1/E2 are pre-registered over ALL 24 reproduced filings, so the 5 holdout
    # rows are folded in before the verdict is printed.
    golden_ids = {id(r[2]) for s in strata.values() for r in s}
    holdout_rows = [c for c in census if id(c) not in golden_ids]
    for row in holdout_rows:
        op = rank_forms(observe(row))
        if op.top_form is Form.CANDIDATE_OMISSION:
            e1 += 1
        if any(not line.observations for line in op.ranked):
            e2 += 1
        if baseline_b(observe(row)).top_form is Form.CANDIDATE_OMISSION:
            b_e1_all += 1

    print("=== headline (IN-SAMPLE FIT - the label may not be dropped) ===")
    print(f"G1 M P@1      : {m_p1}/{m_n}   bar 7/7      -> {'PASS' if (m_p1, m_n) == (7, 7) else 'FAIL'}")
    print(f"G2 H P@1      : {h_p1}/{h_n}  bar >=8/12   -> {'PASS' if h_p1 >= 8 else 'FAIL'}")
    print(f"G3 R@any      : {rany}/{len(results)} bar >=18/19  -> {'PASS' if rany >= 18 else 'FAIL'}")
    print(f"G4 E1={e1} E2={e2} E3={e3}  bar 0/0/0    -> {'PASS' if e1 == e2 == e3 == 0 else 'FAIL'}"
          f"   (E1/E2 over all 24 reproduced filings, E3 over H 12)")
    print(f"baseline B    : H P@1 {b_h}/{h_n} (pre-registered 4/12), "
          f"E1(H) {b_e1_h} (pre-registered 6), E1(all 24) {b_e1_all}")
    print()

    # F1 diagnostic: a 'rule' that is really a constant
    for stratum in ("M", "H"):
        rows = [r for r in results if r["stratum"] == stratum]
        counts: dict[str, int] = {}
        for r in rows:
            if r["shown"]:
                counts[r["shown"][0]] = counts.get(r["shown"][0], 0) + 1
        for form, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            flag = " <-- F1: behaves as a CONSTANT, not a rule" if n / len(rows) >= 5 / 6 else ""
            print(f"F1 {stratum}: {form} is rank 1 in {n}/{len(rows)}{flag}")
    print()

    print("=== per case ===")
    for r in results:
        mark = "OK " if r["p1"] else "MISS"
        print(f"{mark} [{r['stratum']}] {r['name']} ({r['klass']}, SIC {r['sic']}) "
              f"tags={r['tags']} -> {r['shown']} {r['scores']} rules={r['rules']} "
              f"| R@any={'Y' if r['rany'] else 'N'} as {r['hit_as']} | B={r['b_top']}")

    print()
    print("=== holdout (no letter assigned - record BEFORE anyone reads the 10-K) ===")
    for row in holdout:
        op = rank_forms(observe(row))
        print(f"{row['company']} (SIC {row['sic']}) tags={row['legs_present']} "
              f"-> {op.status} {[ (l.form.name, l.score) for l in op.ranked ]} "
              f"rules={list(op.fired_rules)}  # {HOLDOUT_NOTE}")
        for line in op.ranked:
            for o in line.observations:
                print(f"    {line.form.name} <{line.slot}>: {o}")

    json_out = ROOT / "docs" / "data" / "evidence-rules-measurement.json"
    json_out.write_text(json.dumps(
        {"rule_sha256": sha256(RULE_FILE), "results": results,
         "G1": [m_p1, m_n], "G2": [h_p1, h_n], "G3": [rany, len(results)],
         "G4": {"E1": e1, "E2": e2, "E3": e3},
         "baseline_B": {"H_P@1": [b_h, h_n], "E1_H": b_e1_h, "E1_all24": b_e1_all}},
        indent=2), encoding="utf-8")
    print(f"\nwrote {json_out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
