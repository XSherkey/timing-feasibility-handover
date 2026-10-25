"""G1 analysis: clean (append) gate test, plus the n=10 replacement-mode contrast."""
from __future__ import annotations

import glob
import json
import os
import statistics as st

import numpy as np
from scipy import stats


def load(pattern: str) -> dict[int, list[float]]:
    out = {}
    for d in sorted(glob.glob(pattern)):
        p = os.path.join(d, "summary.json")
        if not os.path.exists(p):
            continue
        seed = int(d.rsplit("_s", 1)[1])
        out[seed] = [100 * (r["arctic"] or 0) for r in json.load(open(p, encoding="utf-8"))]
    return out


def wil(a, b):
    try:
        return stats.wilcoxon(a, b)
    except ValueError:
        return None


def main() -> None:
    clean_gate = load("results/routeA_g1/i_clean_gate_s*")
    clean_nogate = load("results/routeA_g1/i2_clean_nogate_s*")
    j = {**load("results/routeA_f2/g_shared_gate_s*"), **load("results/routeA_g1/j_gate_s*")}
    k = {**load("results/routeA_f2/h_shared_nogate_s*"), **load("results/routeA_g1/k_nogate_s*")}
    noinj = load("results/multi_shared_s*")

    def m(rows, s):
        return st.mean(rows[s][1:])

    print("== clean design (append): gate ON vs OFF, seeds %s ==" % sorted(set(clean_gate) & set(clean_nogate)))
    common = sorted(set(clean_gate) & set(clean_nogate))
    for s in common:
        print(f"  seed{s}: gate {m(clean_gate, s):5.1f}   nogate {m(clean_nogate, s):5.1f}   "
              f"diff {m(clean_gate, s) - m(clean_nogate, s):+5.1f}")
    common_clean = common
    a = [m(clean_gate, s) for s in common_clean]
    b = [m(clean_nogate, s) for s in common_clean]
    print(f"  mean gate {st.mean(a):.1f}  nogate {st.mean(b):.1f}  diff {st.mean(np.array(a) - np.array(b)):+.1f}")

    print("\n== arm I vs no-injection (acceptance: |diff| <= 2 pp) ==")
    cc = sorted(set(clean_gate) & set(noinj))
    if cc:
        di = [m(clean_gate, s) - m(noinj, s) for s in cc]
        print(f"  no-injection {st.mean([m(noinj, s) for s in cc]):.1f}  I {st.mean([m(clean_gate, s) for s in cc]):.1f}  "
              f"diff {st.mean(di):+.1f} pp (per seed {[round(d,1) for d in di]})")

    print("\n== replacement mode, n=%d ==" % len(set(j) & set(k)))
    common = sorted(set(j) & set(k))
    for s in common:
        print(f"  seed{s}: gate {m(j, s):5.1f}   nogate {m(k, s):5.1f}   diff {m(j, s) - m(k, s):+5.1f}")
    a = [m(j, s) for s in common]
    b = [m(k, s) for s in common]
    r = wil(a, b)
    print(f"  mean gate {st.mean(a):.1f}  nogate {st.mean(b):.1f}  "
          f"diff {st.mean(np.array(a) - np.array(b)):+.1f}  p={r.pvalue:.4f}" if r else "")

    out = dict(clean=dict(per_seed={str(s): dict(gate=m(clean_gate, s), nogate=m(clean_nogate, s),
                                                 noinject=m(noinj, s) if s in noinj else None)
                                  for s in common_clean},
                          gate_mean=round(st.mean([m(clean_gate, s) for s in common_clean]), 1),
                          nogate_mean=round(st.mean([m(clean_nogate, s) for s in common_clean]), 1),
                          diff=round(st.mean(np.array([m(clean_gate, s) for s in common_clean]) -
                                             np.array([m(clean_nogate, s) for s in common_clean])), 1),
                          vs_noinject=round(st.mean([m(clean_gate, s) - m(noinj, s)
                                                     for s in common_clean if s in noinj]), 2)),
               replace=dict(n=len(common), gate_mean=round(st.mean([m(j, s) for s in common]), 1),
                            nogate_mean=round(st.mean([m(k, s) for s in common]), 1),
                            diff=round(st.mean(np.array([m(j, s) for s in common]) -
                                               np.array([m(k, s) for s in common])), 1),
                            p=round(float(r.pvalue), 5) if r else None))
    with open("results/routeA/g1_gate_power.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("\nwrote results/routeA/g1_gate_power.json")


if __name__ == "__main__":
    main()
