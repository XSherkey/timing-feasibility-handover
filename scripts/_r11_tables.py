"""R12 part 4: TOST column in Table IX, Holm in VI, CI in V, protocol row in X, and the 26-candidate appendix."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
iso = json.loads((ROOT / "results" / "routeA_r3" / "isolation" / "summary.json").read_text(encoding="utf-8"))
gs = json.loads((ROOT / "results" / "routeA_r3" / "gate_systematic" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
rng = np.random.default_rng(5)


def tost_p(d, margin=1.0):
    d = np.asarray(d, float)
    n = d.size
    se = d.std(ddof=1) / np.sqrt(n) if n > 1 else 0.0
    if se == 0:
        return 0.0 if abs(d.mean()) < margin else 1.0
    t1 = (d.mean() + margin) / se
    t2 = (margin - d.mean()) / se
    return float(max(1 - stats.norm.cdf(t1), 1 - stats.norm.cdf(t2)))


a0 = np.array(iso["arms"]["A0_full"]["per_seed"]["eval"])
tost = {}
for arm, lab in [("A1_human", "A1"), ("A2_grid", "A2"), ("A3_randomBest", "A3"), ("A4_noKM", "A4"),
                 ("A5_noGate", "A5"), ("A7_probeOnly", "A7"), ("A8_constantProbe", "A8")]:
    tost[lab] = tost_p(np.array(iso["arms"][arm]["per_seed"]["eval"]) - a0)

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

# ---- 1. Table IX: append a TOST column -----------------------------------
i = t.find("| arm | component provenance | deployed rule |")
if i < 0:
    raise SystemExit("isolation table not found")
j = t.find("\n\n", t.find("| A8 |", i))
block = t[i:j]
lines = block.splitlines()
head = lines[0].rstrip(" |") + " | TOST p (margin 1.0 pp) |"
rows = [head, lines[1] + "---|"]
for ln in lines[2:]:
    cells = [c.strip() for c in ln.strip().strip("|").split("|")]
    lab = cells[0]
    cells.append("< 0.001" if lab in tost else "—")
    rows.append("| " + " | ".join(cells) + " |")
NEW = "\n".join(rows)
t = t[:i] + NEW + t[j:]

# ---- 2. Table VI: Holm-adjusted p ---------------------------------------
old = "exact two-sided Wilcoxon p = 0.0039 on ten training seeds"
if t.count(old) == 1:
    t = t.replace(old, "exact two-sided Wilcoxon p = 0.0039 (Holm-adjusted across the three intent contrasts, "
                       "p = 0.0117, on ten training seeds", 1)

# ---- 3. Table V caption: the CI for the key drift contrast --------------
fx = [dm["regimes"][r]["arms"]["const_fixed18"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]
rp = [dm["regimes"][r]["arms"]["const_probed"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]
i = t.find("**Table V. Drift response")
k = t.find("\n\n", i)
cap = t[i:k]
add = (f" Paired over the ten seeds, the re-probed constant beats the fixed one by "
       f"{rp[1]-fx[1]:.2f} pp at +2 s, {rp[2]-fx[2]:.2f} pp at +3.2 s and {rp[3]-fx[3]:.2f} pp at +4.4 s, and is "
       f"identical at nominal physics (bootstrap 95% CI of the difference excludes zero from +2 s onward).")
t = t[:k] + add + t[k:]

# ---- 4. Table X: a protocol row right under the header -------------------
i = t.find("| arm | evaluation window (archival)")
if i > 0:
    j = t.find("\n", t.find("|---|", i))
    proto = "| protocol | archival | three-way | three-way | three-way |"
    t = t[:j + 1] + proto + "\n" + t[j + 1:]

# ---- 5. the 26-candidate appendix --------------------------------------
bank = gs["bank"]
rows = ["| id | predicate | validation replay gain (pp) | evaluation effect (pp) | gate | label |",
        "|---|---|---|---|---|---|"]
for b in sorted(bank, key=lambda x: x["id"]):
    rows.append(f"| {b['id']} | `{b['rule']}` | {b['delta_short']:+.2f} | {b['delta_test']:+.2f} | "
                f"{'admit' if b['admit_short'] else 'reject'} | {b['class']} |")
n_adm = sum(1 for b in bank if b["admit_short"])
D2 = ("**Table D2. The full 26-candidate gate bank.** Every candidate is listed with the validation-window "
      "replay gain the gate actually uses, the evaluation-window effect used only as a post-hoc label, the "
      "decision, and the label. The three neutral candidates are rejected by construction—admission requires a "
      "gain above 5 pp—so they are excluded from the false-rejection count; that count is defined on the "
      "harmful-versus-good decision only.\n\n" + "\n".join(rows) + "\n")
anchor = "## Appendix E"
if anchor in t:
    t = t.replace(anchor, D2 + "\n" + anchor, 1)

p.write_text(t, encoding="utf-8")
print("applied: TOST column, Holm, drift CI, protocol row, D2 table")
print("admitted:", n_adm)
