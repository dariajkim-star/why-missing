"""Second measurement - v2 evidence rules (name layer w/ R-05' + value layer V-00..V-11).

Grade of every number printed here: POST-HOC IN-SAMPLE FIT (preregistration-v2
header). The label may not be dropped when quoting.

Procedure is bound by docs/evidence-rules-v2-audit-and-measurement-addendum.md:
  s2-1 tie-break: descending score, then ascending Form enum (form 2 first) - unchanged;
  s2-2 F2: OFF-run = v2 name layer only (R-05' kept), ON-run = full v2;
  s2-3 F3: count of rank-1 decided by tie-break; P@1 split tie/non-tie;
  s2-4 named tables: VALUE_CONFLICT, U-10, plus V-03/V-06/V-08 firings and
       tau-decisive cases; V-06's indefinite-lived co-tag flag.

    .venv/Scripts/python.exe scripts/measure_evidence_rules_v2.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adjudicator.concepts import resolve  # noqa: E402
from adjudicator.evidence_rules import (MAX_DISPLAYED_FORMS, ObservationV2,  # noqa: E402
                                        rank_forms_v2)
from adjudicator.residual import TaggedFact  # noqa: E402
from adjudicator.verdict import Form  # noqa: E402
from tests.goldens import MACHINE_RESOLVED_SINCE_SPIKE4, SPIKE4_CENSUS  # noqa: E402

SNAPSHOT = ROOT / "docs" / "data" / "spike4-census-with-values.json"
CONCEPT = resolve("finite_lived_intangibles_net")

LETTER_FORMS: dict[str, tuple[Form, ...]] = {
    "a": (Form.NOT_APPLICABLE, Form.DERIVABLE_SUBTOTAL),
    "b": (Form.REPORTED_ELSEWHERE,),
    "c": (Form.INDUSTRY_HOMONYM,),
    "d": (Form.CANDIDATE_OMISSION,),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_census() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def match(golden_name: str, census: list[dict]) -> dict | None:
    hits = [c for c in census
            if golden_name in c["company"].upper()
            or c["company"].upper() in golden_name
            or c["company"].upper().startswith(golden_name.split()[0])]
    if len(hits) != 1:
        return None
    return hits[0]


def facts_from_json(rows: list[dict]) -> tuple[TaggedFact, ...]:
    return tuple(TaggedFact(
        tag=r["tag"], ddate=r["ddate"], qtrs=r["qtrs"], uom=r["uom"], coreg=r["coreg"],
        value=None if r["value"] is None else Decimal(r["value"]),
        value_raw=r["value_raw"]) for r in rows)


def observe(row: dict) -> ObservationV2:
    return ObservationV2(
        concept=CONCEPT,
        notes_tags=frozenset(row["legs_present"]),
        sic=row["sic"],
        concept_evidence=None,
        unreadable_datasets=(),
        peer_usage=None,
        facts=facts_from_json(row["facts"]),
        evidence_facts=facts_from_json(row["evidence_facts"]),
        period=row["period"],
        value_source_ok=row["value_source_ok"],
    )


def main() -> int:
    print("GRADE: post-hoc in-sample fit - the label may not be dropped")
    for f in ("adjudicator/evidence_rules.py", "adjudicator/residual.py",
              "tests/goldens.py"):
        print(f"{f} sha256 : {sha256(ROOT / f)}")
    print(f"census sha256 : {sha256(SNAPSHOT)}")
    snap = load_census()
    for name, h in snap["cache_archives_sha256"].items():
        print(f"cache {name} sha256 : {h}")
    print()

    census = snap["companies"]
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
          f"total={len(strata['M']) + len(strata['H'])}")
    print()

    results = []
    e1 = e2 = e3 = 0
    f2_changes = []
    for stratum in ("M", "H"):
        for name, klass, row in strata[stratum]:
            obs = observe(row)
            on = rank_forms_v2(obs, value_layer=True)
            off = rank_forms_v2(obs, value_layer=False)
            accepted = LETTER_FORMS[klass]
            shown = [line.form for line in on.ranked]
            top = on.top_form
            p1 = top in accepted
            rany = any(f in accepted for f in shown)
            hit_as = next((f.name for f in shown if f in accepted), "-")

            if top is Form.CANDIDATE_OMISSION:
                e1 += 1
            if any(not line.observations for line in on.ranked):
                e2 += 1
            if stratum == "H" and not (on.needs_human_confirmation and on.blind_spots):
                e3 += 1
            if len(shown) > MAX_DISPLAYED_FORMS:
                print(f"!! {name}: {len(shown)} forms displayed - R@any is INVALID")
            if on.top_form != off.top_form:
                f2_changes.append(dict(
                    name=name, klass=klass, off=off.top_form.name if off.top_form else None,
                    on=on.top_form.name if on.top_form else None,
                    v_rules=[r for r in on.fired_rules if r.startswith("V-")]))

            results.append(dict(
                stratum=stratum, name=name, klass=klass, sic=row["sic"],
                tags=row["legs_present"], status=on.status,
                shown=[f.name for f in shown], scores=[l.score for l in on.ranked],
                rules=list(on.fired_rules), p1=p1, rany=rany, hit_as=hit_as,
                tie=on.tie, off_top=off.top_form.name if off.top_form else None,
                conflicts=list(on.value_conflicts), value_notes=list(on.value_notes),
                obs=[o for l in on.ranked for o in l.observations]))

    golden_ids = {id(r[2]) for s in strata.values() for r in s}
    holdout = [c for c in census if id(c) not in golden_ids]

    def rate(stratum, key):
        rows = [r for r in results if r["stratum"] == stratum]
        return sum(1 for r in rows if r[key]), len(rows)

    m_p1, m_n = rate("M", "p1")
    h_p1, h_n = rate("H", "p1")
    rany = sum(1 for r in results if r["rany"])

    # E1/E2 fold in the 5 holdout rows (pre-registration: over all 24)
    for row in holdout:
        op = rank_forms_v2(observe(row))
        if op.top_form is Form.CANDIDATE_OMISSION:
            e1 += 1
        if any(not line.observations for line in op.ranked):
            e2 += 1

    print("=== headline (POST-HOC IN-SAMPLE FIT - label may not be dropped) ===")
    print(f"G1 M P@1      : {m_p1}/{m_n}   bar 7/7      -> {'PASS' if (m_p1, m_n) == (7, 7) else 'FAIL'}")
    print(f"G2 H P@1      : {h_p1}/{h_n}  bar >=8/12   -> {'PASS' if h_p1 >= 8 else 'FAIL'}")
    print(f"G3 R@any      : {rany}/{len(results)} bar >=18/19  -> {'PASS' if rany >= 18 else 'FAIL'}")
    print(f"G4 E1={e1} E2={e2} E3={e3}  bar 0/0/0    -> {'PASS' if e1 == e2 == e3 == 0 else 'FAIL'}")
    print()

    # F1 diagnostic
    for stratum in ("M", "H"):
        rows = [r for r in results if r["stratum"] == stratum]
        counts: dict[str, int] = {}
        for r in rows:
            if r["shown"]:
                counts[r["shown"][0]] = counts.get(r["shown"][0], 0) + 1
        for form, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            flag = " <-- F1: behaves as a CONSTANT" if n / len(rows) >= 5 / 6 else ""
            print(f"F1 {stratum}: {form} is rank 1 in {n}/{len(rows)}{flag}")
    print()

    # F2: value-layer contribution (0 => the value layer contributed NOTHING)
    print(f"F2 (rank-1 changed by the value layer, denominator 19): {len(f2_changes)}")
    for c in f2_changes:
        print(f"  F2 {c['name']} ({c['klass']}): OFF {c['off']} -> ON {c['on']} via {c['v_rules']}")
    if not f2_changes:
        print("  F2 = 0: the value layer is judged NON-CONTRIBUTING; any P@1 movement"
              " may not be attributed to values (v2 s7-F2)")
    print()

    # F3: rank-1 decided by tie-break; P@1 split tie / non-tie
    ties = [r for r in results if r["tie"]]
    print(f"F3 (rank-1 decided by tie-break): {len(ties)}/19")
    for stratum in ("M", "H"):
        for flag, label in ((True, "tie"), (False, "non-tie")):
            rows = [r for r in results if r["stratum"] == stratum and r["tie"] is flag]
            if rows:
                hit = sum(1 for r in rows if r["p1"])
                print(f"  P@1_{label}({stratum}) = {hit}/{len(rows)}")
    print()

    print("=== per case ===")
    for r in results:
        mark = "OK " if r["p1"] else "MISS"
        tie = " TIE" if r["tie"] else ""
        print(f"{mark} [{r['stratum']}] {r['name']} ({r['klass']}, SIC {r['sic']}) "
              f"tags={r['tags']} -> {r['shown']} {r['scores']}{tie} rules={r['rules']} "
              f"| off_top={r['off_top']} R@any={'Y' if r['rany'] else 'N'} as {r['hit_as']}")
        for o in r["obs"]:
            print(f"      {o}")
        for c in r["conflicts"]:
            print(f"      VALUE_CONFLICT: {c}")
        for nvn in r["value_notes"]:
            print(f"      note: {nvn}")
    print()

    # named tables (audit s2-4)
    print("=== VALUE_CONFLICT (named, separate from the per-form table) ===")
    any_c = False
    for r in results:
        for c in r["conflicts"]:
            any_c = True
            print(f"  {r['name']}: {c}")
    if not any_c:
        print("  none")
    print()
    print("=== U-10 (no comparison date -> movement rules dormant, named) ===")
    any_u = False
    for r in results:
        for nvn in r["value_notes"]:
            if nvn.startswith("U-10"):
                any_u = True
                dd = sorted({f["ddate"] for c2 in census if c2["company"].upper() == r["name"]
                             or r["name"] in c2["company"].upper() for f in c2["facts"]})
                print(f"  {r['name']}: {nvn} | ddates held: {dd}")
    if not any_u:
        print("  none")
    print()
    print("=== V-03 / V-06 / V-08 firings (named, audit conditions 1-2b/1-3a/1-5) ===")
    for rule in ("V-03", "V-06", "V-08"):
        rows = [r for r in results if rule in r["rules"]]
        print(f"  {rule}: {len(rows)} firing(s)")
        for r in rows:
            print(f"    {r['name']} ({r['klass']}) " + "; ".join(
                o for o in r["obs"] if f"[{rule}]" in o))
            if rule == "V-06":
                print("      indefinite-lived co-tag flag: UNOBSERVABLE - the pipeline"
                      " does not load IndefiniteLivedIntangibleAssets* tags; per the"
                      " audit, V-06's score may not be quoted without a U-11 count")
    print()

    print("=== holdout (recorded BEFORE any human reads the 10-K) ===")
    for row in holdout:
        op = rank_forms_v2(observe(row))
        tie = " TIE" if op.tie else ""
        print(f"{row['company']} (SIC {row['sic']}) tags={row['legs_present']} "
              f"-> {op.status} {[(l.form.name, l.score) for l in op.ranked]}{tie} "
              f"rules={list(op.fired_rules)}")
        for line in op.ranked:
            for o in line.observations:
                print(f"    {line.form.name} <{line.slot}>: {o}")
        for c in op.value_conflicts:
            print(f"    VALUE_CONFLICT: {c}")
        for nvn in op.value_notes:
            print(f"    note: {nvn}")

    json_out = ROOT / "docs" / "data" / "evidence-rules-measurement-v2.json"
    json_out.write_text(json.dumps(
        {"grade": "post-hoc in-sample fit",
         "rule_sha256": sha256(ROOT / "adjudicator" / "evidence_rules.py"),
         "residual_sha256": sha256(ROOT / "adjudicator" / "residual.py"),
         "census_sha256": sha256(SNAPSHOT),
         "results": results,
         "G1": [m_p1, m_n], "G2": [h_p1, h_n], "G3": [rany, len(results)],
         "G4": {"E1": e1, "E2": e2, "E3": e3},
         "F2": f2_changes, "F3": len(ties)},
        indent=2), encoding="utf-8")
    print(f"\nwrote {json_out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
