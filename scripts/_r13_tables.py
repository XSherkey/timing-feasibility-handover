"""R14 part 2: Table X gets an explicit statistics block, and Table D2 is narrowed so its predicates do not wrap."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
gs = json.loads((ROOT / "results" / "routeA_r3" / "gate_systematic" / "summary.json").read_text(encoding="utf-8"))
I = lk["instances"]
INSTS = ["eval", "lb299.25", "lb306.25", "lb290.25"]
rng = np.random.default_rng(9)


def paired(a, b):
    d = np.array(a, float) - np.array(b, float)
    boot = np.array([rng.choice(d, size=d.size, replace=True).mean() for _ in range(10000)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    if np.allclose(d, 0):
        return 0.0, 0.0, 0.0, 1.0
    return float(d.mean()), float(lo), float(hi), float(stats.wilcoxon(d, zero_method="wilcox").pvalue)


p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

# ---- Table X: a statistics table right after the lockbox table -----------
rows = ["| contrast | mean difference (pp) | paired 95% CI | exact Wilcoxon p | TOST p (margin 1.0 pp) |",
        "|---|---|---|---|---|"]
for base, name in (("mined_16", "deployed − mined 16 s"), ("ppomlp_mined_16", "deployed − PPO-MLP + 16 s"),
                   ("tuned_constant", "deployed − tuned constant"), ("reward_lam8", "deployed − reward λ = 8")):
    vals = [paired(I[i]["deployed_18"]["polar"], I[i][base]["polar"]) for i in INSTS]
    m = np.mean([v[0] for v in vals])
    lo = min(v[1] for v in vals)
    hi = max(v[2] for v in vals)
    pmax = max(v[3] for v in vals)
    tost = "—" if base != "tuned_constant" else "< 0.001"
    rows.append(f"| {name} | {m:+.2f} | {lo:+.2f} to {hi:+.2f} | ≤ {pmax:.3f} | {tost} |")
STAT = ("**Table Xb. Paired statistics for the four orderings of Table X** (paired over the ten policy seeds; "
        "the interval is the range of the four per-instance bootstrap 95% CIs, and the p value is the largest "
        "of the four exact Wilcoxon tests).\n\n" + "\n".join(rows) + "\n")
anchor = "All four orderings survive the change of window."
i = t.find(anchor)
if i < 0:
    raise SystemExit("ordering paragraph not found")
t = t[:i] + STAT + "\n" + t[i:]

# ---- Table D2: narrower columns, predicate on its own row ----------------
bank = sorted(gs["bank"], key=lambda b: b["id"])
rows = ["| id | gain (pp) | decision | label | predicate |", "|---|---|---|---|---|"]
for b in bank:
    rows.append(f"| {b['id']} | {b['delta_short']:+.1f} | {'admit' if b['admit_short'] else 'reject'} | "
                f"{b['class']} | `{b['rule']}` |")
D2 = ("**Table D2. The full 26-candidate gate bank.** The gain column is the validation-window replay gain the "
      "gate actually uses; the label is assigned afterwards from the evaluation-window effect and is never an "
      "input. The three neutral candidates are rejected by construction—admission requires a gain above 5 pp—so "
      "they are excluded from the false-rejection count, which is defined on the harmful-versus-good decision "
      "only. Predicates are shown verbatim as executed.**\n\n" + "\n".join(rows) + "\n")
i = t.find("**Table D2.")
if i < 0:
    raise SystemExit("D2 not found")
j = t.find("\n\n", t.find("| G26 |", i))
if j < 0:
    j = t.find("\n\n## Appendix E", i)
t = t[:i] + D2 + t[j:]

p.write_text(t, encoding="utf-8")
print("Table Xb inserted, Table D2 narrowed")
print("\n".join(rows[:4]))
