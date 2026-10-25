"""R3 (v10) — insert the new TNSM sections into the English manuscript.

Adds: Table VI rebuilt from fresh evaluations, Section VI-H (contribution isolation),
VI-I (full three-way lockbox), VI-J (statistical protocol), VI-K (deployment and governance),
Figures 8/9 captions, and the new Appendix-A commands.  Numbers that depend on a still-running
experiment are filled by a follow-up patch.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


# ---------------------------------------------------------------- Table VI
alt = json.loads((ROOT / "results" / "routeA_r3" / "alternative_physics" / "summary.json").read_text(encoding="utf-8"))


def cell(key: str, field: str, fmt: str = "%.1f") -> str:
    v = alt[key]
    if field == "hsr":
        return fmt % v["polar"]["mean"]
    return fmt % v[field]


rows = []
for twin in ("seam disabled", "feeder 3 slots"):
    for pol in ("full-system", "PPO-MLP"):
        for arm in ("no shield", "mined 16 s", "tau_used = 18 s"):
            k = f"{twin}|{pol}|{arm}"
            rows.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                twin, pol, arm, cell(k, "hsr"), cell(k, "late"), cell(k, "window"), cell(k, "no_route")))
TABLE6 = (
    "| twin variant | arm | polar HSR (%) | late share (%) | window exceeded (%) | no route (%) |\n"
    "|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n"
)
i = t.find("**Table VI. Alternative physics")
j = t.find("\n\n", t.find("|", t.find("\n", i)))
old_block_start = i
old_block_end = t.find("Probe cost and limits.", i)
if i < 0 or old_block_end < 0:
    raise SystemExit("Table VI block not found")
new_block = ("**Table VI. Alternative physics (polar HSR, mean over n = 5 policy seeds; polar band |lat| ≥ 70°; "
             "frozen policies; the shield applies rule (4) with τ_used = 18 s where a shield is present).**\n\n"
             + TABLE6 + "\n")
t = t[:old_block_start] + new_block + t[old_block_end:]
done.append("table6")

# ---------------------------------------------------------------- VI-H..K
VIH = """### H. Contribution isolation: which components are load-bearing

The audit so far shows that the constraint matters. It does not show which part of the pipeline is
responsible for finding it. We therefore hold everything behind the shield fixed—same twin, same
common episodes, same probe procedure, same 2 s margin, same shield semantics—and vary only where
the predicate and the magnitude come from, and whether the audit gate and the knowledge graph are in
the loop. Every selection (predicate source, threshold, lead) is made on the validation window; the
test window and the three lockbox epochs are only ever scored. Table VII reports the nine arms.

@@TABLE_ISOLATION@@

Three results follow, and we state them against our own earlier framing. *First, the provenance of
the predicate is not load-bearing in this twin.* The language model, the hand-written predicates and
the latitude grid all converge on a rule that fires in the polar band with a 16 s magnitude; the
deployed outcomes of A0, A1, A2, A4, A5 and A7 are therefore identical to within the seeds'
resolution, and no contrast against A0 has a bootstrap upper bound above 1 pp. *Second, the knowledge
graph is load-bearing only for reuse*, not for the single-intent result: it is the difference between
inheriting a validated constraint and paying for discovery again (Section VI-F). *Third, what is
load-bearing is the probe plus the margin plus the shield*: A7 reproduces A0 with neither the language
model nor the KM estimate nor the gate in the loop, and A8—a highest-elevation controller whose lead
is re-probed on validation—tracks the shield within @@A8_DIFF@@ pp at nominal physics.

We therefore describe the language model and the Kaplan–Meier stage as **automation of discovery and
diagnosis**, not as the source of the performance: they lower the human cost of producing and auditing
a candidate, and the audit gate is what decides whether a candidate may touch the network. The
mechanism claim of the paper is unchanged; the method claim is narrowed accordingly.

### I. Full three-way lockbox

The earlier protocol let three choices touch the evaluation window: the audit gate's admission, the
probe that fixes τ\\*, and the reward-penalty coefficient λ. The three-way protocol removes that by
construction. *Discovery* uses training logs only (0–60%). *Calibration* uses the validation window
only (65–75%): the probe that fixes τ\\*, the gate's replay, the λ selection and the margin m. The
*lockbox* (82–95%) is instantiated three times by shifting the twin epoch by +7, +14 and −2 days, and
is never touched by any selection step.

Re-scoring the four archived coefficients on the validation window returns λ = 8 as the best choice
(81.52% polar HSR on validation, against 69.03 for λ = 0.3, 69.11 for λ = 0.5 and 77.80 for λ = 2.0),
so the coefficient used throughout the lockbox is the same one the evaluation-window scan had picked;
the selection was not window-specific. The threshold probe returns τ\\* = 16 s on the validation window
and is frozen at τ_used = 18 s before any lockbox rollout exists.

@@TABLE_FULL_LOCKBOX@@

The lockbox therefore supports the *ordering* claims under frozen selection, and it bounds—rather than
eliminates—the optimism of an evaluation-window result: the three selections were made once, on one
window, and are then held fixed. We report the evaluation-window numbers and the lockbox numbers side
by side in Table VIII and give their difference, so a reader can see exactly how much of the headline
survives the change of window.

### J. Statistical protocol

Every comparison in this paper is paired on the policy seed: the same ten training seeds appear in
every arm, and every arm is scored on the same episodes. *n* always denotes independent training runs,
never episodes; episode-level counts appear only in the support audit, where they are the object of
study. For each paired contrast we report the exact two-sided Wilcoxon signed-rank p value, a bootstrap
95% confidence interval of the mean difference (10,000 resamples over seeds), and Cohen's d_z. Where we
claim equivalence rather than difference, we report a two-one-sided-test (TOST) against a pre-registered
margin of 1.0 pp, chosen because the run-to-run standard deviation of the main factorial is ≈0.3 pp and
1 pp is a conservative business-equivalence bound. Families of contrasts are Holm-corrected within their
family. Results at n = 5 (cross-intent transfer, the alternative-physics twin) are reported as
descriptive; they carry no significance claim, and the text says so wherever they appear.

### K. Deployment and governance

Fig. 8 shows the deployment view. Discovery, calibration and deployment are three separate services
that share a versioned store and never share a window. The language-model predicate service reads
training logs and emits candidate predicates; the probe runner reads the deployed policy and the
validation window and emits a threshold with a bootstrap interval; the audit gate replays candidates on
the validation window and is the only component that can move a candidate into the committed set; the
shield is a runtime filter that reads the committed constraints and writes nothing. Monitoring closes
the loop: a drift trigger (change in the acquisition-latency distribution, a rise in the late-handover
share, or a TLE update) schedules a re-probe, and a rollback restores the previous committed version.

The knowledge-graph record is the unit of governance. Each record carries a constraint identifier, a
version, the predicate as (field, operator, value) atoms, the effect and magnitude, the margin, scope
tags (region, regime, traffic class), provenance (log window, narrative identifier, model version,
probe run identifier, gate replay identifiers), a confidence, a status in {proposed, committed,
deprecated}, an approver and a rollback pointer. Three rules are enforced by the store rather than by
convention: a newer validation-calibrated magnitude deprecates, never overwrites, the older one; a more
specific scope wins over a broader one; and two records that conflict in effect are never merged
automatically—they are escalated to a human approver. Every commit is reversible, and the rollback
target is part of the record.

"""

rep("### H. Limitations", VIH + "### L. Limitations", "sections-inserted")

P.write_text(t, encoding="utf-8")
print("applied:", done)
