"""R10 part 5: isolation paired stats and the two table updates."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
iso = json.loads((ROOT / "results" / "routeA_r3" / "isolation" / "summary.json").read_text(encoding="utf-8"))
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
rng = np.random.default_rng(11)


def paired(a, b, reps=10000):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a - b
    boot = np.array([rng.choice(d, size=d.size, replace=True).mean() for _ in range(reps)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    if np.allclose(d, 0):
        return 0.0, 0.0, 0.0, 1.0
    try:
        p = stats.wilcoxon(a, b, zero_method="wilcox").pvalue
    except ValueError:
        p = float("nan")
    return float(d.mean()), float(lo), float(hi), float(p)


a0 = iso["arms"]["A0_full"]["per_seed"]["eval"]
rows = {}
for arm, label in [("A1_human", "A1"), ("A2_grid", "A2"), ("A3_randomBest", "A3"),
                   ("A4_noKM", "A4"), ("A5_noGate", "A5"), ("A7_probeOnly", "A7"),
                   ("A8_constantProbe", "A8")]:
    m, lo, hi, p = paired(iso["arms"][arm]["per_seed"]["eval"], a0)
    rows[label] = (m, lo, hi, p)
    print(f"{label}: {m:+.3f} [{lo:+.3f}, {hi:+.3f}] p={p:.3f}")

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

# --- Table IX: add two columns to the isolation table ---------------------
i = t.find("| A1 |")
if i < 0:
    raise SystemExit("isolation table not found")
start = t.rfind("\n\n", 0, i)
end = t.find("\n\n", t.find("| A8 |"))
block = t[start + 2:end]
lines = block.splitlines()
head = lines[0].rstrip(" |") + " | Δ vs A0 [95% CI] | p (exact Wilcoxon) |"
sep = "|---|---|---|---|---|---|---|"
out = [head, sep]
for ln in lines[2:]:
    if not ln.startswith("|"):
        continue
    cells = [c.strip() for c in ln.strip().strip("|").split("|")]
    arm = cells[0]
    if arm in rows:
        m, lo, hi, pv = rows[arm]
        cells = cells + [f"{m:+.2f} [{lo:+.2f}, {hi:+.2f}]", ("1.000" if pv == 1.0 else f"{pv:.3f}")]
    else:
        cells = cells + ["—", "—"]
    out.append("| " + " | ".join(cells) + " |")
t = t[:start + 2] + "\n".join(out) + t[end:]

# --- Table X caption: paired CIs for the four contrasts -------------------
caps = []
for base, name in (("mined_16", "the mined 16 s rule"), ("ppomlp_mined_16", "the same-rule PPO-MLP baseline"),
                   ("tuned_constant", "the tuned constant"), ("reward_lam8", "the best reward penalty")):
    vals = [paired(lk["instances"][i]["deployed_18"]["polar"], lk["instances"][i][base]["polar"])
            for i in ("eval", "lb299.25", "lb306.25", "lb290.25")]
    lo = min(v[1] for v in vals)
    hi = max(v[2] for v in vals)
    pmax = max(v[3] for v in vals)
    caps.append(f"against {name} {min(v[0] for v in vals):+.2f} to {max(v[0] for v in vals):+.2f} pp "
                f"(paired 95% CI {lo:+.2f} to {hi:+.2f}; exact Wilcoxon p ≤ {pmax:.3f})")
STAT = ("Paired over the ten policy seeds: " + "; ".join(caps) + ". The deployed arm and the tuned constant are "
        "statistically indistinguishable on every instance, which is why the paper reports that contrast as a tie "
        "and claims no accuracy advantage for calibration—only automation and auditability.")

old_cap = ("**Table X. Full three-way lockbox (polar HSR, |lat| ≥ 70°, campaign policies, traffic seed 0, "
           "n = 10 policy seeds per instance).**")
if t.count(old_cap) != 1:
    raise SystemExit(f"Table X caption count {t.count(old_cap)}")
t = t.replace(old_cap, old_cap + "\n\n" + STAT, 1)

p.write_text(t, encoding="utf-8")
print("tables updated")
