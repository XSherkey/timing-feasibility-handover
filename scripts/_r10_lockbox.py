"""R11 part 1: transpose the lockbox table (9 columns -> 5) and resolve the protocol contradiction."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
gs = json.loads((ROOT / "results" / "routeA_r3" / "gate_systematic" / "summary.json").read_text(encoding="utf-8"))
I = lk["instances"]
INSTS = [("eval", "evaluation window (archival)"), ("lb299.25", "+7 d (three-way)"),
         ("lb306.25", "+14 d (three-way)"), ("lb290.25", "−2 d (three-way)")]
ARMS = [("no_shield", "no shield, full-system"), ("ppomlp_no_shield", "no shield, PPO-MLP"),
        ("mined_16", "mined 16 s rule"), ("deployed_18", "**deployed, τ_used = 18 s**"),
        ("tuned_constant", "tuned constant, 18 s"), ("ppomlp_mined_16", "PPO-MLP + 16 s rule"),
        ("reward_lam8", "reward penalty λ = 8"), ("oracle", "oracle shield")]
n_adm = sum(1 for b in gs["bank"] if b["admit_short"])

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

# ---- 1. transpose the lockbox table --------------------------------------
i = t.find("| instance | no shield (full)")
if i < 0:
    raise SystemExit("lockbox table not found")
j = t.find("\n\n", t.find("| lockbox −2 d", i))
rows = ["| arm | " + " | ".join(lbl for _, lbl in INSTS) + " |", "|" + "---|" * 5]
for arm, lab in ARMS:
    cells = " | ".join("%.2f" % I[inst][arm]["summary"]["mean"] for inst, _ in INSTS)
    rows.append(f"| {lab} | {cells} |")
TABLE = "\n".join(rows)
t = t[:i] + TABLE + t[j:]

# ---- 2. the contradictory lockbox paragraph ------------------------------
old = ("The mined rule, the gate decisions, and λ = 8 remain exactly as originally frozen—which also means "
       "that the *selection* of those three items still originates in the original evaluation window; the "
       "lockbox freezes that selection and measures it, it does not re-select anything.")
new = (f"Each of the three selections is also recoverable from the validation window alone: the probe returns "
       f"τ∗ = 16 s there, the λ scan returns λ = 8 there (81.52% validation polar HSR), and re-running the gate's "
       f"admission on the validation replay alone returns the identical {n_adm} admissions and the identical "
       f"{26 - n_adm} rejections (no candidate's decision changes when the evaluation-window replay is dropped). "
       f"The lockbox therefore measures a selection set that the validation window alone reproduces; what it "
       f"adds is that nothing in it was ever consulted.")
if t.count(old) != 1:
    raise SystemExit(f"lockbox paragraph count {t.count(old)}")
t = t.replace(old, new, 1)

# ---- 3. Section VI-I opening: say re-derived, not merely removed ---------
old2 = ("The earlier protocol let three choices touch the evaluation window: the audit gate's admission, the "
        "probe that fixes τ∗, and the reward-penalty coefficient λ. The three-way protocol removes that by "
        "construction.")
new2 = ("The earlier protocol let three choices touch the evaluation window: the audit gate's admission, the "
        "probe that fixes τ∗, and the reward-penalty coefficient λ. The three-way protocol removes that by "
        "construction, and it does so without changing any of the three: each is independently re-derived on "
        "the validation window and returns the same value (Section VI-I).")
if t.count(old2) == 1:
    t = t.replace(old2, new2, 1)

p.write_text(t, encoding="utf-8")
print("EN updated")
print(TABLE)
