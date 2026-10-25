"""T2-02 support - re-select the reward-penalty coefficient lambda on the validation window."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from r3lib import OUT, SEEDS, arctic, evaluate, summarise, write

LAMBDAS = [0.3, 0.5, 2.0, 8.0]
DIRS = {0.3: "results/routeA_f3/lam0.3", 0.5: "results/routeA_f3/lam0.5",
        2.0: "results/routeA_f3/lam2.0", 8.0: "results/routeA_f3/lam8.0"}


def main() -> int:
    rows = {}
    for lam in LAMBDAS:
        vals = []
        for s in SEEDS:
            r = evaluate(f"lamval_{lam:g}_s{s}", run=f"{DIRS[lam]}/no_forensics_seed{s}",
                         window="validation")
            vals.append(arctic(r))
        rows[f"{lam:g}"] = dict(polar=vals, summary=summarise(vals), dir=DIRS[lam])
        print(f"lambda={lam:5g}  val polar {np.mean(vals):6.2f}  (sd {np.std(vals, ddof=1):4.2f})")
    best = max(rows, key=lambda k: rows[k]["summary"]["mean"] or -1e9)
    out = dict(window="validation", rows=rows, best_lambda=best,
               best_mean=rows[best]["summary"]["mean"],
               note="only the four archived coefficients are re-scored on validation; the archived "
                    "seven-point scan lives in results/routeA_f3")
    write(OUT / "lambda_validation" / "summary.json", out)
    print("best lambda on validation:", best)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
