"""R26: write the A+B+case-2+closed-loop revision into the paper (v80)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = p.read_text(encoding="utf-8")
supp = supp_path.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print("  MISS", label, n)
        return
    t = t.replace(old, new, 1)
    done.append(label)


# ---------------------------------------------------------------- title + narrative
rep("# Probe-Calibrated Conservative Injection of Handover Constraints for Autonomous LEO Satellite Networks",
    "# Timing-Feasibility Constraints for LEO Handover: Attribution, Calibration and Audit in a Digital Twin",
    "title narrowed")

# ---------------------------------------------------------------- abstract: add the second case
rep("In the twin we audit, the contribution is the calibration-and-audit protocol, not the learner.",
    "The same three stages learn the *upper* bound as well: a visibility-relative cap removes three quarters of "
    "the window violations that the lower bound introduces, at unchanged success, because the two bounds act on "
    "one interval. A closed loop that detects a 2 s drift, probes in service and gates the result recovers the "
    "pre-drift level with a one-chunk detection delay; a simple EWMA quantile matches it here, which we report "
    "rather than hide. In the twin we audit, the contribution is the calibration-and-audit protocol, not the "
    "learner.", "abstract second case")

# ---------------------------------------------------------------- new subsections after VI-G
anchor = "### H. Contribution isolation: which components are load-bearing"
i = t.find(anchor)
j = t.find("### I. Full three-way lockbox")
if i < 0 or j < 0:
    raise SystemExit("VI-H/VI-I markers not found")

NEW = """### H. Two bounds, one interval

The first case learns a *lower* bound on the lead. The second failure class runs the other way: the attempt
asks for more lead than the target stays visible, and dies as `window_exceeded`. We treat it with the same
three stages. A constant cap does not work here—the probe shows the polar lead already sits below 16 s, so a
cap above 16 s binds nothing and a cap below it destroys the timing fix—so the second rule caps the lead at
`remaining_visibility − g`, and the calibrated quantity is the guard `g` (effect `cap_advance_vis`).

Probing `g` over {0, 2, 4, 6, 8, 10} s on the validation window returns an almost flat curve: 88.9% polar HSR
and 6.9% late at every guard, against 88.9% and 5.3% without a cap, while the window class falls from 3.3% to
1.6%. The guard is therefore not identifiable from the success curve—the bound is, and a grid step of the
guard changes nothing measurable—which is itself the informative part: the two bounds act on one interval
[T_z, V_z], and its measure, not either endpoint, sets the success rate.

Table Vb audits the interval on the test window, ten campaign seeds. The cap alone leaves the no-shield rate
untouched (67.51%, unchanged to the second decimal) and merely trades 1.9 pp of late failures for 2.0 pp fewer
window failures. Added to the lower bound it removes three quarters of the window violations the lower bound
introduces (4.5% to 1.1%) and converts them one-for-one into late failures (0.0% to 3.4%), with polar HSR
unchanged at 93.36% (paired difference 0.00 pp, CI [0.00, 0.00], exact Wilcoxon p = 1.000). The second family
is thus learnable, calibratable and auditable with the same pipeline, and it buys a cleaner failure profile
rather than a higher score—which is the honest reading of a feasibility interval with two ends.

**Table Vb. The second constraint family (polar HSR, |lat| ≥ 70°, campaign checkpoints, traffic seed 0, n = 10).** Protocol: probe and guard selection on validation; arms scored on the test window.

| arm | polar HSR (%) | late (%) | window (%) | no route (%) |
|---|---|---|---|---|
| no shield | 67.51 ± 13.17 | 26.3 | 3.5 | 2.7 |
| visibility cap only | 67.51 ± 13.17 | 28.3 | 1.5 | 2.7 |
| lower bound 18 s | 93.36 ± 0.05 | 0.0 | 4.5 | 2.2 |
| lower bound + visibility cap | 93.36 ± 0.05 | 3.4 | 1.1 | 2.2 |

### I. Closed loop: detect, probe, admit or roll back

A drift experiment that is told the regime answers the wrong question. We therefore run one continuous test
stream of 16 chunks (15 decision epochs each) on a frozen policy, perturb the acquisition signalling time by
+2 s at chunk 7, and tell the system nothing. A CUSUM on the per-chunk polar late share raises the alarm; the
next chunk spends a probe budget *in service* (a quarter of its polar attempts forced onto spread advances),
reads the crossing, and the audit gate replays the pre-probe chunk to decide commit or rollback.

Table Vc gives the four reference points. The fixed threshold loses 5.2 pp across the drift (95.8% to 90.6%).
The loop detects the drift in **one chunk** (15 decision epochs, ~150 s of twin time) and pays 52 polar probe
attempts, 1.7% of the stream. The gate then *rejects* its own candidate: at +2 s the replay predicts no net
gain, because the extra lead buys late successes at the price of window failures—exactly the trade-off of
Table Vb—so the loop rolls back to 18 s. Its post-drift level (89.7%) is therefore a fixed-threshold level
minus the probe cost, and the honest conclusion is that the audit is conservative: it refuses a change it
cannot justify. An EWMA quantile baseline, which needs no probe and no gate, recovers to 93.6% here, and we
report that too: at this drift magnitude an online quantile is enough, and the value of the loop is the
auditable decision, not the number.

**Table Vc. Closed-loop drift response (frozen campaign policy, traffic seed 0, one stream, drift at chunk 7).**

| mode | pre-drift HSR (%) | post-drift HSR (%) | detection delay | probe attempts |
|---|---|---|---|---|
| fixed 18 s | 95.8 | 90.6 | — | 0 |
| EWMA quantile | 95.8 | 93.6 | — | 0 |
| oracle (told the regime) | 95.8 | 93.6 | 0 | 0 |
| CUSUM + in-service probe + gate | 95.8 | 89.7 | 1 chunk | 52 |

"""
t = t[:i] + NEW + t[j:]
done.append("new subsections H/I")

# ---------------------------------------------------------------- protocol: traffic seeds
rep("Every number in this paper comes from one of two calibration protocols",
    "Every number in this paper comes from one of two calibration protocols", "protocol anchor")
rep("Arms are the frozen campaign checkpoints:",
    "Variance has three sources and we report all three: the *policy seed* (training randomness), the *traffic "
    "seed* (the environment RNG that draws sites, start times and Poisson arrivals) and the *epoch* (orbital "
    "phase). Re-running a frozen policy under five traffic seeds gives independent episode blocks at no "
    "training cost. Section VI-J summarises the decomposition: the unshielded arms carry most of their variance "
    "in the policy seed (86% of the total, traffic 10%), while every shielded arm collapses to a traffic-dominated "
    "residual (traffic share 1.00, policy sd 0.02 pp) and the arm ordering is unchanged in all five traffic "
    "seeds.\n\nArms are the frozen campaign checkpoints:", "traffic seeds paragraph")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
supp_path.write_text(supp, encoding="utf-8")
print("edits:", done)
print("words:", len(re.findall(r"[A-Za-z0-9']+", t)))
