"""R10 part 2: Fig. 4 caption numbers, gate caption, kappa sentence, schema note."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
pc = json.loads((ROOT / "results" / "routeA_r3" / "passive_ci" / "summary.json").read_text(encoding="utf-8"))
bc = json.loads((ROOT / "results" / "routeA_r3" / "passive_ci" / "budget_curves.json").read_text(encoding="utf-8"))
ci = pc["bootstrap"]["ci95"]
w_full = pc["bootstrap"]["width_s"]
iid_full = [c["width"] for c in bc["iid"] if c["n"] == 8682][0]
cl_full = [c["width"] for c in bc["cluster"] if c["n"] == 8682][0]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old[:60]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# ---- Fig. 4 caption: explicit widths -------------------------------------
i = t.find("**Fig. 4.**")
if i < 0:
    raise SystemExit("Fig. 4 caption not found")
j = t.find("\n\n", i)
CAP = (f"**Fig. 4.** Passive support and sample budget. (a) Late-handover rate against the handover advance "
       f"in the passive no-shield log (PPO-MLP, ten seeds, |lat| ≥ 68°, {pc['n_attempts']:,} attempts), with "
       f"binomial 95% intervals and a PAVA monotone fit; the shaded band is the cluster-bootstrap 95% interval "
       f"of the 5%-crossing, [{ci[0]:.0f}, {ci[1]:.0f}] s, i.e. {w_full:.0f} s wide and five grid points. (b) "
       f"Width of that interval against the number of attempts drawn. Resampling attempts independently "
       f"(light) collapses to one grid step (2 s) by 1,000 attempts and to {iid_full:.0f} s at the full budget, "
       f"while resampling (seed, site) blocks (dark) stays at 4–{cl_full:.0f} s and ends at {cl_full:.0f} s on "
       f"the full log—the same number as the shaded band in (a). Below ≈500 attempts the cluster estimate is "
       f"itself degenerate (every replicate returns the same crossing, so the width is 0) and the curve is "
       f"informative only above ≈1,000 attempts. The passivity of the log, not its size, is the binding "
       f"constraint.")
t = t[:i] + CAP + t[j:]
done.append("fig4-caption")

# ---- gate table caption: the effect is an audit label, not a gate input ---
rep("**Table XI. Audit gate over 26 candidates (confusion against the measured effect of each candidate on "
    "the evaluation window; admission requires a replay gain above 5 pp with a positive lower bound).**",
    "**Table XI. Audit gate over 26 candidates.** Each candidate is labelled *harmful*, *neutral* or *good* by "
    "its measured effect on the evaluation window—a post-hoc audit label, never an input to the gate—while the "
    "gate itself admits only on a validation-window replay gain above 5 pp with a positive lower bound. The "
    "confusion is therefore between an admission decision taken on validation and a label assigned on the "
    "evaluation window, which is what makes it an honest audit rather than a tautology.", "gate-caption")

# ---- kappa sentence ------------------------------------------------------
i = t.find("agree on only four of the five items")
if i > 0:
    j = t.find(".", i)
    print("kappa sentence:", t[max(0, i - 160):j + 1])
    t = t[:i] + t[j + 1:]

p.write_text(t, encoding="utf-8")
print("applied:", done)
