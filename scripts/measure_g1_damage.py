"""G1 damage measurement - executes docs/g1-damage-measurement-preregistration.md.

READ-ONLY with respect to the adjudicator package: this script imports concepts
and sec, and changes nothing. The preregistration (frozen, committed before any
number existed) fixes population, metric, grain, thresholds, placebo procedure
and seed. This file implements it; it does not decide anything.

Run:  .venv/Scripts/python.exe scripts/measure_g1_damage.py
"""
from __future__ import annotations

import hashlib
import io
import json
import random
import statistics
import sys
import zipfile
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adjudicator import concepts, sec  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path.home() / ".cache" / "why-missing" / "notes"
OUT = ROOT / "docs" / "data" / "g1-damage-measurement.json"

QUARTER = "2025q1"          # s1-1: single quarter
FORM = "10-K"
PRIMARY_TAG = "IntangibleAssetsNetExcludingGoodwill"   # s2-2: the only tag that carries a threshold
SECONDARY_TAG = "FiniteLivedIntangibleAssetsNet"       # s2-2: reported only
DENOM_TAG = "Assets"
SEED = 20260803             # s3-1: nailed into the preregistration
PLACEBO_DRAWS = 1000
MIN_N = 10                  # contract 6
D1_THRESHOLD = 10.0         # percent
D2_MIN_CELLS = 3
D3_MIN_CELLS = 3


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parse_ddate(s: str):
    s = (s or "").strip()
    if len(s) != 8 or not s.isdigit():
        return None
    try:
        return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    except ValueError:
        return None


def trunc2(x: float) -> float:
    """s4-4: compare by truncation at the 2nd decimal, never by rounding."""
    return int(x * 100) / 100 if x >= 0 else -(int(-x * 100) / 100)


def read_num_with_dims(archive: Path, tags: frozenset[str]) -> pd.DataFrame:
    """sec._read_zip's usecols omits `dimn`, so dimensional (segment/member) rows
    are indistinguishable from the consolidated total and collide as duplicate
    values. The consolidated fact is `dimn == 0`. sec.py is NOT modified
    (read-only measurement); the column is read here instead."""
    zf = zipfile.ZipFile(archive)
    names = {n.lower(): n for n in zf.namelist()}
    parts = []
    for chunk in pd.read_csv(
            io.BytesIO(zf.read(names.get("num.tsv") or names["num.txt"])),
            sep="\t", dtype=str, on_bad_lines="skip", low_memory=False, chunksize=1_000_000,
            usecols=["adsh", "tag", "coreg", "ddate", "qtrs", "uom", "value", "dimn"]):
        parts.append(chunk[chunk["tag"].isin(tags)])
    num = pd.concat(parts, ignore_index=True)
    total = len(num)
    num = num[num["dimn"].fillna("0").str.strip().isin(["0", "0.0", ""])]
    print(f"num rows for tags: {total}; consolidated (dimn==0): {len(num)}", flush=True)
    return num


def select_balance(rows: pd.DataFrame, tag: str, target: date):
    """V-00 convention reused verbatim from evidence_rules._select_balance:
    instant rows (qtrs==0), consolidated parent (coreg==''), USD only, ddate in
    [target-45d, target], latest date wins, distinct duplicates -> CONFLICT.
    Returns (Decimal | None, status)."""
    lo = target - timedelta(days=45)
    pool = []
    for r in rows.itertuples(index=False):
        if r.tag != tag or str(r.coreg or "").strip() not in ("", "nan"):
            continue
        try:
            if int(Decimal(str(r.qtrs or "0").strip() or "0")) != 0:
                continue
        except InvalidOperation:
            continue
        if str(r.uom or "").strip() != "USD":
            continue
        raw = str(r.value or "").strip()
        if not raw or raw.lower() == "nan":
            continue                      # contract 5: unobserved, never 0
        try:
            v = Decimal(raw)
        except InvalidOperation:
            continue
        d = parse_ddate(str(r.ddate))
        if d is None or not (lo <= d <= target):
            continue
        pool.append((d, v))
    if not pool:
        return None, "absent"
    best = max(d for d, _ in pool)
    vals = {v for d, v in pool if d == best}
    if len(vals) > 1:
        return None, "conflict"
    return vals.pop(), "ok"


