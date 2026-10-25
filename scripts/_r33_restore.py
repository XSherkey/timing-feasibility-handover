"""R33 part 4: restore the KM scope sentences and the cluster sentence as their own paragraph."""
from __future__ import annotations

import json
import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
prec = json.loads((ROOT / "results" / "routeA_r3" / "precision" / "summary.json").read_text(encoding="utf-8"))

assert "competing failure" not in t, "already present"
assert "twenty clusters" not in t

anchor = "**Stage 1: recovering the requirement from censored failures**" 
# place the paragraph after the 'Two further remarks' paragraph, i.e. before '### B. Stage 2'
i = t.find("### B. Stage 2")
if i < 0:
    raise SystemExit("Stage 2 heading not found")

NEW = ("Two scope statements belong to this estimator. Because the KM curve keeps only successes and late handovers, it "
       "targets the requirement *conditional on no competing failure*: `no_route` and `window_exceeded` are excluded by "
       "design, and that exclusion is only valid if those classes carry no information about T_z beyond the region, "
       "which we cannot check from the log—so we report it as a limitation of the diagnostic rather than of the "
       "threshold. The blocking unit of the bootstrap that follows is (policy seed, site): five seeds over four sites "
       f"give {prec['n_clusters']} clusters with a median of {prec['cluster_size_median']:.0f} attempts (max "
       f"{prec['cluster_size_max']}), and the cluster means of the requirement span "
       f"{prec['cluster_mean_range'][0]:.1f}–{prec['cluster_mean_range'][1]:.1f} s (sd {prec['cluster_mean_sd']:.1f} s). "
       "That heterogeneity is why resampling whole blocks keeps the interval ≈8 s wide while an i.i.d. bootstrap "
       "collapses to one grid step; the structure is tabulated in Table G2 of the supplementary material.\n\n")

t = t[:i] + NEW + t[i:]
t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("restored; competing failure:", t.count("competing failure"), "| clusters sentence:", t.count("twenty clusters"))
