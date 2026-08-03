"""v2 census - re-derive the spike-4 residual WITH fact rows (amount/ddate/qtrs/uom/coreg).

Writes a NEW file `docs/data/spike4-census-with-values.json`; the M1 golden input
`spike4-census-reproduced.json` is NOT touched. After building, the company list
and legs_present are compared against the committed v1 census and any difference
is printed verbatim (never hidden).

Reads only the local cache (~/.cache/why-missing/notes). No network.

Run:  .venv/Scripts/python.exe scripts/build_census_with_values.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adjudicator import concepts, residual, sec  # noqa: E402

QUARTERS = ("2024q3", "2024q4", "2025q1", "2025q2")
CACHE = Path.home() / ".cache" / "why-missing" / "notes"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "data" / "spike4-census-with-values.json"
V1 = ROOT / "docs" / "data" / "spike4-census-reproduced.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    concept = concepts.resolve("finite_lived_intangibles_net")
    tags = residual.load_tags(concept)  # filter UNION evidence (preregistration-v2 s4-4)
    print(f"loading {len(tags)} tags (filter {len(residual.filter_tags(concept))} "
          f"+ evidence {len(residual.evidence_tags())})")

    archives = {}
    all_filings = []
    for q in QUARTERS:
        for name in sec.archive_names(q):
            p = CACHE / name
            if not p.exists():
                print(f"FATAL: cache archive missing: {p} - stopping, NOT downloading")
                return 1
            archives[name] = sha256(p)
        data = sec.load_quarter(q, tags, CACHE)
        found = residual.find_residuals(data.sub, data.num, concept, q)
        all_filings.extend(found)
        print(f"{q}: residual filings {len(found)}", flush=True)

    companies = residual.one_per_company(all_filings)
    print(f"TOTAL residual filings {len(all_filings)} across {len(companies)} companies")

    def fact_dict(f: residual.TaggedFact) -> dict:
        d = asdict(f)
        d["value"] = None if f.value is None else str(f.value)
        return d

    OUT.write_text(json.dumps({
        "concept": concept.key,
        "window": list(QUARTERS),
        "cache_archives_sha256": archives,
        "residual_filings": len(all_filings),
        "companies": [{
            **{k: getattr(f, k) for k in
               ("cik", "accession", "company", "sic", "period", "quarter")},
            "legs_present": list(f.legs_present),
            "value_source_ok": f.value_source_ok,
            "facts": [fact_dict(x) for x in f.facts],
            "evidence_facts": [fact_dict(x) for x in f.evidence_facts],
        } for f in companies],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT}")

    # --- cross-check against the committed v1 census (report, do not hide) ---
    v1 = json.loads(V1.read_text(encoding="utf-8"))["companies"]
    old = {c["company"]: tuple(c["legs_present"]) for c in v1}
    new = {f.company: f.legs_present for f in companies}
    same = old == new
    print(f"v1-census comparison: companies+legs identical = {same}")
    if not same:
        for k in sorted(set(old) | set(new)):
            if old.get(k) != new.get(k):
                print(f"  DIFF {k}: v1={old.get(k)} v2={new.get(k)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