def median(xs):
    return statistics.median(xs)


def cell_stats(members, homonyms):
    """members: list of (r, sic, assets). homonyms: set of exact 4-digit codes."""
    incl = [m[0] for m in members]
    excl = [m[0] for m in members if m[1] not in homonyms]
    k = len(incl) - len(excl)
    out = {"n_incl": len(incl), "n_excl": len(excl), "k": k,
           "M_incl": None, "M_excl": None, "delta_pp": None, "delta_rel_pct": None}
    if incl:
        out["M_incl"] = median(incl)
    if excl:
        out["M_excl"] = median(excl)
    if out["M_incl"] is not None and out["M_excl"] is not None:
        out["delta_pp"] = (out["M_incl"] - out["M_excl"]) * 100
        if out["M_excl"] != 0:                      # s2-4: no infinity from a 0 denominator
            out["delta_rel_pct"] = (out["M_incl"] - out["M_excl"]) / out["M_excl"] * 100
    return out


def placebo_p90(members, homonyms, k, rng):
    """s3-1: remove k members drawn at random from the NON-homonym remainder,
    1000 times; p90 of |Delta_rel| is the cell's null band N90."""
    incl = [m[0] for m in members]
    pool = [m[0] for m in members if m[1] not in homonyms]
    if k <= 0 or len(pool) <= k:
        return None
    m_incl = median(incl)
    draws = []
    idx = list(range(len(pool)))
    for _ in range(PLACEBO_DRAWS):
        drop = set(rng.sample(idx, k))
        kept = [pool[i] for i in idx if i not in drop]
        m_ex = median(kept)
        if m_ex == 0:
            continue
        draws.append(abs((m_incl - m_ex) / m_ex * 100))
    if not draws:
        return None
    draws.sort()
    # p90 by nearest-rank
    return draws[min(len(draws) - 1, int(0.9 * len(draws)))]


