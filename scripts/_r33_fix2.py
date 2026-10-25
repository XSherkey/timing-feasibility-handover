"""R33 part 2: the last two wording sites and the traffic-lockbox / cluster additions."""
from __future__ import annotations

import json
import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
main = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = main.read_text(encoding="utf-8")
s = supp_path.read_text(encoding="utf-8")
done = []

# 1. stage-1 sentence
old = ("which is precisely why the *passive* process cannot localize the crossing while the *forced-coverage* probe "
       "can.")
new = ("which is precisely why the *passive* process cannot localize the crossing to the 2 s precision a deployment "
       "needs, while the *forced-coverage* probe is designed to.")
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("stage-1 precision")

# 2. conclusion attribution
old = ("accounts for nearly all of its reported gain: 23.4 of the 24.1 pp")
new = ("accounts for nearly all of its reported gain: 23.4 of the 24.1 pp between the reward-only baseline and the "
       "16 s mined-rule arm without the margin")
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("conclusion attribution")

# 3. cluster structure sentence in the main text (Section V-C)
anchor = "The estimator plays two roles:"
i = t.find(anchor)
if i > 0:
    j = t.find("\n\n", i)
    ADD = (" The blocking unit of the bootstrap is (policy seed, site): five seeds over four sites give twenty "
           "clusters with a median of 137 attempts (max 294), and cluster means of the requirement span 3.7–10.4 s "
           "(sd 3.1 s), which is why resampling whole blocks keeps the interval ≈8 s wide while an i.i.d. bootstrap "
           "collapses to one grid step. Both facts are reported in Table G2 of the supplementary material.")
    t = t[:j] + ADD + t[j:]
    done.append("cluster sentence")

# 4. supplement: Table G2 with cluster stats + the six lockbox-traffic cells
prec = json.loads((ROOT / "results" / "routeA_r3" / "precision" / "summary.json").read_text(encoding="utf-8"))
lbt = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_traffic" / "summary.json").read_text(encoding="utf-8"))

G2 = ("\n\n## Appendix G2. Blocking structure and traffic-seed lockbox cells\n\n"
      "**Table G2. Cluster structure of the passive log (|lat| ≥ 70°, five campaign seeds, test window).** The "
      "bootstrap of Section V-C resamples (policy seed, site) blocks; the table gives the structure those blocks have.\n\n"
      "| quantity | value |\n|---|---|\n"
      f"| polar attempts | {prec['n_attempts']:,} |\n"
      f"| late handovers | {prec['n_late']:,} |\n"
      f"| blocks (seed × site) | {prec['n_clusters']} |\n"
      f"| attempts per block, median (max) | {prec['cluster_size_median']:.0f} ({prec['cluster_size_max']}) |\n"
      f"| block-mean requirement, range (sd) | {prec['cluster_mean_range'][0]:.1f}–{prec['cluster_mean_range'][1]:.1f} s "
      f"({prec['cluster_mean_sd']:.1f} s) |\n\n"
      "**Table G3. Traffic-seed lockbox cells (polar HSR, ten policy seeds per cell).** The three epoch-shifted lockbox "
      "columns of Table VII keep traffic seed 0; these six cells repeat the two load-bearing contrasts at seeds 0–2.\n\n"
      "| instance | traffic seed | no shield | deployed 18 s | tuned constant | deployed − no shield | deployed − constant |\n"
      "|---|---|---|---|---|---|---|\n")
for inst, label in (("eval", "evaluation window"), ("lb+7", "+7 d lockbox")):
    for tr in ("0", "1", "2"):
        d = lbt["instances"][inst]["deployed_18"][tr]["summary"]["mean"]
        n = lbt["instances"][inst]["no_shield"][tr]["summary"]["mean"]
        c = lbt["instances"][inst]["tuned_constant"][tr]["summary"]["mean"]
        G2 += f"| {label} | {tr} | {n:.2f} | {d:.2f} | {c:.2f} | {d - n:+.2f} | {d - c:+.2f} |\n"

anchor = "## Appendix H. Drift ladder"
k = s.find(anchor)
if k > 0:
    s = s[:k] + G2.strip() + "\n\n" + s[k:]
    done.append("G2/G3 tables")

# 5. reword the traffic-lockbox sentence in the main text
old = ("What the lockbox does not establish is independence across traffic arrivals or site mixes, and we do not claim "
       "it.")
new = ("The three epoch-shifted columns alone do not test traffic variation; the additional runs give limited evidence "
       "over traffic seeds 0–2 (Table G3), not over new site mixes, and we claim only the former.")
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("lockbox sentence reworded")

main.write_text(re.sub(r"\n{3,}", "\n\n", t), encoding="utf-8")
supp_path.write_text(re.sub(r"\n{3,}", "\n\n", s), encoding="utf-8")
print("edits:", done)
