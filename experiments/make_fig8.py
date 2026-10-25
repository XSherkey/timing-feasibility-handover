"""Regenerate Fig. 8 (six references at nominal and +2 s) from the unified ladder."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTF = ROOT.parent / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "figures"
d = json.loads((ROOT / "results" / "routeA_r3" / "ladder_consistent" / "summary.json").read_text(encoding="utf-8"))
plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.7, "savefig.dpi": 300})

ORDER = [("no_knowledge", "no knowledge"), ("reward_lam8", "reward λ = 8"),
         ("narrative_16s_rule", "narrative 16 s rule"), ("tuned_constant_18", "tuned 18 s constant"),
         ("deployed_probe_shield", "deployed shield"), ("oracle", "oracle")]
nom = [d["regimes"]["nominal"][k]["summary"]["mean"] for k, _ in ORDER]
p2 = [d["regimes"]["plus2s"][k]["summary"]["mean"] for k, _ in ORDER]
nom_sd = [d["regimes"]["nominal"][k]["summary"]["sd"] for k, _ in ORDER]
p2_sd = [d["regimes"]["plus2s"][k]["summary"]["sd"] for k, _ in ORDER]

x = np.arange(len(ORDER))
fig, ax = plt.subplots(figsize=(6.6, 2.9))
ax.bar(x - 0.19, nom, width=0.36, yerr=nom_sd, capsize=2, color="#4a7fb5", label="nominal physics",
       error_kw=dict(elinewidth=0.7, ecolor="#333333"))
ax.bar(x + 0.19, p2, width=0.36, yerr=p2_sd, capsize=2, color="#c0392b", label="+2 s acquisition drift",
       error_kw=dict(elinewidth=0.7, ecolor="#333333"))
for xi, v in zip(x - 0.19, nom):
    ax.text(xi, v + 1.0, f"{v:.1f}", ha="center", fontsize=6.2)
for xi, v in zip(x + 0.19, p2):
    ax.text(xi, v + 1.0, f"{v:.1f}", ha="center", fontsize=6.2)
ax.set_xticks(x)
ax.set_xticklabels([lbl for _, lbl in ORDER], fontsize=6.4, rotation=18, ha="right")
ax.set_ylim(40, 102)
ax.set_ylabel("polar handover success (%)")
ax.legend(fontsize=6.5, frameon=False, loc="lower left")
ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(OUTF / "fig6_forms.png")
fig.savefig(OUTF / "fig6_forms.pdf")
print("Fig. 8 regenerated:", dict(zip([k for k, _ in ORDER], [round(v, 1) for v in nom])),
      dict(zip([k for k, _ in ORDER], [round(v, 1) for v in p2])))
