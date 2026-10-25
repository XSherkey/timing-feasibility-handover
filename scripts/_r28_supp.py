"""R28 pass 2: supplement repairs - H2 body, D2 with both columns, K1 definition, title, stale refs."""
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

# ---- main: feeder slot sentence (line-wrapped) -----------------------------
t, n = re.subn(r"`t_slot = 1\.8 s` and `s = 3` feeder slots against the `P` satellites visible from the target's best\ngateway,",
               "`t_slot = 1.8 s` and `s` feeder slots (three in the nominal configuration, one in the capacity-stress arm) "
               "against the `P` satellites visible from the target's best gateway,", t)
print("feeder slots:", n)

# ---- supplement: title -----------------------------------------------------
s = s.replace("**Supplementary Material for “Probe-Calibrated Conservative Injection of Handover Constraints for "
              "Autonomous LEO Satellite Networks”**",
              "**Supplementary Material for “Timing-Feasibility Constraints for LEO Handover: Attribution, Calibration "
              "and Audit in a Digital Twin”**")

# ---- supplement: Appendix N still carries its old heading -------------------
s = s.replace("### M. Deployment and governance\n\n", "")

# ---- supplement: H2 body ---------------------------------------------------
bank = json.loads((ROOT / "results/routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
i = s.find("## Appendix H2. Drift response")
if i > 0:
    j = s.find("\n\n## Appendix ", i + 10)
    block = s[i:j if j > 0 else len(s)]
    if "| extra acquisition latency" not in block:
        BODY = ("\n\n| extra acquisition latency | 0 | +2.0 s | +3.2 s | +4.4 s |\n|---|---|---|---|---|\n"
                "| tuned constant, fixed 18 s | 93.33 | 92.39 | 85.98 | 83.56 |\n"
                "| constant re-probed on validation + 2 s margin | 93.33 | 93.20 | 93.20 | 93.20 |\n"
                "| shielded policies, fixed 18 s rule | 93.36 ± 0.05 | 92.42 ± 0.05 | 86.01 ± 0.06 | 83.47 ± 0.34 |\n"
                "| shielded policies, threshold re-probed + 2 s | 93.36 ± 0.05 | 93.23 ± 0.05 | 93.23 ± 0.05 | 93.23 ± 0.05 |\n"
                "| narrative 16 s rule (fixed magnitude) | 91.60 | 84.79 | 81.25 | 77.49 |\n"
                "| probe study (five policy seeds) | 16 (5/5) | 18 (5/5) | 20 (5/5) | 22 (4/5), 20 (1/5) |\n")
        s = s[:i] + block.rstrip() + BODY + s[j if j > 0 else len(s):]
        done.append("H2 body")

# ---- supplement: D2 with admission and post-hoc effect ---------------------
gs = json.loads((ROOT / "results/routeA_r3" / "gate_systematic" / "summary.json").read_text(encoding="utf-8"))
rows = ["| id | validation gain (pp) | admission | evaluation effect (pp) | post-hoc label |",
        "|---|---|---|---|---|"]
for c in sorted(gs["bank"], key=lambda b: b["id"]):
    rows.append(f"| {c['id']} | {c['delta_short']:+.2f} | {'admit' if c['admit_short'] else 'reject'} | "
                f"{c['delta_test']:+.2f} | {c['class']} |")
D2 = ("**Table D2. The full 26-candidate gate bank.** The gate decides on the validation gain only (admission "
      "requires > 5 pp); the evaluation effect is measured afterwards, on the window the gate never sees, and is what "
      "assigns the post-hoc label — harmful if the effect is negative, neutral if 0 ≤ Δ < 5 pp, good if Δ ≥ 5 pp. "
      "Because the label is computed from a column the gate does not read, the confusion matrix below is an audit and "
      "not a tautology.\n\n" + "\n".join(rows) + "\n")
i = s.find("**Table D2.")
if i > 0:
    j = s.find("\n\n## Appendix ", i)
    s = s[:i] + D2 + ("\n" if j < 0 else "") + ("" if j < 0 else s[j:])
    done.append("D2 regenerated")

# ---- supplement: stale references -----------------------------------------
for old, new in (("Section VI-L", "Section VI-L"), ("Table IV", "Table M1"), ("Table V ", "Table H2 ")):
    n = s.count(old)
    if old != new and n:
        s = s.replace(old, new)
        done.append(f"supp ref {old}->{new} x{n}")

main.write_text(re.sub(r"\n{3,}", "\n\n", t), encoding="utf-8")
supp_path.write_text(re.sub(r"\n{3,}", "\n\n", s), encoding="utf-8")
print("edits:", done)
