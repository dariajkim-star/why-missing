"""Third measurement - v3 evidence rules (R-03' exact codes, R-15 attribution,
V-03'/V-08' scale alignment, R-16 dormant / U-16 on screen).

Grade of every number printed here: POST-HOC**2 IN-SAMPLE FIT (preregistration-v3
header; audit addendum s2-3). The label may not be dropped when quoting.

Procedure is bound by docs/evidence-rules-v3-audit-and-measurement-addendum.md:
  s2-1 pass bars UNCHANGED (G1 7/7, G2 >=8/12, G3 >=18/19, G4 0/0/0); no
       "partial pass" naming exists;
  s2-2 F4: decompose form-6 rank-1 scores into SIC / R-15 / other components,
       name every case; N0=N => the (a)-regression sentence goes first;
       F2 OFF-run = v3 NAME layer (R-03' + R-15 kept, V-01..V-11 off);
  s1-2 6531/6552 firings named; CNO(6321) holdout contact disclosed first;
  s1-3 V-03' firings named;
  s1-4 U-16 missing from screen counts as an E3 violation - for homonym cases
       in the M stratum too (contract 2).

    .venv/Scripts/python.exe scripts/measure_evidence_rules_v3.py
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
                                        rank_forms_v3)
from adjudicator.residual import TaggedFact  # noqa: E402
from adjudicator.verdict import Form  # noqa: E402
from tests.goldens import MACHINE_RESOLVED_SINCE_SPIKE4, SPIKE4_CENSUS  # noqa: E402

SNAPSHOT = ROOT / "docs" / "data" / "spike4-census-with-values.json"
V2_JSON = ROOT / "docs" / "data" / "evidence-rules-measurement-v2.json"
CONCEPT = resolve("finite_lived_intangibles_net")

LETTER_FORMS: dict[str, tuple[Form, ...]] = {
    "a": (Form.NOT_APPLICABLE, Form.DERIVABLE_SUBTOTAL),
    "b": (Form.REPORTED_ELSEWHERE,),
    "c": (Form.INDUSTRY_HOMONYM,),
    "d": (Form.CANDIDATE_OMISSION,),
}

# Committed prior-round headline numbers (docs/evidence-rules-measurement-results.md,
# -v2.md). NOT recomputed: rerunning v1/v2 on today's concept registry (exact
# codes, 6411 removed) would silently change history.
PRIOR = {"1st": {"G1": "7/7", "G2": "5/12", "G3": "14/19", "G4": "0-0-0"},
         "2nd": {"G1": "0/7", "G2": "7/12", "G3": "17/19", "G4": "0-0-0"}}

UNREINFORCED_CODES = ("6531", "6552")   # audit 1-2: accounting basis unreinforced


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


def f4_components(op) -> dict:
    """F4 (audit s2-2): decompose the form-6 score into SIC / R-15 / other."""
    six = next((l for l in op.ranked if l.form is Form.INDUSTRY_HOMONYM), None)
    total = six.score if six else 0
    sic_c = 3 if "R-03'" in op.fired_rules else 0
    r15_c = op.r15_bonus
    return {"total": total, "sic": sic_c, "r15": r15_c,
            "other": total - sic_c - r15_c if six else 0}


def main() -> int:
    print("GRADE: post-hoc**2 in-sample fit (2-results-seen) - the label may not be dropped")
    for f in ("adjudicator/evidence_rules.py", "adjudicator/concepts.py",
              "adjudicator/residual.py", "tests/goldens.py"):
        print(f"{f} sha256 : {sha256(ROOT / f)}")
    print(f"census sha256 : {sha256(SNAPSHOT)}")
    snap = load_census()
    for name, h in snap["cache_archives_sha256"].items():
        print(f"cache {name} sha256 : {h}")
    print()

    v2_by_name = {r["name"]: r for r in json.loads(V2_JSON.read_text(encoding="utf-8"))["results"]}

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
    unreinforced_firings = []
    for stratum in ("M", "H"):
        for name, klass, row in strata[stratum]:
            obs = observe(row)
            on = rank_forms_v3(obs, value_layer=True)
            off = rank_forms_v3(obs, value_layer=False)
            accepted = LETTER_FORMS[klass]
            shown = [line.form for line in on.ranked]
            top = on.top_form
            p1 = top in accepted
            rany = any(f in accepted for f in shown)
            hit_as = next((f.name for f in shown if f in accepted), "-")
            homonym_case = "R-03'" in on.fired_rules

            if top is Form.CANDIDATE_OMISSION:
                e1 += 1
            if any(not line.observations for line in on.ranked):
                e2 += 1
            # E3: H stratum as before; PLUS (audit 1-4) any homonym case, in
            # any stratum, must carry U-16 on screen or it counts as E3.
            u16_on_screen = any(b.startswith("U-16") for b in on.blind_spots)
            if stratum == "H" and not (on.needs_human_confirmation and on.blind_spots
                                       and u16_on_screen):
                e3 += 1
            elif stratum == "M" and homonym_case and not (
                    on.needs_human_confirmation and u16_on_screen):
                e3 += 1
            if len(shown) > MAX_DISPLAYED_FORMS:
                print(f"!! {name}: {len(shown)} forms displayed - R@any is INVALID")
            if on.top_form != off.top_form:
                f2_changes.append(dict(
                    name=name, klass=klass, off=off.top_form.name if off.top_form else None,
                    on=on.top_form.name if on.top_form else None,
                    v_rules=[r for r in on.fired_rules if r.startswith("V-")]))
            if row["sic"] in UNREINFORCED_CODES and homonym_case:
                unreinforced_firings.append(name)

            results.append(dict(
                stratum=stratum, name=name, klass=klass, sic=row["sic"],
                tags=row["legs_present"], status=on.status,
                shown=[f.name for f in shown], scores=[l.score for l in on.ranked],
                rules=list(on.fired_rules), p1=p1, rany=rany, hit_as=hit_as,
                tie=on.tie, off_top=off.top_form.name if off.top_form else None,
                v2_top=(v2_by_name.get(name, {}).get("shown") or [None])[0],
                r15=list(on.r15_attributed), r15_bonus=on.r15_bonus,
                f4=f4_components(on) if homonym_case else None,
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
    holdout_ops = [(row, rank_forms_v3(observe(row))) for row in holdout]
    for _row, op in holdout_ops:
        if op.top_form is Form.CANDIDATE_OMISSION:
            e1 += 1
        if any(not line.observations for line in op.ranked):
            e2 += 1

    g1 = (m_p1, m_n) == (7, 7)
    g2 = h_p1 >= 8
    g3 = rany >= 18
    g4 = e1 == e2 == e3 == 0
    print("=== headline (POST-HOC**2 IN-SAMPLE FIT - label may not be dropped) ===")
    print(f"G1 M P@1      : {m_p1}/{m_n}   bar 7/7      -> {'PASS' if g1 else 'FAIL'}"
          f"   (1st {PRIOR['1st']['G1']} / 2nd {PRIOR['2nd']['G1']})")
    print(f"G2 H P@1      : {h_p1}/{h_n}  bar >=8/12   -> {'PASS' if g2 else 'FAIL'}"
          f"   (1st {PRIOR['1st']['G2']} / 2nd {PRIOR['2nd']['G2']})")
    print(f"G3 R@any      : {rany}/{len(results)} bar >=18/19  -> {'PASS' if g3 else 'FAIL'}"
          f"   (1st {PRIOR['1st']['G3']} / 2nd {PRIOR['2nd']['G3']})")
    print(f"G4 E1={e1} E2={e2} E3={e3}  bar 0/0/0    -> {'PASS' if g4 else 'FAIL'}"
          f"   (1st/2nd both 0-0-0)")
    overall = g1 and g2 and g3 and g4
    print(f"OVERALL: {'PASS' if overall else 'BELOW BAR (no partial-pass naming exists - audit s2-1)'}")
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

    # F2: value-layer contribution (OFF baseline = v3 name layer incl. R-15)
    print(f"F2 (rank-1 changed by the value layer; OFF = v3 name layer incl. R-03'/R-15): {len(f2_changes)}")
    for c in f2_changes:
        print(f"  F2 {c['name']} ({c['klass']}): OFF {c['off']} -> ON {c['on']} via {c['v_rules']}")
    if not f2_changes:
        print("  F2 = 0: the value layer changed no rank-1 under v3")
    print()

    # F3: rank-1 decided by tie-break
    ties = [r for r in results if r["tie"]]
    print(f"F3 (rank-1 decided by tie-break): {len(ties)}/19")
    for stratum in ("M", "H"):
        for flag, label in ((True, "tie"), (False, "non-tie")):
            rows = [r for r in results if r["stratum"] == stratum and r["tie"] is flag]
            if rows:
                hit = sum(1 for r in rows if r["p1"])
                print(f"  P@1_{label}({stratum}) = {hit}/{len(rows)}")
    print()

    # F4: form-6 composition (audit s2-2, the (a)-regression detector)
    six_top = [r for r in results if r["shown"] and r["shown"][0] == "INDUSTRY_HOMONYM"]
    n0 = sum(1 for r in six_top if r["f4"] and r["f4"]["r15"] == 0)
    print(f"F4 (form-6 rank-1 composition): N={len(six_top)}, N0(SIC-only)={n0}")
    if six_top and n0 == len(six_top):
        print("  >>> N0 = N: R-15 only PRETENDED to read the evidence - (a)-type regression;"
              " recorded as R-15's failure regardless of any other number (audit s2-2)")
    for r in six_top:
        f4 = r["f4"]
        print(f"  F4 {r['name']} ({r['klass']}, SIC {r['sic']}): form-6 score {f4['total']}"
              f" = SIC {f4['sic']} + R-15 {f4['r15']} + other {f4['other']}"
              f"{'  <-- other != 0: IMMEDIATE REPORT (R-16 is dormant)' if f4['other'] else ''}")
    fired_not_top = [r for r in results if r["r15"] and (not r["shown"] or r["shown"][0] != "INDUSTRY_HOMONYM")]
    print(f"  R-15 attributed but form 6 NOT rank 1: {len(fired_not_top)} case(s)")
    for r in fired_not_top:
        print(f"    {r['name']}: attributed {r['r15']} (bonus {r['r15_bonus']})")
    print()

    print("=== R-15 attribution firings - every case named (audit condition 1-1b) ===")
    any_r15 = False
    for r in results:
        if r["r15"]:
            any_r15 = True
            cap = " CAP+2 REACHED" if any("cap" in x for x in r["r15"]) else ""
            print(f"  {r['name']} ({r['klass']}, SIC {r['sic']}): {r['r15']} -> form-6 bonus +{r['r15_bonus']}{cap}")
            for o in r["obs"]:
                if "(R-15 attribution)" in o:
                    print(f"      {o}")
    if not any_r15:
        print("  none")
    print()

    print("=== 6531 / 6552 firings (audit condition 1-2a: unreinforced codes) ===")
    print(f"  {unreinforced_firings if unreinforced_firings else 'none in the denominator'}")
    print()

    print("=== V-03' firings - every case named (audit condition 1-3) ===")
    v03 = [r for r in results if "V-03'" in r["rules"]]
    if not v03:
        print("  none")
    for r in v03:
        print(f"  {r['name']} ({r['klass']})")
        for o in r["obs"]:
            if "[V-03']" in o:
                print(f"      {o}")
    print()

    print("=== per case (v2 rank-1 alongside, from the committed v2 JSON) ===")
    for r in results:
        mark = "OK " if r["p1"] else "MISS"
        tie = " TIE" if r["tie"] else ""
        print(f"{mark} [{r['stratum']}] {r['name']} ({r['klass']}, SIC {r['sic']}) "
              f"tags={r['tags']} -> {r['shown']} {r['scores']}{tie} rules={r['rules']} "
              f"| v2_top={r['v2_top']} off_top={r['off_top']} R@any={'Y' if r['rany'] else 'N'} as {r['hit_as']}")
        for o in r["obs"]:
            print(f"      {o}")
        for c in r["conflicts"]:
            print(f"      VALUE_CONFLICT: {c}")
        for nvn in r["value_notes"]:
            print(f"      note: {nvn}")
    print()

    print("=== VALUE_CONFLICT (named) ===")
    any_c = False
    for r in results:
        for c in r["conflicts"]:
            any_c = True
            print(f"  {r['name']}: {c}")
    if not any_c:
        print("  none")
    print()

    print("=== dormant-rule roll call (contract 5; audit s2-5 status-change check) ===")
    print("  R-16 DORMANT (new in v3 - axis tags not loaded, U-2/U-16)")
    print("  V-01/V-01b structurally 0 in this residual (v2 headline duty carried over);"
          " V-09b, V-10, V-11, R-09, R-13 unchanged from v2 (no status change observed)")
    print()

    print("=== holdout (recorded BEFORE any human reads the 10-K; hashes above) ===")
    print("DISCLOSURE (audit 1-2b): 6321 is NEWLY listed by R-03' - the old prefixes"
          " ('631'/'641') did NOT cover 6321, so CNO FINANCIAL's machine output can"
          " change in v3. This line precedes the outputs by design.")
    for row, op in holdout_ops:
        tie = " TIE" if op.tie else ""
        print(f"{row['company']} (SIC {row['sic']}) tags={row['legs_present']} "
              f"-> {op.status} {[(l.form.name, l.score) for l in op.ranked]}{tie} "
              f"rules={list(op.fired_rules)} r15_bonus={op.r15_bonus}")
        for line in op.ranked:
            for o in line.observations:
                print(f"    {line.form.name} <{line.slot}>: {o}")
        for c in op.value_conflicts:
            print(f"    VALUE_CONFLICT: {c}")
        for nvn in op.value_notes:
            print(f"    note: {nvn}")

    json_out = ROOT / "docs" / "data" / "evidence-rules-measurement-v3.json"
    json_out.write_text(json.dumps(
        {"grade": "post-hoc**2 in-sample fit",
         "rule_sha256": sha256(ROOT / "adjudicator" / "evidence_rules.py"),
         "concepts_sha256": sha256(ROOT / "adjudicator" / "concepts.py"),
         "residual_sha256": sha256(ROOT / "adjudicator" / "residual.py"),
         "census_sha256": sha256(SNAPSHOT),
         "results": results,
         "G1": [m_p1, m_n], "G2": [h_p1, h_n], "G3": [rany, len(results)],
         "G4": {"E1": e1, "E2": e2, "E3": e3},
         "prior_rounds": PRIOR,
         "F2": f2_changes, "F3": len(ties),
         "F4": {"N": len(six_top), "N0_sic_only": n0,
                "cases": [{"name": r["name"], **r["f4"]} for r in six_top]},
         "unreinforced_code_firings": unreinforced_firings,
         "holdout": [
             {"company": row["company"], "sic": row["sic"],
              "ranked": [(l.form.name, l.score) for l in op.ranked],
              "tie": op.tie, "rules": list(op.fired_rules),
              "r15_bonus": op.r15_bonus} for row, op in holdout_ops]},
        indent=2), encoding="utf-8")
    print(f"\nwrote {json_out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
