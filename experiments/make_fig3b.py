"""Fig. 3 v2: categorical lambda axis (lambda = 0 included) and an unconnected frontier."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUTF = ROOT.parent / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "figures"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]
plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.7, "savefig.dpi": 300})

xs = ["0", "0.3", "0.5", "2", "8", "16", "32", "64"]
rec = []
for x in xs:
    arm = "noforensics_none" if x == "0" else f"lam{x}"
    rec.append((x, A[arm]["summary"]["mean"], A[arm]["summary"]["sd"], A[arm]["satisfaction_mean"]))
shield_hsr = A["almond_rule18"]["summary"]["mean"]
shield_s = A["almond_rule18"]["satisfaction_mean"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.6))
pos = range(len(rec))
ax1.errorbar(list(pos), [r[1] for r in rec], yerr=[r[2] for r in rec], marker="o", ms=3.5, lw=1.0,
             capsize=2, color="#c0392b", ecolor="#999999", elinewidth=0.7)
ax1.axhline(shield_hsr, ls="--", lw=0.9, color="#2e5f8a")
ax1.text(len(rec) - 1.4, shield_hsr + 0.9, "shield %.2f" % shield_hsr, fontsize=6.5, color="#2e5f8a")
ax1.set_xticks(list(pos))
ax1.set_xticklabels(xs, fontsize=6.4)
ax1.set_xlabel("penalty coefficient λ")
ax1.set_ylabel("polar HSR (%)")
ax1.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
ax1.set_axisbelow(True)

ax2.plot([r[1] for r in rec], [r[3] for r in rec], "o", ms=4, color="#c0392b")
for x, v, sd, s in rec:
    ax2.annotate(x, (v, s), fontsize=5.6, textcoords="offset points", xytext=(4, -3))
ax2.plot([shield_hsr], [shield_s], "*", ms=11, color="#2e5f8a")
ax2.annotate("shield", (shield_hsr, shield_s), fontsize=6.2, textcoords="offset points", xytext=(-34, 3))
ax2.set_xlabel("polar HSR (%)")
ax2.set_ylabel("satisfaction S")
ax2.grid(ls=":", lw=0.5, alpha=0.6)
ax2.set_axisbelow(True)
fig.tight_layout()
fig.savefig(OUTF / "fig4_lambda_frontier.png")
fig.savefig(OUTF / "fig4_lambda_frontier.pdf")
print("Fig. 3 regenerated")
