"""R7 part 4: D1A/D1B with an explicit check column, and Table C3 rebuilt for the shielded arms."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
mr = dm["regimes"]
REGS = ["1.2", "3.2", "4.4", "5.6"]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# ---- D1A / D1B: add a check column --------------------------------------
for tag, total_label in (("D1A", "Table D1A."), ("D1B", "Table D1B.")):
    i = t.find(f"**{total_label}")
    j = t.find("\n\n", t.find("| total |", i))
    if i < 0 or j < 0:
        raise SystemExit(f"{tag} block not found")
    block = t[i:j]
    lines = [ln for ln in block.splitlines() if ln.strip()]
    out = []
    for ln in lines:
        if not ln.startswith("|"):
            out.append(ln)
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("- "):
            out.append(ln)
            continue
        if cells[0].lower().startswith("advance") or cells[0].lower().startswith("total"):
            if cells[0].lower().startswith("advance"):
                cells = cells + ["Σ = exc + cen + comp"]
            else:
                cells = cells + [cells[1] if False else str(sum(int(c.replace(",", "")) for c in cells[2:5]))]
            out.append("| " + " | ".join(cells) + " |")
            continue
        exc, cen, comp = (int(c.replace(",", "")) for c in cells[2:5])
        s = exc + cen + comp
        att = int(cells[1].replace(",", ""))
        flag = "" if att == s else " **≠**"
        cells = cells + [f"{s:,}{flag}"]
        out.append("| " + " | ".join(cells) + " |")
    t = t[:i] + "\n".join(out) + t[j:]
    done.append(tag)

# ---- Table C3 ------------------------------------------------------------
i = t.find("**Table C3. Drift response per seed")
j = t.find("\n\n", t.find("| calibrated |", i)) if t.find("| calibrated |", i) > 0 else t.find("\n\n", t.find("| mean ± sd", i))
if i < 0 or j < 0:
    raise SystemExit("C3 not found")
rows = ["| seed | fixed 18 s: δ=0 | +2 s | +3.2 s | +4.4 s | re-probed: δ=0 | +2 s | +3.2 s | +4.4 s |",
        "|---|---|---|---|---|---|---|---|---|"]
for k in range(10):
    fx = [mr[r]["arms"]["shield_fixed18"]["polar"][k] for r in REGS]
    rp = [mr[r]["arms"]["shield_probed"]["polar"][k] for r in REGS]
    rows.append("| %d | %s | %s |" % (k, " | ".join("%.2f" % v for v in fx),
                                      " | ".join("%.2f" % v for v in rp)))
fx_mean = [mr[r]["arms"]["shield_fixed18"]["summary"]["mean"] for r in REGS]
rp_mean = [mr[r]["arms"]["shield_probed"]["summary"]["mean"] for r in REGS]
rows.append("| mean | %s | %s |" % (" | ".join("%.2f" % v for v in fx_mean),
                                    " | ".join("%.2f" % v for v in rp_mean)))
taus = [mr[r]["tau_mode"] for r in REGS]
used = [mr[r]["m2"]["summary"]["mean"] if False else mr[r]["tau_mode"] + 2 for r in REGS]
rows.append("| τ∗ (probe) | %s | %s |" % (" | ".join("%.0f" % v for v in taus), " | ".join("%.0f" % v for v in taus)))
rows.append("| τ_used = τ∗ + 2 | %s | %s |" % (" | ".join("%.0f" % v for v in used), " | ".join("%.0f" % v for v in used)))
C3 = ("**Table C3. Drift response per seed, polar HSR (%) at |lat| ≥ 70°, campaign policies, traffic seed 0, "
      "n = 10 policy seeds. Left block: the shield with a fixed 18 s threshold. Right block: the shield with "
      "the threshold re-probed on each physics (τ∗) and the 2 s margin applied (τ_used). The tuned constant is "
      "policy-independent and is therefore not tabulated per seed; its four regime means are "
      "93.33 / 92.39 / 85.98 / 83.56.**\n\n" + "\n".join(rows) + "\n")
t = t[:i] + C3 + t[j:]
done.append("C3")

p.write_text(t, encoding="utf-8")
print("applied:", done)