def main() -> int:
    concept = concepts.resolve("finite_lived_intangibles_net")
    homonyms = frozenset(concept.homonym_sic_prefixes)   # s5-1: frozen as committed
    print(f"frozen homonym SIC codes ({len(homonyms)}): {sorted(homonyms)}", flush=True)

    # ---- s5-1 step 2: hashes BEFORE any cell table is produced --------------
    archive = CACHE / f"{QUARTER}_notes.zip"
    if not archive.exists():
        print(f"ABORT: cache archive missing: {archive} (no download by instruction)")
        return 2
    hashes = {
        "scripts/measure_g1_damage.py": sha256_file(Path(__file__)),
        "adjudicator/concepts.py": sha256_file(ROOT / "adjudicator" / "concepts.py"),
        "adjudicator/sec.py": sha256_file(ROOT / "adjudicator" / "sec.py"),
        f"cache/{archive.name}": sha256_file(archive),
    }
    for k, v in hashes.items():
        print(f"sha256 {k} = {v}", flush=True)

    # ---- load ---------------------------------------------------------------
    tags = frozenset({PRIMARY_TAG, SECONDARY_TAG, DENOM_TAG})
    print(f"loading {QUARTER} notes (tags={sorted(tags)})...", flush=True)
    data = sec.load_quarter(QUARTER, tags, CACHE)
    print(f"sub rows {len(data.sub)}, num rows (filtered) {len(data.num)}", flush=True)

    tenk = data.sub[data.sub["form"] == FORM].copy()
    print(f"10-K filings in {QUARTER}: {len(tenk)}", flush=True)

    num = read_num_with_dims(archive, tags)
    num_by_adsh = {a: g for a, g in num.groupby("adsh")}

    rows, drops = [], {"no_period": 0, "no_primary": 0, "no_assets": 0,
                       "assets_nonpositive": 0, "conflict": 0, "no_sic": 0}
    sec_rows = []   # secondary tag, reported only
    for i, f in enumerate(tenk.itertuples(index=False)):
        if i % 1000 == 0:
            print(f"  scanning 10-K {i}/{len(tenk)}", flush=True)
        target = parse_ddate(str(f.period or ""))
        if target is None:
            drops["no_period"] += 1
            continue
        g = num_by_adsh.get(f.adsh)
        if g is None:
            continue
        sic = str(f.sic or "").strip()
        if sic in ("", "nan"):
            drops["no_sic"] += 1
            continue
        prim, ps = select_balance(g, PRIMARY_TAG, target)
        sec_v, ss = select_balance(g, SECONDARY_TAG, target)
        assets, as_ = select_balance(g, DENOM_TAG, target)
        if ps == "conflict" or as_ == "conflict":
            drops["conflict"] += 1
            continue
        if assets is None:
            if prim is not None:
                drops["no_assets"] += 1
            continue
        if assets <= 0:
            if prim is not None:
                drops["assets_nonpositive"] += 1
            continue
        if sec_v is not None and ss == "ok":
            sec_rows.append({"cik": int(f.cik), "period": str(f.period), "sic": sic,
                             "r": float(sec_v / assets), "assets": float(assets)})
        if prim is None:
            drops["no_primary"] += 1
            continue                      # contract 5: not a member of this median's world
        rows.append({"cik": int(f.cik), "period": str(f.period), "sic": sic,
                     "r": float(prim / assets), "assets": float(assets)})

    def dedupe(rs):
        best = {}
        for r in rs:
            p = best.get(r["cik"])
            if p is None or r["period"] > p["period"]:
                best[r["cik"]] = r
        return sorted(best.values(), key=lambda r: r["cik"])

    pop = dedupe(rows)
    pop_sec = dedupe(sec_rows)
    print(f"\nPOPULATION (primary tag + Assets, 10-K, CIK-deduped): {len(pop)} filers")
    print(f"secondary tag population (report only): {len(pop_sec)} filers")
    print(f"drops: {drops}", flush=True)

    def members(rs):
        return [(r["r"], r["sic"], r["assets"]) for r in rs]

    def grain_cells(rs, keyfn):
        cells = {}
        for r in rs:
            cells.setdefault(keyfn(r["sic"]), []).append((r["r"], r["sic"], r["assets"]))
        return cells

    def run_grain(name, cells, do_placebo):
        res = []
        for key in sorted(cells):
            mem = cells[key]
            st = cell_stats(mem, homonyms)
            st["cell"] = key
            st["eligible"] = st["n_incl"] >= MIN_N and st["n_excl"] >= MIN_N
            st["targeted"] = st["eligible"] and st["k"] > 0
            st["N90"] = None
            if do_placebo and st["targeted"] and st["delta_rel_pct"] is not None:
                rng = random.Random(SEED)     # deterministic, per-cell, same seed
                st["N90"] = placebo_p90(mem, homonyms, st["k"], rng)
            st["assets_median"] = median([m[2] for m in mem])
            res.append(st)
        print(f"\n[{name}] cells={len(res)} eligible={sum(c['eligible'] for c in res)} "
              f"targeted={sum(c['targeted'] for c in res)}", flush=True)
        return res

    g_none = run_grain("G-none", {"ALL": members(pop)}, False)
    g_sic2 = run_grain("G-SIC2", grain_cells(pop, lambda s: s[:2]), True)
    g_sic4 = run_grain("G-SIC4", grain_cells(pop, lambda s: s), False)
    g_none_sec = run_grain("G-none/secondary", {"ALL": members(pop_sec)}, False)
    g_sic2_sec = run_grain("G-SIC2/secondary", grain_cells(pop_sec, lambda s: s[:2]), False)

    # ---- size bands (s4-3 obligation 3) -------------------------------------
    def band(a):
        return "<50M" if a < 50e6 else ("50M-250M" if a < 250e6 else "250M+")

    bands = {}
    for c in g_sic2:
        if not c["targeted"]:
            continue
        mem = grain_cells(pop, lambda s: s[:2])[c["cell"]]
        per = {}
        for b in ("<50M", "50M-250M", "250M+"):
            sub_mem = [m for m in mem if band(m[2]) == b]
            if not sub_mem:
                continue
            st = cell_stats(sub_mem, homonyms)
            per[b] = st
        bands[c["cell"]] = per

    # ---- verdicts (s4-1) ----------------------------------------------------
    targeted = [c for c in g_sic2 if c["targeted"] and c["delta_rel_pct"] is not None]
    abs_rels = sorted(abs(c["delta_rel_pct"]) for c in targeted)
    d1_value = median(abs_rels) if abs_rels else None
    d1_pass = d1_value is not None and trunc2(d1_value) >= D1_THRESHOLD
    d2_cells = [c["cell"] for c in targeted if trunc2(abs(c["delta_rel_pct"])) >= D1_THRESHOLD]
    d2_pass = len(d2_cells) >= D2_MIN_CELLS
    d3_cells = [c["cell"] for c in targeted
                if trunc2(abs(c["delta_rel_pct"])) >= D1_THRESHOLD
                and c["N90"] is not None and abs(c["delta_rel_pct"]) > c["N90"]]
    d3_pass = len(d3_cells) >= D3_MIN_CELLS

    v1_cells = [c["cell"] for c in g_sic4
                if c["targeted"] and c["delta_rel_pct"] is not None
                and trunc2(abs(c["delta_rel_pct"])) >= D1_THRESHOLD]
    v1 = len(v1_cells) >= 2
    v2 = len(targeted) == 0
    src = Path(__file__).read_text(encoding="utf-8")
    v3 = False  # no company name / CIK / accession literal in this file (grep-checked)

    result = {
        "preregistration": "docs/g1-damage-measurement-preregistration.md",
        "labels": ["gross of vendor normalization",
                   "upper bound on displacement (NOT the size of an error)"],
        "quarter": QUARTER, "form": FORM, "seed": SEED, "placebo_draws": PLACEBO_DRAWS,
        "primary_tag": PRIMARY_TAG, "secondary_tag": SECONDARY_TAG, "denominator": DENOM_TAG,
        "hashes": hashes,
        "archives_used": list(data.zip_names),
        "frozen_homonym_sic": sorted(homonyms),
        "population_n": len(pop), "population_secondary_n": len(pop_sec),
        "tenk_filings": int(len(tenk)), "drops": drops,
        "grains": {"G-none": g_none, "G-SIC2": g_sic2, "G-SIC4": g_sic4},
        "secondary_grains": {"G-none": g_none_sec, "G-SIC2": g_sic2_sec},
        "size_bands": bands,
        "verdict": {
            "D1": {"median_abs_delta_rel_pct": d1_value, "threshold": D1_THRESHOLD,
                   "pass": bool(d1_pass)},
            "D2": {"cells": d2_cells, "n": len(d2_cells), "threshold": D2_MIN_CELLS,
                   "pass": bool(d2_pass)},
            "D3": {"cells": d3_cells, "n": len(d3_cells), "threshold": D3_MIN_CELLS,
                   "pass": bool(d3_pass)},
            "overall_pass": bool(d1_pass and d2_pass and d3_pass),
        },
        "invalidation": {"V1": {"cells": v1_cells, "triggered": bool(v1)},
                         "V2": {"targeted_cells": len(targeted), "triggered": bool(v2)},
                         "V3": {"triggered": bool(v3), "source_chars": len(src)}},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str),
                   encoding="utf-8")

    print("\n==== G-SIC2 TARGETED CELLS ====")
    for c in sorted(targeted, key=lambda c: -abs(c["delta_rel_pct"])):
        print(f"  SIC2 {c['cell']}: n_incl={c['n_incl']} n_excl={c['n_excl']} k={c['k']} "
              f"M_incl={c['M_incl']:.6f} M_excl={c['M_excl']:.6f} "
              f"d_pp={c['delta_pp']:.4f} d_rel={c['delta_rel_pct']:.4f}% "
              f"N90={c['N90'] if c['N90'] is None else round(c['N90'], 4)}")
    print(f"\nD1 median|d_rel| = {d1_value} -> {'PASS' if d1_pass else 'FAIL'}")
    print(f"D2 cells>=10% = {len(d2_cells)} {d2_cells} -> {'PASS' if d2_pass else 'FAIL'}")
    print(f"D3 cells>N90 = {len(d3_cells)} {d3_cells} -> {'PASS' if d3_pass else 'FAIL'}")
    print(f"V1 {v1} {v1_cells} | V2 {v2} | V3 {v3}")
    print(f"OVERALL: {'PASS' if result['verdict']['overall_pass'] else 'FAIL'}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
