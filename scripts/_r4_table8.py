"""R4 (v16) part 3: rebuild Table VIII from the consistent lockbox run and fix its prose."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

src = ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json"
if not src.exists():
    raise SystemExit("consistent lockbox summary not ready")
d = json.loads(src.read_text(encoding="utf-8"))

ORDER = ["mined_16", "deployed_18", "tuned_constant", "ppomlp_mined_16", "reward_lam8", "oracle"]
LABEL = {"eval": "evaluation window 82–95%", "lb299.25": "lockbox +7 d (299.25)",
         "lb306.25": "lockbox +14 d (306.25)", "lb290.25": "lockbox −2 d (290.25)"}
rows = ["| instance | mined-rule (16 s) | deployed (τ_used = 18 s) | tuned constant | PPO-MLP + mined 16 s | reward λ = 8 | oracle shield |",
        "|---|---|---|---|---|---|---|"]
for inst in ("eval", "lb299.25", "lb306.25", "lb290.25"):
    cell = d["instances"][inst]
    rows.append("| %s | %s |" % (LABEL[inst], " | ".join("%.2f" % cell[a]["summary"]["mean"] for a in ORDER)))

cap = ("**Table VIII. Full three-way lockbox (polar HSR, |lat| ≥ 70°, campaign policies, traffic seed 0, "
       "n = 10 policy seeds per instance; every selection made on the validation window and frozen "
       "before any lockbox rollout).**")
TABLE = cap + "\n\n" + "\n".join(rows) + "\n"

start = t.find("**Table VIII. Full three-way lockbox")
end = t.find("\n\n", t.find("| lockbox −2 d", start))
if start < 0 or end < 0:
    raise SystemExit("Table VIII block not found")
t = t[:start] + TABLE + t[end:]

old_tail = ("The lockbox therefore supports the *ordering* claims under frozen selection, and it bounds—rather than\n"
            "eliminates—the optimism of an evaluation-window result: the three selections were made once, on one\n"
            "window, and are then held fixed. We report the evaluation-window numbers and the lockbox numbers side\n"
            "by side in Table VIII and give their difference, so a reader can see exactly how much of the headline\n"
            "survives the change of window.")
new_tail = ("Every row of Table VIII is produced by the same policy set, the same traffic seed and the same "
            "episode protocol; the only thing that changes between rows is the twin epoch. This matters "
            "because an earlier version of this table mixed the fixed-architecture replica policies (used by "
            "the factorial of Table C2, whose deployed arm reads 93.31 on the evaluation window) with a "
            "traffic seed that varied per policy seed; the two protocols differ by about 1 pp on the same "
            "arm, which is larger than the effect of the epoch shift itself. Table VIII therefore reports the "
            "campaign policies only, and the evaluation row is the reference the lockbox rows are compared "
            "against.\n\n"
            "The lockbox supports the *ordering* claims under frozen selection, and it bounds—rather than "
            "eliminates—the optimism of an evaluation-window result: the three selections were made once, on "
            "one window, and are then held fixed.")
if t.count(old_tail) != 1:
    raise SystemExit(f"tail paragraph found {t.count(old_tail)}")
t = t.replace(old_tail, new_tail, 1)
p.write_text(t, encoding="utf-8")
print("Table VIII rebuilt from the consistent run")
print("\n".join(rows))
